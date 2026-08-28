"""
RAE Transparent LLM Proxy & Reasoning Gateway.
Captures token usage, latency, intent, actor, and cost per tenant,
automatically writing receipts to RAE Episodic memory.
Supports OpenAI, OpenRouter, and Ollama (Node 3) protocols.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Dynamic RAE-Core Discovery
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAE_CORE_PATH = os.environ.get("RAE_CORE_PATH")
if not RAE_CORE_PATH:
    potential_path = os.path.join(SCRIPT_DIR, "..", "packages", "rae-agentic-memory", "rae-core")
    if os.path.exists(potential_path):
        RAE_CORE_PATH = potential_path

if RAE_CORE_PATH and RAE_CORE_PATH not in sys.path:
    sys.path.append(RAE_CORE_PATH)

try:
    from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation
except ImportError:
    RAE_Enterprise_Foundation = None

RAE_SUITE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if RAE_SUITE_DIR not in sys.path:
    sys.path.append(RAE_SUITE_DIR)

from core.cluster_manager import default_cluster_manager
from core.hard_frames_engine import default_hard_frames_engine

logger = logging.getLogger("rae.llm_proxy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="RAE Transparent LLM Proxy & Reasoning Gateway",
    version="3.0.0",
    description="Universal AI Agent Gateway with Automatic Multi-Tenant Telemetry & Hard-Frames Protection",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cost Table (USD per 1,000 tokens)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "deepseek/deepseek-r1": {"input": 0.00055, "output": 0.00219},
    "openai/gpt-5.6-luna-pro": {"input": 0.0020, "output": 0.0060},
    "openai/gpt-4o": {"input": 0.0025, "output": 0.0100},
    "anthropic/claude-opus-4.8": {"input": 0.0030, "output": 0.0120},
    "anthropic/claude-3-5-sonnet": {"input": 0.0030, "output": 0.0150},
    "default_cloud": {"input": 0.0015, "output": 0.0050},
    "local": {"input": 0.0, "output": 0.0},
}

NODE3_OLLAMA_URL = os.environ.get("NODE3_OLLAMA_URL", "http://172.30.15.11:11434")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


class TokenAccounting:
    def __init__(self):
        self.total_requests = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0
        self.total_savings_usd = 0.0
        self.tenant_metrics: Dict[str, Dict[str, Any]] = {}

    def record(
        self,
        tenant_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        is_local: bool,
        cost_usd: float,
        savings_usd: float,
    ):
        self.total_requests += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_usd += cost_usd
        self.total_savings_usd += savings_usd

        if tenant_id not in self.tenant_metrics:
            self.tenant_metrics[tenant_id] = {
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
                "savings_usd": 0.0,
            }

        tm = self.tenant_metrics[tenant_id]
        tm["requests"] += 1
        tm["prompt_tokens"] += prompt_tokens
        tm["completion_tokens"] += completion_tokens
        tm["cost_usd"] += cost_usd
        tm["savings_usd"] += savings_usd


accounting = TokenAccounting()


def resolve_tenant_and_actor(
    request: Request,
    x_tenant_id: Optional[str] = None,
    x_human_label: Optional[str] = None,
    x_agent_id: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Dynamically resolves tenant ID, human label, and agent actor ID."""
    tenant = (
        x_tenant_id
        or request.query_params.get("tenant")
        or request.headers.get("x-tenant")
        or request.headers.get("x-rae-tenant")
    )
    if not tenant:
        # Resolve via domain/path heuristic
        host = request.headers.get("host", "")
        if "printworks" in host:
            tenant = "printworks"
        elif "dreamsoft" in host:
            tenant = "dreamsoft"
        else:
            tenant = "default-tenant"

    human_label = (
        x_human_label
        or request.headers.get("x-human-label")
        or f"[{tenant.upper()}] Agent Operation"
    )

    agent_id = (
        x_agent_id
        or request.headers.get("user-agent", "").split("/")[0]
        or "universal-agent"
    )

    return tenant, human_label, agent_id


