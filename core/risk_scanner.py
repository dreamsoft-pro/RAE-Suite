"""
RAE-Suite Dynamic Risk Scanner
Analyzes git diff patch, touched file paths, and target tools to compute
RiskClass (R0 to R6) dynamically before execution.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)


class RiskScanResult(BaseModel):
    computed_risk_class: RiskClass
    confidence: float
    risk_factors: List[str]
    is_restricted: bool


class DynamicRiskScanner:
    """
    Computes RiskClass dynamically based on static code analysis, git diff scope,
    and planned tool capabilities.
    """
    def scan_diff(self, git_diff: str, touched_files: Optional[List[str]] = None, planned_tools: Optional[List[str]] = None) -> RiskScanResult:
        files = touched_files or []
        tools = planned_tools or []
        factors = []
        
        score = 1  # Base R1

        # Check for constitution/policy file modifications
        if any("constitution" in f.lower() or "policy" in f.lower() for f in files):
            score = max(score, 5)  # R5
            factors.append("Modification of core Policy/Constitution files")

        # Check for security/auth file modifications
        if any("auth" in f.lower() or "secret" in f.lower() or "key" in f.lower() for f in files):
            score = max(score, 4)  # R4
            factors.append("Modification of security/authentication files")

        # Check for destructive SQL or shell actions
        diff_upper = git_diff.upper()
        if any(kw in diff_upper for kw in ["DROP TABLE", "TRUNCATE", "DROP DATABASE", "RM -RF /"]):
            score = max(score, 5)  # R5
            factors.append("Destructive database or filesystem command detected")

        # Check for tool capability risks
        if any(t in tools for t in ["bash_exec", "sudo", "docker_push"]):
            score = max(score, 4)  # R4
            factors.append("Privileged execution tool requested")

        # High volume diff lines
        lines_changed = len(git_diff.splitlines())
        if lines_changed > 500:
            score = max(score, 3)  # R3
            factors.append(f"Large diff scope ({lines_changed} lines)")

        risk_map = {
            0: RiskClass.R0,
            1: RiskClass.R1,
            2: RiskClass.R2,
            3: RiskClass.R3,
            4: RiskClass.R4,
            5: RiskClass.R5,
            6: RiskClass.R6,
        }
        computed = risk_map.get(score, RiskClass.R3)

        return RiskScanResult(
            computed_risk_class=computed,
            confidence=0.92,
            risk_factors=factors or ["Standard low-risk code modification"],
            is_restricted=computed in [RiskClass.R5, RiskClass.R6],
        )
