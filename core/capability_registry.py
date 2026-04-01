from rae_core.models.capabilities import AgentRegistration
from typing import Dict, Optional

class CapabilityRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentRegistration] = {}

    def register(self, reg: AgentRegistration):
        self._agents[reg.agent_id] = reg

    def get_by_dept(self, department: str) -> Optional[AgentRegistration]:
        return next((a for a in self._agents.values() if a.department == department), None)
