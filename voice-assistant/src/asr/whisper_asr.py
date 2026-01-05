"""
Whisper ASR Implementation
Provides multilingual speech recognition using OpenAI's Whisper model.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class WhisperASR:
    """
    Whisper-based Automatic Speech Recognition.

    Supports 99 languages including Hindi, Malayalam, Tamil, Telugu, etc.
    """

    SUPPORTED_INDIAN_LANGUAGES = {
        "hi": "Hindi",
        "ml": "Malayalam",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "pa": "Punjabi",
        "ur": "Urdu",
    }

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cuda",
        language: Optional[str] = None,
    ):
        """
        Initialize Whisper ASR.

        Args:
            model_size: Model size - tiny, base, small, medium, large
            device: Device to run on - cuda or cpu
            language: Target language code (None for auto-detection)
        """
        self.model_size = model_size
        self.device = device
        self.language = language
        self.model = None

    def load_model(self):
        """Load the Whisper model."""
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        language: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio: Audio file path or numpy array
            language: Override language for this transcription

        Returns:
            Dictionary with transcription results:
            - text: Transcribed text
            - language: Detected/used language
            - segments: Detailed segments with timestamps
        """
        if self.model is None:
            self.load_model()

        target_lang = language or self.language

        try:
            logger.info(f"Transcribing audio (language: {target_lang or 'auto'})")

            # Load audio using soundfile to avoid ffmpeg dependency
            audio_input = audio
            if isinstance(audio, (str, Path)):
                try:
                    import soundfile as sf
                    audio_data, sr = sf.read(str(audio))
                    # Resample to 16kHz if needed (Whisper expects 16kHz)
                    if sr != 16000:
                        # Simple resampling
                        duration = len(audio_data) / sr
                        target_length = int(duration * 16000)
                        indices = np.linspace(0, len(audio_data) - 1, target_length).astype(int)
                        audio_data = audio_data[indices]
                    # Convert to float32 and mono
                    if len(audio_data.shape) > 1:
                        audio_data = audio_data.mean(axis=1)
                    audio_input = audio_data.astype(np.float32)
                except ImportError:
                    # Fall back to whisper's loader (requires ffmpeg)
                    audio_input = str(audio)

            result = self.model.transcribe(
                audio_input,
                language=target_lang,
                task="transcribe",
            )

            detected_lang = result.get("language", target_lang)
            lang_name = self.SUPPORTED_INDIAN_LANGUAGES.get(
                detected_lang, detected_lang
            )

            logger.info(f"Transcription complete. Detected language: {lang_name}")

            return {
                "text": result["text"].strip(),
                "language": detected_lang,
                "language_name": lang_name,
                "segments": result.get("segments", []),
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def detect_language(self, audio: Union[str, Path, np.ndarray]) -> dict:
        """
        Detect the language of audio without full transcription.

        Args:
            audio: Audio file path or numpy array

        Returns:
            Dictionary with language detection results
        """
        if self.model is None:
            self.load_model()

        try:
            import whisper

            # Load and preprocess audio
            if isinstance(audio, (str, Path)):
                audio_array = whisper.load_audio(str(audio))
            else:
                audio_array = audio

            audio_array = whisper.pad_or_trim(audio_array)
            mel = whisper.log_mel_spectrogram(audio_array).to(self.device)

            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)

            return {
                "language": detected_lang,
                "language_name": self.SUPPORTED_INDIAN_LANGUAGES.get(
                    detected_lang, detected_lang
                ),
                "confidence": probs[detected_lang],
                "all_probabilities": dict(sorted(
                    probs.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
            }

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise


# Convenience function for quick transcription
def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
) -> str:
    """
    Quick transcription function.

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        language: Target language

    Returns:
        Transcribed text
    """
    asr = WhisperASR(model_size=model_size, language=language)
    result = asr.transcribe(audio_path)
    return result["text"]
