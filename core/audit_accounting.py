"""
RAE-Suite Audit & Cost Accounting Engine
Tracks token costs, financial costs (USD), latency (ms), model rationales ("co kto dlaczego zrobił"),
and quality outcomes with cryptographic SHA-256 receipts.
"""

import time
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditCostReceipt(BaseModel):
    receipt_id: str
    timestamp: str
    model_name: str
    provider: str  # "local", "antigravity_ultra", "openrouter"
    user_identity: str  # e.g., "grzegorz@cloud" or "antigravity-ultra-email"
    task_intent: str
    rationale: str
    decision: str  # "APPROVE" / "REJECT" / "COMPLETED"
    
    # Financial & Performance Metrics
    prompt_tokens: int = Field(0, ge=0)
    completion_tokens: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    cost_usd: float = Field(0.0, ge=0.0)
    latency_ms: float = Field(0.0, ge=0.0)
    
    # Outcome & Quality Metrics
    quality_effect: str
    ast_violations_count: int = 0
    cryptographic_hash: str = ""


class ExecutionAuditLedger:
    """
    Persists comprehensive audit accounting logs for all model invocations,
    council decisions, token/USD costs, latencies, and rationale.
    """
    def __init__(self, ledger_file_path: str = "docs/RAE_COST_AND_AUDIT_LEDGER.jsonl"):
        self.ledger_file_path = ledger_file_path
        self.receipts: List[AuditCostReceipt] = []

    def record_invocation(
        self,
        model_name: str,
        provider: str,
        user_identity: str,
        task_intent: str,
        rationale: str,
        decision: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        latency_ms: float,
        quality_effect: str,
        ast_violations_count: int = 0
    ) -> AuditCostReceipt:
        total_tokens = prompt_tokens + completion_tokens
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        receipt_id = f"rcpt_{int(time.time() * 1000)}_{len(self.receipts)}"

        raw_payload = f"{receipt_id}:{timestamp}:{model_name}:{provider}:{decision}:{cost_usd}:{total_tokens}"
        crypto_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        receipt = AuditCostReceipt(
            receipt_id=receipt_id,
            timestamp=timestamp,
            model_name=model_name,
            provider=provider,
            user_identity=user_identity,
            task_intent=task_intent,
            rationale=rationale,
            decision=decision,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=round(cost_usd, 6),
            latency_ms=round(latency_ms, 2),
            quality_effect=quality_effect,
            ast_violations_count=ast_violations_count,
            cryptographic_hash=crypto_hash
        )

        self.receipts.append(receipt)
        self._append_to_file(receipt)
        logger.info(f"AuditLedger: Recorded invocation for {model_name} (Cost: ${cost_usd:.6f}, Tokens: {total_tokens}, Latency: {latency_ms:.2f}ms)")
        return receipt

    def _append_to_file(self, receipt: AuditCostReceipt):
        try:
            with open(self.ledger_file_path, "a", encoding="utf-8") as f:
                f.write(receipt.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to append receipt to audit ledger file {self.ledger_file_path}: {e}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates total financial cost, tokens, latencies across all invocations."""
        total_usd = sum(r.cost_usd for r in self.receipts)
        total_tokens = sum(r.total_tokens for r in self.receipts)
        avg_latency = (sum(r.latency_ms for r in self.receipts) / len(self.receipts)) if self.receipts else 0.0

        return {
            "total_invocations": len(self.receipts),
            "total_cost_usd": round(total_usd, 6),
            "total_tokens_consumed": total_tokens,
            "average_latency_ms": round(avg_latency, 2),
            "models_used": list(set(r.model_name for r in self.receipts))
        }
