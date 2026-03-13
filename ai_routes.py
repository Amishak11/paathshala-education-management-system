import time
import requests
from flask import Blueprint, request, jsonify, session

ai_bp = Blueprint("ai_bp", __name__, url_prefix="/student")


OLLAMA_MODEL = "gemma3:4b"   
OLLAMA_URL = "http://localhost:11434/api/generate"


_REQ_LOG = {}  # { session_key: [timestamps...] }

def _session_key() -> str:
    return str(session.get("student_id") or session.get("student_name") or request.remote_addr)

def _rate_limited(limit=100, window_sec=300) -> bool:
    key = _session_key()
    now = time.time()
    arr = _REQ_LOG.get(key, [])
    arr = [t for t in arr if now - t < window_sec]
    if len(arr) >= limit:
        _REQ_LOG[key] = arr
        return True
    arr.append(now)
    _REQ_LOG[key] = arr
    return False



def build_prompt(feature: str, subject: str, text: str) -> str:
    subject = (subject or "General").strip()
    text = (text or "").strip()

    common_rules = f"""
You are Paathshala AI, a friendly tutor for Indian school students (class 6–12).
Subject: {subject}

Rules:
- Use simple English (easy words).
- Be accurate and not too long.
- Use bullet points when helpful.
- Add one real-life example if possible.
"""

    if feature == "explain":
        return common_rules + f"""
Task: Explain the student's doubt step-by-step.
End with 2 quick check questions.

Student doubt:
{text}
"""

    if feature == "easy":
        return common_rules + f"""
Task: Explain the student's doubt in VERY EASY way like teaching a beginner.
- Use short lines
- Use a daily-life analogy
End with 2 quick check questions.

Student doubt:
{text}
"""

    if feature == "quiz":
        return common_rules + f"""
Task: Create a small quiz from the student's topic.
Return:
- 3 MCQs (A/B/C/D)
- Answer key at the end
- 2 short questions

Topic:
{text}
"""

    if feature == "summary":
        return common_rules + f"""
Task: Summarize these notes into easy points.
Return:
- Title (1 line)
- 8–12 bullet points summary
- 5 key terms with 1-line meaning each

Notes:
{text}
"""

    if feature == "flashcards":
        return common_rules + f"""
Task: Create exactly 10 flashcards from the notes.
Format STRICTLY:
1) Q: ...
   A: ...
...
10) Q: ...
    A: ...

Notes:
{text}
"""

    if feature == "mcq":
        return common_rules + f"""
Task: Create exactly 5 MCQs from the notes.
Format:
1) Question
   A) ...
   B) ...
   C) ...
   D) ...
Answer: B

Repeat for 5 questions.

Notes:
{text}
"""

    return common_rules + f"\nText:\n{text}\n"



@ai_bp.route("/debug-ai", methods=["GET"])
def debug_ai():
    try:
        tags = requests.get("http://localhost:11434/api/tags", timeout=5).json()
        models = [m.get("name") for m in tags.get("models", [])]
        return jsonify({
            "ollama_running": True,
            "available_models": models,
            "current_model": OLLAMA_MODEL,
            "current_model_available": OLLAMA_MODEL in models
        })
    except Exception as e:
        return jsonify({
            "ollama_running": False,
            "error": str(e),
            "hint": "Start Ollama app and ensure a model is downloaded (example: ollama run gemma3:4b)."
        }), 500



@ai_bp.route("/ai", methods=["POST"])
def student_ai():
    # login check
    if not session.get("student_name") and not session.get("student_id"):
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    # rate limit
    if _rate_limited(limit=100, window_sec=300):
        return jsonify({"ok": False, "error": "Too many requests. Please try again later."}), 429

    data = request.get_json(silent=True) or {}
    feature = (data.get("feature") or "").strip().lower()
    subject = (data.get("subject") or "General").strip()
    text = (data.get("text") or "").strip()

    allowed = {"explain", "easy", "quiz", "summary", "flashcards", "mcq"}
    if feature not in allowed:
        return jsonify({"ok": False, "error": "Invalid feature"}), 400

    if not text:
        return jsonify({"ok": False, "error": "Please enter text first."}), 400

    if len(text) > 2500:
        return jsonify({"ok": False, "error": "Too long! Please keep it under 2500 characters."}), 400

    prompt = build_prompt(feature, subject, text)

    try:
        # ✅ Ollama request
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4
                }
            },
            timeout=120
        )

        if r.status_code != 200:
            return jsonify({
                "ok": False,
                "error": f"Ollama error ({r.status_code}): {r.text}"
            }), 500

        result = (r.json().get("response") or "").strip()
        if not result:
            result = "⚠️ I couldn't generate a response. Please try again."

        return jsonify({"ok": True, "result": result})

    except requests.exceptions.ConnectionError:
        return jsonify({
            "ok": False,
            "error": f"⚠️ Ollama is not running. Open Ollama app and run the model once: ollama run {OLLAMA_MODEL}"
        }), 500

    except requests.exceptions.Timeout:
        return jsonify({
            "ok": False,
            "error": "⚠️ Ollama took too long to respond. Try a shorter question or use a smaller model like phi3."
        }), 504

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500