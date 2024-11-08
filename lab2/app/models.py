from .utils.db import db
from sqlalchemy import Integer, String, JSON, Column, Float, DateTime
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    specifications = Column(JSON, nullable=True)  # Stores list as JSON
    scrape_time_utc = Column(DateTime, default=datetime.utcnow)