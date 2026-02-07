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
        # channel_cfg is a dict with 'channel_id'
        c_id = channel_cfg.get('channel_id')
        if not c_id:
            continue
            
        try:
             resp = requests.get(f'{BOT_INTERNAL_URL}/channel_name?id={c_id}', timeout=2)
             if resp.status_code == 200:
                 name = resp.json().get('name')
                 channel.append({"id": c_id, "name": name})
             else:
                 channel.append({"id": c_id, "name": "Unknown Channel"})
        except Exception as e:
             current_app.logger.warning(f"Failed to fetch name for channel {c_id}: {e}")
             channel.append({"id": c_id, "name": "Unknown Channel"})

    return jsonify({"channels": channel}), 200
