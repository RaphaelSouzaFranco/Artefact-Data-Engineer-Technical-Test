document.addEventListener("DOMContentLoaded", () => {
  const chatWindow = document.getElementById("chatWindow");
  const messageInput = document.getElementById("messageInput");
  const btnSend = document.getElementById("btnSend");
  const btnReset = document.getElementById("btnReset");
  const threadDisplay = document.getElementById("threadDisplay");
  const typingIndicator = document.getElementById("typingIndicator");
  const suggestionPills = document.querySelectorAll(".suggestion-pill");

  let currentThreadId = localStorage.getItem("emporio_thread_id") || "";

  // Inicialização de sessão
  if (!currentThreadId) {
    resetSession();
  } else {
    updateThreadDisplay(currentThreadId);
    loadHistory(currentThreadId);
  }

  // Ajuste dinâmico de altura do textarea
  messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + "px";
  });

  // Envio com Enter (Shift+Enter para nova linha)
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  btnSend.addEventListener("click", sendMessage);
  btnReset.addEventListener("click", resetSession);

  // Sugestões rápidas
  suggestionPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const text = pill.getAttribute("data-text");
      if (text) {
        messageInput.value = text;
        sendMessage();
      }
    });
  });

  async function resetSession() {
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      const data = await res.json();
      currentThreadId = data.thread_id;
      localStorage.setItem("emporio_thread_id", currentThreadId);
      updateThreadDisplay(currentThreadId);

      // Limpar janela mantendo apenas o banner de boas-vindas
      const welcome = chatWindow.querySelector(".welcome-banner");
      chatWindow.innerHTML = "";
      if (welcome) chatWindow.appendChild(welcome);
    } catch (err) {
      console.error("Erro ao resetar sessão:", err);
    }
  }

  function updateThreadDisplay(id) {
    threadDisplay.textContent = `Sessão: ${id}`;
  }

  async function loadHistory(threadId) {
    try {
      const res = await fetch(`/api/history/${threadId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach((m) => appendMessage(m.role, m.content));
      }
    } catch (err) {
      console.warn("Não foi possível carregar o histórico anterior:", err);
    }
  }

  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    // Adiciona mensagem do usuário na tela
    appendMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";

    // Bloquear input e exibir indicador de digitação
    setInputState(false);
    showTyping(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, thread_id: currentThreadId }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Erro de comunicação com o servidor.");
      }

      const data = await res.json();
      appendMessage("assistant", data.reply);
    } catch (err) {
      appendMessage(
        "assistant",
        "Pedimos desculpas, nosso sistema de atendimento encontrou uma instabilidade temporária. Por favor, tente novamente em alguns instantes."
      );
      console.error("Erro na chamada:", err);
    } finally {
      showTyping(false);
      setInputState(true);
      messageInput.focus();
    }
  }

  function appendMessage(role, content) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const sender = document.createElement("span");
    sender.className = "message-sender";
    sender.textContent = role === "user" ? "Você" : "Empório da Música";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = formatMarkdown(content);

    row.appendChild(sender);
    row.appendChild(bubble);
    chatWindow.appendChild(row);

    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    // Escapar tags HTML para segurança
    let escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Converter formatação em negrito: **texto**
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Converter itálico simples: *texto*
    escaped = escaped.replace(/\*(.*?)\*/g, "<em>$1</em>");

    return escaped;
  }

  function setInputState(enabled) {
    messageInput.disabled = !enabled;
    btnSend.disabled = !enabled;
  }

  function showTyping(show) {
    typingIndicator.style.display = show ? "flex" : "none";
    if (show) {
      chatWindow.appendChild(typingIndicator);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  }
});

