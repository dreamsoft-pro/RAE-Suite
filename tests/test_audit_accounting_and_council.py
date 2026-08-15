import pytest
from rae_contracts import RiskClass
from core.audit_accounting import ExecutionAuditLedger
from core.dynamic_council import DynamicCouncilSelector
from core.quality_tribunal import QualityTribunal


def test_audit_accounting_ledger_records_and_summarizes(tmp_path):
    ledger_file = tmp_path / "test_ledger.jsonl"
    ledger = ExecutionAuditLedger(ledger_file_path=str(ledger_file))

    r1 = ledger.record_invocation(
        model_name="openai/gpt-5.6-luna-pro",
        provider="openrouter",
        user_identity="api_key",
        task_intent="Code Review",
        rationale="Approved AST check",
        decision="APPROVE",
        prompt_tokens=1000,
        completion_tokens=200,
        cost_usd=0.0032,
        latency_ms=450.0,
        quality_effect="Passed AST"
    )

    assert r1.total_tokens == 1200
    assert r1.cryptographic_hash != ""

    summary = ledger.get_summary_stats()
    assert summary["total_invocations"] == 1
    assert summary["total_cost_usd"] == 0.0032
    assert summary["total_tokens_consumed"] == 1200


def test_dynamic_council_selector_provides_quorums():
    selector = DynamicCouncilSelector(antigravity_email="grzegorz@cloud")

    q1 = selector.select_council_quorum(tier=1, risk_class=RiskClass.R1)
    assert len(q1) == 3

    q3 = selector.select_council_quorum(tier=3, risk_class=RiskClass.R5)
    assert len(q3) == 3
    providers = [m.provider for m in q3]
    assert "openrouter" in providers or "antigravity_ultra" in providers


def test_quality_tribunal_evaluates_with_dynamic_council_and_accounting(tmp_path):
    ledger_file = tmp_path / "tribunal_ledger.jsonl"
    ledger = ExecutionAuditLedger(ledger_file_path=str(ledger_file))
    tribunal = QualityTribunal(audit_ledger=ledger)

    valid_diff = "def add(a: int, b: int) -> int:\n    return a + b"
    verdict = tribunal.evaluate_code_change(valid_diff, risk_class=RiskClass.R2, tier=1)

    assert verdict.decision == "APPROVE"
    assert len(verdict.votes) == 3
    assert verdict.total_cost_usd >= 0.0
    assert verdict.total_latency_ms > 0.0
    assert len(ledger.receipts) == 3
