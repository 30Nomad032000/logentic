# Sprint-wise Implementation Schedule

## Project: Hyper-Localized Multilingual Voice Assistant

---

## Sprint Overview

| Sprint | Duration | Focus | Points | Status |
|--------|----------|-------|--------|--------|
| Sprint 1 | Week 1-2 | Research, Setup, Core PoCs | 21 | ✅ Complete |
| Sprint 2 | Week 3-4 | Translation, LLM Integration | 21 | 🔄 In Progress |
| Sprint 3 | Week 5-6 | Full Pipeline, API | 21 | ⬜ Planned |
| Sprint 4 | Week 7-8 | Agent Framework | 18 | ⬜ Planned |
| Sprint 5 | Week 9-10 | Edge Deployment | 18 | ⬜ Planned |
| Sprint 6 | Week 11-12 | Testing, Documentation | 15 | ⬜ Planned |

---

## Sprint 1: Research, Setup & Core PoCs

### Sprint Goal
Establish the project foundation with working ASR and TTS proof-of-concepts.

### Duration
Week 1 - Week 2

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T1.1 | Research ASR options (Whisper, Meta ASR, IndicASR) | US-001 | 1 | ✅ Done |
| T1.2 | Research TTS options (MMS, Cartesia, AI4Bharat) | US-001 | 1 | ✅ Done |
| T1.3 | Research LLM options (Qwen, Llama, Cloud) | US-001 | 1 | ✅ Done |
| T1.4 | Design system architecture diagram | US-002 | 2 | ✅ Done |
| T1.5 | Document component interfaces | US-002 | 1 | ✅ Done |
| T1.6 | Setup Python virtual environment | US-003 | 1 | ✅ Done |
| T1.7 | Configure GPU/CUDA for ML | US-003 | 1 | ✅ Done |
| T1.8 | Create project folder structure | US-004 | 1 | ✅ Done |
| T1.9 | Setup requirements.txt | US-004 | 1 | ✅ Done |
| T1.10 | Implement Whisper ASR wrapper | US-005 | 2 | ✅ Done |
| T1.11 | Test Whisper with Malayalam audio | US-005 | 1 | ✅ Done |
| T1.12 | Research Meta ASR 1B integration | US-005 | 2 | ✅ Done |
| T1.13 | Implement MMS-TTS wrapper | US-006 | 2 | ✅ Done |
| T1.14 | Implement Cartesia TTS wrapper | US-006 | 2 | ✅ Done |
| T1.15 | Create TTS comparison script | US-007 | 1 | ✅ Done |

### Sprint 1 Deliverables
- [x] Technology selection document
- [x] System architecture diagram
- [x] Working development environment
- [x] Project repository structure
- [x] Whisper ASR PoC
- [x] MMS-TTS PoC
- [x] Cartesia TTS PoC
- [x] TTS comparison results

### Sprint 1 Retrospective
**Velocity:** 21 points ✅
**What went well:** All core PoCs completed
**Improvements:** Need to test with more Malayalam samples

---

## Sprint 2: Translation & LLM Integration

### Sprint Goal
Complete the translation layer and integrate conversational AI.

### Duration
Week 3 - Week 4

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T2.1 | Setup IndicTrans2 ML→EN model | US-008 | 2 | ✅ Done |
| T2.2 | Create translation wrapper API | US-008 | 2 | ✅ Done |
| T2.3 | Test ML→EN translation quality | US-008 | 1 | 🔄 In Progress |
| T2.4 | Setup IndicTrans2 EN→ML model | US-009 | 2 | ✅ Done |
| T2.5 | Test EN→ML translation quality | US-009 | 1 | ⬜ Todo |
| T2.6 | Create round-trip translation test | US-012 | 2 | ⬜ Todo |
| T2.7 | Download Qwen 2.5 1.5B model | US-010 | 1 | ✅ Done |
| T2.8 | Implement Qwen chat wrapper | US-010 | 2 | ✅ Done |
| T2.9 | Create voice assistant system prompt | US-010b | 1 | 🔄 In Progress |
| T2.10 | Test LLM response quality | US-010 | 1 | ⬜ Todo |
| T2.11 | Implement conversation memory | US-011 | 2 | ✅ Done |
| T2.12 | Test multi-turn conversations | US-011 | 1 | ⬜ Todo |
| T2.13 | Create integration test script | US-012 | 2 | ⬜ Todo |
| T2.14 | Document Sprint 2 progress | - | 1 | ⬜ Todo |

