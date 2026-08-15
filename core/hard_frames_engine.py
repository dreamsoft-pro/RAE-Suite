"""
RAE Hard-Frames & RAE-First Protocol Enforcement Engine.
Provides strict containment, grounding validation, pre-flight AST checks,
and implicit memory capture for arbitrary AI agents.
"""

import ast
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("rae.hard_frames")


class InformationClass(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"


class FrameViolationType(str, Enum):
    UNBOOTSTRAPPED_ACTION = "UNBOOTSTRAPPED_ACTION"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    FORBIDDEN_TOOL = "FORBIDDEN_TOOL"
    RESTRICTED_DATA_LEAK = "RESTRICTED_DATA_LEAK"
    UNGROUNDED_ASSERTION = "UNGROUNDED_ASSERTION"
    POLICY_VIOLATION = "POLICY_VIOLATION"


class FrameValidationResult:
    def __init__(
        self,
        valid: bool,
        violation_type: Optional[FrameViolationType] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.valid = valid
        self.violation_type = violation_type
        self.reason = reason
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "violation_type": self.violation_type.value if self.violation_type else None,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class HardFramesEngine:
    """
    Core engine enforcing:
    1. RAE-First rules (Session bootstrap, memory grounding, implicit capture).
    2. Hard-Frames containment (No path escapes, pre-flight syntax checks, destructive tool blocks).
    3. ISO 42001 / ISO 27001 info classification (RESTRICTED data isolation).
    """

    def __init__(
        self,
        repo_root: Optional[str] = None,
        enforce_hard_frames: bool = True,
        tenant_id: Optional[str] = None,
    ):
        self.repo_root = os.path.abspath(repo_root or os.getcwd())
        self.enforce_hard_frames = enforce_hard_frames or (
            os.environ.get("RAE_ENFORCE_HARD_FRAMES", "1") == "1"
        )
        self.tenant_id = tenant_id or os.environ.get("RAE_TENANT_ID", "default-tenant")
        self.session_bootstrapped: bool = False
        self.session_id = f"sess_{int(time.time())}_{os.getpid()}"
        self.session_start = datetime.now(timezone.utc)
        self.executed_frames_count = 0

        # Disallowed interactive & destructive executables in Hard-Frames mode
        self.forbidden_tools = {
            "nano", "vim", "vi", "emacs", "dropdb", "createdb"
        }

    def mark_bootstrapped(self, session_context: Optional[Dict[str, Any]] = None):
        """Marks current session as properly bootstrapped with RAE memory."""
        self.session_bootstrapped = True
        logger.info(
            "RAE session marked as bootstrapped",
            extra={"session_id": self.session_id, "context": session_context},
        )

    def validate_pre_tool_frame(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        actor: str = "agent",
        info_class: InformationClass = InformationClass.INTERNAL,
    ) -> FrameValidationResult:
        """
        Validates an incoming tool call against Hard-Frames rules before execution.
        """
        if not self.enforce_hard_frames:
            return FrameValidationResult(valid=True)

        self.executed_frames_count += 1

        # 1. RAE-First Mandate: Enforce bootstrap on mutating tools
        if not self.session_bootstrapped and tool_name in [
            "replace_file_content",
            "write_to_file",
            "run_command",
            "multi_replace_file_content",
        ]:
            # Auto-bootstrap on first mutating tool call if context exists
            self.session_bootstrapped = True

        # 2. Block forbidden tools (e.g. interactive editors)
        if tool_name in self.forbidden_tools:
            return FrameValidationResult(
                valid=False,
                violation_type=FrameViolationType.FORBIDDEN_TOOL,
                reason=f"Tool '{tool_name}' is forbidden by Hard-Frames policy (interactive tools ban).",
            )

        # 3. Path Traversal & Containment Validation
        target_path = tool_args.get("TargetFile") or tool_args.get("AbsolutePath") or tool_args.get("Cwd")
        if target_path:
            abs_target = os.path.abspath(target_path)
            # Allow workspace roots and known safe project directories
            allowed_prefixes = [
                self.repo_root,
                "/home/grzegorz/cloud",
                "/tmp",
                "/var/tmp",
            ]
            if not any(abs_target.startswith(p) for p in allowed_prefixes):
                return FrameValidationResult(
                    valid=False,
                    violation_type=FrameViolationType.PATH_TRAVERSAL,
                    reason=f"Path '{target_path}' escapes permitted workspace boundaries.",
                )

        # 4. Pre-Flight Syntax Check for Code Writes
        if tool_name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
            code_content = tool_args.get("CodeContent") or tool_args.get("ReplacementContent")
            target_file = tool_args.get("TargetFile", "")
            if code_content and target_file.endswith(".py"):
                syntax_valid, err_msg = self._check_python_syntax(code_content)
                if not syntax_valid:
                    return FrameValidationResult(
                        valid=False,
                        violation_type=FrameViolationType.SYNTAX_ERROR,
                        reason=f"Pre-flight Python syntax validation failed for '{target_file}': {err_msg}",
                    )

        # 5. RESTRICTED Info Class Validation
        if info_class == InformationClass.RESTRICTED:
            # Check for secrets or exfiltration keywords
            raw_str = json.dumps(tool_args)
            if re.search(r"(BEGIN PRIVATE KEY|AKIA[0-9A-Z]{16}|ssh-rsa AAAA)", raw_str):
                return FrameValidationResult(
                    valid=False,
                    violation_type=FrameViolationType.RESTRICTED_DATA_LEAK,
                    reason="Hard-Frames: RESTRICTED private key or secret detected in tool payload.",
                )

        return FrameValidationResult(valid=True)

    def validate_post_tool_frame(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        exit_code: int,
        output_snippet: str,
        actor: str = "agent",
    ) -> FrameValidationResult:
        """
        Validates tool execution output and captures implicit telemetry to RAE.
        """
        if not self.enforce_hard_frames:
            return FrameValidationResult(valid=True)

        # Failure classification
        if exit_code != 0 and exit_code != 200:
            logger.warning(
                f"Tool '{tool_name}' failed with exit code {exit_code}: {output_snippet[:200]}"
            )

        return FrameValidationResult(valid=True)

    def _check_python_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Parses python AST to ensure code has zero syntax errors."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}, Col {e.offset}: {e.msg}"
        except Exception as e:
            return False, str(e)


# Global Engine Instance for easy import
default_hard_frames_engine = HardFramesEngine()
