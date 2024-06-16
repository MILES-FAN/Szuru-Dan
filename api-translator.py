import base64
from flask import Flask, request, jsonify
import requests
from utils import *
import time
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

SZURUBOORU_URL = config['API']['backend_url']

if not SZURUBOORU_URL.endswith('/'):
    SZURUBOORU_URL += '/'

DOMAIN_URL = ''
if 'domain_url' in config['API'] and config['API']['domain_url'] != '':
    DOMAIN_URL = config['API']['domain_url']
    if not DOMAIN_URL.endswith('/'):
        DOMAIN_URL += '/'
else:
    DOMAIN_URL = SZURUBOORU_URL

SERVICE_PORT = int(config['API']['port'])
SZURUBOORU_API_URL = f'{SZURUBOORU_URL}api'


headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

fav_map = {}

category_map = {
    'General': 0,
    'Artist': 1,
    'Series': 3,
    'Character': 4,
    'Meta': 5,
    'default': 0,
    'general': 0,
    'artist': 1,
    'series': 3,
    'character': 4,
    'meta': 5,
    0: 'General',
    1: 'Artist',
    3: 'Series',
    4: 'Character',
    5: 'Meta'
}

#print(headers)

@app.route('/posts', methods=['GET'])
@app.route('/posts.json', methods=['GET'])
def search_posts():
    #print(request.args)
    # Translate query parameters from Danbooru to Szurubooru
    query = request.args.get('tags', '')
    query = parse_query(query)
    #print(query)
    limit = request.args.get('limit', 40)
    limit = min(int(limit), 40)
    page = request.args.get('page', 1)
    login = request.args.get('login', None)
    api_key = request.args.get('api_key', None)
    posts_per_page = limit
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
    # Calculate offset based on page number
    offset = (int(page) - 1) * posts_per_page
    tik = time.time()
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

def get_fav(post_id, login):
    post_id = int(post_id)
    if not post_id in fav_map:
        return False
    if login in fav_map[post_id]:
        print(f"{login} has favorited {post_id}")
        return True
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

@app.route('/tags/autocomplete.json', methods=['GET'])
@app.route('/tags/autocomplete', methods=['GET'])
@app.route('/autocomplete.json', methods=['GET'])
@app.route('/autocomplete', methods=['GET'])
def autocomplete_tags():
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

    query = request.args.get('search[query]', '')
    if len (query) < 3:
        query = f'{query}*'
    else:
        query = f'*{query}*'
    limit = request.args.get('limit', 10)
    response = requests.get(f"{SZURUBOORU_API_URL}/tags/?query={query}%20sort:usages&limit={limit}", headers=headers)
    if response.status_code == 200:
        tags = response.json()
        #print(tags)
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
    contentUrl = f"{DOMAIN_URL}{szuru_post['contentUrl']}"
    thumbnailUrl = f"{DOMAIN_URL}{szuru_post['thumbnailUrl']}"
    ext = contentUrl.split('.')[-1]
    favorited = ''
    artist_tag_string = ''
    artist_tag_list = []
    general_tag_string = ''
    general_tag_list = []
    character_tag_string = ''
    character_tag_list = []
    copyright_tag_string = ''
    copyright_tag_list = []
    meta_tag_string = ''
    meta_tag_list = []
    for tag in szuru_post['tags']:
        if tag['category'].lower() == 'default':
            general_tag_list.append(tag['names'][0])
        elif tag['category'].lower() == 'artist':
            artist_tag_list.append(tag['names'][0])
        elif tag['category'].lower() == 'character':
            character_tag_list.append(tag['names'][0])
        elif tag['category'].lower() == 'series':
            copyright_tag_list.append(tag['names'][0])
        elif tag['category'].lower() == 'meta':
            meta_tag_list.append(tag['names'][0])


    favoritedBy = szuru_post['favoritedBy']

    post_id = szuru_post['id']

    for fav in favoritedBy:
        if post_id in fav_map:
            fav_map[post_id].append(fav['name'])
        else:
            fav_map[post_id] = [fav['name']]

    tag_count_artist = len(artist_tag_list)
    tag_count_general = len(general_tag_list)
    tag_count_character = len(character_tag_list)
    tag_count_copyright = len(copyright_tag_list)
    tag_count_meta = len(meta_tag_list)
    artist_tag_string = ' '.join(artist_tag_list)
    general_tag_string = ' '.join(general_tag_list)
    character_tag_string = ' '.join(character_tag_list)
    copyright_tag_string = ' '.join(copyright_tag_list)
    meta_tag_string = ' '.join(meta_tag_list)
    source = ''
    if szuru_post['source']:
        source = szuru_post['source']
    if '\n' in source:
        source = source.split('\n')[0]
    if login:
        favorited = get_fav(szuru_post['id'], login)
    ret = {
        'id': szuru_post['id'],
        'created_at': szuru_post['creationTime'],
        'uploader_id': 1,
        'score': szuru_post['score'],
        'file_url': contentUrl,
        'large_file_url': contentUrl,
        'preview_file_url': thumbnailUrl,
        'file_ext': ext,
        'rating': convert_back_rating(szuru_post['safety']),
        'source': source,
        'tag_string': tags_str(szuru_post['tags']),
        'fav_string': 'fav:1' if favorited else '',
        'tag_string_general': general_tag_string,
        'tag_string_artist': artist_tag_string,
        'tag_string_character': character_tag_string,
        'tag_string_copyright': copyright_tag_string,
        'tag_string_meta': meta_tag_string,
        'tag_count': len(szuru_post['tags']),
        'tag_count_artist': tag_count_artist,
        'tag_count_general': tag_count_general,
        'tag_count_character': tag_count_character,
        'tag_count_copyright': tag_count_copyright,
        'tag_count_meta': tag_count_meta,
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
    app.run(debug=True, host='0.0.0.0' , port=9000)