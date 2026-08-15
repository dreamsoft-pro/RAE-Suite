"""
Unit tests for RAE Hard-Frames Engine & RAE-First Compliance.
"""

import pytest
import os
import sys

# Add core to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.hard_frames_engine import (
    HardFramesEngine,
    FrameViolationType,
    InformationClass,
)


@pytest.fixture
def engine(tmp_path):
    return HardFramesEngine(repo_root=str(tmp_path), enforce_hard_frames=True)


def test_hard_frames_blocks_forbidden_tools(engine):
    res = engine.validate_pre_tool_frame(tool_name="nano", tool_args={})
    assert not res.valid
    assert res.violation_type == FrameViolationType.FORBIDDEN_TOOL


def test_hard_frames_validates_python_syntax_error(engine):
    bad_code = "def broken_func(:\n    return 42"
    res = engine.validate_pre_tool_frame(
        tool_name="write_to_file",
        tool_args={"TargetFile": "/tmp/test.py", "CodeContent": bad_code},
    )
    assert not res.valid
    assert res.violation_type == FrameViolationType.SYNTAX_ERROR
    assert "syntax validation failed" in res.reason.lower()


def test_hard_frames_accepts_valid_python_code(engine):
    good_code = "def working_func():\n    return 42\n"
    res = engine.validate_pre_tool_frame(
        tool_name="write_to_file",
        tool_args={"TargetFile": "/tmp/test_good.py", "CodeContent": good_code},
    )
    assert res.valid
    assert res.violation_type is None


def test_hard_frames_blocks_path_traversal(engine):
    res = engine.validate_pre_tool_frame(
        tool_name="write_to_file",
        tool_args={"TargetFile": "/etc/shadow", "CodeContent": "dangerous"},
    )
    assert not res.valid
    assert res.violation_type == FrameViolationType.PATH_TRAVERSAL


def test_hard_frames_blocks_restricted_key_leak(engine):
    res = engine.validate_pre_tool_frame(
        tool_name="run_command",
        tool_args={"CommandLine": "echo '-----BEGIN PRIVATE KEY----- secret'"},
        info_class=InformationClass.RESTRICTED,
    )
    assert not res.valid
    assert res.violation_type == FrameViolationType.RESTRICTED_DATA_LEAK


def test_hard_frames_mark_bootstrapped(engine):
    assert not engine.session_bootstrapped
    engine.mark_bootstrapped({"tenant_id": "test-tenant"})
    assert engine.session_bootstrapped
