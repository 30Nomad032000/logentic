"""
Database Models
SQLite-backed models for conversation logging, sessions, and system metrics.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Message:
    """A single message in a conversation."""
    id: str = ""
    conversation_id: str = ""
    role: str = ""  # user, assistant, system
    content: str = ""
    language: str = "en"
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class Conversation:
    """A conversation session with multiple messages."""
    id: str = ""
    session_id: str = ""
    language: str = "ml"
    started_at: str = ""
    ended_at: Optional[str] = None
    status: str = "active"  # active, completed, error
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)

    # Pipeline metrics (populated after processing)
    asr_time_ms: float = 0
    translation_time_ms: float = 0
    llm_time_ms: float = 0
    tts_time_ms: float = 0
    total_time_ms: float = 0
    intent: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()


@dataclass
class SystemMetric:
    """A system performance metric snapshot."""
    id: str = ""
    timestamp: str = ""
    component: str = ""  # asr, llm, tts, translation, pipeline
    metric_name: str = ""  # latency_ms, memory_mb, error_count
    value: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
