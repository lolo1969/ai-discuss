"""Pydantic-Schemas für Request / Response und interne Datenstrukturen."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class DialogMessage(BaseModel):
    """Ein einzelner Beitrag im Dialog."""
    provider: Provider
    role_label: str  # z. B. "Optimist", "Skeptiker"
    content: str


class Participant(BaseModel):
    """Beschreibung eines Teilnehmers."""
    provider: Provider
    role_label: str = Field(
        "",
        description="Optionale Perspektive / Rolle, z. B. 'Optimist'. Leer = freie Diskussion.",
    )
    system_prompt: str = Field(
        "",
        description="Optionaler System-Prompt, der die Persönlichkeit definiert.",
    )


class DialogConfig(BaseModel):
    """Konfiguration, die der Nutzer zu Beginn festlegt."""
    topic: str = Field(..., description="Das Diskussionsthema")
    participant_a: Participant
    participant_b: Participant
    max_turns: int = Field(6, ge=2, le=50, description="Anzahl Gesamtzüge (A+B)")
    rules: str = Field(
        "",
        description="Optionale Zusatzregeln für den Dialog",
    )


class StartRequest(BaseModel):
    config: DialogConfig


class InterventionRequest(BaseModel):
    """Der Nutzer kann optional eingreifen."""
    message: str


class DialogState(BaseModel):
    config: DialogConfig
    messages: list[DialogMessage] = []
    current_turn: int = 0
    finished: bool = False


class TurnEvent(BaseModel):
    """SSE-Event für einen einzelnen Turn."""
    turn: int
    provider: str
    role_label: str
    content: str
    finished: bool = False
