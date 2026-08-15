import time
import pytest
from rae_contracts import RiskClass
from core.a2a_protocol import A2AProtocolAdapter, A2AAgentMessage
from core.keycloak_auth import KeycloakAuthGateway


def test_a2a_protocol_registration_and_message_delivery():
    adapter = A2AProtocolAdapter()
    adapter.register_agent("rae-supervisor", ["orchestrate", "audit"], RiskClass.R1)
    adapter.register_agent("rae-memory", ["save_memory", "search_memory"], RiskClass.R1)

    msg = A2AAgentMessage(
        message_id="msg_001",
        sender_agent_id="rae-supervisor",
        recipient_agent_id="rae-memory",
        capability_token="cap_token_123",
        intent="save_memory",
        payload={"key": "test_fact", "content": "Memory content"},
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        nonce="nonce_unique_001"
    )
    msg.signature = adapter.sign_message(msg)

    res = adapter.send_a2a_message(msg)
    assert res["status"] == "DELIVERED"
    assert res["verified"] is True


def test_a2a_protocol_replay_attack_rejection():
    adapter = A2AProtocolAdapter()
    adapter.register_agent("rae-supervisor", ["orchestrate"])
    adapter.register_agent("rae-memory", ["save_memory"])

    msg = A2AAgentMessage(
        message_id="msg_replay",
        sender_agent_id="rae-supervisor",
        recipient_agent_id="rae-memory",
        capability_token="cap_token_123",
        intent="save_memory",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        nonce="nonce_replay_test"
    )
    msg.signature = adapter.sign_message(msg)

    # First send succeeds
    adapter.send_a2a_message(msg)

    # Replay with same nonce fails
    with pytest.raises(ValueError, match="Replay attack detected"):
        adapter.send_a2a_message(msg)


def test_a2a_protocol_unregistered_agent_rejection():
    adapter = A2AProtocolAdapter()
    adapter.register_agent("rae-supervisor", ["orchestrate"])

    msg = A2AAgentMessage(
        message_id="msg_002",
        sender_agent_id="rae-supervisor",
        recipient_agent_id="unregistered_agent",
        capability_token="cap_token_123",
        intent="query",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

    with pytest.raises(ValueError, match="is not registered"):
        adapter.send_a2a_message(msg)


def test_keycloak_auth_gateway_jwt_verification_and_capability():
    gateway = KeycloakAuthGateway()
    token = gateway.create_mock_jwt(
        username="grzegorz",
        roles=["admin", "developer"],
        scopes=["a2a:execute", "memory:write"]
    )

    claims = gateway.verify_token(token)
    assert claims.preferred_username == "grzegorz"
    assert "admin" in claims.roles

    assert gateway.authorize_capability(token, "a2a:execute", min_role="developer")
    assert not gateway.authorize_capability(token, "forbidden:capability", min_role="developer")


def test_keycloak_auth_gateway_audience_mismatch_rejection():
    gateway = KeycloakAuthGateway()
    token = gateway.create_mock_jwt(
        username="grzegorz",
        roles=["user"],
        scopes=["read"],
        aud=["other-client"]
    )

    with pytest.raises(ValueError, match="Audience mismatch"):
        gateway.verify_token(token, expected_aud="rae-suite-client")
