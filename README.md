# AI-Discuss – KI-Dialog-Plattform

Zwei unterschiedliche KI-Modelle (OpenAI GPT + Anthropic Claude) diskutieren dialogisch über ein vom Nutzer gewähltes Thema. Der Nutzer beobachtet den Dialog in Echtzeit (Token-Streaming) und kann optional als Moderator eingreifen.

## Architektur

```
Frontend (Vanilla HTML/CSS/JS)
    ↕ SSE-Stream + REST API
Backend (FastAPI / Python)
    ↕                ↕
OpenAI API      Anthropic API
```

## Features

- **Zwei echte KI-Provider** – OpenAI GPT und Anthropic Claude
- **Gemeinsamer Gesprächsverlauf** – beide KIs sehen alle bisherigen Beiträge
- **Turn-basiert** – abwechselnde Antworten mit Echtzeit-Streaming (SSE)
- **Feste Rollen** – jede KI spricht aus einer vorgegebenen Perspektive
- **Konfigurierbar** – Thema, Rollen, Regeln und Anzahl der Züge
- **Nutzer als Moderator** – optional während des Dialogs eingreifen
- **Stop-Kriterium** – Dialog endet nach definierter Anzahl von Turns

## Schnellstart

### 1. Abhängigkeiten installieren

```bash
cd AI-Discuss
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

### 2. API-Keys konfigurieren

```bash
cp .env.example .env
# Dann .env bearbeiten und die API-Keys eintragen:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Server starten

```bash
uvicorn backend.app:app --reload --port 8000
```

### 4. Öffnen

Im Browser: **http://localhost:8000**

## API-Endpunkte

| Methode  | Pfad                                | Beschreibung                      |
|----------|-------------------------------------|-----------------------------------|
| `POST`   | `/api/dialog/start`                 | Neuen Dialog starten              |
| `GET`    | `/api/dialog/{id}/stream`           | SSE-Stream für den Dialog         |
| `POST`   | `/api/dialog/{id}/intervene`        | Nutzer-Eingriff (Moderator)       |
| `GET`    | `/api/dialog/{id}/state`            | Aktuellen Zustand abrufen         |
| `DELETE` | `/api/dialog/{id}`                  | Session löschen                   |

## Konfiguration (Umgebungsvariablen)

| Variable           | Standard                         | Beschreibung                    |
|--------------------|----------------------------------|---------------------------------|
| `OPENAI_API_KEY`   | –                                | OpenAI API-Schlüssel            |
| `ANTHROPIC_API_KEY` | –                               | Anthropic API-Schlüssel         |
| `OPENAI_MODEL`     | `gpt-4o`                        | OpenAI-Modell                   |
| `ANTHROPIC_MODEL`  | `claude-sonnet-4-20250514` | Anthropic-Modell                |
| `MAX_TOKENS`       | `1024`                           | Max. Tokens pro Antwort         |

## Projektstruktur

```
AI-Discuss/
├── backend/
│   ├── __init__.py
│   ├── app.py          # FastAPI-Anwendung + Routen
│   ├── config.py       # Konfiguration (.env)
│   ├── engine.py       # Dialog-Engine (Orchestrierung)
│   ├── providers.py    # KI-Provider (OpenAI, Anthropic)
│   └── schemas.py      # Pydantic-Modelle
├── frontend/
│   ├── index.html      # Haupt-HTML
│   ├── style.css       # Dark-Mode Styling
│   └── app.js          # Frontend-Logik (SSE, UI)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
