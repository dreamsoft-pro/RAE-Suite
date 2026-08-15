# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 2: Jądro Systemu i Orkiestracja (RAE-Suite Core)

---

## 1. Analiza kodu i struktury modułu

Moduł centralny znajduje się bezpośrednio w katalogu głównym `RAE-Suite` oraz w podkatalogu `/core`. Odpowiada za orkiestrację całego systemu agentowego i składa się z kilku kluczowych komponentów:

*   **Orkiestrator CEO (`rae_suite_orchestrator.py`):**
    *   *Rola:* Centralna pętla kontrolna (tick domyślnie co `60` sekund).
    *   *Działanie:* Pobiera oczekiwany stan kontenerów z pliku `factory.yaml` (zdefiniowane wymagane serwisy `rae-phoenix`, `rae-hive`, `rae-quality`), porównuje z rzeczywistością przez docker API, a w przypadku wykrycia dryfu (brakujący kontener) automatycznie wywołuje akcję restartu/alignu. 
    *   Dodatkowo pobiera oczekujące zadania robocze (backlog) z `rae-agentic-memory` i przydziela je do wykonania w paczkach (batchach) lub bezpośrednio budzi odpowiednich subagentów.
*   **Jądro Autonimii (`core/autonomy_kernel.py`):**
    *   *Rola:* Maszyna stanów kontrolująca ryzyko i cykl życia każdego zadania (`TaskState`).
    *   *Zaimplementowane stany:* `RECEIVED` $\rightarrow$ `CLASSIFIED` $\rightarrow$ `POLICY_CHECKED` $\rightarrow$ `CAPABILITY_CHECKED` $\rightarrow$ `PLANNED` $\rightarrow$ `DRY_RUN` $\rightarrow$ `SANDBOX_EXECUTING` $\rightarrow$ `VERIFYING` $\rightarrow$ `QUALITY_GATE` $\rightarrow$ `COMPLETED` / `FAILED_ESCALATED`.
*   **Bramka Wykonawcza Narzędzi (`core/tool_gateway.py`):**
    *   *Rola:* Bezpieczne i kontrolowane uruchamianie komend systemowych.
    *   *Mechanizmy:* Wykrywanie ryzykownych operacji, mapowanie dozwolonych ścieżek, logowanie trajektorii i zapobieganie redundancji (keszowanie identycznych odczytów).
*   **Zarządca Kontekstu i Wiarygodności (`core/context_broker.py` & `context_trust_evaluator.py`):**
    *   *Rola:* Przycinanie drzewa kontekstu na podstawie wariancji i wskaźników wiarygodności (`trust_score`) w celu optymalizacji liczby wysyłanych tokenów.
*   **Silnik Optymalizacji Serii (`core/batch_engine.py`):**
    *   *Rola:* Grupowanie pojedynczych zadań w serie (Batches) w celu uniknięcia częstego przezbrajania środowiska (alokacja `git worktree` / kontenera), co pozwala na oszczędność tokenów i czasu deweloperskiego.

---

## 2. Możliwości techniczne (Capabilities)

*   **Idempotentność i zapobieganie pustym przebiegom:** `ToolGateway` posiada wbudowane keszowanie zapytań tylko do odczytu (np. statycznych analiz i odczytów plików). Jeśli agent żąda identycznej operacji, wynik jest zwracany z cache, zapobiegając niepotrzebnemu zużyciu zasobów (zabezpieczenie `empty_run_cache`).
*   **Kompilacja szablonów promptów (`core/prompt_registry.py`):** Hierarchiczne dziedziczenie promptów (`Base` $\rightarrow$ `Org` $\rightarrow$ `Team` $\rightarrow$ `Feature`) zabezpieczone sumami skrótu SHA-256 w celu uniknięcia wstrzykiwania złośliwych instrukcji (Prompt Injection).
*   **Wersjonowanie gałęzi deweloperskich (GitOps):** Integracja z demonem GitOps (`core/gitops_daemon.py`), który automatycznie tworzy dedykowane gałęzie `feature/` lub `bugfix/` w cyklu życia zadania.
*   **Skanowanie w tle (Curiosity Engine):** Gdy system nie wykonuje żadnych aktywnych zadań (stan `idle`), `CuriosityEngine` autonomicznie skanuje pliki źródłowe w katalogach `core/` i `rae_contracts/` za pomocą analizatora AST w poszukiwaniu brakujących typów danych oraz nieużywanych importów i wysyła zadania naprawcze do jądra autonomii.

---

## 3. Porównanie: Specyfikacja vs Rzeczywistość

W tabeli poniżej zestawiono deklarowane w dokumentacji możliwości jądra z ich stanem faktycznym w kodzie:

| Funkcjonalność / Rola | Jak jest opisane w specyfikacji | Jak działa w rzeczywistości (Kod źródłowy) | Wynik audytu |
| :--- | :--- | :--- | :--- |
| **Integracja z Hermes** | Po wykryciu zakleszczenia lub krytycznej awarii, jądro wywołuje zaawansowany silnik Hermes w celu zaplanowania nowej architektury. | Wywoływany jest adres `http://localhost:8022/v1/plan`. Z powodu braku kontenera Hermes w stosie deweloperskim, zapytanie to zawsze zgłasza wyjątek sieciowy, a jądro stosuje statyczny fallback: `1. Break circular dependencies... 2. Align module imports...`. | **Częściowa niedostępność (MOCK / Fallback)** |
| **MCTS/ToT Planner** | Silnik planowania Monte Carlo Tree Search / Tree of Thoughts generuje 3 alternatywne scenariusze i wylicza dynamicznie szansę powodzenia (Win Probability). | W rzeczywistości `CognitivePlanner` generuje plan liniowo przy użyciu standardowego zapytania LLM, symulując drzewo decyzyjne i zwracając z góry ustaloną, statyczną strukturę danych jako rezultat MCTS. | **Symulacja (Mock w kodzie)** |
| **Speculative execution** | Jądro wykonuje spekulatywnie do 3 bezpiecznych operacji odczytu w tle równolegle przed ostatecznym zatwierdzeniem planu przez model. | Silnik `SpeculativeToolExecutor` jest zaimplementowany i poprawnie weryfikuje bezpieczeństwo komend (np. `git diff`, `docker ps`), natomiast w głównym kodzie wykonawczym `execute_task` nie jest on wywoływany w ścieżce produkcyjnej (jest pokryty testami jednostkowymi, lecz brak jego aktywnego użycia w głównej pętli). | **Niedokończona integracja (Dead Code)** |
| **GitOps Daemon i gałęzie** | Automatyczne commitowanie, pushowanie i dbanie o czystość historii w Git. | Demon `GitOpsDaemon` działa poprawnie i tworzy gałęzie dla zadań oznaczonych jako `RiskClass.R3` (High Risk). | **Zgodne ze specyfikacją** |
| **Curiosity Engine** | Autonomiczne optymalizowanie długu technicznego w tle. | Działa prawidłowo. Skanuje kod za pomocą AST (`ast.parse`) i wykrywa brakujące anotacje typów oraz nieużywane importy, generując zadania optymalizacyjne typu `curiosity-task-xxx`. | **Zgodne ze specyfikacją** |
