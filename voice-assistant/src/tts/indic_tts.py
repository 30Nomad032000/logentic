"""
Indic TTS Implementation
Provides multilingual text-to-speech for Indian languages using AI4Bharat models.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class IndicTTS:
    """
    AI4Bharat Indic TTS for Indian languages.

    Supports 21 Indian languages with emotion-aware synthesis.
    """

    SUPPORTED_LANGUAGES = {
        "hi": "Hindi",
        "ml": "Malayalam",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "pa": "Punjabi",
        "or": "Odia",
        "as": "Assamese",
        "en": "English",
    }

    SUPPORTED_EMOTIONS = [
        "neutral",
        "happy",
        "sad",
        "angry",
        "fear",
        "surprise",
        "disgust",
    ]

    def __init__(
        self,
        default_language: str = "hi",
        device: str = "cuda",
    ):
        """
        Initialize Indic TTS.

        Args:
            default_language: Default language code
            device: Device to run on - cuda or cpu
        """
        self.default_language = default_language
        self.device = device
        self.model = None
        self.processor = None

    def load_model(self):
        """Load the Indic TTS model from HuggingFace."""
        try:
            from transformers import AutoProcessor, AutoModelForTextToWaveform

            logger.info("Loading AI4Bharat Indic Parler-TTS model...")

            # Note: Using the indic-parler-tts model
            model_id = "ai4bharat/indic-parler-tts"

            self.processor = AutoProcessor.from_pretrained(model_id)
            self.model = AutoModelForTextToWaveform.from_pretrained(model_id)
            self.model.to(self.device)

            logger.info("Indic TTS model loaded successfully")

        except Exception as e:
            logger.warning(f"Failed to load Indic Parler-TTS: {e}")
            logger.info("Falling back to basic TTS...")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """Load a fallback TTS model if primary fails."""
        try:
            # Using Coqui TTS as fallback
            from TTS.api import TTS

            self.model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            logger.info("Fallback TTS model loaded")
        except Exception as e:
            logger.error(f"Failed to load fallback TTS: {e}")

    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        emotion: str = "neutral",
        output_path: Optional[Union[str, Path]] = None,
    ) -> Union[np.ndarray, str]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code (uses default if not specified)
            emotion: Emotion for synthesis
            output_path: Optional path to save audio file

        Returns:
            Audio array or path to saved file
        """
        if self.model is None:
            self.load_model()

        target_lang = language or self.default_language
        lang_name = self.SUPPORTED_LANGUAGES.get(target_lang, target_lang)

        logger.info(f"Synthesizing speech in {lang_name} with {emotion} emotion")

        try:
            # Check if we're using Indic Parler-TTS or fallback
            if hasattr(self.model, 'generate'):
                # Indic Parler-TTS style
                description = f"A {emotion} voice speaking in {lang_name}"

                inputs = self.processor(
                    text=text,
                    description=description,
                    return_tensors="pt"
                ).to(self.device)

                audio = self.model.generate(**inputs)
                audio_array = audio.cpu().numpy().squeeze()

            elif hasattr(self.model, 'tts'):
                # Coqui TTS fallback
                if output_path:
                    self.model.tts_to_file(text=text, file_path=str(output_path))
                    return str(output_path)
                else:
                    audio_array = self.model.tts(text=text)
                    audio_array = np.array(audio_array)
            else:
                raise ValueError("No valid TTS model loaded")

            # Save to file if path provided
            if output_path:
                import soundfile as sf
                sf.write(str(output_path), audio_array, samplerate=22050)
                logger.info(f"Audio saved to {output_path}")
                return str(output_path)

            return audio_array

        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise

    def get_supported_languages(self) -> dict:
        """Return dictionary of supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()

    def get_supported_emotions(self) -> list:
        """Return list of supported emotions."""
        return self.SUPPORTED_EMOTIONS.copy()


# Convenience function for quick synthesis
def text_to_speech(
    text: str,
    language: str = "hi",
    output_path: Optional[str] = None,
) -> Union[np.ndarray, str]:
    """
    Quick text-to-speech function.

    Args:
        text: Text to synthesize
        language: Language code
        output_path: Optional output file path

    Returns:
        Audio array or path to saved file
    """
    tts = IndicTTS(default_language=language)
    return tts.synthesize(text, output_path=output_path)
