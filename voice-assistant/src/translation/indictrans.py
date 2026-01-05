"""
IndicTrans2 Translation Module
Provides Malayalam <-> English translation using AI4Bharat's IndicTrans2.
"""

import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)


class IndicTranslator:
    """
    AI4Bharat IndicTrans2 translator for Indian languages.

    Optimized for Malayalam <-> English translation.
    Runs fully offline after initial model download (~500MB per direction).
    """

    # IndicTrans2 model IDs on HuggingFace
    MODELS = {
        "en-indic": "ai4bharat/indictrans2-en-indic-1B",  # English → Indian languages
        "indic-en": "ai4bharat/indictrans2-indic-en-1B",  # Indian languages → English
    }

    # Language codes for IndicTrans2
    LANG_CODES = {
        "ml": "mal_Mlym",  # Malayalam
        "hi": "hin_Deva",  # Hindi
        "ta": "tam_Taml",  # Tamil
        "te": "tel_Telu",  # Telugu
        "bn": "ben_Beng",  # Bengali
        "mr": "mar_Deva",  # Marathi
        "gu": "guj_Gujr",  # Gujarati
        "kn": "kan_Knda",  # Kannada
        "pa": "pan_Guru",  # Punjabi
        "en": "eng_Latn",  # English
    }

    def __init__(
        self,
        device: str = "cuda",
        load_on_init: bool = False,
    ):
        """
        Initialize IndicTrans2 translator.

        Args:
            device: Device to run on - cuda or cpu
            load_on_init: Whether to load models immediately
        """
        self.device = device
        self.models = {}
        self.tokenizers = {}

        if load_on_init:
            self.load_models()

    def load_models(self, directions: Optional[list] = None):
        """
        Load translation models.

        Args:
            directions: List of directions to load ["en-indic", "indic-en"]
                       If None, loads both.
        """
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch

        directions = directions or ["en-indic", "indic-en"]

        for direction in directions:
            if direction in self.models:
                continue

            model_id = self.MODELS[direction]
            logger.info(f"Loading IndicTrans2 model: {model_id}")

            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                )
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                )

                if self.device == "cuda" and torch.cuda.is_available():
                    model = model.to("cuda")
                else:
                    model = model.to("cpu")
                    self.device = "cpu"

                model.eval()

                self.tokenizers[direction] = tokenizer
                self.models[direction] = model

                logger.info(f"Loaded {direction} model successfully")

            except Exception as e:
                logger.error(f"Failed to load {direction} model: {e}")
                raise

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 256,
    ) -> str:
        """
        Translate text between languages.

        Args:
            text: Text to translate
            source_lang: Source language code (ml, en, hi, etc.)
            target_lang: Target language code
            max_length: Maximum output length

        Returns:
            Translated text
        """
        import torch

        # Determine direction
        if source_lang == "en":
            direction = "en-indic"
        else:
            direction = "indic-en"

        # Load model if needed
        if direction not in self.models:
            self.load_models([direction])

        model = self.models[direction]
        tokenizer = self.tokenizers[direction]

        # Get language codes
        src_code = self.LANG_CODES.get(source_lang, source_lang)
        tgt_code = self.LANG_CODES.get(target_lang, target_lang)

        logger.info(f"Translating: {src_code} → {tgt_code}")

        try:
            # Prepare input with language tags
            input_text = f"{src_code} {text}"

            inputs = tokenizer(
                input_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )

            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # Generate translation
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=5,
                    num_return_sequences=1,
                    forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_code),
                )

            # Decode output
            translated = tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )

            # Remove language tag if present
            if translated.startswith(tgt_code):
                translated = translated[len(tgt_code):].strip()

            logger.info(f"Translation complete: '{text[:50]}...' → '{translated[:50]}...'")

            return translated

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    def ml_to_en(self, text: str) -> str:
        """Translate Malayalam to English."""
        return self.translate(text, source_lang="ml", target_lang="en")

    def en_to_ml(self, text: str) -> str:
        """Translate English to Malayalam."""
        return self.translate(text, source_lang="en", target_lang="ml")

    def get_supported_languages(self) -> dict:
        """Return supported languages."""
        return {
            "ml": "Malayalam",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "mr": "Marathi",
            "gu": "Gujarati",
            "kn": "Kannada",
            "pa": "Punjabi",
            "en": "English",
        }


# Convenience functions
_translator = None

def get_translator(device: str = "cuda") -> IndicTranslator:
    """Get or create singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = IndicTranslator(device=device)
    return _translator


def translate(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Quick translation function.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Translated text
    """
    translator = get_translator()
    return translator.translate(text, source_lang, target_lang)


def ml_to_en(text: str) -> str:
    """Quick Malayalam to English translation."""
    return get_translator().ml_to_en(text)


def en_to_ml(text: str) -> str:
    """Quick English to Malayalam translation."""
    return get_translator().en_to_ml(text)
