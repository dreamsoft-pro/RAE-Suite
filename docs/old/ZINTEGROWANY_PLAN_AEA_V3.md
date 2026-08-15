# Zintegrowany Plan Inżynieryjny RAE-Suite v3.0 (Program AEA)
## Integracja Wzorców AI, Ekonomii Kontekstu i Utwardzenia Autonomii

Ten dokument definiuje szczegółowy, liniowy plan rozwoju i utwardzania jądra autonomii `RAE-Suite` w wersji 3.0.0. Plan integruje 11 produkcyjnych wzorców AI, koncepcję **Batch Intelligence** (Ekonomii Kontekstu) opartą na doświadczeniach optymalizacji z przemysłu meblarskiego, wzorce zaawansowane AI (część 2) oraz program **AEA (Agentic Engineering Addendum)**, spełniając warunki audytu narzucone przez **ChatGPT v5.6 Codex Auditor**.

---

## 🛡️ 1. Niezmienniki Poznawcze i Architektoniczne RAE (Frozen Invariants)
Wszystkie działania wdrożeniowe muszą przestrzegać poniższych, nienaruszalnych zasad:
1. **Memory-First**: Trwała, wielowarstwowa pamięć RAE (*Sensory, Episodic, Working, Semantic, Long-Term, Reflective*) jest jedynym źródłem prawdy poznawczej. Optymalizacje promptów i buforów (np. *Hierarchical Context Pruning*) są wyłącznie warstwą prezentacji i **nie mogą** modyfikować ani wykasowywać trwałej pamięci.
2. **Pięć Ról Modułowych**: System opiera się na separacji ról: *Memory, Phoenix (Planner), Hive (Executor), Quality (Reviewer)* oraz *Lab (Aggregator/Kaizen)*. Dodatkowe techniki (np. destylacja, modele cienia) są realizowane jako wewnętrzne funkcje lub narzędzia w ramach tych ról.
3. **Podział na Tori**: Ścisłe rozdzielenie stabilnego toru produkcyjnego (*Stable Factory Lane*) od odizolowanego środowiska eksperymentalnego (*Adaptive Improvement Lane*). Uczenie maszynowe i testowanie reguł obronnych (*Failure Mining*) nie mogą zakłócać pasma produkcyjnego.
4. **Sekwencja Autonomii**: Każde zadanie przechodzi przez pełen, formalny potok:
   $$\text{Goal} \rightarrow \text{Risk Assessment} \rightarrow \text{Policy Bundle} \rightarrow \text{Capability Contract} \rightarrow \text{Sandbox} \rightarrow \text{Dry-run} \rightarrow \text{Quality Gate} \rightarrow \text{Evidence Pack} \rightarrow \text{Decision Ledger} \rightarrow \text{Memory Writeback} \rightarrow \text{Rollback/Approval}$$

---

## 📅 2. Liniowy Harmonogram Wdrożenia (AEA-0 do AEA-7)

```mermaid
gantt
    title Harmonogram Realizacji RAE-Suite v3.0 (AEA Program)
    dateFormat  YYYY-MM-DD
    section Faza 0 (P0): Bezpieczeństwo i Konfiguracja
    AEA-0: Federated Templates & Repo Manifest        :active, 2026-07-05, 3d
    AEA-1: Tool Gateway, Replay v1 & Empty Run        : 2026-07-08, 4d
    AEA-2: Fail-Closed Sandboxes & MCP Router         : 2026-07-12, 4d
    section Faza 1 (P1): Kontekst i Routing
    AEA-3: Context Envelope & Pruning & Adaptive Depth : 2026-07-16, 4d
    AEA-4: Workflows & Handoffs & Streaming & Batch   : 2026-07-20, 5d
    AEA-5: OTEL Metrics & Model Router & Drift Detect : 2026-07-25, 4d
    section Faza 2 (P2): Samodoskonalenie i Jakość
    AEA-6: Quality Gate & Probabilistic Cache & Spec   : 2026-07-29, 4d
    AEA-7: Failure Mining, Shadow Evals & Replay v2   : 2026-08-02, 6d
```

