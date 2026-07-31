"""
RAE-Suite Mesh & Hardware Cluster Node Manager
Manages hardware-aware routing across cluster nodes:
1. Node 0 (Local Laptop with RTX 5000)
2. Node 1 (Lumina Node with RTX 4080)
3. Node CPU (Thin Client / API Proxy)
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ClusterNodeInfo(BaseModel):
    node_id: str
    name: str
    has_cuda: bool
    vram_gb: float
    status: str = "online"
    capabilities: List[str] = Field(default_factory=list)


class RAEMeshCluster:
    """
    Manages node capabilities, CUDA availability, and task dispatching across RAE Mesh nodes.
    """
    def __init__(self):
        self.nodes: Dict[str, ClusterNodeInfo] = {}
        self._detect_and_register_nodes()

    def _detect_and_register_nodes(self):
        # Local Laptop Detection (RTX 5000)
        has_cuda_local = self._check_cuda_available()
        self.nodes["local_laptop"] = ClusterNodeInfo(
            node_id="node0_rtx5000",
            name="Laptop Primary (RTX 5000)",
            has_cuda=has_cuda_local,
            vram_gb=16.0 if has_cuda_local else 0.0,
            status="online",
            capabilities=["local_inference", "code_generation", "fast_audit"]
        )

        # Node 1 Lumina Detection (RTX 4080 - 100.68.166.117)
        self.nodes["node1_lumina"] = ClusterNodeInfo(
            node_id="node1_lumina_rtx4080",
            name="Node 1 Lumina (RTX 4080)",
            has_cuda=True,
            vram_gb=16.0,
            status="online",
            capabilities=["heavy_local_inference", "embeddings", "vector_search"]
        )

        # Thin CPU Node (No CUDA)
        self.nodes["cpu_node"] = ClusterNodeInfo(
            node_id="node_cpu_thin",
            name="CPU Thin Client",
            has_cuda=False,
            vram_gb=0.0,
            status="online",
            capabilities=["api_proxy", "light_orchestration"]
        )

    def _check_cuda_available(self) -> bool:
        try:
            import subprocess
            res = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0
        except Exception:
            return False

    def get_optimal_node_for_task(self, requires_gpu: bool, heavy_compute: bool = False) -> ClusterNodeInfo:
        """Selects the best available node based on GPU requirements and compute intensity."""
        if requires_gpu:
            if heavy_compute and "node1_lumina" in self.nodes and self.nodes["node1_lumina"].status == "online":
                return self.nodes["node1_lumina"]
            elif self.nodes["local_laptop"].has_cuda:
                return self.nodes["local_laptop"]
            elif self.nodes["node1_lumina"].status == "online":
                return self.nodes["node1_lumina"]

        # Default to CPU node or local laptop
        return self.nodes.get("cpu_node") or list(self.nodes.values())[0]
