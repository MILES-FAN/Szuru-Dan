from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from services.szuru import szuru_request, error_response, get_page_params, escape_query
from models.converters import danbooru_category, convert_tag_format

tags_bp = Blueprint('tags', __name__)

# Szurubooru category names for each Danbooru category id
szuru_category_names = {
    '0': ['default', 'general'],
    '1': ['artist'],
    '3': ['series', 'copyright'],
    '4': ['character'],
    '5': ['meta'],
}

tag_order_map = {
    'count': 'usages',
    'name': 'name',
    'date': 'creation-date',
}

@tags_bp.route('/tags/autocomplete.json', methods=['GET'])
@tags_bp.route('/tags/autocomplete', methods=['GET'])
@tags_bp.route('/autocomplete.json', methods=['GET'])
@tags_bp.route('/autocomplete', methods=['GET'])
def autocomplete_tags():
    headers, login, api_key = get_auth_headers()

    query = request.args.get('search[query]', '')
    if len(query) < 3:
        query = f'{query}*'
    else:
        query = f'*{query}*'
    limit = request.args.get('limit', 10)

    response = requests.get(f"{config.SZURUBOORU_API_URL}/tags/?query={query}%20sort:usages&limit={limit}", headers=headers)
    if response.status_code == 200:
        tags = response.json()
        auto_complete_tags = []
        for tag in tags['results']:
            tag_obj = {
                'type': 'tag-word',
                'label': tag['names'][0],
                'value': tag['names'][0],
                'category': danbooru_category(tag['category']),
                'post_count': tag['usages']
            }
            auto_complete_tags.append(tag_obj)
        return jsonify(auto_complete_tags), 200
    else:
        return jsonify({'message': 'Failed to fetch tags'}), response.status_code

@tags_bp.route('/tags.json', methods=['GET'])
@tags_bp.route('/tags', methods=['GET'])
def search_tags():
    terms = []
    names = request.args.get('search[name_comma]') or request.args.get('search[name]')
    if names:
        escaped = [escape_query(name.strip()) for name in names.split(',') if name.strip()]
        terms.append(f"name:{','.join(escaped)}")
    name_matches = request.args.get('search[name_matches]')
    if name_matches:
        terms.append(f'name:{escape_query(name_matches, keep_wildcards=True)}')
    category = request.args.get('search[category]')
    if category in szuru_category_names:
        terms.append(f"category:{','.join(szuru_category_names[category])}")
    if request.args.get('search[hide_empty]') in ('yes', 'true', '1'):
        terms.append('usages-min:1')
    order = request.args.get('search[order]')
    if order in tag_order_map:
        terms.append(f'sort:{tag_order_map[order]}')

    offset, limit = get_page_params(default_limit=20, max_limit=100)
    response = szuru_request('GET', 'tags/', params={
        'query': ' '.join(terms),
        'offset': offset,
        'limit': limit,
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch tags')
    return jsonify([convert_tag_format(t) for t in response.json().get('results', [])]), 200
