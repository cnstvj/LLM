from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

# Mock login - useful for quick demos without Firebase client setup
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if email and password:
        # Return a mock token and uid - replace with Firebase Auth client flow in production
        return jsonify({'token': 'mock-jwt-token', 'uid': email}), 200
    return jsonify({'error': 'Missing credentials'}), 400
