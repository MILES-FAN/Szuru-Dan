from flask import Blueprint, request, jsonify
from services.szuru import szuru_request, error_response, split_ids
from models.converters import convert_note_format

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes.json', methods=['GET'])
@notes_bp.route('/notes', methods=['GET'])
def search_notes():
    post_ids = split_ids(request.args.get('search[post_id]'))
    if not post_ids:
        return jsonify([]), 200

    # Notes are part of the post resource in szurubooru
    response = szuru_request('GET', 'posts/', params={
        'query': f"id:{','.join(map(str, post_ids))}",
        'limit': len(post_ids),
        'fields': 'id,notes,canvasWidth,canvasHeight,creationTime,lastEditTime',
    })
    if response.status_code != 200:
        return error_response(response, 'Failed to fetch notes')

    notes = []
    for post in response.json().get('results', []):
        for index, note in enumerate(post.get('notes') or []):
            notes.append(convert_note_format(note, index, post))
    return jsonify(notes), 200
