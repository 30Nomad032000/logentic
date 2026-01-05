#!/usr/bin/env python3
"""
Translation Test Script
Test IndicTrans2 Malayalam <-> English translation.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from translation import IndicTranslator, ml_to_en, en_to_ml


def main():
    print("=" * 60)
    print("IndicTrans2 Translation Test")
    print("=" * 60)

    # Test texts
    malayalam_texts = [
        "നമസ്കാരം, എന്റെ പേര് അസിസ്റ്റന്റ് ആണ്",
        "ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയുണ്ട്?",
        "കേരളം ഇന്ത്യയുടെ തെക്കുപടിഞ്ഞാറൻ തീരത്ത് സ്ഥിതി ചെയ്യുന്ന ഒരു സംസ്ഥാനമാണ്.",
    ]

    english_texts = [
        "Hello, how can I help you today?",
        "The weather is pleasant today with partly cloudy skies.",
        "Please turn on the lights in the living room.",
    ]

    # Initialize translator
    print("\n📌 Loading IndicTrans2 models...")
    translator = IndicTranslator(device="cuda")

    # Test Malayalam → English
    print("\n" + "-" * 40)
    print("Malayalam → English")
    print("-" * 40)

    for text in malayalam_texts:
        print(f"\n[ML] {text}")
        start = time.perf_counter()
        translated = translator.ml_to_en(text)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[EN] {translated}")
        print(f"     ⏱️  {elapsed:.1f}ms")

    # Test English → Malayalam
    print("\n" + "-" * 40)
    print("English → Malayalam")
    print("-" * 40)

    for text in english_texts:
        print(f"\n[EN] {text}")
        start = time.perf_counter()
        translated = translator.en_to_ml(text)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[ML] {translated}")
        print(f"     ⏱️  {elapsed:.1f}ms")

    # Round-trip test
    print("\n" + "-" * 40)
    print("Round-trip Test (ML → EN → ML)")
    print("-" * 40)

    original = "എനിക്ക് വെളിച്ചം ഓണാക്കണം"
    print(f"\n[Original ML] {original}")

    en_version = translator.ml_to_en(original)
    print(f"[→ English]   {en_version}")

    back_to_ml = translator.en_to_ml(en_version)
    print(f"[→ Malayalam] {back_to_ml}")

    print("\n" + "=" * 60)
    print("✅ Translation test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
