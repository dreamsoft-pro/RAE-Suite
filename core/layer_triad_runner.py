"""
RAE-Suite Layer Triad Runner
Executes a 3-Model ensemble for any pipeline layer (planning, architecture, implementation, quality_audit, performance_db).
Supports hot-reloadable YAML configuration, dynamic task-level model overrides,
and automatic logging to the cryptographic ExecutionAuditLedger.
"""

import os
import time
import yaml
import httpx
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.audit_accounting import ExecutionAuditLedger

logger = logging.getLogger(__name__)


class LayerTriadRunner:
    """
    Orchestrates tri-model consensus executions across pipeline layers.
    """
    def __init__(self, config_path: str = "/home/grzegorz/cloud/RAE-Suite/config/layer_triads_registry.yaml"):
        self.config_path = Path(config_path)
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.ledger = ExecutionAuditLedger(ledger_file_path="/home/grzegorz/cloud/docs/RAE_COST_AND_AUDIT_LEDGER.jsonl")
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
        return list(cfg.get("layers", {}).keys())

    def get_layer_models(self, layer_name: str) -> List[Dict[str, Any]]:
        cfg = self._get_config()
        return cfg.get("layers", {}).get(layer_name, {}).get("models", [])

    async def _call_single_model(
        self,
        client: httpx.AsyncClient,
        model_cfg: Dict[str, Any],
        payload_text: str,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invokes a single model via OpenRouter API with timing and error isolation."""
        t0 = time.time()
        model_name = model_cfg.get("name", "unknown")
        role = model_cfg.get("role", "expert")
        temp = model_cfg.get("temperature", 0.1)
        provider = model_cfg.get("provider", "openrouter").lower()
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
                "X-Title": "RAE-Triad-Engine",
                "Content-Type": "application/json",
            }

        system_prompt = custom_system_prompt or f"You are acting as the {role} in a 3-model RAE engineering triad. Provide a rigorous, concise, technical assessment."

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
                content = data["choices"][0]["message"]["content"]
                return {
                    "model": model_name,
                    "role": role,
                    "content": content,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
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
        Executes all 3 models in the specified layer in parallel.
        Supports dynamic task-level overrides: model_overrides=['model1', 'model2', 'model3'].
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
            # Fallback default triad
            models_to_run = [
                {"name": "deepseek/deepseek-r1", "role": "concurrency_and_logic", "temperature": 0.1},
                {"name": "anthropic/claude-3.7-sonnet", "role": "architecture_and_types", "temperature": 0.1},
                {"name": "openai/gpt-4o", "role": "domain_and_dto", "temperature": 0.1},
            ]

        # Execute all models concurrently
        async with httpx.AsyncClient(timeout=120.0) as client:
            tasks = []
            for m_cfg in models_to_run:
                m_name = m_cfg.get("name", "")
                sys_prompt = custom_system_prompts.get(m_name) if custom_system_prompts else None
                tasks.append(self._call_single_model(client, m_cfg, payload_text, sys_prompt))

            results = await asyncio.gather(*tasks)

        # Calculate metrics & costs
        total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in results)
        total_completion_tokens = sum(r.get("completion_tokens", 0) for r in results)
        total_tokens = total_prompt_tokens + total_completion_tokens
        
        # Approximate blended cost
        estimated_cost_usd = round(total_prompt_tokens * 0.0000025 + total_completion_tokens * 0.000010, 6)
        max_latency_ms = max((r.get("latency_ms", 0.0) for r in results), default=0.0)

        # Record to RAE Audit Ledger (KTO, CO, DLACZEGO, KOSZT, EFEKT)
        successful_models = [r["model"] for r in results if r.get("status") == "SUCCESS"]
        decision_status = "COMPLETED" if len(successful_models) == len(results) else "PARTIAL_SUCCESS"

        self.ledger.record_invocation(
            model_name=f"triad_{layer_name}_3x",
            provider="openrouter",
            user_identity="antigravity_orchestrator",
            task_intent=f"Layer Triad: {layer_name}",
            rationale=f"3-model ensemble consensus for {layer_name}",
            decision=decision_status,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            cost_usd=estimated_cost_usd,
            latency_ms=max_latency_ms,
            quality_effect=f"{len(successful_models)}/{len(results)} model reviews gathered"
        )

        return {
            "layer": layer_name,
            "models_executed": [r["model"] for r in results],
            "reviews": results,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "max_latency_ms": max_latency_ms,
            "decision": decision_status
        }
