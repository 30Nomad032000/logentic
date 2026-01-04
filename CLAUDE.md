# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hyper-Localized Multilingual Voice Assistant - A voice assistant enabling interaction with digital services using natural voice commands in regional Indian languages. Built with edge computing (Raspberry Pi 5) and agentic workflows (LangGraph).

## Commands

### Installation
```bash
cd voice-assistant
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Running the Server
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
pytest tests/ -v                          # All tests
pytest tests/test_basic.py::TestASR -v    # Single test class
```

### Code Quality
```bash
black src/ tests/                         # Format
ruff check src/ tests/                    # Lint
```

### Demo Scripts
```bash
python scripts/demo_pipeline.py           # Full pipeline demo
python scripts/quick_demo.py              # Quick demo
python demos/demo_with_mic.py             # Microphone input
```

## Architecture

### Pipeline Flow
```
Audio → ASR (Whisper) → Translation (ML→EN) → Intent Detection →
LLM (Qwen) → Translation (EN→ML) → TTS → Audio Response
```

### Core Components (voice-assistant/src/)

| Directory | Purpose | Technology |
|-----------|---------|------------|
| `asr/` | Speech-to-text | Whisper, Indic ASR |
| `tts/` | Text-to-speech | MMS-TTS (offline), Cartesia (online) |
| `translation/` | Bidirectional ML↔EN | IndicTrans2 |
| `llm/` | Response generation | Qwen 2.5 (0.5B-7B variants) |
| `nlu/` | Intent classification | Keyword + ML models |
| `agents/` | Task orchestration | LangGraph stateful graphs |
| `pipeline/` | End-to-end orchestrator | Custom pipeline with timing |
| `api/` | REST endpoints | FastAPI + WebSocket |
| `edge/` | Raspberry Pi client | Async HTTP/WebSocket |

### Key Entry Points

- **API Server**: `src/api/main.py` - FastAPI application
- **Pipeline**: `src/pipeline/orchestrator.py` - `VoiceAssistantPipeline` class
- **Agent Orchestrator**: `src/agents/orchestrator.py` - LangGraph workflow

### Agent System

LangGraph-based orchestrator routes to specialized agents:
- **Info Agent**: Information queries and QA
- **Task Agent**: Task management and reminders
- **Chat Agent**: General conversation
- **Smart Home Agent**: Device control (optional)

### Configuration

Main config: `config/settings.yaml`
- ASR engine/model size
- TTS backend (mms/cartesia/indic_parler)
- LLM model size (0.5b/1.5b/3b/7b)
- Translation settings
- Agent configuration

### Supported Languages

Primary: Malayalam (ml)
Also: Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn), Marathi (mr), Gujarati (gu), Kannada (kn), Punjabi (pa), Urdu (ur), English (en)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/transcribe` | POST | Audio to text |
| `/api/process` | POST | Full pipeline |
| `/api/tts` | POST | Text to speech |
| `/api/text` | POST | Text-only (skip ASR) |
| `/ws` | WebSocket | Real-time streaming |

## Tech Stack

- **ML**: PyTorch, Transformers, Accelerate
- **ASR**: OpenAI Whisper
- **TTS**: MMS-TTS, Cartesia API
- **Translation**: IndicTrans2, SentencePiece
- **LLM**: Qwen 2.5 Instruct (local)
- **Agents**: LangGraph, LangChain
- **API**: FastAPI, Uvicorn, WebSockets
- **Edge**: Raspberry Pi 5 (target deployment)

## Requirements

- Python 3.10+
- CUDA GPU (recommended) or CPU
- 16GB+ RAM for local model inference
