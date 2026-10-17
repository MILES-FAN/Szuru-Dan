import re
from flask import Blueprint, request, jsonify
from services.szuru import szuru_request, error_response, split_ids, get_page_params, escape_query
from models.converters import convert_pool_format

pools_bp = Blueprint('pools', __name__)

pool_order_map = {
    'updated_at': 'last-edit-date',
    'created_at': 'creation-date',
    'post_count': 'post-count',
    'name': 'name',
}

def fetch_pools_by_id(pool_ids):
    """Szurubooru can't search pools by id, so they are fetched one by one"""
    pools = []
    for pool_id in pool_ids:
        response = szuru_request('GET', f'pool/{pool_id}')
        if response.status_code == 200:
            pools.append(convert_pool_format(response.json()))
    return pools

def pool_ids_of_posts(post_ids, match_all):
    """Ids of pools containing all (or any) of the given posts, None on error"""
    response = szuru_request('GET', 'posts/', params={
        'query': f"id:{','.join(map(str, post_ids))}",
        'limit': len(post_ids),
        'fields': 'id,pools',
    })
    if response.status_code != 200:
        return None
    pool_sets = [{pool['id'] for pool in post.get('pools') or []}
                 for post in response.json().get('results', [])]
    if not pool_sets:
        return []
    merged = set.intersection(*pool_sets) if match_all else set.union(*pool_sets)
    return sorted(merged)

@pools_bp.route('/pools.json', methods=['GET'])
@pools_bp.route('/pools', methods=['GET'])
def search_pools():
    pool_ids = split_ids(request.args.get('search[id]'))
    if pool_ids:
        return jsonify(fetch_pools_by_id(pool_ids)), 200

    for key, match_all in (('search[post_ids_include_all]', True), ('search[post_ids_include_any]', False)):
        post_ids = split_ids(request.args.get(key))
        if post_ids:
            pool_ids = pool_ids_of_posts(post_ids, match_all)
            if pool_ids is None:
                return jsonify({'message': 'Failed to fetch pools'}), 500
            return jsonify(fetch_pools_by_id(pool_ids)), 200

    terms = []
    name = request.args.get('search[name_matches]', '').strip()
    if name:
        # Danbooru matches names partially unless wildcards are given,
        # spaces and underscores are interchangeable
        if '*' not in name:
            name = f'*{name}*'
        name = escape_query(re.sub(r'[\s_]+', '*', name), keep_wildcards=True)
        terms.append(f'name:{name}')
    category = request.args.get('search[category]')
    if category == 'collection':
        terms.append('category:collection')
    elif category == 'series':
        terms.append('-category:collection')
    order = request.args.get('search[order]') or request.args.get('search[sort]', 'updated_at')
    terms.append(f"sort:{pool_order_map.get(order, 'last-edit-date')}")

    offset, limit = get_page_params()
    response = szuru_request('GET', 'pools/', params={
        'query': ' '.join(terms),
        'offset': offset,
        'limit': limit,
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch pools')
    return jsonify([convert_pool_format(p) for p in response.json().get('results', [])]), 200

@pools_bp.route('/pools/<int:pool_id>.json', methods=['GET'])
def get_pool(pool_id):
    response = szuru_request('GET', f'pool/{pool_id}')
    if response.status_code != 200:
        return error_response(response, 'Pool not found')
    return jsonify(convert_pool_format(response.json())), 200
