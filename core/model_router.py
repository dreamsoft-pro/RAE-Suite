"""
RAE-Suite Dynamic ModelRouter Implementation
Features Token-Budget Quantile Routing, Cost-Quality Optimization,
and Modern OpenRouter/Local Model Registries.
"""

import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)


class QuantileMetrics(BaseModel):
    p50_ms: float = Field(..., description="p50 latency in ms")
    p95_ms: float = Field(..., description="p95 latency in ms")
    p99_ms: float = Field(..., description="p99 latency in ms")


class ModelProfile(BaseModel):
    model_name: str
    context_window: int
    provider: str
    is_local: bool
    cost_input_1k: float  # USD per 1,000 input tokens
    cost_output_1k: float  # USD per 1,000 output tokens
    quantiles: QuantileMetrics
    quality_score: float  # 0.0 to 1.0
    supports_json_schema: bool
    supports_tools: bool
    max_risk_class: RiskClass


class RouteBudget(BaseModel):
    max_cost_usd: float = Field(0.10, ge=0.0)
    max_input_tokens: int = Field(50000, ge=100)
    max_output_tokens: int = Field(4000, ge=10)
    deadline_ms: float = Field(10000.0, ge=100.0)


class RouteDecision(BaseModel):
    selected_model: str
    fallback_model: str
    estimated_cost_usd: float
    expected_latency_p95_ms: float
    rationale: str
    policy_version: str = "2.1-quantiles"


