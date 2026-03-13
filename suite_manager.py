# suite_manager.py
import sys
import os

# Wyznaczamy ścieżkę do RAE-agentic-memory dynamicznie
current_dir = os.path.dirname(os.path.abspath(__file__))
memory_core_path = os.path.abspath(os.path.join(current_dir, "./packages/rae-agentic-memory/rae-core"))
sys.path.append(memory_core_path)

from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

class RAESuiteManager:
    """Enterprise Manager for the entire RAE-Suite Factory."""
    
    def __init__(self):
        # 1. Inicjalizacja fundamentu dla Suite
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-suite-orchestrator")

    @audited_operation(operation_name="factory_sync", impact_level="high")
    def sync_all_repositories(self):
        """Synchronizuje wszystkie repozytoria i submoduły."""
        print("🚀 Syncing all Factory repositories...")
        # Logika git submodule update --remote itd.
        return "Factory synchronized successfully."

if __name__ == "__main__":
    manager = RAESuiteManager()
    manager.sync_all_repositories()