def calculate_cost_and_savings(
    model: str, prompt_tokens: int, completion_tokens: int, is_local: bool
) -> Tuple[float, float]:
    """Calculates dollar cost and token savings."""
    rates = MODEL_PRICING.get(model, MODEL_PRICING.get("default_cloud", {"input": 0.001, "output": 0.003}))
    cloud_cost = ((prompt_tokens / 1000.0) * rates["input"]) + ((completion_tokens / 1000.0) * rates["output"])

    if is_local:
        return 0.0, cloud_cost
    else:
        return cloud_cost, 0.0


async def log_to_rae_memory(
    tenant_id: str,
    human_label: str,
    agent_id: str,
    model: str,
    prompt_snippet: str,
    response_snippet: str,
    latency_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    savings_usd: float,
):
    """Implicitly records the interaction into RAE Episodic & Working memory."""
    if not RAE_Enterprise_Foundation:
        return

    try:
        foundation = RAE_Enterprise_Foundation(agent_id)
        metadata = {
            "source": "rae_llm_proxy",
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "model": model,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
            "savings_usd": savings_usd,
            "info_class": "INTERNAL",
            "governance": {
                "pattern_type": "llm_invocation",
                "fields": {
                    "model": model,
                    "tokens_total": prompt_tokens + completion_tokens,
                    "cost_usd": cost_usd,
                },
            },
        }
        foundation.bridge.save_event(
            content=f"LLM Call ({model}) | Prompt: {prompt_snippet[:300]}... | Resp: {response_snippet[:300]}...",
            human_label=human_label,
            layer="Episodic",
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Implicit RAE memory logging error: {e}")


@app.get("/health")
async def health_check():
    cluster_status = await default_cluster_manager.get_cluster_status()
    return {
        "status": "healthy",
        "service": "rae-llm-proxy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cluster": cluster_status,
        "metrics": {
            "total_requests": accounting.total_requests,
            "total_prompt_tokens": accounting.total_prompt_tokens,
            "total_completion_tokens": accounting.total_completion_tokens,
            "total_cost_usd": round(accounting.total_cost_usd, 6),
            "total_savings_usd": round(accounting.total_savings_usd, 6),
        },
    }


@app.get("/v1/models")
async def list_openai_models():
    """Returns available models including local Node 3 models and remote high-tier models."""
    node3_models = await default_cluster_manager.list_node3_models()
    models_data = [
        {"id": "deepseek/deepseek-r1", "object": "model", "owned_by": "openrouter"},
        {"id": "openai/gpt-5.6-luna-pro", "object": "model", "owned_by": "openrouter"},
        {"id": "anthropic/claude-opus-4.8", "object": "model", "owned_by": "openrouter"},
    ]
    for m in node3_models:
        models_data.append({"id": m, "object": "model", "owned_by": "ollama-node3"})
        models_data.append({"id": f"ollama/{m}", "object": "model", "owned_by": "ollama-node3"})

    return {"object": "list", "data": models_data}


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_human_label: Optional[str] = Header(None, alias="X-Human-Label"),
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
):
    """
    Universal OpenAI-compatible chat completions endpoint with automatic RAE-First tracking.
    """
    body = await request.json()
    model = body.get("model", "llama3.1:8b")
    messages = body.get("messages", [])
    stream = body.get("stream", False)

    tenant_id, human_label, agent_id = resolve_tenant_and_actor(
        request, x_tenant_id, x_human_label, x_agent_id
    )

    # 1. Hard-Frames Pre-Flight Check
    prompt_str = " ".join([m.get("content", "") for m in messages if isinstance(m.get("content"), str)])
    pre_check = default_hard_frames_engine.validate_pre_tool_frame(
        tool_name="llm_inference",
        tool_args={"model": model, "prompt_length": len(prompt_str)},
        actor=agent_id,
    )
    if not pre_check.valid:
        raise HTTPException(status_code=403, detail=f"Hard-Frames Block: {pre_check.reason}")

    start_time = time.time()
    clean_model = model.replace("ollama/", "")
    is_local = (
        clean_model.startswith("llama")
        or clean_model.startswith("qwen")
        or clean_model.startswith("deepseek")
        or clean_model.startswith("SpeakLeash")
        or clean_model.startswith("mistral")
        or clean_model.startswith("phi4")
    )

    # Forwarding to Node 3 (Ollama)
    if is_local:
        target_url = f"{NODE3_OLLAMA_URL}/v1/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                body["model"] = clean_model
                resp = await client.post(target_url, json=body)
                latency_ms = (time.time() - start_time) * 1000.0

                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)

                data = resp.json()
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", len(prompt_str) // 4)
                completion_tokens = usage.get("completion_tokens", 100)
                cost_usd, savings_usd = calculate_cost_and_savings(model, prompt_tokens, completion_tokens, is_local=True)

                accounting.record(tenant_id, model, prompt_tokens, completion_tokens, True, cost_usd, savings_usd)

                # Async implicit writeback to RAE
                response_snippet = ""
                if data.get("choices") and len(data["choices"]) > 0:
                    response_snippet = data["choices"][0].get("message", {}).get("content", "")

                asyncio.create_task(
                    log_to_rae_memory(
                        tenant_id, human_label, agent_id, model,
                        prompt_str, response_snippet, latency_ms,
                        prompt_tokens, completion_tokens, cost_usd, savings_usd
                    )
                )

                return data
        except Exception as e:
            logger.error(f"Error proxying to Node 3 Ollama: {e}")
            raise HTTPException(status_code=502, detail=f"Node 3 Ollama inference error: {e}")

    # Fallback to OpenRouter / Cloud
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers)
            latency_ms = (time.time() - start_time) * 1000.0
            data = resp.json()

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(prompt_str) // 4)
            completion_tokens = usage.get("completion_tokens", 100)
            cost_usd, savings_usd = calculate_cost_and_savings(model, prompt_tokens, completion_tokens, is_local=False)

            accounting.record(tenant_id, model, prompt_tokens, completion_tokens, False, cost_usd, savings_usd)

            response_snippet = ""
            if data.get("choices") and len(data["choices"]) > 0:
                response_snippet = data["choices"][0].get("message", {}).get("content", "")

            asyncio.create_task(
                log_to_rae_memory(
                    tenant_id, human_label, agent_id, model,
                    prompt_str, response_snippet, latency_ms,
                    prompt_tokens, completion_tokens, cost_usd, savings_usd
                )
            )

            return data
    except Exception as e:
        logger.error(f"Cloud LLM proxy error: {e}")
        raise HTTPException(status_code=502, detail=f"Cloud LLM gateway error: {e}")


