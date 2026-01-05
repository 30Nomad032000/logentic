"""
Qwen 2.5 LLM Module
Local conversational AI using Qwen 2.5 Instruct models.
"""

import logging
from typing import Optional, List, Dict, Literal
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class ChatResponse:
    """Response from chat completion."""
    content: str
    tokens_used: int
    generation_time_ms: float


class QwenLLM:
    """
    Qwen 2.5 Instruct LLM for conversational AI.

    Sizes available:
    - 0.5B: ~1GB VRAM (good for Pi with quantization)
    - 1.5B: ~3GB VRAM (balanced)
    - 3B: ~6GB VRAM (better quality)
    - 7B: ~14GB VRAM (best local quality)
    """

    MODELS = {
        "0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
        "1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
        "3b": "Qwen/Qwen2.5-3B-Instruct",
        "7b": "Qwen/Qwen2.5-7B-Instruct",
    }

    DEFAULT_SYSTEM_PROMPT = """You are a helpful voice assistant. You provide concise, friendly responses suitable for spoken conversation. Keep responses brief and natural - typically 1-3 sentences unless more detail is needed. You can help with:
- Answering questions
- Providing information
- Casual conversation
- Task assistance

Respond naturally as if speaking to someone."""

    def __init__(
        self,
        model_size: str = "1.5b",
        device: str = "cuda",
        system_prompt: Optional[str] = None,
        max_memory_messages: int = 10,
    ):
        """
        Initialize Qwen LLM.

        Args:
            model_size: Model size - 0.5b, 1.5b, 3b, 7b
            device: Device to run on - cuda or cpu
            system_prompt: Custom system prompt
            max_memory_messages: Max conversation history to keep
        """
        self.model_size = model_size
        self.device = device
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.max_memory_messages = max_memory_messages

        self.model = None
        self.tokenizer = None
        self.conversation_history: List[Message] = []

    def load_model(self):
        """Load the Qwen model."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        model_id = self.MODELS.get(self.model_size)
        if not model_id:
            raise ValueError(f"Unknown model size: {self.model_size}. Options: {list(self.MODELS.keys())}")

        logger.info(f"Loading Qwen model: {model_id}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=True,
            )

            # Load with appropriate settings based on device
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
            logger.info(f"Qwen model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load Qwen model: {e}")
            raise

    def _build_messages(self, user_input: str) -> List[Dict]:
        """Build message list for the model."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        for msg in self.conversation_history[-self.max_memory_messages:]:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(
        self,
        user_input: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        remember: bool = True,
    ) -> ChatResponse:
        """
        Chat with the model.

        Args:
            user_input: User's message
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            remember: Whether to add to conversation history

        Returns:
            ChatResponse with generated text and metadata
        """
        import time
        import torch

        if self.model is None:
            self.load_model()

        messages = self._build_messages(user_input)

        logger.info(f"Generating response for: '{user_input[:50]}...'")

        try:
            start_time = time.perf_counter()

            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            inputs = self.tokenizer(text, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            input_length = inputs["input_ids"].shape[1]

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode only the new tokens
            new_tokens = outputs[0][input_length:]
            response_text = self.tokenizer.decode(
                new_tokens,
                skip_special_tokens=True,
            ).strip()

            generation_time = (time.perf_counter() - start_time) * 1000
            tokens_generated = len(new_tokens)

            # Update conversation history
            if remember:
                self.conversation_history.append(Message(role="user", content=user_input))
                self.conversation_history.append(Message(role="assistant", content=response_text))

                # Trim history if too long
                if len(self.conversation_history) > self.max_memory_messages * 2:
                    self.conversation_history = self.conversation_history[-self.max_memory_messages * 2:]

            logger.info(f"Generated {tokens_generated} tokens in {generation_time:.1f}ms")

            return ChatResponse(
                content=response_text,
                tokens_used=tokens_generated,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

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
        import torch

        if self.model is None:
            self.load_model()

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


# Singleton instance
_llm = None


def get_llm(model_size: str = "1.5b", device: str = "cuda") -> QwenLLM:
    """Get or create singleton LLM instance."""
    global _llm
    if _llm is None:
        _llm = QwenLLM(model_size=model_size, device=device)
    return _llm


def chat(user_input: str, **kwargs) -> str:
    """Quick chat function."""
    llm = get_llm()
    response = llm.chat(user_input, **kwargs)
    return response.content


def generate(prompt: str, **kwargs) -> str:
    """Quick generation function."""
    llm = get_llm()
    return llm.generate(prompt, **kwargs)
