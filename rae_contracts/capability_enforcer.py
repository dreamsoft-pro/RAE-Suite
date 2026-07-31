"""
RAE-Suite CapabilityContract Hard Enforcement Engine
Performs pre-execution admission control to ensure no tool or agent action
exceeds memory, CPU, risk_class, or timeout limits BEFORE side-effects occur.
Thread-safe check-and-consume TOCTOU protection included.
"""

import threading
from enum import Enum
from typing import Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from rae_contracts.maes import RiskClass, ExecutionMode


class AdmissionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    DEFERRED = "DEFERRED"
    REJECTED_MEMORY_EXCEEDED = "REJECTED_MEMORY_EXCEEDED"
    REJECTED_CPU_EXCEEDED = "REJECTED_CPU_EXCEEDED"
    REJECTED_RISK_EXCEEDED = "REJECTED_RISK_EXCEEDED"
    REJECTED_UNAUTHORIZED_TOOL = "REJECTED_UNAUTHORIZED_TOOL"
    REJECTED_TIMEOUT_EXCEEDED = "REJECTED_TIMEOUT_EXCEEDED"
    REJECTED_TOKEN_ALREADY_USED = "REJECTED_TOKEN_ALREADY_USED"


class ResourceLimits(BaseModel):
    max_memory_mb: int = Field(512, ge=16, description="Maximum allowed RAM footprint in MB")
    max_cpu_percent: float = Field(80.0, ge=1.0, le=100.0, description="Maximum allowed CPU utilization percentage")
    max_execution_sec: int = Field(60, ge=1, description="Maximum allowed execution timeout in seconds")
    allowed_risk_classes: list[RiskClass] = Field(
        default_factory=lambda: [RiskClass.R0, RiskClass.R1, RiskClass.R2, RiskClass.R3],
        description="List of risk classes permitted for execution"
    )
    allowed_tools: list[str] = Field(default_factory=list, description="Allowlist of tool names")


class AdmissionRequest(BaseModel):
    action: str = Field(..., description="Action or tool requested to run")
    requested_memory_mb: int = Field(..., ge=1)
    requested_cpu_percent: float = Field(..., ge=0.0)
    requested_execution_sec: int = Field(..., ge=1)
    task_risk_class: RiskClass = Field(..., description="Risk class of active task")
    execution_mode: ExecutionMode = Field(ExecutionMode.LIVE)
    single_use_token: Optional[str] = Field(None, description="Optional single-use token to prevent TOCTOU replay attacks")


class AdmissionDecision(BaseModel):
    status: AdmissionStatus
    allowed: bool
    reason: str
    action: str
    limits_evaluated: ResourceLimits


class CapabilityEnforcer:
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self._lock = threading.Lock()
        self._consumed_tokens: Set[str] = set()

    def evaluate_admission(self, request: AdmissionRequest) -> AdmissionDecision:
        """
        Evaluates admission request BEFORE tool execution under thread lock.
        Prevents TOCTOU race conditions and single-use token replay attacks.
        """
        with self._lock:
            # Single-use token replay check
            if request.single_use_token:
                if request.single_use_token in self._consumed_tokens:
                    return AdmissionDecision(
                        status=AdmissionStatus.REJECTED_TOKEN_ALREADY_USED,
                        allowed=False,
                        reason=f"Single-use token '{request.single_use_token}' has already been consumed",
                        action=request.action,
                        limits_evaluated=self.limits
                    )

            # Tool allowlist check
            if self.limits.allowed_tools and request.action not in self.limits.allowed_tools:
                return AdmissionDecision(
                    status=AdmissionStatus.REJECTED_UNAUTHORIZED_TOOL,
                    allowed=False,
                    reason=f"Action '{request.action}' is not in allowed_tools list {self.limits.allowed_tools}",
                    action=request.action,
                    limits_evaluated=self.limits
                )

            # Risk class check
            if request.task_risk_class not in self.limits.allowed_risk_classes:
                return AdmissionDecision(
                    status=AdmissionStatus.REJECTED_RISK_EXCEEDED,
                    allowed=False,
                    reason=f"Task risk_class '{request.task_risk_class}' exceeds contract limit {self.limits.allowed_risk_classes}",
                    action=request.action,
                    limits_evaluated=self.limits
                )

            # Memory check
            if request.requested_memory_mb > self.limits.max_memory_mb:
                return AdmissionDecision(
                    status=AdmissionStatus.REJECTED_MEMORY_EXCEEDED,
                    allowed=False,
                    reason=f"Requested memory {request.requested_memory_mb}MB exceeds contract limit {self.limits.max_memory_mb}MB",
                    action=request.action,
                    limits_evaluated=self.limits
                )

            # CPU check
            if request.requested_cpu_percent > self.limits.max_cpu_percent:
                return AdmissionDecision(
                    status=AdmissionStatus.REJECTED_CPU_EXCEEDED,
                    allowed=False,
                    reason=f"Requested CPU {request.requested_cpu_percent}% exceeds contract limit {self.limits.max_cpu_percent}%",
                    action=request.action,
                    limits_evaluated=self.limits
                )

            # Timeout check
            if request.requested_execution_sec > self.limits.max_execution_sec:
                return AdmissionDecision(
                    status=AdmissionStatus.REJECTED_TIMEOUT_EXCEEDED,
                    allowed=False,
                    reason=f"Requested timeout {request.requested_execution_sec}s exceeds contract limit {self.limits.max_execution_sec}s",
                    action=request.action,
                    limits_evaluated=self.limits
                )

            # Atomically consume single-use token if provided
            if request.single_use_token:
                self._consumed_tokens.add(request.single_use_token)

            return AdmissionDecision(
                status=AdmissionStatus.ACCEPTED,
                allowed=True,
                reason="Admission granted under CapabilityContract limits",
                action=request.action,
                limits_evaluated=self.limits
            )
