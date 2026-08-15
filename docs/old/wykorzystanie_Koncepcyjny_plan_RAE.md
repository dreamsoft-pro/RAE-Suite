# Koncepcyjny plan wykorzystania artykułu w rozwoju RAE-Suite

## 1. Wniosek główny

**Tak, artykuł można wykorzystać do rozwoju RAE-Suite, ale nie jako nową architekturę.**

Powinien zostać potraktowany jako:

1. zewnętrzna lista kontrolna dojrzałości agentowej,
2. wspólny słownik pojęć dla dokumentacji,
3. źródło praktyk operacyjnych,
4. podstawa do sprawdzenia, czy istniejące koncepcje RAE są faktycznie egzekwowane w kodzie.

Artykuł opisuje agent loop, stan, planner/executor, router/specjalistów, workflow files, MCP, pamięć, subagentów, sandboxing, permissions, hooks, ochronę przed prompt injection, structural linting, tracing, logging i metrics.

Większość z tych pojęć **już znajduje się w architekturze RAE-Suite**, często w bardziej zaawansowanej formie. RAE nie powinno więc kopiować artykułu, lecz domknąć różnicę pomiędzy:

> „mamy to opisane w architekturze”

a:

> „żadna akcja nie może ominąć tego mechanizmu w działającym systemie”.

RAE-Suite jest już definiowane jako Control Plane refleksyjnej fabryki, `rae-core` jako wspólny protokół poznawczy i dowodowy, a samodoskonalenie jako osobny Improvement Plane.

---

# 2. Czego nie wolno zmieniać

Poniższe elementy powinny zostać uznane za **zamrożone niezmienniki architektoniczne**.

## 2.1. Memory-first, nie context-window-first

RAE-agentic-memory pozostaje centralną warstwą trwałej poznawczej ciągłości:

* sensory memory,
* episodic memory,
* working memory,
* semantic memory,
* long-term memory,
* reflective memory.

Najważniejszym wyróżnikiem jest przechowywanie nie tylko „co się wydarzyło”, lecz także „dlaczego podjęto decyzję”.

Artykułowa koncepcja `MEMORY.md` może być wykorzystana najwyżej jako niewielki lokalny cache startowy. **Nie może zastąpić warstwowej pamięci RAE.**

## 2.2. Zachowanie pięciu ról modułowych

Pozostają:

* **RAE-agentic-memory** — pamięć i refleksja,
* **Phoenix** — planowanie, architektura i naprawa,
* **Hive** — wykonanie,
* **Quality** — niezależna bramka jakości,
* **Lab** — eksperymenty, pomiary i Kaizen.

Ten podział jest już rdzeniem repozytorium.

Nie należy tworzyć obok nich nowych, generycznych modułów `PlannerAgent`, `ExecutorAgent` czy `ReviewerAgent`. Wzorce z artykułu należy odwzorować na istniejące działy:

| Wzorzec z artykułu     | Odpowiednik RAE           |
| ---------------------- | ------------------------- |
| Planner                | Phoenix                   |
| Executor               | Hive                      |
| Router                 | RAE-Suite / Fabric        |
| Reviewer               | Quality                   |
| Aggregator / learning  | Lab                       |
| Persistent memory      | RAE-agentic-memory        |
| Independent governance | Autonomy Kernel + Auditor |

## 2.3. Stable Factory Lane i Adaptive Improvement Lane

Nowe workflow, reguły, umiejętności i strategie nie mogą trafiać bezpośrednio do produkcyjnego toru wykonania.

Architektura RAE już rozdziela:

* stabilny tor produkcyjny,
* adaptacyjny tor eksperymentalny,
* shadow runs,
* replay,
* failure mining,
* promocję dopiero po quality i policy gates.

## 2.4. Zamrożona sekwencja autonomii

Należy zachować dotychczasowy szkielet:

`goal → risk assessment → policy bundle → capability contract → sandbox/worktree → dry-run → quality gate → evidence pack → decision ledger → memory writeback → rollback/approval → evaluation harness`

Jest on znacznie dojrzalszy niż prosty model `Think → Act → Observe`.

Fundamentalne zasady pozostają:

* **Zero Uncontrolled Action**,
* **No Evidence, No Autonomy**,
* R0–R6,
* deny-by-default,
* R4–R5 wymagające zatwierdzenia,
* R6 zawsze blokowane,
* pełna odtwarzalność decyzji.

---

# 3. Najważniejszy wynik przeglądu kodu

Dokumentacja RAE-Suite jest obecnie bardziej dojrzała niż część wykonawcza.

