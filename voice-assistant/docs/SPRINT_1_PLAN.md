# Sprint 1: Research, Planning & Foundation Setup

## Project: Hyper-Localized Multilingual Voice Assistant
### Using Edge Computing and Agentic Workflows

---

## Sprint 1 Goals

1. Complete technology stack research and selection
2. Design system architecture
3. Setup development environment
4. Build proof-of-concept for core components (ASR, TTS, Agent orchestration)
5. Document findings and establish project foundation

---

## 1. Technology Stack Selection

### 1.1 Automatic Speech Recognition (ASR)

| Option | Languages | Pros | Cons | Recommendation |
|--------|-----------|------|------|----------------|
| **Meta Omnilingual ASR** | 1600+ (incl. Indian) | Best multilingual support, Apache 2.0, supports Tulu, Marwari, Bagheli | Large model sizes (300M-7B) | **PRIMARY** |
| **OpenAI Whisper** | 99 languages | Well-tested, good accuracy, multiple sizes | Limited Indian language support | **FALLBACK** |
| **AI4Bharat IndicASR** | 13 Indian languages | Specialized for Indian languages | Fewer languages | **SPECIALIZED** |

**Selected: Meta Omnilingual ASR** (primary) + **Whisper** (fallback for lighter deployment)

### 1.2 Text-to-Speech (TTS)

| Option | Languages | Features | Recommendation |
|--------|-----------|----------|----------------|
| **AI4Bharat Indic Parler-TTS** | 21 Indian languages | Emotion support, HuggingFace integration | **PRIMARY** |
| **AI4Bharat IndicF5** | 11 Indian languages | Near-human quality, 1417 hrs training | **ALTERNATIVE** |
| **TDIL-DC TTS** | 13 Indian languages | Government-backed, HTS engine | **FALLBACK** |

**Selected: AI4Bharat Indic Parler-TTS** (supports Malayalam, Hindi, and emotions)

### 1.3 Agentic Workflow Framework

| Framework | Approach | Best For | Recommendation |
|-----------|----------|----------|----------------|
| **LangGraph** | Stateful graphs | Complex orchestration, branching, error handling | **PRIMARY** |
| **CrewAI** | Role-based teams | Task delegation, multi-agent coordination | **SECONDARY** |
| **LangChain** | Chains/pipelines | Simple sequential workflows | **BASE LAYER** |

**Selected: LangGraph** (for complex workflow orchestration) + **LangChain** (base utilities)

### 1.4 Edge Computing Platform

| Platform | Specs | Pros | Cons |
|----------|-------|------|------|
| **Raspberry Pi 5** | 8GB RAM, ARM Cortex-A76 | Best performance, AI HAT support | Higher cost |
| **Raspberry Pi 4** | 4-8GB RAM | Widely available, cheaper | Less powerful |
| **Orange Pi 5** | RK3588S, 8GB | Good NPU support | Less community support |

**Selected: Raspberry Pi 5** (8GB) with optional **AI HAT+** for hardware acceleration

### 1.5 LLM for Intent Understanding

| Option | Size | Deployment | Recommendation |
|--------|------|------------|----------------|
| **Qwen 2.5** | 0.5B-7B | Edge-friendly | **EDGE** |
| **Claude API** | Cloud | Best reasoning | **CLOUD** |
| **Llama 3.2** | 1B-3B | Edge-optimized | **ALTERNATIVE** |

**Selected: Hybrid approach** - Qwen 2.5 (1.5B) on edge for simple queries, Claude API for complex tasks

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDGE DEVICE (Raspberry Pi 5)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Microphone  │    │    Camera    │    │   Speaker    │                   │
│  │   (USB/I2S)  │    │  (Optional)  │    │  (USB/I2S)   │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────▲───────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   │                            │
│  ┌──────────────────────────────────────────────┴───────┐                   │
│  │              INPUT HANDLER MODULE                     │                   │
│  │  - Wake word detection (Porcupine/OpenWakeWord)      │                   │
│  │  - Audio capture & preprocessing                      │                   │
│  │  - VAD (Voice Activity Detection)                     │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              EDGE CONTROLLER                          │                   │
│  │  - Request queuing                                    │                   │
│  │  - Response caching                                   │                   │
│  │  - Offline fallback handling                          │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │ (Network: WebSocket/gRPC)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVER / CLOUD LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              ASR MODULE (Speech-to-Text)              │                   │
│  │  - Meta Omnilingual ASR (1600+ languages)            │                   │
│  │  - Whisper fallback                                   │                   │
│  │  - Language detection                                 │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              NLU MODULE (Intent Understanding)        │                   │
│  │  - Intent classification                              │                   │
│  │  - Entity extraction                                  │                   │
│  │  - Context management                                 │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │         AGENTIC WORKFLOW ORCHESTRATOR (LangGraph)     │                   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │                   │
│  │  │ Info Agent  │  │ Task Agent  │  │ Smart Home  │   │                   │
│  │  │ (Search/QA) │  │ (Calendar)  │  │   Agent     │   │                   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              TTS MODULE (Text-to-Speech)              │                   │
│  │  - AI4Bharat Indic Parler-TTS                        │                   │
│  │  - Emotion-aware synthesis                            │                   │
│  │  - 21 Indian language support                         │                   │
│  └──────────────────────────┬───────────────────────────┘                   │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
                    [Audio Response to Edge Device]
