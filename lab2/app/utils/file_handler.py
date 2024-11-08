from flask import request, jsonify

def handle_file_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file:
        # Process the file (e.g., save it or process contents)
        file.save(f'uploads/{file.filename}')
        return jsonify({'message': 'File uploaded successfully'})
    return jsonify({'error': 'File upload failed'}), 400
