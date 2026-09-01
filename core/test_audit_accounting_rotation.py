import pytest
import os
import gzip
import json
from pathlib import Path
from core.audit_accounting import ExecutionAuditLedger


def test_audit_ledger_rotation_and_hash_chain(tmp_path):
    ledger_file = tmp_path / "test_ledger.jsonl"
    # Set low threshold (500 bytes) to force rotation after 2-3 receipts
    ledger = ExecutionAuditLedger(ledger_file_path=str(ledger_file), max_file_size_bytes=500)

    # 1. Record first invocation
    r1 = ledger.record_invocation(
        model_name="deepseek-r1:8b",
        provider="node1_lumina",
        user_identity="test_user",
        task_intent="Local AST evaluation",
        rationale="Local-first check",
        decision="COMPLETED",
        prompt_tokens=150,
        completion_tokens=50,
        cost_usd=0.0,
        latency_ms=45.0,
        quality_effect="0 violations"
    )
    assert r1.previous_hash == "0" * 64
    assert len(r1.cryptographic_hash) == 64

    # 2. Record second invocation
    r2 = ledger.record_invocation(
        model_name="claude-3.7-sonnet",
        provider="openrouter",
        user_identity="test_user",
        task_intent="Architecture review",
        rationale="Triad consensus",
        decision="APPROVE",
        prompt_tokens=2500,
        completion_tokens=800,
        cost_usd=0.012,
        latency_ms=850.0,
        quality_effect="Passed"
    )
    assert r2.previous_hash == r1.cryptographic_hash

    # 3. Record third invocation to trigger rotation (>500 bytes)
    r3 = ledger.record_invocation(
        model_name="gpt-4o",
        provider="openrouter",
        user_identity="test_user",
        task_intent="DTO validation",
        rationale="Triad consensus",
        decision="APPROVE",
        prompt_tokens=1500,
        completion_tokens=500,
        cost_usd=0.008,
        latency_ms=620.0,
        quality_effect="Passed"
    )
    assert r3.previous_hash == r2.cryptographic_hash

    # Check that gzip archives were created in tmp_path
    gz_files = list(tmp_path.glob("*.jsonl.gz"))
    assert len(gz_files) >= 1, f"Expected rotated .gz files, found {gz_files}"

    # Verify content of .gz archive
    with gzip.open(gz_files[0], "rt", encoding="utf-8") as f:
        content = f.read()
        assert "deepseek-r1:8b" in content or "claude-3.7-sonnet" in content