```

---

## 3. Sprint 1 Deliverables Checklist

### Week 1: Research, Setup & Initial PoCs
- [x] Technology stack research and selection
- [x] System architecture design
- [x] Development environment setup
- [x] Project repository structure
- [x] ASR PoC: Whisper integration for basic speech recognition
- [x] TTS PoC: AI4Bharat TTS for Hindi/Malayalam output

### Week 2: PoC Completion & Integration
- [ ] Agent PoC: Basic LangGraph workflow with 2 simple agents
- [ ] Edge PoC: Basic audio capture on Raspberry Pi (or simulation)
- [ ] Basic pipeline: Audio → ASR → Simple Response → TTS
- [ ] API endpoint design
- [ ] Sprint 1 documentation and presentation
- [ ] Sprint 2 planning

---

## 4. Development Environment Setup

### 4.1 Python Environment
```bash
# Python 3.10+ required
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4.2 Required Dependencies
See `requirements.txt` for full list. Key packages:
- `torch` / `torchaudio` - ML framework
- `transformers` - HuggingFace models
- `openai-whisper` - ASR fallback
- `langchain` / `langgraph` - Agent orchestration
- `fastapi` / `uvicorn` - API server
- `sounddevice` / `pyaudio` - Audio handling

### 4.3 Hardware Requirements (Development)
- **Minimum**: 16GB RAM, GPU with 8GB VRAM (for local ASR/TTS)
- **Recommended**: 32GB RAM, GPU with 12GB+ VRAM
- **Cloud Alternative**: Use HuggingFace Inference API or RunPod

### 4.4 Hardware Requirements (Edge Deployment)
- Raspberry Pi 5 (8GB RAM)
- USB Microphone (e.g., ReSpeaker USB Mic Array)
- USB Speaker or 3.5mm audio output
- MicroSD Card (64GB+ recommended)
- Optional: AI HAT+ for hardware acceleration

---

## 5. Project Directory Structure

```
voice-assistant/
├── docs/                    # Documentation
│   ├── SPRINT_1_PLAN.md    # This file
│   ├── architecture/        # Architecture diagrams
│   └── api/                 # API documentation
├── src/
│   ├── asr/                 # Speech recognition module
│   │   ├── __init__.py
│   │   ├── whisper_asr.py   # Whisper implementation
│   │   └── omnilingual.py   # Meta Omnilingual ASR
│   ├── tts/                 # Text-to-speech module
│   │   ├── __init__.py
│   │   └── indic_tts.py     # AI4Bharat TTS
│   ├── nlu/                 # Natural language understanding
│   │   ├── __init__.py
│   │   └── intent.py        # Intent classification
│   ├── agents/              # Agentic workflows
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # LangGraph orchestrator
│   │   └── tools/           # Agent tools
│   ├── edge/                # Edge device code
│   │   ├── __init__.py
│   │   ├── audio_handler.py # Audio capture/playback
│   │   └── client.py        # Edge-to-server communication
│   └── api/                 # API endpoints
│       ├── __init__.py
│       └── main.py          # FastAPI application
├── tests/                   # Test files
├── config/                  # Configuration files
│   └── settings.yaml        # Main configuration
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker setup (optional)
└── README.md                # Project overview
```

---

## 6. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Large model sizes exceed edge capacity | High | High | Use server-based processing, edge for I/O only |
| Poor ASR accuracy for low-resource languages | High | Medium | Use Omnilingual ASR, collect local data for fine-tuning |
| Network latency affects UX | Medium | Medium | Implement caching, offline fallbacks |
| Hardware unavailability (Raspberry Pi) | Medium | Low | Develop with Docker simulation first |
| API costs for cloud LLM | Low | Medium | Use local models for simple queries, rate limiting |

---

## 7. Success Metrics for Sprint 1

| Metric | Target |
|--------|--------|
| ASR accuracy (Hindi) | >85% word accuracy on test sentences |
| ASR accuracy (Malayalam) | >80% word accuracy on test sentences |
| TTS quality | Intelligible output in 2+ languages |
| End-to-end latency | <5 seconds for simple queries |
| Agent task completion | 3+ demo tasks working |

---

## 8. References & Resources

### Research Papers
1. Meta AI - Omnilingual ASR (Nov 2025)
2. AI4Bharat - Multilingual ASR for Indian Languages
3. IEEE papers from project references

### Key Repositories
- [Meta Omnilingual ASR](https://github.com/facebookresearch/omnilingual-asr)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [AI4Bharat Indic-TTS](https://github.com/AI4Bharat/Indic-TTS)
- [LangGraph](https://github.com/langchain-ai/langgraph)

### Documentation
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [LangChain Documentation](https://python.langchain.com/docs)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)

---

## Next Steps (Sprint 2 Preview)

1. Implement full ASR pipeline with language detection
2. Build comprehensive agent toolkit (5+ tools)
3. Deploy server components with Docker
4. Begin Raspberry Pi edge integration
5. User interface development (optional web dashboard)
