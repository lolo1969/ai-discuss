# AI-Discuss – AI Dialog Platform

Two different AI models (OpenAI GPT + Anthropic Claude) engage in a turn-based dialog about a user-defined topic. The user observes the conversation in real-time (token streaming) and can optionally intervene as a moderator.

## Architecture

```
Frontend (Vanilla HTML/CSS/JS)
    ↕ SSE Stream + REST API
Backend (FastAPI / Python)
    ↕                ↕
OpenAI API      Anthropic API
```

## Features

- **Two real AI providers** – OpenAI GPT and Anthropic Claude
- **Shared conversation history** – both AIs see all previous messages
- **Turn-based** – alternating responses with real-time streaming (SSE)
- **Configurable roles** – each AI can speak from a given perspective
- **Customizable** – topic, roles, rules, and number of turns
- **User as moderator** – optionally intervene during the dialog
- **Stop criterion** – dialog ends after a defined number of turns

## Quick Start

### 1. Install dependencies

```bash
cd AI-Discuss
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start the server

```bash
uvicorn backend.app:app --reload --port 8000
```

### 4. Open in browser

Navigate to: **http://localhost:8000**

## API Endpoints

| Method   | Path                                | Description                       |
|----------|-------------------------------------|-----------------------------------|
| `POST`   | `/api/dialog/start`                 | Start a new dialog                |
| `GET`    | `/api/dialog/{id}/stream`           | SSE stream for the dialog         |
| `POST`   | `/api/dialog/{id}/intervene`        | User intervention (moderator)     |
| `GET`    | `/api/dialog/{id}/state`            | Get current dialog state          |
| `DELETE` | `/api/dialog/{id}`                  | Delete a session                  |

## Configuration (Environment Variables)

| Variable           | Default                          | Description                     |
|--------------------|----------------------------------|---------------------------------|
| `OPENAI_API_KEY`   | –                                | OpenAI API key                  |
| `ANTHROPIC_API_KEY` | –                               | Anthropic API key               |
| `OPENAI_MODEL`     | `gpt-4o`                        | OpenAI model                    |
| `ANTHROPIC_MODEL`  | `claude-sonnet-4-20250514` | Anthropic model                 |
| `MAX_TOKENS`       | `1024`                           | Max tokens per response         |

## Project Structure

```
AI-Discuss/
├── backend/
│   ├── __init__.py
│   ├── app.py          # FastAPI application + routes
│   ├── config.py       # Configuration (.env)
│   ├── engine.py       # Dialog engine (orchestration)
│   ├── providers.py    # AI providers (OpenAI, Anthropic)
│   └── schemas.py      # Pydantic models
├── frontend/
│   ├── index.html      # Main HTML
│   ├── style.css       # Dark-mode styling
│   └── app.js          # Frontend logic (SSE, UI)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
