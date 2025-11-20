from flask import Flask, jsonify
from threading import Thread
from waitress import serve
import os

app = Flask('Bot')

@app.route('/')
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>General เบ๊ Bot Status</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
        
        <!-- Custom style for the specific pulsing glow effect -->
        <style>
            :root {
                --teal-glow: #03dac6;
            }
            /* Set Inter as the primary font */
            body {
                font-family: 'Inter', sans-serif;
            }
            .pulse-indicator {
                animation: custom-pulse 1.5s infinite;
            }
            @keyframes custom-pulse {
                0% { box-shadow: 0 0 0 0 rgba(3, 218, 198, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(3, 218, 198, 0); }
                100% { box-shadow: 0 0 0 0 rgba(3, 218, 198, 0); }
            }
        </style>
    </head>
    
    <!-- Applying all styles via Tailwind classes -->
    <body class="bg-gray-900 text-gray-100 flex items-center justify-center min-h-screen p-4">
        <div class="container bg-gray-800 p-8 md:p-14 rounded-xl shadow-2xl text-center max-w-lg w-full">
            
            <!-- Title -->
            <div class="text-4xl md:text-5xl font-extrabold text-purple-400 mb-2">
                General เบ๊ Bot
            </div>
            <p class="text-lg text-gray-400 mb-8">
                Discord Bot Keep-Alive Service
            </p>

            <!-- Status Message -->
            <div class="status-message text-xl text-teal-400 mb-8">
                <span class="pulse-indicator inline-block w-4 h-4 rounded-full bg-teal-400 mr-2 align-middle"></span>
                Status: Operational and Awaiting Commands
            </div>
            
            <!-- Description -->
            <p class="text-sm text-gray-500 max-w-sm mx-auto">
                This HTTP server is dedicated to ensuring the bot remains connected 
                to Discord via a periodic ping from a service like Cron-Job.org.
            </p>

            <!-- Footer -->
            <div class="footer mt-6 text-xs text-gray-600">
                Health check endpoint: <code class="bg-gray-700 px-1 py-0.5 rounded">/status</code>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def run():
    port = int(os.environ.get('PORT', 8080))
    serve(app,host='0.0.0.0', port=port)

def keep_alive():
    """Starts the Flask web server in a background thread."""
    t = Thread(target=run)
    t.start()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running"}), 200