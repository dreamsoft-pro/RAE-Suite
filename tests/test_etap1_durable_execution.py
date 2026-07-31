import os
import pytest
from core.claim_check import ClaimCheckManager, ArtifactRef, RedactionStatus
from core.outbox import TransactionalOutbox
from core.safe_replay import SafeReplayEngine, ReplayMode


def test_claim_check_offloading(tmp_path):
    """ClaimCheckManager must offload payloads > 16 KiB and verify content SHA-256."""
    mgr = ClaimCheckManager(artifact_dir=str(tmp_path))

    # Small payload -> inline (False)
    small_payload = "hello world"
    is_offloaded, res_small = mgr.offload_if_needed(small_payload, "art_1", threshold_bytes=100)
    assert not is_offloaded
    assert res_small == small_payload

    # Large payload -> offloaded (True, ArtifactRef)
    large_payload = "A" * 200
    is_offloaded_large, res_ref = mgr.offload_if_needed(large_payload, "art_2", threshold_bytes=100)
    assert is_offloaded_large
    assert isinstance(res_ref, ArtifactRef)
    assert res_ref.size_bytes == 200

    # Retrieve and verify SHA-256
    retrieved = mgr.retrieve(res_ref)
    assert retrieved == large_payload


def test_transactional_outbox_staging_and_idempotency(tmp_path):
    """TransactionalOutbox must stage messages and reject duplicate idempotency keys."""
    db_file = os.path.join(tmp_path, "outbox.db")
    outbox = TransactionalOutbox(db_path=db_file)

    cmd_id = "cmd_100"
    idempotency_key = "idemp_sha256_unique_1"
    topic = "rae.events.task"
    payload = {"action": "pytest", "status": "PENDING"}

    # First staging -> Success
    ok1, msg1 = outbox.stage_command(cmd_id, idempotency_key, topic, payload)
    assert ok1
    assert msg1 == "STAGED_SUCCESS"

    # Duplicate staging -> Rejected
    ok2, msg2 = outbox.stage_command(cmd_id, idempotency_key, topic, payload)
    assert not ok2
    assert "DUPLICATE_IDEMPOTENCY_KEY" in msg2

    # Fetch pending
    pending = outbox.fetch_pending_messages(limit=10)
    assert len(pending) == 1
    assert pending[0].idempotency_key == idempotency_key


def test_safe_replay_engine_zero_side_effects():
    """SafeReplayEngine in AUDIT_READ_ONLY mode must execute ZERO side-effects."""
    engine_read = SafeReplayEngine(mode=ReplayMode.AUDIT_READ_ONLY)
    res_read = engine_read.replay_step("step_1", "git_commit", {"msg": "fix"})
    assert not res_read.side_effects_executed
    assert res_read.status == "REPLAY_READ_ONLY_COMPLETED"

    # Authorized mode without policy -> Rejected
    engine_exec = SafeReplayEngine(mode=ReplayMode.EXECUTE_AUTHORIZED)
    res_no_pol = engine_exec.replay_step("step_1", "git_commit", {"msg": "fix"}, policy_bundle_hash=None)
    assert not res_no_pol.side_effects_executed
    assert "REJECTED" in res_no_pol.status

    # Authorized mode with valid policy -> Success
    res_auth = engine_exec.replay_step("step_1", "git_commit", {"msg": "fix"}, policy_bundle_hash="sha256:pol12345")
    assert res_auth.side_effects_executed
    assert res_auth.status == "REPLAY_EXECUTE_SUCCESS"
