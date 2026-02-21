"""
Pipecat Custom Processors
Wraps existing voice assistant backends as Pipecat-compatible services.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IndicSTTProcessor:
    """
    Pipecat STT processor wrapping PingalaASR or WhisperASR.

    Converts audio frames to text transcription frames.
    """

    def __init__(self, engine: str = "pingala", device: str = "cpu", **kwargs):
        """
        Initialize STT processor.

        Args:
            engine: ASR engine - "pingala", "whisper", or "indic_whisper"
            device: Device for inference
            **kwargs: Engine-specific arguments
        """
        self.engine_name = engine
        self.device = device
        self.kwargs = kwargs
        self._engine = None

    def _load_engine(self):
        """Lazy load the ASR engine."""
        if self._engine is not None:
            return

        if self.engine_name == "pingala":
            from ..asr import PingalaASR
            self._engine = PingalaASR(device=self.device)
        elif self.engine_name == "whisper":
            from ..asr import WhisperASR
            model_size = self.kwargs.get("model_size", "base")
            self._engine = WhisperASR(model_size=model_size, device=self.device)
        elif self.engine_name == "indic_whisper":
            from ..asr import IndicWhisperASR
            self._engine = IndicWhisperASR(device=self.device)
        else:
            raise ValueError(f"Unknown ASR engine: {self.engine_name}")

        self._engine.load_model()

    async def process_audio(self, audio_data, language: Optional[str] = None) -> dict:
        """
        Process audio data through ASR.

        Args:
            audio_data: Audio numpy array or file path
            language: Optional language hint

        Returns:
            Transcription result dict
        """
        self._load_engine()
        return self._engine.transcribe(audio_data, language=language)


class IndicTranslationProcessor:
    """
    Pipecat translation processor wrapping IndicTranslator.

    Translates text frames between languages.
    """

    def __init__(
        self,
        device: str = "cpu",
        model_variant: str = "dist",
    ):
        """
        Initialize translation processor.

        Args:
            device: Device for inference
            model_variant: "full" or "dist"
        """
        self.device = device
        self.model_variant = model_variant
        self._translator = None

    def _load_translator(self):
        """Lazy load the translator."""
        if self._translator is not None:
            return

        from ..translation import IndicTranslator
        self._translator = IndicTranslator(
            device=self.device,
            model_variant=self.model_variant,
        )

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Translate text between languages.

        Args:
            text: Input text
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        self._load_translator()
        return self._translator.translate(text, source_lang, target_lang)


class IndicLLMProcessor:
    """
    Pipecat LLM processor wrapping Qwen3LLM or QwenLLM.

    Generates response text from user input.
    """

    def __init__(
        self,
        engine: str = "qwen3",
        model_size: str = "1.7b",
        backend: str = "llamacpp",
        device: str = "cpu",
        **kwargs,
    ):
        """
        Initialize LLM processor.

        Args:
            engine: LLM engine - "qwen" or "qwen3"
            model_size: Model size
            backend: Backend for qwen3 - "llamacpp" or "transformers"
            device: Device for inference
            **kwargs: Engine-specific arguments
        """
        self.engine_name = engine
        self.model_size = model_size
        self.backend = backend
        self.device = device
        self.kwargs = kwargs
        self._llm = None

    def _load_llm(self):
        """Lazy load the LLM."""
        if self._llm is not None:
            return

        if self.engine_name == "qwen3":
            from ..llm import Qwen3LLM
            self._llm = Qwen3LLM(
                model_size=self.model_size,
                backend=self.backend,
                device=self.device,
                **self.kwargs,
            )
        else:
            from ..llm import QwenLLM
            self._llm = QwenLLM(
                model_size=self.model_size,
                device=self.device,
            )

        self._llm.load_model()

    async def generate_response(self, user_input: str) -> str:
        """
        Generate a response to user input.

        Args:
            user_input: User's message text

        Returns:
            Generated response text
        """
        self._load_llm()
        response = self._llm.chat(user_input)
        return response.content


class IndicTTSProcessor:
    """
    Pipecat TTS processor wrapping TTSEngine.

    Converts text frames to audio output.
    """

    def __init__(
        self,
        backend: str = "mms",
        device: str = "cpu",
        **kwargs,
    ):
        """
        Initialize TTS processor.

        Args:
            backend: TTS backend - "mms", "indic", "chatterbox", "cartesia"
            device: Device for inference
            **kwargs: Backend-specific arguments
        """
        self.backend = backend
        self.device = device
        self.kwargs = kwargs
        self._engine = None

    def _load_engine(self):
        """Lazy load the TTS engine."""
        if self._engine is not None:
            return

        from ..tts import TTSEngine
        self._engine = TTSEngine(
            backend=self.backend,
            device=self.device,
            **self.kwargs,
        )

    async def synthesize(
        self,
        text: str,
        language: str = "ml",
        output_path: Optional[str] = None,
    ):
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code
            output_path: Optional output file path

        Returns:
            TTSResult with audio data
        """
        self._load_engine()
        return self._engine.synthesize(
            text=text,
            language=language,
            output_path=output_path,
        )
