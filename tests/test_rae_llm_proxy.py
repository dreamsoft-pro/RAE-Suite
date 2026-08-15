"""
Unit & Integration tests for RAE Transparent LLM Proxy & Reasoning Gateway.
"""

import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services")))

from services.rae_llm_proxy import (
    app,
    accounting,
    calculate_cost_and_savings,
    resolve_tenant_and_actor,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rae-llm-proxy"
    assert "metrics" in data


def test_list_models_endpoint(client):
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0


def test_cost_and_savings_calculation():
    # Local model -> zero cost, positive savings
    cost, savings = calculate_cost_and_savings("llama3.1:8b", prompt_tokens=1000, completion_tokens=500, is_local=True)
    assert cost == 0.0
    assert savings > 0.0

    # Cloud model -> positive cost, zero savings
    cost_cloud, savings_cloud = calculate_cost_and_savings("openai/gpt-4o", prompt_tokens=1000, completion_tokens=500, is_local=False)
    assert cost_cloud > 0.0
    assert savings_cloud == 0.0


def test_accounting_record():
    accounting.record(
        tenant_id="test-tenant",
        model="deepseek/deepseek-r1",
        prompt_tokens=1000,
        completion_tokens=500,
        is_local=False,
        cost_usd=0.0015,
        savings_usd=0.0,
    )
    assert accounting.total_requests >= 1
    assert "test-tenant" in accounting.tenant_metrics
    assert accounting.tenant_metrics["test-tenant"]["cost_usd"] >= 0.0015