Kontrakty są dobrze zdefiniowane. Repo posiada między innymi:

* `RiskAssessment`,
* `CapabilityContract`,
* `PolicyBundle`,
* `DecisionLedgerEntry`,
* `QualityGateResult`,
* `EvidencePack`,
* `ApprovalPack`,
* `RollbackPlan`,
* `ExecutionReceipt`,
* formalną maszynę stanów.

Jednocześnie w głównej ścieżce wykonawczej nadal występują uproszczenia:

* `PolicyChecker.check_compliance()` zawsze zwraca `True`;
* capability check w Kernelu jest opisany jako mock;
* klasyfikacja ryzyka jest głównie słownikowym dopasowaniem fraz i zawsze przypisuje pewność `0.98`;
* część danych Quality Gate jest uzupełniana domyślnymi „zielonymi” metrykami;
* Evidence Pack jest obecnie w tej ścieżce głównie hashem payloadu, a ledger przejściem maszyny stanów;
* `ExecutionReceipt` zawiera zahardkodowane informacje o trybie, modelu, capability i zapisie pamięci;
* Phoenix generuje symulowany patch i z góry osiąga sukces przy trzeciej próbie;
* sandbox jest obecnie głównie worktree, a przy błędzie Git może powstać pusty katalog, po czym wykonanie trwa dalej;
* GitOps używa hasha zawartości jako „podpisu”, może przełączać branch w głównym katalogu i generuje lokalny opis PR zamiast rzeczywistego PR;
* orkiestrator ma zahardkodowaną listę aktywnych agentów, a korekta dryfu zapisuje zdarzenie bez rzeczywistego wykonania naprawy;
* MCP posiada ścieżki bezpośredniego uruchamiania `docker`, skryptów i odczytu logów, zamiast obligatoryjnego przejścia przez Autonomy Kernel.

**Wniosek:** priorytetem nie powinno być dodawanie kolejnych agentów, ale przekształcenie istniejących kontraktów w nieomijalne mechanizmy wykonawcze.

---

# 4. RAE Agentic Engineering Addendum

Proponuję nie zmieniać istniejących M1–M8. Nowy materiał powinien zostać dodany jako uzupełniający program:

## `RAE Agentic Engineering Addendum — AEA-0…AEA-7`

Nie jest to konkurencyjna roadmapa. Każdy pakiet AEA wzmacnia istniejące milestone’y v6.8.

---

## AEA-0 — Architektoniczne zamrożenie i jedno źródło prawdy

### Cel

Usunąć rozbieżności między dokumentacją, konfiguracją, submodułami i runtime’em, nie zmieniając zachowania systemu.

### Zakres

1. Utworzyć `docs/architecture/RAE_INVARIANTS.md`.
2. Zapisać tam niezmienniki opisane w rozdziale 2.
3. Wprowadzić wersjonowany `RAEArchitectureProfile`.
4. Ujednolicić nazewnictwo:

   * `rae-phoenix` kontra `rae-phenix`,
   * `packages/rae-core` kontra `packages/rae-agentic-memory`,
   * role, porty i endpointy.
5. Wprowadzić generowany `REPOSITORY_MANIFEST.json`, zawierający:

   * submoduł,
   * commit SHA,
   * wersję kontraktów,
   * obsługiwane capability,
   * endpoint zdrowia,
   * status migracji.
6. Określić nadrzędność dokumentów:

   * v6.8 jako frozen autonomy baseline,
   * architektura v3 jako model Control Plane,
   * starsze plany wyłącznie jako historia.

### Wykorzystanie artykułu

Artykułowe config files zostają rozdzielone na cztery poziomy:

1. `Constitution` — zasady niepodlegające agentowej zmianie.
2. `FactorySpec` — deklaratywny stan fabryki.
3. `AgentProfile` — rola, modele, narzędzia i capability.
4. `WorkflowDefinition` — procedura konkretnego zadania.

Nie należy tworzyć jednego gigantycznego `AGENTS.md`.

---

## AEA-1 — Nieomijalny Autonomy Kernel

### Cel

Żadna akcja narzędziowa, MCP, agentowa ani infrastrukturalna nie może wykonać się poza Kernelem.

### Nowy komponent

## `Tool Execution Gateway`

Każde wywołanie przechodzi przez:

```text
Tool request
→ normalize action
→ classify asset and risk
→ check policy bundle
→ check capability contract
→ check cumulative risk
→ allocate sandbox
→ optional dry-run
→ execute
→ verify result
→ emit MAES
→ update evidence
→ return ToolExecutionReceipt
```

