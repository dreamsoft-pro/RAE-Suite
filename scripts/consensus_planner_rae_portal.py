#!/usr/bin/env python3
"""
RAE-Portal UI & Advanced Search Consensus Planner.
Runs live OpenRouter API calls across 5 mandated models:
1. GPT-5.6 Luna Pro (openai/gpt-5.6-luna-pro)
2. DeepSeek R1 (deepseek/deepseek-r1)
3. Claude Opus 4.8 (anthropic/claude-opus-4.8)
4. GPT-5.6 Sol (openai/gpt-5.6-sol)
5. Fable 5 (anthropic/claude-opus-5)
"""

import os
import sys
import json
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("consensus-planner-rae-portal")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY environment variable is not set!")
    sys.exit(1)

MODELS = [
    ("GPT-5.6 Luna Pro", "openai/gpt-5.6-luna-pro", "Domena UI, Hierarchia Widoków Modułów RAE-PORTAL, Schematy Komponentów i Filtry Wyszukiwania"),
    ("DeepSeek R1", "deepseek/deepseek-r1", "Adversarial Review UI: Wydajność Zapytania Wyszukiwania, Stronicowanie, Wyścigi WebSockets & Wycieki PII w UI"),
    ("Claude Opus 4.8", "anthropic/claude-opus-4.8", "Architektura Komponentów, Design System UX, Maszyny Stanów i Typowane REST/OpenAPI dla Portalu"),
    ("GPT-5.6 Sol", "openai/gpt-5.6-sol", "Optymalizacja Szybkości Skanowania, Indeksowanie Wyszukiwarki, Embedded Grafana/OTel & Footprint"),
    ("Fable 5", "anthropic/claude-opus-5", "Audytowalność ISO 27001/42001 w UI, Interfejs Human-in-the-Loop Approval & Ostateczna Synteza Planu")
]

def query_openrouter(model_id: str, prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rae-suite.internal",
        "X-Title": "RAE-Portal UI Consensus Planner"
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Jesteś Głównym Architektem UI/UX oraz Systemów Audytowalnych w Silicon Oracle RAE Suite. Odpowiadaj bardzo szczegółowo, konkretnie, używając github markdown, po polsku."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error querying model {model_id}: {e}")
        return f"[ERROR: Query failed for {model_id}: {e}]"

def main():
    logger.info("Starting 5-Model Consensus Planning Cycle for RAE-PORTAL UI & Advanced Search...")

    current_plan = """
# Plan Udoskonalenia Interfejsu RAE-PORTAL: Wizualizacja Modułów, Logów Execution Ledger i Wyszukiwarka Multimodalna

## 1. Cel Architektoniczny
Obecny portal RAE-PORTAL posiada zbyt ubogi interfejs użytkownika (UI), uniemożliwiający szczegółowy podgląd działań poszczególnych modułów suity oraz brak jakiejkolwiek zaawansowanej wyszukiwarki zdarzeń, faktów i audytów.
Plan ma na celu przekształcenie RAE-PORTAL w pełnowymiarowy, nowoczesny panel kontrolny (Command Center) dla całej fabryki agentycznej RAE-Suite.

## 2. Główne Moduły i Nowe Dedykowane Widoki w RAE-PORTAL
1. **RAE-Supervisor Dashboard**: Widok stanu klastra, autoryzacji Autonomy Kernel, logów kontenerów Docker, trasowania zadań oraz historii decyzji CEO.
2. **RAE-Quality Tribunal Inspector**: Przeglądarka 3-poziomowych audytów jakościowych, głosowań konsensusowych LLM, raportów statycznych Ruff/Mypy/Coverage i blokad wdrożeniowych.
3. **RAE-Lab Kaizen Observatory**: Wykresy wskaźników długu technicznego (Lean Score, Complexity Index), telemetria MAB (Multi-Armed Bandit) oraz historyczne trendy wydajności.
4. **RAE-Memory Subconscious Explorer**: Podgląd 4 warstw pamięci (Episodic, Semantic, Working, Reflective), wizualizacja grafu wiedzy, statusy wyczyszczenia PII i bezpieczników Circuit Breakers.
5. **RAE-Phoenix & RAE-CLR Lab**: Inspektor procesów samonaprawy kodu, odtworzenia transakcyjnych outboxów, re-playa zdarzeń oraz badań R&D.
6. **A2A & Mesh Route Monitor**: Mapa połączeń peer-to-peer agentów, weryfikacja podpisów cyfrowych, tokeny capability Keycloak oraz metryki OTel/Prometheus.

## 3. Globalna Wyszukiwarka Multimodalna (RAE Global Search)
- **Wyszukiwanie Hybrydowe (Full-Text + Vector Semantic Search)**: Błyskawiczne przeszukiwanie logów execution ledger (`RAE_EXECUTION_LEDGER.jsonl`), faktów pamięciowych, transakcji outbox i śladów audytowych.
- **Filtry Wielowymiarowe**: Po module (`rae-supervisor`, `rae-memory`, itp.), statusie ryzyka (`R0` do `R6`), czasie (timestamp range), dzierżawcy (`tenant_id`) oraz identyfikatorze transakcji (`message_id`/`trace_id`).
- **Anonimizacja PII w UI**: Automatyczne maskowanie wrażliwych danych w widokach portalu zgodnie z normami ISO 27001 / ISO 42001.
"""

    audit_trail = []

    for name, model_id, role in MODELS:
        logger.info(f"--> Konsultacja z modelem {name} ({model_id}) - Rola: {role}...")
        prompt = f"""
Oto aktualny plan rozbudowy RAE-PORTAL UI i Globalnej Wyszukiwarki:

{current_plan}

Jako {name} ({role}), przeanalizuj plan i wprowadź niezbędne poprawki, rozszerzenia komponentowe, specyfikacje interfejsu oraz optymalizacje w swoim obszarze.

Twoja odpowiedź musi zawierać:
1. Analizę braków w dotychczasowym planie RAE-PORTAL.
2. Szczegółowe poprawki i architekturę komponentów UI/UX.
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

        current_plan += f"\n\n---\n\n## Rekomendacje i Audyt: {name} ({role})\n{review}\n"

    # Write Master Implementation Plan
    plan_out_path = "docs/RAE_PORTAL_UI_IMPROVEMENT_PLAN.md"
    with open(plan_out_path, "w", encoding="utf-8") as f:
        f.write(current_plan)
    logger.info(f"✓ Zapisano ostateczny Plan Konsensusu RAE-PORTAL w: {plan_out_path}")

    # Write Consensus Audit Trail
    audit_out_path = "docs/RAE_PORTAL_CONSENSUS_AUDIT_TRAIL.md"
    with open(audit_out_path, "w", encoding="utf-8") as f:
        f.write("# RAE-PORTAL UI 5-Model Consensus Audit Trail\n\n")
        for entry in audit_trail:
            f.write(f"### Model: {entry['model_name']} ({entry['model_id']})\n")
            f.write(f"**Rola:** {entry['role']}\n\n")
            f.write(entry['review'])
            f.write("\n\n---\n\n")
    logger.info(f"✓ Zapisano Ślad Audytowy Portalu w: {audit_out_path}")

if __name__ == "__main__":
    main()
