"""
Inference Engine Factory
Unified factory for creating inference backends across the pipeline.
"""

import logging
from typing import Literal, Optional, Dict

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Factory for creating inference backends.

    Supports:
    - onnx: ONNX Runtime for accelerated CPU/GPU inference (ASR, TTS)
    - llamacpp: llama.cpp for LLM inference via GGUF models
    - transformers: HuggingFace transformers (default fallback)
    """

    @staticmethod
    def create(
        backend: Literal["onnx", "llamacpp", "transformers"],
        **kwargs,
    ):
        """
        Create an inference backend instance.

        Args:
            backend: Backend type to create
            **kwargs: Backend-specific configuration

        Returns:
            Backend instance (ONNXInferenceBackend, LlamaCppBackend, or None for transformers)
        """
        if backend == "onnx":
            from .onnx_backend import ONNXInferenceBackend
            return ONNXInferenceBackend(**kwargs)

        elif backend == "llamacpp":
            from ..llm.llamacpp_backend import LlamaCppBackend
            return LlamaCppBackend(**kwargs)

        elif backend == "transformers":
            # Transformers doesn't need a separate backend wrapper
            # Components use transformers directly
            logger.info("Using transformers backend (no wrapper needed)")
            return None

        else:
            raise ValueError(f"Unknown inference backend: {backend}")

    @staticmethod
    def get_available_backends() -> list:
        """Return list of available backends based on installed packages."""
        available = ["transformers"]  # Always available

        try:
            import onnxruntime
            available.append("onnx")
        except ImportError:
            pass

        try:
            import llama_cpp
            available.append("llamacpp")
        except ImportError:
            pass

        return available
