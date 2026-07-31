import pytest
from datetime import datetime, timezone
from rae_contracts.execution_receipt import (
    ExecutionReceipt,
    TestExecutionResult,
    ExecutionStatus,
    ISOAuditMetadata,
    verify_execution_receipt,
    verify_receipt_chain,
)
from rae_contracts.capability_enforcer import (
    CapabilityEnforcer,
    AdmissionRequest,
    AdmissionStatus,
    ResourceLimits,
)
from rae_contracts.maes import RiskClass, ExecutionMode


def test_zero_fake_success_rejected_on_failed_test():
    """VERIFIED_SUCCESS declared but exit_code != 0 must be rejected."""
    receipt = ExecutionReceipt(
        receipt_id="rcpt_001",
        task_id="task_100",
        step_id="step_1",
        previous_receipt_hash="0" * 64,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="sha256:1234567890abcdef",
        test_result=TestExecutionResult(
            command="pytest tests/",
            exit_code=1,
            passed_count=10,
            failed_count=1,
            duration_ms=500.0,
        ),
        capability_compliance=True,
    ).finalize()

    valid, reason = verify_execution_receipt(receipt)
    assert not valid
    assert "exit_code is 1" in reason


def test_zero_fake_success_rejected_on_empty_diff():
    """VERIFIED_SUCCESS declared but git_diff_hash is empty must be rejected."""
    receipt = ExecutionReceipt(
        receipt_id="rcpt_002",
        task_id="task_100",
        step_id="step_2",
        previous_receipt_hash="0" * 64,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="",
        test_result=TestExecutionResult(
            command="pytest tests/",
            exit_code=0,
            passed_count=10,
            failed_count=0,
            duration_ms=500.0,
        ),
        capability_compliance=True,
    ).finalize()

    valid, reason = verify_execution_receipt(receipt)
    assert not valid
    assert "git_diff_hash is invalid/empty" in reason


def test_zero_fake_success_accepted_on_valid_proof():
    """VERIFIED_SUCCESS with passing tests and valid diff must be accepted."""
    receipt = ExecutionReceipt(
        receipt_id="rcpt_003",
        task_id="task_100",
        step_id="step_3",
        previous_receipt_hash="0" * 64,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="sha256:fedcba0987654321fedcba0987654321",
        test_result=TestExecutionResult(
            command="pytest tests/",
            exit_code=0,
            passed_count=15,
            failed_count=0,
            duration_ms=450.0,
        ),
        capability_compliance=True,
    ).finalize()

    valid, reason = verify_execution_receipt(receipt)
    assert valid
    assert reason == "VERIFIED_VALID"


def test_receipt_chain_verification_and_duplicate_detection():
    """Test valid chain and rejection of duplicate receipt IDs in chain."""
    r1 = ExecutionReceipt(
        receipt_id="rcpt_010",
        task_id="task_200",
        step_id="step_1",
        previous_receipt_hash="0" * 64,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="sha256:aaa111bbb222ccc333",
        test_result=TestExecutionResult(command="pytest", exit_code=0, passed_count=5, failed_count=0, duration_ms=100.0),
    ).finalize()

    r2 = ExecutionReceipt(
        receipt_id="rcpt_011",
        task_id="task_200",
        step_id="step_2",
        previous_receipt_hash=r1.sha256_hash,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="sha256:ddd444eee555fff666",
        test_result=TestExecutionResult(command="pytest", exit_code=0, passed_count=8, failed_count=0, duration_ms=120.0),
    ).finalize()

    valid, reason = verify_receipt_chain([r1, r2])
    assert valid
    assert reason == "CHAIN_VERIFIED_STRONG"

    # Duplicate receipt_id test (r1 -> r2 -> r1)
    valid_dup, reason_dup = verify_receipt_chain([r1, r2, r1])
    assert not valid_dup
    assert "Duplicate receipt_id detected" in reason_dup


def test_capability_enforcer_toctou_single_use_token():
    """CapabilityEnforcer must reject replayed single-use tokens under lock."""
    limits = ResourceLimits(
        max_memory_mb=256,
        max_cpu_percent=50.0,
        max_execution_sec=30,
        allowed_risk_classes=[RiskClass.R0, RiskClass.R1, RiskClass.R2],
        allowed_tools=["git", "pytest", "python3"]
    )
    enforcer = CapabilityEnforcer(limits)

    req1 = AdmissionRequest(
        action="pytest",
        requested_memory_mb=128,
        requested_cpu_percent=20.0,
        requested_execution_sec=10,
        task_risk_class=RiskClass.R1,
        single_use_token="token_unique_999"
    )

    # First attempt -> Accepted
    dec1 = enforcer.evaluate_admission(req1)
    assert dec1.allowed
    assert dec1.status == AdmissionStatus.ACCEPTED

    # Replay attempt -> Rejected
    dec2 = enforcer.evaluate_admission(req1)
    assert not dec2.allowed
    assert dec2.status == AdmissionStatus.REJECTED_TOKEN_ALREADY_USED
