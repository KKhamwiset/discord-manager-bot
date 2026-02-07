import os
import asyncio
import requests
from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from routes.auth import token_required

stats_bp = Blueprint('stats', __name__)





BOT_INTERNAL_URL = os.getenv('BOT_INTERNAL_URL', 'http://bot:8080')


def get_bot_status():
    """Check if bot is ready via internal API"""
    try:
        response = requests.get(f'{BOT_INTERNAL_URL}/is_ready', timeout=2)
        if response.status_code == 200:
            is_ready = response.json().get('is_ready', False)
            return 'online' if is_ready else 'starting'
        return 'offline'
    except requests.RequestException:
        return 'offline'

def get_guilds():
    try:
        response = requests.get(f'{BOT_INTERNAL_URL}/guilds', timeout=2)
        if response.status_code == 200:
            return response.json().get('guilds', [])
        return []
    except requests.RequestException:
        return []

@stats_bp.route('/overview')
def overview():
    """Get bot and server overview information (public)"""
    try:
        status = get_bot_status()
        guilds = get_guilds()
        
        target_id = os.getenv('GUILD_ID')
        guild_info = next((g for g in guilds if g['id'] == str(target_id)), 
                         guilds[0] if guilds else {})
        
    except Exception as e:
        current_app.logger.error(f"Failed to fetch guild info: {e}")
        guild_info = {}
        status = 'offline'

    return jsonify({
        'guild': guild_info,
        'bot_status': status
    })
