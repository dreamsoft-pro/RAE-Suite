#!/usr/bin/env python3
"""
Consensus Planner Cycle Script for RAE-Suite Part 2
(Flow & Auditable Autonomy based on rozwój-RAE-part-2.md)
Performs sequential multi-model LLM audits via OpenRouter:
1. openai/gpt-5.6-luna-pro (Logic & Domain Model Audit for Event Sourcing & Saga)
2. deepseek/deepseek-r1 (Runtime & Concurrency Audit for Redis Streams & Semantic Watchdog)
3. anthropic/claude-opus-4.8 (Types & Architecture Audit for ArtifactRef & Safe Replay)
4. openai/gpt-5.6-sol (Performance & Resource Audit for Cache-Aside & Outbox)
5. anthropic/claude-fable-5 [fallback anthropic/claude-opus-5] (Reliability & ISO Auditability)
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
PLAN_PATH = os.path.join(DOCS_DIR, "detailed_implementation_plan_part2.md")
AUDIT_TRAIL_PATH = os.path.join(DOCS_DIR, "RAE_CONSENSUS_AUDIT_TRAIL_PART2.md")

AUDIT_STAGES = [
    {
        "step": 1,
        "name": "GPT-5.6 Luna Pro",
        "model": "openai/gpt-5.6-luna-pro",
        "fallback_model": None,
        "role": "Logic & Domain Model Audit (Event Sourcing, CQRS & Saga)",
        "instructions": (
            "Jesteś ekspertem ds. logiki domenowej i architektur Event-Driven / Agentic Workflow (GPT-5.6 Luna Pro). "
            "Twoim zadaniem jest przeprowadzić rygorystyczny audyt logiki domenowej w planie rozwoju RAE-Suite Część 2 (rozwój-RAE-part-2.md).\n"
            "Sprawdź:\n"
            "1. Czy model domenowy Event Sourcing, CQRS, Transactional Outbox i Saga są spójne ze specyfikacją w rozwój-RAE-part-2.md?\n"
            "2. Czy DTO ArtifactRef (Claim Check) oraz SagaStep wyczerpują potrzeby bezpiecznego wykonania?\n"
            "3. Czy brakuje jakichś kluczowych zdarzeń domenowych lub przejść w cyklu życia kompensacji Sagi?\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowaną treść planu w formacie Markdown."
        )
    },
    {
        "step": 2,
        "name": "DeepSeek R1",
        "model": "deepseek/deepseek-r1",
        "fallback_model": None,
        "role": "Deep Runtime & Concurrency Audit (Redis Streams & Semantic Watchdog)",
        "instructions": (
            "Jesteś ekspertem ds. systemów rozproszonych, kolejek i współbieżności (DeepSeek R1). "
            "Twoim zadaniem jest przeprowadzenie audytu runtime dla planu RAE-Suite Część 2.\n"
            "Przeanalizuj:\n"
            "1. Wyścigi danych i spójność w Redis Streams (consumer groups, pending entries, DLQ).\n"
            "2. Detekcję pętli bez postępu w Semantic Watchdog / Semantic Circuit Breaker.\n"
            "3. Bezpieczny replay bez skutków ubocznych oraz spójność Transactional Outbox.\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z uwzględnieniem poprawek runtime."
        )
    },
    {
        "step": 3,
        "name": "Claude Opus 4.8",
        "model": "anthropic/claude-opus-4.8",
        "fallback_model": None,
        "role": "Types & Architecture Audit (ArtifactRef, Control Plane & Safe Replay)",
        "instructions": (
            "Jesteś głównym architektem systemowym i ekspertem ds. kontraktów i typowania (Claude Opus 4.8). "
            "Twoim zadaniem jest audyt architektury i typowania planu RAE-Suite Część 2.\n"
            "Przeanalizuj:\n"
            "1. Ścisłość typowania (TypeScript Branded Types) dla ArtifactRef, SagaStep, IdempotencyKey.\n"
            "2. Granice API Gateway / Control Plane i izolację wykonania Docker Proxy (/var/run/docker.sock).\n"
            "3. Spójność kontraktów kompensacji Sagi i bezpiecznego audytowego Replay'a.\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z ulepszoną architekturą i typowaniem."
        )
    },
    {
        "step": 4,
        "name": "GPT-5.6 Sol",
        "model": "openai/gpt-5.6-sol",
        "fallback_model": None,
        "role": "Performance & Resource Audit (Cache-Aside, Singleflight & Outbox)",
        "instructions": (
            "Jesteś inżynierem wydajności wysokoprzepustowych systemów rozproszonych (GPT-5.6 Sol). "
            "Twoim zadaniem jest audyt wydajnościowy planu RAE-Suite Część 2.\n"
            "Przeanalizuj:\n"
            "1. Utwardzenie cache semantycznego (singleflight / request coalescing, TTL jitter, negative caching, invalidation).\n"
            "2. Przepustowość Redis Streams, priorytetyzację wiadomości i minimalizację opóźnień API Gateway (HTTP 202 Async).\n"
            "3. Metryki wydajnościowe i SLO dla płynnego przepływu (Smooth Flow).\n"
            "Zwróć zwięzłą recenzję oraz zaktualizowane sekcje planu z optymalizacjami wydajnościowymi."
        )
    },
    {
        "step": 5,
        "name": "Fable 5",
        "model": "anthropic/claude-fable-5",
        "fallback_model": "anthropic/claude-opus-5",
        "role": "Reliability & ISO Auditability (Auditable Autonomy & Zero-Downtime)",
        "instructions": (
            "Jesteś ekspertem ds. niezawodności systemowej (SRE), bezpieczeństwa i norm ISO 27001/42001 (Fable 5). "
            "Twoim zadaniem jest audyt audytowalnej autonomii (Auditable Autonomy) i niezawodności planu RAE-Suite Część 2.\n"
            "Przeanalizuj:\n"
            "1. Gwarancje audytowalnej autonomii (SHA-256 hash chaining w MAES EventStore, ISO 27001/42001).\n"
            "2. Odporność na awarie workerów (crash resilience, zero lost tasks, safe compensation).\n"
            "3. Ostateczną spójność i kryteria ukończenia trwałego kręgosłupa wykonawczego RAE-Suite.\n"
            "Zwróć zwięzłą recenzję oraz ostateczny podsumowujący tekst poprawek dla planu Część 2."
        )
    }
]

def query_openrouter(model_id, fallback_model, system_prompt, user_content):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/RAE-Suite",
        "X-Title": "RAE-Suite Part 2 Consensus Engine"
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

def run_consensus_cycle_part2():
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        current_plan = f.read()

    audit_logs = []
    audit_logs.append("# RAE-Suite Part 2 OpenRouter Multi-Model Consensus Audit Trail\n")
    audit_logs.append(f"**Data wykonania:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for stage in AUDIT_STAGES:
        step_num = stage["step"]
        name = stage["name"]
        model = stage["model"]
        fallback = stage["fallback_model"]
        role = stage["role"]
        instructions = stage["instructions"]

        print(f"\n==================================================")
        print(f"PART 2 STEP {step_num}/5: {name} ({role})")
        print(f"Target Model: {model}")
        print(f"==================================================")

        prompt_text = (
            f"Oto aktualna wersja Szczegółowego Planu Rozwoju RAE-Suite Część 2 (Flow & Auditable Autonomy):\n\n"
            f"```markdown\n{current_plan}\n```\n\n"
            f"Proszę o przeprowadzenie audytu zgodnie z Twoją rolą ({role}).\n"
            f"1. Przedstaw listę konkretnych uwag, dostrzeżonych luk i rekomendacji usprawnień.\n"
            f"2. Przedstaw zaktualizowany, rozszerzony plan w formacie Markdown (doprecyzuj architekturę, DTO, Sagi, EventStore i Circuit Breaker)."
        )

        used_model, response = query_openrouter(model, fallback, instructions, prompt_text)

        log_entry = (
            f"## Krok {step_num}: {name} ({used_model})\n"
            f"**Rola:** {role}  \n"
            f"**Czas:** {time.strftime('%H:%M:%S')}  \n\n"
            f"### Wynik Audytu i Rekomendacje:\n\n"
            f"{response}\n\n"
            f"---\n\n"
        )
        audit_logs.append(log_entry)

        step_plan_path = os.path.join(DOCS_DIR, f"detailed_implementation_plan_part2_step{step_num}_{name.lower().replace(' ', '_')}.md")
        with open(step_plan_path, "w", encoding="utf-8") as f_step:
            f_step.write(f"<!-- Plan Część 2 po Kroku {step_num}: {name} ({used_model}) -->\n\n" + response)
        print(f"Zapisano plan cząstkowy: {step_plan_path}")

        current_plan = response
        time.sleep(2)

    with open(AUDIT_TRAIL_PATH, "w", encoding="utf-8") as f_trail:
        f_trail.write("".join(audit_logs))
    print(f"\n✓ Zapisano pełny audit trail Część 2: {AUDIT_TRAIL_PATH}")

    final_plan_header = (
        f"# Szczegółowy Iteracyjny Plan Rozwoju RAE-Suite Część 2 (Weryfikacja Konsensusem 5 AI)\n"
        f"**Wersja:** 2.1 (Flow & Auditable Autonomy - Konsensus OpenRouter Multi-Model)\n"
        f"**Zweryfikowano przez:**\n"
        f"1. GPT-5.6 Luna Pro (`openai/gpt-5.6-luna-pro`) - Event Sourcing, CQRS & Saga\n"
        f"2. DeepSeek R1 (`deepseek/deepseek-r1`) - Redis Streams, Concurrency & Semantic Watchdog\n"
        f"3. Claude Opus 4.8 (`anthropic/claude-opus-4.8`) - Claim Check, Control Plane & Branded Types\n"
        f"4. GPT-5.6 Sol (`openai/gpt-5.6-sol`) - Singleflight Cache, Outbox & Performance\n"
        f"5. Fable 5 / Opus 5 (`anthropic/claude-opus-5`) - Auditable Autonomy, Reliability & ISO\n\n"
        f"---\n\n"
    )
    with open(PLAN_PATH, "w", encoding="utf-8") as f_final:
        f_final.write(final_plan_header + current_plan)
    
    consensus_v2_path = os.path.join(DOCS_DIR, "RAE_CONSENSUS_PLAN_PART2.md")
    with open(consensus_v2_path, "w", encoding="utf-8") as f_v2:
        f_v2.write(final_plan_header + current_plan)

    print(f"✓ Zapisano ostateczny skonsolidowany plan Część 2 w: {PLAN_PATH}")
    print(f"✓ Zapisano zapasowy plan konsensusu w: {consensus_v2_path}")

if __name__ == "__main__":
    run_consensus_cycle_part2()
