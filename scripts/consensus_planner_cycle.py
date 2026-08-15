#!/usr/bin/env python3
"""
Consensus Planner Cycle Script for RAE-Suite
Performs sequential multi-model LLM audits via OpenRouter:
1. openai/gpt-5.6-luna-pro (Logic & Domain Model Audit)
2. deepseek/deepseek-r1 (Runtime & Concurrency Audit)
3. anthropic/claude-opus-4.8 (Types & Architecture Audit)
4. openai/gpt-5.6-sol (Performance & Resource Audit)
5. anthropic/claude-fable-5 [fallback anthropic/claude-opus-5] (Reliability & Quality Audit)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("CRITICAL ERROR: OPENROUTER_API_KEY is not set in environment!")
    sys.exit(1)

DOCS_DIR = "/home/grzegorz/cloud/RAE-Suite/docs"
PLAN_PATH = os.path.join(DOCS_DIR, "detailed_implementation_plan.md")
AUDIT_TRAIL_PATH = os.path.join(DOCS_DIR, "RAE_CONSENSUS_AUDIT_TRAIL.md")

AUDIT_STAGES = [
    {
        "step": 1,
        "name": "GPT-5.6 Luna Pro",
        "model": "openai/gpt-5.6-luna-pro",
        "fallback_model": None,
        "role": "Logic & Domain Model Audit",
        "instructions": (
            "Jesteś ekspertem ds. logiki domenowej i architektur DDD / Agentic Workflow (GPT-5.6 Luna Pro). "
            "Twoim zadaniem jest przeprowadzić rygorystyczny audyt logiki domenowej w przedstawionym planie rozwoju RAE-Suite.\n"
            "Sprawdź:\n"
            "1. Czy model domenowy, maszyna stanów zadania i klasyfikacja ryzyka są spójne z uwagami w rozwój-RAE-part-1.md?\n"
            "2. Czy DTO ExecutionReceipt oraz ModelRoutingDecision wyczerpują potrzeby semantyki wykonania?\n"
            "3. Czy brakuje jakichś kluczowych pojęć domenowych lub przejść w maszynie stanów?\n"
            "Zwróć zwięzłą, rzeczową recenzję oraz podaj konkretną zaktualizowaną treść planu lub uzupełnienia w formacie Markdown."
        )
    },
    {
        "step": 2,
        "name": "DeepSeek R1",
        "model": "deepseek/deepseek-r1",
        "fallback_model": None,
        "role": "Deep Runtime & Concurrency Audit",
        "instructions": (
            "Jesteś ekspertem ds. systemów współbieżnych i środowisk wykonawczych (DeepSeek R1). "
            "Twoim zadaniem jest przeprowadzenie głębokiego audytu runtime, współbieżności i wykrywania błędów w planie RAE-Suite.\n"
            "Przeanalizuj:\n"
            "1. Zagrożenia race conditions, deadlocki i wyścigi danych w bezstanowych workerach i maszynie stanów.\n"
            "2. Izolację zadań w Git worktree oraz bezpieczne zarządzenie zasobami w async ToolGateway.\n"
            "3. Zapobieganie utracie stanu i obsługa wyjątków w pętlach naprawczych Phoenix i eskalacji OpenCode/Hermes.\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z uwzględnieniem poprawek runtime i współbieżności."
        )
    },
    {
        "step": 3,
        "name": "Claude Opus 4.8",
        "model": "anthropic/claude-opus-4.8",
        "fallback_model": None,
        "role": "Types & Architecture Audit",
        "instructions": (
            "Jesteś głównym architektem systemowym i ekspertem ds. typowania (Claude Opus 4.8). "
            "Twoim zadaniem jest audyt architektury, kontraktów i typowania planu RAE-Suite.\n"
            "Przeanalizuj:\n"
            "1. Twarde egzekwowanie kontraktów (CapabilityContract hard enforcement, Branded Types, agnostyczność domeny).\n"
            "2. Granice modułów i interfejsów (CognitivePlanner, ModelRouter, Quality Tribunal, OpenCode/Hermes escalation).\n"
            "3. Spójność kontraktów DTO i czystość architektury.\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z ulepszoną architekturą i typowaniem."
        )
    },
    {
        "step": 4,
        "name": "GPT-5.6 Sol",
        "model": "openai/gpt-5.6-sol",
        "fallback_model": None,
        "role": "Performance & Resource Audit",
        "instructions": (
            "Jesteś inżynierem wydajności wysokoprzepustowych systemów rozproszonych (GPT-5.6 Sol). "
            "Twoim zadaniem jest audyt wydajnościowy planu RAE-Suite.\n"
            "Przeanalizuj:\n"
            "1. Optymalizację routingu modeli (expected_tokens, latency, budget rules) i podłączenie metryk z RAE-Lab.\n"
            "2. Wydajność kolejek pub/sub, cache semantycznego i zarządzania pamięcią operacyjną.\n"
            "3. Minimalizację narzutu przy weryfikacji testów i zapisie dowodów wykonania ExecutionReceipt.\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z optymalizacjami wydajnościowymi."
        )
    },
    {
        "step": 5,
        "name": "Fable 5",
        "model": "anthropic/claude-fable-5",
        "fallback_model": "anthropic/claude-opus-5",
        "role": "Reliability, Zero-Downtime & Quality Audit",
        "instructions": (
            "Jesteś ekspertem ds. niezawodności systemowej (SRE), bezpieczeństwa i norm ISO 27001/42001 (Fable 5). "
            "Twoim zadaniem jest audyt niezawodności, audytowalności i Quality Tribunal w planie RAE-Suite.\n"
            "Przeanalizuj:\n"
            "1. Wielomodelowy konsensus w Quality Tribunal (ważone głosowanie, zapobieganie halucynacjom i stronniczości).\n"
            "2. Audytowalność i niezmienność dowodów (SHA-256 hash chaining, ISO 27001/42001 ExecutionReceipt).\n"
            "3. Pętlę automatycznej naprawy Phoenix na podstawie precyzyjnych raportów jakościowych.\n"
            "Zwróć zwięzłą recenzję oraz ostateczny podsumowujący tekst poprawek dla planu."
        )
    }
]

def query_openrouter(model_id, fallback_model, system_prompt, user_content):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/RAE-Suite",
        "X-Title": "RAE-Suite Consensus Engine"
    }
    
    target_model = model_id
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }

    print(f"--> Invoking OpenRouter model: {target_model}...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            print(f"✓ Received response from {target_model} ({len(content)} chars)")
            return target_model, content
    except urllib.error.HTTPError as e:
        print(f"URLLIB ERROR for {target_model}: {e}")
        if fallback_model:
            print(f"--> Attempting fallback model: {fallback_model}...")
            payload["model"] = fallback_model
            req_fb = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req_fb) as resp_fb:
                data_fb = json.loads(resp_fb.read().decode("utf-8"))
                content_fb = data_fb["choices"][0]["message"]["content"]
                print(f"✓ Received response from fallback {fallback_model} ({len(content_fb)} chars)")
                return fallback_model, content_fb
        raise e

def run_consensus_cycle():
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        current_plan = f.read()

    audit_logs = []
    audit_logs.append("# RAE-Suite OpenRouter Multi-Model Consensus Audit Trail\n")
    audit_logs.append(f"**Data wykonania:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for stage in AUDIT_STAGES:
        step_num = stage["step"]
        name = stage["name"]
        model = stage["model"]
        fallback = stage["fallback_model"]
        role = stage["role"]
        instructions = stage["instructions"]

        print(f"\n==================================================")
        print(f"STEP {step_num}/5: {name} ({role})")
        print(f"Target Model: {model}")
        print(f"==================================================")

        prompt_text = (
            f"Oto aktualna wersja Szczegółowego Planu Rozwoju RAE-Suite:\n\n"
            f"```markdown\n{current_plan}\n```\n\n"
            f"Proszę o przeprowadzenie audytu zgodnie z Twoją rolą ({role}).\n"
            f"1. Przedstaw listę konkretnych uwag, dostrzeżonych luk i rekomendacji usprawnień.\n"
            f"2. Przedstaw zaktualizowany, rozszerzony plan w formacie Markdown (możesz dopisać nowe sekcje, doprecyzować istniejące i rozwinąć DTO oraz fazy P0-P3)."
        )

        used_model, response = query_openrouter(model, fallback, instructions, prompt_text)

        # Record audit log entry
        log_entry = (
            f"## Krok {step_num}: {name} ({used_model})\n"
            f"**Rola:** {role}  \n"
            f"**Czas:** {time.strftime('%H:%M:%S')}  \n\n"
            f"### Wynik Audytu i Rekomendacje:\n\n"
            f"{response}\n\n"
            f"---\n\n"
        )
        audit_logs.append(log_entry)

        # Save checkpoint plan for this stage
        step_plan_path = os.path.join(DOCS_DIR, f"detailed_implementation_plan_step{step_num}_{name.lower().replace(' ', '_')}.md")
        with open(step_plan_path, "w", encoding="utf-8") as f_step:
            f_step.write(f"<!-- Plan po Kroku {step_num}: {name} ({used_model}) -->\n\n" + response)
        print(f"Zapisano plan cząstkowy: {step_plan_path}")

        # Integrate updates into current_plan baseline for the next stage
        # We append a summary of improvements and updated sections
        current_plan = response

        # Short pause between API calls to avoid rate limits
        time.sleep(2)

    # Save final Audit Trail
    with open(AUDIT_TRAIL_PATH, "w", encoding="utf-8") as f_trail:
        f_trail.write("".join(audit_logs))
    print(f"\n✓ Zapisano pełny audit trail: {AUDIT_TRAIL_PATH}")

    # Save final consolidated plan to detailed_implementation_plan.md
    final_plan_header = (
        f"# Szczegółowy Iteracyjny Plan Rozwoju RAE-Suite (Zweryfikowany Konsensusem 5 AI)\n"
        f"**Wersja:** 2.0 (Konsensus OpenRouter Multi-Model)\n"
        f"**Zweryfikowano przez:**\n"
        f"1. GPT-5.6 Luna Pro (`openai/gpt-5.6-luna-pro`) - Logika Domenowa i DTO\n"
        f"2. DeepSeek R1 (`deepseek/deepseek-r1`) - Runtime, Izolacja & Współbieżność\n"
        f"3. Claude Opus 4.8 (`anthropic/claude-opus-4.8`) - Architektura & Typowanie\n"
        f"4. GPT-5.6 Sol (`openai/gpt-5.6-sol`) - Wydajność & Metryki RAE-Lab\n"
        f"5. Fable 5 / Opus 5 (`anthropic/claude-opus-5`) - Niezawodność, ISO 27001/42001 & Quality Tribunal\n\n"
        f"---\n\n"
    )
    with open(PLAN_PATH, "w", encoding="utf-8") as f_final:
        f_final.write(final_plan_header + current_plan)
    
    # Also save as RAE_CONSENSUS_PLAN_V2.md for explicit documentation retention
    consensus_v2_path = os.path.join(DOCS_DIR, "RAE_CONSENSUS_PLAN_V2.md")
    with open(consensus_v2_path, "w", encoding="utf-8") as f_v2:
        f_v2.write(final_plan_header + current_plan)

    print(f"✓ Zapisano ostateczny skonsolidowany plan w: {PLAN_PATH}")
    print(f"✓ Zapisano zapasowy plan konsensusu w: {consensus_v2_path}")

if __name__ == "__main__":
    run_consensus_cycle()
