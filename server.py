from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from utils.firebase_admin_init import init_firebase, verify_id_token, get_firestore_client, get_storage_bucket
from routes.chat import chat_bp
from routes.quiz import quiz_bp
from routes.upload import upload_bp
from routes.auth import auth_bp

load_dotenv()
init_firebase()

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
app.register_blueprint(upload_bp, url_prefix='/api/upload')

@app.route('/')
def index():
    return jsonify({'message': 'LLM-LMS Python backend running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
