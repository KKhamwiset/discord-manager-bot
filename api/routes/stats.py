import os
import asyncio
from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from routes.auth import token_required

stats_bp = Blueprint('stats', __name__)


def run_async(coro):
    """Helper to run async code in sync Flask context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@stats_bp.route('/overview')
@token_required
def overview():
    """Get bot and server overview statistics"""
    async def get_stats():
        db = current_app.db
        
        # Get guild info from database (stored by bot)
        guild_info = await db.guild_info.find_one({'guild_id': os.getenv('GUILD_ID')})
        
        # Get command usage stats
        command_logs = await db.command_logs.count_documents({})
        
        # Get recent activity (last 24h)
        yesterday = datetime.now(timezone.utc).timestamp() - 86400
        recent_commands = await db.command_logs.count_documents({
            'timestamp': {'$gte': yesterday}
        })
        
        return {
            'guild': guild_info or {},
            'total_commands': command_logs,
            'commands_24h': recent_commands,
            'bot_status': 'online'  # Could be enhanced with actual bot status
        }
    
    stats = run_async(get_stats())
    return jsonify(stats)


@stats_bp.route('/commands')
@token_required
def command_stats():
    """Get command usage statistics"""
    async def get_command_stats():
        db = current_app.db
        
        # Aggregate command usage
        pipeline = [
            {'$group': {
                '_id': '$command_name',
                'count': {'$sum': 1},
                'last_used': {'$max': '$timestamp'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 20}
        ]
        
        cursor = db.command_logs.aggregate(pipeline)
        stats = await cursor.to_list(length=20)
        
        return [{
            'command': s['_id'],
            'usage_count': s['count'],
            'last_used': s.get('last_used')
        } for s in stats]
    
    stats = run_async(get_command_stats())
    return jsonify({'commands': stats})


@stats_bp.route('/activity')
@token_required
def activity():
    """Get activity data for charts (last 7 days)"""
    async def get_activity():
        db = current_app.db
        
        # Get command usage per day for last 7 days
        week_ago = datetime.now(timezone.utc).timestamp() - (7 * 86400)
        
        pipeline = [
            {'$match': {'timestamp': {'$gte': week_ago}}},
            {'$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': {'$toDate': {'$multiply': ['$timestamp', 1000]}}
                    }
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        cursor = db.command_logs.aggregate(pipeline)
        daily_stats = await cursor.to_list(length=7)
        
        return [{
            'date': s['_id'],
            'commands': s['count']
        } for s in daily_stats]
    
    activity_data = run_async(get_activity())
    return jsonify({'activity': activity_data})
