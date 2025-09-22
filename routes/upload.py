from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os, io, uuid
from utils.firebase_admin_init import verify_id_token, get_storage_bucket, get_firestore_client

upload_bp = Blueprint('upload', __name__)
ALLOWED_EXT = {'pdf', 'txt', 'md'}

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@upload_bp.route('/', methods=['POST'])
def upload_file():
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
    try:
        if token and token != 'mock-jwt-token':
            decoded = verify_id_token(token)
            uid = decoded.get('uid')
        else:
            uid = 'mock-user'
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    filename = secure_filename(file.filename)
    blob_name = f'uploads/{uid}/{uuid.uuid4().hex}_{filename}'
    bucket = get_storage_bucket()
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file.read(), content_type=file.content_type)
    # Create signed url valid for 7 days
    url = blob.generate_signed_url(version='v4', expiration=604800)

    # Save metadata
    try:
        db = get_firestore_client()
        db.collection('users').document(uid).collection('uploads').add({
            'name': filename,
            'path': blob_name,
            'url': url
        })
    except Exception:
        pass

    return jsonify({'message': 'Uploaded', 'url': url})
