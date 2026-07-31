"""
RAE-Suite Transactional Outbox & Command Store
Ensures atomic state commits and event publishing with idempotency registration.
"""

import sqlite3
import json
import threading
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OutboxMessage(BaseModel):
    id: int
    command_id: str
    idempotency_key: str
    topic: str
    payload_json: str
    status: str  # "PENDING", "DISPATCHED", "FAILED"
    created_at: str


class TransactionalOutbox:
    """
    Transactional Outbox pattern using SQLite transaction locks to guarantee
    atomic domain state commit and event publishing.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "/tmp/rae_outbox.db"
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_id TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    topic TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def stage_command(self, command_id: str, idempotency_key: str, topic: str, payload: Dict[str, Any]) -> tuple[bool, str]:
        """
        Atomically stages command message in outbox table under idempotency check.
        Rejects duplicate idempotency keys.
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO outbox_messages (command_id, idempotency_key, topic, payload_json, status) VALUES (?, ?, ?, ?, 'PENDING')",
                        (command_id, idempotency_key, topic, json.dumps(payload))
                    )
                    conn.commit()
                return True, "STAGED_SUCCESS"
            except sqlite3.IntegrityError:
                return False, f"DUPLICATE_IDEMPOTENCY_KEY: Key {idempotency_key[:16]} already staged"

    def fetch_pending_messages(self, limit: int = 50) -> List[OutboxMessage]:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT id, command_id, idempotency_key, topic, payload_json, status, created_at FROM outbox_messages WHERE status = 'PENDING' ORDER BY id ASC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                return [
                    OutboxMessage(
                        id=row["id"],
                        command_id=row["command_id"],
                        idempotency_key=row["idempotency_key"],
                        topic=row["topic"],
                        payload_json=row["payload_json"],
                        status=row["status"],
                        created_at=row["created_at"]
                    )
                    for row in rows
                ]

    def mark_dispatched(self, message_id: int):
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE outbox_messages SET status = 'DISPATCHED' WHERE id = ?", (message_id,))
                conn.commit()