### Sprint 2 Deliverables
- [x] IndicTrans2 ML→EN working
- [x] IndicTrans2 EN→ML working
- [ ] Translation quality report
- [x] Qwen 2.5 LLM integrated
- [x] Conversation memory working
- [ ] Integration tests passing
- [ ] Sprint 2 documentation

### Sprint 2 Progress
**Completed:** 14/21 points (67%)
**Remaining:** 7 points

---

## Sprint 3: Full Pipeline & API Development

### Sprint Goal
Create a working end-to-end voice assistant with API endpoints.

### Duration
Week 5 - Week 6

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T3.1 | Create audio capture module | US-013 | 2 | ⬜ Todo |
| T3.2 | Implement VAD (Voice Activity Detection) | US-013 | 2 | ⬜ Todo |
| T3.3 | Create pipeline orchestrator | US-013 | 3 | ⬜ Todo |
| T3.4 | Integrate all components | US-013 | 1 | ⬜ Todo |
| T3.5 | Create FastAPI application structure | US-014 | 1 | ⬜ Todo |
| T3.6 | Implement /transcribe endpoint | US-014 | 1 | ⬜ Todo |
| T3.7 | Implement /chat endpoint | US-014 | 1 | ⬜ Todo |
| T3.8 | Implement /synthesize endpoint | US-014 | 1 | ⬜ Todo |
| T3.9 | Implement /voice endpoint (full pipeline) | US-014 | 1 | ⬜ Todo |
| T3.10 | Setup WebSocket endpoint | US-015 | 2 | ⬜ Todo |
| T3.11 | Implement streaming audio support | US-015 | 2 | ⬜ Todo |
| T3.12 | Create error handling middleware | US-016 | 2 | ⬜ Todo |
| T3.13 | Implement graceful degradation | US-016 | 1 | ⬜ Todo |
| T3.14 | Create end-to-end test script | - | 1 | ⬜ Todo |

### Sprint 3 Deliverables
- [ ] Audio capture working
- [ ] Full pipeline orchestrator
- [ ] FastAPI REST endpoints
- [ ] WebSocket streaming
- [ ] Error handling
- [ ] End-to-end demo working

---

## Sprint 4: Agent Framework

### Sprint Goal
Implement agentic capabilities using LangGraph.

### Duration
Week 7 - Week 8

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T4.1 | Setup LangGraph framework | US-018 | 2 | ⬜ Todo |
| T4.2 | Create agent state schema | US-018 | 1 | ⬜ Todo |
| T4.3 | Implement agent router | US-018 | 2 | ⬜ Todo |
| T4.4 | Create Info Agent | US-019 | 2 | ⬜ Todo |
| T4.5 | Implement web search tool | US-019 | 1 | ⬜ Todo |
| T4.6 | Create Task Agent | US-020 | 2 | ⬜ Todo |
| T4.7 | Implement reminder storage | US-020 | 1 | ⬜ Todo |
| T4.8 | Create tool registration system | US-021 | 1 | ⬜ Todo |
| T4.9 | Document tool creation guide | US-021 | 1 | ⬜ Todo |
| T4.10 | Integrate agents with pipeline | US-017 | 3 | ⬜ Todo |
| T4.11 | Test agent routing | US-017 | 1 | ⬜ Todo |
| T4.12 | Create agent demo scenarios | US-017 | 1 | ⬜ Todo |

### Sprint 4 Deliverables
- [ ] LangGraph orchestrator
- [ ] Info Agent (Q&A, search)
- [ ] Task Agent (reminders)
- [ ] Tool registration API
- [ ] Agent integration with voice pipeline
- [ ] Demo scenarios

---

## Sprint 5: Edge Deployment

### Sprint Goal
Deploy and optimize for Raspberry Pi 5.

### Duration
Week 9 - Week 10

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T5.1 | Setup Raspberry Pi 5 OS | US-022 | 1 | ⬜ Todo |
| T5.2 | Install Python environment on Pi | US-022 | 1 | ⬜ Todo |
| T5.3 | Configure Pi for ML workloads | US-022 | 2 | ⬜ Todo |
| T5.4 | Apply INT8 quantization to models | US-023 | 2 | ⬜ Todo |
| T5.5 | Convert models to ONNX format | US-023 | 2 | ⬜ Todo |
| T5.6 | Benchmark model performance on Pi | US-023 | 1 | ⬜ Todo |
| T5.7 | Setup USB microphone on Pi | US-025 | 1 | ⬜ Todo |
| T5.8 | Configure audio output on Pi | US-025 | 1 | ⬜ Todo |
| T5.9 | Test audio quality on Pi | US-025 | 1 | ⬜ Todo |
| T5.10 | Profile end-to-end latency | US-024 | 1 | ⬜ Todo |
| T5.11 | Optimize bottlenecks | US-024 | 2 | ⬜ Todo |
| T5.12 | Implement response caching | US-026 | 2 | ⬜ Todo |
| T5.13 | Create Pi deployment script | US-022 | 1 | ⬜ Todo |

