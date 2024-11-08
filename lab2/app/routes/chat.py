from flask import Blueprint, request, jsonify
from app import db
from app.models import Product

chat_blueprint = Blueprint('chat', __name__)