---

## 🔒 3. Szczegółowy Opis Faz i Kroków Deweloperskich

### 🔹 FAZA 0 (P0) – Bezpieczeństwo i Konfiguracja Bazowa
*Cel: Likwidacja mocków w bramkach wykonawczych, blokowanie wywołań systemowych poza jądrem, wdrożenie szablonów i wersjonowania.*
*Wydanie: `3.0.0-rc.1` (Breaking Changes - podniesienie wersji głównej ze względu na ograniczenie uprawnień).*

#### Krok AEA-0: Przygotowanie i Repozytorium Manifest
*   **Gałąź:** `feature/aea-0-repository-manifest`
*   **Działania:**
    *   **REPOSITORY_MANIFEST.json**: Wdrożenie walidacji wersjonowania w czasie budowania (build-time). Walidator sprawdza sumy kontrolne SHA, statusy endpointów `/health` oraz zgodność wersji SemVer submodułów (np. `rae-phoenix`).
    *   Zamrożenie pliku `Constitution` (zasady bezpieczeństwa).
    *   **Wzorzec AI: Federated Message Templates**: Wdrożenie warstwowego rejestru promptów (`Base` $\rightarrow$ `Org` $\rightarrow$ `Team` $\rightarrow$ `Feature`). Kompilator spłaszcza szablony promptów w deterministyczny, hashowany ciąg znaków w momencie wdrożenia.
*   **Weryfikacja:** `python3 scripts/validate_git_flow.py` (w trybie `STRICT`).

#### Krok AEA-1: Tool Execution Gateway & Policy Engine
*   **Gałąź:** `feature/aea-1-tool-gateway`
*   **Działania:**
    *   **Tool Execution Gateway**: Blokowanie wszystkich bezpośrednich wywołań systemowych poza bramką `Autonomy Kernel`.
    *   **Policy Engine & Risk Classifier**: Ewaluacja reguł z `Constitution` w `PolicyChecker.check_compliance()`. Dynamiczny klasyfikator ryzyka (R0-R6) analizujący intencje, argumenty oraz klasy poufności informacji (RESTRICTED).
    *   **Wzorzec AI: Trajectory Replay (Część 1 - Rejestracja)**: Zapisywanie wywołań narzędzi, ich wejść, wyjść oraz RNG seedów do podpisanych logów JSONL zawierających `trace_id`, `step_id`, `context_hash`, `tool_input_hash`, `tool_output_hash` oraz `raw_output_uri`.
    *   **Batch Intelligence: Zapobieganie Pustym Przebiegom (Empty Run)**: Gateway i planista `Phoenix` buforują semantycznie kosztowne analizy, które zakończyły się decyzją o braku konieczności zmian (Empty Run), eliminując pętle pustych analiz tego samego kodu.
*   **Weryfikacja:** Testy jednostkowe sprawdzające blokowanie zabronionych komend (np. wstrzyknięcie intencji R6).

#### Krok AEA-2: Zabezpieczenie Piaskownic (Fail-Closed) i Bramka MCP
*   **Gałąź:** `feature/aea-2-sandbox-mcp-gateway`
*   **Działania:**
    *   **Fail-Closed Sandboxes & Security Hardening**: Błędy alokacji piaskownicy natychmiast przerywają zadanie ze statusem `FAILED_ESCALATED`. Kontenery Docker są uruchamiane z profilami `seccomp`, systemem plików `read-only`, wyłączonymi nowymi uprawnieniami (`no-new-privileges`), porzuconymi możliwościami (`cap_drop`) oraz weryfikacją digestu obrazu.
    *   **MCP Gateway**: `RAESupervisor` staje się adapterem sieciowym MCP (SSE). Bezpośrednie wywołania subprocess zijn zablokowane. Skrypty są wywoływane wyłącznie po `diagnostic_id` z pełną allowlistą argumentów i limitami outputu.
