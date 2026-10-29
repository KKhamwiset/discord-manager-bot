import os
from datetime import datetime, timezone
import requests
from flask import Blueprint, jsonify, request, current_app
from routes.auth import permission_required, token_required

commands_bp = Blueprint('commands', __name__)

BOT_INTERNAL_URL = os.getenv('BOT_INTERNAL_URL', 'http://bot:8080')

PROTECTED_COMMANDS = {
    "help",
    "pause",
    "resume",
    "restart",
    "ping",
    "info",
}


def get_available_commands():
    """Get commands from the running bot via internal API"""
    try:
        response = requests.get(f'{BOT_INTERNAL_URL}/commands', timeout=5)
        if response.status_code == 200:
            return response.json().get('commands', [])
        return []
    except requests.RequestException:
        return []


def notify_bot_toggle(command_name: str, enabled: bool):
    """Notify the running bot instance of command toggle"""
    try:
        requests.post(
            f'{BOT_INTERNAL_URL}/commands/toggle',
            json={'command_name': command_name, 'enabled': enabled},
            timeout=3,
        )
    except requests.RequestException as e:
        current_app.logger.warning(f"Failed to notify bot of command toggle: {e}")


@commands_bp.route('/')
def list_commands():
    """List all available bot commands with persistent DB state merged"""
    bot_commands = get_available_commands()
    db = current_app.db

    # Fetch all stored configs from database
    db_configs = {}
    try:
        for doc in db.command_config.find({}):
            name = doc.get('command_name')
            if name:
                db_configs[name] = doc.get('enabled', True)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch command_config from DB: {e}")

    result = []
    for cmd in bot_commands:
        name = cmd['name']
        is_protected = name in PROTECTED_COMMANDS

        # Protected commands always enabled; otherwise prefer DB state over bot in-memory
        if is_protected:
            enabled = True
        elif name in db_configs:
            enabled = bool(db_configs[name])
        else:
            enabled = bool(cmd.get('enabled', True))

        result.append({
            'name': name,
            'cog': cmd.get('cog', 'Unknown'),
            'description': cmd.get('description', ''),
            'aliases': cmd.get('aliases', []),
            'hidden': cmd.get('hidden', False),
            'enable': enabled,
            'protected': is_protected,
        })

    return jsonify({'commands': result})


@commands_bp.route('/<command_name>', methods=['PATCH'])
@token_required
@permission_required('manage_guild')
def update_command(command_name):
    """Enable/disable a command"""
    if command_name in PROTECTED_COMMANDS:
        return jsonify({
            'error': f'Command "{command_name}" is a protected system command and cannot be disabled'
        }), 400

    data = request.get_json(silent=True) or {}
    if 'enabled' not in data:
        return jsonify({'error': 'Missing enabled field'}), 400

    enabled = bool(data['enabled'])
    db = current_app.db
    user_id = getattr(request, 'user', {}).get('user_id', 'unknown')

    db.command_config.update_one(
        {'command_name': command_name},
        {
            '$set': {
                'enabled': enabled,
                'updated_by': user_id,
                'updated_at': datetime.now(timezone.utc),
            }
        },
        upsert=True
    )

    # Notify running bot instance
    notify_bot_toggle(command_name, enabled)

    result = {'command': command_name, 'enabled': enabled, 'protected': False}
    return jsonify(result)
