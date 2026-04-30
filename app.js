let sessionId   = null;
let isOpen      = false;
let inactivityTimer  = null;
let followUpTimer    = null;
let waitingForReply  = false;

const FOLLOW_UP_DELAY  = 2000;   // 2s after bot finishes → send follow-up
const INACTIVITY_DELAY = 4000;   // 4s after follow-up with no reply → show form link

const FOLLOW_UP_MSG = {
  en: "Is there anything else I can help you with? 😊",
  zh: "還有其他問題嗎？😊",
};
const FORM_MSG = {
  en: "Feel free to fill out our contact form and our team will get back to you shortly! 👉 https://www.cayintech.com/contactus",
  zh: "歡迎填寫表單，我們的業務會盡快與您聯繫！👉 https://www.cayintech.com/contactus",
};

// Detect language from last user message
let lastLang = "zh";
function detectLang(text) {
  return /[一-鿿]/.test(text) ? "zh" : "en";
}

// ── Bubble toggle ────────────────────────────────────────────────────────────
document.getElementById("chat-bubble").addEventListener("click", toggleChat);
document.getElementById("close-btn").addEventListener("click", closeChat);

function toggleChat() {
  isOpen ? closeChat() : openChat();
}

function openChat() {
  isOpen = true;
  document.getElementById("chat-popup").classList.remove("hidden");
  document.getElementById("bubble-icon-open").classList.add("hidden");
  document.getElementById("bubble-icon-close").classList.remove("hidden");
  document.getElementById("unread-badge").classList.add("hidden");
  // Focus first input
  setTimeout(() => {
    const inp = document.getElementById("visitor-name") || document.getElementById("chat-input");
    if (inp) inp.focus();
  }, 100);
}

function closeChat() {
  isOpen = false;
  document.getElementById("chat-popup").classList.add("hidden");
  document.getElementById("bubble-icon-open").classList.remove("hidden");
  document.getElementById("bubble-icon-close").classList.add("hidden");
  // Email conversation record on close
  if (sessionId) {
    fetch(`/api/session/${sessionId}/end`, { method: "POST" }).catch(() => {});
  }
}

// ── Lead form ────────────────────────────────────────────────────────────────
document.getElementById("lead-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name  = document.getElementById("visitor-name").value.trim();
  const email = document.getElementById("visitor-email").value.trim();
  if (!name || !email) return;

  try {
    const res  = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email }),
    });
    const data = await res.json();
    sessionId  = data.sessionId;

    document.getElementById("lead-pane").classList.add("hidden");
    document.getElementById("chat-pane").classList.remove("hidden");

    addBotMsg(`Hi ${name}! 👋 I'm CAYIN's virtual assistant. How can I help you today?`);
  } catch {
    alert("Something went wrong — please try again.");
  }
});

// ── Input ────────────────────────────────────────────────────────────────────
const chatInput = document.getElementById("chat-input");
const sendBtn   = document.getElementById("send-btn");

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); sendMessage(); }
});

// Cancel inactivity timer the moment user starts typing
chatInput.addEventListener("input", () => {
  if (waitingForReply) {
    clearTimeout(inactivityTimer);
    waitingForReply = false;
  }
});

sendBtn.addEventListener("click", sendMessage);

// ── Send ─────────────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || !sessionId) return;

  // Cancel any pending follow-up / inactivity timers
  clearTimeout(followUpTimer);
  clearTimeout(inactivityTimer);
  waitingForReply = false;

  lastLang = detectLang(text);
  chatInput.value = "";
  sendBtn.disabled = true;

  addUserMsg(text);
  const typingEl = addTyping();

  try {
    const response = await fetch(`/api/chat/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    typingEl.remove();
    const { textNode } = addBotMsg("", true);

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let full   = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const p = JSON.parse(line.slice(6));
          if (p.token) { full += p.token; textNode.textContent = full; scrollEnd(); }
          if (p.error) { textNode.textContent = "Sorry, an error occurred. Please try again."; }
        } catch (_) {}
      }
    }

    // ── 2s follow-up after bot finishes ──
    followUpTimer = setTimeout(() => {
      addBotMsg(FOLLOW_UP_MSG[lastLang]);

      // ── 4s inactivity → show form link ──
      waitingForReply = true;
      inactivityTimer = setTimeout(() => {
        if (waitingForReply) {
          addBotMsg(FORM_MSG[lastLang]);
          waitingForReply = false;
        }
      }, INACTIVITY_DELAY);

    }, FOLLOW_UP_DELAY);

  } catch {
    typingEl?.remove();
    addBotMsg("Sorry, I couldn't connect. Please try again.");
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// ── DOM helpers ──────────────────────────────────────────────────────────────
function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addBotMsg(text, streaming = false) {
  const wrap   = document.createElement("div");
  wrap.className = "msg bot";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const textNode = document.createTextNode(text);
  bubble.appendChild(textNode);
  const time   = document.createElement("div");
  time.className = "msg-time";
  time.textContent = now();
  wrap.appendChild(bubble);
  wrap.appendChild(time);
  document.getElementById("chat-messages").appendChild(wrap);
  scrollEnd();

  // Show unread badge if popup is closed
  if (!isOpen) {
    document.getElementById("unread-badge").classList.remove("hidden");
  }
  return { wrap, textNode };
}

function addUserMsg(text) {
  const wrap   = document.createElement("div");
  wrap.className = "msg user";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  const time   = document.createElement("div");
  time.className = "msg-time";
  time.textContent = now();
  wrap.appendChild(bubble);
  wrap.appendChild(time);
  document.getElementById("chat-messages").appendChild(wrap);
  scrollEnd();
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "typing-bubble";
  el.innerHTML = `<span class="t-dot"></span><span class="t-dot"></span><span class="t-dot"></span>`;
  document.getElementById("chat-messages").appendChild(el);
  scrollEnd();
  return el;
}

function scrollEnd() {
  const c = document.getElementById("chat-messages");
  c.scrollTop = c.scrollHeight;
}
