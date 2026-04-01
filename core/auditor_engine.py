from rae_core.models.behavior import BehaviorSignal, BehaviorViolation, DepartmentBehaviorContract
from typing import List
import logging

logger = logging.getLogger(__name__)

class AuditorEngine:
    """
    Advanced behavioral analysis engine for RAE-Suite.
    Transforms raw agent signals into formal compliance violations.
    """
    
    def collect_behavior_signals(self, observed_payloads: list) -> List[BehaviorSignal]:
        """Maps heterogeneous runtime observations into structured BehaviorSignals."""
        result = []
        for p in observed_payloads:
            try:
                result.append(BehaviorSignal(**p))
            except Exception as e:
                logger.error(f"Failed to map signal payload: {e}")
        return result

    def evaluate_behavioral_contract(self, contract: DepartmentBehaviorContract, signals: List[BehaviorSignal]) -> List[BehaviorViolation]:
        """Evaluates structured signals against department-specific guarantees."""
        guarantee_ids = {g.guarantee_id for g in contract.guarantees if g.verifiable}
        violations = []
        for signal in signals:
            if signal.guarantee_id in guarantee_ids and signal.severity_hint != "low":
                violations.append(BehaviorViolation(
                    department=contract.department,
                    guarantee_id=signal.guarantee_id,
                    reason=signal.reason,
                    severity=signal.severity_hint,
                    source_signal_ids=[signal.signal_id]
                ))
        return violations
