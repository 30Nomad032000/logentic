# Scrum Documentation

## Project: Hyper-Localized Multilingual Voice Assistant

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 1 | [Use Case Diagram](01_USE_CASE_DIAGRAM.md) | System use cases and actor interactions |
| 2 | [Activity Diagram](02_ACTIVITY_DIAGRAM.md) | Process flows and component interactions |
| 3 | [Burndown Chart](03_BURNDOWN_CHART.md) | Project schedule and progress tracking |
| 4 | [Product Backlog](04_PRODUCT_BACKLOG.md) | Detailed user stories and epics |
| 5 | [Sprint Schedule](05_SPRINT_SCHEDULE.md) | Sprint-wise implementation plan |

---

## Quick Links

### Current Sprint: Sprint 2
- **Focus:** Translation & LLM Integration
- **Duration:** Week 3-4
- **Progress:** 67% complete

### Project Status
- **Total Points:** 114
- **Completed:** 35 points (31%)
- **Remaining:** 79 points

---

## Project Summary

### Vision
Build a hyper-localized multilingual voice assistant that runs on edge devices, providing natural Malayalam conversation capabilities using AI.

### Key Features
1. **Malayalam Speech Recognition** - Meta ASR 1B
2. **Bidirectional Translation** - IndicTrans2
3. **Conversational AI** - Qwen 2.5 LLM
4. **Natural Speech Synthesis** - MMS-TTS
5. **Agentic Workflows** - LangGraph

### Architecture

```
[User] → [Mic] → [ASR] → [ML→EN] → [LLM] → [EN→ML] → [TTS] → [Speaker]
                   ↑        ↑         ↑        ↑         ↑
                Online    Local     Local    Local     Local
```

---

## Sprint Progress

| Sprint | Status | Points |
|--------|--------|--------|
| Sprint 1 | ✅ Complete | 21/21 |
| Sprint 2 | 🔄 In Progress | 14/21 |
| Sprint 3 | ⬜ Planned | 0/21 |
| Sprint 4 | ⬜ Planned | 0/18 |
| Sprint 5 | ⬜ Planned | 0/18 |
| Sprint 6 | ⬜ Planned | 0/15 |

---

*Last Updated: Sprint 2, Week 3*
