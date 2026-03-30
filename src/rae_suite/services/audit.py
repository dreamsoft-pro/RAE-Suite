import httpx
import os
from rae_core.models.evidence import ActionRecord, OutcomeRecord

class AuditLogger:
    def __init__(self):
        self.api_url = os.getenv("RAE_API_URL", "http://rae-am-api:8000")

    async def log_action(self, action: ActionRecord):
        async with httpx.AsyncClient() as client:
            # Zapis do warstwy episodic pamięci RAE
            response = await client.post(
                f"{self.api_url}/v2/memories",
                json={
                    "content": action.goal,
                    "layer": "episodic",
                    "metadata": action.model_dump()
                }
            )
            return response.status_code == 200
