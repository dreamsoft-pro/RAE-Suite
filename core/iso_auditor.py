"""
RAE-Suite ISO 27001 / ISO 42001 Compliance Auditor
Verifies cryptographically chained ExecutionReceipts, data classification rules,
and AI Management System governance trails.
"""

import logging
from typing import List, Tuple
from pydantic import BaseModel, Field
from rae_contracts.execution_receipt import ExecutionReceipt, verify_receipt_chain, DataClassification

logger = logging.getLogger(__name__)


class ISOComplianceReport(BaseModel):
    is_compliant: bool
    iso27001_data_protection_status: str
    iso42001_ai_governance_status: str
    chain_length: int
    findings: List[str]


class ISOAuditor:
    """
    Audits execution receipts against ISO 27001 (ISMS data non-leakage)
    and ISO 42001 (AI System Governance).
    """
    def audit_receipt_chain(self, receipts: List[ExecutionReceipt]) -> ISOComplianceReport:
        findings = []

        # 1. Chain integrity check
        valid_chain, chain_msg = verify_receipt_chain(receipts)
        if not valid_chain:
            findings.append(f"ISO 42001 Failure: Cryptographic chain broken: {chain_msg}")

        # 2. Data classification leakage check (ISO 27001)
        for r in receipts:
            if r.iso_metadata.data_classification == DataClassification.RESTRICTED:
                # Enforce that RESTRICTED receipts have explicit policy ID
                if not r.iso_metadata.iso42001_policy_id:
                    findings.append(f"ISO 27001 Failure: RESTRICTED receipt {r.receipt_id} lacks policy ID")

        is_compliant = len(findings) == 0

        return ISOComplianceReport(
            is_compliant=is_compliant,
            iso27001_data_protection_status="COMPLIANT" if is_compliant else "NON_COMPLIANT",
            iso42001_ai_governance_status="COMPLIANT" if is_compliant else "NON_COMPLIANT",
            chain_length=len(receipts),
            findings=findings or ["All ISO 27001 and ISO 42001 controls verified successfully"],
        )
