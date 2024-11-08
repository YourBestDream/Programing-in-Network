from flask import Blueprint, request, jsonify
from app import db
from app.models import Product
from sqlalchemy import inspect


crud_blueprint = Blueprint('crud', __name__)

@crud_blueprint.route('/resource', methods=['POST'])
def create_resource():
    data = request.json
    resource = Product(product_name=data['name'], price=data['price'], currency = data['currency'], specifications = data['specifications'])
    db.session.add(resource)
    db.session.commit()
    return jsonify({'message': 'Product created'}), 201

@crud_blueprint.route('/resource', methods=['GET'])
def get_resources():
    resource_id = request.args.get('id')
    name = request.args.get('name')
    if resource_id:
        resource = Product.query.get_or_404(resource_id)
        return jsonify({'id': resource.id, 'name': resource.product_name, 'price': resource.price, 'currency': resource.currency, 'specifications': resource.specifications, 'timestamp': resource.scrape_time_utc})
    elif name:
        resources = Product.query.filter_by(name=name).all()
        return jsonify([{'id': r.id, 'name': r.product_name, 'price': r.price, 'currency': r.currency, 'specifications': r.specifications, 'timestamp': r.scrape_time_utc} for r in resources])
    else:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 5))
        resources = Product.query.offset(offset).limit(limit).all()
        return jsonify([{'id': r.id, 'name': r.product_name, 'price': r.price, 'currency': r.currency, 'specifications': r.specifications, 'timestamp': r.scrape_time_utc} for r in resources])

@crud_blueprint.route('/resource', methods=['PUT'])
def update_resource():
    resource_id = request.args.get('id')
    if not resource_id:
        return jsonify({'error': 'ID query parameter is required'}), 400
    data = request.json
    resource = Product.query.get_or_404(resource_id)
    resource.name = data.get('name', resource.product_name)
    resource.price = data.get('price', resource.price)
    resource.currency = data.get('currency', resource.currency)
    resource.specifications = data.get('specifications', resource.specifications)
    db.session.commit()
    return jsonify({'message': 'Product updated'})

@crud_blueprint.route('/resource', methods=['DELETE'])
def delete_resource():
    resource_id = request.args.get('id')
    if not resource_id:
        return jsonify({'error': 'ID query parameter is required'}), 400
    resource = Product.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})


# for testing purposes
@crud_blueprint.route('/tables', methods=['GET'])
def list_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return jsonify({'tables': tables})