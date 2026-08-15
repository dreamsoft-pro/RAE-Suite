import pytest
from core.redis_broker import RedisStreamsBroker, PriorityClass
from core.saga_coordinator import SagaCoordinator, SagaStepDefinition


def test_redis_broker_priority_and_dlq():
    """RedisStreamsBroker must prioritize CRITICAL over NORMAL and transfer to DLQ after max_deliveries."""
    broker = RedisStreamsBroker(max_deliveries=2)

    # Publish NORMAL first, then CRITICAL
    ok1, id1 = broker.publish("topic.normal", PriorityClass.NORMAL, "idemp_norm_1", {"data": "1"})
    ok2, id2 = broker.publish("topic.critical", PriorityClass.CRITICAL, "idemp_crit_1", {"data": "2"})
    assert ok1 and ok2

    # Duplicate publish -> Rejected
    ok_dup, err_dup = broker.publish("topic.normal", PriorityClass.NORMAL, "idemp_norm_1", {"data": "1"})
    assert not ok_dup
    assert "DUPLICATE_IDEMPOTENCY_KEY" in err_dup

    # Fetch next -> Must yield CRITICAL first
    msg1 = broker.fetch_next()
    assert msg1 is not None
    assert msg1.priority == PriorityClass.CRITICAL

    # Test DLQ on repeated NACK
    broker.nack_and_retry(msg1, "error_1")  # attempt 1
    broker.nack_and_retry(msg1, "error_2")  # attempt 2 -> DLQ
    assert len(broker.dlq) == 1
    assert broker.dlq[0].idempotency_key == "idemp_crit_1"


def test_saga_coordinator_success_and_compensation():
    """SagaCoordinator must execute steps in order, and rollback via compensate_fn on failure."""
    saga = SagaCoordinator("saga_100")
    state = {"worktree_created": False, "patch_applied": False}

    s1_def = SagaStepDefinition(step_id="step_1", action="create_worktree", idempotency_key="idemp_s1")
    def s1_exec():
        state["worktree_created"] = True
        return True
    def s1_comp():
        state["worktree_created"] = False
        return True

    s2_def = SagaStepDefinition(step_id="step_2", action="apply_patch", idempotency_key="idemp_s2")
    def s2_exec():
        # Fails!
        return False
    def s2_comp():
        state["patch_applied"] = False
        return True

    steps = [
        (s1_def, s1_exec, s1_comp),
        (s2_def, s2_exec, s2_comp),
    ]

    report = saga.execute_saga(steps)
    assert report.status == "COMPENSATED"
    assert "step_1" in report.compensated_steps
    assert not state["worktree_created"]

def test_redis_broker_poison_message_rejection():
    """RedisStreamsBroker must reject non-dict poison payloads before processing."""
    broker = RedisStreamsBroker()
    ok, err = broker.publish("topic.test", PriorityClass.NORMAL, "idemp_poison", "corrupt_string_payload")  # type: ignore
    assert not ok
    assert "POISON_MESSAGE_REJECTED" in err


def test_saga_coordinator_compensation_failed_terminal_state():
    """SagaCoordinator must enter COMPENSATION_FAILED state and set manual_intervention_required when compensation fails."""
    saga = SagaCoordinator("saga_fault_1")

    s1_def = SagaStepDefinition(step_id="step_1", action="create_db", idempotency_key="idemp_fault1")
    def s1_exec():
        return True
    def s1_comp():
        # Compensation itself crashes!
        raise RuntimeError("DB connection lost during rollback")

    s2_def = SagaStepDefinition(step_id="step_2", action="seed_data", idempotency_key="idemp_fault2")
    def s2_exec():
        return False
    def s2_comp():
        return True

    steps = [
        (s1_def, s1_exec, s1_comp),
        (s2_def, s2_exec, s2_comp),
    ]

    report = saga.execute_saga(steps)
    assert report.status == "COMPENSATION_FAILED"
    assert report.manual_intervention_required
    assert "step_1_COMPENSATION_FAILED" in report.compensated_steps
