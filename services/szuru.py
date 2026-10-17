import requests
from flask import request, jsonify
from config import config
from services.auth import get_auth_headers

# Characters that szurubooru's search parser treats specially
QUERY_SPECIAL_CHARS = '\\*:-.,'

def szuru_request(method, path, params=None, json=None, timeout=30):
    """Call the szurubooru API with the auth of the current request"""
    headers, login, api_key = get_auth_headers()
    url = f"{config.SZURUBOORU_API_URL}/{path.lstrip('/')}"
    return requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)

def error_response(response, message):
    """Turn a failed szurubooru response into a Danbooru style error"""
    try:
        detail = response.json().get('description', '')
    except ValueError:
        detail = ''
    return jsonify({'success': False, 'message': message, 'detail': detail}), response.status_code

def escape_query(value, keep_wildcards=False):
    """Escape a literal value for use inside a szurubooru search token"""
    special = QUERY_SPECIAL_CHARS.replace('*', '') if keep_wildcards else QUERY_SPECIAL_CHARS
    return ''.join(f'\\{c}' if c in special else c for c in value)

def get_param(name, default=None):
    """Read a Danbooru parameter from the query string, form body or JSON body.
    `comment[body]` style names are also looked up as nested JSON objects."""
    if name in request.args:
        return request.args[name]
    if name in request.form:
        return request.form[name]
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        if name in data:
            return data[name]
        if name.endswith(']') and '[' in name:
            outer, inner = name[:-1].split('[', 1)
            nested = data.get(outer)
            if isinstance(nested, dict) and inner in nested:
                return nested[inner]
    return default

def split_ids(value):
    """Split Danbooru id lists ('1,2', '1 2', '1+2') into a list of ints"""
    if value is None:
        return []
    ids = []
    for part in str(value).replace(',', ' ').replace('+', ' ').split():
        if part.isdigit():
            ids.append(int(part))
    return ids

def get_page_params(default_limit=20, max_limit=100):
    """Convert Danbooru page/limit parameters into szurubooru offset/limit"""
    try:
        limit = min(int(request.args.get('limit', default_limit)), max_limit)
    except ValueError:
        limit = default_limit
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    return (page - 1) * limit, limit

def parse_score(value):
    """Danbooru accepts 1/-1 as well as up/down for votes"""
    if value in ('up', 'upvote'):
        return 1
    if value in ('down', 'downvote'):
        return -1
    try:
        return max(-1, min(1, int(value)))
    except (TypeError, ValueError):
        return None
