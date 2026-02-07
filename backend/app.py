"""FastAPI-Anwendung – API-Endpunkte für den KI-Dialog."""

from __future__ import annotations

import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.engine import DialogEngine
from backend.schemas import DialogConfig, InterventionRequest, StartRequest

app = FastAPI(title="AI-Discuss", version="1.0.0")

# CORS für lokale Entwicklung
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aktive Dialog-Sessions (In-Memory – für Prototyp ausreichend)
_sessions: Dict[str, DialogEngine] = {}


# ---------------------------------------------------------------------------
# API-Routen
# ---------------------------------------------------------------------------

@app.post("/api/dialog/start")
async def start_dialog(req: StartRequest):
    """Erstellt eine neue Dialog-Session und gibt die Session-ID zurück."""
    session_id = uuid.uuid4().hex[:12]
    engine = DialogEngine(config=req.config)
    _sessions[session_id] = engine
    return {"session_id": session_id}


@app.get("/api/dialog/{session_id}/stream")
async def stream_dialog(session_id: str):
    """SSE-Stream für den laufenden Dialog."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session nicht gefunden")
    return StreamingResponse(
        engine.run_dialog(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/dialog/{session_id}/intervene")
async def intervene(session_id: str, req: InterventionRequest):
    """Nutzer-Eingriff in den laufenden Dialog."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session nicht gefunden")
    if engine.finished:
        raise HTTPException(400, "Dialog ist bereits beendet")
    await engine.inject_user_message(req.message)
    return {"status": "ok", "message": "Nachricht wurde eingefügt."}


@app.get("/api/dialog/{session_id}/state")
async def get_state(session_id: str):
    """Gibt den aktuellen Dialogzustand zurück."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session nicht gefunden")
    return engine.state.model_dump()


@app.delete("/api/dialog/{session_id}")
async def delete_session(session_id: str):
    """Löscht eine Dialog-Session."""
    if session_id in _sessions:
        del _sessions[session_id]
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Statische Dateien (Frontend)
# ---------------------------------------------------------------------------

_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
