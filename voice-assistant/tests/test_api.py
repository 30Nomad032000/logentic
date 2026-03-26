"""
Tests for the FastAPI application and dashboard endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from src.api.main import app
    from src.agents import AgentOrchestrator
    from src.db import get_db
    import src.api.main as api_module

    if api_module.orchestrator is None:
        api_module.orchestrator = AgentOrchestrator()
        api_module.orchestrator.setup()
    if api_module.db is None:
        api_module.db = get_db()

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.2.0"
        assert "components" in data

    def test_health_has_components(self, client):
        response = client.get("/health")
        data = response.json()
        components = data["components"]
        assert "asr" in components
        assert "tts" in components
        assert "orchestrator" in components
        assert "database" in components


class TestDashboard:
    """Tests for dashboard endpoints."""

    def test_dashboard_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_stats(self, client):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "avg_latency" in data
        assert "languages" in data
        assert "intents" in data

    def test_dashboard_conversations_list(self, client):
        response = client.get("/api/dashboard/conversations?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data

    def test_dashboard_conversation_not_found(self, client):
        response = client.get("/api/dashboard/conversations/nonexistent")
        assert response.status_code == 404


class TestTextEndpoint:
    """Tests for the text processing endpoint."""

    def test_process_text(self, client):
        response = client.post(
            "/api/text",
            data={"text": "hello there", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "input" in data
        assert "response" in data
        assert "intent" in data
        assert data["language"] == "en"

    def test_process_text_logs_conversation(self, client):
        """Verify that text processing creates a conversation log."""
        # Get initial count
        stats = client.get("/api/dashboard/stats").json()
        initial_count = stats["total_conversations"]

        # Process text
        client.post(
            "/api/text",
            data={"text": "what is the weather", "language": "en"},
        )

        # Verify count increased
        stats = client.get("/api/dashboard/stats").json()
        assert stats["total_conversations"] == initial_count + 1


class TestTTSEndpoint:
    """Tests for TTS endpoint (503 when engine not loaded)."""

    def test_tts_not_initialized(self, client):
        response = client.post(
            "/api/tts",
            data={"text": "hello", "language": "en"},
        )
        # Will be 503 if TTS engine not loaded, or 200 if loaded
        assert response.status_code in [200, 503]
