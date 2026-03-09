"""
Pingala V1 ASR Implementation
CPU-first multilingual speech recognition with 2.94% WER.
Uses the official pingala-shunya SDK.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class PingalaASR:
    """
    Pingala V1 Automatic Speech Recognition.

    Uses the official PingalaTranscriber from pingala-shunya package.
    Achieves 2.94% WER -- significantly better than Whisper on Indian languages.
    Supports 200+ languages including all 11 target Indian languages.
    """

    MODEL_ID = "shunyalabs/pingala-v1-universal"

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
        "en": "English",
    }

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: str = "cpu",
        language: Optional[str] = None,
    ):
        self.model_id = model_id or self.MODEL_ID
        self.device = device
        self.language = language
        self.transcriber = None

    def load_model(self):
        """Load the Pingala V1 model via official SDK."""
        try:
            from pingala_shunya import PingalaTranscriber

            logger.info(f"Loading Pingala V1 model: {self.model_id}")

            self.transcriber = PingalaTranscriber(
                model_name=self.model_id,
                backend="ct2",
            )

            logger.info(f"Pingala V1 model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Pingala V1 model: {e}")
            raise

    def _ensure_wav(self, audio: Union[str, Path]) -> str:
        """Convert non-WAV audio to WAV using ffmpeg."""
        audio_path = str(audio)
        if audio_path.lower().endswith(".wav"):
            return audio_path

        # Use ffmpeg to convert to a temp WAV file
        import tempfile
        import subprocess

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", tmp.name],
            capture_output=True,
        )
        return tmp.name

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
            Dictionary with text, language, language_name, segments
        """
        if self.transcriber is None:
            self.load_model()

        target_lang = language or self.language

        try:
            logger.info(f"Transcribing audio (language: {target_lang or 'auto'})")

            tmp_wav = None

            if isinstance(audio, np.ndarray):
                # Save numpy array to temp WAV
                import tempfile
                import soundfile as sf

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp.close()
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                sf.write(tmp.name, audio.astype(np.float32), 16000)
                audio_path = tmp.name
                tmp_wav = tmp.name
            else:
                audio_path = self._ensure_wav(audio)
                if audio_path != str(audio):
                    tmp_wav = audio_path

            # Use official SDK transcribe_file
            kwargs = {"beam_size": 5}
            if target_lang:
                kwargs["language"] = target_lang

            segments, info = self.transcriber.transcribe_file(
                audio_path,
                **kwargs,
            )

            # Clean up temp file
            if tmp_wav:
                try:
                    Path(tmp_wav).unlink()
                except Exception:
                    pass

            # Combine all segment texts
            text = " ".join(seg.text.strip() for seg in segments).strip()

            detected_lang = target_lang or getattr(info, "language", "auto")
            lang_name = self.SUPPORTED_INDIAN_LANGUAGES.get(
                detected_lang, detected_lang
            )

            logger.info(f"Transcription complete: '{text[:80]}'")

            return {
                "text": text,
                "language": detected_lang,
                "language_name": lang_name,
                "segments": [
                    {"start": s.start, "end": s.end, "text": s.text}
                    for s in segments
                ],
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def detect_language(self, audio: Union[str, Path, np.ndarray]) -> dict:
        """Detect the language of audio."""
        result = self.transcribe(audio, language=None)
        return {
            "language": result["language"],
            "language_name": result["language_name"],
            "confidence": 0.0,
            "all_probabilities": {},
        }


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
) -> str:
    """Quick transcription using Pingala V1."""
    asr = PingalaASR(language=language)
    result = asr.transcribe(audio_path)
    return result["text"]
