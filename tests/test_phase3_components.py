import os
import pytest
from datetime import datetime, timezone
from core.event_store import MAESEventStore, compute_idempotency_key
from core.iso_auditor import ISOAuditor
from rae_contracts.maes import MinimumAuditableEvent, AuditableEventType, RiskClass, ExecutionMode
from rae_contracts.execution_receipt import ExecutionReceipt, TestExecutionResult, ExecutionStatus, ISOAuditMetadata, DataClassification


def test_maes_event_store_append_and_idempotency(tmp_path):
    """EventStore must append events and reject duplicate idempotency keys."""
    store_file = os.path.join(tmp_path, "event_store.jsonl")
    store = MAESEventStore(store_path=store_file)

    event = MinimumAuditableEvent(
        event_id="evt_100",
        sequence_no=1,
        trace_id="trc_100",
        task_id="tsk_100",
        module_id="rae-hive",
        event_type=AuditableEventType.TASK_RECEIVED,
        risk_class=RiskClass.R1,
        execution_mode=ExecutionMode.LIVE,
        action="pytest",
        payload_hash="sha256:111222333444",
        policy_bundle_hash="sha256:policy123",
        signing_key_id="key_1",
        signature="sig_1",
        human_label="Task execution started"
    )

    key = compute_idempotency_key("tenant1", "proj1", "trc_100", "1", "pytest", "sha256:111222333444")

    # First append -> Success
    ok1, res1 = store.append_event(event, idempotency_key=key)
    assert ok1
    assert res1 == key

    # Duplicate append -> Rejected
    ok2, res2 = store.append_event(event, idempotency_key=key)
    assert not ok2
    assert "DUPLICATE_EVENT_REJECTED" in res2

    # Check projection
    proj = store.get_task_projection("tsk_100")
    assert proj is not None
    assert proj.event_count == 1


def test_iso_auditor_compliance_check():
    """ISOAuditor must verify cryptographic receipt chain and ISO metadata."""
    auditor = ISOAuditor()

    r1 = ExecutionReceipt(
        receipt_id="rcpt_iso_1",
        task_id="task_iso",
        step_id="step_1",
        previous_receipt_hash="0" * 64,
        execution_status=ExecutionStatus.VERIFIED_SUCCESS,
        git_diff_hash="sha256:abcd1234abcd1234",
        test_result=TestExecutionResult(command="pytest", exit_code=0, passed_count=5, failed_count=0, duration_ms=100.0),
        iso_metadata=ISOAuditMetadata(data_classification=DataClassification.CONFIDENTIAL, iso42001_policy_id="ISO-POL-1")
    ).finalize()

    report = auditor.audit_receipt_chain([r1])
    assert report.is_compliant
    assert report.iso27001_data_protection_status == "COMPLIANT"
    assert report.iso42001_ai_governance_status == "COMPLIANT"
