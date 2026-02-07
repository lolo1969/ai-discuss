/* ===========================
   AI-Discuss – Frontend Logic
   =========================== */

const API_BASE = window.location.origin;

// DOM elements
const setupPanel      = document.getElementById("setup-panel");
const dialogPanel     = document.getElementById("dialog-panel");
const dialogTopic     = document.getElementById("dialog-topic");
const turnCounter     = document.getElementById("turn-counter");
const messagesEl      = document.getElementById("dialog-messages");
const btnStart        = document.getElementById("btn-start");
const btnPause        = document.getElementById("btn-pause");
const btnStop         = document.getElementById("btn-stop");
const btnNew          = document.getElementById("btn-new");
const btnIntervene    = document.getElementById("btn-intervene");
const interventionInp = document.getElementById("intervention-input");

let currentSessionId  = null;
let eventSource       = null;
let maxTurns          = 6;
let currentMsgEl      = null;
let currentContentEl  = null;
let isPaused          = false;

// Slider live update
const tokenDelaySlider = document.getElementById("token-delay");
const delayValueLabel  = document.getElementById("delay-value");
tokenDelaySlider.addEventListener("input", () => {
    delayValueLabel.textContent = tokenDelaySlider.value;
});

// ---------------------------------------------------------------------------
// Start dialog
// ---------------------------------------------------------------------------

btnStart.addEventListener("click", async () => {
    const config = buildConfig();
    if (!config) return;

    btnStart.disabled = true;
    btnStart.textContent = "Starting…";

    try {
        const res = await fetch(`${API_BASE}/api/dialog/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config }),
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Error: " + (err.detail || JSON.stringify(err)));
            return;
        }

        const { session_id } = await res.json();
        currentSessionId = session_id;
        maxTurns = config.max_turns;

        // Switch UI
        setupPanel.classList.add("hidden");
        dialogPanel.classList.remove("hidden");
        dialogTopic.textContent = `💬 ${config.topic}`;
        turnCounter.textContent = `Turn 0/${maxTurns}`;
        messagesEl.innerHTML = "";

        // Start SSE stream
        startStream(session_id);
    } catch (e) {
        alert("Connection error: " + e.message);
    } finally {
        btnStart.disabled = false;
        btnStart.textContent = "Start Dialog ▶";
    }
});

// ---------------------------------------------------------------------------
// SSE-Stream
// ---------------------------------------------------------------------------

function startStream(sessionId) {
    eventSource = new EventSource(`${API_BASE}/api/dialog/${sessionId}/stream`);

    eventSource.addEventListener("turn_start", (e) => {
        const data = JSON.parse(e.data);
        const { turn, provider, role_label } = data;

        turnCounter.textContent = `Turn ${turn + 1}/${maxTurns}`;

        // New message bubble
        const msgEl = document.createElement("div");
        msgEl.className = `message provider-${provider}`;
        msgEl.innerHTML = `
            <div class="message-header">
                <span class="message-role">${escapeHtml(role_label)}</span>
                <span class="message-provider">${provider.toUpperCase()}</span>
            </div>
            <div class="message-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        `;
        messagesEl.appendChild(msgEl);
        currentMsgEl = msgEl;
        currentContentEl = msgEl.querySelector(".message-content");
        scrollToBottom();
    });

    eventSource.addEventListener("token", (e) => {
        const data = JSON.parse(e.data);
        if (!currentContentEl) return;

        // Remove typing indicator on first token
        const indicator = currentContentEl.querySelector(".typing-indicator");
        if (indicator) indicator.remove();

        currentContentEl.textContent += data.token;
        scrollToBottom();
    });

    eventSource.addEventListener("turn_end", (e) => {
        const data = JSON.parse(e.data);
        // Render content as formatted HTML
        if (currentContentEl) {
            currentContentEl.innerHTML = formatContent(data.content);
        }
        currentMsgEl = null;
        currentContentEl = null;
        scrollToBottom();
    });

    eventSource.addEventListener("dialog_end", (e) => {
        const data = JSON.parse(e.data);
        const statusEl = document.createElement("div");
        statusEl.className = "status-message finished";
        statusEl.textContent = `✓ Dialog finished after ${data.total_turns} turns`;
        messagesEl.appendChild(statusEl);
        scrollToBottom();
        closeStream();
    });

    eventSource.onerror = () => {
        // Stream was closed or error occurred
        closeStream();
    };
}

function closeStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

// ---------------------------------------------------------------------------
// User intervention
// ---------------------------------------------------------------------------

btnIntervene.addEventListener("click", sendIntervention);
interventionInp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendIntervention();
});

