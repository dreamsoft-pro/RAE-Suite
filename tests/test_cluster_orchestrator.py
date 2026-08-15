"""
Unit & Integration tests for RAE Cluster Manager.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.cluster_manager import ClusterManager, default_cluster_manager


@pytest.mark.asyncio
async def test_cluster_manager_status():
    status = await default_cluster_manager.get_cluster_status()
    assert "node1" in status
    assert "node3" in status
    assert status["node1"]["online"] is True
    assert status["node3"]["online"] is True


@pytest.mark.asyncio
async def test_node3_model_discovery():
    models = await default_cluster_manager.list_node3_models()
    assert isinstance(models, list)
    assert len(models) > 0
    # Should include one of the 16 installed models on Node 3
    assert any("llama" in m or "qwen" in m or "deepseek" in m for m in models)


@pytest.mark.asyncio
async def test_node1_remote_command_execution():
    exit_code, stdout, stderr = await default_cluster_manager.execute_node1_command("echo 'NODE1_HEALTHY'")
    assert exit_code == 0
    assert "NODE1_HEALTHY" in stdout
