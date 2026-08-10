from flask import Flask, jsonify, request
from threading import Thread
from waitress import serve
import os
import asyncio
import concurrent.futures

import discord

app = Flask('Bot')
bot_instance = None 


class PermissionSubjectNotFound(Exception):
    pass

def set_bot(bot):
    """Set the bot instance so Flask can check its status"""
    global bot_instance
    bot_instance = bot


def run():
    port = int(os.environ.get('PORT', 8080))
    serve(app,host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()


async def _resolve_permission_payload(guild_id: int, user_id: int):
    guild = bot_instance.get_guild(guild_id)
    if guild is None:
        try:
            guild = await bot_instance.fetch_guild(guild_id)
        except discord.NotFound as exc:
            raise PermissionSubjectNotFound from exc
        if guild is None:
            raise PermissionSubjectNotFound

    # Application ownership is an explicit override for the configured guild.
    # Resolve it before guild membership so the bot owner is not accidentally
    # denied merely because they are not cached as a member of that guild.
    is_owner = bool(await bot_instance.is_owner(discord.Object(id=user_id)))
    member = guild.get_member(user_id)
    if member is None:
        if is_owner:
            return {
                "is_owner": True,
                "administrator": False,
                "manage_guild": False,
                "manage_roles": False,
                "manage_threads": False,
            }
        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound as exc:
            raise PermissionSubjectNotFound from exc
        if member is None:
            raise PermissionSubjectNotFound

    permissions = member.guild_permissions
    return {
        "is_owner": is_owner,
        "administrator": bool(permissions.administrator),
        "manage_guild": bool(permissions.manage_guild),
        "manage_roles": bool(permissions.manage_roles),
        "manage_threads": bool(permissions.manage_threads),
    }


@app.route('/',methods=['GET'])
def home():
    return jsonify({"message": "Bot is running", "instance": os.getenv("INSTANCE")}), 200

@app.route('/commands',methods=['GET'])
def get_commands():
    if not bot_instance:
        return jsonify({"error": "Bot instance not ready"}), 503
        
    commands_list = []
    for command in bot_instance.commands:
        commands_list.append({
            "name": command.name,
            "description": command.help or "No description",
            "aliases": command.aliases,
            "hidden": command.hidden,
            "cog": command.cog_name,
            "enabled": command.enabled
        })
    return jsonify({"commands": commands_list}), 200


@app.route('/is_ready', methods=['GET'])
def is_ready():
    ready = bot_instance.is_ready() if bot_instance else False
    return jsonify({"is_ready": ready}), 200


@app.route('/permissions', methods=['GET'])
def get_permissions():
    raw_user_id = request.args.get('user_id', '')
    try:
        user_id = int(raw_user_id)
        if user_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id parameter"}), 400

    raw_guild_id = os.getenv("GUILD_ID")
    try:
        guild_id = int(raw_guild_id)
        if guild_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Permission authority unavailable"}), 503

    try:
        if not bot_instance or not bot_instance.is_ready():
            return jsonify({"error": "Permission authority unavailable"}), 503
        loop = bot_instance.loop
        if loop.is_closed() or not loop.is_running():
            return jsonify({"error": "Permission authority unavailable"}), 503
        future = asyncio.run_coroutine_threadsafe(
            _resolve_permission_payload(guild_id, user_id),
            loop,
        )
        return jsonify(future.result(timeout=5)), 200
    except PermissionSubjectNotFound:
        return jsonify({"error": "Guild member not found"}), 404
    except (concurrent.futures.TimeoutError, discord.HTTPException, RuntimeError):
        return jsonify({"error": "Permission authority unavailable"}), 503
    except Exception:
        app.logger.exception("Internal permission lookup failed")
        return jsonify({"error": "Permission authority unavailable"}), 503

@app.route('/guilds', methods=['GET'])
def get_guilds():
    if not bot_instance:
        return jsonify({"error": "Bot instance not ready"}), 503
    guilds_list = []
    for guild in bot_instance.guilds:
        guilds_list.append({
            "id": str(guild.id),
            "name": guild.name,
            "icon": guild.icon.key if guild.icon else None,
            "members": guild.member_count,
            "region": str(guild.preferred_locale)
        })
    return jsonify({"guilds": guilds_list}), 200

@app.route('/channel_name',methods=['GET'])
def get_channel_name():
    id = request.args.get('id')
    if not id:
         return jsonify({"error": "Missing id parameter"}), 400
         
    if not bot_instance:
        return jsonify({"error": "Bot instance not ready"}), 503
    
    guild_id = os.getenv("GUILD_ID")
    if not guild_id:
        return jsonify({"error": "GUILD_ID not set"}), 500
        
    guild = bot_instance.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
        
    channel = guild.get_channel(int(id)) or guild.get_thread(int(id))

    if not channel:
        try:
             future = asyncio.run_coroutine_threadsafe(guild.fetch_channel(int(id)), bot_instance.loop)
             channel = future.result(timeout=5)
        except Exception as e:
             message = f"Failed to fetch channel {id}: {e}"
             print(message)
    
    if not channel:
        return jsonify({"error": "Channel not found"}), 404
    return jsonify({"name": channel.name}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200
