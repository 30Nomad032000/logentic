#!/usr/bin/env python3
"""
Voice Assistant Pipeline Demo
Demonstrates the full pipeline: ASR → Translation → Intent → LLM → Translation → TTS
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print demo banner."""
    print("\n" + "=" * 70)
    print("   🎙️  HYPER-LOCALIZED MULTILINGUAL VOICE ASSISTANT")
    print("   📍 Malayalam → English → LLM → English → Malayalam")
    print("=" * 70)


def print_result(result):
    """Pretty print pipeline result."""
    print("\n" + "-" * 70)
    print("📊 PIPELINE RESULTS")
    print("-" * 70)

    # Input
    print(f"\n📥 INPUT:")
    print(f"   Malayalam: {result.malayalam_text}")

    # Translation
    print(f"\n🔄 TRANSLATION (ML → EN):")
    print(f"   English: {result.english_text}")
    print(f"   ⏱️  Time: {result.translation_ml_en_time_ms:.1f}ms")

    # Intent Detection
    if result.intent_type:
        print(f"\n🎯 INTENT DETECTED:")
        print(f"   Type: {result.intent_type.upper()}")
        print(f"   Description: {result.intent_description}")
        print(f"   Confidence: {result.intent_confidence:.0%}")
        if result.intent_entities:
            print(f"   Entities: {result.intent_entities}")

    # LLM Response
    print(f"\n🤖 LLM RESPONSE:")
    print(f"   English: {result.english_response}")
    print(f"   ⏱️  Time: {result.llm_time_ms:.1f}ms")

    # Translation back
    print(f"\n🔄 TRANSLATION (EN → ML):")
    print(f"   Malayalam: {result.malayalam_response}")
    print(f"   ⏱️  Time: {result.translation_en_ml_time_ms:.1f}ms")

    # TTS
    print(f"\n🔊 TTS:")
    print(f"   ⏱️  Time: {result.tts_time_ms:.1f}ms")

    # Total
    print(f"\n⏱️  TOTAL TIME: {result.total_time_ms:.1f}ms ({result.total_time_ms/1000:.2f}s)")

    if not result.success:
        print(f"\n❌ ERROR: {result.error}")

    print("-" * 70)


def demo_text_input():
    """Demo with text input (no audio recording needed)."""
    from pipeline import VoiceAssistantPipeline

    print_banner()

    # Test inputs in Malayalam
    test_inputs = [
        # Greeting
        ("നമസ്കാരം, എന്റെ പേര് രാഹുൽ ആണ്", "Greeting - Introduction"),
        # Weather question
        ("ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയുണ്ട്?", "Weather - Question"),
        # Time question
        ("ഇപ്പോൾ സമയം എത്രയായി?", "Time - Question"),
        # General question
        ("കേരളത്തിന്റെ തലസ്ഥാനം ഏതാണ്?", "Information - Question"),
        # Task/Command
        ("എനിക്ക് ഒരു റിമൈൻഡർ സെറ്റ് ചെയ്യണം", "Task - Reminder"),
    ]

    # Initialize pipeline
    print("\n🔧 Initializing pipeline...")
    pipeline = VoiceAssistantPipeline(
        asr_engine="whisper",
        asr_model_size="base",
        llm_model_size="1.5b",
        tts_engine="mms",
        device="cuda",
        detect_intent=True,
    )

    # Load components
    pipeline.load_components(show_progress=True)

    # Output directory
    output_dir = Path(__file__).parent.parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)

    # Process each test input
    for i, (malayalam_text, description) in enumerate(test_inputs, 1):
        print(f"\n\n{'='*70}")
        print(f"📝 TEST {i}: {description}")
        print(f"{'='*70}")

        output_audio = output_dir / f"response_{i}.wav"

        result = pipeline.process_text(
            text=malayalam_text,
            input_language="ml",
            output_audio_path=str(output_audio),
        )

        print_result(result)

        if result.success:
            print(f"💾 Audio saved to: {output_audio}")

        # Clear conversation for next test
        pipeline.clear_conversation()

    print(f"\n\n{'='*70}")
    print("✅ DEMO COMPLETE!")
    print(f"📁 Output files saved to: {output_dir}")
    print(f"{'='*70}\n")


