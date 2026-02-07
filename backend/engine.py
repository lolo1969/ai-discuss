"""Dialog-Engine – verwaltet den Zustand und orchestriert die Turns."""

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
    """Hält den gesamten Dialogzustand und produziert SSE-Events."""

    def __init__(self, config: DialogConfig) -> None:
        self.state = DialogState(config=config)
        self._participants = [config.participant_a, config.participant_b]
        # Standardlabels setzen wenn keine Rolle definiert
        provider_labels = {"openai": "GPT", "anthropic": "Claude"}
        for p in self._participants:
            if not p.role_label:
                p.role_label = provider_labels.get(p.provider.value, p.provider.value)
        # System-Prompts mit Thema + Regeln anreichern
        for p in self._participants:
            p.system_prompt = self._build_system_prompt(p)

    # ----- Hilfsmethoden -----

    def _build_system_prompt(self, participant: Participant) -> str:
        cfg = self.state.config
        base = f"Du nimmst an einem Dialog zum Thema \"{cfg.topic}\" teil.\n"
        if participant.role_label:
            base += f"Deine Rolle / Perspektive: {participant.role_label}.\n"
        if cfg.rules:
            base += f"Zusätzliche Regeln: {cfg.rules}\n"
        base += (
            "Beziehe dich auf die vorherigen Beiträge deines Gesprächspartners. "
            "Halte dich kurz und prägnant (max. 3-4 Absätze)."
        )
        if participant.role_label:
            base += " Antworte aus deiner zugewiesenen Perspektive."
        if participant.system_prompt:
            base += f"\n\nZusätzlicher Kontext: {participant.system_prompt}"
        return base

    @property
    def current_participant(self) -> Participant:
        idx = self.state.current_turn % 2
        return self._participants[idx]

    @property
    def finished(self) -> bool:
        return self.state.current_turn >= self.state.config.max_turns

    # ----- Haupt-Loop -----

    async def run_dialog(self) -> AsyncIterator[str]:
        """Generator, der SSE-formatierte JSON-Strings liefert."""
        while not self.finished:
            participant = self.current_participant
            content_parts: list[str] = []

            # SSE: Turn-Start
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
                # SSE: Token-Stream
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

            # SSE: Turn-Ende
            yield self._sse_event("turn_end", {
                "turn": self.state.current_turn - 1,
                "provider": participant.provider.value,
                "role_label": participant.role_label,
                "content": full_content,
                "finished": self.finished,
            })

            # Kleine Pause zwischen Turns
            await asyncio.sleep(0.3)

        # SSE: Dialog komplett
        yield self._sse_event("dialog_end", {"total_turns": self.state.current_turn})

    async def inject_user_message(self, message: str) -> None:
        """Nutzer-Eingriff: Nachricht wird dem Verlauf hinzugefügt."""
        self.state.messages.append(
            DialogMessage(
                provider=self.current_participant.provider,  # wird wie Kontext behandelt
                role_label="Moderator (Nutzer)",
                content=message,
            )
        )

    @staticmethod
    def _sse_event(event_type: str, data: dict) -> str:
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"event: {event_type}\ndata: {payload}\n\n"
