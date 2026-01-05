"""
Sprint 1 Demo Script
Demonstrates voice assistant capabilities without Raspberry Pi.
Run: python demo.py
"""

import sys
import os

# Fix Python path - add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def demo_intent_classification():
    """Demo 1: Intent Classification"""
    print("\n" + "="*60)
    print("DEMO 1: Intent Classification (NLU)")
    print("="*60)

    from src.nlu import IntentClassifier
    classifier = IntentClassifier()

    test_inputs = [
        "hello, how are you",
        "what is the weather today",
        "remind me to call doctor at 3pm",
        "turn on the living room lights",
        "play some relaxing music",
        "what time is it now",
        "help me with something",
    ]

    print(f"\n{'Input':<40} {'Intent':<20} {'Confidence'}")
    print("-"*70)

    for text in test_inputs:
        result = classifier.classify(text)
        print(f"{text:<40} {result.intent:<20} {result.confidence:.2f}")


def demo_agent_orchestrator():
    """Demo 2: Agent Orchestrator"""
    print("\n" + "="*60)
    print("DEMO 2: Agent Orchestrator (LangGraph Workflow)")
    print("="*60)

    from src.agents import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    orchestrator.setup()

    queries = [
        ("What is machine learning?", "en"),
        ("Set a reminder for tomorrow", "en"),
        ("Hello there!", "en"),
        ("Tell me about Python programming", "en"),
    ]

    for query, lang in queries:
        print(f"\n>>> User: {query}")
        result = orchestrator.process(query, lang)
        print(f"    Intent: {result['intent']}")
        print(f"    Response: {result['response']}")


def demo_asr_simulation():
    """Demo 3: ASR (Simulated - shows capability)"""
    print("\n" + "="*60)
    print("DEMO 3: ASR Module Info")
    print("="*60)

    from src.asr import WhisperASR

    asr = WhisperASR(model_size="base")

    print("\nSupported Indian Languages:")
    print("-"*40)
    for code, name in asr.SUPPORTED_INDIAN_LANGUAGES.items():
        print(f"  {code}: {name}")

    print("\n[Note: To test actual transcription, provide an audio file]")
    print("Example: asr.transcribe('your_audio.wav')")


def demo_tts_info():
    """Demo 4: TTS Module Info"""
    print("\n" + "="*60)
    print("DEMO 4: TTS Module Info")
    print("="*60)

    from src.tts import IndicTTS

    tts = IndicTTS()

    print("\nSupported Languages for Speech Synthesis:")
    print("-"*40)
    for code, name in tts.get_supported_languages().items():
        print(f"  {code}: {name}")

    print("\nSupported Emotions:")
    print("-"*40)
    for emotion in tts.get_supported_emotions():
        print(f"  - {emotion}")


def demo_interactive():
    """Demo 5: Interactive Text Chat"""
    print("\n" + "="*60)
    print("DEMO 5: Interactive Mode")
    print("="*60)
    print("Type your queries (type 'quit' to exit)")

    from src.agents import AgentOrchestrator
    from src.nlu import IntentClassifier

    orchestrator = AgentOrchestrator()
    orchestrator.setup()
    classifier = IntentClassifier()

    while True:
        try:
            user_input = input("\n>>> You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not user_input:
                continue

            # Classify intent
            intent_result = classifier.classify(user_input)

            # Process through agents
            result = orchestrator.process(user_input, "en")

            print(f"    [Intent: {intent_result.intent}]")
            print(f"<<< Assistant: {result['response']}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def main():
    """Main demo runner"""
    print("\n" + "#"*60)
    print("#  HYPER-LOCALIZED MULTILINGUAL VOICE ASSISTANT")
    print("#  Sprint 1 Demo - MCA Final Year Project")
    print("#"*60)

    demos = {
        "1": ("Intent Classification", demo_intent_classification),
        "2": ("Agent Orchestrator", demo_agent_orchestrator),
        "3": ("ASR Module Info", demo_asr_simulation),
        "4": ("TTS Module Info", demo_tts_info),
        "5": ("Interactive Chat", demo_interactive),
        "a": ("Run All Demos", None),
    }

    print("\nAvailable Demos:")
    for key, (name, _) in demos.items():
        print(f"  {key}. {name}")

    choice = input("\nSelect demo (1-5, 'a' for all, or 'q' to quit): ").strip().lower()

    if choice == 'q':
        return
    elif choice == 'a':
        demo_intent_classification()
        demo_agent_orchestrator()
        demo_asr_simulation()
        demo_tts_info()
        demo_interactive()
    elif choice in demos and demos[choice][1]:
        demos[choice][1]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
