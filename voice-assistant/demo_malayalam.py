"""
Malayalam Speech Recognition Demo
Uses AI4Bharat IndicWhisper for better Malayalam support.

First run: pip install transformers accelerate
Then: python demo_malayalam.py
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("\n" + "="*60)
    print("INDIAN LANGUAGE SPEECH RECOGNITION DEMO")
    print("Using OpenAI Whisper Large V3 (best multilingual support)")
    print("="*60)

    # Check dependencies
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"\nMissing dependency: {e}")
        print("Run: pip install sounddevice soundfile numpy")
        return

    try:
        from transformers import WhisperProcessor
    except ImportError:
        print("\nMissing transformers library.")
        print("Run: pip install transformers accelerate torch")
        return

    # Import our ASR
    from src.asr import IndicWhisperASR

    # Settings
    duration = 6  # seconds - slightly longer for Malayalam
    sample_rate = 16000

    print("\nSelect language:")
    print("  1. Malayalam (ml)")
    print("  2. Hindi (hi)")
    print("  3. Tamil (ta)")
    print("  4. Telugu (te)")
    print("  5. English (en)")

    lang_choice = input("Choice [1]: ").strip() or "1"
    lang_map = {"1": "ml", "2": "hi", "3": "ta", "4": "te", "5": "en"}
    language = lang_map.get(lang_choice, "ml")

    print(f"\nSelected: {language.upper()}")
    print("Using OpenAI whisper-large-v3 (~3GB download on first run)")

    # Initialize ASR - using GPU (RTX 4070)
    asr = IndicWhisperASR(language=language, device="cuda")

    print("\nReady! Press ENTER to start recording...")

    while True:
        choice = input("\nPress ENTER to record (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            break

        print(f"\nRecording for {duration} seconds... Speak in {language.upper()} now!")

        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        print("Recording complete!")

        # Save temp file
        temp_file = "temp_malayalam.wav"
        sf.write(temp_file, audio, sample_rate)

        # Transcribe
        print("Transcribing...")
        try:
            result = asr.transcribe(temp_file, language=language)

            print("\n" + "-"*50)
            print(f"Transcription: {result['text']}")
            print(f"Language: {result['language_name']}")
            print("-"*50)

        except Exception as e:
            print(f"Error: {e}")

        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