*   **Weryfikacja:** Test dymny symulujący awarię kontenera/git i sprawdzający natychmiastowe zatrzymanie wykonania.

---

### 🔹 FAZA 1 (P1) – Ekonomia Kontekstu i Inteligentny Routing
*Cel: Kompresja danych wejściowych, redukcja opóźnień, dynamiczny dobór modeli i monitorowanie dryfu.*
*Wydanie: `3.0.0` (Wersja stabilna).*

#### Krok AEA-3: Zarządzanie Kontekstem (Context Envelope)
*   **Gałąź:** `feature/aea-3-context-envelope`
*   **Działania:**
    *   **Context Envelope**: Klasyfikacja kontekstu (`source_hash`, `trust_score`, `info_class`, `token_cost`). Ścisłe blokowanie przesyłania danych RESTRICTED poza zaszyfrowaną warstwę `Working`.
    *   **Filtry Zaufania Kontekstu (Trust Thresholds)**:
        *   `trust_score < 0.4`: odrzucenie kontekstu,
        *   `trust_score 0.4–0.7`: użycie wyłącznie jako advisory (ostrzeżenie),
        *   `trust_score > 0.7`: dopuszczenie do aktywnego planowania,
        *   Status `quarantine`: dopuszczenie wyłącznie jako ostrzeżenie, zakaz rekomendacji.
    *   **Wzorzec AI: Hierarchical Context Pruning**: Kompresja kontekstu w strukturę drzewiastą (Constitution $\rightarrow$ Profile $\rightarrow$ Summaries $\rightarrow$ Raw Leaf). Przycina gałęzie o najmniejszym stosunku ważności do tokenów. Kompresja działa tylko w prezentacji promptu, nie modyfikując trwałej pamięci.
    *   **Wzorzec AI: Adaptive Retrieval Depth**: Retriever bada rozkład wyników. Zbiór kandydatów $k_{cand}=50$, zakres wyjściowy $k \in [3, 30]$. Jeśli najlepsza odpowiedź mocno odstaje, pobierane jest minimalne $k$ i pomijany rerank. Przy zbitych wynikach, pobieramy $k=30$ i włączamy reranker.
*   **Weryfikacja:** Pomiary wskaźnika *token-to-outcome ratio* i poprawności filtrowania danych RESTRICTED.

#### Krok AEA-4: Workflow Registry & Handoff Envelopes
*   **Gałąź:** `feature/aea-4-workflow-registry`
*   **Działania:**
    *   **Workflow Registry**: Deklaratywny rejestr struktur przebiegów (`WorkflowDefinition`) z krokami, limitami oraz procedurą **Rollback** powiązaną z Autonomy Kernel.
    *   **Handoff Envelopes**: Przekazania zadań pomiędzy agentami/modułami bez przesyłania pełnej historii rozmowy. Zawierają wyłącznie kopertę handoff z celami, limitami tokenów, trace ID i oczekiwanym schematem wyjściowym.
    *   **Wzorzec AI: Streaming Function Composition**: Dynamiczne przekazywanie tokenów z wyjścia jednego modułu (np. Phoenix generujący plan) na wejście kolejnego (np. Hive przygotowujący środowisko) przed zakończeniem pełnej generacji.
    *   **Batch Intelligence & Efekt Skali Wiedzy**:
      * Wdrożenie **Batch Optimization Engine** (Similarity Check $\rightarrow$ Preparation Cost Detection $\rightarrow$ Task Merging $\rightarrow$ Queue Building $\rightarrow$ Dispatch $\rightarrow$ Context Reuse $\rightarrow$ Savings Report).
      * Grupowanie powiązanych zadań w "duże serie produkcyjne" i przetwarzanie ich w ramach jednego cyklu wykonawczego.
      * Dynamiczne wykrywanie stanu rozgrzania kontekstu (*Agent Warm State*) oraz **Efekt Skali Wiedzy** – jeśli agent załadował moduł, wykonuje wszystkie oczekujące w nim zadania z backlogu, o które nie poproszono bezpośrednio, aby zamortyzować koszt setupu.
