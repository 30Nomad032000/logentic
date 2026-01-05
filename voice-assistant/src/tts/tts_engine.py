"""
Unified TTS Engine
Supports multiple backends with A/B testing capability.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Union, Literal
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    """Result from TTS synthesis."""
    audio: Union[np.ndarray, str]
    backend: str
    language: str
    duration_ms: float
    sample_rate: int
    text: str


class TTSEngine:
    """
    Unified TTS engine supporting multiple backends.

    Backends:
    - mms: Meta MMS-TTS (offline, ~300MB)
    - cartesia: Cartesia API (online, high quality)
    - indic: AI4Bharat Indic TTS (offline, larger)

    Usage:
        engine = TTSEngine(backend="mms")
        result = engine.synthesize("നമസ്കാരം", language="ml")

        # A/B Testing
        results = engine.compare("Hello world", backends=["mms", "cartesia"])
    """

    BACKENDS = ["mms", "cartesia", "indic"]

    def __init__(
        self,
        backend: Literal["mms", "cartesia", "indic"] = "mms",
        device: str = "cuda",
        **kwargs,
    ):
        """
        Initialize TTS Engine.

        Args:
            backend: TTS backend to use
            device: Device for local models (cuda/cpu)
            **kwargs: Backend-specific arguments
        """
        self.default_backend = backend
        self.device = device
        self.kwargs = kwargs
        self._engines = {}

    def _get_engine(self, backend: str):
        """Lazy load and cache TTS engines."""
        if backend not in self._engines:
            if backend == "mms":
                from .mms_tts import MMSTTS
                self._engines[backend] = MMSTTS(device=self.device)

            elif backend == "cartesia":
                from .cartesia_tts import CartesiaTTS
                self._engines[backend] = CartesiaTTS(**self.kwargs)

            elif backend == "indic":
                from .indic_tts import IndicTTS
                self._engines[backend] = IndicTTS(device=self.device)

            else:
                raise ValueError(f"Unknown backend: {backend}")

        return self._engines[backend]

    def synthesize(
        self,
        text: str,
        language: str = "ml",
        backend: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> TTSResult:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code
            backend: Override default backend
            output_path: Optional path to save audio
            **kwargs: Backend-specific arguments

        Returns:
            TTSResult with audio and metadata
        """
        backend = backend or self.default_backend
        engine = self._get_engine(backend)

        start_time = time.perf_counter()

        try:
            audio = engine.synthesize(
                text=text,
                language=language,
                output_path=output_path,
                **kwargs,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000

            sample_rate = getattr(engine, 'sample_rate', 22050)

            return TTSResult(
                audio=audio,
                backend=backend,
                language=language,
                duration_ms=duration_ms,
                sample_rate=sample_rate,
                text=text,
            )

        except Exception as e:
            logger.error(f"TTS synthesis failed ({backend}): {e}")
            raise

    def compare(
        self,
        text: str,
        language: str = "ml",
        backends: Optional[list] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> dict[str, TTSResult]:
        """
        Compare multiple TTS backends for A/B testing.

        Args:
            text: Text to synthesize
            language: Language code
            backends: List of backends to compare (default: all available)
            output_dir: Directory to save audio files

        Returns:
            Dictionary mapping backend name to TTSResult
        """
        backends = backends or self.BACKENDS
        results = {}

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        for backend in backends:
            try:
                output_path = None
                if output_dir:
                    output_path = output_dir / f"{backend}_{language}.wav"

                result = self.synthesize(
                    text=text,
                    language=language,
                    backend=backend,
                    output_path=output_path,
                )
                results[backend] = result

                logger.info(
                    f"[{backend}] Synthesized in {result.duration_ms:.1f}ms"
                )

            except Exception as e:
                logger.warning(f"[{backend}] Failed: {e}")
                results[backend] = None

        return results

    def benchmark(
        self,
        texts: list[str],
        language: str = "ml",
        backends: Optional[list] = None,
        iterations: int = 3,
    ) -> dict:
        """
        Benchmark TTS backends.

        Args:
            texts: List of texts to synthesize
            language: Language code
            backends: Backends to benchmark
            iterations: Number of iterations per text

        Returns:
            Benchmark results with timing statistics
        """
        backends = backends or self.BACKENDS
        results = {b: {"times": [], "errors": 0} for b in backends}

        for backend in backends:
            engine = None
            try:
                engine = self._get_engine(backend)
            except Exception as e:
                logger.warning(f"Cannot load {backend}: {e}")
                continue

            for text in texts:
                for _ in range(iterations):
                    try:
                        start = time.perf_counter()
                        engine.synthesize(text, language=language)
                        elapsed = (time.perf_counter() - start) * 1000
                        results[backend]["times"].append(elapsed)
                    except Exception:
                        results[backend]["errors"] += 1

        # Calculate statistics
        for backend, data in results.items():
            times = data["times"]
            if times:
                data["mean_ms"] = np.mean(times)
                data["std_ms"] = np.std(times)
                data["min_ms"] = np.min(times)
                data["max_ms"] = np.max(times)
            else:
                data["mean_ms"] = None

        return results


# Quick access functions
def tts(
    text: str,
    language: str = "ml",
    backend: str = "mms",
    output_path: Optional[str] = None,
) -> TTSResult:
    """Quick TTS synthesis."""
    engine = TTSEngine(backend=backend)
    return engine.synthesize(text, language=language, output_path=output_path)


def compare_tts(
    text: str,
    language: str = "ml",
    output_dir: str = "./tts_comparison",
) -> dict:
    """Quick A/B comparison."""
    engine = TTSEngine()
    return engine.compare(text, language=language, output_dir=output_dir)
