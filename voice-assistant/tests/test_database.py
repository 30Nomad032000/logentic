"""
Tests for database layer - conversation logging and metrics.
"""

import pytest
from src.db.models import Conversation, Message, SystemMetric
from src.db.database import Database


class TestModels:
    """Tests for database model dataclasses."""

    def test_message_auto_id(self):
        msg = Message(role="user", content="hello")
        assert msg.id  # auto-generated UUID
        assert msg.timestamp  # auto-generated timestamp

    def test_conversation_auto_id(self):
        conv = Conversation(language="ml")
        assert conv.id
        assert conv.session_id
        assert conv.started_at
        assert conv.status == "active"

    def test_system_metric_auto_id(self):
        metric = SystemMetric(component="asr", metric_name="latency_ms", value=120.5)
        assert metric.id
        assert metric.timestamp


class TestDatabase:
    """Tests for database CRUD operations."""

    def test_connect(self, temp_db):
        assert temp_db.conn is not None

    def test_save_and_get_conversation(self, temp_db, sample_conversation):
        conv_id = temp_db.save_conversation(sample_conversation)
        assert conv_id == sample_conversation.id

        loaded = temp_db.get_conversation(conv_id)
        assert loaded is not None
        assert loaded.language == "ml"
        assert loaded.intent == "general_chat"
        assert loaded.total_time_ms == 641.1
        assert len(loaded.messages) == 2

    def test_list_conversations(self, temp_db, sample_conversation):
        temp_db.save_conversation(sample_conversation)

        convs = temp_db.list_conversations(limit=10)
        assert len(convs) == 1
        assert convs[0].id == sample_conversation.id

    def test_count_conversations(self, temp_db, sample_conversation):
        assert temp_db.count_conversations() == 0
        temp_db.save_conversation(sample_conversation)
        assert temp_db.count_conversations() == 1

    def test_get_nonexistent_conversation(self, temp_db):
        result = temp_db.get_conversation("nonexistent-id")
        assert result is None

    def test_messages_order(self, temp_db, sample_conversation):
        temp_db.save_conversation(sample_conversation)
        msgs = temp_db.get_messages(sample_conversation.id)
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"

    def test_save_metric(self, temp_db):
        metric = SystemMetric(
            component="asr",
            metric_name="latency_ms",
            value=120.5,
        )
        temp_db.save_metric(metric)

        metrics = temp_db.get_metrics(component="asr")
        assert len(metrics) == 1
        assert metrics[0].value == 120.5

    def test_get_metrics_filtered(self, temp_db):
        temp_db.save_metric(SystemMetric(component="asr", metric_name="latency_ms", value=100))
        temp_db.save_metric(SystemMetric(component="llm", metric_name="latency_ms", value=200))
        temp_db.save_metric(SystemMetric(component="asr", metric_name="memory_mb", value=50))

        asr_metrics = temp_db.get_metrics(component="asr")
        assert len(asr_metrics) == 2

        latency_metrics = temp_db.get_metrics(metric_name="latency_ms")
        assert len(latency_metrics) == 2

    def test_avg_latency(self, temp_db, sample_conversation):
        temp_db.save_conversation(sample_conversation)
        avg = temp_db.get_avg_latency(hours=24)
        assert avg["asr_ms"] == 120.5
        assert avg["total_ms"] == 641.1
        assert avg["conversation_count"] == 1

    def test_language_stats(self, temp_db):
        c1 = Conversation(language="ml", status="completed")
        c2 = Conversation(language="ml", status="completed")
        c3 = Conversation(language="hi", status="completed")
        temp_db.save_conversation(c1)
        temp_db.save_conversation(c2)
        temp_db.save_conversation(c3)

        stats = temp_db.get_language_stats()
        assert len(stats) == 2
        assert stats[0]["language"] == "ml"
        assert stats[0]["count"] == 2

    def test_intent_stats(self, temp_db):
        c1 = Conversation(intent="greeting", status="completed")
        c2 = Conversation(intent="greeting", status="completed")
        c3 = Conversation(intent="weather", status="completed")
        temp_db.save_conversation(c1)
        temp_db.save_conversation(c2)
        temp_db.save_conversation(c3)

        stats = temp_db.get_intent_stats()
        assert len(stats) == 2
        assert stats[0]["intent"] == "greeting"
        assert stats[0]["count"] == 2
