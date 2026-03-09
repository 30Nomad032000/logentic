"""
Agent Factory
Creates agent instances based on backend configuration.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agent orchestrator instances.

    Supports:
    - langgraph: LangGraph-based orchestrator (default)
    - clawgo: ClawGo/OpenClaw agent with BYOM support
    """

    @staticmethod
    def create(
        backend: str = "langgraph",
        config: Optional[Dict[str, Any]] = None,
        llm=None,
    ):
        """
        Create an agent instance.

        Args:
            backend: Agent backend - "langgraph" or "clawgo"
            config: Backend-specific configuration
            llm: Optional LLM instance for generating responses

        Returns:
            AgentOrchestrator or ClawGoAgent instance
        """
        config = config or {}

        if backend == "clawgo":
            from .clawgo_agent import ClawGoAgent
            agent = ClawGoAgent(
                gateway_url=config.get("gateway_url"),
                llm_provider=config.get("llm_provider", "ollama"),
                llm_model=config.get("llm_model", "qwen3:1.7b"),
                workspace_dir=config.get("workspace_dir"),
                config_path=config.get("config_path"),
            )
            agent.setup()
            return agent

        elif backend == "langgraph":
            from .orchestrator import AgentOrchestrator
            agent = AgentOrchestrator(config=config, llm=llm)
            agent.setup()
            return agent

        else:
            raise ValueError(f"Unknown agent backend: {backend}")
