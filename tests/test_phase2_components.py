import pytest
from core.model_router import ModelRouter
from core.quality_tribunal import QualityTribunal
from core.risk_scanner import DynamicRiskScanner
from rae_contracts import RiskClass


def test_quality_tribunal_voting_thresholds():
    """Low risk requires majority, High risk requires unanimity."""
    router = ModelRouter()
    tribunal = QualityTribunal(router)

    # Clean code diff
    clean_diff = "+ def add(a, b):\n+     return a + b\n"
    
    # Low risk (R1) -> APPROVED
    res_low = tribunal.evaluate_code_change(clean_diff, risk_class=RiskClass.R1)
    assert res_low.decision == "APPROVE"
    assert not res_low.unanimity_required

    # High risk (R5) clean code -> APPROVED
    res_high = tribunal.evaluate_code_change(clean_diff, risk_class=RiskClass.R5)
    assert res_high.decision == "APPROVE"
    assert res_high.unanimity_required

    # High risk with forbidden import -> REJECTED
    forbidden_diff = "+ import sentence_transformers\n"
    res_forbidden = tribunal.evaluate_code_change(forbidden_diff, risk_class=RiskClass.R5)
    assert res_forbidden.decision == "REJECT"


def test_quality_tribunal_disqualification_on_hallucination():
    """Hallucinated AST symbol must disqualify judge vote."""
    router = ModelRouter()
    tribunal = QualityTribunal(router)

    hallucinated_diff = "+ x = hallucinated_symbol()\n"
    res = tribunal.evaluate_code_change(hallucinated_diff, risk_class=RiskClass.R2)
    assert res.votes[0].is_disqualified
    assert res.votes[0].disqualification_reason == "Hallucinated AST symbol detected"


def test_dynamic_risk_scanner():
    """DynamicRiskScanner must detect policy/destructive changes and escalate risk."""
    scanner = DynamicRiskScanner()

    # Standard clean diff -> R1
    res_clean = scanner.scan_diff("+ x = 1\n", touched_files=["main.py"])
    assert res_clean.computed_risk_class == RiskClass.R1
    assert not res_clean.is_restricted

    # Destructive SQL -> R5
    res_dest = scanner.scan_diff("+ DROP TABLE users;\n", touched_files=["db.py"])
    assert res_dest.computed_risk_class == RiskClass.R5
    assert res_dest.is_restricted

    # Constitution modification -> R5
    res_const = scanner.scan_diff("+ policy = True\n", touched_files=["core/constitution.yaml"])
    assert res_const.computed_risk_class == RiskClass.R5
    assert res_const.is_restricted
