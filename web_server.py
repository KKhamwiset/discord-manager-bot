from flask import Flask , jsonify
from threading import Thread
import os
app = Flask('General เบ๊ Bot')
@app.route('/')
def home():
    return "General เบ๊ Bot is running!"

def run(): 
    port = int(os.environ.get('PORT', 8080)) 
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200
