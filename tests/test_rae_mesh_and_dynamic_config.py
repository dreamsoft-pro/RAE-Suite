import pytest
from rae_contracts import RiskClass
from core.rae_mesh import RAEMeshCluster
from core.dynamic_council import DynamicCouncilSelector


def test_rae_mesh_cluster_detects_nodes_and_hardware():
    cluster = RAEMeshCluster()
    assert "local_laptop" in cluster.nodes
    assert "node1_lumina" in cluster.nodes
    assert "cpu_node" in cluster.nodes

    # Test hardware-aware optimal node dispatching
    gpu_node = cluster.get_optimal_node_for_task(requires_gpu=True, heavy_compute=True)
    assert gpu_node.has_cuda
    assert "node1" in gpu_node.node_id or "node0" in gpu_node.node_id


def test_dynamic_council_hot_reloads_config_and_calculates_pareto():
    selector = DynamicCouncilSelector(config_path="config/models_mesh_registry.yaml")
    
    assert len(selector.catalog) > 0
    assert "anthropic/claude-fable-5" in selector.catalog
    assert "deepseek/deepseek-v4" in selector.catalog

    fable_5 = selector.catalog["anthropic/claude-fable-5"]
    assert fable_5.quality_score == 0.99
    assert fable_5.pareto_score != 0.0


def test_dynamic_council_selects_fable5_and_deepseek_v4_for_tier3():
    selector = DynamicCouncilSelector(config_path="config/models_mesh_registry.yaml")
    
    q3 = selector.select_council_quorum(tier=3, risk_class=RiskClass.R5)
    assert len(q3) == 3
    model_names = [m.model_name for m in q3]
    assert "anthropic/claude-fable-5" in model_names or "deepseek/deepseek-v4" in model_names
