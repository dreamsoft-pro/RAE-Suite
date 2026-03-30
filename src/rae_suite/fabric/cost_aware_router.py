from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class CostAwareRouter:
    RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def route(self, capability_id: str, agents: List[dict], max_risk: str = "high") -> Optional[dict]:
        candidates = [a for a in agents if capability_id in a.get("capabilities", [])]
        
        allowed = [
            c for c in candidates 
            if self.RISK_ORDER.get(c.get("risk_class", "low"), 0) <= self.RISK_ORDER.get(max_risk, 2)
        ]

        if not allowed:
            return None

        # Lexicographical sort with inf fallback
        allowed.sort(key=lambda x: (
            self.RISK_ORDER.get(x.get("risk_class", "low"), 0),
            x.get("estimated_ncu", 0.0),
            x.get("failure_rate_30d", 0.0),
            x.get("latency_p50_s", float("inf"))
        ))

        return allowed[0]
