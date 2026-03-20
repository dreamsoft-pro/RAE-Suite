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
    Example Orchestration Flow:
    1. Phoenix writes code
    2. Quality audits code
    3. Lab runs tests
    """
    return {"status": "task_initiated", "plan": task}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
