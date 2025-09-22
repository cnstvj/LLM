from flask import Blueprint, request, jsonify
import os, requests, json, re
from utils.firebase_admin_init import verify_id_token, get_firestore_client
from google.cloud import firestore

quiz_bp = Blueprint('quiz', __name__)

# Default to OpenRouter if available, otherwise Ollama local
LLM_API_URL = os.environ.get('LLM_API_URL') or "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')


def call_llm(messages, model="openchat/openchat-3.5-0106", max_tokens=800, temperature=0.3):
    headers = {"Content-Type": "application/json"}

    if "openrouter.ai" in LLM_API_URL:
        # Use OpenRouter
        if not OPENROUTER_API_KEY:
            return {"error": "Missing OPENROUTER_API_KEY environment variable"}
        headers.update({
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "LLM-LMS"
        })

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

    else:
        # Use Ollama local
        payload = {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature}
        }

    try:
        response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": "LLM API request failed",
            "details": str(e),
            "status_code": getattr(e.response, "status_code", None),
            "response_text": getattr(e.response, "text", None),
            "url": LLM_API_URL
        }


def extract_json(raw: str):
    if not raw:
        raise ValueError("Empty LLM response")

    raw = raw.strip()
    if raw.startswith(""):
        raw = re.sub(r"(?:json)?", "", raw).strip("` \n")

    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        raise ValueError("No JSON array found in output")

    json_str = match.group(0)

    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    return json.loads(json_str)


@quiz_bp.route("/", methods=["POST"])
def generate_quiz():
    # --- Authentication ---
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    try:
        if token and token != "mock-jwt-token":
            decoded = verify_id_token(token)
            uid = decoded.get("uid")
        else:
            uid = "mock-user"
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    # --- Input ---
    data = request.get_json() or {}
    text = data.get("text") or data.get("context")
    n = int(data.get("n", 5))

    if not text or len(text.strip()) < 3:
        return jsonify({"error": "Please provide a topic or passage"}), 400
    if n < 1 or n > 20:
        return jsonify({"error": "Number of questions must be between 1 and 20"}), 400

    # --- LLM prompt ---
    system = {
        "role": "system",
        "content": "You are an educational content generator. Produce multiple-choice questions with one correct answer and three distractors."
    }
    user_prompt = {
        "role": "user",
        "content": (
            f"Create {n} multiple-choice questions (A-D) based on the following input. "
            "If it's a passage, generate questions directly from it. "
            "If it's only a topic, first create a short educational summary and then generate questions. "
            "For each question, mark the correct choice letter and provide a one-line explanation. "
            "Respond ONLY with a JSON array in this format, with no explanation or extra text: "
            '[{"question": "...", "options": ["A ...", "B ...", "C ...", "D ..."], "answer": "A", "explanation": "..."}]'
            f"\n\nInput:\n{text}"
        )
    }
    messages = [system, user_prompt]

    # --- Call LLM ---
    try:
        resp = call_llm(messages)
        if "error" in resp:
            return jsonify(resp), 500

        if "message" in resp and "content" in resp["message"]:
            raw = resp["message"]["content"]
        elif "choices" in resp and resp["choices"]:
            raw = resp["choices"][0].get("message", {}).get("content", "")
        else:
            return jsonify({"error": "LLM returned empty response", "raw_llm_output": resp}), 500

        quiz = extract_json(raw)
        if not isinstance(quiz, list) or not quiz:
            return jsonify({"error": "Quiz format invalid", "raw_llm_output": raw}), 422
    except Exception as e:
        return jsonify({
            "error": "Failed to parse quiz JSON",
            "details": str(e),
            "raw_llm_output": raw if "raw" in locals() else ""
        }), 422

    # --- Save to Firestore ---
    try:
        db = get_firestore_client()
        db.collection("users").document(uid).collection("generatedQuizzes").add({
            "quiz": quiz,
            "createdAt": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"⚠ Firestore save failed: {e}")

    return jsonify({"quiz": quiz}), 200