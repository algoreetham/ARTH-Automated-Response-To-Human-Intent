/**
 * ARTH GUI Client Script
 * Handles the animated pulsing Jarvis orb, chat communication, Yes/No permission modal, and Activity Log.
 */

// Global State
let orbState = "idle"; // idle, thinking, speaking, permission
let activityLogs = [];

// --- TAB SWITCHING ---
function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach((el) => el.classList.remove("active"));

  if (tabName === "chat") {
    document.getElementById("tab-chat").classList.add("active");
    document.getElementById("tab-btn-chat").classList.add("active");
  } else if (tabName === "log") {
    document.getElementById("tab-log").classList.add("active");
    document.getElementById("tab-btn-log").classList.add("active");
    refreshLogs();
  }
}

// --- ORB CANVAS ANIMATION ---
const canvas = document.getElementById("orbCanvas");
const ctx = canvas.getContext("2d");
let angle = 0;

function drawOrb() {
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;

  ctx.clearRect(0, 0, width, height);

  // Pick color palette based on state
  let primaryColor = "rgba(0, 240, 255, ";
  let secondaryColor = "rgba(0, 112, 243, ";

  if (orbState === "thinking") {
    primaryColor = "rgba(245, 166, 35, ";
    secondaryColor = "rgba(255, 204, 0, ";
  } else if (orbState === "speaking") {
    primaryColor = "rgba(138, 43, 226, ";
    secondaryColor = "rgba(0, 240, 255, ";
  } else if (orbState === "permission") {
    primaryColor = "rgba(255, 51, 102, ";
    secondaryColor = "rgba(245, 166, 35, ";
  }

  // Pulsing scale factor
  const pulseSpeed = orbState === "thinking" || orbState === "speaking" ? 0.08 : 0.03;
  const pulse = Math.sin(angle * 2) * 6;
  const baseRadius = 38 + pulse;

  // Outer ambient glow
  const gradient = ctx.createRadialGradient(centerX, centerY, baseRadius * 0.4, centerX, centerY, baseRadius * 1.8);
  gradient.addColorStop(0, primaryColor + "0.6)");
  gradient.addColorStop(0.5, secondaryColor + "0.25)");
  gradient.addColorStop(1, "transparent");

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(centerX, centerY, baseRadius * 1.8, 0, Math.PI * 2);
  ctx.fill();

  // Core Sphere
  const coreGrad = ctx.createRadialGradient(centerX, centerY, 5, centerX, centerY, baseRadius);
  coreGrad.addColorStop(0, "#ffffff");
  coreGrad.addColorStop(0.4, primaryColor + "0.9)");
  coreGrad.addColorStop(1, secondaryColor + "0.8)");

  ctx.fillStyle = coreGrad;
  ctx.beginPath();
  ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
  ctx.fill();

  // Orbiting Rings
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(angle);

  ctx.strokeStyle = primaryColor + "0.7)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.ellipse(0, 0, baseRadius + 14, (baseRadius + 14) * 0.45, Math.PI / 4, 0, Math.PI * 2);
  ctx.stroke();

  ctx.rotate(-angle * 2.2);
  ctx.strokeStyle = secondaryColor + "0.8)";
  ctx.beginPath();
  ctx.ellipse(0, 0, baseRadius + 22, (baseRadius + 22) * 0.35, -Math.PI / 3, 0, Math.PI * 2);
  ctx.stroke();

  ctx.restore();

  angle += pulseSpeed;
  requestAnimationFrame(drawOrb);
}

function setOrbStatus(state, label) {
  orbState = state;
  const labelEl = document.getElementById("orbStatus");
  if (labelEl) {
    labelEl.innerText = label || state.toUpperCase();
    if (state === "permission") {
      labelEl.style.color = "var(--accent-red)";
    } else if (state === "thinking") {
      labelEl.style.color = "var(--accent-gold)";
    } else {
      labelEl.style.color = "var(--accent-cyan)";
    }
  }
}

