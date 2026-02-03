from flask import Flask, jsonify
from threading import Thread
from waitress import serve
import os

app = Flask('Bot')


def run():
    port = int(os.environ.get('PORT', 8080))
    serve(app,host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200