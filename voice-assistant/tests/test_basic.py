"""
Basic tests for Voice Assistant core components.
Tests initialization and configuration of all modules.
"""

import pytest


class TestASR:
    """Tests for ASR module."""

    def test_whisper_asr_init(self):
        from src.asr import WhisperASR

        asr = WhisperASR(model_size="tiny", device="cpu")
        assert asr.model_size == "tiny"
        assert asr.device == "cpu"
        assert asr.model is None

    def test_whisper_supported_languages(self):
        from src.asr import WhisperASR

        asr = WhisperASR()
        assert "hi" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert "ml" in asr.SUPPORTED_INDIAN_LANGUAGES

    def test_pingala_asr_init(self):
        from src.asr import PingalaASR

        asr = PingalaASR(device="cpu")
        assert asr.device == "cpu"
        assert asr.model is None
        assert asr.model_id == "shunya-labs/pingala-v1"

    def test_pingala_supported_languages(self):
        from src.asr import PingalaASR

        asr = PingalaASR()
        assert "hi" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert "ml" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert "en" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert len(asr.SUPPORTED_INDIAN_LANGUAGES) == 11


class TestTTS:
    """Tests for TTS module."""

    def test_indic_tts_init(self):
        from src.tts import IndicTTS

        tts = IndicTTS(default_language="hi")
        assert tts.default_language == "hi"
        assert tts.model is None

    def test_indic_tts_variants(self):
        from src.tts import IndicTTS

        tts_mini = IndicTTS(variant="mini")
        assert tts_mini.variant == "mini"
        assert "mini" in IndicTTS.MODEL_VARIANTS
        assert "full" in IndicTTS.MODEL_VARIANTS

    def test_tts_supported_languages(self):
        from src.tts import IndicTTS

        tts = IndicTTS()
        languages = tts.get_supported_languages()
        assert "hi" in languages
        assert "ml" in languages

    def test_tts_supported_emotions(self):
        from src.tts import IndicTTS

        tts = IndicTTS()
        emotions = tts.get_supported_emotions()
        assert "neutral" in emotions
        assert "happy" in emotions

    def test_chatterbox_tts_init(self):
        from src.tts import ChatterboxTTS

        tts = ChatterboxTTS(device="cpu")
        assert tts.device == "cpu"
        assert tts.sample_rate == 24000

    def test_tts_engine_backends(self):
        from src.tts import TTSEngine

        assert "mms" in TTSEngine.BACKENDS
        assert "cartesia" in TTSEngine.BACKENDS
        assert "indic" in TTSEngine.BACKENDS
        assert "chatterbox" in TTSEngine.BACKENDS


class TestTranslation:
    """Tests for Translation module."""

    def test_translator_init(self):
        from src.translation.indictrans import IndicTranslator

        translator = IndicTranslator(device="cpu", model_variant="dist")
        assert translator.device == "cpu"
        assert translator.model_variant == "dist"

    def test_model_variants(self):
        from src.translation.indictrans import IndicTranslator

        assert "full" in IndicTranslator.MODEL_VARIANTS
        assert "dist" in IndicTranslator.MODEL_VARIANTS
        assert "indic-indic" in IndicTranslator.MODEL_VARIANTS["dist"]

    def test_lang_codes_coverage(self):
        from src.translation.indictrans import IndicTranslator

        codes = IndicTranslator.LANG_CODES
        for lang in ["ml", "hi", "ta", "te", "bn", "mr", "gu", "kn", "pa", "ur", "en"]:
            assert lang in codes

    def test_get_translator_singleton(self):
        from src.translation.indictrans import get_translator
        import src.translation.indictrans as module

        module._translator = None
        t1 = get_translator(device="cpu", model_variant="dist")
        t2 = get_translator(device="cpu", model_variant="dist")
        assert t1 is t2
        module._translator = None


class TestLLM:
    """Tests for LLM module."""

    def test_qwen_llm_init(self):
        from src.llm import QwenLLM

        llm = QwenLLM(model_size="0.5b", device="cpu")
        assert llm.model_size == "0.5b"
        assert llm.device == "cpu"
        assert llm.model is None

    def test_qwen3_llm_init(self):
        from src.llm import Qwen3LLM

        llm = Qwen3LLM(model_size="0.6b", backend="llamacpp", device="cpu")
        assert llm.model_size == "0.6b"
        assert llm.backend_type == "llamacpp"

    def test_qwen3_model_sizes(self):
        from src.llm import Qwen3LLM

        assert "0.6b" in Qwen3LLM.MODELS_GGUF
        assert "1.7b" in Qwen3LLM.MODELS_GGUF
        assert "4b" in Qwen3LLM.MODELS_GGUF

    def test_qwen3_history_management(self):
        from src.llm import Qwen3LLM

        llm = Qwen3LLM()
        assert len(llm.conversation_history) == 0
        llm.clear_history()
        assert len(llm.conversation_history) == 0

    def test_get_llm_routes_to_qwen3(self):
        from src.llm.qwen import get_llm
        from src.llm import Qwen3LLM
        import src.llm.qwen as module

        module._llm = None
        llm = get_llm(engine="qwen3", model_size="0.6b", device="cpu")
        assert isinstance(llm, Qwen3LLM)
        module._llm = None

    def test_get_llm_routes_to_qwen(self):
        from src.llm.qwen import get_llm, QwenLLM
        import src.llm.qwen as module

        module._llm = None
        llm = get_llm(engine="qwen", model_size="0.5b", device="cpu")
        assert isinstance(llm, QwenLLM)
        module._llm = None