class ModelRouter:
    """
    Implements Token-Budget & Quantile Routing.
    Evaluates candidates against risk class, token bounds, and latency quantiles.
    """
    def __init__(self):
        self.registry: Dict[str, ModelProfile] = {}
        self._load_default_registry()

    def _load_default_registry(self):
        # OpenRouter / Remote High-Tier Reasoning Models
        self.registry["deepseek/deepseek-r1"] = ModelProfile(
            model_name="deepseek/deepseek-r1",
            context_window=64000,
            provider="openrouter",
            is_local=False,
            cost_input_1k=0.00055,
            cost_output_1k=0.00219,
            quantiles=QuantileMetrics(p50_ms=800.0, p95_ms=2500.0, p99_ms=4000.0),
            quality_score=0.96,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6,
        )

        self.registry["openai/gpt-5.6-luna-pro"] = ModelProfile(
            model_name="openai/gpt-5.6-luna-pro",
            context_window=128000,
            provider="openrouter",
            is_local=False,
            cost_input_1k=0.0020,
            cost_output_1k=0.0060,
            quantiles=QuantileMetrics(p50_ms=600.0, p95_ms=1800.0, p99_ms=3000.0),
            quality_score=0.95,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6,
        )

        self.registry["anthropic/claude-opus-4.8"] = ModelProfile(
            model_name="anthropic/claude-opus-4.8",
            context_window=200000,
            provider="openrouter",
            is_local=False,
            cost_input_1k=0.0030,
            cost_output_1k=0.0120,
            quantiles=QuantileMetrics(p50_ms=700.0, p95_ms=2000.0, p99_ms=3500.0),
            quality_score=0.97,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6,
        )

        self.registry["moonshotai/kimi-k3"] = ModelProfile(
            model_name="moonshotai/kimi-k3",
            context_window=128000,
            provider="openrouter",
            is_local=False,
            cost_input_1k=0.0010,
            cost_output_1k=0.0030,
            quantiles=QuantileMetrics(p50_ms=650.0, p95_ms=1900.0, p99_ms=3200.0),
            quality_score=0.94,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6,
        )

        # Local Models (Node 1 Lumina RTX 4080 & Laptop GPU)
        self.registry["SpeakLeash/bielik-11b-v3.0-instruct:Q5_K_M"] = ModelProfile(
            model_name="SpeakLeash/bielik-11b-v3.0-instruct:Q5_K_M",
            context_window=32768,
            provider="ollama",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            quantiles=QuantileMetrics(p50_ms=180.0, p95_ms=450.0, p99_ms=800.0),
            quality_score=0.92,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R4,
        )

        self.registry["qwen3.5:9b"] = ModelProfile(
            model_name="qwen3.5:9b",
            context_window=32768,
            provider="ollama",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            quantiles=QuantileMetrics(p50_ms=120.0, p95_ms=300.0, p99_ms=600.0),
            quality_score=0.89,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R3,
        )

        self.registry["deepseek-r1:8b"] = ModelProfile(
            model_name="deepseek-r1:8b",
            context_window=64000,
            provider="ollama",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            quantiles=QuantileMetrics(p50_ms=220.0, p95_ms=600.0, p99_ms=1200.0),
            quality_score=0.94,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R5,
        )

    def calculate_estimated_cost(self, profile: ModelProfile, input_tokens: int, output_tokens: int) -> float:
        return ((input_tokens / 1000.0) * profile.cost_input_1k) + ((output_tokens / 1000.0) * profile.cost_output_1k)

    def route_task(
        self,
        risk_class: RiskClass,
        expected_input_tokens: int = 5000,
        expected_output_tokens: int = 1000,
        budget: Optional[RouteBudget] = None,
    ) -> RouteDecision:
        """
        Calculates optimal model selection based on risk class, token estimates,
        and latency quantiles under budget constraints.
        """
        active_budget = budget or RouteBudget()

        eligible_candidates = []
        for name, profile in self.registry.items():
            # Check context window
            if expected_input_tokens + expected_output_tokens > profile.context_window:
                continue

            # Calculate cost
            cost = self.calculate_estimated_cost(profile, expected_input_tokens, expected_output_tokens)
            if cost > active_budget.max_cost_usd:
                continue

            # Check p95 latency deadline
            if profile.quantiles.p95_ms > active_budget.deadline_ms:
                continue

            eligible_candidates.append((cost, profile.quality_score, profile))

        if not eligible_candidates:
            # Fallback to local default if budget or deadline is tight
            local_profile = self.registry.get("llama-3.1-8b") or list(self.registry.values())[0]
            return RouteDecision(
                selected_model=local_profile.model_name,
                fallback_model="llama-3.1-8b",
                estimated_cost_usd=0.0,
                expected_latency_p95_ms=local_profile.quantiles.p95_ms,
                rationale="Fallback: No model satisfied strict budget/deadline constraints.",
            )

        # High risk requires high quality
        if risk_class in [RiskClass.R4, RiskClass.R5, RiskClass.R6]:
            # Sort primarily by quality_score descending, then cost ascending
            eligible_candidates.sort(key=lambda x: (-x[1], x[0]))
        else:
            # Sort primarily by cost ascending, then quality_score descending
            eligible_candidates.sort(key=lambda x: (x[0], -x[1]))

        selected = eligible_candidates[0][2]
        fallback = eligible_candidates[1][2].model_name if len(eligible_candidates) > 1 else "llama-3.1-8b"
        est_cost = self.calculate_estimated_cost(selected, expected_input_tokens, expected_output_tokens)

        return RouteDecision(
            selected_model=selected.model_name,
            fallback_model=fallback,
            estimated_cost_usd=est_cost,
            expected_latency_p95_ms=selected.quantiles.p95_ms,
            rationale=f"Selected {selected.model_name} for risk_class {risk_class} under cost ${est_cost:.5f}",
        )

    def get_tribunal_quorum_models(self, tier: int) -> List[str]:
        """Returns 3 models for Quality Tribunal quorum voting based on tier."""
        if tier == 1:
            return ["llama-3.1-8b", "openai/gpt-5.6-luna-pro", "moonshotai/kimi-k3"]
        elif tier == 2:
            return ["deepseek/deepseek-r1", "anthropic/claude-opus-4.8", "openai/gpt-5.6-luna-pro"]
        elif tier == 3:
            return ["deepseek/deepseek-r1", "anthropic/claude-opus-4.8", "moonshotai/kimi-k3"]
        else:
            raise ValueError(f"Unknown Quality Tribunal Tier: {tier}")
