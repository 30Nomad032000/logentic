"""
llama.cpp Backend for LLM Inference
Provides fast CPU/GPU inference using GGUF quantized models via llama-cpp-python.
"""

import logging
import os
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class LlamaCppBackend:
    """
    llama.cpp inference backend using llama-cpp-python.

    Loads GGUF quantized models for fast CPU inference on edge devices.
    Supports configurable quantization levels and threading.
    """

    # Default GGUF model repositories on HuggingFace
    GGUF_REPOS = {
        "qwen3-0.6b": "Qwen/Qwen3-0.6B-GGUF",
        "qwen3-1.7b": "Qwen/Qwen3-1.7B-GGUF",
        "qwen3-4b": "Qwen/Qwen3-4B-GGUF",
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        repo_id: Optional[str] = None,
        filename: Optional[str] = None,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
        quantization: str = "Q4_K_M",
        verbose: bool = False,
    ):
        """
        Initialize llama.cpp backend.

        Args:
            model_path: Direct path to a GGUF file (skips download)
            repo_id: HuggingFace repo ID for GGUF model
            filename: Specific GGUF filename in the repo
            n_ctx: Context window size
            n_threads: Number of CPU threads
            n_gpu_layers: Number of layers to offload to GPU (0 for CPU-only)
            quantization: Quantization level (Q4_K_M, Q5_K_M, Q8_0, etc.)
            verbose: Enable verbose llama.cpp output
        """
        self.model_path = model_path
        self.repo_id = repo_id
        self.filename = filename
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.quantization = quantization
        self.verbose = verbose
        self._model = None

    def _download_gguf(self) -> str:
        """Download GGUF model from HuggingFace Hub and return local path."""
        from huggingface_hub import hf_hub_download

        repo_id = self.repo_id
        filename = self.filename

        if not filename:
            # Construct filename from quantization level
            filename = f"*{self.quantization}*.gguf"

        logger.info(f"Downloading GGUF model: {repo_id}/{filename}")

        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
            )
            logger.info(f"GGUF model downloaded to: {local_path}")
            return local_path
        except Exception:
            # Try pattern matching if exact filename fails
            from huggingface_hub import HfApi
            api = HfApi()
            files = api.list_repo_files(repo_id)
            gguf_files = [f for f in files if f.endswith(".gguf")]
            quant_files = [f for f in gguf_files if self.quantization.lower() in f.lower()]

            if quant_files:
                filename = quant_files[0]
            elif gguf_files:
                filename = gguf_files[0]
                logger.warning(
                    f"Quantization '{self.quantization}' not found, using: {filename}"
                )
            else:
                raise FileNotFoundError(f"No GGUF files found in {repo_id}")

            local_path = hf_hub_download(repo_id=repo_id, filename=filename)
            logger.info(f"GGUF model downloaded to: {local_path}")
            return local_path

    def load(self):
        """Load the GGUF model into llama.cpp."""
        from llama_cpp import Llama

        # Resolve model path
        if self.model_path and Path(self.model_path).exists():
            path = self.model_path
        elif self.repo_id:
            path = self._download_gguf()
        else:
            raise ValueError("Either model_path or repo_id must be provided")

        logger.info(f"Loading GGUF model: {path}")
        logger.info(
            f"Config: n_ctx={self.n_ctx}, n_threads={self.n_threads}, "
            f"n_gpu_layers={self.n_gpu_layers}"
        )

        self._model = Llama(
            model_path=path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            verbose=self.verbose,
        )

        logger.info("GGUF model loaded successfully")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a raw prompt.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences

        Returns:
            Generated text
        """
        if self._model is None:
            self.load()

        result = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )

        return result["choices"][0]["text"]

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Chat completion with message history.

        Args:
            messages: List of {"role": ..., "content": ...} messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            tools: Optional tool definitions for function calling

        Returns:
            Chat completion result dict with 'choices' key
        """
        if self._model is None:
            self.load()

        kwargs = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        if tools:
            kwargs["tools"] = tools

        result = self._model.create_chat_completion(**kwargs)
        return result

    @property
    def loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
