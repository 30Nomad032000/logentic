# Logentic - Hyper-Localized Multilingual Voice Assistant

A voice assistant enabling interaction with digital services using natural voice commands in regional Indian languages. Built with edge computing (Raspberry Pi 5) and agentic workflows (LangGraph).

## Features

- **21+ Indian Languages** — Hindi, Malayalam, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Punjabi, Urdu, English, and more
- **Edge Computing** — Runs on Raspberry Pi 5 with local model inference
- **Agentic Workflows** — LangGraph-based orchestrator routes to specialized agents (Info, Task, Chat, Smart Home)
- **React Dashboard** — Real-time monitoring with stats, health checks, latency breakdown, and conversation logs
- **Single-Process Deployment** — FastAPI serves both the API and the React frontend (no Node.js needed in production)

## Architecture

```
Audio → ASR (Whisper) → Translation (ML→EN) → Intent Detection →
LLM (Qwen) → Translation (EN→ML) → TTS → Audio Response
```

```
Edge Device (RPi 5) → Server (ASR/NLU/Agents/TTS) → Edge Device (Audio Response)
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend development only, not needed in production)
- CUDA GPU (recommended) or CPU
- 16GB+ RAM for local model inference

### Backend Setup

```bash
cd voice-assistant
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd voice-assistant/frontend
npm install
npm run build                # Outputs to src/api/static/
```

### Run

```bash
cd voice-assistant
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` to access the dashboard.

### Development Mode

```bash
# Terminal 1: Backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (HMR, proxied to backend)
cd voice-assistant/frontend && npm run dev   # → http://localhost:3000
```

## Project Structure

```
voice-assistant/
├── frontend/                 # React + Vite + TypeScript dashboard
│   ├── src/
│   │   ├── api/              # API client & TypeScript types
│   │   ├── components/       # React components (layout, stats, health, etc.)
│   │   ├── context/          # Dashboard state (Context + useReducer)
│   │   ├── hooks/            # Custom hooks (polling, WebSocket)
│   │   └── styles/           # CSS variables & globals
│   ├── package.json
│   └── vite.config.ts
├── src/
│   ├── asr/                  # Speech-to-text (Whisper, Indic ASR)
│   ├── tts/                  # Text-to-speech (MMS-TTS, Cartesia, Chatterbox)
│   ├── translation/          # Bidirectional ML↔EN (IndicTrans2)
│   ├── llm/                  # Response generation (Qwen 2.5)
│   ├── agents/               # Task orchestration (LangGraph)
│   ├── pipeline/             # End-to-end orchestrator
│   ├── api/                  # FastAPI + WebSocket + static serving
│   ├── db/                   # SQLite conversation storage
│   └── config.py             # YAML config loader
├── config/                   # settings.yaml
├── tests/                    # pytest test suite
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with component status |
| `/api/transcribe` | POST | Audio to text (ASR) |
| `/api/process` | POST | Full pipeline (ASR + NLU + Agent + Response) |
| `/api/tts` | POST | Text to speech synthesis |
| `/api/text` | POST | Text input processing (skip ASR) |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/dashboard/conversations` | GET | Recent conversations |
| `/ws` | WebSocket | Real-time audio streaming |
| `/ws/stream` | WebSocket | Full STT → LLM → TTS streaming |

## Tech Stack

| Layer | Technology |
|-------|------------|
| **ASR** | OpenAI Whisper, Pingala Indic ASR |
| **TTS** | MMS-TTS (offline), Cartesia (online), Chatterbox |
| **Translation** | IndicTrans2, SentencePiece |
| **LLM** | Qwen 2.5 Instruct (0.5B–7B, local) |
| **Agents** | LangGraph, LangChain |
| **API** | FastAPI, Uvicorn, WebSockets |
| **Frontend** | React 18, Vite, TypeScript, CSS Modules |
| **Database** | SQLite |
| **Edge** | Raspberry Pi 5 |
| **ML** | PyTorch, Transformers, Accelerate |

## Configuration

Main config: `voice-assistant/config/settings.yaml`

- ASR engine and model size
- TTS backend (mms / cartesia / indic_parler / chatterbox)
- LLM model size (0.5b / 1.5b / 3b / 7b)
- Translation settings
- Agent orchestrator (langgraph / clawgo)

## Testing

```bash
cd voice-assistant
pytest tests/ -v
```

## License

This project is developed as part of MCA Final Year Project.
