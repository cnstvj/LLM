from flask import Blueprint, request, jsonify
import os, requests
from utils.firebase_admin_init import verify_id_token, get_firestore_client
from firebase_admin import firestore

chat_bp = Blueprint('chat', __name__)


LLM_API_URL = os.environ.get('LLM_API_URL', 'http://localhost:11434/api/chat')


def call_llm(messages, model='mistralai/Mixtral-8x7B-Instruct-v0.1', max_tokens=400, temperature=0.2):
    api_key = os.environ.get('OPENROUTER_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost',  # required by OpenRouter
        'X-Title': 'LLM-LMS'
    }
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature
    }
    response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

@chat_bp.route('/', methods=['POST'])
def chat():
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

    data = request.get_json() or {}
    question = data.get('question', '').strip()
    context = data.get('contextText') or data.get('context') or ''

    if not question:
        return jsonify({'error': 'Question required'}), 400

    system = {
        'role': 'system',
        'content': 'You are an AI tutor. Answer concisely and step-by-step. Use only the provided context.'
    }
    user_msg = {
        'role': 'user',
        'content': f"Context:\n{context}\n\nQuestion:\n{question}" if context else f"Question:\n{question}\n\nNote: No context provided."
    }
    messages = [system, user_msg]



    try:
        resp = call_llm(messages, max_tokens=500)
        # Ollama returns {'message': {'content': ...}} or {'choices': ...}
        if 'message' in resp and 'content' in resp['message']:
            answer = resp['message']['content']
        elif 'choices' in resp and resp['choices']:
            answer = resp['choices'][0].get('message', {}).get('content', None)
        else:
            answer = None
        if not answer:
            return jsonify({'error': 'No answer returned from LLM'}), 200
    except Exception as e:
        return jsonify({'error': 'LLM request failed', 'details': str(e)}), 500


    # Log chat to Firestore only if answer is valid
    try:
        db = get_firestore_client()
        db.collection('users').document(uid).collection('chats').add({
            'question': question,
            'answer': answer,
            'createdAt': getattr(firestore, 'SERVER_TIMESTAMP', None)
        })
    except Exception:
        # Log or handle Firestore errors as needed
        pass

    return jsonify({'answer': answer})
