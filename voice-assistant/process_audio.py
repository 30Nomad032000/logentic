"""
Meta Omnilingual ASR - Audio File Processor
Processes pre-recorded audio files (for use in WSL2)

Usage: python process_audio.py <audio_file> [language]
Example: python process_audio.py /mnt/e/Work/logentic/voice-assistant/recorded_audio.wav mal_Mlym
"""

import sys
import os


def main():
    print("\n" + "="*60)
    print("META OMNILINGUAL ASR - FILE PROCESSOR")
    print("="*60)

    # Check arguments
    if len(sys.argv) < 2:
        print("\nUsage: python process_audio.py <audio_file> [language]")
        print("\nLanguage codes:")
        print("  mal_Mlym  - Malayalam")
        print("  hin_Deva  - Hindi")
        print("  tam_Taml  - Tamil")
        print("  tel_Telu  - Telugu")
        print("  eng_Latn  - English")
        print("\nExample:")
        print("  python process_audio.py /mnt/e/Work/logentic/voice-assistant/recorded_audio.wav mal_Mlym")
        return

    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "mal_Mlym"

    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"Error: File not found: {audio_file}")
        return

    print(f"\nAudio file: {audio_file}")
    print(f"Language: {language}")

    # Import Omnilingual ASR
    try:
        from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline
    except ImportError:
        print("\nError: omnilingual-asr not installed")
        print("Run: pip install omnilingual-asr")
        return

    # Select model
    print("\nSelect model:")
    print("  1. 300M CTC (fastest, ~1GB)")
    print("  2. 1B CTC (balanced)")
    print("  3. 7B LLM (best quality, needs ~14GB VRAM)")
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

    print("\nTranscribing...")

    try:
        transcriptions = pipeline.transcribe(
            [audio_file],
            lang=[language],
            batch_size=1
        )

        print("\n" + "="*60)
        print("RESULT")
        print("="*60)
        print(f"Language: {language}")
        print(f"Transcription: {transcriptions[0]}")
        print("="*60)

    except Exception as e:
        print(f"Transcription error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
