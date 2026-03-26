# Presenter Script — Interim Project Presentation
**Hyper-Localized Multilingual Voice Assistant**
Ebin John Joseph | ASI24MCA-2025 | Guide: Sukrith Lal

> Estimated total time: ~15–18 minutes. Adjust pacing to your slot.

---

## Slide 1 — Title Slide
**[~30 seconds]**

> Good morning. I'm Ebin John Joseph, register number ASI24MCA-2025, presenting my main project interim report — a **Hyper-Localized Multilingual Voice Assistant**. This project is guided by **Sukrith Lal sir**.

---

## Slide 2 — Introduction
**[~1 minute]**

> India has 22 official languages and over 19,500 dialects. Yet, today's voice assistants — Alexa, Google Assistant, Siri — primarily serve English and Hindi speakers. That leaves roughly **780 million Indians** unable to use voice technology in their own language.
>
> There are three core problems here:
> 1. A **digital divide** — 90% of India's internet users prefer local languages but digital services are English-first.
> 2. **Privacy** — every voice query you make to Alexa or Google is sent to a remote server.
> 3. **Connectivity** — 65% of rural India has unreliable internet, making cloud-dependent assistants unusable.
>
> Our project addresses all three by building a **fully offline, privacy-preserving voice assistant** that runs on edge hardware and supports **Malayalam** as the primary language, along with 10 other Indian languages.

---

## Slide 3 — Objectives
**[~1 minute]**

> The **main objective** is to design and develop a hyper-localized multilingual voice assistant that enables seamless human-computer interaction using natural voice commands in regional Indian languages.
>
> Our five specific objectives are:
> 1. **Multilingual speech recognition** — achieve over 85% accuracy for Malayalam ASR. We've actually surpassed this with 97% accuracy using Pingala V1.
> 2. **Real-time bidirectional translation** — Malayalam to English and back, with over 90% accuracy using IndicTrans2.
> 3. **Agentic AI orchestration** — using LangGraph to intelligently route user queries to specialized agents.
> 4. **Edge deployment readiness** — optimize all models to run within resource constraints, targeting under 3 seconds end-to-end latency.
> 5. **Privacy-preserving architecture** — all processing happens locally, no voice data ever leaves the device.

---

## Slide 4 — Literature Review
**[~1.5 minutes]**

> We studied six major existing systems and research works.
>
> **Google Assistant** and **Amazon Alexa** are cloud-based and only support Hindi among Indian languages — no Malayalam, no offline mode, and both have privacy concerns.
>
> **Rasa Open Source** supports local NLU but has no built-in ASR, TTS, or Indian language models.
>
> **AI4Bharat's IndicTrans2** is excellent for translation across 22 Indian languages, but it's just a translation model — no voice pipeline, no agents.
>
> **OpenAI's Whisper** supports 99 languages but has lower accuracy for low-resource languages like Malayalam compared to specialized models.
>
> **Bhashini**, the government platform, provides cloud APIs for Indian language AI but offers no offline or edge support.
>
> The key **research gap** we identified: no existing system combines multilingual Indic ASR, a local LLM, agentic workflows, and edge deployment in a single privacy-preserving pipeline. That's exactly what our system does.

---

## Slide 5 — Proposed System
**[~1 minute]**

> Our proposed system is an end-to-end voice AI pipeline running entirely on-device.
>
> The key features are: fully offline operation, support for 11 Indian languages, agentic workflows using LangGraph with four specialized agents, and a real-time monitoring dashboard.
>
> Compared to existing systems, we offer **zero cloud dependency**, **no API fees** since we use open-source models, **local inference** avoiding network round-trips, and an **extensible** plug-in architecture.
>
> The core components are: **Pingala V1** for ASR with just 2.94% word error rate, **IndicTrans2-Dist** for translation at 211 million parameters, **Qwen3** via llama.cpp for response generation, **MMS-TTS** for speech synthesis, and a **LangGraph** orchestrator with 4 specialized agents.

---

## Slide 6 — System Architecture
**[~1 minute]**

> The system follows a **three-layer architecture**.
>
> At the top, we have the **input layer** — voice audio comes in from the user in any supported Indian language.
>
> The **processing layer** is the core pipeline: Audio goes through ASR for speech-to-text, then through translation from the source language to English, then intent detection classifies what the user wants, the LangGraph orchestrator routes to the appropriate agent, the LLM generates a response, and finally translation converts it back to the user's language.
>
> The **output layer** converts text to speech using MMS-TTS and delivers the audio response.
>
> On the right you can see our agent system — the LangGraph orchestrator routes to four specialized agents: Info Agent for information queries, Task Agent for task management, Chat Agent for general conversation, and Smart Home Agent for device control.

---

## Slide 7 — Methodology (Scrum)
**[~1 minute]**

