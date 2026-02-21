"""
Chatterbox TTS Implementation
350M parameter low-compute text-to-speech model.
CPU-friendly with 24kHz output quality.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class ChatterboxTTS:
    """
    Chatterbox-Turbo Text-to-Speech engine.

    350M parameter model designed for low-compute environments.
    Outputs 24kHz audio, runs efficiently on CPU.
    """

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ml": "Malayalam",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
    }

    def __init__(
        self,
        device: str = "cpu",
        sample_rate: int = 24000,
    ):
        """
        Initialize Chatterbox TTS.

        Args:
            device: Device to run on - cpu (default) or cuda
            sample_rate: Output sample rate (24kHz default)
        """
        self.device = device
        self.sample_rate = sample_rate
        self.model = None

    def load_model(self):
        """Load the Chatterbox model."""
        try:
            from chatterbox.tts import ChatterboxTTS as CBModel

            logger.info("Loading Chatterbox-Turbo model...")
            self.model = CBModel.from_pretrained(device=self.device)
            logger.info("Chatterbox model loaded successfully")

        except ImportError:
            logger.error(
                "chatterbox-tts not installed. "
                "Install with: pip install chatterbox-tts"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> Union[np.ndarray, str]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code (used for voice selection)
            output_path: Optional path to save audio file
            **kwargs: Additional arguments (ignored for compatibility)

        Returns:
            Audio numpy array or path to saved file
        """
        if self.model is None:
            self.load_model()

        lang = language or "en"
        logger.info(f"Synthesizing with Chatterbox: '{text[:50]}...' (lang={lang})")

        try:
            wav = self.model.generate(text)

            # Convert to numpy array
            if hasattr(wav, 'cpu'):
                audio_array = wav.cpu().numpy().squeeze()
            else:
                audio_array = np.array(wav).squeeze()

            # Save to file if path provided
            if output_path:
                import soundfile as sf
                sf.write(str(output_path), audio_array, samplerate=self.sample_rate)
                logger.info(f"Audio saved to {output_path}")
                return str(output_path)

            return audio_array

        except Exception as e:
            logger.error(f"Chatterbox synthesis failed: {e}")
            raise

    def get_supported_languages(self) -> dict:
        """Return supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()
