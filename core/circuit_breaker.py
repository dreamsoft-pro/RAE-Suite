"""
RAE-Suite Transport Circuit Breaker
Protects downstream services (LLMs, Memory API, Qdrant, Redis) from cascading failures.
State machine transitions: CLOSED -> OPEN -> HALF_OPEN.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from pydantic import BaseModel, Field


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class TransportCircuitBreaker:
    """
    Thread-safe state machine for Transport Circuit Breaker.
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout_s: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()
        self._lock = threading.Lock()

    def allow_execution(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change >= self.recovery_timeout_s:
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                    return True
                return False
            return True

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.last_state_change = time.time()

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()

    def execute(self, fn: Callable[[], Any]) -> tuple[bool, Any, Optional[str]]:
        """
        Executes function under Circuit Breaker guard.
        Returns (success, result, error_reason).
        """
        if not self.allow_execution():
            return False, None, f"CIRCUIT_BREAKER_OPEN: Requests blocked in {self.state} state"

        try:
            res = fn()
            self.record_success()
            return True, res, None
        except Exception as e:
            self.record_failure()
            return False, None, f"EXECUTION_FAILED: {str(e)}"
