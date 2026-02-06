from flask import Flask, jsonify
from threading import Thread
from waitress import serve
import os

app = Flask('Bot')
bot_instance = None 

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
            "member_count": guild.member_count,
            "region": str(guild.preferred_locale)
        })
    return jsonify({"guilds": guilds_list}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200