### Najważniejsze zmiany

* zastąpienie `PolicyChecker.return True` realnym Policy Engine;
* capability check na podstawie wersjonowanego kontraktu;
* klasyfikowanie nie tylko tekstu intencji, ale:

  * narzędzia,
  * argumentów,
  * zasobów docelowych,
  * środowiska,
  * klasy informacji,
  * poprzednich operacji w tym samym `trace_id`;
* wykrywanie eskalacji złożonej z wielu pozornie bezpiecznych kroków;
* ustawianie `NEEDS_APPROVAL` przy niskiej pewności klasyfikatora;
* brak capability oznacza `DENY`, nigdy fallback do `ALLOW`.

### DoD

Nie istnieje publiczna metoda wykonawcza, która potrafi uruchomić shell, zapis pliku, połączenie sieciowe, Git, SQL lub Docker bez `ToolExecutionReceipt`.

---

## AEA-2 — Context Engineering i ochrona przed context rot

### Cel

Wykorzystać artykułową koncepcję zarządzania kontekstem bez ograniczania RAE do prostego pliku pamięci.

### Nowy kontrakt: `ContextEnvelope`

Powinien zawierać:

* `context_id`,
* `source_type`,
* `source_uri`,
* `source_hash`,
* `trust_score`,
* `information_class`,
* `tenant_id`,
* `project_id`,
* `memory_layer`,
* `created_at`,
* `valid_until`,
* `token_cost`,
* `retrieval_reason`,
* `allowed_uses`,
* `related_decisions`,
* `quarantine_status`.

### Context Assembly Pipeline

```text
Goal
→ required knowledge classes
→ retrieval from project memory
→ optional shared knowledge
→ live documentation snapshot
→ trust evaluation
→ contradiction detection
→ budget-aware ranking
→ context pack
→ immutable source hashes
```

### Reguły

* Working memory nie jest automatycznie źródłem prawdy.
* Reflective memory może doradzać, ale nie zawsze decydować.
* Semantic memory wymaga potwierdzonej proweniencji.
* Pamięć R5/R6 nie może być wykorzystywana bez jawnej polityki.
* Kontekst odrzucony przez Trust Evaluator nie może wrócić przez inny retriever.
* System mierzy:

  * context utilization,
  * retrieval precision,
  * contradiction rate,
  * stale-context rate,
  * token-to-outcome ratio.

Prompt caching powinien być wyłącznie optymalizacją adaptera providera. Nie może wpływać na semantykę ani trwałość pamięci.

---

## AEA-3 — MCP i narzędzia jako ograniczone capability

### Cel

MCP ma być warstwą transportową, a nie alternatywną ścieżką wykonania.

### Zmiana architektoniczna

Obecny `RAESupervisor` powinien stać się cienkim adapterem:

```text
MCP client
→ MCP adapter
→ Tool Execution Gateway
→ Autonomy Kernel
→ Hive / Memory / Quality
```

### Zasady

* brak bezpośredniego `subprocess` w publicznym MCP;
* skrypty wybierane po `diagnostic_id`, nie po dowolnej nazwie pliku;
* pełna allowlista argumentów;
* timeout i limit rozmiaru outputu;
* brak dostępu do pełnych logów bez redakcji;
* narzędzia ładowane dynamicznie zgodnie z capability kontraktu;
* pełny schema toola pobierany dopiero wtedy, gdy router go potrzebuje;
* narzędzia infrastrukturalne domyślnie R4/R5;
* `create_memory` musi przechodzić przez Memory Writeback Policy;
* dane z tool outputów są traktowane jako potencjalnie wrogie instrukcje.

### Fail-closed sandbox

Jeżeli nie uda się utworzyć worktree albo kontenera, zadanie kończy się:

`FAILED_ESCALATED`

Nie może powstać pusty katalog udający sandbox.

---

## AEA-4 — Workflow Registry i bezpieczne handoffy

### Cel

Wprowadzić workflow files i subagent patterns z artykułu bez rozmywania obecnych ról.

### Nowy zasób: `WorkflowDefinition`

```yaml
workflow_id: safe-code-change
version: 1.0
entry_conditions:
  risk_classes: [R1, R2, R3]
steps:
  - capability: phoenix.plan_change
  - capability: hive.prepare_worktree
  - capability: phoenix.generate_patch
  - capability: quality.evaluate_patch
  - capability: hive.commit_local
exit_conditions:
  required_quality_status: ACCEPT
rollback:
  capability: hive.restore_snapshot
evidence_profile: code_change_full
```

### Handoff Envelope

