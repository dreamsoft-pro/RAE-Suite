import sys
import os
import httpx
import json

from pathlib import Path

# Force correct python and path dynamically
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CLOUD_ROOT = PROJECT_ROOT.parent

RAE_CORE_PATH = str(PROJECT_ROOT / "packages" / "rae-agentic-memory" / "rae-core")

# Find site-packages directory in virtualenv dynamically
lib_dir = CLOUD_ROOT / ".venv" / "lib"
site_packages_dirs = list(lib_dir.glob("python*/site-packages")) if lib_dir.exists() else []
if site_packages_dirs:
    VENV_PATH = str(site_packages_dirs[0])
else:
    VENV_PATH = str(CLOUD_ROOT / ".venv" / "lib" / "python3.12" / "site-packages")

if RAE_CORE_PATH not in sys.path:
    sys.path.append(RAE_CORE_PATH)
if VENV_PATH not in sys.path:
    sys.path.append(VENV_PATH)

from rae_core.utils.context import RAEContextLocator

def validate_integration():
    # 1. Dynamic context discovery (Agnostic)
    tenant_id = RAEContextLocator.get_current_tenant_id()
    project = RAEContextLocator.get_project_name()
    api_url = os.getenv("RAE_API_URL", "http://localhost:8000")
    
    print(f"--- RAE AGNOSTIC VALIDATION ---")
    print(f"Detected Tenant: {tenant_id}")
    print(f"Detected Project: {project}")
    
    # 2. Simulate RAE-First Hook Event
    # We use the full path to python from venv to ensure psutil is found
    print("\n[STEP 1] Simulating AGY Hook Event...")
    hook_script = str(CLOUD_ROOT / "scripts" / "agy_rae_hook.py")
    python_bin = str(CLOUD_ROOT / ".venv" / "bin" / "python3")
    
    # Set PYTHONPATH and RAE_API_URL for the sub-process as well
    os.environ["PYTHONPATH"] = f"{RAE_CORE_PATH}:{os.environ.get('PYTHONPATH', '')}"
    os.environ["RAE_API_URL"] = api_url
    
    cmd = f"{python_bin} {hook_script} validation_event 'Fluid test of RAE-First bridge'"
    os.system(cmd)
    
    # 3. Verify via API Query
    print("[STEP 2] Verifying memory persistence (Fluid Query)...")
    payload = {
        "query": "Fluid test of RAE-First bridge",
        "project": "antigravity-cli",
        "k": 1
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{api_url}/v2/memories/query",
                json=payload,
                headers={"X-Tenant-Id": tenant_id}
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    mem = results[0]
                    print("✅ SUCCESS: Memory retrieved!")
                    print(f"   Label: {mem.get('human_label')}")
                    print(f"   Content: {mem.get('content')}")
                    print(f"   Metadata: {json.dumps(mem.get('metadata'), indent=2)}")
                    print(f"   Cognitive Layer Decision: {mem.get('metadata', {}).get('layer', 'undetermined')}")
                else:
                    print("❌ FAILURE: Memory not found in search results.")
            else:
                print(f"❌ FAILURE: API Error {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ ERROR: Connection failed: {str(e)}")

if __name__ == "__main__":
    validate_integration()
