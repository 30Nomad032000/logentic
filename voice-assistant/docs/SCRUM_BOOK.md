# Scrum Book: Hyper-Localized Multilingual Voice Assistant

## Project Overview

**Project Name:** Hyper-Localized Multilingual Voice Assistant
**Technology Stack:** Edge Computing + Agentic Workflows
**Primary Language:** Malayalam
**Team Size:** 1-2 developers
**Sprint Duration:** 2 weeks
**Total Sprints Planned:** 6 sprints (12 weeks)

---

## 1. System Representation

### 1.1 Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VOICE ASSISTANT SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────┐                                                               │
│    │  User   │                                                               │
│    │(Malayalam│                                                              │
│    │ Speaker)│                                                               │
│    └────┬────┘                                                               │
│         │                                                                    │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         ├───►│  UC1: Speak Voice Command                            │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │                         │                                          │
│         │                         ▼ <<include>>                              │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         │    │  UC2: Transcribe Speech (ASR)                        │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │                         │                                          │
│         │                         ▼ <<include>>                              │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         │    │  UC3: Translate Malayalam ↔ English                  │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │                         │                                          │
│         │                         ▼ <<include>>                              │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         │    │  UC4: Process Intent & Generate Response (LLM)       │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │                         │                                          │
│         │         ┌───────────────┼───────────────┐                         │
│         │         ▼               ▼               ▼                         │
│         │    ┌─────────┐    ┌─────────┐    ┌─────────────┐                 │
│         │    │UC4a:    │    │UC4b:    │    │UC4c:        │                 │
│         │    │Answer   │    │Execute  │    │Control      │                 │
│         │    │Question │    │Task     │    │Smart Home   │                 │
│         │    └─────────┘    └─────────┘    └─────────────┘                 │
│         │                         │                                          │
│         │                         ▼ <<include>>                              │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         │    │  UC5: Synthesize Speech Response (TTS)               │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │                         │                                          │
│         │◄────────────────────────┘                                          │
│         │                                                                    │
│    ┌────┴────┐                                                               │
│    │  User   │◄── Receives spoken response in Malayalam                     │
│    └─────────┘                                                               │
│                                                                              │
│    ┌─────────┐                                                               │
│    │  Admin  │                                                               │
│    └────┬────┘                                                               │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         ├───►│  UC6: Configure System Settings                      │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         ├───►│  UC7: Monitor System Performance                     │       │
│         │    └──────────────────────────────────────────────────────┘       │
│         │    ┌──────────────────────────────────────────────────────┐       │
│         └───►│  UC8: Add/Update Agent Tools                         │       │
│              └──────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Use Case Descriptions

| UC ID | Use Case | Actor | Description | Priority |
|-------|----------|-------|-------------|----------|
| UC1 | Speak Voice Command | User | User speaks a command/query in Malayalam | High |
| UC2 | Transcribe Speech | System | Convert Malayalam speech to text using Meta ASR | High |
| UC3 | Translate Text | System | Translate between Malayalam and English | High |
| UC4 | Process Intent | System | LLM understands intent and generates response | High |
| UC4a | Answer Question | System | Provide information/answers to queries | High |
| UC4b | Execute Task | System | Perform tasks like reminders, calculations | Medium |
| UC4c | Control Smart Home | System | Control IoT devices (future) | Low |
| UC5 | Synthesize Speech | System | Convert text response to Malayalam speech | High |
| UC6 | Configure Settings | Admin | Modify system configuration | Medium |
| UC7 | Monitor Performance | Admin | View system metrics and logs | Low |
| UC8 | Manage Agent Tools | Admin | Add or update agent capabilities | Medium |

---

### 1.3 Activity Diagram - Voice Command Processing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVITY DIAGRAM: Voice Command Flow                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────┐
                              │   START   │
                              └─────┬─────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ User Speaks Command │
                         │   (Malayalam)       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Capture Audio      │
                         │  (Microphone)       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  ASR Processing     │
                         │  (Meta ASR 1B)      │
                         │  [ONLINE]           │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Malayalam Text     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Translate ML → EN  │
                         │  (IndicTrans2)      │
                         │  [LOCAL]            │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  English Text       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  LLM Processing     │
                         │  (Qwen 2.5 1.5B)    │
                         │  [LOCAL]            │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   Answer    │ │   Execute   │ │   Agent     │
            │   Query     │ │   Task      │ │   Action    │
            └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  English Response   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Translate EN → ML  │
                         │  (IndicTrans2)      │
                         │  [LOCAL]            │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Malayalam Response │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  TTS Synthesis      │
                         │  (MMS-TTS)          │
                         │  [LOCAL]            │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Play Audio         │
                         │  (Speaker)          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              ┌───────────┐
                              │    END    │
                              └───────────┘
