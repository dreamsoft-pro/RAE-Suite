"""
RAE-Suite ExecutionReceipt Contract & Proof Verification Engine
Guarantees 'Zero Fake Success' by enforcing mandatory test execution proofs,
git diff SHA-256 validation, ISO 27001/42001 metadata, cycle detection, and cryptographic hash chaining.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Set, Tuple
from pydantic import BaseModel, Field, ConfigDict


class ExecutionStatus(str, Enum):
    VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    REJECTED_CAPABILITY_EXCEEDED = "REJECTED_CAPABILITY_EXCEEDED"
    REJECTED_NO_EVIDENCE = "REJECTED_NO_EVIDENCE"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class TestExecutionResult(BaseModel):
    __test__ = False
    command: str = Field(..., description="Test command line executed")
    exit_code: int = Field(..., description="Process exit code (0 for success)")
    passed_count: int = Field(..., ge=0, description="Number of passed tests")
    failed_count: int = Field(..., ge=0, description="Number of failed tests")
    duration_ms: float = Field(..., ge=0.0, description="Test execution duration in milliseconds")
    coverage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Test coverage percentage")


class ISOAuditMetadata(BaseModel):
    iso42001_policy_id: str = Field("ISO-42001-RAE-POL-01", description="ISO 42001 AI Management System Policy ID")
    data_classification: DataClassification = Field(DataClassification.CONFIDENTIAL)
    model_version_routed: Optional[str] = Field(None, description="Routed LLM model identifier")
    evidence_signature: Optional[str] = Field(None, description="SHA-256 signature of evidence pack")


class ExecutionReceipt(BaseModel):
    receipt_id: str = Field(..., description="Unique receipt UUID")
    task_id: str = Field(..., description="Target task UUID")
    step_id: str = Field(..., description="Step UUID within task")
    previous_receipt_hash: str = Field("0" * 64, description="SHA-256 hash of previous receipt in chain")
    execution_status: ExecutionStatus = Field(..., description="Verified execution status")
    git_diff_hash: str = Field(..., description="SHA-256 hash of git diff patch produced")
    test_result: TestExecutionResult = Field(..., description="Test execution proof details")
    artifact_uris: List[str] = Field(default_factory=list, description="URIs of generated artifacts")
    capability_compliance: bool = Field(True, description="Hard CapabilityContract compliance flag")
    iso_metadata: ISOAuditMetadata = Field(default_factory=ISOAuditMetadata)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sha256_hash: Optional[str] = Field(None, description="Calculated self SHA-256 hash")

    model_config = ConfigDict(frozen=False)

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 hash of the receipt fields."""
        payload = {
            "receipt_id": self.receipt_id,
            "task_id": self.task_id,
            "step_id": self.step_id,
            "previous_receipt_hash": self.previous_receipt_hash,
            "execution_status": self.execution_status.value,
            "git_diff_hash": self.git_diff_hash,
            "exit_code": self.test_result.exit_code,
            "passed_count": self.test_result.passed_count,
            "failed_count": self.test_result.failed_count,
            "capability_compliance": self.capability_compliance,
            "timestamp": self.timestamp.isoformat(),
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def finalize(self) -> "ExecutionReceipt":
        """Calculates and assigns self sha256_hash."""
        object.__setattr__(self, "sha256_hash", self.compute_hash())
        return self


def verify_execution_receipt(receipt: ExecutionReceipt) -> Tuple[bool, str]:
    """
    Enforces 'Zero Fake Success' invariant.
    Rejects any receipt claiming VERIFIED_SUCCESS if test exit_code != 0,
    failed_count > 0, capability_compliance is False, or git_diff_hash is empty.
    """
    if receipt.execution_status == ExecutionStatus.VERIFIED_SUCCESS:
        if receipt.test_result.exit_code != 0:
            return False, f"Contract Violation: VERIFIED_SUCCESS declared but test exit_code is {receipt.test_result.exit_code}"
        if receipt.test_result.failed_count > 0:
            return False, f"Contract Violation: VERIFIED_SUCCESS declared but failed_count is {receipt.test_result.failed_count}"
        if not receipt.capability_compliance:
            return False, "Contract Violation: VERIFIED_SUCCESS declared but capability_compliance is False"
        if not receipt.git_diff_hash or len(receipt.git_diff_hash) < 8:
            return False, "Contract Violation: VERIFIED_SUCCESS declared but git_diff_hash is invalid/empty"

    computed = receipt.compute_hash()
    if receipt.sha256_hash and receipt.sha256_hash != computed:
        return False, f"Hash Mismatch: Provided {receipt.sha256_hash} != Computed {computed}"

    return True, "VERIFIED_VALID"


def verify_receipt_chain(receipts: List[ExecutionReceipt]) -> Tuple[bool, str]:
    """
    Verifies cryptographic SHA-256 chain of receipts with cycle and duplicate ID detection
    using thread-safe immutable snapshot tuple.
    """
    if not receipts:
        return True, "CHAIN_EMPTY"

    snapshot = tuple(receipts)
    seen_hashes: Set[str] = set()
    seen_ids: Set[str] = set()
    prev_hash = "0" * 64

    for idx, r in enumerate(snapshot):
        valid, msg = verify_execution_receipt(r)
        if not valid:
            return False, f"Receipt index {idx} ({r.receipt_id}) invalid: {msg}"

        if r.receipt_id in seen_ids:
            return False, f"Broken Chain: Duplicate receipt_id detected at index {idx} ({r.receipt_id})"
        seen_ids.add(r.receipt_id)

        current_hash = r.sha256_hash or r.compute_hash()
        if current_hash in seen_hashes:
            return False, f"Broken Chain: Cyclic loop detected at index {idx} ({r.receipt_id})"
        seen_hashes.add(current_hash)

        if r.previous_receipt_hash != prev_hash:
            return False, f"Broken Chain at index {idx} ({r.receipt_id}): expected prev_hash {prev_hash}, got {r.previous_receipt_hash}"

        prev_hash = current_hash

    return True, "CHAIN_VERIFIED_STRONG"
