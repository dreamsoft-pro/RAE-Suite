"""
RAE-Suite Lightweight MAES EventStore & CQRS Projections
Zero-bloat, lightweight append-only event store for Mobile, Windows, and Mesh nodes.
Features SHA-256 Idempotency Key registration and CQRS Read Projections.
"""

import os
import json
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from rae_contracts.maes import MinimumAuditableEvent, AuditableEventType, RiskClass, ExecutionMode


def compute_idempotency_key(
    tenant_id: str,
    project_id: str,
    trace_id: str,
    step_id: str,
    action: str,
    input_hash: str
) -> str:
    """Calculates deterministic SHA-256 idempotency key."""
    raw = f"{tenant_id}:{project_id}:{trace_id}:{step_id}:{action}:{input_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TaskStatusProjection(BaseModel):
    task_id: str
    last_event_type: AuditableEventType
    status: str
    event_count: int
    last_updated: str


class MAESEventStore:
    """
    Append-only lightweight EventStore.
    Persists events to disk as JSONL with SHA-256 idempotency deduplication
    and maintains CQRS read projections.
    """
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or "/tmp/rae_event_store.jsonl"
        self._lock = threading.Lock()
        self._idempotency_registry: Dict[str, str] = {}
        self._task_projections: Dict[str, TaskStatusProjection] = {}

    def append_event(self, event: MinimumAuditableEvent, idempotency_key: Optional[str] = None) -> tuple[bool, str]:
        """
        Appends event to store under thread lock.
        Rejects duplicate events matching an already processed idempotency key.
        """
        with self._lock:
            key = idempotency_key or compute_idempotency_key(
                tenant_id="default_tenant",
                project_id="rae_suite",
                trace_id=event.trace_id,
                step_id=str(event.sequence_no),
                action=event.action,
                input_hash=event.payload_hash
            )

            # Idempotency check
            if key in self._idempotency_registry:
                return False, f"DUPLICATE_EVENT_REJECTED: Idempotency key {key[:12]} already committed"

            self._idempotency_registry[key] = event.event_id

            # Write event to JSONL
            event_dict = event.model_dump(mode="json")
            with open(self.store_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")

            # Update CQRS Task Status Projection
            task_id = event.task_id or event.trace_id
            proj = self._task_projections.get(task_id)
            if proj:
                proj.last_event_type = event.event_type
                proj.status = "COMPLETED" if event.event_type == AuditableEventType.EVIDENCE_PACKED else "IN_PROGRESS"
                proj.event_count += 1
                proj.last_updated = event.timestamp.isoformat()
            else:
                self._task_projections[task_id] = TaskStatusProjection(
                    task_id=task_id,
                    last_event_type=event.event_type,
                    status="STARTED",
                    event_count=1,
                    last_updated=event.timestamp.isoformat()
                )

            return True, key

    def get_task_projection(self, task_id: str) -> Optional[TaskStatusProjection]:
        with self._lock:
            return self._task_projections.get(task_id)
