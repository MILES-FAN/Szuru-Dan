from flask import Blueprint, request, jsonify
from services.auth import extract_auth_from_request
from services.szuru import szuru_request, error_response, get_param, split_ids, get_page_params, parse_score, escape_query
from models.converters import CURRENT_USER_ID, convert_comment_format, convert_vote_format

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/comments.json', methods=['GET'])
@comments_bp.route('/comments', methods=['GET'])
def search_comments():
    login, _ = extract_auth_from_request()
    post_ids = split_ids(request.args.get('search[post_id]') or request.args.get('post_id'))
    terms = []
    if post_ids:
        terms.append(f"post:{','.join(map(str, post_ids))}")
    creator_name = request.args.get('search[creator_name]')
    if creator_name:
        terms.append(f'user:{escape_query(creator_name, keep_wildcards=True)}')

    # A single post's comments are usually requested without a limit
    offset, limit = get_page_params(default_limit=100 if post_ids else 20)
    response = szuru_request('GET', 'comments/', params={
        'query': ' '.join(terms),
        'offset': offset,
        'limit': limit,
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch comments')

    comments = [convert_comment_format(c, login) for c in response.json().get('results', [])]
    return jsonify(comments), 200

@comments_bp.route('/comments/<int:comment_id>.json', methods=['GET'])
@comments_bp.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    login, _ = extract_auth_from_request()
    response = szuru_request('GET', f'comment/{comment_id}')
    if response.status_code != 200:
        return error_response(response, 'Comment not found')
    return jsonify(convert_comment_format(response.json(), login)), 200

@comments_bp.route('/comments.json', methods=['POST'])
@comments_bp.route('/comments', methods=['POST'])
def create_comment():
    login, _ = extract_auth_from_request()
    post_id = get_param('comment[post_id]') or get_param('post_id')
    body = get_param('comment[body]') or get_param('body')
    if not post_id or not body:
        return jsonify({'message': 'comment[post_id] and comment[body] are required'}), 400

    response = szuru_request('POST', 'comments/', json={'postId': int(post_id), 'text': body})
    if response.status_code != 200:
        return error_response(response, 'Failed to create comment')
    return jsonify(convert_comment_format(response.json(), login)), 201

def get_comment_version(comment_id):
    """Szurubooru needs the current version for edits, returns (version, error_response)"""
    response = szuru_request('GET', f'comment/{comment_id}', params={'fields': 'version'})
    if response.status_code != 200:
        return None, error_response(response, 'Comment not found')
    return response.json()['version'], None

@comments_bp.route('/comments/<int:comment_id>.json', methods=['PUT', 'PATCH'])
@comments_bp.route('/comments/<int:comment_id>', methods=['PUT', 'PATCH'])
def update_comment(comment_id):
    login, _ = extract_auth_from_request()
    body = get_param('comment[body]') or get_param('body')
    if not body:
        return jsonify({'message': 'comment[body] is required'}), 400

    version, error = get_comment_version(comment_id)
    if error:
        return error
    response = szuru_request('PUT', f'comment/{comment_id}', json={'version': version, 'text': body})
    if response.status_code != 200:
        return error_response(response, 'Failed to update comment')
    return jsonify(convert_comment_format(response.json(), login)), 200

@comments_bp.route('/comments/<int:comment_id>.json', methods=['DELETE'])
@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    version, error = get_comment_version(comment_id)
    if error:
        return error
    response = szuru_request('DELETE', f'comment/{comment_id}', json={'version': version})
    if response.status_code != 200:
        return error_response(response, 'Failed to delete comment')
    return jsonify({'message': 'Comment deleted'}), 200

def set_comment_score(comment_id, score):
    response = szuru_request('PUT', f'comment/{comment_id}/score', json={'score': score})
    if response.status_code != 200:
        return error_response(response, 'Failed to vote')
    comment = response.json()
    return jsonify(convert_vote_format('comment_id', comment_id, comment.get('ownScore', score), comment.get('lastEditTime'))), 200

@comments_bp.route('/comments/<int:comment_id>/votes.json', methods=['POST', 'PUT'])
@comments_bp.route('/comments/<int:comment_id>/votes', methods=['POST', 'PUT'])
def vote_comment(comment_id):
    score = parse_score(get_param('score'))
    if score is None:
        return jsonify({'message': 'Invalid score'}), 400
    return set_comment_score(comment_id, score)

@comments_bp.route('/comments/<int:comment_id>/votes.json', methods=['DELETE'])
@comments_bp.route('/comments/<int:comment_id>/votes', methods=['DELETE'])
@comments_bp.route('/comment_votes/<int:comment_id>.json', methods=['DELETE'])
@comments_bp.route('/comment_votes/<int:comment_id>', methods=['DELETE'])
def remove_comment_vote(comment_id):
    # Vote ids are comment ids, see convert_vote_format
    return set_comment_score(comment_id, 0)

@comments_bp.route('/comment_votes.json', methods=['GET'])
@comments_bp.route('/comment_votes', methods=['GET'])
def get_comment_votes():
    comment_ids = split_ids(request.args.get('search[comment_id]'))
    user_id = request.args.get('search[user_id]')
    if not comment_ids or (user_id and user_id != str(CURRENT_USER_ID)):
        return jsonify([]), 200

    response = szuru_request('GET', 'comments/', params={
        'query': f"id:{','.join(map(str, comment_ids))}",
        'limit': len(comment_ids),
        'fields': 'id,ownScore,lastEditTime',
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch votes')

    votes = [
        convert_vote_format('comment_id', c['id'], c['ownScore'], c.get('lastEditTime'))
        for c in response.json().get('results', [])
        if c.get('ownScore')
    ]
    return jsonify(votes), 200
