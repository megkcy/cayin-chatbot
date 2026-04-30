import csv
import io
import json
import os
import smtplib
import uuid
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
from groq import Groq

load_dotenv()

app = Flask(__name__, static_folder=".")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CONVERSATIONS_FILE = Path("data/conversations.json")
CSV_FILE = Path("data/conversations.csv")
SITE_KNOWLEDGE_FILE = Path("data/site_knowledge.txt")
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
You are a friendly CAYIN Technology (鎧應科技) sales assistant.

BEFORE every reply, you MUST:
1. Search through the PRODUCT KNOWLEDGE and REFERENCE Q&A sections below
2. Base your answer strictly on what is found there
3. If the answer is not in the knowledge base, say you'll connect them with the team via the contact form

Give helpful, complete answers — aim for 3-5 sentences. Cover the key points clearly but don't over-explain. Be conversational, not formal.
Company name rules: ONLY use 鎧應科技 when replying in Traditional Chinese (繁體中文). For ALL other languages (English, Simplified Chinese, Japanese, Thai, Spanish, French, etc.), always use CAYIN Technology.

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
- NEVER mention official website URLs
- Keep answers to 2-3 sentences max
- For pricing or detailed inquiries on hardware (SMP players, CMS servers): direct to contact form https://www.cayintech.com/contactus
- For ANY GO CAYIN questions or inquiries (GO CAYIN poster, meetingPost+, etc.): direct to https://www.gocayin.com/submit-inquiry
- GO CAYIN pricing — CURRENCY RULE (strictly follow this):
  * If the user's message is in 繁體中文 → quote TWD prices ONLY (no USD)
  * If the user's message is in ANY other language → quote USD prices ONLY (no TWD)

- GO CAYIN poster pricing:
  TWD:  Basic: 免費 | Professional: NT$400/月 or NT$4,000/年 | Professional Team: NT$1,900/月 or NT$19,000/年
  USD:  Basic: Free | Professional: $15/month or $150/year | Professional Team: $60/month or $600/year

- GO CAYIN meetingPost+ pricing:
  TWD:  Basic: 免費 | Professional: NT$600/月 or NT$6,000/年 | Professional Team: NT$1,900/月 or NT$19,000/年
  USD:  Basic: Free | Professional: $20/month or $200/year | Professional Team: $60/month or $600/year
- GO CAYIN pricing pages (always include the matching language link when discussing pricing):
  * English — poster: https://www.gocayin.com/en/pricing | meetingPost+: https://www.gocayin.com/en/pricing#meetingPost+
  * 繁體中文 — poster: https://www.gocayin.com/zh-TW/pricing | meetingPost+: https://www.gocayin.com/zh-TW/pricing#meetingPost+
