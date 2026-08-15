"""
RAE-Suite Dynamic Multi-Model Council & Pareto Optimization Selector
Supports hot-reloadable config (config/models_mesh_registry.yaml), dynamic market models
(DeepSeek-v4, Claude Fable 5, GPT-5.6 Sol, Luna Pro, Opus 4.8), Pareto Price-to-Quality score optimization,
and RAE Mesh node hardware dispatch (RTX 5000, RTX 4080, CPU).
"""

import os
import yaml
import time
import threading
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from rae_contracts import RiskClass
from core.rae_mesh import RAEMeshCluster, ClusterNodeInfo

logger = logging.getLogger(__name__)


class ModelDescriptor(BaseModel):
    model_name: str
    provider: str  # "local", "local_mesh", "antigravity_ultra", "openrouter"
    category: str  # "planning", "reasoning", "code_synthesis", "audit", "local_guard"
    cost_per_1k_input: float
    cost_per_1k_output: float
    avg_latency_ms: float
    quality_score: float  # 0.0 to 1.0
    supports_tools: bool = True
    assigned_node: str = "any"
    auth_method: str = "api_key"
    pareto_score: float = 0.0


class DynamicCouncilSelector:
    """
    Hot-reloadable, Pareto-optimized model selector for RAE-Suite.
    Dynamically balances cost (USD), latency (ms), and quality score with thread safety.
    """
    def __init__(self, config_path: str = "config/models_mesh_registry.yaml", antigravity_email: str = "grzegorz@cloud"):
        self.config_path = config_path
        self.antigravity_email = antigravity_email
        self.mesh_cluster = RAEMeshCluster()
        self.catalog: Dict[str, ModelDescriptor] = {}
        self.last_loaded_mtime: float = 0.0
        self._lock = threading.Lock()
        self.w_quality = 0.60
        self.w_cost = 0.25
        self.w_latency = 0.15
        self.reload_config()

    def reload_config(self, force: bool = False):
        """Hot-reloads config atomically under thread lock."""
        with self._lock:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file {self.config_path} not found. Using fallback in-memory catalog.")
                return

            mtime = os.path.getmtime(self.config_path)
            if not force and mtime <= self.last_loaded_mtime:
                return

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                settings = data.get("global_settings", {})
                self.w_quality = settings.get("pareto_weight_quality", 0.60)
                self.w_cost = settings.get("pareto_weight_cost", 0.25)
                self.w_latency = settings.get("pareto_weight_latency", 0.15)

                raw_models = data.get("models", {})
                new_catalog = {}

                for name, cfg in raw_models.items():
                    m_input = max(float(cfg.get("cost_input_1k", 0.0)), 0.0)
                    m_output = max(float(cfg.get("cost_output_1k", 0.0)), 0.0)
                    avg_cost_1k = (m_input + m_output) / 2.0
                    q_score = max(min(float(cfg.get("quality_score", 0.80)), 1.0), 0.0)
                    lat_ms = max(float(cfg.get("avg_latency_ms", 500.0)), 10.0)

                    lat_sec = lat_ms / 1000.0
                    cost_penalty = avg_cost_1k * 100.0
                    pareto = (self.w_quality * q_score) - (self.w_cost * cost_penalty) - (self.w_latency * (lat_sec / 10.0))

                    desc = ModelDescriptor(
                        model_name=cfg.get("model_name", name),
                        provider=cfg.get("provider", "openrouter"),
                        category=cfg.get("category", "general"),
                        cost_per_1k_input=m_input,
                        cost_per_1k_output=m_output,
                        avg_latency_ms=lat_ms,
                        quality_score=q_score,
                        supports_tools=cfg.get("supports_tools", True),
                        assigned_node=cfg.get("assigned_node", "any"),
                        auth_method=cfg.get("auth_method", f"email:{self.antigravity_email}" if cfg.get("provider") == "antigravity_ultra" else "api_key"),
                        pareto_score=round(pareto, 4)
                    )
                    new_catalog[name] = desc

                if new_catalog:
                    self.catalog = new_catalog
                    self.last_loaded_mtime = mtime
                    logger.info(f"DynamicCouncilSelector: Hot-reloaded {len(self.catalog)} models from {self.config_path}")

            except Exception as e:
                logger.error(f"Error reloading config {self.config_path}: {e}")

    def select_council_quorum(self, tier: int, risk_class: RiskClass) -> List[ModelDescriptor]:
        """
        Dynamically selects a 3-model quorum balancing Pareto score, local GPU nodes,
        Antigravity Ultra, and OpenRouter SOTA models (Fable 5, DeepSeek v4, Opus 4.8).
        """
        self.reload_config()

        # Sort all available models by Pareto score descending
        sorted_models = sorted(self.catalog.values(), key=lambda m: m.pareto_score, reverse=True)

        if tier == 1:
            # Tier 1 (L1 Guard): Local/Mesh + Antigravity Ultra + Top Pareto OpenRouter
            local_model = self._find_model_by_provider("local") or self._find_model_by_provider("local_mesh")
            ultra_model = self._find_model_by_provider("antigravity_ultra")
            top_openrouter = self._find_top_openrouter_model(sorted_models)

            quorum = [
                local_model or sorted_models[0],
                ultra_model or (sorted_models[1] if len(sorted_models) > 1 else sorted_models[0]),
                top_openrouter or (sorted_models[2] if len(sorted_models) > 2 else sorted_models[0])
            ]
            return quorum

        elif tier == 2:
            # Tier 2 (L2 Deep Audit): High Reasoning Models (DeepSeek-v4, GPT-5.6 Sol, Claude Opus 4.8)
            deepseek_v4 = self.catalog.get("deepseek/deepseek-v4")
            opus_48 = self.catalog.get("anthropic/claude-opus-4.8")
            gpt_sol = self.catalog.get("openai/gpt-5.6-sol")

            quorum = [
                deepseek_v4 or sorted_models[0],
                opus_48 or (sorted_models[1] if len(sorted_models) > 1 else sorted_models[0]),
                gpt_sol or (sorted_models[2] if len(sorted_models) > 2 else sorted_models[0])
            ]
            return quorum

        elif tier == 3:
            # Tier 3 (L3 Supreme Council / Planning): Claude Fable 5, DeepSeek-v4, Antigravity Ultra
            fable_5 = self.catalog.get("anthropic/claude-fable-5")
            deepseek_v4 = self.catalog.get("deepseek/deepseek-v4")
            ultra_model = self._find_model_by_provider("antigravity_ultra")

            quorum = [
                fable_5 or sorted_models[0],
                deepseek_v4 or (sorted_models[1] if len(sorted_models) > 1 else sorted_models[0]),
                ultra_model or (sorted_models[2] if len(sorted_models) > 2 else sorted_models[0])
            ]
            return quorum

        else:
            raise ValueError(f"Invalid Tribunal Tier: {tier}")

    def _find_model_by_provider(self, provider: str) -> Optional[ModelDescriptor]:
        for m in self.catalog.values():
            if m.provider == provider:
                return m
        return None

    def _find_top_openrouter_model(self, sorted_models: List[ModelDescriptor]) -> Optional[ModelDescriptor]:
        for m in sorted_models:
            if m.provider == "openrouter":
                return m
        return None
