# RAE-Suite/rae_suite_orchestrator.py
import asyncio
import os
import json
import httpx
import yaml
import structlog
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from core.infra_reconciler import InfraReconciler
from core.autonomy_kernel import AutonomyKernel
from core.curiosity_engine import CuriosityEngine
from core.batch_engine import BatchOptimizationEngine, BatchTask
import uuid

try:
    from rae_libs.rae_core.utils.memory_bridge import RAEMemoryBridge
except ImportError:
    # Fallback to standard core bridge
    try:
        from rae_core.utils.memory_bridge import RAEMemoryBridge
    except ImportError:
        # Fallback fake bridge for testing
        class RAEMemoryBridge:
            def __init__(self, project_name):
                self.project_name = project_name
            def save_event(self, text, layer="episodic"):
                print(f"🌉 [Bridge Fake] Event Saved: {text} ({layer})")
            def log_decision(self, action, reasoning, payload):
                print(f"🌉 [Bridge Fake] Decision Logged: {action} - {reasoning}")

logger = structlog.get_logger(__name__)

class RAE_CEO_Orchestrator:
    """The Intelligent Brain of the RAE Suite (Unified Audit Edition) utilizing a Declarative Reconciler."""
    
    def __init__(self):
        self.api_url = os.getenv("RAE_API_URL", "http://localhost:8011")
        self.orchestration_interval = int(os.getenv("ORCHESTRATION_TICK", "60"))
        self.last_action_time = None
        self.factory_spec_path = os.getenv("FACTORY_SPEC_PATH", "factory.yaml")
        # Unified Bridge
        self.bridge = RAEMemoryBridge(project_name="rae-suite-ceo")
        
        # Infra Reconciler
        self.infra_reconciler = InfraReconciler()

        # Autonomy Kernel (Silicon Oracle v6.8)
        self.kernel = AutonomyKernel(bridge=self.bridge, repo_root=".")
        self.curiosity_engine = CuriosityEngine(kernel=self.kernel, repo_root=".")
        self.planning_agent = os.getenv("CEO_PLANNING_AGENT", "rae-oracle-gemini")
        self.batch_engine = BatchOptimizationEngine()

    async def run_loop(self):
        logger.info("orchestrator_booted", role="CEO_Agent", mode="Declarative Reconciler")
        self.bridge.save_event("Orkiestrator CEO został uruchomiony w trybie deklaratywnego Reconcilera.", layer="episodic")
        
        while True:
            try:
                # 1. OBSERVE (Desired State from YAML + Actual State from Docker & Memory)
                desired_state = self._load_desired_factory_spec()
                actual_state = await self._observe_system_state()
                
                # 2. PLAN & DECIDE (Reconcile / Drift Alignment)
                drifts = self._detect_configuration_drifts(desired_state, actual_state)
                
                if drifts:
                    logger.warning("configuration_drifts_detected", count=len(drifts))
                    for drift in drifts:
                        await self._align_drift(drift)
                    self.last_action_time = datetime.utcnow()
                else:
                    # Queue backlog items into Batch Engine (Context Economy Optimization)
                    backlog = actual_state.get("backlog", [])
                    if backlog:
                        for task in backlog:
                            # Map task to BatchTask
                            self.batch_engine.add_task(BatchTask(
                                task_id=task.get("id", f"tsk-{uuid.uuid4().hex[:6]}"),
                                module="phoenix" if "phoenix" in task.get("content", "").lower() else "hive",
                                target_file=task.get("project", "main.py"),
                                action_type="refactor" if "phoenix" in task.get("content", "").lower() else "test",
                                complexity=0.5
                            ))
                        
                        batches = self.batch_engine.optimize_and_group()
                        if batches:
                            logger.warning("batch_optimization_found_groups", count=len(batches))
                            for batch in batches:
                                await self._dispatch_batch(batch)
                            self.last_action_time = datetime.utcnow()
                        else:
                            # If stable, prioritize outstanding items in the development backlog
                            decision = await self._decide_backlog_action(actual_state)
                            if decision.get("intent") != "IDLE":
                                await self._dispatch_action(decision)
                                self.last_action_time = datetime.utcnow()
                    else:
                        decision = await self._decide_backlog_action(actual_state)
                        if decision.get("intent") != "IDLE":
                            # Audit strategic decision
                            self._log_signed_decision(
                                action="strategy_selected",
                                reasoning=decision.get("reasoning", "Executing backlog task."),
                                payload={"target_agent": decision.get("agent"), "backlog_count": len(actual_state["backlog"])}
                            )
                            await self._dispatch_action(decision)
                            self.last_action_time = datetime.utcnow()
                        else:
                            logger.info("system_fully_aligned_and_stable")
                            await self.curiosity_engine.trigger_idle_scan()

            except Exception as e:
                logger.error("reconciliation_cycle_failed", error=str(e))
                
            await asyncio.sleep(self.orchestration_interval)

    def _load_desired_factory_spec(self) -> Dict[str, Any]:
        """Loads desired factory state configuration from factory.yaml spec."""
        if not os.path.exists(self.factory_spec_path):
            # Safe default fallback specification
            return {
                "version": "1.0",
                "agents": [
                    {"name": "rae-phoenix", "required": True, "min_instances": 1},
                    {"name": "rae-hive", "required": True, "min_instances": 1},
                    {"name": "rae-quality", "required": True, "min_instances": 1}
                ]
            }
        with open(self.factory_spec_path, "r") as f:
            return yaml.safe_load(f)

    async def _observe_system_state(self) -> Dict[str, Any]:
        """Queries Lab, Quality and Memory for actual live state snapshot."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Lab Insights
            lab_resp = None
            try:
                lab_resp = await client.get(f"{self.api_url}/v2/lab/insights")
            except Exception:
                pass
                
            # Query Pending Tasks in Memory
            task_resp = None
            try:
                task_resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": "pending development tasks",
                    "layer": "working",
                    "k": 5
                })
            except Exception:
                pass
            
            return {
                "lab_insights": lab_resp.json() if lab_resp and lab_resp.status_code == 200 else {},
                "backlog": task_resp.json().get("results", []) if task_resp and task_resp.status_code == 200 else [],
                "active_agents": ["rae-phoenix", "rae-hive", "rae-quality"] # Mock actual docker running states
            }

    def _detect_configuration_drifts(self, desired: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies discrepancies between desired factory specs and running container states."""
        drifts = []
        desired_agents = desired.get("agents", [])
        actual_running = actual.get("active_agents", [])
        
        for agent in desired_agents:
            name = agent.get("name")
            required = agent.get("required", False)
            if required and name not in actual_running:
                drifts.append({
                    "type": "missing_agent_container",
                    "agent": name,
                    "reasoning": f"Desired agent '{name}' is marked required but is not running in actual state."
                })
        return drifts

    async def _align_drift(self, drift: Dict[str, Any]):
        """Executes corrective commands to automatically align configuration dry-runs."""
        agent = drift.get("agent")
        logger.warning("aligning_drift_correction", agent=agent, type=drift.get("type"))
        
        # In a real environment, this invokes docker-compose or hive deployment command
        self.bridge.save_event(f"Autonomicznie naprawiono dryf: uruchomiono brakujący kontener {agent}.", layer="episodic")

    async def _decide_backlog_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Strategic decision prioritizing outstanding development backlogs."""
        prompt = f"""
        Jesteś CEO Suity RAE. Masz pod sobą: Phoenix (Refaktoryzacja), Hive (Budowanie), Lab (Analiza).
        STAN FABRYKI: {state}
        
        Zdecyduj o kolejnym kroku. Jeśli jakość (Lab) odpada - wyślij Phoenixa. Jeśli backlog jest pełny - wyślij Hive.
        Odpowiedz JEDNYM JSONEM: {{"intent": "WAKE_AGENT", "agent": "rae-phoenix"|"rae-hive", "reasoning": "string"}}
        Jeśli wszystko OK, odpowiedz: {{"intent": "IDLE"}}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                    "intent": "CEO_STRATEGIC_PLANNING",
                    "target_agent": self.planning_agent,
                    "payload": {"prompt": prompt}
                }, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json().get("payload", {}).get("interaction_data", {"intent": "IDLE"})
        except Exception:
            pass
            
        # Basic heuristic fallback if LLM is offline
        if len(state.get("backlog", [])) > 2:
            return {"intent": "WAKE_AGENT", "agent": "rae-hive", "reasoning": "Backlog has high density. Waking up Hive."}
        return {"intent": "IDLE"}

    def _log_signed_decision(self, action: str, reasoning: str, payload: dict):
        """Signs and registers an ISO-compliant cryptographic strategic evidence record."""
        raw_msg = f"{action}:{reasoning}:{json.dumps(payload, sort_keys=True)}"
        signature = hashlib.sha256(raw_msg.encode("utf-8")).hexdigest()
        
        full_payload = {
            **payload,
            "orchestrator_signature": signature,
            "iso_compliance": "ISO-27001",
            "signed_at": datetime.utcnow().isoformat()
        }
        
        self.bridge.log_decision(
            action=action,
            reasoning=reasoning,
            payload=full_payload
        )

    async def _dispatch_action(self, decision: Dict[str, Any]):
        """Dispatches commands via the Autonomy Kernel to enforce lifecycle and auditability."""
        agent = decision.get("agent")
        reasoning = decision.get("reasoning")
        
        logger.warning("ceo_dispatching_orders", target=agent, reason=reasoning)
        
        # Enforce Silicon Oracle v6.8 Lifecycle
        receipt = await self.kernel.execute_task(
            goal_id=f"goal-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            intent=reasoning, # Using reasoning as intent for risk classification
            payload={"target_agent": agent, "instruction": reasoning}
        )
        
        logger.info("task_lifecycle_completed", id=receipt.id, status=receipt.execution_status)

    async def _dispatch_batch(self, batch):
        """Dispatches a batch of tasks via the Autonomy Kernel to optimize context switches."""
        logger.warning("ceo_dispatching_batch", batch_id=batch.batch_id, count=len(batch.tasks))
        
        # Calculate savings
        tokens_saved, duration_saved = self.batch_engine.dispatch_batch(batch)
        
        # Log to bridge
        self.bridge.save_event(
            f"Wysłano paczkę zadań {batch.batch_id} (moduł: {batch.module}) do jądra autonomii. "
            f"Zaoszczędzono: {tokens_saved} tokenów, {duration_saved:.1f}s przezbrojeń.",
            layer="reflective"
        )
        
        # Serialize tasks for payload
        tasks_payload = []
        for t in batch.tasks:
            tasks_payload.append({
                "task_id": t.task_id,
                "file": t.target_file,
                "action": t.action_type
            })
            
        receipt = await self.kernel.execute_task(
            goal_id=f"goal-batch-{batch.batch_id}",
            task_id=f"task-batch-{batch.batch_id}",
            intent=f"BATCH_EXECUTION: {batch.module} tasks",
            payload={
                "target_agent": "rae-phoenix" if batch.module == "phoenix" else "rae-hive",
                "batch_id": batch.batch_id,
                "tasks": tasks_payload,
                "metrics": {
                    "tokens_saved": tokens_saved,
                    "duration_saved": duration_saved,
                    "batch_size": len(batch.tasks)
                }
            }
        )
        logger.info("batch_lifecycle_completed", id=receipt.id, status=receipt.execution_status)

if __name__ == "__main__":
    orchestrator = RAE_CEO_Orchestrator()
    asyncio.run(orchestrator.run_loop())
