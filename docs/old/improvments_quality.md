# Iteracyjny Plan Poprawy Jakości Kodu (RAE-Suite v3.0)

Ten dokument zawiera ustrukturyzowany, zatwierdzony przez **ChatGPT v5.6 Codex Auditor** plan poprawy jakości jądra RAE-Suite. Wdraża on zasady *Context Economy*, *11 wzorców AI* oraz zapewnia pełną ochronę niezmiennych architektury RAE (*RAE Invariants*).

---

## 💻 Ocena Wykonalności Sprzętowej (Środowisko Lokalne ZBook)

*   **Specyfikacja:** Core i7 (6-8 rdzeni), 64GB RAM, NVIDIA Quadro RTX 5000 (16GB VRAM), 1TB SSD.
*   **Werdykt:** **TAK, stos jest w pełni wykonalny lokalnie.**
*   **Uzasadnienie & Warunki Pracy:**
    *   **RAM:** Pamięć 64GB pozwala na bezproblemowe uruchomienie kontenerów SonarQube, Trivy, Postgres, Redis oraz lokalnych instancji LLM (np. Llama 3 8B / DeepSeek 7B w Ollamie). Stos bazowy zużywa ok. 12-16GB RAM, co pozostawia ponad 40GB wolnej przestrzeni roboczej.
    *   **VRAM:** RTX 5000 (16GB VRAM) pozwala na pełne oddelegowanie wnioskowania lokalnych modeli bez obciążania procesora systemowego (CPU).
    *   **Krytyczna Liniowość (Sekwencyjność):** Skanery bezpieczeństwa (DAST OWASP ZAP), fuzzery (Schemathesis) oraz testy mutacyjne (`mutmut`) muszą być uruchamiane **sekwencyjnie** w ramach potoków PR/CI. Równoległe uruchomienie tych procesów doprowadzi do throttlingu CPU oraz I/O, powodując błędy flakiness i timeouts w testach.

---

## 📅 Harmonogram Wdrożenia

Każdy etap będzie wdrażany jako osobne wydanie SemVer 2.0.0. Ze względu na usunięcie mocków i wartości domyślnych z bramki jakości, Iteracja 1 rozpocznie główny cykl wydawniczy `3.0.0-rc.1`.

### 1. Iteracja 1: Deterministic Core & Fixes (Wydanie: `3.0.0-rc.1`)
*   **Błędy CoverageEngine:**
    *   Naprawienie braku importu modułu `json` w RAE-Quality.
    *   Prawidłowa obsługa kodów wyjścia (exit codes) pytest.
    *   Dodanie czyszczenia starych plików `coverage.json` przed każdym testem w celu zapobieżenia odczytowi nieaktualnych raportów.
*   **Usunięcie wartości domyślnych (Mock-free Quality Gate):**
    *   Zastąpienie domyślnych wartości (np. `coverage = 0.85`, `type_safety = 0.90`) w przypadku braku danych ze skanera bezwzględnym błędem bramki jakościowej (`status: ERROR`).
*   **Utrwalanie Wyników (Memory-First):**
    *   Zapisywanie wyników każdego audytu (`QualityGateResult`) oraz powiązanych struktur `EvidencePack` w trwałej pamięci RAE-Memory (warstwa *Long-Term/Reflective*).
*   **Wersjonowane Polityki Jakości (Quality Policy as Code):**
    *   Wydzielenie progów jakościowych (coverage, typowanie, dopuszczalne podatności) do zewnętrznego pliku `quality_policy.yaml`.
    *   Wprowadzenie deterministycznej walidacji schematu dla polityk za pomocą biblioteki Pydantic.
