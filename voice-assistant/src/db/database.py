"""
Database Layer
SQLite database for conversation logging and system metrics.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .models import Conversation, Message, SystemMetric, Task

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "voice_assistant.db"


class Database:
    """
    SQLite database for the voice assistant.

    Stores:
    - Conversations and messages (chat history)
    - Pipeline performance metrics
    - System health snapshots
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open database connection and create tables."""
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        logger.info(f"Database connected: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    def _create_tables(self):
        """Create database tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                language TEXT DEFAULT 'ml',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                status TEXT DEFAULT 'active',
                intent TEXT DEFAULT '',
                asr_time_ms REAL DEFAULT 0,
                translation_time_ms REAL DEFAULT 0,
                llm_time_ms REAL DEFAULT 0,
                tts_time_ms REAL DEFAULT 0,
                total_time_ms REAL DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE TABLE IF NOT EXISTS system_metrics (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                component TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                source_input TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_created
                ON tasks(created_at);

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_started
                ON conversations(started_at);
            CREATE INDEX IF NOT EXISTS idx_metrics_component
                ON system_metrics(component, timestamp);
        """)

    # ── Conversations ──

    def save_conversation(self, conv: Conversation) -> str:
        """Save a conversation to the database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO conversations
               (id, session_id, language, started_at, ended_at, status, intent,
                asr_time_ms, translation_time_ms, llm_time_ms, tts_time_ms,
                total_time_ms, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                conv.id, conv.session_id, conv.language,
                conv.started_at, conv.ended_at, conv.status, conv.intent,
                conv.asr_time_ms, conv.translation_time_ms,
                conv.llm_time_ms, conv.tts_time_ms, conv.total_time_ms,
                json.dumps(conv.metadata),
            ),
        )
        for msg in conv.messages:
            msg.conversation_id = conv.id
            self.save_message(msg)
        self.conn.commit()
        return conv.id

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        row = self.conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        ).fetchone()
        if not row:
            return None
        conv = self._row_to_conversation(row)
        conv.messages = self.get_messages(conv_id)
        return conv

    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Conversation]:
        """List conversations with pagination."""
        query = "SELECT * FROM conversations"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(query, params).fetchall()
        convs = []
        for row in rows:
            conv = self._row_to_conversation(row)
            conv.messages = self.get_messages(conv.id)
            convs.append(conv)
        return convs

    def count_conversations(self) -> int:
        """Count total conversations."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM conversations").fetchone()
        return row["cnt"]

    def _row_to_conversation(self, row: sqlite3.Row) -> Conversation:
        return Conversation(
            id=row["id"],
            session_id=row["session_id"],
            language=row["language"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            status=row["status"],
            intent=row["intent"],
            asr_time_ms=row["asr_time_ms"],
            translation_time_ms=row["translation_time_ms"],
            llm_time_ms=row["llm_time_ms"],
            tts_time_ms=row["tts_time_ms"],
            total_time_ms=row["total_time_ms"],
            metadata=json.loads(row["metadata"]),
        )

    # ── Messages ──

    def save_message(self, msg: Message):
        """Save a message to the database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO messages
               (id, conversation_id, role, content, language, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                msg.id, msg.conversation_id, msg.role,
                msg.content, msg.language, msg.timestamp,
                json.dumps(msg.metadata),
            ),
        )

    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation."""
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()
        return [
            Message(
                id=r["id"],
                conversation_id=r["conversation_id"],
                role=r["role"],
                content=r["content"],
                language=r["language"],
                timestamp=r["timestamp"],
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

    # ── Tasks ──

    def save_task(self, task: Task) -> str:
        """Save a task to the database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO tasks
               (id, title, status, created_at, completed_at, source_input)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task.id, task.title, task.status, task.created_at,
             task.completed_at, task.source_input),
        )
        self.conn.commit()
        return task.id

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Task]:
        """List tasks, optionally filtered by status."""
        query = "SELECT * FROM tasks"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [
            Task(
                id=r["id"], title=r["title"], status=r["status"],
                created_at=r["created_at"], completed_at=r["completed_at"],
                source_input=r["source_input"],
            )
            for r in rows
        ]

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update a task's status. Returns True if found."""
        completed_at = datetime.utcnow().isoformat() if status == "done" else None
        cur = self.conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at, task_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ── System Metrics ──

    def save_metric(self, metric: SystemMetric):
        """Save a system metric."""
        self.conn.execute(
            """INSERT INTO system_metrics
               (id, timestamp, component, metric_name, value, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                metric.id, metric.timestamp, metric.component,
                metric.metric_name, metric.value,
                json.dumps(metric.metadata),
            ),
        )
        self.conn.commit()

    def get_metrics(
        self,
        component: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[SystemMetric]:
        """Get system metrics with optional filtering."""
        query = "SELECT * FROM system_metrics WHERE 1=1"
        params: list = []
        if component:
            query += " AND component = ?"
            params.append(component)
        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [
            SystemMetric(
                id=r["id"],
                timestamp=r["timestamp"],
                component=r["component"],
                metric_name=r["metric_name"],
                value=r["value"],
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

    def get_avg_latency(self, hours: int = 24) -> dict:
        """Get average latency per component over the last N hours."""
        row = self.conn.execute(
            """SELECT
                AVG(asr_time_ms) as avg_asr,
                AVG(translation_time_ms) as avg_translation,
                AVG(llm_time_ms) as avg_llm,
                AVG(tts_time_ms) as avg_tts,
                AVG(total_time_ms) as avg_total,
                COUNT(*) as count
            FROM conversations
            WHERE started_at >= datetime('now', ? || ' hours')""",
            (f"-{hours}",),
        ).fetchone()
        return {
            "asr_ms": round(row["avg_asr"] or 0, 1),
            "translation_ms": round(row["avg_translation"] or 0, 1),
            "llm_ms": round(row["avg_llm"] or 0, 1),
            "tts_ms": round(row["avg_tts"] or 0, 1),
            "total_ms": round(row["avg_total"] or 0, 1),
            "conversation_count": row["count"],
        }

    def get_language_stats(self) -> List[dict]:
        """Get conversation count per language."""
        rows = self.conn.execute(
            """SELECT language, COUNT(*) as count
               FROM conversations
               GROUP BY language
               ORDER BY count DESC"""
        ).fetchall()
        return [{"language": r["language"], "count": r["count"]} for r in rows]

    def get_intent_stats(self) -> List[dict]:
        """Get conversation count per intent."""
        rows = self.conn.execute(
            """SELECT intent, COUNT(*) as count
               FROM conversations
               WHERE intent != ''
               GROUP BY intent
               ORDER BY count DESC"""
        ).fetchall()
        return [{"intent": r["intent"], "count": r["count"]} for r in rows]


# ── Singleton ──

_db: Optional[Database] = None


def get_db(db_path: Optional[str] = None) -> Database:
    """Get or create singleton database instance."""
    global _db
    if _db is None:
        _db = Database(db_path=db_path)
        _db.connect()
    return _db
