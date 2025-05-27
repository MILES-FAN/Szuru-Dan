from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import fav_map, get_fav

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('/favorites.json', methods=['POST'])
@favorites_bp.route('/favorites', methods=['POST'])
def create_favorite():
    post_id = None
    data = request.get_data()
    if data:
        post_id = int(data.decode('utf-8').removeprefix('post_id='))
        print(post_id)
    else:
        post_id = request.args.get('post_id')
    
    headers, login, api_key = get_auth_headers()
    
    if post_id in fav_map:
        if login not in fav_map[post_id]:
            fav_map[post_id].append(login)

    response = requests.post(f"{config.SZURUBOORU_API_URL}/post/{post_id}/favorite", headers=headers)
    if response.status_code == 200:
        return jsonify({'message': 'Favorite created'}), 200
    else:
        return jsonify({'message': 'Failed to create favorite'}), response.status_code

@favorites_bp.route('/favorites/<int:post_id>.json', methods=['DELETE'])
@favorites_bp.route('/favorites/<int:post_id>', methods=['DELETE'])
def delete_favorite(post_id):
    headers, login, api_key = get_auth_headers()
    
    if post_id in fav_map:
        if login in fav_map[post_id]:
            fav_map[post_id].remove(login)

    response = requests.delete(url=f"{config.SZURUBOORU_API_URL}/post/{post_id}/favorite", headers=headers)
    if response.status_code == 200:
        return jsonify({'message': 'Favorite deleted'}), 200
    else:
        return jsonify({'message': 'Failed to delete favorite'}), response.status_code

@favorites_bp.route('/post_votes.json', methods=['GET'])
@favorites_bp.route('/favorites.json', methods=['GET'])
def get_favorites():
    headers, login, api_key = get_auth_headers()
    
    post_ids = request.args.get('search[post_id]', '')
    if ',' in post_ids:
        post_ids = post_ids.split(',')
    elif '+' in post_ids:
        post_ids = post_ids.split('+')
    else:
        post_ids = post_ids.split(' ')
    
    favorites = []
    print(f"Searching favorites for {login}")
    for post_id in post_ids:
        if get_fav(post_id, login):
            fav_item = {
                "id": int(post_id),
                "user_id": 1,
                "post_id": int(post_id),
                "created_at": "2021-09-01T00:00:00Z",
                "updated_at": "2021-09-01T00:00:00Z",
                "score": 1,
                "is_deleted": False,
            }
            favorites.append(fav_item)

    return jsonify(favorites), 200 