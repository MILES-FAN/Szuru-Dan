from flask import Blueprint, request, jsonify
import logging
import requests
import time
from config import config
from services.auth import get_auth_headers
from models.converters import convert_post_format
from utils import parse_query
from services.timing import Timer, RequestTimer
from services.szuru import szuru_request, error_response

logger = logging.getLogger(__name__)

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['GET'])
@posts_bp.route('/posts.json', methods=['GET'])
def search_posts():
    # Create a request timer
    timer = RequestTimer()
    timer.checkpoint("Request started")
    
    # Parse query parameters
    with Timer("Parse query parameters"):
        query = request.args.get('tags', '')
        original_query = query
        query = parse_query(query)
        limit = request.args.get('limit', 40)
        limit = min(int(limit), 100)
        page = request.args.get('page', 1)
    
    timer.checkpoint("Query parameters parsed")
    
    # Get authentication info
    with Timer("Get authentication headers"):
        headers, login, api_key = get_auth_headers()
    
    timer.checkpoint("Authentication processed")
    
    posts_per_page = limit
    offset = (int(page) - 1) * posts_per_page
    
    # Build the API URL
    api_url = f"{config.SZURUBOORU_API_URL}/posts"
    api_params = {'offset': offset, 'limit': posts_per_page, 'query': query}
    
    timer.checkpoint("API URL constructed")
    
    # Call the Szurubooru API
    with Timer("Szurubooru API request"):
        try:
            response = requests.get(api_url, params=api_params, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            logger.error(f"API request timeout for query: {original_query}")
            return jsonify({'message': 'API request timeout'}), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return jsonify({'message': 'API request failed'}), 500
    
    timer.checkpoint("Szurubooru API response received")
    
    if response.status_code == 200:
        with Timer("Parse JSON response"):
            szuru_posts = response.json()
        
        timer.checkpoint("JSON parsed")
        
        # Convert the format
        with Timer("Convert post formats"):
            results = szuru_posts.get('results', [])
            danbooru_posts = []
            
            for i, post in enumerate(results):
                with Timer(f"Convert post {i+1}/{len(results)}"):
                    converted_post = convert_post_format(post, login)
                    danbooru_posts.append(converted_post)
        
        timer.checkpoint("All posts converted")
        
        # Build the response
        with Timer("Build JSON response"):
            response_data = jsonify(danbooru_posts)
        
        timer.checkpoint("Response built")
        timer.summary()
        
        return response_data
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        # Danbooru clients check for 401 to report bad credentials, szurubooru answers 403
        status = 401 if response.status_code == 403 and login else response.status_code
        return error_response(response, 'Failed to fetch posts')[0], status

@posts_bp.route('/posts/<int:post_id>.json', methods=['GET'])
def get_post(post_id):
    timer = RequestTimer(f"post-{post_id}")
    timer.checkpoint("Single post request started")
    
    with Timer("Get authentication headers"):
        headers, login, api_key = get_auth_headers()
    
    timer.checkpoint("Authentication processed")
    
    with Timer("Szurubooru API request"):
        response = requests.get(f"{config.SZURUBOORU_API_URL}/post/{post_id}", headers=headers)
    
    timer.checkpoint("API response received")
    
    if response.status_code == 200:
        with Timer("Parse JSON and convert format"):
            szuru_post = response.json()
            danbooru_post = convert_post_format(szuru_post, login)
        
        timer.checkpoint("Post converted")
        timer.summary()
        
        return jsonify(danbooru_post)
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        return jsonify({'message': 'Post not found'}), response.status_code

@posts_bp.route('/counts/posts.json', methods=['GET'])
@posts_bp.route('/counts/posts', methods=['GET'])
def get_post_count():
    query = parse_query(request.args.get('tags', ''))
    with Timer("Get post count"):
        try:
            # Only the total is needed, so fetch as little as possible
            response = szuru_request('GET', 'posts/', params={'query': query, 'limit': 1, 'fields': 'id'})
        except requests.exceptions.RequestException as e:
            logger.error(f"Post count request failed: {e}")
            return jsonify({'message': 'API request failed'}), 500
    if response.status_code != 200:
        return error_response(response, 'Failed to count posts')
    return jsonify({'counts': {'posts': response.json().get('total', 0)}}), 200
