"""Dialog engine – manages state and orchestrates turns."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from backend.providers import stream_response
from backend.schemas import (
    DialogConfig,
    DialogMessage,
    DialogState,
    Participant,
    TurnEvent,
)


class DialogEngine:
    """Holds the entire dialog state and produces SSE events."""

    def __init__(self, config: DialogConfig) -> None:
        self.state = DialogState(config=config)
        self._participants = [config.participant_a, config.participant_b]
        # Set default labels if no role is defined
        provider_labels = {"openai": "GPT", "anthropic": "Claude"}
        for p in self._participants:
            if not p.role_label:
                p.role_label = provider_labels.get(p.provider.value, p.provider.value)
        # Enrich system prompts with topic + rules
        for p in self._participants:
            p.system_prompt = self._build_system_prompt(p)

    # ----- Helper methods -----

    def _build_system_prompt(self, participant: Participant) -> str:
        cfg = self.state.config
        base = f"You are participating in a dialog about \"{cfg.topic}\".\n"
        if participant.role_label:
            base += f"Your role / perspective: {participant.role_label}.\n"
        if cfg.rules:
            base += f"Additional rules: {cfg.rules}\n"
        base += (
            "Refer to the previous contributions of your conversation partner. "
            "Keep your responses concise (max 3-4 paragraphs)."
        )
        if participant.role_label:
            base += " Respond from your assigned perspective."
        if participant.system_prompt:
            base += f"\n\nAdditional context: {participant.system_prompt}"
        return base

    @property
    def current_participant(self) -> Participant:
        idx = self.state.current_turn % 2
        return self._participants[idx]

    @property
    def finished(self) -> bool:
        return self.state.current_turn >= self.state.config.max_turns

    # ----- Main loop -----

    async def run_dialog(self) -> AsyncIterator[str]:
        """Generator that yields SSE-formatted JSON strings."""
        while not self.finished:
            participant = self.current_participant
            content_parts: list[str] = []

            # SSE: Turn start
            yield self._sse_event("turn_start", {
                "turn": self.state.current_turn,
                "provider": participant.provider.value,
                "role_label": participant.role_label,
            })

            async for token in stream_response(
                provider=participant.provider,
                system_prompt=participant.system_prompt,
                history=self.state.messages,
            ):
                content_parts.append(token)
                # SSE: Token stream
                yield self._sse_event("token", {
                    "turn": self.state.current_turn,
                    "token": token,
                })

            full_content = "".join(content_parts)
            self.state.messages.append(
                DialogMessage(
                    provider=participant.provider,
                    role_label=participant.role_label,
                    content=full_content,
                )
            )
            self.state.current_turn += 1

            # SSE: Turn end
            yield self._sse_event("turn_end", {
                "turn": self.state.current_turn - 1,
                "provider": participant.provider.value,
                "role_label": participant.role_label,
                "content": full_content,
                "finished": self.finished,
            })

            # Short pause between turns
            await asyncio.sleep(0.3)

        # SSE: Dialog complete
        yield self._sse_event("dialog_end", {"total_turns": self.state.current_turn})

    async def inject_user_message(self, message: str) -> None:
        """User intervention: message is added to the history."""
        self.state.messages.append(
            DialogMessage(
                provider=self.current_participant.provider,  # treated as context
                role_label="Moderator (User)",
                content=message,
            )
        )

    @staticmethod
    def _sse_event(event_type: str, data: dict) -> str:
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"event: {event_type}\ndata: {payload}\n\n"
