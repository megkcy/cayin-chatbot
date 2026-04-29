let sessionId = null;

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

    document.getElementById("lead-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");

    addBotMsg(`Hi ${name}! 👋 I'm your CAYIN Technology digital signage expert.\nHow can I help you today?`);
  } catch {
    alert("Something went wrong — please try again.");
  }
});

// ── Input events ─────────────────────────────────────────────────────────────
const chatInput = document.getElementById("chat-input");
const sendBtn   = document.getElementById("send-btn");

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); sendMessage(); }
});

sendBtn.addEventListener("click", sendMessage);

// ── Send ─────────────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || !sessionId) return;

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
  } catch {
    typingEl?.remove();
    addBotMsg("Sorry, I couldn't connect. Please check your connection and try again.");
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
  const wrap = document.createElement("div");
  wrap.className = "msg bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const textNode = document.createTextNode(text);
  bubble.appendChild(textNode);

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = now();

  wrap.appendChild(bubble);
  wrap.appendChild(time);
  document.getElementById("chat-messages").appendChild(wrap);
  scrollEnd();
  return { wrap, textNode };
}

function addUserMsg(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg user";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const time = document.createElement("div");
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
