import os
import sys
from pathlib import Path

# Fix PYTHONPATH for internal packages
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "packages" / "rae-core" / "src"))
sys.path.append(str(BASE_DIR / "rae_core" / "src"))

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from rae_core.models.capabilities import AgentRegistration
from rae_core.models.behavior import DepartmentBehaviorContract, BehaviorSignal
from core.auditor_engine import AuditorEngine
from core.behavior_registry import BehaviorRegistry
from core.capability_registry import CapabilityRegistry
from core.reconcile import Reconciler
from core.factory import FactorySpec
from fabric.cost_aware_router import CostAwareRouter

app = FastAPI(title="RAE-Suite Control Plane v2.0 (Master)")

# Inicjalizacja komponentów
cap_registry = CapabilityRegistry()
beh_registry = BehaviorRegistry()
auditor = AuditorEngine()
router = CostAwareRouter()
default_spec = FactorySpec(factory_id="master-factory", active_departments=[], agents={}, budgets={})
reconciler = Reconciler(default_spec)

@app.get("/health")
async def health():
    return {"status": "operational", "version": "3.2.0", "api": "v2"}

@app.get("/v2/factory/reconcile")
async def factory_reconcile():
    return await reconciler.reconcile_all()

@app.post("/v2/departments/register")
async def register_department(reg: AgentRegistration):
    cap_registry.register(reg)
    return {"status": "registered", "agent_id": reg.agent_id}

@app.get("/v2/fabric/route")
async def route_task(capability_id: str, max_risk: str = "high"):
    agents = [vars(a) for a in cap_registry._agents.values()]
    decision = router.route(capability_id, agents, max_risk)
    if not decision:
        raise HTTPException(status_code=404, detail=f"No agent for {capability_id}")
    return decision

@app.post("/v2/audit/evaluate")
async def audit_evaluate(department: str, raw_signals: List[dict]):
    contract = beh_registry.get(department)
    if not contract:
        raise HTTPException(status_code=404, detail=f"No contract for {department}")
    signals = auditor.collect_behavior_signals(raw_signals)
    violations = auditor.evaluate_behavioral_contract(contract, signals)
    return {"verdict": "BLOCKED" if violations else "PASSED", "violations": violations}
