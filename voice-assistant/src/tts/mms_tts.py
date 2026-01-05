"""
MMS-TTS (Meta Multilingual Speech) Implementation
Offline TTS supporting 1100+ languages including Malayalam.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class MMSTTS:
    """
    Meta's MMS-TTS for offline multilingual text-to-speech.

    Supports Malayalam, Hindi, Tamil, and 1100+ other languages.
    Runs fully offline after initial model download (~300MB).
    """

    # Language codes for MMS-TTS (ISO 639-3)
    LANGUAGE_CODES = {
        "ml": "mal",  # Malayalam
        "hi": "hin",  # Hindi
        "ta": "tam",  # Tamil
        "te": "tel",  # Telugu
        "bn": "ben",  # Bengali
        "mr": "mar",  # Marathi
        "gu": "guj",  # Gujarati
        "kn": "kan",  # Kannada
        "pa": "pan",  # Punjabi
        "en": "eng",  # English
    }

    def __init__(
        self,
        default_language: str = "ml",
        device: str = "cuda",
    ):
        """
        Initialize MMS-TTS.

        Args:
            default_language: Default language code (ISO 639-1)
            device: Device to run on - cuda or cpu
        """
        self.default_language = default_language
        self.device = device
        self.model = None
        self.tokenizer = None
        self.sample_rate = 16000

    def load_model(self, language: Optional[str] = None):
        """Load the MMS-TTS model for specified language."""
        try:
            from transformers import VitsModel, AutoTokenizer
            import torch

            lang = language or self.default_language
            mms_lang = self.LANGUAGE_CODES.get(lang, lang)

            model_id = f"facebook/mms-tts-{mms_lang}"

            logger.info(f"Loading MMS-TTS model: {model_id}")

            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = VitsModel.from_pretrained(model_id)

            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
            else:
                self.model = self.model.to("cpu")
                self.device = "cpu"

            self.model.eval()
            self._current_language = lang

            logger.info(f"MMS-TTS model loaded successfully for {mms_lang}")

        except Exception as e:
            logger.error(f"Failed to load MMS-TTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        speed: float = 1.0,
    ) -> Union[np.ndarray, str]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code (uses default if not specified)
            output_path: Optional path to save audio file
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            Audio array (numpy) or path to saved file
        """
        import torch

        target_lang = language or self.default_language

        # Load model if not loaded or language changed
        if self.model is None or getattr(self, '_current_language', None) != target_lang:
            self.load_model(target_lang)

        logger.info(f"Synthesizing speech in {target_lang}: '{text[:50]}...'")

        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt")

            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # Generate audio
            with torch.no_grad():
                output = self.model(**inputs)

            audio_array = output.waveform.cpu().numpy().squeeze()

            # Apply speed adjustment if needed
            if speed != 1.0:
                audio_array = self._adjust_speed(audio_array, speed)

            # Save to file if path provided
            if output_path:
                import soundfile as sf
                sf.write(str(output_path), audio_array, samplerate=self.sample_rate)
                logger.info(f"Audio saved to {output_path}")
                return str(output_path)

            return audio_array

        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Adjust audio playback speed using resampling."""
        from scipy import signal

        # Resample to change speed
        original_length = len(audio)
        new_length = int(original_length / speed)
        return signal.resample(audio, new_length)

    def get_supported_languages(self) -> dict:
        """Return dictionary of supported languages."""
        return {
            code: name for code, name in [
                ("ml", "Malayalam"),
                ("hi", "Hindi"),
                ("ta", "Tamil"),
                ("te", "Telugu"),
                ("bn", "Bengali"),
                ("mr", "Marathi"),
                ("gu", "Gujarati"),
                ("kn", "Kannada"),
                ("pa", "Punjabi"),
                ("en", "English"),
            ]
        }


# Convenience function
def synthesize_mms(
    text: str,
    language: str = "ml",
    output_path: Optional[str] = None,
) -> Union[np.ndarray, str]:
    """
    Quick MMS-TTS synthesis function.

    Args:
        text: Text to synthesize
        language: Language code
        output_path: Optional output file path

    Returns:
        Audio array or path to saved file
    """
    tts = MMSTTS(default_language=language)
    return tts.synthesize(text, output_path=output_path)
