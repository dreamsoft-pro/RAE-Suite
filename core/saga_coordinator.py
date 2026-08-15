"""
RAE-Suite Saga Coordinator & Compensation Engine
Executes multi-step distributed workflows. Automatically triggers backward
compensations ('compensate()') in reverse order upon step failure.
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SagaStepDefinition(BaseModel):
    step_id: str
    action: str
    idempotency_key: str


class SagaStepResult(BaseModel):
    step_id: str
    action: str
    success: bool
    error_message: Optional[str] = None


class SagaExecutionReport(BaseModel):
    saga_id: str
    status: str  # "COMPLETED", "COMPENSATED", "COMPENSATION_FAILED"
    executed_steps: List[SagaStepResult]
    compensated_steps: List[str]
    manual_intervention_required: bool = False


class SagaCoordinator:
    """
    Coordinates distributed Sagas with compensation rollbacks.
    Guarantees COMPENSATION_FAILED terminal state and manual intervention flag on compensation error.
    """
    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self._executed_steps: List[tuple[SagaStepDefinition, Callable[[], bool]]] = []

    def execute_saga(self, steps: List[tuple[SagaStepDefinition, Callable[[], bool], Callable[[], bool]]]) -> SagaExecutionReport:
        """
        Executes sequence of (step_def, execute_fn, compensate_fn).
        If execute_fn returns False or raises Exception, triggers backward compensation.
        """
        step_results = []

        for step_def, exec_fn, comp_fn in steps:
            try:
                ok = exec_fn()
                if ok:
                    self._executed_steps.append((step_def, comp_fn))
                    step_results.append(SagaStepResult(step_id=step_def.step_id, action=step_def.action, success=True))
                else:
                    step_results.append(SagaStepResult(step_id=step_def.step_id, action=step_def.action, success=False, error_message="Step execution failed"))
                    # Trigger backward compensation
                    compensated_step_ids, comp_failed = self._rollback_compensations()
                    status = "COMPENSATION_FAILED" if comp_failed else "COMPENSATED"
                    return SagaExecutionReport(
                        saga_id=self.saga_id,
                        status=status,
                        executed_steps=step_results,
                        compensated_steps=compensated_step_ids,
                        manual_intervention_required=comp_failed
                    )
            except Exception as e:
                step_results.append(SagaStepResult(step_id=step_def.step_id, action=step_def.action, success=False, error_message=str(e)))
                compensated_step_ids, comp_failed = self._rollback_compensations()
                status = "COMPENSATION_FAILED" if comp_failed else "COMPENSATED"
                return SagaExecutionReport(
                    saga_id=self.saga_id,
                    status=status,
                    executed_steps=step_results,
                    compensated_steps=compensated_step_ids,
                    manual_intervention_required=comp_failed
                )

        return SagaExecutionReport(
            saga_id=self.saga_id,
            status="COMPLETED",
            executed_steps=step_results,
            compensated_steps=[],
            manual_intervention_required=False
        )

    def _rollback_compensations(self) -> tuple[List[str], bool]:
        compensated = []
        has_failure = False
        for step_def, comp_fn in reversed(self._executed_steps):
            try:
                ok = comp_fn()
                if ok:
                    compensated.append(step_def.step_id)
                else:
                    has_failure = True
                    logger.error(f"Saga compensation returned False on step {step_def.step_id}")
                    compensated.append(f"{step_def.step_id}_COMPENSATION_FAILED")
            except Exception as e:
                has_failure = True
                logger.error(f"Saga compensation error on step {step_def.step_id}: {e}")
                compensated.append(f"{step_def.step_id}_COMPENSATION_FAILED")
        return compensated, has_failure
