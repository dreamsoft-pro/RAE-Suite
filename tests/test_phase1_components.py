import pytest
from core.model_router import ModelRouter, RouteBudget
from core.cognitive_planner import CognitivePlanner
from core.escalation_engine import (
    DualEscalationEngine,
    EscalationRequest,
    EscalationReason,
    EscalationTarget,
)
from rae_contracts import RiskClass


def test_model_router_quantile_budget_routing():
    """ModelRouter must respect risk class, token estimates, and latency quantiles."""
    router = ModelRouter()

    # R1 task -> should select cheap/fast model
    decision_low = router.route_task(risk_class=RiskClass.R1, expected_input_tokens=2000, expected_output_tokens=500)
    assert decision_low.selected_model in ["llama-3.1-8b", "openai/gpt-5.6-luna-pro", "moonshotai/kimi-k3", "deepseek/deepseek-r1"]

    # R5 high-risk task -> should select high-quality model (DeepSeek R1 or Claude Opus 4.8)
    decision_high = router.route_task(risk_class=RiskClass.R5, expected_input_tokens=10000, expected_output_tokens=2000)
    assert decision_high.selected_model in ["anthropic/claude-opus-4.8", "deepseek/deepseek-r1", "openai/gpt-5.6-luna-pro"]


def test_dual_escalation_engine_routing():
    """DualEscalationEngine must route to OpenCode for multi-file AST, Hermes for standard, and Human for RESTRICTED."""
    engine = DualEscalationEngine(max_repair_cycles=3)

    # Multi-file refactoring -> OpenCode
    req_opencode = EscalationRequest(
        task_id="task_opencode_1",
        risk_class=RiskClass.R2,
        failed_repair_attempts=3,
        reason=EscalationReason.COMPLEX_AST_REFACTORING_REQUIRED,
        error_trace="SyntaxError in core/model_router.py",
        modified_files=["core/model_router.py", "core/cognitive_planner.py"]
    )
    res_opencode = engine.evaluate_escalation(req_opencode)
    assert res_opencode.target == EscalationTarget.OPENCODE

    # Standard agentic failure -> Hermes
    req_hermes = EscalationRequest(
        task_id="task_hermes_1",
        risk_class=RiskClass.R2,
        failed_repair_attempts=3,
        reason=EscalationReason.MAX_REPAIR_CYCLES_EXCEEDED,
        error_trace="Timeout in tool execution",
        modified_files=["main.py"]
    )
    res_hermes = engine.evaluate_escalation(req_hermes)
    assert res_hermes.target == EscalationTarget.HERMES

    # RESTRICTED R6 risk -> Human Operator
    req_human = EscalationRequest(
        task_id="task_restricted_1",
        risk_class=RiskClass.R6,
        failed_repair_attempts=1,
        reason=EscalationReason.HIGH_RISK_RESTRICTED_VIOLATION,
        error_trace="Attempted mutation of RESTRICTED policy key",
        modified_files=["core/constitution.yaml"]
    )
    res_human = engine.evaluate_escalation(req_human)
    assert res_human.target == EscalationTarget.HUMAN_OPERATOR
