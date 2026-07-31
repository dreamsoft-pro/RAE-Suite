#!/usr/bin/env python3
"""
RAE-Suite 5-Model Consensus Planner for A2A, Keycloak, OpenAPI, Lightweight Core & Telemetry Plan.
Runs live OpenRouter API calls across:
1. GPT-5.6 Luna (openai/gpt-5.6-luna-pro)
2. DeepSeek R1 (deepseek/deepseek-r1)
3. Claude Opus 4.8 (anthropic/claude-opus-4.8)
4. GPT-5.6 Sol (openai/gpt-5.6-sol)
5. Fable 5 (anthropic/claude-fable-5)
"""

import os
import sys
import json
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("consensus-planner-a2a")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY environment variable is not set!")
    sys.exit(1)

MODELS = [
    ("GPT-5.6 Luna Pro", "openai/gpt-5.6-luna-pro", "Domena, Schematy OpenAPI, DTO, Keycloak Integration & Ingesting Report"),
    ("DeepSeek R1", "deepseek/deepseek-r1", "Adversarial Review: Concurrency, Race Conditions, Fail-Closed, A2A Security & Memory Leaks"),
    ("Claude Opus 4.8", "anthropic/claude-opus-4.8", "Typowanie Branded Types, Model & DB Agnostic Core, System Architecture Audit"),
    ("GPT-5.6 Sol", "openai/gpt-5.6-sol", "Wydajność, RAE Mesh, Lekki Footprint dla Urządzeń, OTel Telemetry & Grafana"),
    ("Fable 5", "anthropic/claude-opus-5", "ISO 27001/42001 Audytowalność, Niezaprzeczalność Zdarzeń A2A, Ostateczna Synteza Planu")
]

def query_openrouter(model_id: str, prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rae-suite.internal",
        "X-Title": "RAE-Suite A2A Consensus Planner"
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Jesteś wybitnym Architektem Systemów AI i Bezpieczeństwa w zespole Silicon Oracle RAE Suite. Odpowiadaj konkretnie, używając github markdown, po polsku."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error querying model {model_id}: {e}")
        return f"[ERROR: Query failed for {model_id}: {e}]"

def main():
    logger.info("Starting 5-Model Consensus Planning Cycle for RAE-Suite A2A / Keycloak / OpenAPI / Lightweight Core...")
    
    # Read the MCP architecture report
    report_path = "docs/rae_mcp_architecture_report.md"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
    else:
        report_text = "Report not found."

    current_plan = f"""
# Plan Bazowy Udoskonalenia RAE-Suite: A2A, Keycloak, OpenAPI, Lekki Core Agnostyczny i Telemetria Mesh

## 1. Raport Wejściowy
{report_text}

## 2. Kluczowe Filary Transformacji RAE-Suite
1. **A2A Protocol (Agent-to-Agent Protocol)**: Bezpieczne odkrywanie usług, bezpośrednia delegacja peer-to-peer między agentami (`rae-hive`, `rae-memory`, `rae-phoenix`, `rae-clr`), podpisane cyfrowo transakcje A2A.
2. **OpenAPI v3 & Keycloak OAuth2 / OIDC**: Ujednolicenie wszystkich endpointów REST/MCP pod OpenAPI, autoryzacja RBAC i zintegrowane tokeny capability w Keycloak.
3. **Model & Database Agnostic Core**: RAE Core pozostaje całkowicie agnostyczny od konkretnych modeli LLM i baz danych (Lekkie adaptery, Pydantic DTO, wsparcie dla SQLite/Postgres/Qdrant/Local).
4. **Lekkość i Wielourządzeniowość (Mobile/Thin Client/Windows/Laptop/Mesh)**: Niskie zużycie RAM/CPU, uruchamianie na dowolnym urządzeniu, dynamiczny routing RAE Mesh.
5. **Pełna Telemetria OpenTelemetry & Grafana**: Śledzenie distributed traces (OTel), metryki Prometheus i wskaźniki Kaizen.
6. **Objęcie Całej Suity RAE**: `rae-agentic-memory`, `rae-phoenix`, `rae-clr`, `rae-hive`, `rae-contracts`, `rae-core`.
"""

    audit_trail = []

    for name, model_id, role in MODELS:
        logger.info(f"--> Konsultacja z modelem {name} ({model_id}) - Rola: {role}...")
        prompt = f"""
Oto aktualny stan planu architektonicznego RAE-Suite:

{current_plan}

Jako {name} ({role}), przeanalizuj plan i zgłoś niezbędne poprawki, uzupełnienia architektoniczne oraz rekomendacje w swoim obszarze specjalizacji.

Twoja odpowiedź musi zawierać:
1. Analizę i wykryte luki w dotychczasowym planie.
2. Konkretne poprawki i wpisy do planu ulepszeń.
3. Uzasadnienie z punktu widzenia Twojej roli ({role}).
"""
        review = query_openrouter(model_id, prompt)
        logger.info(f"✓ Odebrano odpowiedź od {name} ({len(review)} znaków)")
        
        audit_trail.append({
            "model_name": name,
            "model_id": model_id,
            "role": role,
            "review": review
        })

        # Append model feedback to cumulative plan
        current_plan += f"\n\n---\n\n## Rekomendacje i Audyt: {name} ({role})\n{review}\n"

    # Write Master Implementation Plan
    plan_out_path = "docs/RAE_SUITE_A2A_KEYCLOAK_LIGHTWEIGHT_PLAN.md"
    with open(plan_out_path, "w", encoding="utf-8") as f:
        f.write(current_plan)
    logger.info(f"✓ Zapisano ostateczny Plan Konsensusu w: {plan_out_path}")

    # Write Consensus Audit Trail
    audit_out_path = "docs/RAE_SUITE_CONSENSUS_AUDIT_TRAIL.md"
    with open(audit_out_path, "w", encoding="utf-8") as f:
        f.write("# RAE-Suite 5-Model Consensus Audit Trail\n\n")
        for entry in audit_trail:
            f.write(f"### Model: {entry['model_name']} ({entry['model_id']})\n")
            f.write(f"**Rola:** {entry['role']}\n\n")
            f.write(entry['review'])
            f.write("\n\n---\n\n")
    logger.info(f"✓ Zapisano Ślad Audytowy w: {audit_out_path}")

if __name__ == "__main__":
    main()
