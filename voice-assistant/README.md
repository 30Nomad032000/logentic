# Hyper-Localized Multilingual Voice Assistant

A voice assistant that enables users to interact with digital services using natural voice commands in regional and low-resource Indian languages. Built with edge computing and agentic workflows.

## Project Overview

This project addresses the gap in existing voice assistants which primarily support global languages. Our solution provides:

- **Multilingual Support**: 21+ Indian languages including Hindi, Malayalam, Tamil, Telugu, Bengali, etc.
- **Edge Computing**: Raspberry Pi integration for local input/output handling
- **Agentic Workflows**: LangGraph-based orchestration for intelligent task execution
- **Accessibility**: Voice-first design for regional and accessibility requirements

## Architecture

```
Edge Device (RPi) → Server (ASR/NLU/Agents/TTS) → Edge Device (Audio Response)
```

See [docs/SPRINT_1_PLAN.md](docs/SPRINT_1_PLAN.md) for detailed architecture.

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended) or CPU
- 16GB+ RAM for local model inference

### Installation

```bash
# Clone repository
cd voice-assistant

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Start API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/transcribe` | POST | Audio to text (ASR) |
| `/api/process` | POST | Full pipeline (ASR → NLU → Agent → Response) |
| `/api/tts` | POST | Text to speech |
| `/api/text` | POST | Text input processing (skip ASR) |
| `/ws` | WebSocket | Real-time streaming |

### Example Usage

```python
import requests

# Transcribe audio
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/transcribe",
        files={"audio": f},
        data={"language": "hi"}  # Hindi
    )
    print(response.json())

# Process text directly
response = requests.post(
    "http://localhost:8000/api/text",
    data={"text": "What is the weather today?", "language": "en"}
)
print(response.json())
```

## Project Structure

```
voice-assistant/
├── docs/                    # Documentation
├── src/
│   ├── asr/                 # Speech recognition
│   ├── tts/                 # Text-to-speech
│   ├── nlu/                 # Natural language understanding
│   ├── agents/              # Agentic workflows (LangGraph)
│   ├── edge/                # Edge device code
│   └── api/                 # FastAPI endpoints
├── tests/                   # Test files
├── config/                  # Configuration
└── requirements.txt
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| ASR | Meta Omnilingual ASR / OpenAI Whisper |
| TTS | AI4Bharat Indic Parler-TTS |
| Agent Framework | LangGraph |
| API | FastAPI |
| Edge Platform | Raspberry Pi 5 |

## Sprint Progress

- [x] Sprint 1: Research, Planning & Foundation
  - [x] Technology stack research
  - [x] System architecture design
  - [x] Development environment setup
  - [x] Basic module implementation

- [ ] Sprint 2: Core Implementation (Upcoming)
- [ ] Sprint 3: Integration & Testing
- [ ] Sprint 4: Edge Deployment & Demo

## References

1. Meta AI - Omnilingual ASR (2025)
2. AI4Bharat - Multilingual ASR/TTS for Indian Languages
3. LangGraph Documentation
4. IEEE Papers on Multimodal Assistive Technologies

## License

This project is developed as part of MCA Final Year Project.

## Contributors

- Ebin (MCA Student)
