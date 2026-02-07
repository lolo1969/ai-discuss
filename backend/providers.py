"""AI provider abstraction (OpenAI + Anthropic)."""

from __future__ import annotations

from typing import AsyncIterator

import anthropic
import openai

from backend.config import (
    ANTHROPIC_MODEL,
    MAX_TOKENS,
    OPENAI_MODEL,
    get_anthropic_api_key,
    get_openai_api_key,
)
from backend.schemas import DialogMessage, Provider, Role


def _build_openai_messages(
    system_prompt: str,
    history: list[DialogMessage],
    current_provider: Provider,
) -> list[dict]:
    """Build the OpenAI-compatible message list."""
    msgs: list[dict] = []
    if system_prompt:
        msgs.append({"role": Role.SYSTEM.value, "content": system_prompt})
    for m in history:
        # Own messages = assistant, other's = user
        role = Role.ASSISTANT.value if m.provider == current_provider else Role.USER.value
        msgs.append({"role": role, "content": f"[{m.role_label}]: {m.content}"})
    return msgs


def _build_anthropic_messages(
    history: list[DialogMessage],
    current_provider: Provider,
) -> list[dict]:
    """Build the Anthropic-compatible message list."""
    msgs: list[dict] = []
    for m in history:
        role = "assistant" if m.provider == current_provider else "user"
        msgs.append({"role": role, "content": f"[{m.role_label}]: {m.content}"})
    # Anthropic requires the first message to have role=user.
    # If the list is empty or starts with assistant, insert a placeholder.
    if not msgs or msgs[0]["role"] == "assistant":
        msgs.insert(0, {"role": "user", "content": "(Start of dialog)"})
    return msgs


# ---------------------------------------------------------------------------
# Streaming generators
# ---------------------------------------------------------------------------

async def stream_openai(
    system_prompt: str,
    history: list[DialogMessage],
    current_provider: Provider,
) -> AsyncIterator[str]:
    """Stream tokens from OpenAI."""
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please add it to .env.")
    client = openai.AsyncOpenAI(api_key=api_key)
    messages = _build_openai_messages(system_prompt, history, current_provider)
    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def stream_anthropic(
    system_prompt: str,
    history: list[DialogMessage],
    current_provider: Provider,
) -> AsyncIterator[str]:
    """Stream tokens from Anthropic."""
    api_key = get_anthropic_api_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set. Please add it to .env.")
    client = anthropic.AsyncAnthropic(api_key=api_key)
    messages = _build_anthropic_messages(history, current_provider)
    async with client.messages.stream(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt or "You are a helpful conversation partner.",
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def stream_response(
    provider: Provider,
    system_prompt: str,
    history: list[DialogMessage],
) -> AsyncIterator[str]:
    """Universal dispatcher."""
    if provider == Provider.OPENAI:
        async for token in stream_openai(system_prompt, history, provider):
            yield token
    elif provider == Provider.ANTHROPIC:
        async for token in stream_anthropic(system_prompt, history, provider):
            yield token
    else:
        raise ValueError(f"Unknown provider: {provider}")
