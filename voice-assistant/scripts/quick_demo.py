#!/usr/bin/env python3
"""
Quick Pipeline Demo - Lightweight version for testing
Tests each component separately with progress display.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    print("\n" + "=" * 70)
    print("   🎙️  VOICE ASSISTANT - QUICK DEMO")
    print("=" * 70)

    # Test input
    malayalam_input = "നമസ്കാരം, ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയുണ്ട്?"
    print(f"\n📥 INPUT (Malayalam):")
    print(f"   {malayalam_input}")

    # Step 1: Translation ML → EN
    print("\n" + "-" * 50)
    print("🔄 STEP 1: Translation (Malayalam → English)")
    print("-" * 50)

    try:
        from translation import IndicTranslator

        start = time.perf_counter()
        translator = IndicTranslator(device="cuda")
        english_text = translator.ml_to_en(malayalam_input)
        trans_time = (time.perf_counter() - start) * 1000

        print(f"   ✅ English: {english_text}")
        print(f"   ⏱️  Time: {trans_time:.1f}ms")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        english_text = "Hello, how is the weather today?"
        print(f"   ⚠️  Using fallback: {english_text}")

    # Step 2: Intent Detection
    print("\n" + "-" * 50)
    print("🎯 STEP 2: Intent Detection")
    print("-" * 50)

    try:
        from pipeline.intent import IntentDetector

        detector = IntentDetector(use_llm=False)
        intent = detector.detect(malayalam_input, english_text)

        print(f"   ✅ Intent Type: {intent.type.value.upper()}")
        print(f"   📝 Description: {intent.description}")
        print(f"   🎯 Confidence: {intent.confidence:.0%}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   ⚠️  Skipping intent detection")

    # Step 3: LLM Response
    print("\n" + "-" * 50)
    print("🤖 STEP 3: LLM Response Generation")
    print("-" * 50)

    try:
        from llm import QwenLLM

        start = time.perf_counter()
        llm = QwenLLM(model_size="1.5b", device="cuda")
        llm.set_system_prompt("""You are a helpful voice assistant. Give brief, natural responses suitable for speech. Keep responses to 1-2 sentences.""")

        response = llm.chat(english_text)
        english_response = response.content
        llm_time = (time.perf_counter() - start) * 1000

        print(f"   ✅ Response: {english_response}")
        print(f"   ⏱️  Time: {llm_time:.1f}ms")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        english_response = "The weather today is pleasant with partly cloudy skies."
        print(f"   ⚠️  Using fallback: {english_response}")

    # Step 4: Translation EN → ML
    print("\n" + "-" * 50)
    print("🔄 STEP 4: Translation (English → Malayalam)")
    print("-" * 50)

    try:
        start = time.perf_counter()
        malayalam_response = translator.en_to_ml(english_response)
        trans_time = (time.perf_counter() - start) * 1000

        print(f"   ✅ Malayalam: {malayalam_response}")
        print(f"   ⏱️  Time: {trans_time:.1f}ms")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        malayalam_response = english_response
        print(f"   ⚠️  Using English response")

    # Step 5: TTS
    print("\n" + "-" * 50)
    print("🔊 STEP 5: Text-to-Speech (MMS-TTS)")
    print("-" * 50)

    output_dir = Path(__file__).parent.parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "quick_demo_response.wav"

    try:
        from tts import TTSEngine

        start = time.perf_counter()
        tts = TTSEngine(backend="mms", device="cuda")
        result = tts.synthesize(
            text=malayalam_response,
            language="ml",
            output_path=str(output_file)
        )
        tts_time = (time.perf_counter() - start) * 1000

        print(f"   ✅ Audio generated!")
        print(f"   💾 Saved to: {output_file}")
        print(f"   ⏱️  Time: {tts_time:.1f}ms")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   ⚠️  TTS failed")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"""
   INPUT:    {malayalam_input}

   ENGLISH:  {english_text}

   INTENT:   {intent.type.value.upper() if 'intent' in dir() else 'N/A'}

   RESPONSE: {english_response}

   OUTPUT:   {malayalam_response}

   AUDIO:    {output_file}
""")
    print("=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
