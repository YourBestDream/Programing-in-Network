from flask import Blueprint, request, jsonify
from app.utils.db import db
from app.models import Product

crud_blueprint = Blueprint('crud', __name__)

@crud_blueprint.route('/resource', methods=['POST'])
def create_resource():
    data = request.json
    resource = Product(name=data['name'], description=data['description'])
    db.session.add(resource)
    db.session.commit()
    return jsonify({'message': 'Product created'}), 201

@crud_blueprint.route('/resource', methods=['GET'])
def get_resources():
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 5))
    resources = Product.query.offset(offset).limit(limit).all()
    return jsonify([{'id': r.id, 'name': r.name, 'description': r.description} for r in resources])

@crud_blueprint.route('/resource/<int:id>', methods=['PUT'])
def update_resource(id):
    data = request.json
    resource = Product.query.get_or_404(id)
    resource.name = data['name']
    resource.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Product updated'})

@crud_blueprint.route('/resource/<int:id>', methods=['DELETE'])
def delete_resource(id):
    resource = Product.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})
