import os
import jwt
import requests
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, redirect, current_app

auth_bp = Blueprint('auth', __name__)

DISCORD_API_URL = 'https://discord.com/api/v10'
DISCORD_OAUTH_URL = 'https://discord.com/api/oauth2'


def create_token(user_data: dict) -> str:
    """Create JWT token with user data"""
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'avatar': user_data.get('avatar'),
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check cookie fallback
        if not token:
            token = request.cookies.get('auth_token')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login')
def login():
    """Redirect to Discord OAuth2 authorization page"""
    client_id = current_app.config['DISCORD_CLIENT_ID']
    redirect_uri = current_app.config['OAUTH_REDIRECT_URI']
    scope = 'identify guilds'
    
    oauth_url = (
        f"{DISCORD_OAUTH_URL}/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}"
    )
    
    return jsonify({'url': oauth_url})


@auth_bp.route('/callback')
def callback():
    """Handle OAuth2 callback from Discord"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return jsonify({'error': error}), 400
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    # Exchange code for access token
    token_response = requests.post(
        f"{DISCORD_OAUTH_URL}/token",
        data={
            'client_id': current_app.config['DISCORD_CLIENT_ID'],
            'client_secret': current_app.config['DISCORD_CLIENT_SECRET'],
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': current_app.config['OAUTH_REDIRECT_URI']
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    print(f"token_response: {token_response.text}")

    if token_response.status_code != 200:
        return jsonify({'error': 'Failed to get access token'}), 400
    
    token_data = token_response.json()
    access_token = token_data['access_token']
    
    # Get user info from Discord
    user_response = requests.get(
        f"{DISCORD_API_URL}/users/@me",
        headers={'Authorization': f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return jsonify({'error': 'Failed to get user info'}), 400
    
    user_data = user_response.json()
    
    # Create JWT token
    jwt_token = create_token(user_data)

    return jsonify({
        'token': jwt_token,
        'user': {
            'id': user_data['id'],
            'username': user_data['username'],
            'avatar': user_data.get('avatar'),
            'global_name': user_data.get('global_name')
        }
    })


@auth_bp.route('/me')
@token_required
def me():
    """Get current authenticated user"""
    return jsonify({
        'user_id': request.user['user_id'],
        'username': request.user['username'],
        'avatar': request.user['avatar']

    })


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout user (client should delete token)"""
    return jsonify({'message': 'Logged out successfully'})
