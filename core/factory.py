from pydantic import BaseModel, Field
from typing import List, Dict
from rae_core.models.capabilities import AgentRegistration
from rae_core.models.economics import BudgetEnvelope

class FactorySpec(BaseModel):
    factory_id: str
    active_departments: List[str]
    agents: Dict[str, AgentRegistration]
    budgets: Dict[str, BudgetEnvelope]
    status: str = "operational"
