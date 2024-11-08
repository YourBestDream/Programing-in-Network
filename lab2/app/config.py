# Unsafest shit thatI have ever done but will be sufficient for this lab
import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'password')}@db/"
        f"{os.getenv('POSTGRES_DB', 'lab_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
