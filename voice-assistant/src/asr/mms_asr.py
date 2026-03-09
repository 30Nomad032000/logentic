"""
Meta Omnilingual ASR Implementation
Uses the official omnilingual-asr package (omniASR-LLM-1B).
Supports 1600+ languages including all Indian languages.
Falls back to MMS-1B (facebook/mms-1b-all) if omnilingual-asr is not installed.

Install: pip install omnilingual-asr
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


# Language code mapping: ISO 639-1 -> Omnilingual ASR format (lang_Script)
LANG_TO_OMNI = {
    "ml": "mal_Mlym",   # Malayalam
    "hi": "hin_Deva",   # Hindi
    "ta": "tam_Taml",   # Tamil
    "te": "tel_Telu",   # Telugu
    "bn": "ben_Beng",   # Bengali
    "mr": "mar_Deva",   # Marathi
    "gu": "guj_Gujr",   # Gujarati
    "kn": "kan_Knda",   # Kannada
    "pa": "pan_Guru",   # Punjabi
    "ur": "urd_Arab",   # Urdu
    "en": "eng_Latn",   # English
}

# ISO 639-1 -> ISO 639-3 (for MMS-1B fallback)
LANG_TO_MMS = {
    "ml": "mal", "hi": "hin", "ta": "tam", "te": "tel",
    "bn": "ben", "mr": "mar", "gu": "guj", "kn": "kan",
    "pa": "pan", "ur": "urd", "en": "eng",
}

LANG_NAMES = {
    "ml": "Malayalam", "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
    "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
    "pa": "Punjabi", "ur": "Urdu", "en": "English",
}


def _load_audio_from_file(audio_path: str) -> np.ndarray:
    """Load audio from any format (WebM, OGG, WAV, etc.) as 16kHz mono float32."""
    # For WAV files, try soundfile first
    if audio_path.lower().endswith(".wav"):
        try:
            import soundfile as sf
            data, sr = sf.read(audio_path)
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            if sr != 16000:
                duration = len(data) / sr
                target_len = int(duration * 16000)
                indices = np.linspace(0, len(data) - 1, target_len).astype(int)
                data = data[indices]
            return data.astype(np.float32)
        except Exception:
            pass

    # For non-WAV (WebM, OGG, etc.), convert via ffmpeg
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-f", "wav", tmp.name],
            capture_output=True, check=True,
        )
        import soundfile as sf
        data, sr = sf.read(tmp.name)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        return data.astype(np.float32)
    finally:
        try:
            Path(tmp.name).unlink()
        except Exception:
            pass


class OmnilASR:
    """
    Meta Omnilingual ASR — 1600+ language speech recognition.

    Uses the official omnilingual-asr package with omniASR-LLM-1B model.
    """

    def __init__(
        self,
        model_card: str = "omniASR_LLM_Unlimited_1B_v2",
        device: str = "cpu",
        language: Optional[str] = None,
    ):
        self.model_card = model_card
        self.device = device
        self.language = language
        self.pipeline = None

    def load_model(self):
        """Load the Omnilingual ASR pipeline."""
        from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

        logger.info(f"Loading Omnilingual ASR model: {self.model_card}")
        self.pipeline = ASRInferencePipeline(model_card=self.model_card)
        logger.info("Omnilingual ASR model loaded")

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        language: Optional[str] = None,
    ) -> dict:
        if self.pipeline is None:
            self.load_model()

        target_lang = language or self.language or "ml"
        omni_lang = LANG_TO_OMNI.get(target_lang, f"{target_lang}_Latn")

        # Omnilingual ASR expects file paths; save numpy arrays to temp files
        tmp_path = None
        if isinstance(audio, np.ndarray):
            import soundfile as sf
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.close()
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            sf.write(tmp.name, audio.astype(np.float32), 16000)
            audio_path = tmp.name
            tmp_path = tmp.name
        else:
            audio_path = str(audio)
            # Convert non-WAV to WAV for the pipeline
            if not audio_path.lower().endswith((".wav", ".flac")):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp.close()
                subprocess.run(
                    ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-f", "wav", tmp.name],
                    capture_output=True, check=True,
                )
                audio_path = tmp.name
                tmp_path = tmp.name

        try:
            logger.info(f"Transcribing with Omnilingual ASR (lang={omni_lang})")
            results = self.pipeline.transcribe(
                [audio_path],
                lang=[omni_lang],
                batch_size=1,
            )
            text = results[0] if results else ""
        finally:
            if tmp_path:
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass

        return {
            "text": text.strip() if isinstance(text, str) else str(text).strip(),
            "language": target_lang,
            "language_name": LANG_NAMES.get(target_lang, target_lang),
        }


class MMSASR:
    """
    Meta MMS-1B ASR — fallback if omnilingual-asr is not installed.

    Uses facebook/mms-1b-all (1B params, 1000+ languages).
    """

    MODEL_ID = "facebook/mms-1b-all"

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: str = "cpu",
        language: Optional[str] = None,
    ):
        self.model_id = model_id or self.MODEL_ID
        self.device = device
        self.language = language
        self.model = None
        self.processor = None

    def load_model(self):
        from transformers import Wav2Vec2ForCTC, AutoProcessor
        import torch

        logger.info(f"Loading MMS model: {self.model_id}")

        cuda_available = torch.cuda.is_available()
        if self.device == "cuda" and cuda_available:
            device = "cuda:0"
        else:
            device = "cpu"

        self.processor = AutoProcessor.from_pretrained(self.model_id)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_id).to(device)
        self._device = device

        logger.info(f"MMS model loaded on {device}")

    def _set_language(self, lang_code: str):
        mms_code = LANG_TO_MMS.get(lang_code, lang_code)
        self.processor.tokenizer.set_target_lang(mms_code)
        self.model.load_adapter(mms_code)

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        language: Optional[str] = None,
    ) -> dict:
        if self.model is None:
            self.load_model()

        import torch

        target_lang = language or self.language or "ml"
        self._set_language(target_lang)

        # Load audio
        if isinstance(audio, np.ndarray):
            audio_data = audio.mean(axis=1) if len(audio.shape) > 1 else audio
            audio_data = audio_data.astype(np.float32)
        else:
            audio_data = _load_audio_from_file(str(audio))

        logger.info(f"Transcribing audio ({len(audio_data) / 16000:.1f}s) in {target_lang}")

        inputs = self.processor(audio_data, sampling_rate=16000, return_tensors="pt")
        input_values = inputs.input_values.to(self._device)

        with torch.no_grad():
            outputs = self.model(input_values)

        predicted_ids = torch.argmax(outputs.logits, dim=-1)
        text = self.processor.batch_decode(predicted_ids)[0]

        return {
            "text": text.strip(),
            "language": target_lang,
            "language_name": LANG_NAMES.get(target_lang, target_lang),
        }


def create_asr(device: str = "cpu", language: Optional[str] = None):
    """
    Create the best available Meta ASR engine.
    Tries Omnilingual ASR first, falls back to MMS-1B.
    """
    try:
        import omnilingual_asr  # noqa: F401
        logger.info("Using Meta Omnilingual ASR (omniASR-LLM-1B)")
        return OmnilASR(device=device, language=language)
    except ImportError:
        logger.info("omnilingual-asr not installed, falling back to MMS-1B")
        return MMSASR(device=device, language=language)
