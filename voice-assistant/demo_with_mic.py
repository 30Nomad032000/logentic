"""
Demo with Laptop Microphone
Record audio from your laptop mic and test ASR + full pipeline.

Requirements:
    pip install sounddevice soundfile

Run: python demo_with_mic.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_audio_devices():
    """List available audio devices."""
    try:
        import sounddevice as sd
        print("\nAvailable Audio Devices:")
        print("-"*50)
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  [{i}] {device['name']} (inputs: {device['max_input_channels']})")
        return True
    except ImportError:
        print("sounddevice not installed. Run: pip install sounddevice")
        return False


def record_and_transcribe():
    """Record from mic and transcribe."""
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        from src.asr import WhisperASR

        print("\n" + "="*60)
        print("RECORD & TRANSCRIBE DEMO")
        print("="*60)

        # Settings
        duration = 5  # seconds
        sample_rate = 16000

        input(f"\nPress ENTER to start recording ({duration} seconds)...")

        print("Recording... Speak now!")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        print("Recording complete!")

        # Save to temp file
        temp_file = "temp_recording.wav"
        sf.write(temp_file, audio, sample_rate)
        print(f"Saved to {temp_file}")

        # Ask for language
        print("\nSelect language:")
        print("  1. Auto-detect")
        print("  2. Malayalam (ml)")
        print("  3. Hindi (hi)")
        print("  4. Tamil (ta)")
        print("  5. English (en)")
        lang_choice = input("Choice [1]: ").strip() or "1"

        lang_map = {"1": None, "2": "ml", "3": "hi", "4": "ta", "5": "en"}
        language = lang_map.get(lang_choice, None)

        # Transcribe
        print("\nTranscribing (loading Whisper model, may take a moment)...")
        # Using RTX 4070 GPU for fast inference
        asr = WhisperASR(model_size="medium", device="cuda")
        result = asr.transcribe(temp_file, language=language)

        print("\n" + "-"*40)
        print(f"Transcription: {result['text']}")
        print(f"Language: {result['language_name']} ({result['language']})")
        print("-"*40)

        # Clean up
        os.remove(temp_file)

        return result['text']

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install sounddevice soundfile")
        return None


def full_pipeline_demo():
    """Full pipeline: Record -> ASR -> NLU -> Agent -> Response"""
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        from src.asr import WhisperASR
        from src.nlu import IntentClassifier
        from src.agents import AgentOrchestrator

        print("\n" + "="*60)
        print("FULL PIPELINE DEMO")
        print("="*60)
        print("Pipeline: Mic -> ASR -> NLU -> Agent -> Response")

        # Initialize components
        print("\nInitializing components...")
        asr = WhisperASR(model_size="base", device="cpu")
        classifier = IntentClassifier()
        orchestrator = AgentOrchestrator()
        orchestrator.setup()
        print("Components ready!")

        # Settings
        duration = 5
        sample_rate = 16000

        while True:
            choice = input("\nPress ENTER to record (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                break

            # Record
            print(f"Recording for {duration} seconds... Speak now!")
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            print("Recording complete!")

            # Save temp
            temp_file = "temp_recording.wav"
            sf.write(temp_file, audio, sample_rate)

            # ASR
            print("Transcribing...")
            asr_result = asr.transcribe(temp_file)
            transcription = asr_result['text']
            language = asr_result['language']

            print(f"\n[ASR] You said: \"{transcription}\"")
            print(f"[ASR] Language: {asr_result['language_name']}")

            if not transcription.strip():
                print("[Warning] No speech detected")
                os.remove(temp_file)
                continue

            # NLU
            intent_result = classifier.classify(transcription)
            print(f"[NLU] Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")

            # Agent
            agent_result = orchestrator.process(transcription, language)
            print(f"[Agent] Response: {agent_result['response']}")

            # Clean up
            os.remove(temp_file)

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install sounddevice soundfile openai-whisper")


def main():
    print("\n" + "#"*60)
    print("#  VOICE ASSISTANT - MICROPHONE DEMO")
    print("#  (Works on any laptop/PC with a microphone)")
    print("#"*60)

    if not check_audio_devices():
        return

    print("\nOptions:")
    print("  1. Simple Record & Transcribe")
    print("  2. Full Pipeline Demo (ASR -> NLU -> Agent)")
    print("  q. Quit")

    choice = input("\nSelect option: ").strip()

    if choice == '1':
        record_and_transcribe()
    elif choice == '2':
        full_pipeline_demo()
    elif choice.lower() == 'q':
        print("Bye!")
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
