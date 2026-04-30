(function () {
  if (document.getElementById("cayin-chat-frame")) return;

  var iframe = document.createElement("iframe");
  iframe.id  = "cayin-chat-frame";
  iframe.src = (window.CAYIN_CHAT_URL || "https://your-chatbot-server.com") + "/?embed=1";

  iframe.style.cssText = [
    "position:fixed",
    "bottom:0",
    "right:0",
    "width:420px",
    "height:700px",
    "border:none",
    "z-index:2147483647",
    "background:transparent",
    "pointer-events:auto",
  ].join(";");

  iframe.allow = "microphone";
  iframe.setAttribute("scrolling", "no");
  iframe.setAttribute("loading", "lazy");

  // Only inject iframe when user hovers or clicks near bottom-right corner
  // to avoid blocking main page load
  var injected = false;
  function injectIframe() {
    if (!injected) {
      injected = true;
      document.body.appendChild(iframe);
    }
  }

  // Inject after page fully loaded (does not block rendering)
  if (document.readyState === "complete") {
    setTimeout(injectIframe, 1000);
  } else {
    window.addEventListener("load", function () {
      setTimeout(injectIframe, 1000);
    });
  }
})();
