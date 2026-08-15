"""
RAE Cluster Manager & Remote Compute Orchestration.
Integrates Node 1 (Lumina GPU Compute), Node 2 (Julka), and Node 3 (Piotrek Local LLM Inference).
"""

import asyncio
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import httpx
import yaml

logger = logging.getLogger("rae.cluster_manager")


class ClusterNode:
    def __init__(
        self,
        node_id: str,
        transport: str,
        host: Optional[str] = None,
        user: Optional[str] = None,
        url: Optional[str] = None,
        proxy_script: Optional[str] = None,
        description: str = "",
    ):
        self.node_id = node_id
        self.transport = transport
        self.host = host
        self.user = user
        self.url = url
        self.proxy_script = proxy_script
        self.description = description
        self.is_online = False
        self.last_checked = 0.0


class ClusterManager:
    """
    Manages connections and remote execution across RAE compute nodes:
    - Node 1: High-Performance GPU Node (i7-14700KF, RTX 4080, 64GB RAM, 100.68.166.117)
    - Node 3: Local LLM Inference Node (16 models, Ollama, 172.30.15.11:11434)
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.nodes: Dict[str, ClusterNode] = {}
        self._load_config()

    def _find_config_path(self) -> str:
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "cluster.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "packages", "rae-agentic-memory", "config", "cluster.yaml"),
            "/home/grzegorz/cloud/RAE-Suite/packages/rae-agentic-memory/config/cluster.yaml",
            "/home/grzegorz/cloud/config/cluster.yaml",
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)
        return candidates[0]

    def _load_config(self):
        if not os.path.exists(self.config_path):
            # Fallback default configuration
            self.nodes["node1"] = ClusterNode(
                node_id="node1",
                transport="ssh_mcp",
                host="100.68.166.117",
                user="operator",
                description="Node 1 (Lumina GPU Compute - RTX 4080)",
            )
            self.nodes["node3"] = ClusterNode(
                node_id="node3",
                transport="local_proxy",
                url="http://172.30.15.11:11434",
                proxy_script="infra/node_agent/ollama_proxy_mcp.py",
                description="Node 3 (Piotrek Inference - 16 Ollama Models)",
            )
            return

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        for nid, cfg in data.get("nodes", {}).items():
            self.nodes[nid] = ClusterNode(
                node_id=nid,
                transport=cfg.get("transport", "ssh_mcp"),
                host=cfg.get("host"),
                user=cfg.get("user"),
                url=cfg.get("url"),
                proxy_script=cfg.get("proxy_script"),
                description=cfg.get("description", f"Compute Node {nid}"),
            )

    async def check_node_health(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if not node:
            return False

        if node.transport == "ssh_mcp":
            cmd = f"ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no -o BatchMode=yes {node.user}@{node.host} 'exit 0'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            node.is_online = proc.returncode == 0
            return node.is_online

        elif node.transport == "local_proxy":
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(f"{node.url}/api/tags")
                    node.is_online = resp.status_code == 200
                    return node.is_online
            except Exception:
                node.is_online = False
                return False

        return False

    async def get_cluster_status(self) -> Dict[str, Any]:
        """Returns health status of all cluster nodes."""
        status = {}
        for nid in self.nodes:
            is_healthy = await self.check_node_health(nid)
            node = self.nodes[nid]
            status[nid] = {
                "id": nid,
                "online": is_healthy,
                "transport": node.transport,
                "host_or_url": node.host or node.url,
                "description": node.description,
            }
        return status

    async def list_node3_models(self) -> List[str]:
        """Fetches active model names from Node 3 (Ollama)."""
        node = self.nodes.get("node3")
        if not node or not node.url:
            return []

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{node.url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to fetch models from Node 3: {e}")
        return []

    async def execute_node1_command(self, command: str, timeout_seconds: int = 60) -> Tuple[int, str, str]:
        """Executes a remote command on Node 1 (Lumina) over SSH."""
        node = self.nodes.get("node1")
        if not node or not node.host:
            raise ValueError("Node 1 is not configured")

        ssh_cmd = (
            f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
            f"{node.user}@{node.host} '{command}'"
        )
        proc = await asyncio.create_subprocess_shell(
            ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            return (
                proc.returncode or 0,
                stdout_b.decode("utf-8", errors="replace"),
                stderr_b.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            proc.kill()
            return -1, "", f"Execution timed out after {timeout_seconds}s"


# Default cluster manager singleton
default_cluster_manager = ClusterManager()
