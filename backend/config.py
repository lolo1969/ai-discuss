"""Zentrale Konfiguration – liest Werte aus .env oder Umgebungsvariablen."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# .env im Projektverzeichnis laden (ein Verzeichnis über backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"


def _load_env() -> None:
    """Lädt die .env-Datei jedes Mal neu (override=True)."""
    load_dotenv(_env_path, override=True)


def get_openai_api_key() -> str:
    _load_env()
    return os.getenv("OPENAI_API_KEY", "")


def get_anthropic_api_key() -> str:
    _load_env()
    return os.getenv("ANTHROPIC_API_KEY", "")


# Abwärtskompatible Konstanten – werden beim Import gesetzt
_load_env()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Standardmodelle – können bei Bedarf angepasst werden
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Maximale Tokens pro Antwort
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