```

---

### 1.4 Activity Diagram - System Initialization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVITY DIAGRAM: System Startup                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────┐
                              │   START   │
                              └─────┬─────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Load Configuration │
                         │  (settings.yaml)    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │         PARALLEL LOAD          │
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │ Load Trans- │ │  Load LLM   │ │  Load TTS   │
            │ lation Model│ │  (Qwen)     │ │  (MMS)      │
            │ (IndicTrans)│ │             │ │             │
            └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                              ◇ All Loaded? ◇
                             ╱              ╲
                           Yes              No
                           ╱                  ╲
                          ▼                    ▼
               ┌─────────────────┐   ┌─────────────────┐
               │ Initialize      │   │  Log Error &    │
               │ Audio Handler   │   │  Retry/Exit     │
               └────────┬────────┘   └─────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Start API Server│
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ System Ready    │
               │ (Listening)     │
               └────────┬────────┘
                        │
                        ▼
                  ┌───────────┐
                  │    END    │
                  └───────────┘
```

---

## 2. Project Schedule - Ideal Burndown Chart

### 2.1 Sprint Overview

| Sprint | Duration | Focus Area | Story Points |
|--------|----------|------------|--------------|
| Sprint 1 | Week 1-2 | Research, Setup, ASR/TTS PoC | 21 |
| Sprint 2 | Week 3-4 | Translation, LLM Integration | 21 |
| Sprint 3 | Week 5-6 | Full Pipeline, API Development | 21 |
| Sprint 4 | Week 7-8 | Agent Framework, Tools | 18 |
| Sprint 5 | Week 9-10 | Edge Deployment, Optimization | 18 |
| Sprint 6 | Week 11-12 | Testing, Documentation, Polish | 15 |

**Total Story Points:** 114

### 2.2 Ideal Burndown Chart

```
Story
Points
  │
114├────●
   │     ╲
100├──────╲────
   │       ╲
 93├────────●
   │         ╲
 80├──────────╲────
   │           ╲
 72├────────────●
   │             ╲
 60├──────────────╲────
   │               ╲
 51├────────────────●
   │                 ╲
 40├──────────────────╲────
   │                   ╲
 33├────────────────────●
   │                     ╲
 20├──────────────────────╲────
   │                       ╲
 15├────────────────────────●
   │                         ╲
  0├──────────────────────────●────
   │     │     │     │     │     │
   └─────┴─────┴─────┴─────┴─────┴────► Sprints
       S1    S2    S3    S4    S5    S6


   Sprint Progress Table:
   ┌─────────┬─────────────┬────────────┬───────────────┬──────────┐
   │ Sprint  │ Points Done │ Remaining  │ % Complete    │ Actual   │
   ├─────────┼─────────────┼────────────┼───────────────┼──────────┤
   │ Start   │      0      │    114     │     0%        │    ✅    │
   │ S1 End  │     21      │     93     │    18%        │  21 pts  │
   │ S2 End  │     42      │     72     │    37%        │  21 pts  │
   │ S3 End  │     63      │     51     │    55%        │  21 pts  │
   │ S4 End  │     81      │     33     │    71%        │  18 pts  │
   │ S5 End  │     99      │     15     │    87%        │    --    │
   │ S6 End  │    114      │      0     │   100%        │    --    │
   └─────────┴─────────────┴────────────┴───────────────┴──────────┘

   * Sprints 1-4 COMPLETED. On track with ideal burndown.
```

### 2.3 Velocity Chart (Planned vs Actual)

```
Story
Points
   │          Planned ░░░   Actual ██
 25├──────────────────────────────────────
   │    ┌███┐ ┌███┐ ┌███┐
 21├────│ 21│ │ 21│ │ 21│────────────────
   │    │ A │ │ A │ │ A │ ┌███┐ ┌───┐
 18├────│   │ │   │ │   │ │ 18│ │ 18│────
   │    │   │ │   │ │   │ │ A │ │ P │ ┌───┐
 15├────│   │ │   │ │   │ │   │ │   │ │ 15│
   │    │   │ │   │ │   │ │   │ │   │ │ P │
 10├────│   │ │   │ │   │ │   │ │   │ │   │
   │    │   │ │   │ │   │ │   │ │   │ │   │
  5├────│   │ │   │ │   │ │   │ │   │ │   │
   │    │   │ │   │ │   │ │   │ │   │ │   │
  0├────┴───┴─┴───┴─┴───┴─┴───┴─┴───┴─┴───┴─
        S1    S2    S3    S4    S5    S6
                                 A=Actual P=Planned

   Avg Velocity (S1-S4): 20.25 pts/sprint
```

