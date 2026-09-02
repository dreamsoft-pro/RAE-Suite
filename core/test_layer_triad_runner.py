import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from core.layer_triad_runner import LayerTriadRunner


@pytest.fixture
def runner():
    return LayerTriadRunner(config_path="/home/grzegorz/cloud/RAE-Suite/config/layer_triads_registry.yaml")


def test_get_available_layers(runner):
    layers = runner.get_available_layers()
    assert "tier1_generate" in layers
    assert "tier2_review_repair" in layers
    assert "tier3_judge" in layers
    assert "local_gpu_triad" in layers


def test_3tier_models_registry(runner):
    # Tier 1
    t1 = runner.get_layer_models("tier1_generate")
    assert len(t1) == 3
    t1_names = [m["name"] for m in t1]
    assert "z-ai/glm-5.3-flash" in t1_names
    assert "deepseek/deepseek-v4-flash" in t1_names
    assert "xiaomi/mimo-v2.5" in t1_names

    # Tier 2
    t2 = runner.get_layer_models("tier2_review_repair")
    assert len(t2) == 3
    t2_names = [m["name"] for m in t2]
    assert "deepseek/deepseek-v4-pro-0813" in t2_names
    assert "z-ai/glm-5.3" in t2_names
    assert "moonshotai/kimi-k2.7-code" in t2_names

    # Tier 3
    t3 = runner.get_layer_models("tier3_judge")
    assert len(t3) == 3
    t3_names = [m["name"] for m in t3]
    assert "openai/gpt-5.6-sol" in t3_names
    assert "moonshotai/kimi-k3" in t3_names
    assert "anthropic/claude-sonnet-5" in t3_names


@pytest.mark.asyncio
async def test_execute_layer_triad_mocked(runner):
    with patch.object(runner, "_call_single_model", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = [
            {"model": "z-ai/glm-5.3-flash", "role": "primary_coder", "content": "Diff 1", "prompt_tokens": 100, "completion_tokens": 50, "cost_usd": 0.0001, "latency_ms": 300.0, "status": "SUCCESS"},
            {"model": "deepseek/deepseek-v4-flash", "role": "secondary_independent_coder", "content": "Diff 2", "prompt_tokens": 120, "completion_tokens": 60, "cost_usd": 0.0001, "latency_ms": 400.0, "status": "SUCCESS"},
            {"model": "xiaomi/mimo-v2.5", "role": "alternative_solution_coder", "content": "Diff 3", "prompt_tokens": 110, "completion_tokens": 55, "cost_usd": 0.0001, "latency_ms": 350.0, "status": "SUCCESS"},
        ]

        result = await runner.execute_layer_triad(
            layer_name="tier1_generate",
            payload_text="Generate CRUD patch"
        )

        assert result["layer"] == "tier1_generate"
        assert len(result["models_evaluated"]) == 3
        assert len(result["reviews"]) == 3
        assert result["total_tokens"] == (100+50 + 120+60 + 110+55)


@pytest.mark.asyncio
async def test_execute_3tier_cascade_mocked(runner):
    with patch.object(runner, "_call_single_model", new_callable=AsyncMock) as mock_call:
        # Mock 9 calls (3 per tier)
        mock_call.return_value = {
            "model": "mock-model",
            "role": "expert",
            "content": "Step output",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost_usd": 0.001,
            "latency_ms": 200.0,
            "status": "SUCCESS"
        }

        result = await runner.execute_3tier_cascade("Refactor calculator module")

        assert result["pipeline"] == "3_tier_cascade"
        assert "tier1_generate" in result
        assert "tier2_review_repair" in result
        assert "tier3_judge" in result
        assert result["total_tokens"] > 0
