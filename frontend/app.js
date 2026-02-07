/* ===========================
   AI-Discuss – Frontend-Logik
   =========================== */

const API_BASE = window.location.origin;

// DOM-Elemente
const setupPanel      = document.getElementById("setup-panel");
const dialogPanel     = document.getElementById("dialog-panel");
const dialogTopic     = document.getElementById("dialog-topic");
const turnCounter     = document.getElementById("turn-counter");
const messagesEl      = document.getElementById("dialog-messages");
const btnStart        = document.getElementById("btn-start");
const btnStop         = document.getElementById("btn-stop");
const btnNew          = document.getElementById("btn-new");
const btnIntervene    = document.getElementById("btn-intervene");
const interventionInp = document.getElementById("intervention-input");

let currentSessionId  = null;
let eventSource       = null;
let maxTurns          = 6;
let currentMsgEl      = null;
let currentContentEl  = null;

// ---------------------------------------------------------------------------
// Dialog starten
// ---------------------------------------------------------------------------

btnStart.addEventListener("click", async () => {
    const config = buildConfig();
    if (!config) return;

    btnStart.disabled = true;
    btnStart.textContent = "Wird gestartet…";

    try {
        const res = await fetch(`${API_BASE}/api/dialog/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config }),
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Fehler: " + (err.detail || JSON.stringify(err)));
            return;
        }

        const { session_id } = await res.json();
        currentSessionId = session_id;
        maxTurns = config.max_turns;

        // UI umschalten
        setupPanel.classList.add("hidden");
        dialogPanel.classList.remove("hidden");
        dialogTopic.textContent = `💬 ${config.topic}`;
        turnCounter.textContent = `Turn 0/${maxTurns}`;
        messagesEl.innerHTML = "";

        // SSE-Stream starten
        startStream(session_id);
    } catch (e) {
        alert("Verbindungsfehler: " + e.message);
    } finally {
        btnStart.disabled = false;
        btnStart.textContent = "Dialog starten ▶";
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

        // Neue Nachrichten-Bubble
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

        // Typing-Indicator entfernen beim ersten Token
        const indicator = currentContentEl.querySelector(".typing-indicator");
        if (indicator) indicator.remove();

        currentContentEl.textContent += data.token;
        scrollToBottom();
    });

    eventSource.addEventListener("turn_end", (e) => {
        const data = JSON.parse(e.data);
        // Inhalt als formatiertes HTML rendern
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
        statusEl.textContent = `✓ Dialog beendet nach ${data.total_turns} Zügen`;
        messagesEl.appendChild(statusEl);
        scrollToBottom();
        closeStream();
    });

    eventSource.onerror = () => {
        // Stream wurde geschlossen oder Fehler
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
// Nutzer-Eingriff
// ---------------------------------------------------------------------------

btnIntervene.addEventListener("click", sendIntervention);
interventionInp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendIntervention();
});

async function sendIntervention() {
    const message = interventionInp.value.trim();
    if (!message || !currentSessionId) return;

    interventionInp.value = "";

    // Sofort lokal anzeigen
    const msgEl = document.createElement("div");
    msgEl.className = "message provider-moderator";
    msgEl.innerHTML = `
        <div class="message-header">
            <span class="message-role">Moderator (Du)</span>
            <span class="message-provider">NUTZER</span>
        </div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    messagesEl.appendChild(msgEl);
    scrollToBottom();

    try {
        await fetch(`${API_BASE}/api/dialog/${currentSessionId}/intervene`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
    } catch (e) {
        console.error("Intervention fehlgeschlagen:", e);
    }
}

// ---------------------------------------------------------------------------
// Steuerung
// ---------------------------------------------------------------------------

btnStop.addEventListener("click", () => {
    closeStream();
    if (currentSessionId) {
        fetch(`${API_BASE}/api/dialog/${currentSessionId}`, { method: "DELETE" });
    }
    const statusEl = document.createElement("div");
    statusEl.className = "status-message";
    statusEl.textContent = "⏹ Dialog vom Nutzer abgebrochen";
    messagesEl.appendChild(statusEl);
});

btnNew.addEventListener("click", () => {
    closeStream();
    if (currentSessionId) {
        fetch(`${API_BASE}/api/dialog/${currentSessionId}`, { method: "DELETE" });
        currentSessionId = null;
    }
    dialogPanel.classList.add("hidden");
    setupPanel.classList.remove("hidden");
});

// ---------------------------------------------------------------------------
// Hilfsfunktionen
// ---------------------------------------------------------------------------

function buildConfig() {
    const topic = document.getElementById("topic").value.trim();
    if (!topic) {
        alert("Bitte gib ein Thema ein.");
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
        rules: document.getElementById("rules").value.trim(),
    };
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatContent(text) {
    // Einfache Absatzformatierung
    return text
        .split(/\n{2,}/)
        .map((p) => `<p>${escapeHtml(p.trim())}</p>`)
        .join("")
        .replace(/\n/g, "<br>");
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
