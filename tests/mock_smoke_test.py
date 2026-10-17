"""Smoke test against a mock szurubooru server, no real backend needed.

Usage: python tests/mock_smoke_test.py
Prints every translated request and the JSON returned to the client.
"""
import os, sys, json, tempfile, threading
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
# config.py reads config.ini from the working directory
os.chdir(tempfile.mkdtemp())
with open('config.ini', 'w') as f:
    f.write("[API]\nbackend_url = http://127.0.0.1:18080/\nport = 9000\n"
            "reverse_proxy_mode = false\nenable_timing_logs = false\n")
from flask import Flask, request, jsonify
from werkzeug.serving import make_server

calls = []
fake = Flask('fake')
POST = {
    'version': 3, 'id': 7, 'creationTime': '2024-01-01T00:00:00Z', 'lastEditTime': '2024-02-01T00:00:00Z',
    'safety': 'safe', 'source': 'http://a\nhttp://b', 'checksumMD5': 'abc', 'canvasWidth': 1000, 'canvasHeight': 500,
    'contentUrl': 'data/posts/7.png', 'thumbnailUrl': 'data/generated-thumbnails/7.jpg', 'fileSize': 123,
    'tags': [{'names': ['foo'], 'category': 'General', 'usages': 3}, {'names': ['bar'], 'category': 'artist', 'usages': 1},
             {'names': ['baz'], 'category': 'weird', 'usages': 1}],
    'user': {'name': 'other'}, 'score': -2, 'ownScore': -1, 'ownFavorite': True, 'favoriteCount': 4,
    'commentCount': 2, 'noteCount': 1, 'favoritedBy': [{'name': 'me'}, {'name': 'other'}],
    'notes': [{'polygon': [[0.1, 0.2], [0.1, 0.6], [0.5, 0.6], [0.5, 0.2]], 'text': 'hi'}],
    'pools': [{'id': 3, 'names': ['p3']}],
}
COMMENT = {'version': 2, 'id': 11, 'postId': 7, 'user': {'name': 'me'}, 'text': 'hello',
           'creationTime': '2024-01-01T00:00:00Z', 'lastEditTime': None, 'score': 1, 'ownScore': 1}
POOL = {'version': 1, 'id': 3, 'names': ['p3'], 'category': 'default', 'posts': [{'id': 7}, {'id': 8}],
        'creationTime': '2024-01-01T00:00:00Z', 'lastEditTime': None, 'postCount': 2, 'description': 'd'}

