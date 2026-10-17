from flask import Blueprint, request, jsonify
from services.auth import extract_auth_from_request
from services.szuru import szuru_request, error_response, get_param, split_ids
from models.converters import CURRENT_USER_ID, user_id_for

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('/favorites.json', methods=['POST'])
@favorites_bp.route('/favorites', methods=['POST'])
def create_favorite():
    post_id = get_param('post_id')
    if post_id is None or not str(post_id).isdigit():
        return jsonify({'message': 'post_id is required'}), 400

    response = szuru_request('POST', f'post/{post_id}/favorite')
    if response.status_code == 200:
        return jsonify({'message': 'Favorite created'}), 200
    else:
        return error_response(response, 'Failed to create favorite')

@favorites_bp.route('/favorites/<int:post_id>.json', methods=['DELETE'])
@favorites_bp.route('/favorites/<int:post_id>', methods=['DELETE'])
def delete_favorite(post_id):
    response = szuru_request('DELETE', f'post/{post_id}/favorite')
    if response.status_code == 200:
        return jsonify({'message': 'Favorite deleted'}), 200
    else:
        return error_response(response, 'Failed to delete favorite')

@favorites_bp.route('/favorites.json', methods=['GET'])
@favorites_bp.route('/favorites', methods=['GET'])
def get_favorites():
    post_ids = split_ids(request.args.get('search[post_id]'))
    user_id = request.args.get('search[user_id]')
    # Only the logged in user's favorites can be looked up by id
    if not post_ids or (user_id and user_id != str(CURRENT_USER_ID)):
        return jsonify([]), 200

    response = szuru_request('GET', 'posts/', params={
        'query': f"id:{','.join(map(str, post_ids))}",
        'limit': len(post_ids),
        'fields': 'id,ownFavorite',
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch favorites')

    favorites = [
        {
            'id': post['id'],
            'user_id': CURRENT_USER_ID,
            'post_id': post['id'],
        }
        for post in response.json().get('results', [])
        if post.get('ownFavorite')
    ]
    return jsonify(favorites), 200

@favorites_bp.route('/posts/<int:post_id>/favorites.json', methods=['GET'])
@favorites_bp.route('/posts/<int:post_id>/favorites', methods=['GET'])
def get_post_favorites(post_id):
    login, _ = extract_auth_from_request()
    response = szuru_request('GET', f'post/{post_id}', params={'fields': 'id,favoritedBy'})
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch favorites')

    favorites = []
    for user in response.json().get('favoritedBy', []):
        user_id = user_id_for(user, login)
        favorites.append({
            'id': user_id,
            'user_id': user_id,
            'post_id': post_id,
            'user': {'id': user_id, 'name': user['name']},
        })
    return jsonify(favorites), 200
