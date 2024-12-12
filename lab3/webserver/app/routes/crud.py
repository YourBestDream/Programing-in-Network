from flask import Blueprint, request, jsonify
from app import db
from app.models import Product
from sqlalchemy import inspect
import json
from datetime import datetime

crud_blueprint = Blueprint('crud', __name__)

@crud_blueprint.route('/resource', methods=['POST'])
def create_resource():
    data = request.get_json()
    # The manager sends data in {"data": "..."} format
    # Parse the received data (could be str(result))
    try:
        received = data.get("data")
        # Try to parse it if it's JSON-like
        # If it’s a string from scraped_data, parse it
        parsed = json.loads(received.replace("'", '"')) if isinstance(received, str) else received
        # Let's assume parsed['filtered_products'] exists
        if isinstance(parsed, dict) and 'filtered_products' in parsed:
            for p in parsed['filtered_products']:
                product = Product(
                    product_name = p['product_name'],
                    price = p['price'],
                    currency = p['currency'],
                    specifications = p.get('specifications', []),
                    scrape_time_utc = datetime.fromisoformat(p['scrape_time_utc'])
                )
                db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Products created'}), 201
        else:
            # Maybe it's FTP data or another format, handle accordingly
            # For simplicity: If it's not in the expected format, just store as one product
            product = Product(
                product_name="Generic",
                price=0,
                currency="eur",
                specifications=[],
                scrape_time_utc=datetime.utcnow()
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Single product created from FTP data'}), 201
    except Exception as e:
        print("Error processing resource data:", e)
        return jsonify({'error': 'Invalid data format'}), 400

@crud_blueprint.route('/resource', methods=['GET'])
def get_resources():
    resources = Product.query.all()
    return jsonify([
        {
            'id': r.id, 
            'name': r.product_name, 
            'price': r.price, 
            'currency': r.currency, 
            'specifications': r.specifications, 
            'timestamp': r.scrape_time_utc.isoformat()
        } for r in resources
    ])

@crud_blueprint.route('/tables', methods=['GET'])
def list_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return jsonify({'tables': tables})
