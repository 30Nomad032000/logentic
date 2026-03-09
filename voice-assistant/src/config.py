"""
Typed Configuration Module
Loads settings.yaml into typed dataclasses for type-safe configuration access.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"


@dataclass
class ASRConfig:
    """ASR configuration."""
    engine: str = "pingala"  # pingala, whisper, indic_whisper
    device: str = "cpu"
    language: Optional[str] = None

    # Whisper-specific
    whisper_model_size: str = "base"

    # Pingala-specific
    pingala_model_id: Optional[str] = None


@dataclass
class LLMConfig:
    """LLM configuration."""
    engine: str = "qwen3"  # qwen, qwen3
    model_size: str = "1.7b"
    device: str = "cpu"
    backend: str = "llamacpp"  # llamacpp, transformers
    max_new_tokens: int = 256
    temperature: float = 0.7
    max_memory_messages: int = 10

    # llama.cpp specific
    llamacpp_n_ctx: int = 2048
    llamacpp_n_threads: int = 4
    llamacpp_n_gpu_layers: int = 0
    llamacpp_quantization: str = "Q4_K_M"


@dataclass
class TTSConfig:
    """TTS configuration."""
    engine: str = "mms"  # mms, cartesia, indic, chatterbox
    device: str = "cpu"
    default_language: str = "ml"

    # Indic Parler-TTS specific
    indic_variant: str = "mini"  # full, mini

    # Cartesia specific
    cartesia_api_key: Optional[str] = None
    cartesia_model_id: str = "sonic-2"
    cartesia_voice_id: Optional[str] = None


@dataclass
class TranslationConfig:
    """Translation configuration."""
    engine: str = "indictrans2"
    device: str = "cpu"
    model_variant: str = "dist"  # full, dist
    source_lang: str = "ml"
    target_lang: str = "en"
    enable_m2m: bool = False  # Enable direct Indic-to-Indic


@dataclass
class AgentConfig:
    """Agent configuration."""
    orchestrator: str = "langgraph"  # langgraph, clawgo

    # ClawGo specific
    clawgo_gateway_url: str = "http://localhost:11434"
    clawgo_llm_provider: str = "ollama"
    clawgo_llm_model: str = "qwen3:1.7b"
    clawgo_workspace_dir: Optional[str] = None


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    mode: str = "pipecat"  # pipecat, legacy
    default_language: str = "ml"


@dataclass
class InferenceConfig:
    """Inference engine configuration."""
    asr_backend: str = "transformers"  # transformers, onnx
    tts_backend: str = "transformers"  # transformers, onnx
    llm_backend: str = "llamacpp"  # llamacpp, transformers


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class AppConfig:
    """Top-level application configuration."""
    name: str = "Hyper-Localized Voice Assistant"
    version: str = "0.2.0"
    debug: bool = True

    asr: ASRConfig = field(default_factory=ASRConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


def load_config(path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from YAML file into typed AppConfig.

    Args:
        path: Path to settings.yaml (uses default if not specified)

    Returns:
        Typed AppConfig instance
    """
    import yaml

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return AppConfig()

    logger.info(f"Loading config from: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config = AppConfig()

    # App level
    app_cfg = raw.get("app", {})
    config.name = app_cfg.get("name", config.name)
    config.version = app_cfg.get("version", config.version)
    config.debug = app_cfg.get("debug", config.debug)

    # ASR
    asr_cfg = raw.get("asr", {})
    config.asr.engine = asr_cfg.get("engine", config.asr.engine)
    config.asr.device = asr_cfg.get("device", config.asr.device)
    config.asr.language = asr_cfg.get("language")
    whisper_cfg = asr_cfg.get("whisper", {})
    config.asr.whisper_model_size = whisper_cfg.get("model_size", config.asr.whisper_model_size)
    pingala_cfg = asr_cfg.get("pingala", {})
    config.asr.pingala_model_id = pingala_cfg.get("model_id")
    mms_cfg = asr_cfg.get("mms", {})
    # Only apply device from the active engine's section
    if config.asr.engine == "mms" and mms_cfg.get("device"):
        config.asr.device = mms_cfg["device"]
    elif config.asr.engine == "whisper" and whisper_cfg.get("device"):
        config.asr.device = whisper_cfg["device"]
    elif config.asr.engine == "pingala" and pingala_cfg.get("device"):
        config.asr.device = pingala_cfg["device"]

    # LLM
    llm_cfg = raw.get("llm", {})
    config.llm.engine = llm_cfg.get("engine", config.llm.engine)
    config.llm.model_size = llm_cfg.get("model_size", config.llm.model_size)
    config.llm.device = llm_cfg.get("device", config.llm.device)
    config.llm.backend = llm_cfg.get("backend", config.llm.backend)
    config.llm.max_new_tokens = llm_cfg.get("max_new_tokens", config.llm.max_new_tokens)
    config.llm.temperature = llm_cfg.get("temperature", config.llm.temperature)
    config.llm.max_memory_messages = llm_cfg.get("max_memory_messages", config.llm.max_memory_messages)
    llamacpp_cfg = llm_cfg.get("llamacpp", {})
    config.llm.llamacpp_n_ctx = llamacpp_cfg.get("n_ctx", config.llm.llamacpp_n_ctx)
    config.llm.llamacpp_n_threads = llamacpp_cfg.get("n_threads", config.llm.llamacpp_n_threads)
    config.llm.llamacpp_n_gpu_layers = llamacpp_cfg.get("n_gpu_layers", config.llm.llamacpp_n_gpu_layers)
    config.llm.llamacpp_quantization = llamacpp_cfg.get("quantization", config.llm.llamacpp_quantization)

    # TTS
    tts_cfg = raw.get("tts", {})
    config.tts.engine = tts_cfg.get("engine", config.tts.engine)
    config.tts.default_language = tts_cfg.get("default_language", config.tts.default_language)
    config.tts.device = tts_cfg.get("device", config.tts.device)
    indic_cfg = tts_cfg.get("indic", {})
    config.tts.indic_variant = indic_cfg.get("variant", config.tts.indic_variant)
    cartesia_cfg = tts_cfg.get("cartesia", {})
    config.tts.cartesia_api_key = cartesia_cfg.get("api_key")
    config.tts.cartesia_model_id = cartesia_cfg.get("model_id", config.tts.cartesia_model_id)
    config.tts.cartesia_voice_id = cartesia_cfg.get("voice_id")

    # Translation
    trans_cfg = raw.get("translation", {})
    config.translation.engine = trans_cfg.get("engine", config.translation.engine)
    config.translation.device = trans_cfg.get("device", config.translation.device)
    config.translation.model_variant = trans_cfg.get("model_variant", config.translation.model_variant)
    config.translation.source_lang = trans_cfg.get("source_lang", config.translation.source_lang)
    config.translation.target_lang = trans_cfg.get("target_lang", config.translation.target_lang)
    config.translation.enable_m2m = trans_cfg.get("enable_m2m", config.translation.enable_m2m)

    # Agents
    agents_cfg = raw.get("agents", {})
    config.agents.orchestrator = agents_cfg.get("orchestrator", config.agents.orchestrator)
    clawgo_cfg = agents_cfg.get("clawgo", {})
    config.agents.clawgo_gateway_url = clawgo_cfg.get("gateway_url", config.agents.clawgo_gateway_url)
    config.agents.clawgo_llm_provider = clawgo_cfg.get("llm_provider", config.agents.clawgo_llm_provider)
    config.agents.clawgo_llm_model = clawgo_cfg.get("llm_model", config.agents.clawgo_llm_model)
    config.agents.clawgo_workspace_dir = clawgo_cfg.get("workspace_dir")

    # Pipeline
    pipeline_cfg = raw.get("pipeline", {})
    config.pipeline.mode = pipeline_cfg.get("mode", config.pipeline.mode)
    config.pipeline.default_language = pipeline_cfg.get("default_language", config.pipeline.default_language)

    # Inference
    inference_cfg = raw.get("inference", {})
    config.inference.asr_backend = inference_cfg.get("asr_backend", config.inference.asr_backend)
    config.inference.tts_backend = inference_cfg.get("tts_backend", config.inference.tts_backend)
    config.inference.llm_backend = inference_cfg.get("llm_backend", config.inference.llm_backend)

    # Server
    server_cfg = raw.get("server", {})
    config.server.host = server_cfg.get("host", config.server.host)
    config.server.port = server_cfg.get("port", config.server.port)
    config.server.cors_origins = server_cfg.get("cors_origins", config.server.cors_origins)

    logger.info(f"Config loaded: ASR={config.asr.engine}, LLM={config.llm.engine}, TTS={config.tts.engine}")
    return config
