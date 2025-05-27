import base64
from flask import request
from utils import encode_auth_headers

def get_auth_headers():
    """Extract authentication from request and return headers dict"""
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    login, api_key = extract_auth_from_request()
    
    if login and api_key:
        headers['Authorization'] = f'Token {encode_auth_headers(login, api_key)}'
    
    return headers, login, api_key

def extract_auth_from_request():
    """Extract login and api_key from various sources in the request"""
    login = None
    api_key = None
    
    # Try to get from JSON body
    d_format = request.args.get('format', None)
    data = request.get_data()
    if data and d_format == 'json':
        json_data = request.get_json()
        login = json_data.get('login', None)
        api_key = json_data.get('api_key', None)
    
    # Try to get from Authorization header
    elif 'Authorization' in request.headers:
        auth = request.headers['Authorization']
        if auth.startswith('Basic '):
            auth = auth.split(' ')[1]
            auth = base64.b64decode(auth).decode('utf-8')
            login, api_key = auth.split(':')
            print(login, api_key)
    
    # Try to get from query parameters
    if not login or not api_key:
        login = request.args.get('login', None)
        api_key = request.args.get('api_key', None)
    
    return login, api_key 