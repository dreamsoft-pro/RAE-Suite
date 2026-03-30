import yaml
import os
from rae_suite.core.factory import FactorySpec

class FactoryLoader:
    def __init__(self, config_path: str = "factory.yaml"):
        self.config_path = config_path

    def load(self) -> FactorySpec:
        if not os.path.exists(self.config_path):
            return FactorySpec(factory_id="default", active_departments=[], agents={}, budgets={})
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            return FactorySpec(**data)