- For ANY "how to" / setup / configuration / troubleshooting questions: always include the Online Help Center link https://onlinehelp.cayintech.com/main.html in your reply
- Phone: +886-2-2595-1005
"""


def send_conversation_email(session):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    notify_to = os.environ.get("NOTIFY_EMAIL", "press@cayintech.com")

    if not smtp_user or not smtp_pass:
        print("Email not sent: SMTP_USER / SMTP_PASS not configured.")
        return

    msgs = session.get("messages", [])
    if not msgs:
        return

    # Build plain-text body
    lines = [
        f"New Chat Conversation — CAYIN Technology 鎧應科技",
        f"{'=' * 50}",
        f"Visitor : {session['name']}",
        f"Email   : {session['email']}",
        f"Started : {session['startedAt']}",
        f"{'=' * 50}",
        "",
    ]
    for m in msgs:
        role = "Visitor" if m["role"] == "user" else "CAYIN Bot"
        ts = m.get("timestamp", "")[:19].replace("T", " ")
        lines.append(f"[{ts}] {role}:")
        lines.append(f"  {m['content']}")
        lines.append("")

    body = "\n".join(lines)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[CAYIN Chat] {session['name']} <{session['email']}>"
    msg["From"] = smtp_user
    msg["To"] = notify_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, notify_to, msg.as_string())
    print(f"Conversation emailed to {notify_to}")


def load_conversations():
    return json.loads(CONVERSATIONS_FILE.read_text())


def save_conversations(conversations):
    CONVERSATIONS_FILE.write_text(json.dumps(conversations, indent=2, ensure_ascii=False))
    _write_csv(conversations)


def _write_csv(conversations):
    """Rebuild the full CSV from all conversations."""
    rows = []
    for s in conversations:
        for m in s.get("messages", []):
            rows.append({
                "Session ID":   s.get("id", ""),
                "Name":         s.get("name", ""),
                "Email":        s.get("email", ""),
                "Started At":   s.get("startedAt", "")[:19].replace("T", " "),
                "Role":         "Visitor" if m["role"] == "user" else "CAYIN Bot",
                "Message":      m.get("content", ""),
                "Timestamp":    m.get("timestamp", "")[:19].replace("T", " "),
            })
    with CSV_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Session ID", "Name", "Email", "Started At",
            "Role", "Message", "Timestamp",
        ])
        writer.writeheader()
        writer.writerows(rows)


def _build_csv_bytes():
    """Return current CSV as bytes (for email attachment)."""
    if CSV_FILE.exists():
        return CSV_FILE.read_bytes()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "Session ID", "Name", "Email", "Started At",
        "Role", "Message", "Timestamp",
    ])
    writer.writeheader()
    return buf.getvalue().encode("utf-8-sig")


def send_weekly_csv_email():
    """Called every Monday — sends full conversations CSV to NOTIFY_EMAIL."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    notify_to = os.environ.get("NOTIFY_EMAIL", "press@cayintech.com")

    if not smtp_user or not smtp_pass:
        print("Weekly email not sent: SMTP_USER / SMTP_PASS not configured.")
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"cayin_chat_{today}.csv"
    csv_bytes = _build_csv_bytes()

    msg = MIMEMultipart()
    msg["Subject"] = f"[CAYIN Chat] Weekly Conversation Report — {today}"
    msg["From"] = smtp_user
    msg["To"] = notify_to
    msg.attach(MIMEText(
        f"Hi,\n\nPlease find attached the weekly chat conversation report ({today}).\n\n"
        "— CAYIN Chatbot",
        "plain", "utf-8"
    ))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(csv_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, notify_to, msg.as_string())
    print(f"Weekly CSV emailed to {notify_to}")


def get_qa_context():
    lines = ["REFERENCE Q&A (use these exact answers when questions match):\n"]
    for i, pair in enumerate(QA_PAIRS, 1):
        lines.append(f"Q{i}: {pair['question']}")
        lines.append(f"A{i}: {pair['answer']}\n")
    return "\n".join(lines)


def get_site_knowledge():
    """Load previously scraped website content if available."""
    if SITE_KNOWLEDGE_FILE.exists():
        content = SITE_KNOWLEDGE_FILE.read_text(encoding="utf-8")
        if content.strip():
            return f"\n\nLATEST WEBSITE CONTENT (scraped from cayintech.com):\n{content}"
    return ""


def build_system_prompt():
    return f"{SKILL_KNOWLEDGE}\n\n{get_qa_context()}{get_site_knowledge()}"


# ── Web scraper ──────────────────────────────────────────────────────────────

SCRAPE_PAGES = [
    ("Homepage",         "https://www.cayintech.com"),
    ("Products",         "https://www.cayintech.com/digital-signage-products/overview.html"),
    ("GO CAYIN",         "https://www.gocayin.com/en"),
    ("SMP Players",      "https://www.cayintech.com/digital-signage-products/digital-signage-player.html"),
    ("CMS Software",     "https://www.cayintech.com/digital-signage-products/digital-signage-software.html"),
    ("News/Updates",     "https://www.cayintech.com/news.html"),
]

SCRAPE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CAYINBot/1.0)"}


