# RAE-Suite/rae_suite_orchestrator.py
import asyncio
import os
import httpx
import structlog
from datetime import datetime
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)

class RAE_CEO_Orchestrator:
    """The Intelligent Brain of the RAE Suite. Operates as a CEO Agent (Observe-Plan-Dispatch)."""
    
    def __init__(self):
        self.api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
        self.orchestration_interval = int(os.getenv("ORCHESTRATION_TICK", "120")) # 2 mins
        self.last_action_time = None

    async def run_loop(self):
        logger.info("orchestrator_booted", role="CEO_Agent", mode="Autonomous")
        
        while True:
            try:
                # 1. OBSERVE: Fetch System State
                state = await self._observe_system_state()
                logger.info("observing_factory_state", state_summary=state["summary"])
                
                # 2. PLAN & DECIDE: Ask LLM for next priority
                decision = await self._decide_next_action(state)
                
                # 3. DISPATCH: Execute decision via A2A Bridge
                if decision.get("intent") != "IDLE":
                    await self._dispatch_action(decision)
                    self.last_action_time = datetime.utcnow()
                else:
                    logger.info("system_stable_idling")

            except Exception as e:
                logger.error("orchestration_cycle_failed", error=str(e))
                
            await asyncio.sleep(self.orchestration_interval)

    async def _observe_system_state(self) -> Dict[str, Any]:
        """Queries Lab, Quality and Memory for a holistic view."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Lab Insights
            lab_resp = await client.get(f"{self.api_url}/v2/lab/insights")
            # Query Pending Tasks in Memory
            task_resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                "query": "pending development tasks",
                "layer": "working",
                "k": 5
            })
            
            return {
                "lab_insights": lab_resp.json() if lab_resp.status_code == 200 else {},
                "backlog": task_resp.json().get("results", []) if task_resp.status_code == 200 else [],
                "summary": "Observation complete."
            }

    async def _decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """High-level reasoning for Suita prioritization."""
        # Wzorzec Advanced Senior: Przesyłamy metryki do LLM przez Bridge
        prompt = f"""
        Jesteś CEO Suity RAE. Masz pod sobą: Phoenix (Refaktoryzacja), Hive (Budowanie), Lab (Analiza).
        STAN FABRYKI: {state}
        OSTATNIA AKCJA: {self.last_action_time}
        
        Zdecyduj o kolejnym kroku. Jeśli jakość (Lab) spada - wyślij Phoenixa. Jeśli backlog jest pełny - wyślij Hive.
        Odpowiedz JEDNYM JSONEM: {{"intent": "WAKE_AGENT", "agent": "rae-phoenix"|"rae-hive", "reasoning": "string"}}
        Jeśli wszystko OK, odpowiedz: {{"intent": "IDLE"}}
        """
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                "intent": "CEO_STRATEGIC_PLANNING",
                "target_agent": "rae-oracle-gemini",
                "payload": {"prompt": prompt}
            })
            if resp.status_code == 200:
                return resp.json().get("payload", {}).get("interaction_data", {"intent": "IDLE"})
            return {"intent": "IDLE"}

    async def _dispatch_action(self, decision: Dict[str, Any]):
        """Wakes up targeted agents via Bridge."""
        agent = decision.get("agent")
        reasoning = decision.get("reasoning")
        
        logger.warning("ceo_dispatching_orders", target=agent, reason=reasoning)
        
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.api_url}/v2/bridge/interact", json={
                "intent": "EXECUTE_STRATEGY",
                "source_agent": "rae-suite-ceo",
                "target_agent": agent,
                "payload": {"instruction": reasoning}
            })

if __name__ == "__main__":
    orchestrator = RAE_CEO_Orchestrator()
    asyncio.run(orchestrator.run_loop())
