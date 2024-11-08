import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')

    db_host = os.getenv('POSTGRES_HOST', 'localhost')  # Default to 'localhost'

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'password')}@{db_host}:5432/"
        f"{os.getenv('POSTGRES_DB', 'lab_db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app, supports_credentials=True)

    from .routes.chat import chat_blueprint
    from .routes.crud import crud_blueprint

    app.register_blueprint(chat_blueprint, url_prefix='/')
    app.register_blueprint(crud_blueprint, url_prefix='/')

    return app
