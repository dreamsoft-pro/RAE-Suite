import pytest
from rae_contracts import RiskClass
from core.portal_hitl_approval import PortalHITLApprovalEngine


def test_hitl_approval_workflow_lifecycle():
    engine = PortalHITLApprovalEngine()
    req = engine.create_approval_request(
        target_module="rae-memory",
        action_name="purge_semantic_layer",
        risk_class=RiskClass.R4,
        requested_by="operator"
    )

    assert req.status == "PENDING"
    assert req.request_id != ""

    processed = engine.process_approval(
        request_id=req.request_id,
        approved=True,
        approver="grzegorz_admin",
        reason="Approved for maintenance"
    )

    assert processed.status == "APPROVED"
    assert processed.approved_by == "grzegorz_admin"


def test_iso_compliance_visualizer_report():
    engine = PortalHITLApprovalEngine()
    report = engine.get_iso_compliance_report()

    assert report.iso_27001_status == "COMPLIANT"
    assert report.iso_42001_status == "COMPLIANT"
    assert report.pii_redaction_coverage_pct == 100.0
    assert report.audit_chain_integrity == "VERIFIED_SHA256"
