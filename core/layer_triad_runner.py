"""
RAE-Suite 3-Tier Multi-Model Consensus Engine
Implements the 3-Tier Architecture defined in models-for-rae.md:
- Tier I: Generate (GLM-5.3-Flash, DeepSeek-V4-Flash, MiMo-V2.5)
- Tier II: Review & Repair (DeepSeek-V4-Pro-0813, GLM-5.3, Kimi-K2.7-Code)
- Tier III: Judge & Consensus (GPT-5.6-Sol, Kimi-K3, Claude-Sonnet-5)
- Tier 0: Zero-Cost Local GPU (DeepSeek-R1-8B, Bielik-11B, Qwen-3.5-9B on Node 1 RTX 4080)
"""

import os
import sys
import time
import yaml
import httpx
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.audit_accounting import ExecutionAuditLedger

logger = logging.getLogger(__name__)


class LayerTriadRunner:
    """
    Orchestrates 3-Tier multi-model consensus and evaluation.
    """
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Dynamically resolve relative to this file
            default_path = Path(__file__).resolve().parent.parent / "config" / "layer_triads_registry.yaml"
            self.config_path = default_path if default_path.exists() else Path("/home/grzegorz/cloud/RAE-Suite/config/layer_triads_registry.yaml")

        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.ledger = ExecutionAuditLedger()
        self._last_mtime = 0.0
        self._cached_config: Dict[str, Any] = {}

    def _get_config(self) -> Dict[str, Any]:
        """Atomically hot-reloads configuration if modified on disk."""
        if not self.config_path.exists():
            logger.warning(f"Triad config file {self.config_path} not found. Returning empty dict.")
            return {}

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self._last_mtime:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._cached_config = yaml.safe_load(f) or {}
                self._last_mtime = current_mtime
                logger.info(f"LayerTriadRunner: Hot-reloaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to read triad config: {e}")
        return self._cached_config

    def get_available_layers(self) -> List[str]:
        cfg = self._get_config()
        tiers = list(cfg.get("tiers", {}).keys())
        layers = list(cfg.get("layers", {}).keys())
        # Return unique list
        return sorted(list(set(tiers + layers)))

    def get_layer_models(self, layer_name: str) -> List[Dict[str, Any]]:
        cfg = self._get_config()
        # 1. Check in tiers
        if layer_name in cfg.get("tiers", {}):
            return cfg["tiers"][layer_name].get("models", [])
        # 2. Check in layers (aliases)
        target = cfg.get("layers", {}).get(layer_name)
        if isinstance(target, str) and target in cfg.get("tiers", {}):
            return cfg["tiers"][target].get("models", [])
        elif isinstance(target, dict):
            return target.get("models", [])
        return []

    async def _call_single_model(
        self,
        client: httpx.AsyncClient,
        model_cfg: Dict[str, Any],
        payload_text: str,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invokes a single model with timing, pricing estimation, and error isolation."""
        t0 = time.time()
        model_name = model_cfg.get("name", "unknown")
        role = model_cfg.get("role", "expert")
        temp = model_cfg.get("temperature", 0.1)
        provider = model_cfg.get("provider", "openrouter").lower()
        cost_in_m = model_cfg.get("cost_input_per_m", 0.0)
        cost_out_m = model_cfg.get("cost_output_per_m", 0.0)

        if provider in ("node1_lumina", "node1", "local_gpu"):
            endpoint_url = "http://100.68.166.117:11434/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
        elif provider in ("local", "ollama"):
            endpoint_url = "http://localhost:11434/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
        else:
            endpoint_url = f"{self.openrouter_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://rae-suite.local",
                "X-Title": "RAE-3Tier-Engine",
                "Content-Type": "application/json",
            }

        system_prompt = custom_system_prompt or f"You are acting as the {role} in the 3-Tier RAE software engineering pipeline. Provide a rigorous, concise, high-quality assessment."

        body = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload_text}
            ],
            "temperature": temp,
        }

        try:
            resp = await client.post(endpoint_url, json=body, headers=headers)
            duration_ms = (time.time() - t0) * 1000

            if resp.status_code == 200:
                data = resp.json()
                usage = data.get("usage", {})
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                content = data["choices"][0]["message"]["content"]
                
                # Precise cost calculation
                cost_usd = (p_tokens * cost_in_m / 1_000_000.0) + (c_tokens * cost_out_m / 1_000_000.0)

                return {
                    "model": model_name,
                    "role": role,
                    "content": content,
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "cost_usd": round(cost_usd, 6),
                    "latency_ms": round(duration_ms, 2),
                    "status": "SUCCESS"
                }
            else:
                return {
                    "model": model_name,
                    "role": role,
                    "content": f"Error {resp.status_code}: {resp.text}",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost_usd": 0.0,
                    "latency_ms": round(duration_ms, 2),
                    "status": "ERROR"
                }
        except Exception as e:
            duration_ms = (time.time() - t0) * 1000
            return {
                "model": model_name,
                "role": role,
                "content": f"Exception: {str(e)}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
                "latency_ms": round(duration_ms, 2),
                "status": "EXCEPTION"
            }

    async def execute_layer_triad(
        self,
        layer_name: str,
        payload_text: str,
        model_overrides: Optional[List[str]] = None,
        custom_system_prompts: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes all 3 models in the specified tier/layer in parallel.
        """
        if not self.api_key:
            self.api_key = os.getenv("OPENROUTER_API_KEY", "")

        configured_models = self.get_layer_models(layer_name)

        if model_overrides and len(model_overrides) >= 1:
            models_to_run = [
                {"name": m, "role": f"override_expert_{i+1}", "temperature": 0.1, "weight": 1.0}
                for i, m in enumerate(model_overrides)
            ]
        elif configured_models:
            models_to_run = configured_models
        else:
            # Fallback default tier1 triad
            models_to_run = [
                {"name": "z-ai/glm-5.3-flash", "role": "primary_coder", "cost_input_per_m": 0.075, "cost_output_per_m": 0.25},
                {"name": "deepseek/deepseek-v4-flash", "role": "secondary_independent_coder", "cost_input_per_m": 0.05, "cost_output_per_m": 0.16},
                {"name": "xiaomi/mimo-v2.5", "role": "alternative_solution_coder", "cost_input_per_m": 0.119, "cost_output_per_m": 0.238},
            ]

        t0 = time.time()
        timeout = httpx.Timeout(120.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [
                self._call_single_model(
                    client=client,
                    model_cfg=m,
                    payload_text=payload_text,
                    custom_system_prompt=(custom_system_prompts or {}).get(m.get("name", ""))
                )
                for m in models_to_run
            ]
            results = await asyncio.gather(*tasks)

        total_latency_ms = (time.time() - t0) * 1000
        total_p_tokens = sum(r.get("prompt_tokens", 0) for r in results)
        total_c_tokens = sum(r.get("completion_tokens", 0) for r in results)
        total_tokens = total_p_tokens + total_c_tokens
        total_cost_usd = sum(r.get("cost_usd", 0.0) for r in results)

        # Synthesize consensus and identify disagreements/vetos
        successful_reviews = [r for r in results if r.get("status") == "SUCCESS"]
        synthesis = self._synthesize_reviews(layer_name, successful_reviews)

        # Record invocation in execution audit ledger
        self.ledger.record_invocation(
            model_name=f"triad_{layer_name}_3x",
            provider="openrouter",
            user_identity="antigravity_orchestrator",
            task_intent=f"Tier Triad: {layer_name}",
            rationale=f"3-model ensemble consensus for {layer_name}",
            decision="COMPLETED" if len(successful_reviews) >= 2 else "PARTIAL_SUCCESS",
            prompt_tokens=total_p_tokens,
            completion_tokens=total_c_tokens,
            cost_usd=total_cost_usd,
            latency_ms=total_latency_ms,
            quality_effect=f"{len(successful_reviews)}/{len(results)} model reviews gathered"
        )

        return {
            "layer": layer_name,
            "total_latency_ms": round(total_latency_ms, 2),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "models_evaluated": [r.get("model") for r in results],
            "reviews": results,
            "synthesis": synthesis
        }

    async def execute_3tier_cascade(self, task_text: str) -> Dict[str, Any]:
        """
        Executes the full 3-Tier Pipeline:
        Tier I (Generate) -> Tier II (Review/Repair) -> Tier III (Judge & Final Consensus)
        """
        t0 = time.time()
        logger.info("Executing 3-Tier Cascade: Tier I (Generate)...")
        tier1_res = await self.execute_layer_triad("tier1_generate", task_text)

        # Prepare Tier II input with Tier I proposals
        tier2_input = f"""### TASK TO ANALYZE AND REPAIR
{task_text}

### TIER I GENERATED PROPOSALS & CODE CANDIDATES:
{tier1_res.get('synthesis', '')}
"""
        logger.info("Executing 3-Tier Cascade: Tier II (Review & Repair)...")
        tier2_res = await self.execute_layer_triad("tier2_review_repair", tier2_input)

        # Prepare Tier III input with Tier II findings
        tier3_input = f"""### ORIGINAL TASK
{task_text}

### TIER II REPAIRED SOLUTION & DETECTED BUGS:
{tier2_res.get('synthesis', '')}
"""
        logger.info("Executing 3-Tier Cascade: Tier III (Judge & Final Consensus)...")
        tier3_res = await self.execute_layer_triad("tier3_judge", tier3_input)

        total_cost = (
            tier1_res.get("total_cost_usd", 0.0) +
            tier2_res.get("total_cost_usd", 0.0) +
            tier3_res.get("total_cost_usd", 0.0)
        )
        total_tokens = (
            tier1_res.get("total_tokens", 0) +
            tier2_res.get("total_tokens", 0) +
            tier3_res.get("total_tokens", 0)
        )
        total_latency = (time.time() - t0) * 1000

        return {
            "pipeline": "3_tier_cascade",
            "total_latency_ms": round(total_latency, 2),
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "tier1_generate": tier1_res,
            "tier2_review_repair": tier2_res,
            "tier3_judge": tier3_res,
            "final_verdict": tier3_res.get("synthesis", "")
        }

    def _synthesize_reviews(self, layer_name: str, reviews: List[Dict[str, Any]]) -> str:
        if not reviews:
            return "No successful model reviews gathered."
        
        parts = [f"### 🛡️ RAE 3-MODEL CONSENSUS SYNTHESIS ({layer_name.upper()})\n"]
        for r in reviews:
            parts.append(f"#### 👤 {r.get('model')} (Role: {r.get('role')})\n{r.get('content')}\n")
        return "\n".join(parts)
