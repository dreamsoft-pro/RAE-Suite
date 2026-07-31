"""
RAE-Suite Dual Escalation Engine (Hermes + OpenCode Engine)
Provides dual-path autonomous escalation when repair loops exceed budget
or require complex multi-file architectural refactoring.
"""

import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)


class EscalationTarget(str, Enum):
    HERMES = "HERMES"
    OPENCODE = "OPENCODE"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"


class EscalationReason(str, Enum):
    MAX_REPAIR_CYCLES_EXCEEDED = "MAX_REPAIR_CYCLES_EXCEEDED"
    COMPLEX_AST_REFACTORING_REQUIRED = "COMPLEX_AST_REFACTORING_REQUIRED"
    HIGH_RISK_RESTRICTED_VIOLATION = "HIGH_RISK_RESTRICTED_VIOLATION"
    CAPABILITY_EXCEEDED = "CAPABILITY_EXCEEDED"


class EscalationRequest(BaseModel):
    task_id: str
    risk_class: RiskClass
    failed_repair_attempts: int = Field(..., ge=0)
    reason: EscalationReason
    error_trace: str
    modified_files: List[str] = Field(default_factory=list)


class EscalationResult(BaseModel):
    escalation_id: str
    target: EscalationTarget
    status: str
    dispatch_payload: Dict[str, Any]
    message: str


class DualEscalationEngine:
    def __init__(self, max_repair_cycles: int = 3):
        self.max_repair_cycles = max_repair_cycles

    def evaluate_escalation(self, request: EscalationRequest) -> EscalationResult:
        """
        Routes escalation to Hermes (systemic/agent orchestrator) or
        OpenCode (deep multi-file code generator) based on task parameters.
        """
        escalation_id = f"esc_{request.task_id[:8]}_{request.failed_repair_attempts}"

        # If risk class is R5/R6 (RESTRICTED), require human operator sign-off
        if request.risk_class in [RiskClass.R5, RiskClass.R6]:
            return EscalationResult(
                escalation_id=escalation_id,
                target=EscalationTarget.HUMAN_OPERATOR,
                status="DISPATCHED_HUMAN_APPROVAL",
                dispatch_payload={"task_id": request.task_id, "risk_class": request.risk_class.value},
                message=f"Escalated to Human Operator due to RESTRICTED risk class {request.risk_class.value}",
            )

        # For code refactoring tasks with >1 modified files or AST complexity -> OpenCode
        if request.reason == EscalationReason.COMPLEX_AST_REFACTORING_REQUIRED or len(request.modified_files) > 1:
            return EscalationResult(
                escalation_id=escalation_id,
                target=EscalationTarget.OPENCODE,
                status="DISPATCHED_OPENCODE_ENGINE",
                dispatch_payload={
                    "task_id": request.task_id,
                    "engine": "opencode",
                    "files": request.modified_files,
                    "error_trace": request.error_trace[:500],
                },
                message="Escalated to OpenCode Engine for multi-file deep AST refactoring",
            )

        # Default escalation path -> Hermes agentic orchestrator
        return EscalationResult(
            escalation_id=escalation_id,
            target=EscalationTarget.HERMES,
            status="DISPATCHED_HERMES_ORCHESTRATOR",
            dispatch_payload={
                "task_id": request.task_id,
                "engine": "hermes",
                "repair_cycles": request.failed_repair_attempts,
            },
            message="Escalated to Hermes Agent Orchestrator for agentic resolution",
        )