def scrape_cayintech():
    """Scrape key CAYIN pages and save to data/site_knowledge.txt."""
    print(f"[{datetime.utcnow().isoformat()}] Starting CAYIN website scrape...")
    sections = []

    for label, url in SCRAPE_PAGES:
        try:
            r = requests.get(url, headers=SCRAPE_HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Remove noise tags
            for tag in soup(["script", "style", "nav", "footer", "header",
                              "noscript", "iframe", "form"]):
                tag.decompose()

            # Extract clean text
            text = " ".join(soup.get_text(separator=" ").split())
            text = text[:3000]  # cap per page to keep prompt size reasonable

            sections.append(f"## {label} ({url})\n{text}")
            print(f"  ✓ {label}: {len(text)} chars")
        except Exception as e:
            print(f"  ✗ {label}: {e}")

    if sections:
        scraped_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        content = f"Scraped: {scraped_at}\n\n" + "\n\n".join(sections)
        SITE_KNOWLEDGE_FILE.write_text(content, encoding="utf-8")
        print(f"[{datetime.utcnow().isoformat()}] Scrape complete — saved to {SITE_KNOWLEDGE_FILE}")
        _send_scrape_notification(scraped_at, len(sections))
    else:
        print("Scrape failed: no content retrieved.")


def _send_scrape_notification(scraped_at, page_count):
    """Send email notification after successful scrape."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    notify_to = os.environ.get("NOTIFY_EMAIL", "press@cayintech.com")

    if not smtp_user or not smtp_pass:
        print("Scrape notification not sent: SMTP not configured.")
        return

    pages_scraped = "\n".join(f"  • {label}: {url}" for label, url in SCRAPE_PAGES)
    body = (
        f"Hi,\n\n"
        f"The CAYIN chatbot has successfully scraped the website and updated its knowledge base.\n\n"
        f"Scraped at : {scraped_at}\n"
        f"Pages updated : {page_count}\n\n"
        f"Pages scraped:\n{pages_scraped}\n\n"
        f"The chatbot will now use the latest website content when answering visitor questions.\n\n"
        f"— CAYIN Chatbot"
    )

    msg = MIMEMultipart()
    msg["Subject"] = f"[CAYIN Chatbot] Website Knowledge Updated — {scraped_at[:10]}"
    msg["From"] = smtp_user
    msg["To"] = notify_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, notify_to, msg.as_string())
        print(f"Scrape notification emailed to {notify_to}")
    except Exception as e:
        print(f"Scrape notification email error: {e}")


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


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


@app.route("/api/session/<session_id>/end", methods=["POST"])
def end_session(session_id):
    conversations = load_conversations()
    session = next((s for s in conversations if s["id"] == session_id), None)
    if session and session.get("messages"):
        try:
            send_conversation_email(session)
        except Exception as e:
            print(f"Email error: {e}")
    return jsonify({"ok": True})


@app.route("/api/admin/conversations", methods=["GET"])
def admin_conversations():
    return jsonify(load_conversations())


@app.route("/api/admin/export-csv", methods=["GET"])
def export_csv():
    """Manual download of the latest CSV."""
    from flask import send_file
    _write_csv(load_conversations())
    return send_file(
        str(CSV_FILE.resolve()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"cayin_chat_{datetime.utcnow().strftime('%Y-%m-%d')}.csv",
    )


# ── Schedulers ───────────────────────────────────────────────────────────────
scheduler = BackgroundScheduler(timezone="Asia/Taipei")

# Every Monday 09:00 — send weekly CSV report
scheduler.add_job(
    send_weekly_csv_email,
    CronTrigger(day_of_week="mon", hour=9, minute=0),
    id="weekly_csv_email",
    replace_existing=True,
)

# Every other Monday 09:00 — scrape cayintech.com for latest content
scheduler.add_job(
    scrape_cayintech,
    CronTrigger(day_of_week="mon", hour=9, minute=5, week="*/2"),
    id="biweekly_scrape",
    replace_existing=True,
)

scheduler.start()

# Run scraper once on startup if no data yet
if not SITE_KNOWLEDGE_FILE.exists():
    import threading
    threading.Thread(target=scrape_cayintech, daemon=True).start()


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set. Add it to your .env file.")
    app.run(host="0.0.0.0", port=5000, debug=False)