Każde przekazanie pracy pomiędzy modułami powinno zawierać:

* cel,
* wymagane capability,
* ograniczony context pack,
* wejściowe artefakty,
* oczekiwany output schema,
* budżet,
* deadline,
* stop conditions,
* trace i parent span,
* klasyfikację danych,
* wymagane dowody.

Subagent nie powinien dostawać całej historii rozmowy. Otrzymuje tylko Handoff Envelope.

### Map-reduce

Dopuszczalne głównie dla zadań read-only:

* przegląd dużego repo,
* analiza wielu plików,
* analiza dokumentów,
* klasyfikacja problemów.

Zapisy równoległe wyłącznie w osobnych worktree. Scalanie wykonuje dedykowany workflow z Quality Gate.

---

## AEA-5 — Agent-native Quality Gates

### Cel

Połączyć artykułowe structural linting i pre-commit gates z istniejącymi Quality, Phoenix i Legacy Behavior Guard.

### Warstwy bramki

1. walidacja kontraktów,
2. formatter i standardowy linter,
3. type checking,
4. structural rules,
5. SAST i dependency scanning,
6. testy istniejące,
7. test integrity,
8. coverage delta,
9. mutation testing,
10. Legacy Behavior Guard,
11. architecture rules,
12. niezależny werdykt Auditora.

### Ważne

Pre-commit i CI muszą korzystać z tego samego profilu Quality Gate.

Nie powinny istnieć dwa zestawy reguł:

* jeden dla człowieka,
* drugi dla agenta.

### Candidate Guardrails

Gdy Lab zauważy powtarzalny antywzorzec:

1. tworzy regułę,
2. rejestruje jej proweniencję,
3. uruchamia ją w shadow mode,
4. wykonuje replay historyczny,
5. mierzy false positives,
6. przygotowuje rollback,
7. tworzy PR,
8. dopiero po akceptacji reguła może blokować.

W istniejącym blueprintcie promocja guardraila wymaga shadow mode, replayu i FP poniżej ustalonego progu.

---

## AEA-6 — Jedna obserwowalność: trace, audit i outcome

### Cel

Nie tworzyć osobnych, niespójnych systemów logowania dla każdego modułu.

### Model

```text
OpenTelemetry Trace
 ├── goal span
 ├── planning span
 ├── policy decision span
 ├── tool spans
 ├── quality gate spans
 ├── evidence span
 └── memory writeback span

MAES
 └── minimalne audytowalne wydarzenia

Evidence Pack
 └── pełne artefakty i raporty

Decision Ledger
 └── trwałe hashe, decyzje i odwołania
```

### Rozróżnienie

* **trace** — co system wykonywał,
* **log** — szczegóły techniczne,
* **MAES** — minimalny formalny zapis zdarzenia,
* **Evidence Pack** — dowody,
* **Decision Ledger** — trwały rejestr decyzji,
* **Outcome Record** — czy działanie rzeczywiście przyniosło wartość.

Nie należy zapisywać prywatnego, ukrytego toku rozumowania modeli. Zapisujemy:

* decyzję,
* jawne uzasadnienie,
* wykorzystane dowody,
* alternatywy,
* confidence,
* wyniki narzędzi.

### Outcome metrics

Oprócz tokenów, kosztów i czasu:

* czy testy przeszły,
* czy PR został zaakceptowany,
* czy zmiana została wdrożona,
* czy nastąpił rollback,
* liczba regresji po wdrożeniu,
* czas do wykrycia problemu,
* czas do poprawnego PR,
* odsetek poprawek zaakceptowanych bez ręcznej korekty.

Proponowany wcześniej **Model Performance Intelligence** powinien zostać częścią RAE-Lab i uczyć router:

* jaki model,
* dla jakiego typu zadania,
* przy jakim ryzyku,
* w jakim języku,
* w jakim repo,
* za jaki koszt

osiąga najlepszy wynik.

---

## AEA-7 — Kontrolowane compound engineering

### Cel

Każde wykonane zadanie powinno ulepszać przyszłe workflow, ale bez samomodyfikowania stabilnego runtime’u.

### Pętla

```text
Execute
→ evaluate outcome
→ post-mortem
→ extract reusable lesson
→ propose workflow/guardrail change
→ replay
→ shadow mode
→ Quality + Auditor
→ PR
→ human approval where required
→ promotion
```

### Rodzaje wiedzy

* sukces jednorazowy → episodic,
* potwierdzony wzorzec → semantic,
* wniosek strategiczny → reflective,
* nowa procedura → Candidate Workflow,
* wykryty antywzorzec → Candidate Guardrail,
* wynik porównania modeli → Model Performance Intelligence.

