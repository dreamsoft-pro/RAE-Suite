# test_factory_impulse.py
import requests
import json
from datetime import datetime

TENANT_UUID = "66435998-b1d9-5521-9481-55a9fd10e014"
BASE_URL = "http://rae-api-dev:8000/v2/memories"
HEADERS = {"X-Tenant-Id": TENANT_UUID, "Content-Type": "application/json"}

def log_to_rae(title, content, label):
    payload = {
        "content": f"[{title}] {content}",
        "metadata": {
            "type": "process_log",
            "swarm_id": "test_impulse_001"
        },
        "project": "screenwatcher",
        "human_label": label
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS)
    return resp.status_code

def run_test():
    print("🚀 Rozpoczynam impuls testowy Fabryki RAE...")
    
    # 1. Krok Phoenixa
    print("-> Symulacja pracy Phoenix (Planowanie poprawki)...")
    log_to_rae("PHOENIX_PLAN", "Zaproponowano optymalizację pętli sumowania w collector/admin.py w celu redukcji złożoności O(n).", "Planowanie Optymalizacji Collector")
    
    # 2. Krok Quality
    print("-> Symulacja pracy Quality (Skanowanie bezpieczeństwa)...")
    log_to_rae("QUALITY_SCAN", "Skan Bandit zakończony statusem SUCCESS. Nie wykryto podatności typu SQL Injection w nowym kodzie.", "Audyt Bezpieczeństwa Poprawki")
    
    # 3. Krok Lab
    print("-> Symulacja pracy Lab (Wnioski Kaizen)...")
    log_to_rae("LAB_INSIGHT", "Optymalizacja skróciła czas generowania raportu o 15%. Wynik Lean: 0.85.", "Wniosek Kaizen: Wydajność Raportowania")

    print("✅ Impuls zakończony. Wszystkie zdarzenia zapisane w RAE.")

if __name__ == "__main__":
    run_test()
