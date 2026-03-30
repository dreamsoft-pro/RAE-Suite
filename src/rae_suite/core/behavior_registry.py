from rae_core.models.behavior import DepartmentBehaviorContract
from typing import Dict, Optional

class BehaviorRegistry:
    def __init__(self):
        self._contracts: Dict[str, DepartmentBehaviorContract] = {}

    def register(self, contract: DepartmentBehaviorContract) -> None:
        self._contracts[contract.department] = contract

    def get(self, department: str) -> Optional[DepartmentBehaviorContract]:
        return self._contracts.get(department)