---

## 3. Detailed Product Backlog

### 3.1 Epic Overview

| Epic ID | Epic Name | Description | Priority |
|---------|-----------|-------------|----------|
| E1 | Speech Recognition | Malayalam speech-to-text capability | Critical |
| E2 | Translation | Malayalam ↔ English translation | Critical |
| E3 | Conversational AI | LLM-based response generation | Critical |
| E4 | Speech Synthesis | Malayalam text-to-speech | Critical |
| E5 | Pipeline Integration | End-to-end voice pipeline | High |
| E6 | Agent Framework | LangGraph-based agentic workflows | High |
| E7 | Edge Deployment | Raspberry Pi deployment | Medium |
| E8 | DevOps & Testing | CI/CD, testing, documentation | Medium |

### 3.2 Full Product Backlog

| ID | User Story | Epic | Priority | Points | Sprint |
|----|------------|------|----------|--------|--------|
| **SPRINT 1** |
| US-001 | As a developer, I want to research and select the tech stack so that we have the right tools | E1 | Critical | 3 | S1 |
| US-002 | As a developer, I want to design the system architecture so that the team has a clear blueprint | E5 | Critical | 3 | S1 |
| US-003 | As a developer, I want to set up the development environment so that I can start coding | E8 | Critical | 2 | S1 |
| US-004 | As a developer, I want to create the project structure so that code is organized | E8 | High | 2 | S1 |
| US-005 | As a user, I want speech-to-text for Malayalam so that my voice is understood | E1 | Critical | 5 | S1 |
| US-006 | As a user, I want text-to-speech for Malayalam so that I hear responses | E4 | Critical | 5 | S1 |
| US-007 | As a developer, I want to compare TTS options (MMS vs Cartesia) for quality | E4 | High | 1 | S1 |
| **SPRINT 2** |
| US-008 | As a user, I want my Malayalam speech translated to English for processing | E2 | Critical | 5 | S2 |
| US-009 | As a user, I want English responses translated back to Malayalam | E2 | Critical | 5 | S2 |
| US-010 | As a user, I want the assistant to understand and respond to my queries | E3 | Critical | 5 | S2 |
| US-011 | As a user, I want the assistant to remember our conversation context | E3 | High | 3 | S2 |
| US-012 | As a developer, I want to test the translation quality for accuracy | E2 | High | 3 | S2 |
| **SPRINT 3** |
| US-013 | As a user, I want to speak and get spoken responses end-to-end | E5 | Critical | 8 | S3 |
| US-014 | As a developer, I want a REST API to interact with the assistant | E5 | High | 5 | S3 |
| US-015 | As a developer, I want WebSocket support for real-time communication | E5 | High | 5 | S3 |
| US-016 | As a developer, I want proper error handling in the pipeline | E5 | High | 3 | S3 |
| **SPRINT 4** |
| US-017 | As a user, I want the assistant to perform tasks using agent tools | E6 | High | 5 | S4 |
| US-018 | As a developer, I want LangGraph orchestration for complex workflows | E6 | High | 5 | S4 |
| US-019 | As a user, I want the assistant to answer information queries | E6 | High | 3 | S4 |
| US-020 | As a user, I want the assistant to set reminders and tasks | E6 | Medium | 3 | S4 |
| US-021 | As a developer, I want to easily add new agent tools | E6 | Medium | 2 | S4 |
| **SPRINT 5** |
| US-022 | As a user, I want the assistant to run on Raspberry Pi | E7 | High | 5 | S5 |
| US-023 | As a developer, I want model optimization for edge deployment | E7 | High | 5 | S5 |
| US-024 | As a user, I want low latency responses (<3 seconds) | E7 | High | 3 | S5 |
| US-025 | As a developer, I want audio input/output on the Pi | E7 | High | 3 | S5 |
| US-026 | As a developer, I want caching for frequently used responses | E7 | Medium | 2 | S5 |
| **SPRINT 6** |
| US-027 | As a developer, I want comprehensive unit tests | E8 | High | 3 | S6 |
| US-028 | As a developer, I want integration tests for the pipeline | E8 | High | 3 | S6 |
| US-029 | As a developer, I want performance benchmarks documented | E8 | Medium | 2 | S6 |
| US-030 | As a developer, I want user documentation | E8 | Medium | 3 | S6 |
| US-031 | As a developer, I want API documentation | E8 | Medium | 2 | S6 |
| US-032 | As a user, I want a demo showcasing all features | E8 | High | 2 | S6 |

