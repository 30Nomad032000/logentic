"""
Direct Whisper Demo for Malayalam
Uses openai-whisper library directly (simpler, better language support)

Run: python demo_whisper_direct.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("\n" + "="*60)
    print("MALAYALAM SPEECH RECOGNITION (Direct Whisper)")
    print("="*60)

    try:
        import whisper
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Missing: {e}")
        print("Run: pip install openai-whisper sounddevice soundfile numpy")
        return

    # Check for GPU
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("\nSelect model size:")
    print("  1. small (500MB) - fastest")
    print("  2. medium (1.5GB) - balanced")
    print("  3. large-v3 (3GB) - best quality")
    model_choice = input("Choice [1]: ").strip() or "1"
    model_map = {"1": "small", "2": "medium", "3": "large-v3"}
    model_name = model_map.get(model_choice, "small")

    print(f"\nLoading Whisper {model_name}...")
    model = whisper.load_model(model_name, device=device)
    print("Model loaded!")

    print("\nSelect language:")
    print("  1. Malayalam (ml)")
    print("  2. Hindi (hi)")
    print("  3. Tamil (ta)")
    print("  4. Auto-detect")
    lang_choice = input("Choice [1]: ").strip() or "1"
    lang_map = {"1": "ml", "2": "hi", "3": "ta", "4": None}
    language = lang_map.get(lang_choice)

    if language:
        print(f"\nForcing language: {language}")
    else:
        print("\nAuto-detecting language")

    duration = 6
    sample_rate = 16000

    print("\nReady! Speak clearly in Malayalam.")

    while True:
        choice = input("\nPress ENTER to record (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            break

        print(f"Recording {duration} seconds...")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        print("Recording complete!")

        # Save temp file
        temp_file = "temp_recording.wav"
        sf.write(temp_file, audio, sample_rate)

        print("Transcribing...")

        # Transcribe with forced language
        result = model.transcribe(
            temp_file,
            language=language,      # Force language (e.g., "ml")
            task="transcribe",      # Transcribe, don't translate
            fp16=(device == "cuda"),
            verbose=True,           # Show progress
            condition_on_previous_text=False,  # Faster
        )

        print("\n" + "-"*50)
        print(f"Detected language: {result.get('language', 'N/A')}")
        print(f"Text: {result['text']}")
        print("-"*50)

        # Cleanup
        os.remove(temp_file)

    print("Goodbye!")


if __name__ == "__main__":
    main()
