"""
ClawGo Agent Integration
Bridge between the voice assistant pipeline and ClawGo (OpenClaw Pi node).
ClawGo handles voice I/O natively with LLM processing via gateway.
"""

import logging
import subprocess
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ClawGoAgent:
    """
    ClawGo (OpenClaw) agent for Raspberry Pi voice assistant.

    ClawGo is a Go-based headless node that connects to an OpenClaw gateway.
    It handles voice input (mic → STT) and voice output (TTS → speaker) natively,
    with LLM processing happening via the gateway.

    Supports BYOM (Bring Your Own Model) via Ollama for local Qwen3 inference.
    """

    DEFAULT_GATEWAY_URL = "http://localhost:11434"  # Ollama default
    DEFAULT_BINARY_NAME = "clawgo"

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        binary_path: Optional[str] = None,
        workspace_dir: Optional[str] = None,
        llm_provider: str = "ollama",
        llm_model: str = "qwen3:1.7b",
        config_path: Optional[str] = None,
    ):
        """
        Initialize ClawGo agent.

        Args:
            gateway_url: URL of the OpenClaw gateway / Ollama endpoint
            binary_path: Path to ClawGo binary (auto-detected if not set)
            workspace_dir: Path to ClawGo workspace directory
            llm_provider: LLM provider - "ollama" for local, "openai" for cloud
            llm_model: Model name for the provider
            config_path: Path to ClawGo config JSON
        """
        self.gateway_url = gateway_url or self.DEFAULT_GATEWAY_URL
        self.binary_path = binary_path
        self.workspace_dir = workspace_dir or str(
            Path(__file__).parent.parent.parent / "config" / "clawgo"
        )
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.config_path = config_path

        self._process = None
        self._ollama_client = None

    def setup(self):
        """
        Setup ClawGo agent and verify dependencies.

        Checks for:
        1. ClawGo binary availability
        2. Ollama running (if using local LLM)
        3. Gateway connectivity
        """
        logger.info("Setting up ClawGo agent...")

        # Verify workspace directory
        workspace = Path(self.workspace_dir)
        if not workspace.exists():
            logger.warning(f"Workspace not found at {workspace}, creating...")
            workspace.mkdir(parents=True, exist_ok=True)

        # Setup Ollama client if using local LLM
        if self.llm_provider == "ollama":
            self._setup_ollama()

        logger.info("ClawGo agent setup complete")

    def _setup_ollama(self):
        """Initialize Ollama client for local LLM inference."""
        try:
            import ollama
            self._ollama_client = ollama.Client(host=self.gateway_url)

            # Verify Ollama is running and model is available
            try:
                models = self._ollama_client.list()
                model_names = [m.get("name", "") for m in models.get("models", [])]
                if self.llm_model not in model_names:
                    logger.warning(
                        f"Model '{self.llm_model}' not found in Ollama. "
                        f"Available: {model_names}. "
                        f"Pull with: ollama pull {self.llm_model}"
                    )
            except Exception as e:
                logger.warning(f"Could not connect to Ollama at {self.gateway_url}: {e}")

        except ImportError:
            logger.warning("ollama package not installed. Install with: pip install ollama")

    def process(
        self,
        user_input: str,
        language: str = "en",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process user input through ClawGo/Ollama.

        Args:
            user_input: User's text input (already transcribed)
            language: Language code
            context: Optional context dictionary

        Returns:
            Response dictionary with 'response', 'intent', 'language' keys
        """
        if self.llm_provider == "ollama" and self._ollama_client:
            return self._process_via_ollama(user_input, language, context)
        else:
            return self._process_fallback(user_input, language)

    def _process_via_ollama(
        self,
        user_input: str,
        language: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Process through Ollama (local Qwen3)."""
        try:
            # Load SOUL.md for personality if available
            soul_path = Path(self.workspace_dir) / "SOUL.md"
            system_prompt = ""
            if soul_path.exists():
                system_prompt = soul_path.read_text(encoding="utf-8")
            else:
                system_prompt = (
                    "You are a multilingual voice assistant for Indian languages. "
                    "Provide concise, helpful responses suitable for spoken conversation. "
                    "Keep responses brief (1-3 sentences)."
                )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]

            response = self._ollama_client.chat(
                model=self.llm_model,
                messages=messages,
            )

            return {
                "response": response["message"]["content"],
                "intent": "clawgo_chat",
                "language": language,
                "provider": "ollama",
                "model": self.llm_model,
            }

        except Exception as e:
            logger.error(f"Ollama processing failed: {e}")
            return {
                "response": f"Error processing request: {e}",
                "intent": "error",
                "language": language,
            }

    def _process_fallback(
        self,
        user_input: str,
        language: str,
    ) -> Dict[str, Any]:
        """Fallback processing without Ollama."""
        return {
            "response": f"[ClawGo] Received: {user_input}",
            "intent": "clawgo_fallback",
            "language": language,
        }

    def start_voice_listener(self):
        """
        Start ClawGo voice listener subprocess.

        Launches the ClawGo binary which handles mic input and speaker output.
        """
        if self._process is not None:
            logger.warning("ClawGo voice listener already running")
            return

        binary = self.binary_path or self.DEFAULT_BINARY_NAME

        try:
            cmd = [binary, "--gateway", self.gateway_url]
            if self.config_path:
                cmd.extend(["--config", self.config_path])

            logger.info(f"Starting ClawGo voice listener: {' '.join(cmd)}")
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"ClawGo started (PID: {self._process.pid})")

        except FileNotFoundError:
            logger.error(
                f"ClawGo binary not found: {binary}. "
                f"Run scripts/setup_clawgo.sh to install."
            )
        except Exception as e:
            logger.error(f"Failed to start ClawGo: {e}")

    def stop(self):
        """Stop ClawGo subprocess."""
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            logger.info("ClawGo stopped")
            self._process = None
