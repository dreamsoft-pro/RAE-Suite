class CanaryManager:
    def rollout_canary(self, proposal_id: str, traffic_percent: float = 0.1):
        return {"proposal_id": proposal_id, "mode": "canary", "traffic": traffic_percent}