// --- CHAT SYSTEM ---
function appendMessage(sender, text, isUser = false) {
  const history = document.getElementById("chatHistory");
  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${isUser ? "user" : "assistant"}`;

  const header = document.createElement("div");
  header.className = "bubble-header";
  header.innerText = sender;

  const body = document.createElement("div");
  body.className = "bubble-body";
  body.innerText = text;

  bubble.appendChild(header);
  bubble.appendChild(body);
  history.appendChild(bubble);

  history.scrollTop = history.scrollHeight;
}

async function sendMessage() {
  const inputEl = document.getElementById("chatInput");
  const text = inputEl.value.trim();
  if (!text) return;

  appendMessage("Boss", text, true);
  inputEl.value = "";

  setOrbStatus("thinking", "THINKING");

  try {
    if (window.pywebview && window.pywebview.api) {
      const response = await window.pywebview.api.send_message(text);
      if (response && response.reply) {
        appendMessage("ARTH", response.reply, false);
      }
      if (response && response.logs) {
        activityLogs = response.logs;
        renderLogsTable(activityLogs);
      }
    } else {
      // Browser HTTP API mode
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });
        if (res.ok) {
          const response = await res.json();
          if (response && response.reply) {
            appendMessage("ARTH", response.reply, false);
            // Orb reflects speaking status while audio plays
            setOrbStatus("speaking", "SPEAKING...");
            setTimeout(() => setOrbStatus("idle", "IDLE"), 2500);
          }
          if (response && response.logs) {
            activityLogs = response.logs;
            renderLogsTable(activityLogs);
          }
        } else {
          appendMessage("ARTH", `Server responded with status ${res.status}.`, false);
        }
      } catch (networkErr) {
        appendMessage("ARTH", "Running in offline preview: received '" + text + "'. (Launch `python3 main.py --web` for live backend)", false);
      }
    }
  } catch (err) {
    appendMessage("ARTH", "An error occurred: " + err, false);
    setOrbStatus("idle", "IDLE");
  }
}

// Enter key support
document.getElementById("chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// --- VOICE RECOGNITION (DUAL-ENGINE: BROWSER + MAC HARDWARE MIC) ---
const micBtn = document.getElementById("micBtn");
let recognition = null;
let isRecordingVoice = false;

const SpeechRecClass = window.SpeechRecognition || window.webkitSpeechRecognition;

function setupWebSpeech() {
  if (!SpeechRecClass) return null;
  try {
    const rec = new SpeechRecClass();
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = "en-IN"; // Multilingual Indian English default

    rec.onstart = function () {
      isRecordingVoice = true;
      micBtn.classList.add("listening");
      setOrbStatus("listening", "LISTENING...");
      const inputEl = document.getElementById("chatInput");
      inputEl.placeholder = "🎙️ Listening to you, Boss... Speak now!";
    };

    rec.onresult = function (event) {
      let interim = "";
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      const inputEl = document.getElementById("chatInput");
      if (interim) {
        inputEl.value = interim;
      }
      if (finalTranscript) {
        inputEl.value = finalTranscript;
        inputEl.placeholder = "Type a command or ask ARTH...";
        sendMessage();
      }
    };

    rec.onerror = function (event) {
      console.warn("Browser SpeechRecognition error:", event.error);
      isRecordingVoice = false;
      micBtn.classList.remove("listening");
      setOrbStatus("idle", "IDLE");
      const inputEl = document.getElementById("chatInput");
      inputEl.placeholder = "Type a command or ask ARTH...";

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        appendMessage("ARTH", "⚠️ Browser microphone access is blocked. Please click the lock/settings icon in the browser address bar and choose 'Allow' for Microphone. Alternatively, switching to Mac hardware microphone...", false);
        triggerHardwareMicListen();
      } else if (event.error === "no-speech") {
        appendMessage("ARTH", "Boss, no speech was detected. Please try clicking the mic and speaking again.", false);
      } else if (event.error === "network") {
        appendMessage("ARTH", "Speech service network timeout. Falling back to native Mac hardware mic...", false);
        triggerHardwareMicListen();
      }
    };

    rec.onend = function () {
      isRecordingVoice = false;
      micBtn.classList.remove("listening");
      const inputEl = document.getElementById("chatInput");
      inputEl.placeholder = "Type a command or ask ARTH...";
      if (orbState === "listening") {
        setOrbStatus("idle", "IDLE");
      }
    };

    return rec;
  } catch (e) {
    console.error("SpeechRec init error:", e);
    return null;
  }
}

recognition = setupWebSpeech();

// Native Hardware Microphone Listener Fallback (/api/voice/listen)
async function triggerHardwareMicListen() {
  if (isRecordingVoice) return;
  isRecordingVoice = true;
  micBtn.classList.add("listening");
  setOrbStatus("listening", "LISTENING (MAC MIC)...");

  const inputEl = document.getElementById("chatInput");
  inputEl.placeholder = "🎙️ Listening directly through Mac mic (4s)...";

  try {
    let res;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.listen_voice) {
      res = await window.pywebview.api.listen_voice(4.0, "en");
    } else {
      const resp = await fetch("/api/voice/listen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration: 4.0, lang: "en" })
      });
      res = await resp.json();
    }

    if (res && res.status === "success" && res.transcript) {
      appendMessage("Boss", res.transcript, true);
      if (res.reply) {
        appendMessage("ARTH", res.reply, false);
        setOrbStatus("speaking", "SPEAKING...");
        setTimeout(() => setOrbStatus("idle", "IDLE"), 2500);
      }
      if (res.logs) {
        activityLogs = res.logs;
        renderLogsTable(activityLogs);
      }
    } else if (res && res.reply) {
      appendMessage("ARTH", res.reply, false);
    }
  } catch (err) {
    console.error("Hardware mic listener error:", err);
    appendMessage("ARTH", "Unable to capture audio from Mac mic: " + err, false);
  } finally {
    isRecordingVoice = false;
    micBtn.classList.remove("listening");
    setOrbStatus("idle", "IDLE");
    inputEl.placeholder = "Type a command or ask ARTH...";
  }
}

if (micBtn) {
  micBtn.addEventListener("click", () => {
    if (isRecordingVoice) {
      if (recognition) {
        try { recognition.stop(); } catch (e) {}
      }
      isRecordingVoice = false;
      micBtn.classList.remove("listening");
      setOrbStatus("idle", "IDLE");
      return;
    }

    // Try browser SpeechRecognition first
    if (recognition) {
      try {
        recognition.start();
        return;
      } catch (err) {
        console.warn("Could not start browser SpeechRecognition, using hardware mic:", err);
      }
    }

    // Fall back directly to Mac hardware microphone
    triggerHardwareMicListen();
  });
}

// --- YES / NO PERMISSION MODAL ---
window.arthApp = {
  showPermissionModal: function (promptMessage) {
    setOrbStatus("permission", "APPROVAL NEEDED");
    document.getElementById("modalPromptText").innerText = promptMessage;
    document.getElementById("permissionModal").classList.add("active");
  },
};

function resolvePermission(approved) {
  document.getElementById("permissionModal").classList.remove("active");
  setOrbStatus("thinking", "PROCESSING");

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.resolve_permission(approved);
  } else {
    fetch("/api/permission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: Boolean(approved) })
    }).catch(console.error);
  }
}

// Background polling for permissions in browser mode
if (!window.pywebview) {
  setInterval(async () => {
    try {
      const res = await fetch("/api/permission");
      if (res.ok) {
        const data = await res.json();
        const modal = document.getElementById("permissionModal");
        if (data.waiting && data.prompt) {
          if (!modal.classList.contains("active")) {
            window.arthApp.showPermissionModal(data.prompt);
          }
        } else {
          if (modal.classList.contains("active") && !data.waiting) {
            modal.classList.remove("active");
          }
        }
      }
    } catch (e) {
      // Offline/quiet
    }
  }, 1000);
}

// --- ACTIVITY LOG TAB (Section 14) ---
async function refreshLogs() {
  if (window.pywebview && window.pywebview.api) {
    const q = document.getElementById("logSearchInput").value;
    const s = document.getElementById("logStatusFilter").value;
    activityLogs = await window.pywebview.api.get_logs(q, s);
    renderLogsTable(activityLogs);
  } else {
    try {
      const res = await fetch("/api/logs");
      if (res.ok) {
        activityLogs = await res.json();
        renderLogsTable(activityLogs);
      }
    } catch (e) {
      console.error("Failed to fetch logs:", e);
    }
  }
}

function filterLogs() {
  const query = document.getElementById("logSearchInput").value.toLowerCase();
  const status = document.getElementById("logStatusFilter").value.toLowerCase();

  const filtered = activityLogs.filter((item) => {
    const matchStatus = status === "all" || item.status.toLowerCase() === status;
    const searchable = (item.query + " " + item.tool + " " + item.reason).toLowerCase();
    const matchQuery = !query || searchable.includes(query);
    return matchStatus && matchQuery;
  });

  renderLogsTable(filtered);
}

function renderLogsTable(logs) {
  const tbody = document.getElementById("logTableBody");
  tbody.innerHTML = "";

  if (!logs || logs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; opacity:0.6;">No activity records found.</td></tr>';
    return;
  }

  logs.forEach((log) => {
    const tr = document.createElement("tr");

    const timeFormatted = log.timestamp ? log.timestamp.split("T")[1]?.slice(0, 8) : "";

    tr.innerHTML = `
      <td>${timeFormatted}</td>
      <td><strong>${escapeHtml(log.query)}</strong></td>
      <td><code>${escapeHtml(log.tool)}</code></td>
      <td><span class="log-status-badge ${escapeHtml(log.status)}">${escapeHtml(log.status)}</span></td>
      <td>${escapeHtml(log.reason)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// --- INITIALIZATION ---
function applyInitialState(state) {
  if (state.user_name) {
    document.getElementById("user-display-name").innerText = state.user_name;
  }
  if (state.model) {
    document.getElementById("infoModel").innerText = state.model;
  }
  if (state.context_window) {
    document.getElementById("infoContext").innerText = state.context_window + " tokens";
  }
  if (state.logs) {
    activityLogs = state.logs;
    renderLogsTable(activityLogs);
  }
  if (state.todos) {
    renderTodos(state.todos);
  }
  if (state.reminders) {
    renderReminders(state.reminders);
  }
}

window.addEventListener("pywebviewready", async function () {
  if (window.pywebview && window.pywebview.api) {
    const state = await window.pywebview.api.get_initial_state();
    applyInitialState(state);
  }
});

// Browser HTTP mode initialization
window.addEventListener("DOMContentLoaded", async function () {
  if (!window.pywebview) {
    try {
      const res = await fetch("/api/state");
      if (res.ok) {
        const state = await res.json();
        applyInitialState(state);
      }
    } catch (e) {
      // Running standalone
    }
  }
});

function renderTodos(todos) {
  const container = document.getElementById("todoList");
  container.innerHTML = "";
  document.getElementById("todoCount").innerText = todos.length;

  todos.forEach((t) => {
    const div = document.createElement("div");
    div.className = `todo-item ${t.done ? "done" : ""}`;
    div.innerHTML = `<span>${t.done ? "☑" : "☐"}</span> <span>${escapeHtml(t.task)}</span>`;
    container.appendChild(div);
  });
}

function renderReminders(reminders) {
  const container = document.getElementById("reminderList");
  container.innerHTML = "";
  document.getElementById("reminderCount").innerText = reminders.length;

  reminders.forEach((r) => {
    const div = document.createElement("div");
    div.className = "todo-item";
    div.innerHTML = `<span>⏰</span> <span>${escapeHtml(r.title)} (${escapeHtml(r.time)})</span>`;
    container.appendChild(div);
  });
}

// Start orb animation loop
drawOrb();