### Sprint 5 Deliverables
- [ ] Pi 5 environment ready
- [ ] Quantized models
- [ ] ONNX runtime working
- [ ] Audio I/O on Pi
- [ ] <3 second latency
- [ ] Response caching
- [ ] Deployment script

---

## Sprint 6: Testing & Documentation

### Sprint Goal
Ensure quality and create comprehensive documentation.

### Duration
Week 11 - Week 12

### Sprint Backlog

| Task ID | Task Description | Story | Points | Status |
|---------|-----------------|-------|--------|--------|
| T6.1 | Write unit tests for ASR module | US-027 | 0.5 | ⬜ Todo |
| T6.2 | Write unit tests for translation | US-027 | 0.5 | ⬜ Todo |
| T6.3 | Write unit tests for LLM module | US-027 | 0.5 | ⬜ Todo |
| T6.4 | Write unit tests for TTS module | US-027 | 0.5 | ⬜ Todo |
| T6.5 | Write unit tests for agents | US-027 | 1 | ⬜ Todo |
| T6.6 | Create integration test suite | US-028 | 2 | ⬜ Todo |
| T6.7 | Write end-to-end audio tests | US-028 | 1 | ⬜ Todo |
| T6.8 | Benchmark latency metrics | US-029 | 1 | ⬜ Todo |
| T6.9 | Profile memory usage | US-029 | 1 | ⬜ Todo |
| T6.10 | Write user README | US-030 | 1 | ⬜ Todo |
| T6.11 | Create setup guide | US-030 | 1 | ⬜ Todo |
| T6.12 | Generate API documentation | - | 1 | ⬜ Todo |
| T6.13 | Create demo video/presentation | - | 2 | ⬜ Todo |
| T6.14 | Final bug fixes and polish | - | 2 | ⬜ Todo |

### Sprint 6 Deliverables
- [ ] >80% test coverage
- [ ] Integration tests passing
- [ ] Performance benchmarks
- [ ] User documentation
- [ ] API documentation
- [ ] Demo presentation
- [ ] Production-ready release

---

## Sprint Calendar View

```
Week  1   2   3   4   5   6   7   8   9  10  11  12
      ├───────┼───────┼───────┼───────┼───────┼───────┤
      │       │       │       │       │       │       │
      │ SP1   │ SP2   │ SP3   │ SP4   │ SP5   │ SP6   │
      │       │       │       │       │       │       │
      │Research│Transl │Pipeli-│Agents │ Edge  │Testing│
      │ Setup │ LLM   │ne API │       │Deploy │ Docs  │
      │ PoCs  │       │       │       │       │       │
      ├───────┼───────┼───────┼───────┼───────┼───────┤
          ▲       ▲       ▲       ▲       ▲       ▲
          │       │       │       │       │       │
         M1      M2      M3      M4      M5      M6
      Foundation Core  Pipeline Agent   Edge   Release
      Complete  Ready  Working  Ready  Deploy  Ready
```

---

## Milestone Checklist

### M1: Foundation Complete (Sprint 1) ✅
- [x] Tech stack selected
- [x] Architecture designed
- [x] Dev environment working
- [x] ASR PoC complete
- [x] TTS PoC complete

### M2: Core Components Ready (Sprint 2) 🔄
- [x] Translation working
- [x] LLM integrated
- [ ] Quality validated
- [ ] Integration tested

### M3: Pipeline Functional (Sprint 3)
- [ ] End-to-end working
- [ ] API endpoints ready
- [ ] WebSocket streaming
- [ ] Error handling

### M4: Agent Capabilities (Sprint 4)
- [ ] LangGraph integrated
- [ ] Agents working
- [ ] Tools available
- [ ] Routing logic

### M5: Edge Deployment (Sprint 5)
- [ ] Running on Pi 5
- [ ] Models optimized
- [ ] Latency target met
- [ ] Audio working

### M6: Production Ready (Sprint 6)
- [ ] Tests complete
- [ ] Documentation done
- [ ] Demo ready
- [ ] Release tagged

---

*Document Version: 1.0*
*Last Updated: Sprint 2*
