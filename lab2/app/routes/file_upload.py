from flask import Blueprint, request, jsonify
import json

file_handler = Blueprint('file_handler', __name__)

@file_handler.route('/upload-json', methods=['POST'])
def upload_json_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.json'):
        try:
            file_data = json.load(file)
            return jsonify({'message': 'File uploaded successfully', 'data': file_data}), 200
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON file'}), 400
    else:
        return jsonify({'error': 'File is not a JSON'}), 400