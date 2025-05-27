from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import category_map

tags_bp = Blueprint('tags', __name__)

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
                'category': category_map[tag['category']],
                'post_count': tag['usages']
            }
            auto_complete_tags.append(tag_obj)
        return jsonify(auto_complete_tags), 200
    else:
        return jsonify({'message': 'Failed to fetch tags'}), response.status_code 