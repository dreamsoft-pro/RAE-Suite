import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from core.layer_triad_runner import LayerTriadRunner


@pytest.fixture
def runner():
    return LayerTriadRunner(config_path="/home/grzegorz/cloud/RAE-Suite/config/layer_triads_registry.yaml")


def test_get_available_layers(runner):
    layers = runner.get_available_layers()
    assert "planning" in layers
    assert "architecture" in layers
    assert "implementation" in layers
    assert "quality_audit" in layers
    assert "performance_db" in layers


def test_get_layer_models(runner):
    models = runner.get_layer_models("planning")
    assert len(models) == 3
    model_names = [m["name"] for m in models]
    assert "deepseek/deepseek-r1" in model_names
    assert "anthropic/claude-3.7-sonnet" in model_names
    assert "openai/o3-mini" in model_names


@pytest.mark.asyncio
async def test_execute_layer_triad_mocked(runner):
    with patch.object(runner, "_call_single_model", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = [
            {"model": "m1", "role": "r1", "content": "Review 1", "prompt_tokens": 100, "completion_tokens": 50, "latency_ms": 300.0, "status": "SUCCESS"},
            {"model": "m2", "role": "r2", "content": "Review 2", "prompt_tokens": 120, "completion_tokens": 60, "latency_ms": 400.0, "status": "SUCCESS"},
            {"model": "m3", "role": "r3", "content": "Review 3", "prompt_tokens": 110, "completion_tokens": 55, "latency_ms": 350.0, "status": "SUCCESS"},
        ]

        result = await runner.execute_layer_triad(
            layer_name="planning",
            payload_text="Test proposal"
        )

        assert result["layer"] == "planning"
        assert len(result["models_executed"]) == 3
        assert len(result["reviews"]) == 3
        assert result["total_tokens"] == (100+50 + 120+60 + 110+55)
        assert result["decision"] == "COMPLETED"


@pytest.mark.asyncio
async def test_execute_layer_triad_with_overrides(runner):
    with patch.object(runner, "_call_single_model", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = [
            {"model": "custom/model-a", "role": "override_expert_1", "content": "Review A", "prompt_tokens": 100, "completion_tokens": 50, "latency_ms": 200.0, "status": "SUCCESS"},
            {"model": "custom/model-b", "role": "override_expert_2", "content": "Review B", "prompt_tokens": 100, "completion_tokens": 50, "latency_ms": 250.0, "status": "SUCCESS"},
            {"model": "custom/model-c", "role": "override_expert_3", "content": "Review C", "prompt_tokens": 100, "completion_tokens": 50, "latency_ms": 300.0, "status": "SUCCESS"},
        ]

        result = await runner.execute_layer_triad(
            layer_name="planning",
            payload_text="Test proposal",
            model_overrides=["custom/model-a", "custom/model-b", "custom/model-c"]
        )

        assert result["models_executed"] == ["custom/model-a", "custom/model-b", "custom/model-c"]
        assert len(result["reviews"]) == 3
