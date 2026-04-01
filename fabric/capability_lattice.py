from typing import Dict, List

class CapabilityLattice:
    def __init__(self):
        self.links: Dict[str, List[str]] = {}

    def link_capabilities(self, parent: str, child: str):
        if parent not in self.links:
            self.links[parent] = []
        self.links[parent].append(child)

    def get_dependencies(self, capability_id: str) -> List[str]:
        return self.links.get(capability_id, [])
