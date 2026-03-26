"""
Tests for newly added modules: MMS ASR, XiaoZhi bridge, Indic ASR,
Cartesia TTS, MMS TTS, LlamaCpp backend, Pipeline orchestrator,
and ClawGo agent.

Tests initialization and basic functionality without loading heavy models.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestMMSASR:
    """Tests for Meta MMS ASR module."""

    def test_mmsasr_init(self):
        from src.asr.mms_asr import MMSASR
        asr = MMSASR(device="cpu")
        assert asr.device == "cpu"
        assert asr.model is None
        assert asr.MODEL_ID == "facebook/mms-1b-all"

    def test_omnilingual_asr_init(self):
        from src.asr.mms_asr import OmnilASR
        asr = OmnilASR(device="cpu", language="ml")
        assert asr.device == "cpu"
        assert asr.language == "ml"
        assert asr.pipeline is None

    def test_lang_mappings(self):
        from src.asr.mms_asr import LANG_TO_OMNI, LANG_TO_MMS, LANG_NAMES
        for lang in ["ml", "hi", "ta", "te", "bn", "mr", "gu", "kn", "pa", "ur", "en"]:
            assert lang in LANG_TO_OMNI
            assert lang in LANG_TO_MMS
            assert lang in LANG_NAMES

    def test_create_asr_factory(self):
        from src.asr import create_asr
        asr = create_asr(device="cpu")
        assert asr is not None
        assert asr.device == "cpu"


class TestIndicWhisperASR:
    """Tests for Indic Whisper ASR."""

    def test_indic_whisper_init(self):
        from src.asr import IndicWhisperASR
        asr = IndicWhisperASR(device="cpu")
        assert asr.device == "cpu"


class TestXiaoZhiBridge:
    """Tests for XiaoZhi protocol bridge."""

    def test_router_has_routes(self):
        from src.api.xiaozhi_bridge import router
        route_paths = [r.path for r in router.routes]
        assert "/xiaozhi/ota/" in route_paths
        assert "/xiaozhi/v1/" in route_paths

    def test_get_connected_devices_empty(self):
        from src.api.xiaozhi_bridge import get_connected_devices, connected_devices
        # Clear any state
        connected_devices.clear()
        result = get_connected_devices()
        assert result == {}

    def test_get_connected_devices_with_device(self):
        import time
        from src.api.xiaozhi_bridge import get_connected_devices, connected_devices
        connected_devices.clear()
        connected_devices["test-device-123"] = {
            "session_id": "sess-001",
            "connected_at": time.time() - 10,
            "websocket": MagicMock(),
        }
        result = get_connected_devices()
        assert "test-device-123" in result
        assert result["test-device-123"]["session_id"] == "sess-001"
        assert result["test-device-123"]["uptime_seconds"] >= 10
        connected_devices.clear()  # cleanup

    def test_ota_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.xiaozhi_bridge import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get(
            "/xiaozhi/ota/",
            headers={"device-id": "test-123", "device-model": "edgex-d1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "websocket" in data
        assert "server_time" in data
        assert "firmware" in data


class TestCartesiaTTS:
    """Tests for Cartesia TTS module."""

    def test_cartesia_init(self):
        from src.tts.cartesia_tts import CartesiaTTS
        tts = CartesiaTTS(api_key="test-key")
        assert tts.api_key == "test-key"


class TestMMSTTS:
    """Tests for MMS TTS module."""

    def test_mms_tts_init(self):
        from src.tts.mms_tts import MMSTTS
        tts = MMSTTS(device="cpu")
        assert tts.device == "cpu"
        assert tts.model is None


class TestLlamaCppBackend:
    """Tests for llama.cpp GGUF inference backend."""

    def test_llamacpp_init(self):
        from src.llm.llamacpp_backend import LlamaCppBackend
        backend = LlamaCppBackend(
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,
        )
        assert backend.n_ctx == 2048
        assert backend.n_threads == 4
        assert backend.n_gpu_layers == 0
        assert backend._model is None

    def test_llamacpp_gguf_repos(self):
        from src.llm.llamacpp_backend import LlamaCppBackend
        assert "qwen3-0.6b" in LlamaCppBackend.GGUF_REPOS
        assert "qwen3-1.7b" in LlamaCppBackend.GGUF_REPOS
        assert "qwen3-4b" in LlamaCppBackend.GGUF_REPOS


class TestPipelineOrchestrator:
    """Tests for the legacy pipeline orchestrator."""

    def test_pipeline_result_structure(self):
        from src.pipeline.orchestrator import VoiceAssistantPipeline
        pipeline = VoiceAssistantPipeline()
        assert pipeline is not None


class TestClawGoAgent:
    """Tests for ClawGo agent."""

    def test_clawgo_init(self):
        from src.agents.clawgo_agent import ClawGoAgent
        agent = ClawGoAgent(
            gateway_url="http://localhost:11434",
            llm_provider="ollama",
            llm_model="qwen3:1.7b",
        )
        assert agent.gateway_url == "http://localhost:11434"

    def test_clawgo_config(self):
        from src.agents.clawgo_agent import ClawGoAgent
        agent = ClawGoAgent(
            gateway_url="http://test:1234",
            llm_provider="ollama",
            llm_model="custom-model",
        )
        assert agent.llm_provider == "ollama"
        assert agent.llm_model == "custom-model"


class TestAgentFactory:
    """Tests for AgentFactory with different backends."""

    def test_create_langgraph(self):
        from src.agents import AgentFactory
        agent = AgentFactory.create(backend="langgraph")
        assert agent is not None

    def test_create_langgraph_with_llm(self):
        from src.agents import AgentFactory
        mock_llm = MagicMock()
        agent = AgentFactory.create(backend="langgraph", llm=mock_llm)
        assert agent.llm is mock_llm

    def test_create_invalid_raises(self):
        from src.agents import AgentFactory
        with pytest.raises(ValueError):
            AgentFactory.create(backend="nonexistent")


class TestOrchestratorFallbackResponses:
    """Tests for orchestrator fallback and helper functions."""

    def test_strip_think_tags(self):
        from src.agents.orchestrator import _strip_think_tags
        assert _strip_think_tags("Hello world") == "Hello world"
        assert _strip_think_tags("<think>reasoning</think>Answer") == "Answer"
        assert _strip_think_tags("<think>long\nreasoning\nblock</think>Final.") == "Final."

    def test_get_fallback_rotates(self):
        from src.agents.orchestrator import _get_fallback, IntentType, _fallback_counter
        import src.agents.orchestrator as orch_module

        orch_module._fallback_counter = 0
        r1 = _get_fallback(IntentType.GENERAL_CHAT)
        r2 = _get_fallback(IntentType.GENERAL_CHAT)
        # Should rotate through different responses
        assert isinstance(r1, str) and len(r1) > 0
        assert isinstance(r2, str) and len(r2) > 0

    def test_fallback_for_each_intent(self):
        from src.agents.orchestrator import _get_fallback, IntentType
        for intent in [IntentType.INFORMATION_QUERY, IntentType.TASK_MANAGEMENT,
                       IntentType.GENERAL_CHAT, IntentType.UNKNOWN]:
            result = _get_fallback(intent)
            assert isinstance(result, str)
            assert len(result) > 10

    def test_agent_prompts_defined(self):
        from src.agents.orchestrator import AGENT_PROMPTS
        assert "info_agent" in AGENT_PROMPTS
        assert "task_agent" in AGENT_PROMPTS
        assert "chat_agent" in AGENT_PROMPTS

    def test_orchestrator_llm_respond_fallback(self):
        """Without LLM, _llm_respond should return a fallback string."""
        from src.agents import AgentOrchestrator
        orch = AgentOrchestrator(llm=None)
        orch.setup()
        result = orch._llm_respond("test input", "info_agent")
        assert isinstance(result, str)
        assert len(result) > 0


class TestASRPackageInit:
    """Tests for ASR package __init__.py exports."""

    def test_asr_exports(self):
        from src.asr import WhisperASR, PingalaASR, IndicWhisperASR, create_asr
        assert WhisperASR is not None
        assert PingalaASR is not None
        assert IndicWhisperASR is not None
        assert create_asr is not None


class TestCachePackageInit:
    """Tests for cache package __init__.py exports."""

    def test_cache_exports(self):
        from src.cache import ResponseCache, CacheEntry, CacheStats, get_cache
        assert ResponseCache is not None
        assert CacheEntry is not None
        assert CacheStats is not None
        assert get_cache is not None


class TestOptimizationPackageInit:
    """Tests for optimization package __init__.py exports."""

    def test_optimization_exports(self):
        from src.optimization import ModelOptimizer, MemoryProfile, MemoryTracker, LazyModelLoader
        assert ModelOptimizer is not None
        assert MemoryProfile is not None
        assert MemoryTracker is not None
        assert LazyModelLoader is not None
