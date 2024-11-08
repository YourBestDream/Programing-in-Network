from flask import Flask
from flask_socketio import SocketIO
from .utils.db import init_db
from .routes import register_routes

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Initialize database
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    # Initialize SocketIO
    socketio.init_app(app)
    
    return app
