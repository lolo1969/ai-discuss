"""FastAPI application – API endpoints for the AI dialog."""

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

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active dialog sessions (in-memory – sufficient for prototype)
_sessions: Dict[str, DialogEngine] = {}


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.post("/api/dialog/start")
async def start_dialog(req: StartRequest):
    """Create a new dialog session and return the session ID."""
    session_id = uuid.uuid4().hex[:12]
    engine = DialogEngine(config=req.config)
    _sessions[session_id] = engine
    return {"session_id": session_id}


@app.get("/api/dialog/{session_id}/stream")
async def stream_dialog(session_id: str):
    """SSE stream for the running dialog."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session not found")
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
    """User intervention in the running dialog."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session not found")
    if engine.finished:
        raise HTTPException(400, "Dialog has already ended")
    await engine.inject_user_message(req.message)
    return {"status": "ok", "message": "Message was injected."}


@app.post("/api/dialog/{session_id}/pause")
async def toggle_pause(session_id: str):
    """Toggle pause/resume for the dialog."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session not found")
    if engine.is_paused:
        engine.resume()
    else:
        engine.pause()
    return {"paused": engine.is_paused}


@app.get("/api/dialog/{session_id}/state")
async def get_state(session_id: str):
    """Return the current dialog state."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(404, "Session not found")
    return engine.state.model_dump()


@app.delete("/api/dialog/{session_id}")
async def delete_session(session_id: str):
    """Delete a dialog session."""
    if session_id in _sessions:
        del _sessions[session_id]
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static files (frontend)
# ---------------------------------------------------------------------------

_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
