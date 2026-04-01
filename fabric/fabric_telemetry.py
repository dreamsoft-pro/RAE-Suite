from datetime import datetime
from typing import Dict

class FabricTelemetry:
    def __init__(self):
        self.metrics: Dict[str, dict] = {}

    def record_call(self, capability_id: str, latency_ms: float, status: str):
        if capability_id not in self.metrics:
            self.metrics[capability_id] = {"calls": 0, "failures": 0, "avg_latency": 0.0}
        
        m = self.metrics[capability_id]
        m["avg_latency"] = (m["avg_latency"] * m["calls"] + latency_ms) / (m["calls"] + 1)
        m["calls"] += 1
        if status == "failure":
            m["failures"] += 1