> We follow **Agile Scrum** methodology with 6 sprints across 12 weeks. Our product backlog has **114 story points** organized into 8 epics.
>
> Each sprint is 2 weeks with daily standups, sprint planning, and retrospectives. We maintain a burndown chart and daily scrum log for tracking.
>
> The sprint breakdown is:
> - Sprint 1: Research, setup, ASR & TTS proof-of-concepts — 21 points
> - Sprint 2: Translation, LLM integration, memory — 21 points
> - Sprint 3: Pipeline, API, Pingala ASR, WebSocket — 21 points
> - Sprint 4: LangGraph agents, dashboard, database — 18 points
> - Sprint 5 (current): Edge optimization, caching, Docker — 18 points
> - Sprint 6 (planned): Testing and documentation — 15 points
>
> We're currently at **87% completion** with 99 out of 114 story points delivered.

---

## Slide 8 — System Design (Use Cases & Activity)
**[~1 minute]**

> This slide shows our use case diagram and activity diagram.
>
> The **use case diagram** shows the User actor interacting with the system through voice queries, language selection, task management, and conversation. The System actor handles ASR, translation, intent detection, agent routing, and TTS.
>
> The **activity diagram** traces the flow from when a user speaks — the audio is captured, transcribed by ASR, translated to English, classified for intent, routed to the appropriate agent, processed by the LLM, translated back to the user's language, and finally synthesized to speech.

---

## Slide 9 — Data Flow & Database Design
**[~1 minute]**

> Here we have the **Level 1 Data Flow Diagram** and the **ER Diagram**.
>
> The DFD shows how voice audio flows through our five processing stages — ASR, Translation, NLU/Intent, Agent/LLM, and TTS — with the data store holding conversations, metrics, and cached responses.
>
> The **ER diagram** shows three entities:
> - **Conversation** — stores session information with a unique ID, language, creation time, and message count.
> - **Message** — stores individual messages with role, content, intent, agent used, and timing information. It has a foreign key relationship to Conversation (one-to-many).
> - **SystemMetric** — an independent table that logs component performance metrics like latency, memory usage, and success rates.

---

## Slide 10 — Tools & Technologies
**[~1 minute]**

> Our technology stack spans multiple layers.
>
> For ASR, we use **Pingala V1** which achieves 2.94% word error rate for Malayalam — 50% better than Whisper for Indian languages.
>
> For translation, **IndicTrans2-Dist** — the distilled version at 211 million parameters, which is 5 times smaller than the full model with comparable accuracy.
>
> The LLM is **Qwen3** running through **llama.cpp** with GGUF quantization, enabling efficient CPU inference with zero API cost.
>
> For the agent framework, we chose **LangGraph** over vanilla LangChain chains because it provides stateful graphs, conditional routing, and built-in memory management.
>
> The API layer uses **FastAPI** with WebSocket support, and the dashboard is built with **React, TypeScript, and Tailwind CSS**.

---

## Slide 11 — Sprint Progress
**[~1 minute]**

> Here's our sprint-by-sprint implementation progress.
>
> Sprints 1 through 4 are **100% complete** — that's 81 out of 81 story points delivered.
>
> **Sprint 5** is currently active with 18 points. Originally this was planned for Raspberry Pi deployment, but due to budget constraints, we pivoted to **edge-ready optimization** — implementing response caching, model optimization, Docker containerization with resource limits simulating edge hardware, and a performance benchmarking suite.
>
> **Sprint 6** is planned for weeks 11–12, covering unit tests, integration tests, documentation, and the final demo.

---

## Slide 12 — Implementation
**[~1.5 minutes]**

> This slide shows our working modules and outputs.
>
> On the left, you can see a **pipeline output sample** — a user speaks in Malayalam asking about the weather in Kerala. The ASR transcribes it in 480 milliseconds, translation converts it to English in 120 milliseconds, intent is detected as "information_query", the InfoAgent processes it via Qwen3 in 340 milliseconds, translation back to Malayalam takes 130 milliseconds, and TTS generates the audio in 380 milliseconds. **Total end-to-end: 1.45 seconds**.
>
> In the center, our **React dashboard** shows real-time monitoring — total queries, average latency, latency breakdown by component, and component health status.
>
> On the right, the **API endpoints** — we have REST endpoints for transcription, full pipeline processing, TTS, and text-only mode, plus a WebSocket endpoint for real-time streaming.

---

## Slide 13 — Current Status
**[~1 minute]**

> We're at **87% project completion** — 99 of 114 story points are done with 15 remaining.
>
> All core modules are 100% complete: ASR engine, translation, LLM with memory, TTS, pipeline and API, agent framework, and the dashboard.
>
> **Edge optimization** is at 70% — caching and Docker are done, benchmarking and final optimization are in progress.
>
> **Testing and documentation** is at 30% — that's planned for Sprint 6.
>
> On the right, you can see the completed module details — 4 ASR engines with automatic fallback, bidirectional translation for 11 languages, dual LLM backends, 4 TTS engines, and the LangGraph orchestration system.

---

## Slide 14 — Challenges
**[~1 minute]**

