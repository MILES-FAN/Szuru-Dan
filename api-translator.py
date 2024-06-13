import base64
from flask import Flask, request, jsonify
import requests
from utils import *
import time
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

SZURUBOORU_URL = config['SZURUBOORU']['url']
if not SZURUBOORU_URL.endswith('/'):
    SZURUBOORU_URL += '/'
SERVICE_PORT = int(config['SERVICE']['port'])
SZURUBOORU_API_URL = f'{SZURUBOORU_URL}api'

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

fav_map = {}
fav_expiration = 60
fav_exp_map = {}

#print(headers)

@app.route('/posts', methods=['GET'])
@app.route('/posts.json', methods=['GET'])
def search_posts():
    #print(request.args)
    # Translate query parameters from Danbooru to Szurubooru
    query = request.args.get('tags', '')
    query = parse_query(query)
    #print(query)
    limit = request.args.get('limit', 100)
    page = request.args.get('page', 1)
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    posts_per_page = 40
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
    # Calculate offset based on page number
    offset = (int(page) - 1) * posts_per_page

    # Call Szurubooru API
    response = requests.get(f"{SZURUBOORU_API_URL}/posts?offset={offset}&limit={posts_per_page}&query={query}", headers=headers)
    
    if response.status_code == 200:
        szuru_posts = response.json()
        # Convert Szurubooru response to Danbooru format
        danbooru_posts = [convert_post_format(post, login) for post in szuru_posts.get('results', [])]
        return jsonify(danbooru_posts)
    else:
        #print(response.text)
        return jsonify({'message': 'Failed to fetch posts'}), response.status_code

def get_fav(post_id, login, force_refresh=False):
    post_id = str(post_id)
    for key in fav_exp_map:
        if time.time() - fav_exp_map[key] > fav_expiration:
            fav_map.pop(key, None)
            fav_exp_map.pop(key, None)
    if not force_refresh and post_id in fav_map:
        for name in fav_map[post_id]:
            if name == login:
                return True
        return False
    fav_map[post_id] = []
    query = f'fav:{login} id:{post_id}'
    response = requests.get(url=f"{SZURUBOORU_API_URL}/posts?query={query}", headers=headers)
    if response.status_code == 200:
        szuru_post = response.json()
        if len(szuru_post['results']) > 0:
            fav_map[post_id].append(login)
            return True
    
    if login in fav_map[post_id]:
        fav_map[post_id].remove(login)
    return False

@app.route('/posts/<int:post_id>.json', methods=['GET'])
def get_post(post_id):
    #print(request.args)
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    # Fetch post by ID from Szurubooru
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'

    response = requests.get(f"{SZURUBOORU_API_URL}/post/{post_id}", headers=headers)
    if response.status_code == 200:
        szuru_post = response.json()
        danbooru_post = convert_post_format(szuru_post, login)
        return jsonify(danbooru_post)
    else:
        return jsonify({'message': 'Post not found'}), response.status_code

@app.route('/counts/posts.json', methods=['GET'])
def get_post_count():
    return jsonify({'counts': 100}), 200

def tags_str(tags):
    tags_list = []
    for tag in tags:
        tags_list.append(tag['names'][0])

    return ' '.join(tags_list)

@app.route('/favorites.json', methods=['POST'])
@app.route('/favorites', methods=['POST'])
def create_favorite():
    post_id = None
    data = request.get_data()
    if data:
        post_id = int(data.decode('utf-8').removeprefix('post_id='))
        print(post_id)
    else:
        post_id = request.args.get('post_id')
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'

    if post_id in fav_map:
        if login not in fav_map[post_id]:
            fav_map[post_id].append(login)

    response = requests.post(f"{SZURUBOORU_API_URL}/post/{post_id}/favorite", headers=headers)
    if response.status_code == 200:
        return jsonify({'message': 'Favorite created'}), 200
    else:
        return jsonify({'message': 'Failed to create favorite'}), response.status_code

@app.route('/favorites/<int:post_id>.json', methods=['DELETE'])
@app.route('/favorites/<int:post_id>', methods=['DELETE'])
def delete_favorite(post_id):
    post_id = post_id
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'

    if post_id in fav_map:
        if login in fav_map[post_id]:
            fav_map[post_id].remove(login)

    response = requests.delete(url=f"{SZURUBOORU_API_URL}/post/{post_id}/favorite", headers=headers)
    if response.status_code == 200:
        return jsonify({'message': 'Favorite deleted'}), 200
    else:
        return jsonify({'message': 'Failed to delete favorite'}), response.status_code


