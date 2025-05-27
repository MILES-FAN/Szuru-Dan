from flask import Blueprint, request, jsonify
import requests
from config import config
from services.auth import get_auth_headers
from models.converters import convert_user_format

users_bp = Blueprint('users', __name__)

@users_bp.route('/users/<int:user_id>.json', methods=['GET'])
@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    headers, login, api_key = get_auth_headers()
    
    response = requests.get(f"{config.SZURUBOORU_API_URL}/users/?query={login}", headers=headers)
    if response.status_code == 200:
        user_profile = response.json()
        profile = convert_user_format(user_profile)
        return jsonify(profile)
    else:
        return jsonify({'message': 'Profile not found'}), response.status_code

@users_bp.route('/profile', methods=['GET'])
@users_bp.route('/profile.json', methods=['GET'])
def get_profile():
    headers, login, api_key = get_auth_headers()
    
    response = requests.get(f"{config.SZURUBOORU_API_URL}/users/?query={login}", headers=headers)
    if response.status_code == 200:
        user_profile = response.json()
        profile = convert_user_format(user_profile)
        return jsonify(profile)
    else:
        return jsonify({'message': 'Profile not found'}), response.status_code 