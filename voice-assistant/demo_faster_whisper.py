"""
Faster Whisper Demo for Malayalam
Optimized Whisper implementation - faster and works better on Windows

Install:
    pip install faster-whisper

Run: python demo_faster_whisper.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("\n" + "="*60)
    print("FASTER WHISPER - MALAYALAM DEMO")
    print("Optimized Whisper with CTranslate2 backend")
    print("="*60)

    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Missing: {e}")
        print("Run: pip install sounddevice soundfile numpy")
        return

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("\nfaster-whisper not installed.")
        print("Run: pip install faster-whisper")
        return

    # Check CUDA
    import torch
    cuda_available = torch.cuda.is_available()
    print(f"\nCUDA available: {cuda_available}")
    if cuda_available:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        device = "cuda"
        compute_type = "float16"
    else:
        device = "cpu"
        compute_type = "int8"

    print("\nSelect model:")
    print("  1. small (faster)")
    print("  2. medium (balanced)")
    print("  3. large-v3 (best quality)")
    model_choice = input("Choice [2]: ").strip() or "2"
    model_map = {"1": "small", "2": "medium", "3": "large-v3"}
    model_name = model_map.get(model_choice, "medium")

    print(f"\nLoading {model_name} on {device}...")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print("Model loaded!")

    print("\nSelect language:")
    print("  1. Malayalam (ml)")
    print("  2. Hindi (hi)")
    print("  3. Tamil (ta)")
    print("  4. Telugu (te)")
    print("  5. Auto-detect")
    lang_choice = input("Choice [1]: ").strip() or "1"
    lang_map = {"1": "ml", "2": "hi", "3": "ta", "4": "te", "5": None}
    language = lang_map.get(lang_choice)

    if language:
        print(f"\nForcing language: {language}")
    else:
        print("\nAuto-detecting language")

    duration = 6
    sample_rate = 16000

    print("\nReady! Speak clearly in your chosen language.")

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

        try:
            # Transcribe with faster-whisper
            segments, info = model.transcribe(
                temp_file,
                language=language,
                task="transcribe",  # transcribe, not translate
                beam_size=5,
                vad_filter=True,    # Remove silence
            )

            # Collect all segments
            text = ""
            for segment in segments:
                text += segment.text

            print("\n" + "-"*50)
            print(f"Detected language: {info.language} ({info.language_probability:.1%})")
            print(f"Transcription: {text.strip()}")
            print("-"*50)

        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()

        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("Goodbye!")


if __name__ == "__main__":
    main()