async function sendIntervention() {
    const message = interventionInp.value.trim();
    if (!message || !currentSessionId) return;

    interventionInp.value = "";

    // Show locally immediately
    const msgEl = document.createElement("div");
    msgEl.className = "message provider-moderator";
    msgEl.innerHTML = `
        <div class="message-header">
            <span class="message-role">Moderator (You)</span>
            <span class="message-provider">USER</span>
        </div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    messagesEl.appendChild(msgEl);
    scrollToBottom();

    try {
        const res = await fetch(`${API_BASE}/api/dialog/${currentSessionId}/intervene`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        const data = await res.json();
        // If dialog was finished, the backend extended it – restart SSE stream
        if (data.continued) {
            maxTurns = data.max_turns;
            startStream(currentSessionId);
        }
    } catch (e) {
        console.error("Intervention failed:", e);
    }
}

// ---------------------------------------------------------------------------
// Controls
// ---------------------------------------------------------------------------

btnPause.addEventListener("click", async () => {
    if (!currentSessionId) return;
    try {
        const res = await fetch(`${API_BASE}/api/dialog/${currentSessionId}/pause`, { method: "POST" });
        const data = await res.json();
        isPaused = data.paused;
        btnPause.textContent = isPaused ? "▶ Resume" : "⏸ Pause";
        btnPause.title = isPaused ? "Resume dialog" : "Pause dialog";

        // Show status in chat
        const statusEl = document.createElement("div");
        statusEl.className = "status-message";
        statusEl.textContent = isPaused ? "⏸ Dialog paused" : "▶ Dialog resumed";
        messagesEl.appendChild(statusEl);
        scrollToBottom();
    } catch (e) {
        console.error("Pause toggle failed:", e);
    }
});

btnStop.addEventListener("click", () => {
    closeStream();
    if (currentSessionId) {
        fetch(`${API_BASE}/api/dialog/${currentSessionId}`, { method: "DELETE" });
    }
    isPaused = false;
    btnPause.textContent = "⏸ Pause";
    const statusEl = document.createElement("div");
    statusEl.className = "status-message";
    statusEl.textContent = "⏹ Dialog stopped by user";
    messagesEl.appendChild(statusEl);
});

btnNew.addEventListener("click", () => {
    closeStream();
    if (currentSessionId) {
        fetch(`${API_BASE}/api/dialog/${currentSessionId}`, { method: "DELETE" });
        currentSessionId = null;
    }
    isPaused = false;
    btnPause.textContent = "⏸ Pause";
    dialogPanel.classList.add("hidden");
    setupPanel.classList.remove("hidden");
});

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

function buildConfig() {
    const topic = document.getElementById("topic").value.trim();
    if (!topic) {
        alert("Please enter a topic.");
        return null;
    }

    return {
        topic,
        participant_a: {
            provider: document.getElementById("prov-a").value,
            role_label: document.getElementById("role-a").value.trim(),
            system_prompt: document.getElementById("sysprompt-a").value.trim(),
        },
        participant_b: {
            provider: document.getElementById("prov-b").value,
            role_label: document.getElementById("role-b").value.trim(),
            system_prompt: document.getElementById("sysprompt-b").value.trim(),
        },
        max_turns: parseInt(document.getElementById("max-turns").value, 10) || 6,
        token_delay_ms: parseInt(document.getElementById("token-delay").value, 10) || 80,
        rules: document.getElementById("rules").value.trim(),
    };
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatContent(text) {
    // Simple paragraph formatting
    return text
        .split(/\n{2,}/)
        .map((p) => `<p>${escapeHtml(p.trim())}</p>`)
        .join("")
        .replace(/\n/g, "<br>");
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
