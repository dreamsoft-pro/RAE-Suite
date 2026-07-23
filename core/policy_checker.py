import os
import yaml
import uuid
import logging
from datetime import datetime, timezone
from rae_contracts import RiskClass, RiskAssessment, DecisionType

logger = logging.getLogger(__name__)

class PolicyChecker:
    def __init__(self):
        self.active_policy_bundle_hash = "sbx-default-policy-v7.0"

    def check_compliance(self, risk_assessment: RiskAssessment) -> bool:
        # Check reasons for explicit violations of C1 to C6 constitution principles
        for reason in risk_assessment.reasons:
            if any(violation in reason for violation in [
                "Violates C1", "Violates C2", "Violates C3", "Violates C4", "Violates C5", "Violates C6",
                "RESTRICTED data processed outside Working layer"
            ]):
                return False
        return True

    def evaluate_policy(self, risk_assessment: RiskAssessment) -> DecisionType:
        if risk_assessment.risk_class == RiskClass.R6:
            logger.warning(f"Policy evaluation QUARANTINE due to R6 risk class for trace {risk_assessment.trace_id}")
            return DecisionType.QUARANTINE

        # Compliance check denies non-compliant actions for R5, R4 or lower
        if not self.check_compliance(risk_assessment):
            logger.warning(f"Policy evaluation DENIED due to compliance failure for trace {risk_assessment.trace_id}")
            return DecisionType.DENY

        if risk_assessment.risk_class in [RiskClass.R4, RiskClass.R5]:
            logger.info(f"Policy evaluation NEEDS_APPROVAL due to R4/R5 risk class for trace {risk_assessment.trace_id}")
            return DecisionType.NEEDS_APPROVAL
            
        return DecisionType.ALLOW


class RiskClassifier:
    """
    Central Risk Classifier for RAE-Suite.
    Upgraded to utilize constitution.yaml principles for evaluation.
    """
    def __init__(self):
        self.constitution_path = os.path.join(os.path.dirname(__file__), "constitution.yaml")
        self.principles = []
        self._load_constitution()

    def _load_constitution(self):
        try:
            if os.path.exists(self.constitution_path):
                with open(self.constitution_path, "r") as f:
                    config = yaml.safe_load(f)
                    self.principles = config.get("principles", [])
            else:
                logger.warning("constitution_not_found_using_fallback")
        except Exception as e:
            logger.error(f"failed_to_load_constitution: {e}")

    def assess_risk(self, trace_id: str, intent: str, payload: dict) -> RiskAssessment:
        intent_lower = intent.lower()
        reasons = []
        risk_class = RiskClass.R0
        
        # 1. Check RESTRICTED data isolation principle
        info_class = (payload.get("information_class") or payload.get("info_class") or "").lower()
        memory_layer = (payload.get("memory_layer") or payload.get("layer") or "").lower()
        
        if info_class == "restricted" and memory_layer != "working":
            risk_class = RiskClass.R6
            reasons.append("Violates C6 (Relative Project Paths Only / Layer Isolation): RESTRICTED data processed outside Working layer is forbidden.")

        # Cross-reference with Constitutional principles
        # C1: Do no harm to production data
        elif any(kw in intent_lower for kw in ["delete all", "drop database", "expose secret", "steal keys", "bypass policy", "truncate"]):
            risk_class = RiskClass.R6
            reasons.append("Violates C1 (Do no harm to production data): Prohibited destructive action.")
            
        # C2: Latency & C3: Explicit code & C6: Absolute paths
        elif any(kw in intent_lower for kw in ["infrastructure", "prod-deploy", "rotate secret", "access credentials"]):
            risk_class = RiskClass.R5
            reasons.append("High-risk infrastructure operation flagged under C2/C3 guidance.")
            
        elif any(kw in intent_lower for kw in ["database schema", "alembic migrate", "restart container", "scale pods"]):
            risk_class = RiskClass.R4
            reasons.append("System topology modification requiring formal change control.")
            
        elif any(kw in intent_lower for kw in ["pull request", "merge request", "commit to develop", "push to main"]):
            risk_class = RiskClass.R3
            reasons.append("Code promotion operation triggering dynamic MCTS branch planning.")
            
        elif any(kw in intent_lower for kw in ["refactor code", "apply patch", "fix bug", "modify file", "write tool"]):
            risk_class = RiskClass.R2
            reasons.append("Local workspace code modification.")
            
        elif any(kw in intent_lower for kw in ["run test", "lint check", "execute script", "simulation"]):
            risk_class = RiskClass.R1
            reasons.append("Sterile sandbox execution.")
            
        else:
            risk_class = RiskClass.R0
            reasons.append("Sterile read-only operations.")

        # Match constitutional keywords if loaded
        for principle in self.principles:
            desc_keywords = [word.lower() for word in principle["name"].split() if len(word) > 3]
            if any(kw in intent_lower for kw in desc_keywords):
                reasons.append(f"Intent matched principle {principle['id']}: {principle['name']}")

        assessment = RiskAssessment(
            id=f"risk-{uuid.uuid4()}",
            trace_id=trace_id,
            risk_class=risk_class,
            confidence=0.98,
            reasons=reasons,
            requires_human_review=(risk_class in [RiskClass.R4, RiskClass.R5, RiskClass.R6]),
            assessed_at=datetime.now(timezone.utc)
        )
        
        logger.info("risk_assessed_v7", trace_id=trace_id, risk_class=risk_class, id=assessment.id)
        return assessment