@fake.route('/api/<path:p>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api(p):
    calls.append((request.method, p, dict(request.args), request.get_json(silent=True), request.headers.get('Authorization')))
    if p in ('posts/', 'posts') and 'forbidden' in request.args.get('query',''):
        return jsonify({'name': 'AuthError', 'description': 'bad token'}), 403
    if p in ('posts/', 'posts'):
        return jsonify({'total': 42, 'results': [POST]})
    if p.startswith('post/') and p.endswith('/score'):
        return jsonify(dict(POST, ownScore=request.json['score']))
    if p.startswith('post/'):
        return jsonify(POST)
    if p == 'comments/' and request.method == 'POST':
        return jsonify(dict(COMMENT, text=request.json['text']))
    if p == 'comments/':
        return jsonify({'total': 1, 'results': [COMMENT]})
    if p.startswith('comment/') and p.endswith('/score'):
        return jsonify(dict(COMMENT, ownScore=request.json['score']))
    if p.startswith('comment/'):
        return jsonify({} if request.method == 'DELETE' else COMMENT)
    if p.startswith('pool/') or p == 'pools/':
        return jsonify(POOL if p.startswith('pool/') else {'total': 1, 'results': [POOL]})
    if p == 'tags/':
        return jsonify({'total': 1, 'results': [{'names': ['re:zero'], 'category': 'series', 'usages': 9, 'creationTime': 'x'}]})
    return jsonify({'name': 'NotFound', 'description': 'nope'}), 404

srv = make_server('127.0.0.1', 18080, fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()

from app import create_app
c = create_app().test_client()
auth = {'login': 'me', 'api_key': 'k'}

def show(method, url, **kw):
    calls.clear()
    r = getattr(c, method)(url, **kw)
    print(f'--- {method.upper()} {url} -> {r.status_code}')
    print(json.dumps(r.get_json(), ensure_ascii=False)[:700])
    for call in calls:
        print('   szuru:', call[0], call[1], call[2], call[3], 'auth' if call[4] else 'noauth')

show('get', '/posts.json', query_string=dict(auth, tags='rating:s', limit=1))
show('get', '/counts/posts.json', query_string=dict(auth, tags='foo rating:e'))
show('get', '/favorites.json', query_string={**auth, 'search[post_id]': '7 8', 'search[user_id]': '1'})
show('get', '/favorites.json', query_string={**auth, 'search[post_id]': '7', 'search[user_id]': '5'})
show('post', '/favorites.json', query_string=dict(auth, post_id=7))
show('post', '/favorites', query_string=auth, data='post_id=7', content_type='application/x-www-form-urlencoded')
show('delete', '/favorites/7.json', query_string=auth)
show('get', '/posts/7/favorites.json', query_string=auth)
show('post', '/posts/7/votes.json', query_string=dict(auth, score=1))
show('delete', '/post_votes/7.json', query_string=auth)
show('get', '/post_votes.json', query_string={**auth, 'search[post_id]': '7,8', 'search[user_id]': '1'})
show('get', '/comments.json', query_string={**auth, 'search[post_id]': '7', 'only': 'id,is_deleted'})
show('post', '/comments.json', query_string=auth, data={'comment[post_id]': '7', 'comment[body]': 'yo', 'comment[do_not_bump_post]': 'true'})
show('put', '/comments/11.json', query_string=auth, data={'comment[body]': 'edited'})
show('delete', '/comments/11.json', query_string=auth)
show('post', '/comments/11/votes.json', query_string=dict(auth, score=-1))
show('delete', '/comment_votes/11.json', query_string=auth)
show('get', '/comment_votes.json', query_string={**auth, 'search[comment_id]': '11,12'})
show('get', '/notes.json', query_string={**auth, 'search[post_id]': '7'})
show('get', '/pools.json', query_string={**auth, 'search[post_ids_include_all]': '7'})
show('get', '/pools.json', query_string={**auth, 'search[name_matches]': 'my pool', 'search[category]': 'series', 'search[order]': 'post_count', 'page': 2, 'limit': 10})
show('get', '/pools/3.json', query_string=auth)
show('get', '/tags.json', query_string={**auth, 'search[name_comma]': 're:zero,foo-bar', 'search[order]': 'count', 'search[hide_empty]': 'yes', 'limit': 1000})
show('get', '/autocomplete.json', query_string={**auth, 'search[query]': 're', 'limit': 5})
# JSON body auth used by AnimeBoxes style clients
show('post', '/favorites.json?format=json', json={'login': 'me', 'api_key': 'k', 'post_id': 7})

print('=========== AnimeBoxes flow')
ab = {'login': 'me', 'api_key': 'k'}
show('get', '/posts.json?login=me&api_key=k&limit=1')
show('get', '/posts.json?login=me&api_key=k&limit=100&page=1&tags=' + 'foo%20rating:safe%20order:score%20width:%3E=1920')
show('get', '/posts.json?login=me&api_key=k&limit=1&tags=forbidden')
show('post', '/favorites?login=me&api_key=k&post_id=7', data='{}', content_type='application/json; charset=utf-8')
show('delete', '/favorites/7?login=me&api_key=k')
show('get', '/notes.json?group_by=note&search[post_id]=7&page=1&login=me&api_key=k')
show('get', '/pools.json?search[name_matches]=abc&search[sort]=name&commit=Search&page=1&login=me&api_key=k')
show('get', '/tags.json?search[order]=count&search[hide_empty]=true&limit=10&only=id,name,category,post_count&search[name_matches]=*fo*&api_key=k&login=me')
srv.shutdown()
