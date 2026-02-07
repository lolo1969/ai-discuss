"""Central configuration – reads values from .env or environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"


def _load_env() -> None:
    """Reload the .env file on every call (override=True)."""
    load_dotenv(_env_path, override=True)


def get_openai_api_key() -> str:
    _load_env()
    return os.getenv("OPENAI_API_KEY", "")


def get_anthropic_api_key() -> str:
    _load_env()
    return os.getenv("ANTHROPIC_API_KEY", "")


# Backward-compatible constants – set on import
_load_env()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Default models – can be adjusted as needed
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Maximum tokens per response
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