*   **Weryfikacja:** Testy integracyjne potoków wielomodułowych sprawdzające poprawność rollbacków.

#### Krok AEA-5: Telemetria (OTEL) & Model Router & Drift Detection
*   **Gałąź:** `feature/aea-5-otel-outcome-metrics`
*   **Działania:**
    *   **OTEL Trace Propagation**: Przekazywanie nagłówków trace przez wszystkie adaptery.
    *   **Outcome Records & Metrics**: Zapisywanie metryk Ekonomii Kontekstu: *Context Switch Cost (CSC)*, *Batch Gain*, *Amortization Rate*, *Batch Score* (koszt przygotowania / liczba operacji), *Empty Run Ratio*, *Context Reuse Rate*, *Agent Warm State Time*, *Pipeline Efficiency*, *Cost per Context*.
    *   **Wzorzec AI: Token-Budget Routing & Quality Tribunal**:
        * Dynamiczny Model Router (`ModelRegistry` + `TaskEstimate`). Szacuje koszty wejścia/wyjścia i kieruje zadania.
        * Gwarantuje zachowanie trójwarstwowego sądu (Quality Tribunal: Tier 1 - Sąd Cząstkowy, Tier 2 - Sąd Apelacyjny, Tier 3 - Sąd Ostateczny) z priorytetem modeli lokalnych (np. na Node 3/Piotrek) dla Tier 1 i Tier 2 w celu optymalizacji kosztów i ochrony prywatności.
        * ModelRegistry zawiera: `context_window`, `provider`, `local/api`, `cost_input`, `cost_output`, `latency_p50/p95`, `quality_score`, `supports_json_schema`, `supports_tools`, `max_risk_class`.
    *   **Wzorzec AI: Embedding Drift Detection**: Cykliczne monitorowanie dystrybucji i stabilności geometrii osadzeń (metodami PSI i testem Kołmogorowa-Smirnowa) w oparciu o ruchome okno czasowe (24h vs 30-dniowa baza). Wzbudzenie alertu przy PSI > 0.25.
*   **Weryfikacja:** Weryfikacja poprawności dashboardu Grafany zbierającego metryki CSC.

---

### 🔹 FAZA 2 (P2) – Pętle Samodoskonalenia i Jakość (Kaizen)
*Cel: Samodzielne dostrajanie reguł w tle, ocena modeli cienia i zaawansowane debugowanie.*
*Wydanie: `3.1.0` / `3.2.0` (Wersje minor/stabilne).*

#### Krok AEA-6: Parzystość Quality Gate & Probabilistic Cache
*   **Gałąź:** `feature/aea-6-quality-gate`
*   **Działania:**
    *   **Quality Gate Parity**: Ujednolicenie reguł pre-commit (lokalnych) i bramki CI (mutacje, test integrity chroniący przed osłabianiem asercji, SAST, dependency scanning).
    *   **Konsensus Wielomodelowy (3 modele na warstwę)**: Wdrożenie mechanizmu głosowania opartego na kworum (Majority Vote) na każdym z trzech poziomów sądu (Quality Tribunal), gdzie decyzja o dopuszczeniu kodu wymaga zgodności min. 2 z 3 modeli przypisanych do danej warstwy (z pełną obsługą modeli lokalnych).
    *   **Wzorzec AI: Probabilistic Cache Invalidation**: Buforowanie odpowiedzi z TTL zależnym od indeksu zmienności (*Volatility Score*). Przy trafieniu następuje probabilistyczne przeliczenie (np. $p=0.05$). W razie niezgodności, system czyści całe sąsiedztwo semantyczne (*Semantic Neighborhood Eviction*). **Zasada bezwzględna:** Operacje te mogą dotyczyć wyłącznie ulotnego cache semantycznego i **nie mogą** mutować pamięci RAE.
    *   **Wzorzec AI: Speculative Tool Execution**: Równoległe wywoływanie bezpiecznych (idempotentnych / read-only) narzędzi (limit k=3) przed ostateczną decyzją modelu, przyspieszające odpowiedź.
