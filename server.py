import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
from groq import Groq

load_dotenv()

app = Flask(__name__, static_folder="public")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CONVERSATIONS_FILE = Path("data/conversations.json")
CONVERSATIONS_FILE.parent.mkdir(exist_ok=True)
if not CONVERSATIONS_FILE.exists():
    CONVERSATIONS_FILE.write_text("[]")

# Q&A pairs loaded from CSV at startup
QA_PAIRS = [
    {
        "question": "SMP-2310 / SMP-2200 / SMP-8100 / SMP-2300 / SMP-2400 要多少錢 ? 價格多少 ?",
        "answer": "若您對於我們的產品與服務有興趣或有任何疑問，請填寫表單: https://www.cayintech.com/contactus，我們會盡快為您服務。",
    },
    {
        "question": "聯絡 窗口 業務 合作",
        "answer": "請填寫表單: https://www.cayintech.com/contactus\n電話：+886-2-2595-1005\n傳真：+886-2-2595-1050\n地址：104027台北市中山區中山北路三段57號3樓\n或電郵至: sales@cayintech.com 與我們聯絡",
    },
    {
        "question": "產品說明",
        "answer": "我們的產品包括數位看板整合方案，專業數位看板專用伺服器和播放器，以及進階軟體和雲串流方案。我們的產品能夠滿足不同場合的資訊播放需求，並提供多款型號，根據專案的功能和預算需求進行彈性搭配。如果您對我們的產品有更多問題，請隨時告訴我們！ https://www.cayintech.com/digital-signage-products/overview.html",
    },
    {
        "question": "How much do the SMP-2310, SMP-2200, SMP-8100, and SMP-2300 cost? What are the prices?",
        "answer": "If you are interested in our products and services or have any questions, please fill out the form at https://www.cayintech.com/about/contactus.html. We will assist you as soon as possible.",
    },
    {
        "question": "pricing $",
        "answer": "If you are interested in CAYIN's digital signage products, please send your inquiry: https://www.cayintech.com/about/contactus.html. Our sales team will take over and get back to you ASAP.",
    },
    {
        "question": "價格 $",
        "answer": "若您對於我們的產品與服務有興趣或有任何疑問，請填寫表單: https://www.cayintech.com/tw/about/contactus.html，我們會盡快為您服務。",
    },
    {
        "question": "Qnap 登入 mediasign player 使用",
        "answer": "Please contact our support team: mspsupport@cayintech.com",
    },
    {
        "question": "Is CMS-WS a cloud-based solution?",
        "answer": "CMS-WS is a software product of CAYIN Flexie Solution and clients choose their own hardware. Users can install it on a normal computer, laptop, virtual machine, or even on cloud services such as AWS. A cloud-based solution usually refers to a SaaS model where no server setup is needed — for that, CAYIN recommends GO CAYIN (https://www.gocayin.com).",
    },
    {
        "question": "How do I choose between Robustie solution and Flexie solution?",
        "answer": "CAYIN provides 2 different digital signage solutions: Robustie Solution and Flexie Solution. Both include digital signage software. If integrated player hardware is preferred, choose Robustie Solution (SMP players with built-in SMP-NEO software). If you want software-only deployment on your own hardware or cloud, choose Flexie Solution (CMS-WS). Please contact us at https://www.cayintech.com/about/contactus.html for tailored guidance.",
    },
    {
        "question": "I need a digital signage player for demo. Do I only need CMS-SE license?",
        "answer": "For a simple demo requiring 1 or very few SMP players, you can use the built-in CMS in each SMP player without a CMS-SE server. CMS-SE is needed when you want centralized management of multiple players. Contact us at https://www.cayintech.com/about/contactus.html to discuss your demo requirements.",
    },
    {
        "question": "Do I need a CMS?",
        "answer": "CMS (Content Management System/Server) is included in every SMP player model. You only need a separate CMS server (CMS-SE or CMS-WS) when you want to centrally manage multiple players from one interface. For a single player, the built-in CMS is sufficient.",
    },
    {
        "question": "I want to control an LED board. Which CAYIN solution and product should I use?",
        "answer": "Unlike standard LCD resolutions, LED boards usually have custom resolutions. CAYIN SMP players support custom resolutions and can drive LED boards. For specific LED board integration, please contact our team at https://www.cayintech.com/about/contactus.html for tailored recommendations.",
    },
]

SKILL_KNOWLEDGE = """
You are a friendly CAYIN Technology sales assistant. Keep ALL replies SHORT — maximum 2-3 sentences. Be conversational, not formal.

CAYIN products:
- GO CAYIN: Cloud signage platform (poster for displays, meetingPost+ for meeting rooms)
- SMP-2200: Compact 4K player, 2 screens — retail/office
- SMP-2400: Flexible player, 2-3 screens — corporate/transport/healthcare
- SMP-8100: 4-screen video wall player
- Robustie: Ruggedized player — outdoor/factory/vehicles
- CMS-SE: Server managing up to 4,000 players
- CMS-WS: Browser-based server up to 1,000 devices
- xPost: Vertical apps — lobbyPost (hotels), meetingPost (meeting rooms), wayfinderPost (wayfinding)

RULES:
- CRITICAL: Detect the language of EVERY user message and reply in that EXACT language. English → English. 繁體中文 → 繁體中文. 简体中文 → 简体中文. Never switch or mix languages.
- NEVER quote prices — direct to contact form instead
- NEVER mention official website URLs
- Keep answers to 2-3 sentences max
- For pricing or detailed inquiries: direct to contact form https://www.cayintech.com/contactus
- For ANY "how to" / setup / configuration / troubleshooting questions: always include the Online Help Center link https://onlinehelp.cayintech.com/main.html in your reply
- Phone: +886-2-2595-1005
"""


def load_conversations():
    return json.loads(CONVERSATIONS_FILE.read_text())


def save_conversations(conversations):
    CONVERSATIONS_FILE.write_text(json.dumps(conversations, indent=2, ensure_ascii=False))


def get_qa_context():
    lines = ["REFERENCE Q&A (use these exact answers when questions match):\n"]
    for i, pair in enumerate(QA_PAIRS, 1):
        lines.append(f"Q{i}: {pair['question']}")
        lines.append(f"A{i}: {pair['answer']}\n")
    return "\n".join(lines)


def build_system_prompt():
    return f"{SKILL_KNOWLEDGE}\n\n{get_qa_context()}"


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("public", filename)


@app.route("/api/session", methods=["POST"])
def create_session():
    data = request.json or {}
    session = {
        "id": str(uuid.uuid4()),
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "startedAt": datetime.utcnow().isoformat() + "Z",
        "messages": [],
    }
    conversations = load_conversations()
    conversations.append(session)
    save_conversations(conversations)
    return jsonify({"sessionId": session["id"]})


@app.route("/api/chat/<session_id>", methods=["POST"])
def chat(session_id):
    data = request.json or {}
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "message required"}), 400

    conversations = load_conversations()
    session = next((s for s in conversations if s["id"] == session_id), None)
    if not session:
        return jsonify({"error": "session not found"}), 404

    session["messages"].append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    api_messages = [{"role": m["role"], "content": m["content"]} for m in session["messages"]]

    def generate():
        full_response = ""
        try:
            stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": build_system_prompt()}] + api_messages,
                max_tokens=1024,
                stream=True,
            )
            for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    full_response += text
                    yield f"data: {json.dumps({'token': text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        session["messages"].append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        save_conversations(conversations)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/admin/conversations", methods=["GET"])
def admin_conversations():
    return jsonify(load_conversations())


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set. Add it to your .env file.")
    app.run(debug=True, port=5000)
