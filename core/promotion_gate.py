from rae_core.models.improvement import ImprovementProposal, PromotionDecision
from typing import List
import logging

logger = logging.getLogger(__name__)

class PromotionGate:
    REQUIRED_GATES = [
        "has_shadow_run",
        "shadow_passed",
        "has_rollback_plan",
        "auditor_approved",
    ]

    def evaluate(self, proposal: ImprovementProposal, metrics: dict) -> PromotionDecision:
        failures = []
        for gate in self.REQUIRED_GATES:
            if not metrics.get(gate):
                failures.append(f"{gate}: Failed")
        
        if failures:
            return PromotionDecision(proposal_id=proposal.proposal_id, approved=False, reason="; ".join(failures))
        return PromotionDecision(proposal_id=proposal.proposal_id, approved=True, reason="All gates passed.")
