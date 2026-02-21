"""
Pipecat Voice Pipeline
Production-grade STT → Translation → LLM → Translation → TTS pipeline
using Pipecat framework with built-in VAD, streaming, and WebSocket transport.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path
import numpy as np

from .pipecat_processors import (
    IndicSTTProcessor,
    IndicTranslationProcessor,
    IndicLLMProcessor,
    IndicTTSProcessor,
)

logger = logging.getLogger(__name__)


@dataclass
class PipecatPipelineResult:
    """Result from the Pipecat voice pipeline."""
    # Input
    audio_input: Optional[str] = None

    # ASR Stage
    transcribed_text: str = ""
    asr_time_ms: float = 0

    # Translation input→EN
    english_text: str = ""
    translation_to_en_time_ms: float = 0

    # LLM Response
    english_response: str = ""
    llm_time_ms: float = 0

    # Translation EN→output
    translated_response: str = ""
    translation_from_en_time_ms: float = 0

    # TTS Stage
    audio_output: Optional[Union[np.ndarray, str]] = None
    tts_time_ms: float = 0

    # Total
    total_time_ms: float = 0
    success: bool = True
    error: Optional[str] = None
    input_language: str = "ml"


class PipecatVoicePipeline:
    """
    Production-grade voice assistant pipeline using Pipecat framework.

    Pipeline: Audio → STT → Translation → LLM → Translation → TTS → Audio

    Features:
    - Built-in VAD (Voice Activity Detection)
    - Streaming support via WebSocket
    - Wraps existing backends (Pingala, Qwen3, Indic Parler-TTS, etc.)
    - Automatic component lifecycle management
    """

    def __init__(
        self,
        # ASR config
        asr_engine: str = "pingala",
        asr_device: str = "cpu",
        asr_kwargs: Optional[dict] = None,
        # Translation config
        translation_device: str = "cpu",
        translation_variant: str = "dist",
        # LLM config
        llm_engine: str = "qwen3",
        llm_model_size: str = "1.7b",
        llm_backend: str = "llamacpp",
        llm_device: str = "cpu",
        llm_kwargs: Optional[dict] = None,
        # TTS config
        tts_backend: str = "mms",
        tts_device: str = "cpu",
        tts_kwargs: Optional[dict] = None,
        # Pipeline config
        default_language: str = "ml",
    ):
        """
        Initialize the Pipecat voice pipeline.

        Args:
            asr_engine: ASR engine (pingala, whisper, indic_whisper)
            asr_device: Device for ASR
            asr_kwargs: Additional ASR config
            translation_device: Device for translation
            translation_variant: Translation model variant (full, dist)
            llm_engine: LLM engine (qwen, qwen3)
            llm_model_size: LLM model size
            llm_backend: LLM backend (llamacpp, transformers)
            llm_device: Device for LLM
            llm_kwargs: Additional LLM config
            tts_backend: TTS backend (mms, indic, chatterbox, cartesia)
            tts_device: Device for TTS
            tts_kwargs: Additional TTS config
            default_language: Default input/output language
        """
        self.default_language = default_language

        # Initialize processors
        self.stt = IndicSTTProcessor(
            engine=asr_engine,
            device=asr_device,
            **(asr_kwargs or {}),
        )
        self.translator = IndicTranslationProcessor(
            device=translation_device,
            model_variant=translation_variant,
        )
        self.llm = IndicLLMProcessor(
            engine=llm_engine,
            model_size=llm_model_size,
            backend=llm_backend,
            device=llm_device,
            **(llm_kwargs or {}),
        )
        self.tts = IndicTTSProcessor(
            backend=tts_backend,
            device=tts_device,
            **(tts_kwargs or {}),
        )

        self._pipecat_pipeline = None
        logger.info(
            f"PipecatVoicePipeline initialized: "
            f"ASR={asr_engine}, LLM={llm_engine}-{llm_model_size}, TTS={tts_backend}"
        )

    def setup_pipecat(self):
        """
        Setup the Pipecat pipeline framework with transport and services.

        This creates the actual Pipecat Pipeline with Daily/WebSocket transport.
        Call this for streaming mode. For simple request/response, use process() directly.
        """
        try:
            from pipecat.pipeline.pipeline import Pipeline
            from pipecat.pipeline.task import PipelineTask

            logger.info("Setting up Pipecat pipeline framework...")

            # Build pipeline chain: STT → Translate → LLM → Translate → TTS
            # In streaming mode, Pipecat manages the frame flow automatically
            self._pipecat_pipeline = Pipeline([
                self.stt,
                self.translator,
                self.llm,
                self.translator,
                self.tts,
            ])

            logger.info("Pipecat pipeline setup complete")

        except ImportError:
            logger.warning(
                "pipecat-ai not installed. Streaming mode unavailable. "
                "Using direct process() mode. Install with: pip install pipecat-ai"
            )

    async def process(
        self,
        audio_path: Optional[str] = None,
        text_input: Optional[str] = None,
        input_language: str = "ml",
        output_audio_path: Optional[str] = None,
    ) -> PipecatPipelineResult:
        """
        Process a voice query through the full pipeline.

        This is the direct (non-streaming) processing mode.
        For streaming, use setup_pipecat() and connect via WebSocket.

        Args:
            audio_path: Path to input audio file
            text_input: Direct text input (skips ASR)
            input_language: Input language code
            output_audio_path: Path to save output audio

        Returns:
            PipecatPipelineResult with all intermediate results
        """
        result = PipecatPipelineResult(
            audio_input=audio_path,
            input_language=input_language,
        )
        total_start = time.perf_counter()

        try:
            # Stage 1: ASR
            if audio_path:
                start = time.perf_counter()
                asr_result = await self.stt.process_audio(
                    audio_path, language=input_language
                )
                result.transcribed_text = asr_result["text"]
                result.asr_time_ms = (time.perf_counter() - start) * 1000
                logger.info(f"ASR: {result.transcribed_text}")
            elif text_input:
                result.transcribed_text = text_input
            else:
                raise ValueError("Either audio_path or text_input must be provided")

            # Stage 2: Translate to English (if not already English)
            if input_language != "en":
                start = time.perf_counter()
                result.english_text = await self.translator.translate(
                    result.transcribed_text, input_language, "en"
                )
                result.translation_to_en_time_ms = (time.perf_counter() - start) * 1000
            else:
                result.english_text = result.transcribed_text

            # Stage 3: LLM Response
            start = time.perf_counter()
            result.english_response = await self.llm.generate_response(
                result.english_text
            )
            result.llm_time_ms = (time.perf_counter() - start) * 1000

            # Stage 4: Translate back from English
            if input_language != "en":
                start = time.perf_counter()
                result.translated_response = await self.translator.translate(
                    result.english_response, "en", input_language
                )
                result.translation_from_en_time_ms = (
                    (time.perf_counter() - start) * 1000
                )
            else:
                result.translated_response = result.english_response

            # Stage 5: TTS
            start = time.perf_counter()
            tts_result = await self.tts.synthesize(
                text=result.translated_response,
                language=input_language,
                output_path=output_audio_path,
            )
            result.audio_output = tts_result.audio
            result.tts_time_ms = (time.perf_counter() - start) * 1000

            result.success = True

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result.success = False
            result.error = str(e)

        result.total_time_ms = (time.perf_counter() - total_start) * 1000
        return result

    async def process_text(
        self,
        text: str,
        input_language: str = "ml",
        output_audio_path: Optional[str] = None,
    ) -> PipecatPipelineResult:
        """
        Process text input (skip ASR).

        Args:
            text: Input text
            input_language: Language of input
            output_audio_path: Path to save output audio

        Returns:
            PipecatPipelineResult
        """
        return await self.process(
            text_input=text,
            input_language=input_language,
            output_audio_path=output_audio_path,
        )
