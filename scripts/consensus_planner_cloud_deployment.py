#!/usr/bin/env python3
"""
RAE-Suite Cloud Deployment & Keycloak Multi-Agent Consensus Planner.
Consults expert models via OpenRouter to audit:
1. GPT-5.6 Luna Pro: Keycloak OIDC configuration, Client scopes, User authentication & RBAC
2. DeepSeek R1: Concurrency, Network routing, SSL Ingress, Failover & Remote Inference routing
3. Claude Opus 4.8: Kubernetes manifests, PVCs, Ceph SSD storage, Service mesh & Security hardening
4. GPT-5.6 Sol: Database migration (PostgreSQL pgvector, Qdrant), Data integrity & Performance
5. Fable 5: ISO 27001 / ISO 42001 compliance, Agent Access Tokens, Audit Trails & Synthesis
"""

import os
import sys
import json
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("consensus-cloud-deployment")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY is not set!")
    sys.exit(1)

MODELS = [
    ("GPT-5.6 Luna Pro", "openai/gpt-5.6-luna-pro", "Keycloak OIDC Configuration, Client Scopes, User Auth (lesniowskig@gmail.com) & RBAC Gateway"),
    ("DeepSeek R1", "deepseek/deepseek-r1", "Adversarial Architecture Review: Remote LLM Delegation (Node1, Node3, Laptop), SSL Ingress, Fail-Closed Security"),
    ("Claude Opus 4.8", "anthropic/claude-opus-4.8", "Kubernetes Manifests (Namespace rae, Ingress traefik, Ceph RBD SSD PVCs, Service routing)"),
    ("GPT-5.6 Sol", "openai/gpt-5.6-sol", "Data Migration (pgvector, Qdrant vectors, Redis), Live Sync & Zero-Data-Loss Verification"),
    ("Fable 5", "anthropic/claude-opus-5", "ISO 27001/42001 Compliance, Agent Authentication, Multi-Device Access & Final Synthesis")
]

BASE_PLAN = """
# Plan Wdrożenia RAE-Suite na Chmurze Kubernetes (rae.dreamsoft.pro)

## 1. Architektura i Komponenty
- **Domena i SSL**: `rae.dreamsoft.pro` zabezpieczona certyfikatem Let's Encrypt (`letsencrypt-prod` ClusterIssuer, Ingress Traefik).
- **Namespace K8s**: `rae`
- **Pamięć trwała (Ceph RBD SSD)**:
  - `rae-postgres-data` (10Gi) - PostgreSQL 16 + pgvector (`ankane/pgvector:latest`)
  - `rae-qdrant-data` (10Gi) - Qdrant Vector DB (`qdrant/qdrant:latest`)
  - `rae-redis-data` (5Gi) - Redis 7 (`redis:7-alpine`)
- **Usługi Aplikacyjne**:
  - `rae-memory`: Silnik pamięci RAE (FastAPI port 8000)
  - `rae-portal`: Dashboard / Web UI (NiceGUI port 8080)
  - `rae-supervisor` / `rae-mcp`: Serwer MCP (port 8005) dla agentów AI
  - `rae-suite`: Orkiestrator procesów (port 8009)
- **Routing Ingress**:
  - `/api/` -> `rae-memory:8000`
  - `/mcp/`, `/sse` -> `rae-supervisor:8005`
  - `/` -> `rae-portal:8080` (zabezpieczone Keycloak OIDC)

## 2. Uwierzytelnianie Keycloak (auth.cloud.printworks.pl)
- **Realm**: `master` (lub dedykowany `rae`)
- **Klient**: `rae-portal` (Public OIDC client z PKCE, redirect: `https://rae.dreamsoft.pro/callback`)
- **Klient API**: `rae-memory-api` (Bearer JWT / JWKS RS256 validation)
- **Użytkownicy**:
  - Główny użytkownik: `lesniowskig@gmail.com` (hasło: `042121LMlmlmRae!@#$`)
  - Możliwość ręcznego dodawania kolejnych użytkowników w Keycloak Console.
- **Autoryzacja Agentów**: Klucze API (`X-API-Key`) oraz tokeny Keycloak dla zewnętrznych agentów i urządzeń.

## 3. Delegacja Obliczeń LLM (Zero-GPU Cloud Footprint)
- Chmura nie posiada dedykowanego GPU do ciężkich modeli LLM.
- Wszystkie zadania inferencji i rozumowania (LLM) są delegowane do:
  - Laptopa lokalnego: `http://100.77.51.15:11434`
  - Node 1 (Lumina - i7-14700KF, RTX 4080, 64GB RAM): `100.68.166.117`
  - Node 3 (Piotrek - Ollama Proxy): `172.30.15.11:11434` / `100.109.20.121:11434`

## 4. Migracja Danych z Laptopa do Chmury
- Eksport bazy PostgreSQL (pgvector) `rae` z kontenera lokalnego i import do k8s PostgreSQL.
- Eksport i transfer wektorów Qdrant (`memories`) z lokalnego Qdrant do k8s Qdrant.
- Weryfikacja spójności (liczba wspomnień, relacje grafowe, metadane).
"""

def query_openrouter(model_id: str, prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rae.dreamsoft.pro",
        "X-Title": "RAE-Suite Cloud Consensus Planner"
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Jesteś Głównym Architektem Bezpieczeństwa i Chmury Silicon Oracle RAE Suite. Dokonaj szczegółowej, rygorystycznej recenzji planu wdrożenia. Odpowiadaj w formacie github markdown po polsku, wskazując konkretne zalecenia techniczne, konfiguracje i zabezpieczenia."},
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
    logger.info("Starting Multi-Agent Consensus Planning for RAE-Suite Cloud Deployment...")
    reviews = []
    
    for name, model_id, focus in MODELS:
        logger.info(f"==> Querying {name} ({model_id}) on: {focus}...")
        prompt = f"""
Przeanalizuj poniższy Plan Wdrożenia RAE-Suite na Chmurę Kubernetes pod kątem Twojej specjalizacji: **{focus}**.

Oto Plan Bazowy:
{BASE_PLAN}

Podaj konkretne, rygorystyczne wytyczne techniczne:
1. Dokładna weryfikacja i zalecane konfiguracje (K8s YAML, Keycloak OIDC, Ingress, Routing API).
2. Zabezpieczenia (TLS, PKCE, CORS, fail-closed, ochrona sekretów, rotacja tokenów).
3. Strategia bezpiecznej migracji danych (pg_dump/pg_restore dla pgvector, Qdrant snapshots).
4. Konfiguracja agentów łączących się zdalnie przez MCP/REST z innych urządzeń.
"""
        response = query_openrouter(model_id, prompt)
        reviews.append((name, focus, response))
        logger.info(f"Received response from {name}.")

    output_path = "/home/grzegorz/cloud/RAE-Suite/docs/RAE_SUITE_CLOUD_DEPLOYMENT_PLAN.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 🏛️ RAE-SUITE CLOUD DEPLOYMENT & KEYCLOAK INTEGRATION PLAN\n\n")
        f.write("## 📋 Wstępny Plan Bazowy\n\n")
        f.write(BASE_PLAN)
        f.write("\n\n---\n\n## 🧠 Wyniki Rzeczywistych Konsultacji Multi-Agent Consensus (OpenRouter Live API)\n\n")
        for name, focus, review in reviews:
            f.write(f"### 🛡️ Recenzja: {name}\n")
            f.write(f"**Obszar ekspertyzy**: {focus}\n\n")
            f.write(review)
            f.write("\n\n---\n\n")
            
    logger.info(f"Consensus plan written to {output_path}")

if __name__ == "__main__":
    main()
