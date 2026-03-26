"""
Integration tests for Voice Assistant pipeline.
Tests end-to-end flows without loading heavy ML models.
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass


class TestAgentOrchestrationFlow:
    """Test the full agent orchestration flow with mocked LLM."""

    def test_info_query_routes_to_info_agent(self):
        """Information queries should route to the info agent."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        with patch("src.agents.orchestrator._get_agent_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = MagicMock(content="Kerala's capital is Thiruvananthapuram.")
            mock_llm.system_prompt = "test"
            mock_llm_fn.return_value = mock_llm

            result = orchestrator.process("What is the capital of Kerala?", "en")

        assert "response" in result
        assert result["intent"] == "information_query"
        assert result["response"]  # non-empty
        assert "[Info Agent]" not in result["response"]  # no mock prefix

    def test_task_request_routes_to_task_agent(self):
        """Task requests should route to the task agent."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        with patch("src.agents.orchestrator._get_agent_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = MagicMock(content="I've set a reminder for 5 PM to call mom.")
            mock_llm.system_prompt = "test"
            mock_llm_fn.return_value = mock_llm

            result = orchestrator.process("Remind me to call mom at 5pm", "en")

        assert result["intent"] == "task_management"
        assert "response" in result
        assert "[Task Agent]" not in result["response"]

    def test_greeting_routes_to_chat_agent(self):
        """Greetings should route to the chat agent."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        with patch("src.agents.orchestrator._get_agent_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = MagicMock(content="Hello! Nice to meet you!")
            mock_llm.system_prompt = "test"
            mock_llm_fn.return_value = mock_llm

            # Use input without "how" which triggers information_query
            result = orchestrator.process("Hey there, good morning!", "en")

        assert result["intent"] == "general_chat"
        assert "response" in result
        assert "[Chat Agent]" not in result["response"]

    def test_fallback_when_llm_unavailable(self):
        """Agents should return graceful fallback when LLM is unavailable."""
        from src.agents import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        with patch("src.agents.orchestrator._get_agent_llm") as mock_llm_fn:
            mock_llm_fn.return_value = None

            result = orchestrator.process("What is the weather?", "en")

        assert "response" in result
        assert len(result["response"]) > 0  # fallback response exists


class TestIntentClassification:
    """Test intent classification across different methods."""

    def test_keyword_greeting(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="keyword")
        result = classifier.classify("hello namaste how are you")
        assert result.intent == "greeting"
        assert result.confidence > 0

    def test_keyword_weather(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="keyword")
        result = classifier.classify("what is the weather temperature today")
        assert result.intent == "weather"

    def test_keyword_reminder(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="keyword")
        result = classifier.classify("remind me at 5pm")
        assert result.intent == "reminder"

    def test_entity_extraction_time(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("remind me at 5pm")
        time_entities = [e for e in result.entities if e["type"] == "time"]
        assert len(time_entities) > 0

    def test_entity_extraction_number(self):
        from src.nlu import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("set timer for 30 minutes")
        number_entities = [e for e in result.entities if e["type"] == "number"]
        assert len(number_entities) > 0

    def test_llm_classify_falls_back_gracefully(self):
        """LLM classification should fall back to keyword when LLM not available."""
        from src.nlu import IntentClassifier

        classifier = IntentClassifier(model_type="llm")
        result = classifier.classify("hello there", "en")
        assert result.intent in ("greeting", "unknown")


class TestPipelineIntentDetection:
    """Test the pipeline's intent detection module."""

    def test_intent_detector_weather(self):
        from src.pipeline.intent import IntentDetector

        detector = IntentDetector(use_llm=False)
        intent = detector.detect("what is the weather", "what is the weather")
        assert intent.type.value == "weather"
        assert intent.confidence > 0

    def test_intent_detector_greeting(self):
        from src.pipeline.intent import IntentDetector

        detector = IntentDetector(use_llm=False)
        intent = detector.detect("hello good morning", "hello good morning")
        assert intent.type.value == "greeting"

    def test_intent_detector_reminder(self):
        from src.pipeline.intent import IntentDetector

        detector = IntentDetector(use_llm=False)
        intent = detector.detect("set a reminder for meeting", "set a reminder for meeting")
        assert intent.type.value == "reminder"

    def test_intent_detector_unknown_falls_to_general(self):
        from src.pipeline.intent import IntentDetector

        detector = IntentDetector(use_llm=False)
        intent = detector.detect("xyzzy blorp", "xyzzy blorp")
        assert intent.type.value == "general"


class TestDatabaseConversationFlow:
    """Test database operations for conversation logging."""

    def test_save_and_retrieve_conversation(self, temp_db, sample_conversation):
        """Full conversation save and retrieve cycle."""
        temp_db.save_conversation(sample_conversation)

        # Retrieve it
        convs = temp_db.list_conversations(limit=10)
        assert len(convs) >= 1

        conv = convs[0]
        assert conv.language == "ml"
        assert conv.intent == "general_chat"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"

    def test_conversation_stats(self, temp_db, sample_conversation):
        """Stats should reflect saved conversations."""
        temp_db.save_conversation(sample_conversation)

        count = temp_db.count_conversations()
        assert count >= 1

        lang_stats = temp_db.get_language_stats()
        assert any(s.get("language") == "ml" or s.get("_id") == "ml" for s in lang_stats) if lang_stats else True

    def test_multiple_conversations(self, temp_db):
        """Multiple conversations should all be retrievable."""
        from src.db.models import Conversation, Message

        for i in range(5):
            conv = Conversation(
                language="ml" if i % 2 == 0 else "hi",
                intent="greeting",
                status="completed",
                total_time_ms=100.0 + i * 50,
            )
            conv.messages = [
                Message(role="user", content=f"Test input {i}", language="en"),
                Message(role="assistant", content=f"Test response {i}", language="en"),
            ]
            temp_db.save_conversation(conv)

        count = temp_db.count_conversations()
        assert count == 5


class TestAPIIntegration:
    """Test API endpoints with orchestrator integration."""

    @pytest.fixture
    def client(self):
        from src.api.main import app
        from src.agents import AgentOrchestrator
        from src.db import get_db
        from fastapi.testclient import TestClient
        import src.api.main as api_module

        # Ensure orchestrator and db are available for tests
        if api_module.orchestrator is None:
            api_module.orchestrator = AgentOrchestrator()
            api_module.orchestrator.setup()
        if api_module.db is None:
            api_module.db = get_db()

        return TestClient(app)

    def test_text_endpoint_returns_real_response(self, client):
        """Text endpoint should return a real response, not a mock stub."""
        response = client.post(
            "/api/text",
            data={"text": "hello there", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()
        # Should not contain mock agent prefixes
        assert "[Info Agent]" not in data.get("response", "")
        assert "[Task Agent]" not in data.get("response", "")
        assert "[Chat Agent]" not in data.get("response", "")

    def test_text_endpoint_with_question(self, client):
        """Question input should be processed and return intent."""
        response = client.post(
            "/api/text",
            data={"text": "What is the capital of India?", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] is not None
        assert len(data["response"]) > 0

    def test_health_endpoint_version(self, client):
        """Health endpoint should return correct version."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == "0.2.0"

    def test_dashboard_stats_structure(self, client):
        """Dashboard stats should have all required fields."""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        for key in ["total_conversations", "avg_latency", "languages", "intents"]:
            assert key in data