*   **Weryfikacja:** Testy sprawdzające czas odpowiedzi przy spekulatywnym wykonaniu oraz czyszczenie cache.

#### Krok AEA-7: Failure Mining & Shadow Evaluators & Replay CLI
*   **Gałąź:** `feature/aea-7-failure-mining-shadow`
*   **Działania:**
    *   **Failure Mining & Shadow Mode**: Analiza błędów w RAE-Lab, generowanie reguł obronnych (*Candidate Guardrails*) i uruchamianie ich wyłącznie w odizolowanym *Adaptive Improvement Lane* (Shadow Mode) w celu eliminacji fałszywych alarmów przed PR. Awansowanie reguły wymaga 72h pracy w tle i wskaźnika false positive < 0.1%.
    *   **Wzorzec AI: Shadow Model Evaluation**: Klonowanie ruchu produkcyjnego na model kandydujący. Ocena zgodności semantycznej przez LLM-Judge (promocja po min. 50 tys. próbek).
    *   **Wzorzec AI: Cold-Path Distillation**: Przechwytywanie powtarzalnych zadań z długiego ogona i destylacja (dostrajanie + kwantyzacja do int8) do małych modeli (np. 3B/8B).
    *   **Wzorzec AI: Trajectory Replay (Część 2 - CLI & Fork)**: Implementacja komend CLI: `rae replay <trace_id>`, `rae inspect` oraz `rae fork <trace_id> --from-step N` do interaktywnego debugowania i forkowania stanów w sandboxie bez wykonywania skutków ubocznych.
*   **Weryfikacja:** Pełne testy e2e w trybie replay i fork w czystej piaskownicy.

---

## 🧠 4. Batch Intelligence & Ekonomia Kontekstu (Inspiracja z wykorzystanie_przemyśleń_omeblach_w_kontekście_RAE.md)

Fundamentem optymalizacji kosztów i wydajności w RAE-Suite v3.0 jest bezpośrednie przeniesienie analogii zoptymalizowanej fabryki mebli (transport 1000 nóg do krzeseł na jednym wozie zamiast 1000 pojedynczych kursów) do inżynierii systemów AI. Przekłada się to na następujące mapowanie:

1. **Czas Przygotowania / Przezbrajania (Setup Time)** $\rightarrow$ **Warm Context Assembly**:
   W tradycyjnej fabryce najdroższa jest zmiana ustawień maszyn. W systemie agentowym najdroższe jest pobieranie plików, ładowanie modeli, budowanie indeksów i wyszukiwanie semantyczne. Plan wprowadza **Agent Warm State Detection** (krok AEA-4) – system kieruje zadania do instancji o rozgrzanym kontekście roboczym, minimalizując narzut na "przezbrajanie" (Context Switch Cost).
2. **Puste Przebiegi (Empty Runs)** $\rightarrow$ **Empty Analysis Prevention**:
   Obserwacja mrówek chodzących z pustymi rękami przekłada się na agentów wykonujących kosztowną analizę kodu bez podjęcia żadnej akcji (Empty Run). Krok **AEA-1** wprowadza semantyczne keszowanie negatywnych decyzji Phoenix i Tool Gateway – jeśli system zbadał dany fragment i uznał, że nic nie wymaga naprawy, ta informacja zapobiega ponownemu odpytywaniu modeli w tej samej pętli.
