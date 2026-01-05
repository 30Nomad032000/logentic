"""
Basic tests for Voice Assistant components.
Sprint 1 - Foundation tests.
"""

import pytest


class TestASR:
    """Tests for ASR module."""

    def test_whisper_asr_init(self):
        """Test WhisperASR initialization."""
        from src.asr import WhisperASR

        asr = WhisperASR(model_size="tiny", device="cpu")
        assert asr.model_size == "tiny"
        assert asr.device == "cpu"
        assert asr.model is None  # Model not loaded yet

    def test_supported_languages(self):
        """Test supported Indian languages."""
        from src.asr import WhisperASR

        asr = WhisperASR()
        assert "hi" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert "ml" in asr.SUPPORTED_INDIAN_LANGUAGES
        assert asr.SUPPORTED_INDIAN_LANGUAGES["hi"] == "Hindi"


class TestTTS:
    """Tests for TTS module."""

    def test_indic_tts_init(self):
        """Test IndicTTS initialization."""
        from src.tts import IndicTTS

        tts = IndicTTS(default_language="hi")
        assert tts.default_language == "hi"
        assert tts.model is None  # Model not loaded yet

    def test_supported_languages(self):
        """Test supported TTS languages."""
        from src.tts import IndicTTS

        tts = IndicTTS()
        languages = tts.get_supported_languages()
        assert "hi" in languages
        assert "ml" in languages

    def test_supported_emotions(self):
        """Test supported TTS emotions."""
        from src.tts import IndicTTS

        tts = IndicTTS()
        emotions = tts.get_supported_emotions()
        assert "neutral" in emotions
        assert "happy" in emotions


class TestNLU:
    """Tests for NLU module."""

    def test_intent_classifier_init(self):
        """Test IntentClassifier initialization."""
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="keyword")
        assert classifier.model_type == "keyword"

    def test_intent_classification(self):
        """Test basic intent classification."""
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()

        # Test greeting intent
        result = classifier.classify("hello how are you")
        assert result.intent == "greeting"

        # Test weather intent
        result = classifier.classify("what is the weather today")
        assert result.intent == "weather"

        # Test reminder intent
        result = classifier.classify("remind me to call mom")
        assert result.intent == "reminder"

    def test_get_supported_intents(self):
        """Test getting supported intents."""
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()
        intents = classifier.get_supported_intents()
        assert "greeting" in intents
        assert "weather" in intents


class TestAgents:
    """Tests for Agent orchestrator."""

    def test_orchestrator_init(self):
        """Test AgentOrchestrator initialization."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        assert orchestrator.graph is None
        assert orchestrator.agents == {}

    def test_orchestrator_process(self):
        """Test basic orchestrator processing."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        result = orchestrator.process("hello there", "en")
        assert "response" in result
        assert result["language"] == "en"


class TestEdge:
    """Tests for Edge module."""

    def test_audio_handler_init(self):
        """Test AudioHandler initialization."""
        from src.edge import AudioHandler

        handler = AudioHandler(sample_rate=16000, channels=1)
        assert handler.sample_rate == 16000
        assert handler.channels == 1

    def test_edge_client_init(self):
        """Test EdgeClient initialization."""
        from src.edge import EdgeClient

        client = EdgeClient(server_url="http://localhost:8000")
        assert client.server_url == "http://localhost:8000"


# Run tests with: pytest tests/ -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
