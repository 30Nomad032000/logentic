"""
Voice Assistant Pipeline Orchestrator
Connects all components: ASR → Translation → LLM → Translation → TTS
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from the voice assistant pipeline."""
    # Input
    audio_input: Optional[str] = None

    # ASR Stage
    malayalam_text: str = ""
    asr_time_ms: float = 0

    # Translation ML→EN
    english_text: str = ""
    translation_ml_en_time_ms: float = 0

    # Intent Detection
    intent_type: str = ""
    intent_description: str = ""
    intent_confidence: float = 0
    intent_entities: dict = field(default_factory=dict)

    # LLM Response
    english_response: str = ""
    llm_time_ms: float = 0

    # Translation EN→ML
    malayalam_response: str = ""
    translation_en_ml_time_ms: float = 0

    # TTS Stage
    audio_output: Optional[Union[np.ndarray, str]] = None
    tts_time_ms: float = 0

    # Total
    total_time_ms: float = 0
    success: bool = True
    error: Optional[str] = None


class VoiceAssistantPipeline:
    """
    End-to-end voice assistant pipeline.

    Pipeline flow:
    Audio → ASR → Malayalam Text → Translate → English Text
         → Intent Detection → LLM → English Response
         → Translate → Malayalam Response → TTS → Audio
    """

    def __init__(
        self,
        asr_engine: str = "whisper",
        asr_model_size: str = "base",
        llm_model_size: str = "1.5b",
        tts_engine: str = "mms",
        device: str = "cuda",
        detect_intent: bool = True,
    ):
        """
        Initialize the pipeline.

        Args:
            asr_engine: ASR engine to use (whisper, meta_asr)
            asr_model_size: Size of ASR model
            llm_model_size: Size of Qwen model (0.5b, 1.5b, 3b, 7b)
            tts_engine: TTS engine to use (mms, cartesia)
            device: Device to run on (cuda, cpu)
            detect_intent: Whether to detect and show intent
        """
        self.asr_engine = asr_engine
        self.asr_model_size = asr_model_size
        self.llm_model_size = llm_model_size
        self.tts_engine = tts_engine
        self.device = device
        self.detect_intent = detect_intent

        # Components (lazy loaded)
        self._asr = None
        self._translator = None
        self._llm = None
        self._tts = None
        self._intent_detector = None

        logger.info(f"Pipeline initialized: ASR={asr_engine}, LLM=qwen-{llm_model_size}, TTS={tts_engine}")

    def load_components(self, show_progress: bool = True):
        """Load all pipeline components."""
        if show_progress:
            print("Loading pipeline components...")

        # Load ASR
        if show_progress:
            print("  [1/5] Loading ASR...")
        self._load_asr()

        # Load Translator
        if show_progress:
            print("  [2/5] Loading Translation models...")
        self._load_translator()

        # Load LLM
        if show_progress:
            print("  [3/5] Loading LLM...")
        self._load_llm()

        # Load TTS
        if show_progress:
            print("  [4/5] Loading TTS...")
        self._load_tts()

        # Load Intent Detector
        if self.detect_intent:
            if show_progress:
                print("  [5/5] Loading Intent Detector...")
            self._load_intent_detector()

        if show_progress:
            print("✓ All components loaded!")

    def _load_asr(self):
        """Load ASR component."""
        if self._asr is not None:
            return

        if self.asr_engine == "whisper":
            from ..asr import WhisperASR
            self._asr = WhisperASR(
                model_size=self.asr_model_size,
                device=self.device,
            )
            self._asr.load_model()
        else:
            raise ValueError(f"Unknown ASR engine: {self.asr_engine}")

    def _load_translator(self):
        """Load translation component."""
        if self._translator is not None:
            return

        from ..translation import IndicTranslator
        self._translator = IndicTranslator(device=self.device)
        # Pre-load both directions
        self._translator.load_models(["indic-en", "en-indic"])

    def _load_llm(self):
        """Load LLM component."""
        if self._llm is not None:
            return

        from ..llm import QwenLLM
        self._llm = QwenLLM(
            model_size=self.llm_model_size,
            device=self.device,
        )
        # Set voice assistant system prompt
        self._llm.set_system_prompt("""You are a helpful voice assistant that speaks Malayalam. You provide concise, friendly responses suitable for spoken conversation. Keep responses brief (1-3 sentences) and natural. Respond in English - your response will be translated to Malayalam.

You can help with:
- Answering questions
- Providing information
- Casual conversation
- Simple tasks

Be conversational and helpful.""")
        self._llm.load_model()

    def _load_tts(self):
        """Load TTS component."""
        if self._tts is not None:
            return

        from ..tts import TTSEngine
        self._tts = TTSEngine(backend=self.tts_engine, device=self.device)

    def _load_intent_detector(self):
        """Load intent detector."""
        if self._intent_detector is not None:
            return

        from .intent import IntentDetector
        self._intent_detector = IntentDetector(use_llm=False)  # Use keyword-based for speed

    def process(
        self,
        audio_path: Optional[str] = None,
        text_input: Optional[str] = None,
        input_language: str = "ml",
        output_audio_path: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process a voice query through the full pipeline.

        Args:
            audio_path: Path to input audio file (Malayalam speech)
            text_input: Direct text input (skips ASR)
            input_language: Input language code (ml, en)
            output_audio_path: Path to save output audio

        Returns:
            PipelineResult with all intermediate results
        """
        result = PipelineResult(audio_input=audio_path)
        total_start = time.perf_counter()

        try:
            # Stage 1: ASR (if audio provided)
            if audio_path:
                start = time.perf_counter()
                self._load_asr()
                asr_result = self._asr.transcribe(audio_path)
                result.malayalam_text = asr_result["text"]
                result.asr_time_ms = (time.perf_counter() - start) * 1000
                logger.info(f"ASR: {result.malayalam_text}")
            elif text_input:
                result.malayalam_text = text_input
                result.asr_time_ms = 0
            else:
                raise ValueError("Either audio_path or text_input must be provided")

            # Stage 2: Translate ML → EN (if input is Malayalam)
            if input_language == "ml":
                start = time.perf_counter()
                self._load_translator()
                result.english_text = self._translator.ml_to_en(result.malayalam_text)
                result.translation_ml_en_time_ms = (time.perf_counter() - start) * 1000
                logger.info(f"Translation ML→EN: {result.english_text}")
            else:
                result.english_text = result.malayalam_text
                result.translation_ml_en_time_ms = 0

            # Stage 3: Intent Detection
            if self.detect_intent and self._intent_detector:
                from .intent import IntentDetector
                if self._intent_detector is None:
                    self._intent_detector = IntentDetector(use_llm=False)

                intent = self._intent_detector.detect(
                    result.malayalam_text,
                    result.english_text
                )
                result.intent_type = intent.type.value
                result.intent_description = intent.description
                result.intent_confidence = intent.confidence
                result.intent_entities = intent.entities
                logger.info(f"Intent: {result.intent_type} - {result.intent_description}")

            # Stage 4: LLM Response
            start = time.perf_counter()
            self._load_llm()
            llm_response = self._llm.chat(result.english_text)
            result.english_response = llm_response.content
            result.llm_time_ms = (time.perf_counter() - start) * 1000
            logger.info(f"LLM Response: {result.english_response}")

            # Stage 5: Translate EN → ML
            start = time.perf_counter()
            self._load_translator()
            result.malayalam_response = self._translator.en_to_ml(result.english_response)
            result.translation_en_ml_time_ms = (time.perf_counter() - start) * 1000
            logger.info(f"Translation EN→ML: {result.malayalam_response}")

            # Stage 6: TTS
            start = time.perf_counter()
            self._load_tts()
            tts_result = self._tts.synthesize(
                text=result.malayalam_response,
                language="ml",
                output_path=output_audio_path,
            )
            result.audio_output = tts_result.audio
            result.tts_time_ms = (time.perf_counter() - start) * 1000
            logger.info(f"TTS complete")

            result.success = True

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result.success = False
            result.error = str(e)

        result.total_time_ms = (time.perf_counter() - total_start) * 1000
        return result

    def process_text(
        self,
        text: str,
        input_language: str = "ml",
        output_audio_path: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process text input (skip ASR).

        Args:
            text: Input text
            input_language: Language of input (ml or en)
            output_audio_path: Path to save output audio

        Returns:
            PipelineResult
        """
        return self.process(
            text_input=text,
            input_language=input_language,
            output_audio_path=output_audio_path,
        )

    def clear_conversation(self):
        """Clear LLM conversation history."""
        if self._llm:
            self._llm.clear_history()
            logger.info("Conversation history cleared")
