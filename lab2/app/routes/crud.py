from flask import Blueprint, request, jsonify
from app.utils.db import db
from app.models.data_model import Resource

crud_blueprint = Blueprint('crud', __name__)

@crud_blueprint.route('/resource', methods=['POST'])
def create_resource():
    data = request.json
    resource = Resource(name=data['name'], description=data['description'])
    db.session.add(resource)
    db.session.commit()
    return jsonify({'message': 'Resource created'}), 201

@crud_blueprint.route('/resource', methods=['GET'])
def get_resources():
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 5))
    resources = Resource.query.offset(offset).limit(limit).all()
    return jsonify([{'id': r.id, 'name': r.name, 'description': r.description} for r in resources])

@crud_blueprint.route('/resource/<int:id>', methods=['PUT'])
def update_resource(id):
    data = request.json
    resource = Resource.query.get_or_404(id)
    resource.name = data['name']
    resource.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Resource updated'})

@crud_blueprint.route('/resource/<int:id>', methods=['DELETE'])
def delete_resource(id):
    resource = Resource.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({'message': 'Resource deleted'})