---

## 4. Sprint-wise Implementation Schedule

### Sprint 1: Research, Setup & Core PoCs (Week 1-2)

**Sprint Goal:** Establish foundation with working ASR and TTS

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T1.1 | Technology stack research | Dev | ✅ Done | 3 |
| T1.2 | System architecture design | Dev | ✅ Done | 3 |
| T1.3 | Development environment setup | Dev | ✅ Done | 2 |
| T1.4 | Project repository structure | Dev | ✅ Done | 2 |
| T1.5 | Whisper ASR integration | Dev | ✅ Done | 3 |
| T1.6 | Meta ASR 1B research | Dev | ✅ Done | 2 |
| T1.7 | MMS-TTS implementation | Dev | ✅ Done | 3 |
| T1.8 | Cartesia TTS integration | Dev | ✅ Done | 2 |
| T1.9 | TTS A/B comparison | Dev | ✅ Done | 1 |

**Sprint 1 Velocity:** 21 points ✅

---

### Sprint 2: Translation & LLM Integration (Week 3-4)

**Sprint Goal:** Complete translation layer and conversational AI

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T2.1 | IndicTrans2 ML→EN setup | Dev | ✅ Done | 3 |
| T2.2 | IndicTrans2 EN→ML setup | Dev | ✅ Done | 2 |
| T2.3 | Translation API wrapper | Dev | ✅ Done | 2 |
| T2.4 | Qwen 2.5 LLM integration | Dev | ✅ Done | 3 |
| T2.5 | Conversation memory | Dev | ✅ Done | 2 |
| T2.6 | System prompt tuning | Dev | ✅ Done | 2 |
| T2.7 | IndicTrans2-Dist (5x smaller) upgrade | Dev | ✅ Done | 3 |
| T2.8 | Qwen3 + llama.cpp backend | Dev | ✅ Done | 2 |
| T2.9 | Indic-to-Indic translation support | Dev | ✅ Done | 2 |

**Sprint 2 Velocity:** 21 points ✅

**Key Deliverables:**
- IndicTrans2-Dist models (~211M, 5x smaller, same quality)
- Qwen3 LLM with llama.cpp GGUF backend for fast CPU inference
- Direct Indic-to-Indic translation without English pivot
- Dual backend support (llamacpp + transformers)

---

### Sprint 3: Full Pipeline, API & Major Upgrade (Week 5-6)

**Sprint Goal:** Working end-to-end voice assistant with API, upgraded models, and dashboard

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T3.1 | Pingala V1 ASR engine (CPU-first, 2.94% WER) | Dev | ✅ Done | 3 |
| T3.2 | Pipecat pipeline framework integration | Dev | ✅ Done | 5 |
| T3.3 | FastAPI endpoints + dashboard serving | Dev | ✅ Done | 3 |
| T3.4 | WebSocket streaming (/ws/stream) | Dev | ✅ Done | 3 |
| T3.5 | Indic Parler-TTS Mini (69 voices) + Chatterbox TTS | Dev | ✅ Done | 2 |
| T3.6 | ONNX Runtime inference backend | Dev | ✅ Done | 3 |
| T3.7 | Typed configuration system (src/config.py) | Dev | ✅ Done | 2 |

**Sprint 3 Velocity:** 21 points ✅

**Key Deliverables:**
- Pingala V1 ASR (50%+ better accuracy, runs on CPU)
- Pipecat production-grade STT→LLM→TTS pipeline
- Indic Parler-TTS Mini with 69 voices and emotion control
- Chatterbox-Turbo 350M (low-compute alternative TTS)
- ONNX Runtime backend for accelerated inference
- Streaming WebSocket endpoint
- Typed dataclass configuration loaded from YAML

---

### Sprint 4: Agent Framework, Dashboard & Testing (Week 7-8)

