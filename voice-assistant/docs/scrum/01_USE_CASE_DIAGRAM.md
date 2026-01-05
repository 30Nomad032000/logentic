# Use Case Diagram

## Project: Hyper-Localized Multilingual Voice Assistant

---

## 1. System Use Case Diagram

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

---

## 2. Actors

| Actor | Description | Type |
|-------|-------------|------|
| **User** | Malayalam-speaking end user who interacts with the voice assistant | Primary |
| **Admin** | System administrator who configures and monitors the system | Secondary |
| **External System** | Third-party APIs (Meta ASR, optional cloud services) | External |

---

## 3. Use Case Descriptions

### UC1: Speak Voice Command

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC1 |
| **Name** | Speak Voice Command |
| **Actor** | User |
| **Description** | User speaks a command or query in Malayalam |
| **Preconditions** | System is running and listening |
| **Postconditions** | Audio is captured and ready for processing |
| **Main Flow** | 1. User activates the assistant (wake word or button) <br> 2. System indicates it's listening <br> 3. User speaks in Malayalam <br> 4. System captures audio |
| **Alternative Flow** | User can cancel by saying "cancel" or timeout |
| **Priority** | Critical |

---

### UC2: Transcribe Speech (ASR)

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC2 |
| **Name** | Transcribe Speech |
| **Actor** | System |
| **Description** | Convert Malayalam speech to text using Meta ASR 1B |
| **Preconditions** | Audio is captured |
| **Postconditions** | Malayalam text is generated |
| **Main Flow** | 1. Audio is sent to Meta ASR API <br> 2. ASR processes and returns text <br> 3. Text is validated |
| **Alternative Flow** | If ASR fails, fallback to Whisper |
| **Priority** | Critical |
| **Dependencies** | Requires internet connection |

---

### UC3: Translate Malayalam ↔ English

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC3 |
| **Name** | Translate Text |
| **Actor** | System |
| **Description** | Translate between Malayalam and English using IndicTrans2 |
| **Preconditions** | Text is available |
| **Postconditions** | Translated text is ready |
| **Main Flow** | 1. Malayalam text received <br> 2. IndicTrans2 translates to English <br> 3. (After LLM) English response translated to Malayalam |
| **Priority** | Critical |
| **Notes** | Runs locally, no internet required |

---

### UC4: Process Intent & Generate Response

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC4 |
| **Name** | Process Intent |
| **Actor** | System |
| **Description** | LLM understands user intent and generates appropriate response |
| **Preconditions** | English text is available |
| **Postconditions** | English response is generated |
| **Main Flow** | 1. English text sent to Qwen LLM <br> 2. LLM processes with conversation context <br> 3. Response generated |
| **Extensions** | UC4a, UC4b, UC4c |
| **Priority** | Critical |

---

### UC4a: Answer Question

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC4a |
| **Name** | Answer Question |
| **Actor** | System |
| **Description** | Provide informative answers to user queries |
| **Examples** | "What is the weather?", "Who is the president?" |
| **Priority** | High |

---

### UC4b: Execute Task

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC4b |
| **Name** | Execute Task |
| **Actor** | System |
| **Description** | Perform tasks like reminders, calculations, etc. |
| **Examples** | "Set a reminder for 5 PM", "Calculate 25 times 4" |
| **Priority** | Medium |

---

### UC4c: Control Smart Home

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC4c |
| **Name** | Control Smart Home |
| **Actor** | System |
| **Description** | Control IoT devices via voice |
| **Examples** | "Turn on the lights", "Set AC to 24 degrees" |
| **Priority** | Low (Future) |

---

### UC5: Synthesize Speech Response

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC5 |
| **Name** | Synthesize Speech |
| **Actor** | System |
| **Description** | Convert Malayalam text to speech using MMS-TTS |
| **Preconditions** | Malayalam response text is ready |
| **Postconditions** | Audio is played to user |
| **Main Flow** | 1. Malayalam text sent to MMS-TTS <br> 2. Audio generated locally <br> 3. Audio played through speaker |
| **Priority** | Critical |
| **Notes** | Runs locally, no internet required |

---

### UC6: Configure System Settings

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC6 |
| **Name** | Configure Settings |
| **Actor** | Admin |
| **Description** | Modify system configuration parameters |
| **Examples** | Change language, adjust TTS voice, set API keys |
| **Priority** | Medium |

---

### UC7: Monitor System Performance

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC7 |
| **Name** | Monitor Performance |
| **Actor** | Admin |
| **Description** | View system metrics, logs, and health status |
| **Examples** | View latency, check error logs, monitor memory |
| **Priority** | Low |

---

### UC8: Add/Update Agent Tools

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC8 |
| **Name** | Manage Agent Tools |
| **Actor** | Admin |
| **Description** | Add new tools or update existing agent capabilities |
| **Examples** | Add weather API tool, update calendar integration |
| **Priority** | Medium |

---

## 4. Use Case Relationships

```
                    <<include>>
    UC1 ─────────────────────────► UC2
                                    │
                    <<include>>     │
                ◄───────────────────┘
                │
                ▼
              UC3 ◄──────────────────┐
                │                    │
    <<include>> │                    │ <<include>>
                ▼                    │
              UC4 ───────────────────┘
                │
        ┌───────┼───────┐
        │       │       │
        ▼       ▼       ▼
     UC4a    UC4b    UC4c
        │       │       │
        └───────┼───────┘
                │
    <<include>> │
                ▼
              UC5
```

---

## 5. Non-Functional Requirements

| Requirement | Description | Target |
|-------------|-------------|--------|
| **Performance** | End-to-end latency | < 3 seconds |
| **Availability** | System uptime | > 99% |
| **Scalability** | Concurrent users | 1 (edge device) |
| **Security** | Data handling | Audio not stored permanently |
| **Usability** | Natural conversation | MOS > 3.5/5 |

---

*Document Version: 1.0*
*Last Updated: Sprint 2*
