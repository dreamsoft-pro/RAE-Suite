from fastapi import FastAPI, Request
import uvicorn
import httpx
import os
import sys

# In docker, rae_core is mounted to /app/rae_core
# We add /app to sys.path to find rae_core package
sys.path.append("/app")

from rae_core.bridge.handler import register_bridge

app = FastAPI(title="RAE-Suite Orchestrator")

# Register Bridge for the Orchestrator itself
register_bridge(app, "rae-suite-orchestrator")

@app.get("/health")
def health():
    return {"status": "healthy", "module": "rae-suite"}

@app.post("/v2/orchestrate/task")
async def orchestrate_task(task: dict):
    """
    Active Orchestration Flow via OpenClaw.
    """
    rae_api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
    
    # 1. Instruct OpenClaw to take over as the active orchestrator for this plan
    bridge_payload = {
        "payload": {
            "intent": "execute_plan",
            "plan": task,
            "required_agents": ["rae-phoenix", "rae-lab", "rae-quality"]
        },
        "source_agent": "rae-suite-orchestrator",
        "target_agent": "open-claw"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{rae_api_url}/v2/bridge/interact",
                json=bridge_payload,
                timeout=10.0
            )
            response.raise_for_status()
            bridge_response = response.json()
            return {"status": "task_delegated_to_openclaw", "bridge_response": bridge_response}
    except Exception as e:
        return {"status": "failed_to_delegate", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