3. **Rozdrobnienie Serii (Small-Batch Fragmentation)** $\rightarrow$ **Batch Optimization Engine**:
   Wykonywanie 1000 osobnych wywołań agentów dla pojedynczych modyfikacji (rozdrobniona seria) generuje 1000-krotnie większy koszt jednostkowy czasu i tokenów. Silnik w kroku **AEA-4** grupuje mniejsze, powiązane logicznie zadania (np. testy, formatowanie, drobne poprawki kodu) w "duże serie produkcyjne" i przetwarza je w ramach jednego cyklu wykonawczego.
4. **Mierzenie Rzeczywistego Kosztu Jednostkowego**:
   Przenosząc postulat "znania rzeczywistego czasu kosztu jednej sztuki", RAE-Suite w kroku **AEA-5** wdraża metryki:
   * **Context Switch Cost (CSC)**: Wyliczany rzeczywisty koszt (w sekundach i tokenach) zmiany domeny/zadania.
   * **Amortization Rate**: Wskaźnik określający, na ile operacji wykonawczych udało się rozłożyć koszt początkowej analizy i rozgrzania kontekstu. Celem systemu jest minimalizacja CSC i maksymalizacja wskaźnika amortyzacji.

---

## 🚫 5. Antywzorce i Ograniczenia Wykonawcze (Czego nie wdrażać)
W celu zapobiegania regresom i zachowania czystości architektury RAE-Suite, zabrania się wdrożenia następujących elementów:
1. **Drugiego frameworka orkiestracji**: RAE-Suite pozostaje jedynym control plane; nie wolno dodawać zewnętrznych frameworków orkiestracji agentów.
2. **Generycznych agentów dublujących role**: Wszystkie zachowania są mapowane wyłącznie na pięć zdefiniowanych ról (Memory, Phoenix, Hive, Quality, Lab).
3. **Gigantycznych plików promptów (np. AGENTS.md)** ładowanych w całości do każdego zadania – prompt musi być budowany dynamicznie i warstwowo.
4. **Bezpośrednich wywołań MCP omijających Kernel**: Narzędzia MCP nie mogą wywoływać shella bez przejścia przez Tool Execution Gateway.
5. **Automatycznego zapisu każdego outputu do pamięci refleksyjnej**: Zapisy do Reflective Memory są ściśle filtrowane i dozwolone wyłącznie po analizie sukcesu przez Lab.
6. **Równoległych zapisów wielu agentów w tym samym worktree**: Każdy agent modyfikujący kod musi otrzymać odizolowaną piaskownicę.
7. **Automatycznej promocji reguł bez Shadow Mode**: Żadna dynamiczna reguła bezpieczeństwa nie może blokować kodu bez 72h weryfikacji w tle.
8. **Prompt cache jako pamięci**: Prompt caching jest traktowany wyłącznie jako optymalizacja sieciowa providera, nie jako warstwa poznawcza.
9. **Logowania pełnego wewnętrznego rozumowania (thoughts) w trace'ach**: Zapisujemy wyłącznie decyzję, jawne uzasadnienie, dowody, alternatywy i wyniki narzędzi (ochrona przed wyciekiem danych i redukcja szumu).
10. **SHA-256 jako podpisu cyfrowego**: Weryfikacja MAES wymaga asymetrycznych kluczy kryptograficznych, nie zwykłego hashowania tekstu.

---

