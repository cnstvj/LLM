# LLM-LMS Backend (Python / Flask)

This is a Python-based backend for the Personalized LLM-powered Learning Management System.

## Features
- Chat endpoint (proxy to OpenRouter LLM API)
- Quiz generation endpoint (OpenRouter LLM API)
- File upload to Firebase Storage
- Simple mock auth route for demo purposes
- Firebase Admin integration for Firestore & Storage (logging & file storage)

## Quickstart

1. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate   # on Windows use `venv\\Scripts\\activate`
pip install -r requirements.txt
```

2. Create a Firebase service account JSON and set `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env`.
3. Copy `.env.example` to `.env` and fill values (`LLM_API_URL`, `FIREBASE_SERVICE_ACCOUNT_PATH`, `FIREBASE_STORAGE_BUCKET`, etc.).
## Using OpenRouter (Cloud LLM API)

This backend now uses [OpenRouter](https://openrouter.ai/) to access open-source LLMs via a free/public API.

1. **Sign up at [OpenRouter](https://openrouter.ai/)**
2. **Get your API key from the OpenRouter dashboard.**
3. **Set your API key in `.env` as `OPENROUTER_API_KEY`.**
4. **Set `LLM_API_URL` to `https://openrouter.ai/api/v1/chat/completions` (already set in `.env.example`).**
5. **You can change the model used in the code (default: `mistralai/Mixtral-8x7B-Instruct-v0.1`).**
4. Run server:
```bash
python server.py
```

## Endpoints
- `GET /` - health check
- `POST /api/auth/login` - mock login
- `POST /api/chat` - body: { question, contextText } with Authorization: Bearer <id-token or mock-jwt-token>
- `POST /api/quiz` - body: { text, n }
- `POST /api/upload` - form-data file upload (Authorization header required)

## Notes
- This is designed for hackathon/demo use. For production, harden auth, validation, and error handling.
