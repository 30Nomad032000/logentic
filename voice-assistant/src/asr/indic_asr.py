"""
Fine-tuned Whisper ASR for Indian Languages
Uses community fine-tuned models for much better accuracy than base Whisper.

Install: pip install transformers torch accelerate
"""

import logging
from pathlib import Path
from typing import Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class IndicWhisperASR:
    """
    Fine-tuned Whisper models for Indian languages.

    Uses community models fine-tuned specifically for each language.
    Much better accuracy than base Whisper for Indian languages.
    """

    SUPPORTED_LANGUAGES = {
        "ml": "Malayalam",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "en": "English",
    }

    # Whisper uses full language names for some languages
    WHISPER_LANG_CODES = {
        "ml": "malayalam",
        "hi": "hindi",
        "ta": "tamil",
        "te": "telugu",
        "bn": "bengali",
        "mr": "marathi",
        "gu": "gujarati",
        "kn": "kannada",
        "en": "english",
    }

    # Model IDs - using OpenAI official models (safetensors format, no torch version issues)
    MODEL_IDS = {
        "ml": "openai/whisper-large-v3",             # Malayalam - use large for best results
        "ml-large": "openai/whisper-large-v3",       # Same as above
        "hi": "openai/whisper-large-v3",             # Hindi
        "ta": "openai/whisper-large-v3",             # Tamil
        "te": "openai/whisper-large-v3",             # Telugu
        "bn": "openai/whisper-large-v3",             # Bengali
        "kn": "openai/whisper-large-v3",             # Kannada
        "en": "openai/whisper-medium",               # English
        "default": "openai/whisper-large-v3",        # Large model as default
    }

    def __init__(
        self,
        language: str = "ml",
        device: str = "cpu",
    ):
        """
        Initialize IndicWhisper ASR.

        Args:
            language: Target language code (ml, hi, ta, te, ml-large, etc.)
            device: Device to run on - cuda or cpu
        """
        # Handle special case: ml-large uses large model but targets Malayalam
        if language == "ml-large":
            self.language = "ml"  # Target language is Malayalam
            self.model_id = self.MODEL_IDS["ml-large"]
        else:
            self.language = language
            self.model_id = self.MODEL_IDS.get(language, self.MODEL_IDS["default"])

        self.device = device
        self.model = None
        self.processor = None

    def load_model(self):
        """Load the fine-tuned Whisper model from HuggingFace."""
        try:
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
            import torch

            logger.info(f"Loading model: {self.model_id}")
            print(f"Loading Whisper model: {self.model_id}")
            print("(First run downloads the model, may take a few minutes...)")

            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            print(f"CUDA available: {cuda_available}")
            if cuda_available:
                print(f"GPU: {torch.cuda.get_device_name(0)}")

            # Determine device
            if self.device == "cuda" and cuda_available:
                device = "cuda:0"
                dtype = torch.float16
            else:
                device = "cpu"
                dtype = torch.float32

            # Load model and processor separately for better control
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            model.to(device)

            # Clear any default generation config that might override language
            model.generation_config.forced_decoder_ids = None
            model.generation_config.suppress_tokens = None

            # Create pipeline with explicit language setting
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=dtype,
                device=device,
            )

            print(f"Model loaded on {device}")
            print(f"Target language: {self.language} ({self.SUPPORTED_LANGUAGES.get(self.language, self.language)})")

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
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
            Dictionary with transcription results
        """
        if not hasattr(self, 'pipe') or self.pipe is None:
            self.load_model()

        target_lang = language or self.language

        try:
            import torch
            import soundfile as sf

            logger.info(f"Transcribing audio in {self.SUPPORTED_LANGUAGES.get(target_lang, target_lang)}")

            # Load audio
            if isinstance(audio, (str, Path)):
                audio_data, sr = sf.read(str(audio))
            else:
                audio_data = audio.flatten()
                sr = 16000

            # Resample to 16kHz if needed
            if sr != 16000:
                duration = len(audio_data) / sr
                target_length = int(duration * 16000)
                indices = np.linspace(0, len(audio_data) - 1, target_length).astype(int)
                audio_data = audio_data[indices]

            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)

            audio_data = audio_data.astype(np.float32)

            # Get the Whisper language code (full name)
            whisper_lang = self.WHISPER_LANG_CODES.get(target_lang, target_lang)
            print(f"[DEBUG] Forcing language: {whisper_lang}")

            # Process audio through feature extractor
            inputs = self.processor(
                audio_data,
                sampling_rate=16000,
                return_tensors="pt"
            )

            # Move to same device and dtype as model
            device = next(self.pipe.model.parameters()).device
            dtype = next(self.pipe.model.parameters()).dtype
            input_features = inputs.input_features.to(device=device, dtype=dtype)

            # Get language and task tokens
            tokenizer = self.processor.tokenizer

            # Force Malayalam output by setting decoder_input_ids
            # Format: <|startoftranscript|><|ml|><|transcribe|><|notimestamps|>
            lang_token = f"<|{whisper_lang}|>"

            decoder_input_ids = tokenizer.get_decoder_prompt_ids(
                language=whisper_lang,
                task="transcribe",
                no_timestamps=True,
            )

            print(f"[DEBUG] Language token: {lang_token}")
            print(f"[DEBUG] Decoder prompt IDs: {decoder_input_ids}")

            # Build decoder input IDs manually to force Malayalam
            # <|startoftranscript|> <|malayalam|> <|transcribe|> <|notimestamps|>
            sot_token_id = tokenizer.convert_tokens_to_ids("<|startoftranscript|>")
            lang_token_id = tokenizer.convert_tokens_to_ids(lang_token)
            transcribe_token_id = tokenizer.convert_tokens_to_ids("<|transcribe|>")
            notimestamps_token_id = tokenizer.convert_tokens_to_ids("<|notimestamps|>")

            decoder_input_ids = torch.tensor([[
                sot_token_id,
                lang_token_id,
                transcribe_token_id,
                notimestamps_token_id,
            ]]).to(device)

            print(f"[DEBUG] Decoder IDs: {decoder_input_ids.tolist()}")

            # Generate transcription with explicit decoder input
            with torch.no_grad():
                predicted_ids = self.pipe.model.generate(
                    input_features,
                    decoder_input_ids=decoder_input_ids,
                    max_new_tokens=256,
                    do_sample=False,
                )

            # Decode the output
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True
            )[0]

            return {
                "text": transcription.strip(),
                "language": target_lang,
                "language_name": self.SUPPORTED_LANGUAGES.get(target_lang, target_lang),
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise


# Quick test function
def test_indic_whisper(audio_path: str, language: str = "ml"):
    """Test IndicWhisper with an audio file."""
    asr = IndicWhisperASR(language=language)
    result = asr.transcribe(audio_path)
    print(f"Transcription: {result['text']}")
    print(f"Language: {result['language_name']}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_indic_whisper(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ml")
    else:
        print("Usage: python indic_asr.py <audio_file> [language_code]")
        print("Language codes: ml (Malayalam), hi (Hindi), ta (Tamil), te (Telugu)")