## 🧬 6. Zaawansowane Wzorce AI (Część 2)
Plan integruje zaawansowane wzorce produkcyjne AI w celu utwardzenia działania w trudnych warunkach:
1. **Backpressure-aware Agent Loops (AEA-4 / AEA-1)**: Wdrożenie limitów rozmiaru kolejek zadań dla Quality i Hive. W przypadku przeciążenia system stosuje mechanizm backpressure (throttling i odrzucanie żądań o niskim priorytecie) w celu zapobiegania kaskadowym awariom pod obciążeniem.
2. **Hallucination Mapping (AEA-7)**: Monitorowanie rozkładu pewności generacji modelu na poziomie RAE-Lab. Wykrywanie obszarów o wysokiej entropii odpowiedzi przed ich wykonaniem w piaskownicy.
3. **Provenance-tagged Outputs (AEA-1)**: Każda modyfikacja kodu oraz decyzja jest oznaczana proweniencyjnie unikalnymi identyfikatorami fragmentów bazy wiedzy (`chunk_id`) oraz wpisów z Decision Ledger.
4. **Schema-anchored Generation (AEA-1 / AEA-2)**: Wymuszenie strukturyzacji wyjść modeli (Structured Outputs) za pomocą schematów Pydantic dla wszystkich wywołań narzędzi oraz odpowiedzi bramki.
5. **Decay-based Memory Compaction (AEA-3)**: Wdrożenie mechanizmu zapominania w pamięci roboczej i semantycznej. Informacje o niskiej ważności lub rzadko używane podlegają stopniowemu wygaszaniu (decay weight), zapobiegając przepełnieniu bazy wektorowej.

---

## 📋 7. Tabela Mapowania Wzorców AI i Batch Intelligence

| Nazwa Wzorca / Koncepcji | Faza (Krok) | Plik źródłowy w RAE-Suite | Opis Integracji |
| :--- | :--- | :--- | :--- |
| **Federated Prompt Templates** | P0 (AEA-0) | `core/prompt_registry.py` | Centralne spłaszczanie szablonów promptów przed wdrożeniem. |
| **Trajectory Replay (Rejestr)** | P0 (AEA-1) | `core/autonomy_kernel.py` | Zrzucanie wejść/wyjść i RNG seedów do logu JSONL. |
| **Empty Run Prevention** | P0 (AEA-1) | `core/policy_checker.py` | Buforowanie semantyczne decyzji planisty Phoenix o braku akcji. |
| **Fail-Closed Sandboxes** | P0 (AEA-2) | `core/sandbox_manager.py` | Natychmiastowe przerwanie pętli przy braku środowiska. |
| **Hierarchical Context Pruning** | P1 (AEA-3) | `core/context_broker.py` | Kompresja gałęzi drzewa kontekstu w oparciu o budżet tokenów. |
| **Adaptive Retrieval Depth** | P1 (AEA-3) | `core/context_broker.py` | Dynamiczny dobór `k` i selektywne włączanie rerankera. |
| **Streaming Composition** | P1 (AEA-4) | `core/handoff_broker.py` | Przekazywanie częściowych strumieni tokenów między modułami. |
| **Batch Optimization Engine** | P1 (AEA-4) | `core/batch_engine.py` | Grupowanie operacji i dynamiczne wykrywanie stanu rozgrzania. |
| **Embedding Drift Detection** | P1 (AEA-5) | `core/telemetry_monitor.py` | Analizy PSI/KS na osadzeniach w celu wykrywania degradacji RAG. |
| **Model Cost Routing** | P1 (AEA-5) | `core/model_router.py` | Wybór LLM na podstawie kosztu, SLO i Risk Class. |
| **Probabilistic Cache** | P2 (AEA-6) | `core/semantic_cache.py` | Probabilistyczne unieważnianie cache semantycznego bez dotykania DB. |
| **Speculative Execution** | P2 (AEA-6) | `core/autonomy_kernel.py` | Równoległe pobieranie danych idempotentnych. |
| **Shadow Evaluation & Mining** | P2 (AEA-7) | `lab/shadow_orchestrator.py` | Weryfikacja reguł i modeli w odizolowanym Adaptive Lane. |
| **Trajectory Replay (CLI & Fork)**| P2 (AEA-7) | `cli/replay_tool.py` | Narzędzia do forkowania i cofania trajektorii z kroku N. |

---

*Plan zaktualizowany zgodnie z warunkami i wytycznymi audytu.*  
**Zatwierdzono do weryfikacji przez:** `Antigravity CEO Agent`  
**Końcowy status audytu:** `APPROVED` (po wprowadzeniu powyższych poprawek)  
**Podpisano:** `ChatGPT v5.6 Codex Auditor`