Lab może proponować zmiany. Nie może samodzielnie zmieniać Constitution, polityk R4/R5 ani Stable Factory Lane.

---

# 5. Powiązanie z istniejącymi M1–M8

| Istniejący milestone     | Uzupełnienie AEA    |
| ------------------------ | ------------------- |
| M1 Autonomy Kernel       | AEA-0, AEA-1        |
| M2 Safe Code Autonomy    | AEA-3, AEA-5        |
| M3 Embedding Agnosticism | AEA-2               |
| M4 GitOps Agent Flow     | AEA-1, AEA-4, AEA-6 |
| M5 Phoenix Closed Loop   | AEA-4, AEA-5        |
| M6 Lab Shadow Guardrails | AEA-5, AEA-7        |
| M7 Infra Reconciler      | AEA-1, AEA-3, AEA-6 |
| M8 Evaluation Harness    | AEA-2, AEA-6, AEA-7 |

Nie trzeba zmieniać zamrożonej roadmapy. Addendum doprecyzowuje, w jaki sposób milestone’y mają zostać zrealizowane produkcyjnie.

---

# 6. Kolejność implementacji

## Priorytet P0 — bezpieczeństwo ścieżki wykonawczej

1. Tool Execution Gateway.
2. Realny Policy Checker.
3. Capability enforcement.
4. Fail-closed sandbox.
5. MCP wyłącznie przez Kernel.
6. Prawdziwy Evidence Pack i trwały ledger.
7. Usunięcie mock success z produkcyjnych ścieżek.

Bez tego rozwijanie dalszej autonomii zwiększa powierzchnię ryzyka.

## Priorytet P1 — przewidywalność i jakość

1. Workflow Registry.
2. Handoff Envelope.
3. Context Envelope.
4. Quality Gate parity: lokalnie i CI.
5. Structural linting.
6. OTEL trace propagation.
7. Outcome Records.

## Priorytet P2 — uczenie i optymalizacja

1. Model Performance Intelligence.
2. Candidate Workflows.
3. automatyczny failure mining,
4. live document retrieval,
5. prompt-cache hints,
6. deferred MCP tool discovery,
7. map-reduce dla dużych analiz.

---

# 7. Czego nie wdrażać

1. **Drugiego frameworka orkiestracji obok RAE-Suite.**
2. Generycznych agentów dublujących Phoenix, Hive, Quality lub Lab.
3. Ogromnego `AGENTS.md` ładowanego do każdego zadania.
4. Bezpośrednich narzędzi MCP omijających Kernel.
5. Automatycznego zapisu każdego outputu do pamięci refleksyjnej.
6. Równoległych zapisów wielu agentów w tym samym worktree.
7. Automatycznej promocji reguł Lab bez shadow mode.
8. Traktowania zielonych testów wygenerowanych przez agenta jako wystarczającego dowodu.
9. Używania prompt cache jako pamięci.
10. Zapisywania pełnego wewnętrznego rozumowania modeli w trace’ach.
11. Uznawania SHA-256 tekstu za pełnoprawny podpis cyfrowy.
12. Deklarowania ISO compliance wyłącznie na podstawie obecności pól w JSON.

---

# 8. Ostateczna rekomendacja

Artykuł należy włączyć do RAE jako:

## `Agentic Engineering Compatibility Profile`

Profil powinien służyć do oceniania każdej wersji RAE-Suite w sześciu obszarach:

1. configuration,
2. context and memory,
3. capability access,
4. orchestration,
5. guardrails,
6. observability and outcomes.

RAE nie potrzebuje rewolucji architektonicznej. Potrzebuje **egzekucyjnego utwardzenia własnej, bardzo dobrej architektury**.

Najkrócej:

> Nie dodawać więcej „inteligencji” przed domknięciem kontroli nad tym, jak obecna inteligencja działa.

Największą przewagą RAE nad systemami opisywanymi w artykule jest połączenie:

* pamięci refleksyjnej,
* policy-controlled autonomy,
* risk classes,
* capability contracts,
* Quality Gate,
* Evidence Pack,
* Decision Ledger,
* niezależnego Auditora,
* oddzielonego Improvement Plane.

Największą obecną luką jest to, że część z tych mechanizmów nadal można w praktyce ominąć albo zastępują je mocki, fallbacki i domyślne sukcesy.

Dlatego pierwszym celem powinno być osiągnięcie:

## „No Tool Call Outside the Kernel”

Dopiero później:

## „Every Successful Run Improves the Factory”.