def demo_interactive():
    """Interactive demo - type Malayalam text and get responses."""
    from pipeline import VoiceAssistantPipeline

    print_banner()
    print("\n🎮 INTERACTIVE MODE")
    print("Type Malayalam text and press Enter. Type 'quit' to exit.\n")

    # Initialize pipeline
    print("🔧 Initializing pipeline...")
    pipeline = VoiceAssistantPipeline(
        asr_engine="whisper",
        llm_model_size="1.5b",
        tts_engine="mms",
        device="cuda",
        detect_intent=True,
    )
    pipeline.load_components(show_progress=True)

    output_dir = Path(__file__).parent.parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)

    response_count = 0

    while True:
        try:
            print("\n" + "-" * 50)
            user_input = input("👤 You (Malayalam): ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                break

            if not user_input:
                continue

            response_count += 1
            output_audio = output_dir / f"interactive_{response_count}.wav"

            result = pipeline.process_text(
                text=user_input,
                input_language="ml",
                output_audio_path=str(output_audio),
            )

            print(f"\n🔄 English: {result.english_text}")

            if result.intent_type:
                print(f"🎯 Intent: {result.intent_type.upper()} ({result.intent_confidence:.0%})")
                print(f"   → {result.intent_description}")

            print(f"\n🤖 Response (EN): {result.english_response}")
            print(f"🗣️  Response (ML): {result.malayalam_response}")
            print(f"\n⏱️  Total: {result.total_time_ms:.1f}ms")
            print(f"💾 Audio: {output_audio}")

        except KeyboardInterrupt:
            break

    print("\n\n✅ Demo ended. Goodbye!")


def demo_with_audio():
    """Demo with audio file input."""
    from pipeline import VoiceAssistantPipeline

    print_banner()

    # Check for audio files in test directory
    test_audio_dir = Path(__file__).parent.parent / "test_audio"

    if not test_audio_dir.exists():
        print(f"\n⚠️  No test audio directory found at: {test_audio_dir}")
        print("Creating directory. Please add Malayalam audio files (.wav) and run again.")
        test_audio_dir.mkdir(exist_ok=True)
        return

    audio_files = list(test_audio_dir.glob("*.wav"))

    if not audio_files:
        print(f"\n⚠️  No .wav files found in: {test_audio_dir}")
        print("Please add Malayalam audio files and run again.")
        return

    print(f"\n📁 Found {len(audio_files)} audio file(s)")

    # Initialize pipeline
    print("\n🔧 Initializing pipeline...")
    pipeline = VoiceAssistantPipeline(
        asr_engine="whisper",
        asr_model_size="base",
        llm_model_size="1.5b",
        tts_engine="mms",
        device="cuda",
        detect_intent=True,
    )
    pipeline.load_components(show_progress=True)

    output_dir = Path(__file__).parent.parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)

    # Process each audio file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n\n{'='*70}")
        print(f"🎙️  Processing: {audio_file.name}")
        print(f"{'='*70}")

        output_audio = output_dir / f"response_{audio_file.stem}.wav"

        result = pipeline.process(
            audio_path=str(audio_file),
            output_audio_path=str(output_audio),
        )

        print_result(result)

        if result.success:
            print(f"💾 Audio saved to: {output_audio}")

        pipeline.clear_conversation()

    print(f"\n\n{'='*70}")
    print("✅ DEMO COMPLETE!")
    print(f"{'='*70}\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Assistant Pipeline Demo")
    parser.add_argument(
        "--mode",
        choices=["text", "interactive", "audio"],
        default="text",
        help="Demo mode: text (predefined), interactive, or audio (from files)"
    )

    args = parser.parse_args()

    if args.mode == "text":
        demo_text_input()
    elif args.mode == "interactive":
        demo_interactive()
    elif args.mode == "audio":
        demo_with_audio()


if __name__ == "__main__":
    main()
