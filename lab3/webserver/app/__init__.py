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

    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_user = os.getenv('POSTGRES_USER', 'user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'password')
    db_name = os.getenv('POSTGRES_DB', 'lab_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app, supports_credentials=True)

    from .routes.crud import crud_blueprint
    from .routes.file_upload import file_handler
    app.register_blueprint(crud_blueprint, url_prefix='/')
    app.register_blueprint(file_handler, url_prefix='/')

    return app
