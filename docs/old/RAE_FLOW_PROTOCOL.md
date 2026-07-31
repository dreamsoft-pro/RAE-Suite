# 📜 RAE SUITE: TWARDY KONTRAKT FLOW (v1.0)
Status: **MANDATORY ENFORCEMENT**

## 🎯 FUNDAMENTY OPERACYJNE
1. **DETERMINIZM**: Każdy etap musi zakończyć się mierzalnym artefaktem (Evidence Pack, Contract, Code, Test Report).
2. **ZERO-WARNING POLICY**: Proces zostaje wstrzymany przy dowolnym ostrzeżeniu lintera lub błędu typu.
3. **ENTERPRISE AUDIT**: Każda operacja agenta MUSI być dekorowana przez `@audited_operation` z automatycznym mapowaniem projektu na tenant.
4. **MODULAR AUTONOMY**: Moduły komunikują się przez MCP (SSE) – nigdy bezpośrednio do bazy innego modułu.

## 🚀 PIPELINE: SZEŚĆ STOPNI DETERMINIZMU

### ETAP 1: ONTOLOGICAL INGESTION (DISCOVERY)
- **Cel**: Zrozumienie kontekstu przed działaniem.
- **Refactor**: Ekstrakcja logiki biznesowej do "Evidence Pack".
- **Create**: Rozszerzenie intencji o standardy "Institutional Memory".
- **Narzędzia**: `RAE-Phoenix` + `RAE-agentic-memory` (Semantic Layer).

### ETAP 2: BEHAVIOR-DRIVEN CONTRACTING
- **Cel**: Definicja "Co" budujemy, a nie "Jak".
- **Działanie**: Generowanie i zatwierdzenie pliku `.contract.yml`.
- **Narzędzia**: `RAE-Core` (Supreme Council / L3 Reasoning).

### ETAP 3: SWARM EXECUTION (HIVE)
- **Cel**: Produkcja wysokiej jakości kodu.
- **Działanie**: Pętla Writer-Auditor. Writer generuje, Auditor weryfikuje przeciwko kontraktowi.
- **Narzędzia**: `RAE-Hive` (Multi-Agent Swarm).

### ETAP 4: HARD FRAMES & DETERMINISTIC VALIDATION
- **Cel**: Gwarancja bezpieczeństwa i poprawności.
- **Działanie**: Izolacja sieciowa, testy jednostkowe, skanery ISO 27001 / 42001.
- **Narzędzia**: `RAE-Quality` (Sentinel).

### ETAP 5: OBSERVABILITY & TELEMETRY INJECTION
- **Cel**: Monitoring zachowania systemu.
- **Działanie**: Wstrzykiwanie hooków OpenTelemetry i rejestracja w Grafanie.
- **Narzędzia**: `RAE-Lab` (Analityka).

### ETAP 6: GOVERNANCE & META-REFLECTION
- **Cel**: Nauka systemu na błędach i sukcesach.
- **Działanie**: Zamknięcie audytu, aktualizacja wag MAB (Multi-Armed Bandit).
- **Narzędzia**: `RAE-Core` (Reflective Layer).

## 🛠️ REFINEMENT LOOP
Dla każdego konkretnego zadania, **Orkiestrator** musi:
1. Pobrać ten kontrakt.
2. Uszczegółowić parametry dla każdego etapu (np. jakie konkretnie testy w Etapie 4).
3. Zapisać "Job Plan" w warstwie Working pamięci.
