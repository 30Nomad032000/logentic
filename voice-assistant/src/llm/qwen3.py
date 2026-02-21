"""
Qwen3 LLM Module
Local conversational AI using Qwen3 Instruct models with llama.cpp or transformers backend.
"""

import logging
import time
from typing import Optional, List, Dict, Literal

from .qwen import Message, ChatResponse

logger = logging.getLogger(__name__)


class Qwen3LLM:
    """
    Qwen3 Instruct LLM with dual backend support.

    Backends:
    - llamacpp (default): Fast CPU inference via GGUF quantized models
    - transformers: Standard HuggingFace transformers (GPU recommended)

    Sizes available:
    - 0.6B: ~400MB GGUF Q4 (excellent for Pi)
    - 1.7B: ~1GB GGUF Q4 (balanced)
    - 4B: ~2.5GB GGUF Q4 (better quality)
    """

    MODELS_TRANSFORMERS = {
        "0.6b": "Qwen/Qwen3-0.6B",
        "1.7b": "Qwen/Qwen3-1.7B",
        "4b": "Qwen/Qwen3-4B",
    }

    MODELS_GGUF = {
        "0.6b": {"repo_id": "Qwen/Qwen3-0.6B-GGUF", "filename": None},
        "1.7b": {"repo_id": "Qwen/Qwen3-1.7B-GGUF", "filename": None},
        "4b": {"repo_id": "Qwen/Qwen3-4B-GGUF", "filename": None},
    }

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful voice assistant. You provide concise, friendly responses "
        "suitable for spoken conversation. Keep responses brief and natural - typically "
        "1-3 sentences unless more detail is needed. You can help with answering questions, "
        "providing information, casual conversation, and task assistance. "
        "Respond naturally as if speaking to someone."
    )

    def __init__(
        self,
        model_size: str = "1.7b",
        backend: Literal["llamacpp", "transformers"] = "llamacpp",
        device: str = "cpu",
        system_prompt: Optional[str] = None,
        max_memory_messages: int = 10,
        # llama.cpp specific
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
        quantization: str = "Q4_K_M",
    ):
        """
        Initialize Qwen3 LLM.

        Args:
            model_size: Model size - 0.6b, 1.7b, 4b
            backend: Inference backend - llamacpp (default) or transformers
            device: Device to run on - cpu or cuda (transformers only)
            system_prompt: Custom system prompt
            max_memory_messages: Max conversation history to keep
            n_ctx: Context window size (llamacpp)
            n_threads: CPU threads (llamacpp)
            n_gpu_layers: GPU layer offload count (llamacpp)
            quantization: GGUF quantization level (llamacpp)
        """
        self.model_size = model_size
        self.backend_type = backend
        self.device = device
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.max_memory_messages = max_memory_messages

        # llama.cpp config
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.quantization = quantization

        self._backend = None
        self.model = None
        self.tokenizer = None
        self.conversation_history: List[Message] = []

    def load_model(self):
        """Load the Qwen3 model using the configured backend."""
        if self.backend_type == "llamacpp":
            self._load_llamacpp()
        else:
            self._load_transformers()

    def _load_llamacpp(self):
        """Load model via llama.cpp backend."""
        from .llamacpp_backend import LlamaCppBackend

        gguf_config = self.MODELS_GGUF.get(self.model_size)
        if not gguf_config:
            raise ValueError(
                f"Unknown model size: {self.model_size}. "
                f"Options: {list(self.MODELS_GGUF.keys())}"
            )

        self._backend = LlamaCppBackend(
            repo_id=gguf_config["repo_id"],
            filename=gguf_config["filename"],
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            quantization=self.quantization,
        )
        self._backend.load()
        logger.info(f"Qwen3 {self.model_size} loaded via llama.cpp")

    def _load_transformers(self):
        """Load model via HuggingFace transformers."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        model_id = self.MODELS_TRANSFORMERS.get(self.model_size)
        if not model_id:
            raise ValueError(
                f"Unknown model size: {self.model_size}. "
                f"Options: {list(self.MODELS_TRANSFORMERS.keys())}"
            )

        logger.info(f"Loading Qwen3 model: {model_id}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, trust_remote_code=True
        )

        if self.device == "cuda" and torch.cuda.is_available():
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                trust_remote_code=True,
            )
            self.model = self.model.to("cpu")
            self.device = "cpu"

        self.model.eval()
        logger.info(f"Qwen3 model loaded via transformers on {self.device}")

    def _build_messages(self, user_input: str) -> List[Dict]:
        """Build message list for the model."""
        messages = [{"role": "system", "content": self.system_prompt}]

        for msg in self.conversation_history[-self.max_memory_messages:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_input})
        return messages

    def chat(
        self,
        user_input: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        remember: bool = True,
        tools: Optional[List[Dict]] = None,
    ) -> ChatResponse:
        """
        Chat with the model.

        Args:
            user_input: User's message
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            remember: Whether to add to conversation history
            tools: Optional tool definitions for function calling (Qwen3 native)

        Returns:
            ChatResponse with generated text and metadata
        """
        if self._backend is None and self.model is None:
            self.load_model()

        messages = self._build_messages(user_input)
        start_time = time.perf_counter()

        if self.backend_type == "llamacpp":
            response_text, tokens_generated = self._chat_llamacpp(
                messages, max_new_tokens, temperature, top_p, tools
            )
        else:
            response_text, tokens_generated = self._chat_transformers(
                messages, max_new_tokens, temperature, top_p
            )

        generation_time = (time.perf_counter() - start_time) * 1000

        if remember:
            self.conversation_history.append(
                Message(role="user", content=user_input)
            )
            self.conversation_history.append(
                Message(role="assistant", content=response_text)
            )
            if len(self.conversation_history) > self.max_memory_messages * 2:
                self.conversation_history = self.conversation_history[
                    -self.max_memory_messages * 2:
                ]

        logger.info(
            f"Generated {tokens_generated} tokens in {generation_time:.1f}ms"
        )

        return ChatResponse(
            content=response_text,
            tokens_used=tokens_generated,
            generation_time_ms=generation_time,
        )

    def _chat_llamacpp(
        self,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        top_p: float,
        tools: Optional[List[Dict]] = None,
    ) -> tuple:
        """Chat using llama.cpp backend. Returns (text, token_count)."""
        result = self._backend.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
        )

        choice = result["choices"][0]
        content = choice["message"]["content"] or ""
        tokens = result.get("usage", {}).get("completion_tokens", 0)
        return content.strip(), tokens

    def _chat_transformers(
        self,
        messages: List[Dict],
        max_new_tokens: int,
        temperature: float,
        top_p: float,
    ) -> tuple:
        """Chat using transformers backend. Returns (text, token_count)."""
        import torch

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        input_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][input_length:]
        response_text = self.tokenizer.decode(
            new_tokens, skip_special_tokens=True
        ).strip()

        return response_text, len(new_tokens)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        """
        Simple text generation without chat formatting.

        Args:
            prompt: Raw prompt text
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if self._backend is None and self.model is None:
            self.load_model()

        if self.backend_type == "llamacpp":
            return self._backend.generate(
                prompt, max_tokens=max_new_tokens, temperature=temperature
            )
        else:
            import torch

            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def set_system_prompt(self, prompt: str):
        """Update the system prompt."""
        self.system_prompt = prompt
        logger.info("System prompt updated")