@app.post("/api/chat")
async def ollama_chat(request: Request):
    """Native Ollama format endpoint forwarding to Node 3 with RAE telemetry."""
    body = await request.json()
    model = body.get("model", "llama3.1:8b")
    start_time = time.time()
    tenant_id, human_label, agent_id = resolve_tenant_and_actor(request)

    target_url = f"{NODE3_OLLAMA_URL}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(target_url, json=body)
            latency_ms = (time.time() - start_time) * 1000.0
            data = resp.json()

            prompt_tokens = data.get("prompt_eval_count", 50)
            completion_tokens = data.get("eval_count", 50)
            cost_usd, savings_usd = calculate_cost_and_savings(model, prompt_tokens, completion_tokens, is_local=True)
            accounting.record(tenant_id, model, prompt_tokens, completion_tokens, True, cost_usd, savings_usd)

            resp_msg = data.get("message", {}).get("content", "")
            asyncio.create_task(
                log_to_rae_memory(
                    tenant_id, human_label, agent_id, model,
                    str(body.get("messages", [])), resp_msg,
                    latency_ms, prompt_tokens, completion_tokens, cost_usd, savings_usd
                )
            )
            return data
    except Exception as e:
        logger.error(f"Ollama API proxy error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/tags")
async def ollama_tags():
    """Forward tags listing to Node 3 Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{NODE3_OLLAMA_URL}/api/tags")
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Cannot reach Node 3: {e}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("RAE_LLM_PROXY_PORT", "8002"))
    logger.info(f"Starting RAE Transparent LLM Proxy on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
