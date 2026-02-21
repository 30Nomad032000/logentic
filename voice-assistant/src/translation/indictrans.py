"""
IndicTrans2 Translation Module
Provides multilingual translation using AI4Bharat's IndicTrans2.
Supports both full (1B) and distilled (~211M) model variants.
"""

import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)


class IndicTranslator:
    """
    AI4Bharat IndicTrans2 translator for Indian languages.

    Supports two model variants:
    - "full": Original 1B parameter models (~500MB per direction)
    - "dist": Distilled ~211M parameter models (~100MB per direction, 5x smaller, same quality)

    Also supports direct Indic-to-Indic translation via the indic-indic-dist model.
    """

    # IndicTrans2 model IDs on HuggingFace
    MODEL_VARIANTS = {
        "full": {
            "en-indic": "ai4bharat/indictrans2-en-indic-1B",
            "indic-en": "ai4bharat/indictrans2-indic-en-1B",
        },
        "dist": {
            "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
            "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
            "indic-indic": "ai4bharat/indictrans2-indic-indic-dist-320M",
        },
    }

    # Backward compat alias
    MODELS = MODEL_VARIANTS["full"]

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
        "ur": "urd_Arab",  # Urdu
        "en": "eng_Latn",  # English
    }

    def __init__(
        self,
        device: str = "cuda",
        load_on_init: bool = False,
        model_variant: Literal["full", "dist"] = "dist",
    ):
        """
        Initialize IndicTrans2 translator.

        Args:
            device: Device to run on - cuda or cpu
            load_on_init: Whether to load models immediately
            model_variant: Model variant - "full" (1B) or "dist" (~211M, recommended)
        """
        self.device = device
        self.model_variant = model_variant
        self.models = {}
        self.tokenizers = {}

        if load_on_init:
            self.load_models()

    def load_models(self, directions: Optional[list] = None):
        """
        Load translation models.

        Args:
            directions: List of directions to load ["en-indic", "indic-en", "indic-indic"]
                       If None, loads en-indic and indic-en.
        """
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch

        directions = directions or ["en-indic", "indic-en"]
        variant_models = self.MODEL_VARIANTS[self.model_variant]

        for direction in directions:
            if direction in self.models:
                continue

            if direction not in variant_models:
                logger.warning(
                    f"Direction '{direction}' not available for variant '{self.model_variant}', skipping"
                )
                continue

            model_id = variant_models[direction]
            logger.info(f"Loading IndicTrans2 model ({self.model_variant}): {model_id}")

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

    def translate_indic(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 256,
    ) -> str:
        """
        Translate directly between two Indic languages (without English pivot).

        Only available with the 'dist' model variant which includes the indic-indic model.
        Falls back to two-step translation (src→en→tgt) if indic-indic model unavailable.

        Args:
            text: Text to translate
            source_lang: Source Indic language code (ml, hi, ta, etc.)
            target_lang: Target Indic language code
            max_length: Maximum output length

        Returns:
            Translated text
        """
        direction = "indic-indic"
        variant_models = self.MODEL_VARIANTS[self.model_variant]

        if direction not in variant_models:
            logger.info(
                f"Indic-Indic model not available for variant '{self.model_variant}', "
                f"falling back to two-step translation via English"
            )
            english = self.translate(text, source_lang, "en", max_length)
            return self.translate(english, "en", target_lang, max_length)

        return self._translate_with_direction(
            text, source_lang, target_lang, direction, max_length
        )

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
        # For Indic-to-Indic (neither is English), use translate_indic
        if source_lang != "en" and target_lang != "en":
            return self.translate_indic(text, source_lang, target_lang, max_length)

        # Determine direction
        if source_lang == "en":
            direction = "en-indic"
        else:
            direction = "indic-en"

        return self._translate_with_direction(
            text, source_lang, target_lang, direction, max_length
        )

    def _translate_with_direction(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        direction: str,
        max_length: int = 256,
    ) -> str:
        """
        Internal method to translate with a specific model direction.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            direction: Model direction key (en-indic, indic-en, indic-indic)
            max_length: Maximum output length

        Returns:
            Translated text
        """
        import torch

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

def get_translator(
    device: str = "cuda",
    model_variant: str = "dist",
) -> IndicTranslator:
    """Get or create singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = IndicTranslator(device=device, model_variant=model_variant)
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