@app.route('/post_votes.json', methods=['GET'])
@app.route('/favorites.json', methods=['GET'])
def get_favorites():
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    if 'Authorization' in request.headers:
        auth = request.headers['Authorization']
        if auth.startswith('Basic '):
            auth = auth.split(' ')[1]
            auth = base64.b64decode(auth).decode('utf-8')
            login, api_key = auth.split(':')
            print(login, api_key)
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
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
        #print(post_id)
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

    #print(favorites)
    return jsonify(favorites), 200

@app.route('/users/<int:user_id>.json', methods=['GET'])
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    login = None
    api_key = None
    d_format = request.args.get('format', None)
    data = request.get_data()
    if data and d_format == 'json':
        json = request.get_json()
        login = json.get('login', None)
        api_key = json.get('api_key', None)
    elif 'Authorization' in request.headers:
        auth = request.headers['Authorization']
        if auth.startswith('Basic '):
            auth = auth.split(' ')[1]
            auth = base64.b64decode(auth).decode('utf-8')
            login, api_key = auth.split(':')
            print(login, api_key)

    if not login or not api_key:
        login = request.args.get('login', None)
        api_key = request.args.get('api_key', None)
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
    response = requests.get(f"{SZURUBOORU_API_URL}/users/?query={login}", headers=headers)
    if response.status_code == 200:
        user_profile = response.json()
        profile = convert_user_format(user_profile)
        return jsonify(profile)
    else:
        #print(response.text)
        return jsonify({'message': 'Profile not found'}), response.status_code


@app.route('/profile', methods=['GET'])
@app.route('/profile.json', methods=['GET'])
def get_profile():
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    if 'Authorization' in request.headers:
        auth = request.headers['Authorization']
        if auth.startswith('Basic '):
            auth = auth.split(' ')[1]
            auth = base64.b64decode(auth).decode('utf-8')
            login, api_key = auth.split(':')
            print(login, api_key)
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
    response = requests.get(f"{SZURUBOORU_API_URL}/users/?query={login}", headers=headers)
    if response.status_code == 200:
        user_profile = response.json()
        profile = convert_user_format(user_profile)
        return jsonify(profile)
    else:
        return jsonify({'message': 'Profile not found'}), response.status_code

def convert_user_format(user_profile):
    user_profile = user_profile['results'][0]
    print(user_profile)
    profile = {
        'last_logged_in_at': user_profile['lastLoginTime'],
        'id': 1,
        'name': user_profile['name'],
        'level': 20,
        'created_at': user_profile['creationTime'],
        'blacklisted_tags': '',
        'favorite_tags': '',
        'is_deleted': False,
        'is_banned': False,
        'level_string': user_profile['rank'],
        'time_zone': 'Eastern Time (US & Canada)',
        'post_upload_count': user_profile['uploadedPostCount'],
        'updated_at': user_profile['lastLoginTime']
    }
    return profile

def convert_post_format(szuru_post, login=None):
    # Example conversion function
    contentUrl = f"{SZURUBOORU_URL}{szuru_post['contentUrl']}"
    thumbnailUrl = f"{SZURUBOORU_URL}{szuru_post['thumbnailUrl']}"
    ext = contentUrl.split('.')[-1]
    favorited = ''
    if login:
        favorited = get_fav(szuru_post['id'], login)
    ret = {
        'id': szuru_post['id'],
        'created_at': szuru_post['creationTime'],
        'uploader_id': 1,
        'file_url': contentUrl,
        'large_file_url': contentUrl,
        'preview_file_url': thumbnailUrl,
        'file_ext': ext,
        'rating': convert_back_rating(szuru_post['safety']),
        'source': szuru_post['source'],
        'tag_string': tags_str(szuru_post['tags']),
        'fav_string': 'fav:1' if favorited else '',
        'tag_string_general': tags_str(szuru_post['tags']),
        'image_width': szuru_post['canvasWidth'],
        'image_height': szuru_post['canvasHeight'],
        'file_size': szuru_post['fileSize'],
        'has_large': True,
        'has_visible_children': False,
        'has_active_children': False,
        'has_children': False,
        'media_asset': {
            'id': szuru_post['id'],
            'created_at': szuru_post['creationTime'],
            'updated_at': szuru_post['creationTime'],
            'md5': szuru_post['checksumMD5'],
            'file_ext': ext,
            'image_width': szuru_post['canvasWidth'],
            'image_height': szuru_post['canvasHeight'],
            'variants': [
                {
                    'type': 'sample',
                    'url': contentUrl,
                    'width': szuru_post['canvasWidth'],
                    'height': szuru_post['canvasHeight'],
                    'file_ext': ext
                },
                {
                    'type': 'original',
                    'url': contentUrl,
                    'width': szuru_post['canvasWidth'],
                    'height': szuru_post['canvasHeight'],
                    'file_ext': ext
                }
            ]
        }
    }
    return ret

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0' , port=SERVICE_PORT)