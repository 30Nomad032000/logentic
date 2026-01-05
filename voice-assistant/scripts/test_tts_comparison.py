#!/usr/bin/env python3
"""
TTS A/B Testing Script
Compare MMS-TTS (offline) vs Cartesia (online) for Malayalam.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tts import TTSEngine, compare_tts


def main():
    # Test texts in different languages
    test_texts = {
        "ml": [
            # Short
            "നമസ്കാരം, എന്റെ പേര് അസിസ്റ്റന്റ് ആണ്",
            # Medium
            "കേരളം ഇന്ത്യയുടെ തെക്കുപടിഞ്ഞാറൻ തീരത്ത് സ്ഥിതി ചെയ്യുന്ന ഒരു സംസ്ഥാനമാണ്. ഇവിടെ മനോഹരമായ കടൽത്തീരങ്ങളും പച്ചപ്പ് നിറഞ്ഞ മലകളും ഉണ്ട്.",
            # Long paragraph
            "ഇന്നത്തെ കാലാവസ്ഥാ റിപ്പോർട്ട് അനുസരിച്ച്, കേരളത്തിൽ ഭാഗികമായ മേഘാവൃതമായ ആകാശവും ഇടയ്ക്കിടെ മഴയും പ്രതീക്ഷിക്കുന്നു. താപനില ഇരുപത്തിയഞ്ച് മുതൽ മുപ്പത് ഡിഗ്രി സെൽഷ്യസ് വരെ ആയിരിക്കും. കടൽ ശാന്തമായിരിക്കും, മത്സ്യബന്ധനത്തിന് അനുകൂലമായ സാഹചര്യമാണ്. എന്നിരുന്നാലും, മലയോര മേഖലകളിൽ ശക്തമായ കാറ്റ് വീശാൻ സാധ്യതയുണ്ട്.",
        ],
        "hi": [
            "नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?",
            "आज का मौसम कैसा है?",
        ],
        "en": [
            "Hello, how can I help you today?",
            "The weather is quite pleasant this morning.",
        ],
    }

    output_dir = Path(__file__).parent.parent / "test_outputs" / "tts_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TTS A/B Testing: MMS-TTS vs Cartesia")
    print("=" * 60)

    # Test Malayalam (primary target)
    print("\n📌 Testing Malayalam (ml):")
    print("-" * 40)

    text_labels = ["Short", "Medium", "Long paragraph"]

    for i, text in enumerate(test_texts["ml"]):
        label = text_labels[i] if i < len(text_labels) else f"Text {i+1}"
        print(f"\n[{label}]: {text[:60]}...")

        # Filename-safe label
        file_label = label.lower().replace(" ", "_")

        # Test MMS-TTS (offline)
        try:
            engine = TTSEngine(backend="mms", device="cuda")
            result = engine.synthesize(
                text=text,
                language="ml",
                output_path=output_dir / f"ml_mms_{file_label}.wav"
            )
            print(f"  ✅ MMS-TTS: {result.duration_ms:.1f}ms (offline)")
        except Exception as e:
            print(f"  ❌ MMS-TTS failed: {e}")

        # Test Cartesia (online)
        try:
            engine = TTSEngine(backend="cartesia")
            result = engine.synthesize(
                text=text,
                language="ml",
                output_path=output_dir / f"ml_cartesia_{file_label}.wav"
            )
            print(f"  ✅ Cartesia: {result.duration_ms:.1f}ms (online)")
        except Exception as e:
            print(f"  ❌ Cartesia failed: {e}")

    print(f"\n📁 Output files saved to: {output_dir}")

    # Quick comparison
    print("\n" + "=" * 60)
    print("Quick Comparison (all backends):")
    print("=" * 60)

    try:
        results = compare_tts(
            text="നമസ്കാരം, എങ്ങനെയുണ്ട്?",
            language="ml",
            output_dir=str(output_dir / "comparison"),
        )

        print("\nResults:")
        for backend, result in results.items():
            if result:
                print(f"  {backend}: {result.duration_ms:.1f}ms")
            else:
                print(f"  {backend}: Failed")

    except Exception as e:
        print(f"Comparison failed: {e}")

    print("\n✅ Done! Listen to the audio files to compare quality.")


if __name__ == "__main__":
    main()
