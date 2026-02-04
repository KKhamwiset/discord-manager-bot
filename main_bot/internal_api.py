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

@app.route('/is_ready', methods=['GET'])
def is_ready():
    ready = bot_instance.is_ready() if bot_instance else False
    return jsonify({"is_ready": ready}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200