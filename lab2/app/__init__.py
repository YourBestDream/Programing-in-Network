from flask import Flask
from .utils.db import init_db
from .routes import register_routes
from .socketio_instance  import socketio

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
