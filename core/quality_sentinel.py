import os
import yaml
import uuid
import logging
from typing import Dict, Any, List, Optional
from rae_contracts import QualityStatus, QualityGateResult

logger = logging.getLogger(__name__)

class QualitySentinel:
    """
    Multi-Tier Quality Gate for RAE-Suite.
    Upgraded to enforce Constitutional AI principles (Anthropic approach).
    """
    def __init__(self, integrity_guard):
        self.integrity_guard = integrity_guard
        self.constitution_path = os.path.join(os.path.dirname(__file__), "constitution.yaml")
        self.principles = []
        self._load_constitution()

    def _load_constitution(self):
        try:
            if os.path.exists(self.constitution_path):
                with open(self.constitution_path, "r") as f:
                    config = yaml.safe_load(f)
                    self.principles = config.get("principles", [])
        except Exception as e:
            logger.error(f"failed_to_load_constitution: {e}")

    async def evaluate_quality(
        self, 
        trace_id: str, 
        original_test_code: str, 
        modified_test_code: str,
        metrics: Dict[str, Any]
    ) -> QualityGateResult:
        """
        Conducts a full quality audit including Constitutional validation.
        """
        logger.info("quality_audit_started", trace_id=trace_id)
        
        # 1. Test Integrity Check (AST)
        integrity_passed, violations = self.integrity_guard.verify_integrity(original_test_code, modified_test_code)
        
        # 2. Coverage Drift Check
        cov_before = metrics.get("coverage_before", 0.0)
        cov_after = metrics.get("coverage_after", 0.0)
        coverage_regression = cov_after < cov_before
        
        # 3. Static Vulnerability Scan
        critical_vulns = metrics.get("critical_vulns", 0)
        
        # 4. Constitutional AI Critique Checks (AST structural linting)
        patch_code = metrics.get("patch_code", "")
        critique_details = []
        if patch_code:
            critique_details = self.verify_ast_compliance(patch_code)
        constitutional_violations = len(critique_details)


        # Determine Final Status
        status = QualityStatus.APPROVED
        if not integrity_passed:
            status = QualityStatus.QUARANTINE
            logger.error(f"quality_violation_test_integrity: {violations}")
        elif constitutional_violations > 0:
            status = QualityStatus.REJECTED
            logger.warning(f"quality_violation_constitutional: {critique_details}")
        elif coverage_regression:
            status = QualityStatus.REJECTED
            logger.warning(f"quality_violation_coverage_drift: before={cov_before}, after={cov_after}")
        elif critical_vulns > 0:
            status = QualityStatus.REJECTED
            logger.error(f"quality_violation_vulnerabilities count={critical_vulns}")
        elif not metrics.get("tests_passed", False):
            status = QualityStatus.REJECTED
            logger.warning("quality_violation_tests_failed")

        result = QualityGateResult(
            id=f"gate-{uuid.uuid4()}",
            status=status,
            existing_tests_passed=metrics.get("tests_passed", False),
            coverage_before=cov_before,
            coverage_after=cov_after,
            critical_vulnerabilities=critical_vulns,
            test_integrity_passed=integrity_passed,
            mutation_score=metrics.get("mutation_score", 0.0),
            architecture_violations=constitutional_violations,
            report_uri=" | ".join(critique_details) if critique_details else None
        )
        
        logger.info("quality_audit_completed", trace_id=trace_id, status=status)
        return result

    def verify_ast_compliance(self, patch_code: str) -> List[str]:
        """
        Parses patch code into AST and inspects import statements and string literals
        for C1/C3/C6 violations. Ensures strict compliance with Silicon Oracle v7.0.
        """
        import ast
        violations = []

        # Clean git diff formatting if present
        clean_lines = []
        for line in patch_code.splitlines():
            if line.startswith("@@") or line.startswith("---") or line.startswith("+++") or line.startswith("diff "):
                continue
            if line.startswith("+ "):
                clean_lines.append(line[2:])
            elif line.startswith("+"):
                clean_lines.append(line[1:])
            elif line.startswith("-"):
                continue
            else:
                clean_lines.append(line)
        cleaned_code = "\n".join(clean_lines)

        try:
            tree = ast.parse(cleaned_code)
            for node in ast.walk(tree):
                # Check for imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "sentence_transformers":
                            violations.append("AST Violates C3: Forbidden import of sentence_transformers.")
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "sentence_transformers":
                        violations.append("AST Violates C3: Forbidden import of sentence_transformers.")
                
                # Check for string literals (absolute paths, drop table queries)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value
                    if any(path in val for path in ["/home/", "/etc/", "/usr/local/bin/"]):
                        violations.append(f"AST Violates C6: Found absolute filesystem path in string literal: '{val}'")
                    if any(sql in val.upper() for sql in ["DROP TABLE", "TRUNCATE TABLE", "DROP DATABASE"]):
                        violations.append(f"AST Violates C1: Found destructive database query in string literal: '{val}'")
        except SyntaxError as e:
            violations.append(f"AST Syntax Error: {e.msg} at line {e.lineno}")
        except Exception as e:
            violations.append(f"AST Parsing Error: {str(e)}")
        return violations

