import os
import asyncio
import requests
from flask import Blueprint, jsonify, request, current_app
from routes.auth import token_required

channel_bp = Blueprint('channel', __name__)

BOT_INTERNAL_URL = os.getenv('BOT_INTERNAL_URL', 'http://bot:8080')

@channel_bp.route('/list')
@token_required
def list_channels():
    """Get all channels for the authorized user"""
    try:
        response = requests.get(f'{BOT_INTERNAL_URL}/channels', timeout=5)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({'error': 'Failed to fetch channels'}), 500
    except Exception as e:
        current_app.logger.error(f"Failed to fetch channels: {e}")
        return jsonify({'error': 'Failed to fetch channels'}), 500
