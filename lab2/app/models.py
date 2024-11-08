from . import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String, nullable=False)
    specifications = db.Column(db.JSON, nullable=True)  # Stores list as JSON
    scrape_time_utc = db.Column(db.DateTime, default=datetime.utcnow)