import os

import requests
from flask import Blueprint, jsonify, request, current_app
from routes.auth import token_required

commands_bp = Blueprint('commands', __name__)





BOT_INTERNAL_URL = os.getenv('BOT_INTERNAL_URL', 'http://bot:8080')


def get_available_commands():
    """Get commands from the running bot via internal API"""
    try:
        response = requests.get(f'{BOT_INTERNAL_URL}/commands', timeout=5)
        if response.status_code == 200:
            return response.json().get('commands', [])
        return []
    except requests.RequestException:
        return []


@commands_bp.route('')
def list_commands():
    """List all available bot commands"""
    bot_commands = get_available_commands()
    result = []
    for cmd in bot_commands:
        result.append({
            'name': cmd['name'],
            'cog': cmd.get('cog', 'Unknown'),
            'description': cmd.get('description', ''),
            'aliases': cmd.get('aliases', []),
            'hidden' : cmd.get('hidden', False),
            'enable' : cmd.get('enabled', True)
        })
    
    return jsonify({'commands': result})


@commands_bp.route('/<command_name>', methods=['PATCH'])
@token_required
def update_command(command_name):
    """Enable/disable a command"""
    data = request.get_json()
    
    if 'enabled' not in data:
        return jsonify({'error': 'Missing enabled field'}), 400
    
    db = current_app.db
    
    db.command_config.update_one(
        {'command_name': command_name},
        {'$set': {'enabled': data['enabled']}},
        upsert=True
    )
    
    result = {'command': command_name, 'enabled': data['enabled']}
    return jsonify(result)
