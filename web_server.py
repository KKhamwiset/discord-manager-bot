from flask import Flask
from threading import Thread

app = Flask('General เบ๊ Bot')
@app.route('/')
def home():
    return "General เบ๊ Bot is running!"

def run(): 
    app.run(host='0.0.0.0', port=8080) 

def keep_alive():
    t = Thread(target=run)
    t.start()