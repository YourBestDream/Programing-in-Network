# Unsafest shit thatI have ever done but will be sufficient for this lab

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@db/lab_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'supersecretkey'