class TestNLU:
    """Tests for NLU module."""

    def test_intent_classifier_init(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="keyword")
        assert classifier.model_type == "keyword"

    def test_intent_classification(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("hello how are you")
        assert result.intent == "greeting"

        result = classifier.classify("what is the weather today")
        assert result.intent == "weather"

        result = classifier.classify("remind me to call mom")
        assert result.intent == "reminder"

    def test_supported_intents(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()
        intents = classifier.get_supported_intents()
        assert "greeting" in intents
        assert "weather" in intents


class TestAgents:
    """Tests for Agent orchestrator."""

    def test_orchestrator_init(self):
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        assert orchestrator.graph is None
        assert orchestrator.agents == {}

    def test_orchestrator_process(self):
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()
        result = orchestrator.process("hello there", "en")
        assert "response" in result
        assert result["language"] == "en"

    def test_clawgo_agent_init(self):
        from src.agents import ClawGoAgent

        agent = ClawGoAgent(
            gateway_url="http://localhost:11434",
            llm_model="qwen3:1.7b",
        )
        assert agent.gateway_url == "http://localhost:11434"
        assert agent.llm_model == "qwen3:1.7b"

    def test_agent_factory_langgraph(self):
        from src.agents import AgentFactory, AgentOrchestrator

        agent = AgentFactory.create(backend="langgraph")
        assert isinstance(agent, AgentOrchestrator)

    def test_agent_factory_invalid(self):
        from src.agents import AgentFactory

        with pytest.raises(ValueError):
            AgentFactory.create(backend="nonexistent")


class TestInference:
    """Tests for Inference engine module."""

    def test_onnx_backend_init(self):
        from src.inference import ONNXInferenceBackend

        backend = ONNXInferenceBackend(model_path="test.onnx")
        assert backend.model_path == "test.onnx"
        assert not backend.loaded

    def test_inference_engine_available_backends(self):
        from src.inference import InferenceEngine

        available = InferenceEngine.get_available_backends()
        assert "transformers" in available

    def test_inference_engine_transformers(self):
        from src.inference import InferenceEngine

        result = InferenceEngine.create("transformers")
        assert result is None


class TestPipeline:
    """Tests for Pipeline module."""

    def test_legacy_pipeline_init(self):
        from src.pipeline import VoiceAssistantPipeline

        pipeline = VoiceAssistantPipeline(
            asr_engine="whisper",
            llm_model_size="1.5b",
            tts_engine="mms",
            device="cpu",
        )
        assert pipeline.asr_engine == "whisper"

    def test_pipecat_pipeline_init(self):
        from src.pipeline import PipecatVoicePipeline

        pipeline = PipecatVoicePipeline(
            asr_engine="pingala",
            llm_engine="qwen3",
            llm_model_size="1.7b",
            tts_backend="mms",
        )
        assert pipeline.default_language == "ml"
        assert pipeline.stt is not None
        assert pipeline.llm is not None


class TestConfig:
    """Tests for Configuration module."""

    def test_config_defaults(self):
        from src.config import AppConfig

        config = AppConfig()
        assert config.asr.engine == "pingala"
        assert config.llm.engine == "qwen3"
        assert config.llm.backend == "llamacpp"
        assert config.translation.model_variant == "dist"
        assert config.pipeline.mode == "pipecat"

    def test_load_config_from_yaml(self):
        from src.config import load_config

        config = load_config()
        assert config.version == "0.2.0"
        assert config.asr.engine == "pingala"
        assert config.llm.engine == "qwen3"

    def test_load_config_missing_file(self):
        from src.config import load_config

        config = load_config("/nonexistent/settings.yaml")
        assert config.asr.engine == "pingala"  # uses defaults


class TestEdge:
    """Tests for Edge module."""

    def test_audio_handler_init(self):
        from src.edge import AudioHandler

        handler = AudioHandler(sample_rate=16000, channels=1)
        assert handler.sample_rate == 16000
        assert handler.channels == 1

    def test_edge_client_init(self):
        from src.edge import EdgeClient

        client = EdgeClient(server_url="http://localhost:8000")
        assert client.server_url == "http://localhost:8000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
