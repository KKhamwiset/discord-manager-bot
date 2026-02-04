import os
import asyncio
import requests
from flask import Blueprint, jsonify, request, current_app
from routes.auth import token_required

commands_bp = Blueprint('commands', __name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


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


@commands_bp.route('/')
@token_required
def list_commands():
    """List all available bot commands"""
    async def get_commands():
        db = current_app.db
        
        # Get command config from database
        config = await db.command_config.find({}).to_list(length=100)
        config_map = {c['command_name']: c for c in config}
        
        # Get live commands from bot
        bot_commands = get_available_commands()
        
        # Merge with config
        result = []
        for cmd in bot_commands:
            cmd_config = config_map.get(cmd['name'], {})
            result.append({
                'name': cmd['name'],
                'cog': cmd.get('cog', 'Unknown'),
                'description': cmd.get('description', ''),
                'aliases': cmd.get('aliases', []),
                'enabled': cmd_config.get('enabled', cmd.get('enabled', True)),
                'usage_count': cmd_config.get('usage_count', 0)
            })
        
        return result
    
    commands = run_async(get_commands())
    return jsonify({'commands': commands})


@commands_bp.route('/<command_name>', methods=['PATCH'])
@token_required
def update_command(command_name):
    """Enable/disable a command"""
    data = request.get_json()
    
    if 'enabled' not in data:
        return jsonify({'error': 'Missing enabled field'}), 400
    
    async def update():
        db = current_app.db
        
        await db.command_config.update_one(
            {'command_name': command_name},
            {'$set': {'enabled': data['enabled']}},
            upsert=True
        )
        
        return {'command': command_name, 'enabled': data['enabled']}
    
    result = run_async(update())
    return jsonify(result)


@commands_bp.route('/logs')
@token_required
def command_logs():
    """Get recent command execution logs"""
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 100)  # Cap at 100
    
    async def get_logs():
        db = current_app.db
        
        cursor = db.command_logs.find({}).sort('timestamp', -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        return [{
            'command': log.get('command_name'),
            'user': log.get('user_name'),
            'channel': log.get('channel_name'),
            'timestamp': log.get('timestamp'),
            'success': log.get('success', True)
        } for log in logs]
    
    logs = run_async(get_logs())
    return jsonify({'logs': logs})
