"""Pydantic schemas for request/response and internal data structures."""

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
    """A single message in the dialog."""
    provider: Provider
    role_label: str  # e.g. "Optimist", "Skeptic"
    content: str


class Participant(BaseModel):
    """Description of a participant."""
    provider: Provider
    role_label: str = Field(
        "",
        description="Optional perspective/role, e.g. 'Optimist'. Empty = open discussion.",
    )
    system_prompt: str = Field(
        "",
        description="Optional system prompt that defines the personality.",
    )


class DialogConfig(BaseModel):
    """Configuration set by the user at the start."""
    topic: str = Field(..., description="The discussion topic")
    participant_a: Participant
    participant_b: Participant
    max_turns: int = Field(6, ge=2, le=50, description="Total number of turns (A+B)")
    token_delay_ms: int = Field(
        80,
        ge=0,
        le=500,
        description="Delay in milliseconds between each streamed token (0 = real-time)",
    )
    rules: str = Field(
        "",
        description="Optional additional rules for the dialog",
    )


class StartRequest(BaseModel):
    config: DialogConfig


class InterventionRequest(BaseModel):
    """The user can optionally intervene."""
    message: str


class DialogState(BaseModel):
    config: DialogConfig
    messages: list[DialogMessage] = []
    current_turn: int = 0
    finished: bool = False


class TurnEvent(BaseModel):
    """SSE event for a single turn."""
    turn: int
    provider: str
    role_label: str
    content: str
    finished: bool = False