**Sprint Goal:** Agentic capabilities, monitoring dashboard, database, and testing infrastructure

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T4.1 | LangGraph agent orchestrator | Dev | ✅ Done | 3 |
| T4.2 | ClawGo (OpenClaw) agent + Ollama BYOM | Dev | ✅ Done | 3 |
| T4.3 | Agent factory (langgraph/clawgo routing) | Dev | ✅ Done | 2 |
| T4.4 | SQLite database for conversation logging | Dev | ✅ Done | 2 |
| T4.5 | Frontend dashboard (HTML/CSS/JS) | Dev | ✅ Done | 3 |
| T4.6 | Dashboard API endpoints (stats, conversations) | Dev | ✅ Done | 2 |
| T4.7 | Comprehensive test suite (pytest fixtures, DB tests, API tests) | Dev | ✅ Done | 3 |

**Sprint 4 Velocity:** 18 points ✅

**Key Deliverables:**
- LangGraph stateful workflow with intent-based routing
- ClawGo/OpenClaw Pi agent with Ollama for local Qwen3 inference
- AgentFactory for switching between LangGraph and ClawGo backends
- SQLite database with conversation/message/metric models
- Real-time dashboard with stats, latency breakdown, conversation logs, language distribution, and live testing panel
- Dashboard served automatically at root (/) when API starts
- Comprehensive test suite: conftest.py fixtures, test_basic.py (core), test_database.py (DB CRUD), test_api.py (endpoints)
- Repository cleanup: removed 13 unnecessary files

---

### Sprint 5: Edge Deployment (Week 9-10)

**Sprint Goal:** Running on Raspberry Pi 5

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T5.1 | Pi 5 environment setup | Dev | ⬜ Todo | 2 |
| T5.2 | Model quantization | Dev | ⬜ Todo | 3 |
| T5.3 | ONNX conversion | Dev | ⬜ Todo | 3 |
| T5.4 | Audio I/O on Pi | Dev | ⬜ Todo | 3 |
| T5.5 | Response caching | Dev | ⬜ Todo | 2 |
| T5.6 | Performance profiling | Dev | ⬜ Todo | 2 |
| T5.7 | Latency optimization | Dev | ⬜ Todo | 3 |

**Sprint 5 Target:** 18 points

---

### Sprint 6: Testing & Documentation (Week 11-12)

**Sprint Goal:** Production-ready with documentation

| Task ID | Task | Assignee | Status | Points |
|---------|------|----------|--------|--------|
| T6.1 | Unit test suite | Dev | ✅ Done | 3 |
| T6.2 | Integration test suite | Dev | ✅ Done | 3 |
| T6.3 | Performance benchmarks | Dev | ✅ Done | 2 |
| T6.4 | User documentation | Dev | ✅ Done | 2 |
| T6.5 | API documentation | Dev | ✅ Done | 2 |
| T6.6 | Demo video/presentation | Dev | ✅ Done | 2 |
| T6.7 | Final polish & bug fixes | Dev | ✅ Done | 1 |

**Sprint 6 Target:** 15 points

---

## 5. Definition of Done (DoD)

A user story is considered **DONE** when:

- [ ] Code is written and follows project coding standards
- [ ] Unit tests are written and passing
- [ ] Code is reviewed (self-review for solo developer)
- [ ] Integration tests pass
- [ ] Documentation is updated
- [ ] Feature works on development environment
- [ ] No critical bugs remain
- [ ] Performance meets requirements

---

## 6. Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---------|------|-------------|--------|------------|
| R1 | Model too large for Pi | High | High | Use quantization, cloud fallback |
| R2 | Poor Malayalam ASR accuracy | Medium | High | Fine-tune on local data |
| R3 | High latency | Medium | Medium | Caching, model optimization |
| R4 | API costs exceed budget | Low | Medium | Use local models primarily |
| R5 | Hardware unavailability | Low | High | Develop with simulation first |

---

## 7. Project Metrics

### Key Performance Indicators (KPIs)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| ASR Accuracy (Malayalam) | >85% | ~97% (Pingala V1, 2.94% WER) | ✅ Exceeds |
| Translation Accuracy | >90% | ~93% (IndicTrans2-Dist) | ✅ Meets |
| End-to-end Latency | <3 sec | TBD (pending Pi deployment) | ⏳ Sprint 5 |
| TTS Quality (MOS) | >3.5/5 | TBD (Indic Parler-TTS Mini) | ⏳ Sprint 5 |
| Sprint Velocity | 18-21 pts | 20.25 avg (81/114 done) | ✅ On Track |
| Test Coverage | >70% | Basic suite (core + DB + API) | ✅ Foundation |
| Dashboard | Functional | Live w/ stats, logs, testing | ✅ Complete |

---

*Last Updated: Sprint 4, Week 8*
*Scrum Master: Self-managed*
*Product Owner: Self-managed*
