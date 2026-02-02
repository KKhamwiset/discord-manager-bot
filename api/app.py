import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    app.config['MONGO_DB'] = os.getenv('MONGO_DB', 'discord_bot_db')
    
    # Discord OAuth2 config
    app.config['DISCORD_CLIENT_ID'] = os.getenv('DISCORD_CLIENT_ID')
    app.config['DISCORD_CLIENT_SECRET'] = os.getenv('DISCORD_CLIENT_SECRET')
    app.config['OAUTH_REDIRECT_URI'] = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:3000/api/auth/callback')
    
    # CORS - allow Next.js frontend
    CORS(app, origins=[
        'http://localhost:3000',
        os.getenv('FRONTEND_URL', 'http://localhost:3000')
    ], supports_credentials=True)
    
    # MongoDB connection
    mongo_client = AsyncIOMotorClient(
        app.config['MONGO_URI'],
        serverSelectionTimeoutMS=5000,
        maxPoolSize=20
    )
    app.db = mongo_client[app.config['MONGO_DB']]
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.stats import stats_bp
    from routes.commands import commands_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(commands_bp, url_prefix='/api/commands')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/')
    def home():
        return {'message': 'Discord Bot API', 'version': '1.0.0'}, 200
    
    return app


if __name__ == '__main__':
    from waitress import serve
    app = create_app()
    port = int(os.getenv('API_PORT', 5000))
    print(f"🚀 Flask API running on port {port}")
    serve(app, host='0.0.0.0', port=port)
