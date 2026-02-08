import os
import requests
from flask import Blueprint, jsonify, request, current_app
from routes.auth import token_required

channel_bp = Blueprint('channel', __name__)

BOT_INTERNAL_URL = os.getenv('BOT_INTERNAL_URL', 'http://bot:8080')

@channel_bp.route('/', methods=['GET'])
@token_required
def list_channels():
    "Get channel that are available for configuration"
    db = current_app.db
    channel = []
    guild_id = os.getenv('GUILD_ID')
    doc = db.guild_config.find_one({"_id": guild_id})
    if not doc:
        return jsonify({"channels": []}), 200
        
    allowed_channels = doc.get("allowed_channels", [])
    for channel_cfg in allowed_channels:
        c_id = channel_cfg.get('channel_id')
        mode = channel_cfg.get('cmd_mode')
        if not c_id:
            continue
            
        try:
             resp = requests.get(f'{BOT_INTERNAL_URL}/channel_name?id={c_id}', timeout=2)
             if resp.status_code == 200:
                 name = resp.json().get('name')
                 allowed_commands = channel_cfg.get('allowed_commands', [])
                 channel.append({"id": c_id, "name": name, "allowed_commands": allowed_commands, "cmd_mode": mode})
             else:
                 channel.append({"id": c_id, "name": "Unknown Channel", "allowed_commands": [], "cmd_mode": ""})
        except Exception as e:
             current_app.logger.warning(f"Failed to fetch name for channel {c_id}: {e}")
             channel.append({"id": c_id, "name": "Unknown Channel", "allowed_commands": [], "cmd_mode": ""})

    return jsonify({"channels": channel}), 200


@channel_bp.route('/<channel_id>', methods=['PATCH'])
@token_required
def update_channel_commands(channel_id):
    """Add or remove a command from a channel's allowed list"""
    data = request.get_json()
    action = data.get('action')
    command = data.get('command')
    
    if not action or not command:
        return jsonify({'error': 'Missing action or command'}), 400
        
    if action not in ['add', 'remove']:
        return jsonify({'error': 'Invalid action'}), 400
        
    db = current_app.db
    guild_id = os.getenv('GUILD_ID')
    
    update_query = {}
    if action == 'add':
        update_query = {'$addToSet': {'allowed_channels.$.allowed_commands': command}}
    else:
        update_query = {'$pull': {'allowed_channels.$.allowed_commands': command}}
        
    result = db.guild_config.update_one(
        {'_id': guild_id, 'allowed_channels.channel_id': channel_id},
        update_query
    )
    
    if result.modified_count == 0:
        return jsonify({'error': 'Channel not found or no changes made'}), 404
        
    return jsonify({'success': True, 'action': action, 'command': command}), 200
