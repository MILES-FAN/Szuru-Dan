from flask import Blueprint, request, jsonify
from services.szuru import szuru_request, error_response, get_param, split_ids, parse_score
from models.converters import CURRENT_USER_ID, convert_vote_format

votes_bp = Blueprint('votes', __name__)

def set_post_score(post_id, score):
    response = szuru_request('PUT', f'post/{post_id}/score', json={'score': score},
                             params={'fields': 'id,ownScore,lastEditTime'})
    if response.status_code != 200:
        return error_response(response, 'Failed to vote')
    post = response.json()
    return jsonify(convert_vote_format('post_id', post_id, post.get('ownScore', score), post.get('lastEditTime'))), 200

@votes_bp.route('/posts/<int:post_id>/votes.json', methods=['POST', 'PUT'])
@votes_bp.route('/posts/<int:post_id>/votes', methods=['POST', 'PUT'])
def vote_post(post_id):
    score = parse_score(get_param('score'))
    if score is None:
        return jsonify({'message': 'Invalid score'}), 400
    return set_post_score(post_id, score)

@votes_bp.route('/posts/<int:post_id>/votes.json', methods=['DELETE'])
@votes_bp.route('/posts/<int:post_id>/votes', methods=['DELETE'])
@votes_bp.route('/post_votes/<int:post_id>.json', methods=['DELETE'])
@votes_bp.route('/post_votes/<int:post_id>', methods=['DELETE'])
def remove_post_vote(post_id):
    # Vote ids are post ids, see convert_vote_format
    return set_post_score(post_id, 0)

@votes_bp.route('/post_votes.json', methods=['GET'])
@votes_bp.route('/post_votes', methods=['GET'])
def get_post_votes():
    post_ids = split_ids(request.args.get('search[post_id]'))
    user_id = request.args.get('search[user_id]')
    # Only the logged in user's votes are visible
    if not post_ids or (user_id and user_id != str(CURRENT_USER_ID)):
        return jsonify([]), 200

    response = szuru_request('GET', 'posts/', params={
        'query': f"id:{','.join(map(str, post_ids))}",
        'limit': len(post_ids),
        'fields': 'id,ownScore,lastEditTime',
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch votes')

    votes = [
        convert_vote_format('post_id', post['id'], post['ownScore'], post.get('lastEditTime'))
        for post in response.json().get('results', [])
        if post.get('ownScore')
    ]
    return jsonify(votes), 200
