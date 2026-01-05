"""
Meta Omnilingual ASR Demo
Supports 1600+ languages including Malayalam
Works in WSL2 with PulseAudio

Run: python demo_meta_asr.py
"""

import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def record_audio_pulseaudio(duration=6, sample_rate=16000):
    """Record audio using PulseAudio (for WSL2)."""
    print(f"Recording {duration} seconds... Speak now!")

    # Create temp file
    temp_file = tempfile.mktemp(suffix=".wav")

    # Use parecord for recording
    try:
        proc = subprocess.Popen(
            ["parecord", "--channels=1", f"--rate={sample_rate}", "--file-format=wav", temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for duration
        import time
        time.sleep(duration)

        # Stop recording
        proc.terminate()
        proc.wait()

        print("Recording complete!")
        return temp_file

    except FileNotFoundError:
        print("Error: parecord not found. Install with: sudo apt install pulseaudio-utils")
        return None
    except Exception as e:
        print(f"Recording error: {e}")
        return None


def record_audio_sounddevice(duration=6, sample_rate=16000):
    """Record audio using sounddevice (for Windows/native Linux)."""
    import sounddevice as sd
    import soundfile as sf
    import numpy as np

    print(f"Recording {duration} seconds... Speak now!")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    print("Recording complete!")

    # Save to temp file
    temp_file = tempfile.mktemp(suffix=".wav")
    sf.write(temp_file, audio, sample_rate)
    return temp_file


def record_audio(duration=6, sample_rate=16000):
    """Record audio - auto-detects best method."""
    # Check if we're in WSL2
    is_wsl = os.path.exists("/mnt/wslg") or "microsoft" in os.uname().release.lower()

    if is_wsl:
        # Try PulseAudio first in WSL2
        return record_audio_pulseaudio(duration, sample_rate)
    else:
        # Use sounddevice on native systems
        try:
            return record_audio_sounddevice(duration, sample_rate)
        except Exception as e:
            print(f"sounddevice failed: {e}, trying PulseAudio...")
            return record_audio_pulseaudio(duration, sample_rate)


def main():
    print("\n" + "="*60)
    print("META OMNILINGUAL ASR DEMO")
    print("Supports 1600+ languages including Malayalam")
    print("="*60)

    # Check if we're in WSL
    is_wsl = os.path.exists("/mnt/wslg") or "microsoft" in os.uname().release.lower()
    if is_wsl:
        print("Detected: WSL2 (using PulseAudio)")
        # Ensure PULSE_SERVER is set
        if "PULSE_SERVER" not in os.environ:
            os.environ["PULSE_SERVER"] = "unix:/mnt/wslg/PulseServer"
            print("Set PULSE_SERVER to WSLg")

    try:
        from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline
    except ImportError:
        print("\nOmnilingual ASR not installed.")
        print("Run: pip install omnilingual-asr")
        return

    print("\nSelect model:")
    print("  1. 300M CTC (fastest, ~1GB)")
    print("  2. 1B CTC (balanced)")
    print("  3. 7B LLM (best quality, ~14GB VRAM needed)")
    model_choice = input("Choice [1]: ").strip() or "1"

    model_map = {
        "1": "omniASR_CTC_300M",
        "2": "omniASR_CTC_1B",
        "3": "omniASR_LLM_7B",
    }
    model_name = model_map.get(model_choice, "omniASR_CTC_300M")

    print(f"\nLoading {model_name}...")
    try:
        pipeline = ASRInferencePipeline(model_card=model_name)
        print("Model loaded!")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Language selection
    print("\nSelect language:")
    print("  1. Malayalam (mal_Mlym)")
    print("  2. Hindi (hin_Deva)")
    print("  3. Tamil (tam_Taml)")
    print("  4. Telugu (tel_Telu)")
    print("  5. English (eng_Latn)")
    lang_choice = input("Choice [1]: ").strip() or "1"

    lang_map = {
        "1": "mal_Mlym",
        "2": "hin_Deva",
        "3": "tam_Taml",
        "4": "tel_Telu",
        "5": "eng_Latn",
    }
    lang_names = {
        "1": "Malayalam",
        "2": "Hindi",
        "3": "Tamil",
        "4": "Telugu",
        "5": "English",
    }
    language = lang_map.get(lang_choice, "mal_Mlym")
    lang_name = lang_names.get(lang_choice, "Malayalam")

    print(f"\nLanguage: {lang_name} ({language})")

    duration = 6

    print("\nReady! Speak clearly.")

    while True:
        choice = input("\nPress ENTER to record (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            break

        # Record audio
        temp_file = record_audio(duration=duration)

        if not temp_file or not os.path.exists(temp_file):
            print("Recording failed!")
            continue

        print("Transcribing...")

        try:
            # Transcribe with Omnilingual ASR
            transcriptions = pipeline.transcribe(
                [temp_file],
                lang=[language],
                batch_size=1
            )

            result_text = transcriptions[0]

            print("\n" + "-"*50)
            print(f"Language: {lang_name}")
            print(f"Transcription: {result_text}")
            print("-"*50)

            # Save to file
            output_file = "transcriptions.txt"
            with open(output_file, "a", encoding="utf-8") as f:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n[{timestamp}] Language: {lang_name}\n")
                f.write(f"Transcription: {result_text}\n")
                f.write("-"*50 + "\n")

            print(f"Saved to: {output_file}")

        except Exception as e:
            print(f"Transcription error: {e}")

        # Cleanup
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    print("Goodbye!")


if __name__ == "__main__":
    main()