*   **Kontrola Pętli Naprawczej (Phoenix Safeguards):**
    *   Ograniczenie automatycznej pętli naprawczej Phoenixa do maksymalnie 3 prób.
    *   Implementacja *circuit breakera* — po 3 nieudanych próbach generowany jest zrzut pełnej trajektorii do pliku JSONL celem analizy offline (`rae replay`).
    *   Ścisła blokada uprawnień: agent generujący (`Phoenix` - rola Plannera) ma całkowity zakaz modyfikacji plików polityk, testów (w celu ich "wyzielenia") oraz konfiguracji SonarQube.

### 2. Iteracja 2: Static Analysis & Security Gateways (Wydanie: `3.1.0`)
*   **Skaner Trivy:**
    *   Integracja skanera podatności paczek językowych, obrazów OCI/Docker oraz IaC (Terraform, Kubernetes config).
    *   **Bezpieczeństwo:** Całkowity zakaz montowania socketu `/var/run/docker.sock` do agentów. Obrazy przekazywane są jako archiwum OCI, lub skanowane przez oddzielny serwer Trivy.
*   **Skaner Gitleaks:**
    *   Wprowadzenie automatycznego skanowania sekretów i kluczy API na poziomie diffa w Pull Request oraz integracji z hookiem `pre-commit`.
    *   Zasada bezwzględna: wykryty klucz = natychmiastowe odrzucenie zmiany (klucz musi być unieważniony, nie tylko usunięty z historii).
*   **Integracja z SonarQube:**
    *   Konfiguracja oficjalnego SonarQube MCP Server w trybie tylko do odczytu (`SONARQUBE_READ_ONLY=true`).
    *   Wdrożenie webhooka SonarQube z weryfikacją podpisu HMAC-SHA256 w `RAE-Quality` do asynchronicznego odbierania statusu Quality Gate.

### 3. Iteracja 3: Advanced Verification & API Fuzzing (Wydanie: `3.2.0`)
*   **Differential Mutation Testing:**
    *   Integracja narzędzia `mutmut` (Python) oraz `StrykerJS` (TypeScript).
    *   **Optymalizacja:** Aby uniknąć degradacji wydajności na laptopie, testy mutacyjne uruchamiane są w trybie przyrostowym (differential) — wyłącznie dla linii kodu zmodyfikowanych w ramach aktualnego Pull Requestu (czas wykonania < 5 minut).
*   **Schemathesis (API Contract Testing):**
    *   Automatyczne fuzzowanie API FastAPI na podstawie wygenerowanego kontraktu OpenAPI w celu wykrywania nieobsługiwanych wartości brzegowych i błędów HTTP 500.
*   **Eliminacja Pustych Przebiegów (Empty Run Prevention):**
    *   Dodanie algorytmu wykrywającego, czy zmiana na PR dotyczy wyłącznie dokumentacji, testów czy kodu wykonywalnego. Jeśli pliki binarne lub kod logiczny nie uległy zmianie, ciężkie skany są pomijane.
*   **OWASP ZAP (DAST):**
    *   Uruchomienie OWASP ZAP Baseline na każdym PR w celu aktywnego wykrywania podatności webowych.

### 4. Iteracja 4: Dependency Hygiene & Secure Supply Chain (Wydanie: `3.3.0`)
*   **Automatyzacja Zależności (Renovate):**
    *   Wdrożenie Renovate w wersji self-hosted w celu aktualizacji paczek Pythona, npm i obrazów Docker.
    *   Konfiguracja automatycznego scalania (automerge) wyłącznie dla wersji patch przy 100% zielonym pipeline i braku zmian w licencjach bibliotek.
*   **CycloneDX SBOM & Cosign:**
    *   Generowanie SBOM (Software Bill of Materials) dla każdego zbudowanego obrazu RAE-Suite.
    *   Podpisywanie artefaktów za pomocą narzędzia Cosign.
    *   Generowanie metadanych pochodzenia (provenance) zgodnie ze standardem SLSA Build Level 2.
    *   **Bramka wdrożeniowa (Fail-Closed):** Próba wdrożenia kontenera bez podpisów i SBOM skutkuje natychmiastowym przerwaniem procesu.
