"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def temp_db(temp_dir):
    """Provide a temporary database instance."""
    from src.db.database import Database

    db = Database(db_path=str(temp_dir / "test.db"))
    db.connect()
    yield db
    db.close()


@pytest.fixture
def sample_conversation():
    """Provide a sample conversation for testing."""
    from src.db.models import Conversation, Message

    conv = Conversation(
        language="ml",
        intent="general_chat",
        status="completed",
        asr_time_ms=120.5,
        translation_time_ms=85.3,
        llm_time_ms=340.2,
        tts_time_ms=95.1,
        total_time_ms=641.1,
    )
    conv.messages = [
        Message(role="user", content="Hello, how are you?", language="en"),
        Message(role="assistant", content="I'm doing well!", language="en"),
    ]
    return conv


@pytest.fixture
def app_config():
    """Provide a test AppConfig with default values."""
    from src.config import AppConfig

    return AppConfig()