> We faced several technical challenges.
>
> **Model memory constraints** — running ASR, translation, LLM, and TTS simultaneously requires 10 to 16 GB of RAM. We solved this with lazy model loading — models load only on demand — plus using the distilled IndicTrans2 which is 5 times smaller, and GGUF quantized LLM.
>
> **Async pipeline integration** — the Pipecat framework uses async callbacks but ML models are synchronous. We implemented async wrappers with ThreadPoolExecutor for CPU-bound inference.
>
> **Translation quality** — spoken Malayalam differs from written text. ASR outputs colloquial forms that translation models struggle with. We added custom text normalization.
>
> **Budget constraint** — we couldn't afford a Raspberry Pi for Sprint 5. So we pivoted to Docker-based edge simulation with 2 CPU and 4 GB RAM limits, proving edge-readiness without physical hardware.

---

## Slide 15 — Future Work
**[~45 seconds]**

> For the remaining work:
>
> In **Sprint 5** (current): complete performance benchmarking, finalize Docker containerization, and implement response caching.
>
> **Sprint 6** (weeks 11–12): unit tests targeting over 80% coverage, integration test suite, performance benchmarks, user documentation, and the final demo.
>
> Post-project enhancements we envision include: physical **Raspberry Pi deployment** when hardware becomes available, **wake word detection** for hands-free activation, **smart home integration** via MQTT, a **mobile companion app**, and a **RAG knowledge base** for domain-specific Q&A.

---

## Slide 16 — Expected Outcome
**[~45 seconds]**

> The expected outcomes are:
> - **Under 3 seconds** end-to-end latency
> - **93% translation accuracy**
> - Support for **11 Indian languages**
> - **Zero cloud dependency**
>
> The key benefits are **digital inclusion** for non-English speakers, **data sovereignty** with all processing happening locally, **zero operational cost** using open-source models, and a **reproducible research** pipeline that can be adapted for other low-resource languages.

---

## Slide 17 — Conclusion
**[~45 seconds]**

> To summarize:
>
> We've built a **complete voice AI pipeline** — end-to-end ASR to translation to LLM to agents to TTS — with under 3 seconds latency, supporting Malayalam and 10 other Indian languages.
>
> We've achieved **state-of-the-art accuracy** — 2.94% word error rate for ASR, approximately 93% translation accuracy, and natural conversational responses via Qwen3.
>
> We've implemented an **intelligent agent system** using LangGraph with specialized agents for different user intents.
>
> The project is **87% complete** with 99 of 114 story points delivered across 5 sprints, on track for final delivery in Sprint 6.
>
> In essence, this project demonstrates that **local-first, privacy-preserving AI** can match cloud-based solutions for Indian language voice interaction, using open-source models at zero operational cost.

---

## Slide 18 — References
**[~15 seconds]**

> Our work builds on key research including **IndicTrans2** for translation, **Whisper** and **Pingala V1** for ASR, **MMS** for multilingual speech, and **Qwen3** for the LLM. The references are listed here for your review.

---

## Slide 19 — Thank You
**[~15 seconds]**

> That concludes my interim presentation. Voice is the most natural interface, and by bringing AI to regional languages on edge devices, we can bridge the digital divide for hundreds of millions. Thank you. I'm happy to take any questions.

---

## Common Questions & Answers

**Q: Why not just use Google Assistant or Alexa?**
> They don't support Malayalam, require constant internet, send voice data to cloud servers, and charge API fees. Our system is fully offline, private, and free.

**Q: Why Pingala V1 over Whisper?**
> Pingala V1 achieves 2.94% WER for Indian languages compared to ~5.8% for Whisper. It's designed specifically for Indic speech and runs efficiently on CPU.

**Q: Why Qwen3 and not GPT or Llama?**
> Qwen3 offers the best performance-to-size ratio for our use case. The 0.6B to 4B parameter range fits edge constraints, and llama.cpp enables efficient GGUF quantized inference on CPU.

**Q: How do you handle languages you haven't tested?**
> IndicTrans2 officially supports all 22 scheduled Indian languages. We've validated 11 of them. The architecture is language-agnostic — adding a new language requires no code changes, just model support.

**Q: What's the difference between the agents?**
> The **Info Agent** handles factual questions and Q&A. The **Task Agent** manages to-do items and reminders. The **Chat Agent** handles general conversation. The **Smart Home Agent** controls IoT devices. The LangGraph orchestrator automatically routes each query to the right agent based on intent classification.

**Q: Why Docker instead of actual Raspberry Pi?**
> Budget constraints. But Docker with resource limits (2 CPUs, 4GB RAM) accurately simulates the Pi 5's constraints. The models, code, and architecture are identical — only the hardware differs. When a Pi becomes available, deployment is straightforward.

**Q: What about real-time performance?**
> Our pipeline achieves approximately 1.5 seconds end-to-end latency: ASR ~480ms, translation ~250ms, LLM ~340ms, TTS ~380ms. Response caching can reduce repeated queries to under 200ms.

**Q: How is this different from Bhashini?**
> Bhashini is a cloud API gateway — it requires internet for every request and doesn't include an LLM or agent system. Our system runs completely offline with intelligent task routing.
