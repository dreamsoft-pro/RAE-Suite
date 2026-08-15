# RAE-Suite v3 Architecture Plan

- **Typ dokumentu:** RFC / plan architektoniczny
- **Status:** Draft v1
- **Data:** 2026-03-27
- **Zakres:** `rae-core`, `RAE-agentic-memory`, `RAE-Suite`, moduły działowe, `RAE Fabric`, `RAE Mesh`
- **Licencja docelowa ekosystemu:** Apache 2.0

---

## 1. Streszczenie

Celem RAE-Suite v3 jest przekształcenie obecnego ekosystemu modułów w **spójny, deklaratywny, audytowalny i zdolny do samodoskonalenia system operacyjny dla refleksyjnej fabryki oprogramowania**.

Wersja v3 wprowadza trzy kluczowe decyzje architektoniczne:

1. **RAE-Suite staje się Control Plane fabryki**, a nie tylko zbiorem spiętych usług.
2. **`rae-core` staje się wspólnym protokołem poznawczym i dowodowym** dla wszystkich instancji, runtime'ów i trybów działania.
3. **Samodoskonalenie zostaje wydzielone do osobnego Improvement Plane**, aby system mógł eksperymentować i uczyć się bez destabilizowania toru stabilnej produkcji.

Docelowo RAE-Suite ma łączyć:
- lokalność i prywatność,
- audytowalność i polityki zgodności,
- pamięć działań, kosztów, efektów i porażek,
- capability-driven orchestration,
- federację doświadczenia między instancjami za zgodą użytkowników.

---

## 2. Kontekst i motywacja

RAE-Suite nie jest zwykłym frameworkiem agentowym. Jest próbą zbudowania fabryki oprogramowania, która posiada:
- dział planowania,
- dział produkcji,
- dział kontroli jakości,
- laboratorium badawcze,
- niezależnego audytora,
- wspólną pamięć operacyjną i refleksyjną.

Kluczowe założenie systemu brzmi:

> Każdy dział zapisuje do wspólnego rdzenia, co zrobił, dlaczego to zrobił, jaki był koszt, jaki przyniosło to efekt oraz czego nauczył się z sukcesów i porażek.

To oznacza, że RAE nie jest wyłącznie systemem pamięci. Jest systemem **organizacyjnego uczenia się agentów**.

Wersja v3 odpowiada na trzy potrzeby:

1. **Ustrukturyzowanie całości** w spójną architekturę warstwową.
2. **Wydzielenie bezpiecznego toru samodoskonalenia** obok stabilnej produkcji.
3. **Zdefiniowanie jawnego modelu zasobów i kontraktów**, aby system był programowalny, interoperacyjny i długowieczny.

---

## 3. Cele

### 3.1 Cele główne

1. Zbudować z RAE-Suite **Factory OS for Reflective Autonomous Engineering**.
2. Uczynić `RAE-Suite` deklaratywnym **Control Plane** fabryki.
3. Uczynić `rae-core` małym, stabilnym i przenośnym **substratem poznawczym**.
4. Wydzielić **Stable Factory Lane** i **Adaptive Improvement Lane**.
5. Oprzeć przepływ pracy na **capability contracts**, a nie na sztywnych zależnościach między modułami.
6. Zapewnić **audytowalność, governance, telemetry i failure learning** jako elementy rdzenia.
7. Umożliwić **Mesh** jako federację doświadczenia za zgodą użytkowników.

### 3.2 Cele poboczne

1. Uprościć wdrożenia i profile uruchomieniowe.
2. Zmniejszyć ryzyko dryfu konfiguracji i ręcznego „leczenia” środowisk.
3. Ułatwić rozbudowę o nowe działy, runtime'y i capability bez przebudowy całego systemu.

---

## 4. Niezamierzone cele

Niniejszy plan **nie** zakłada:

1. Budowy własnego hypervisora, systemu kontenerowego lub alternatywy dla Kubernetes.
2. Centralizacji wszystkich danych wszystkich użytkowników.
3. Automatycznego self-modifying production bez bramek bezpieczeństwa.
4. Zamiany RAE w monolit wykonujący wszystko w jednym procesie.
5. Uzależnienia całego systemu od jednego dostawcy modeli lub jednej infrastruktury.

---

## 5. Zasady architektoniczne

1. **Local-first** — wszystko, co istotne, musi móc działać lokalnie.
2. **Privacy-first** — wymiana wiedzy i danych wyłącznie jawnie i za zgodą.
3. **Open-source-first** — standard, runtime'y i control plane pozostają otwarte.
4. **Policy-first** — polityki są częścią rdzenia, nie dodatkiem.
5. **Evidence-first** — każda ważna akcja pozostawia ślad dowodowy.
6. **Failure-aware** — porażki są pełnoprawnym źródłem wiedzy.
7. **Safe self-improvement** — samodoskonalenie odbywa się obok produkcji, nie na niej.
8. **Capability-driven orchestration** — routing po zdolnościach, nie po nazwach usług.
9. **Declarative operations** — stan docelowy ma być opisany jawnie.
10. **Disposable runtime** — runtime ma się dać odtworzyć, wymienić i zreconcile'ować.

---

## 6. Warstwy systemu

### 6.1 `rae-core`

Wspólny, mały, przenośny rdzeń kontraktów i semantyki.

Rola:
- kanoniczne modele danych,
- kontrakty pamięci i dowodów,
- semantyka warstw pamięci,
- formaty audit/evidence/failure learning,
- kontrakty kompatybilności między instancjami,
- formaty wymiany w `RAE Mesh`.

`rae-core` nie jest „całym RAE”. Jest **wspólnym protokołem** dla wielu runtime'ów i instancji.

### 6.2 `RAE-agentic-memory`

Referencyjny runtime pamięci zgodny z `rae-core`.

Rola:
- storage,
- retrieval,
- embeddings/runtime ML,
- policy-aware persistence,
- sync i mesh exchange,
- profile uruchomieniowe: local / secure / mobile / factory / research.

### 6.3 `RAE-Suite`

Docelowy **Control Plane fabryki**.

Rola:
- odczyt `FactorySpec`,
- reconcile i lifecycle ops,
- registry działów i capability,
- routing pracy,
- policy enforcement,
- health/status,
- deployment profiles,
- obsługa bramek jakości i audytu.

### 6.4 Department Engines

Wyspecjalizowane działy fabryki:
- **Phoenix** — planowanie zmian, generacja/refaktor, strategie wykonawcze,
- **Hive** — wykonanie operacyjne, środowiska, Playwright, działania „hands”,
- **Quality** — quality gates, security, coverage, compliance,
- **Lab** — eksperymenty, analiza, insight packs, samodoskonalenie,
- **Independent Auditor** — niezależne werdykty i nadzór zgodności.

### 6.5 `RAE Fabric`

Warstwa capability lattice.

Rola:
- ogłaszanie capability,
- linkowanie capability,
- routowanie zadań po capability,
- dobór wykonawców z uwzględnieniem kosztu, ryzyka i polityk,
- spójna komunikacja między działami.

### 6.6 `RAE Mesh`

Federacja doświadczenia i pamięci za zgodą.

Rola:
- wymiana paczek wiedzy,
- wymiana insight/failure patterns/benchmark packs,
- selective sharing,
- provenance, TTL, zakres i polityki wymiany.

---

## 7. Podwójny układ operacyjny

### 7.1 Stable Factory Lane

Tor stabilnej produkcji.

Cechy:
- przewidywalność,
- polityki i quality gates,
- ścisła audytowalność,
- niski apetyt na ryzyko,
- kontrolowany lifecycle,
- brak niejawnej samomodyfikacji.

Do tego toru należą:
- planowanie produkcyjne,
- wykonanie,
- kontrola jakości,
- audyt,
- standardowy routing i policy enforcement,
- pamięć operacyjna.

### 7.2 Adaptive Improvement Lane

Tor badawczo-korekcyjny.

Cechy:
- eksperymenty,
- hipotezy,
- replay historycznych zadań,
- shadow runs,
- canary,
- failure mining,
- kompilacja lekcji i propozycji zmian.

Do tego toru należą:
- eksperymenty w Labie,
- testowanie nowych providerów/workflow/polityk,
- wydobywanie antywzorców,
- bezpieczne przygotowanie zmian do ewentualnej promocji do Stable Lane.

### 7.3 Reguła rozdziału

Żadna zmiana nie może trafić do Stable Factory Lane bez przejścia przez:
- eksperyment lub analizę porównawczą,
- ocenę ryzyka,
- quality gate,
- wymagane policy gates,
- ewentualny werdykt Auditora,
- możliwość rollbacku.

---

## 8. Resource Model

Wszystko, co ważne operacyjnie, powinno być reprezentowane jako **zasób pierwszej klasy**.

### 8.1 Zasoby podstawowe

#### `Factory`
Opisuje całą fabrykę jako byt zarządzalny.

Pola przykładowe:
- `metadata.name`
- `spec.profile`
- `spec.departments`
- `spec.memory`
- `spec.policies`
- `spec.gates`
- `status.health`
- `status.drift`

#### `Department`
Opisuje dział fabryki.

Pola:
- `name`
- `engine`
- `capabilities`
- `risk_class`
- `allowed_models`
- `required_policies`
- `status`

#### `AgentRole`
Opisuje rolę logiczną w dziale.

Pola:
- `role_id`
- `department`
- `responsibilities`
- `allowed_capabilities`
- `escalation_path`

#### `Capability`
Opisuje kontrakt zdolności.

Pola:
- `capability_id`
- `input_schema`
- `output_schema`
- `cost_model`
- `risk_class`
- `allowed_callers`
- `required_policies`
- `evidence_requirements`

#### `Workflow`
Opisuje przepływ pracy między capability.

Pola:
- `workflow_id`
- `steps`
- `entry_conditions`
- `exit_conditions`
- `quality_gates`
- `rollback_path`

#### `Task`
Jednostka pracy zlecana w fabryce.

Pola:
- `task_id`
- `goal`
- `context_refs`
- `required_capabilities`
- `risk_class`
- `status`
- `trace_id`

#### `Artifact`
Wynik działania działu lub workflow.

Pola:
- `artifact_id`
- `type`
- `producer`
- `location`
- `related_task_id`
- `quality_status`

### 8.2 Zasoby pamięci i dowodów

#### `ActionRecord`
Rekord akcji wykonanej przez dział/rolę.

Pola:
- `action_id`
- `department`
- `role`
- `action_type`
- `goal`
- `tools_used`
- `timestamp`
- `trace_id`

#### `DecisionEvidenceRecord`
Dowód decyzji: co, dlaczego, na jakiej podstawie.

Pola:
- `evidence_id`
- `decision_summary`
- `reasoning_summary`
- `policy_basis`
- `input_refs`
- `confidence`
- `cost`

#### `OutcomeRecord`
Efekt działania.

Pola:
- `outcome_id`
- `action_id`
- `result`
- `quality_result`
- `latency`
- `cost`
- `observed_effect`

#### `FailureLearningRecord`
Rekord uczenia się z porażki lub kosztownego sukcesu.

Pola:
- `failure_id`
- `failure_type`
- `failure_stage`
- `impact_scope`
- `wasted_cost`
- `root_cause_hypothesis`
- `lesson_learned`
- `future_guardrail`
- `retry_recommendation`

#### `PolicyDecisionRecord`
Rekord decyzji polityk i governance.

Pola:
- `policy_decision_id`
- `policy_id`
- `subject_ref`
- `decision`
- `reason`
- `timestamp`

#### `AuditVerdict`
Werdykt niezależnego audytora.

Pola:
- `verdict_id`
- `subject_ref`
- `status`
- `severity`
- `findings`
- `required_actions`
- `approved_by`

### 8.3 Zasoby Improvement Plane

#### `Experiment`
Definicja eksperymentu.

Pola:
- `experiment_id`
- `hypothesis_ref`
- `baseline`
- `candidate`
- `dataset_refs`
- `risk_class`
- `budget_limit`
- `success_criteria`

#### `ExperimentRun`
Pojedyncze wykonanie eksperymentu.

Pola:
- `run_id`
- `experiment_id`
- `mode` (`offline`, `shadow`, `canary`)
- `metrics`
- `result`
- `trace_id`

#### `Hypothesis`
Hipoteza poprawy.

Pola:
- `hypothesis_id`
- `statement`
- `motivation`
- `target_metric`
- `origin` (`lab`, `quality`, `auditor`, `memory`)

#### `CandidateStrategy`
Kandydat strategii do oceny.

Pola:
- `strategy_id`
- `type`
- `description`
- `affected_workflows`
- `risk_class`

#### `ImprovementProposal`
Propozycja zmiany po eksperymentach.

Pola:
- `proposal_id`
- `source_hypothesis`
- `evidence_refs`
- `expected_gain`
- `expected_risk`
- `promotion_requirements`

#### `ShadowRun`
Uruchomienie równoległe bez wpływu na produkcję.

#### `CanaryRollout`
Ograniczone wdrożenie do części ruchu/zadań.

#### `PromotionDecision`
Formalna decyzja promowania zmiany.

#### `RollbackDecision`
Formalna decyzja cofnięcia zmiany.

#### `InsightPack`
Skondensowana, wersjonowana paczka wiedzy strategicznej.

#### `FailurePatternPack`
Paczka wzorców porażek i antywzorców.

#### `BenchmarkSuite`
Zestaw benchmarków do porównań kandydatów.

### 8.4 Zasoby Mesh

#### `MeshPeer`
Opis zaufanej instancji w mesh.

#### `MeshExchangeEnvelope`
Opakowanie wymiany wiedzy z metadanymi zgody, zakresu i provenance.

#### `ConsentGrant`
Jawna zgoda na określony zakres wymiany.

---

## 9. Capability Contracts

Capability są podstawową jednostką wykonania i integracji.

Każdy kontrakt capability powinien definiować:
- identyfikator capability,
- schemat wejścia,
- schemat wyjścia,
- preconditions i postconditions,
- wymagane polityki,
- klasę ryzyka,
- model kosztowy,
- wymagane evidence,
- uprawnionych wywołujących,
- zasady retry/timeout/escalation.

### Przykładowe capability

- `plan.refactor`
- `plan.angular_migration`
- `execute.container_command`
- `execute.playwright_audit`
- `scan.sast`
- `scan.coverage`
- `validate.behavior_contract`
- `run.experiment`
- `compare.baseline_vs_candidate`
- `publish.insight_pack`
- `issue.audit_verdict`
- `trigger.rollback`

Zależności między działami powinny być budowane przez capability i policy-aware routing, a nie przez twarde zależności typu „moduł A zna URL modułu B”.

---

## 10. FactorySpec

`FactorySpec` jest deklaratywnym opisem fabryki.

Powinien definiować:
- aktywny profil runtime,
- pamięć i tryb mesh,
- działy i ich capability,
- polityki,
- quality gates,
- tor poprawy (Improvement Plane),
- zasady eksperymentów,
- wymagania audytowe,
- budżety i limity ryzyka.

### Przykładowy szkic

```yaml
apiVersion: rae.dev/v1
kind: Factory
metadata:
  name: rae-suite-main
spec:
  profile: factory-secure
  memory:
    runtime: rae-agentic-memory
    meshEnabled: true
    consentMode: explicit
  departments:
    - name: planning
      engine: phoenix
      capabilities:
        - plan.refactor
        - plan.migration
    - name: production
      engine: hive
      capabilities:
        - execute.container_command
        - execute.playwright_audit
    - name: quality
      engine: quality
      capabilities:
        - scan.sast
        - scan.coverage
        - validate.behavior_contract
    - name: lab
      engine: lab
      capabilities:
        - run.experiment
        - publish.insight_pack
    - name: auditor
      engine: auditor
      capabilities:
        - issue.audit_verdict
  policies:
    - iso27001
    - iso42001
    - hardFrames
    - zeroRegression
  gates:
    - quality.mustPass
    - auditor.requiredForHighRisk
  improvement:
    enabled: true
    requireShadowBeforeCanary: true
    requireRollbackPlan: true
    experimentBudget:
      daily: 100
```

---

## 11. Control Plane

### 11.1 Rola

`RAE-Suite` jako Control Plane odpowiada za:
- odczyt `FactorySpec`,
- utrzymanie desired state,
- rejestrację działów, capability i workflow,
- reconcile środowiska,
- health/status,
- policy enforcement,
- lifecycle ops,
- bramki jakości i audytu,
- orchestrację pracy między działami.

### 11.2 Pętle control plane

#### Reconcile Loop
Porównuje stan rzeczywisty do stanu opisanego w `FactorySpec` i koryguje drift.

#### Lifecycle Loop
Uruchamia, aktualizuje, zatrzymuje i wymienia moduły/runtime'y.

#### Evidence Loop
Dba o to, aby wszystkie istotne akcje trafiały do `rae-core` jako evidence.

#### Governance Loop
Pilnuje polityk, budżetów, quality gates i zasad escalacji.

#### Routing Loop
Dobiera capability i wykonawców na podstawie dostępności, kosztu, ryzyka i polityk.

---

## 12. Improvement Plane

Improvement Plane jest boczną płaszczyzną samodoskonalenia.

### 12.1 Cele

- prowadzenie eksperymentów,
- testowanie hipotez,
- wykrywanie wzorców porażek,
- generowanie propozycji zmian,
- bezpieczne wdrażanie ulepszeń,
- kompilacja lekcji do postaci packów wiedzy.

### 12.2 Reguła bezpieczeństwa

Improvement Plane nigdy nie zmienia bezpośrednio Stable Factory Lane.
Każda zmiana wymaga ścieżki:
1. hipoteza,
2. eksperyment offline,
3. shadow,
4. canary,
5. quality/audit/policy review,
6. promotion lub rollback,
7. zapis wiedzy do core.

### 12.3 Pętla samodoskonalenia

1. **Observe** — zbieranie działań, kosztów, efektów, porażek i telemetryki.
2. **Diagnose** — wykrywanie trendów, spadków jakości i błędnych wzorców.
3. **Hypothesize** — stawianie hipotez poprawy.
4. **Generate Candidates** — tworzenie kandydatów strategii, providerów, workflow lub polityk.
5. **Offline Evaluate** — testy na danych historycznych, benchmarkach, replayach i behavior contracts.
6. **Shadow Run** — uruchomienie równoległe bez wpływu na produkcję.
7. **Canary** — ograniczone wdrożenie z automatycznym rollbackiem.
8. **Promote/Reject** — decyzja na podstawie evidence, quality i audytu.
9. **Codify** — zapis lekcji do `rae-core` i aktualizacja guardrails/routing/polityk.

---

## 13. Rola RAE-Lab w v3

RAE-Lab staje się pełnoprawnym silnikiem eksperymentów i samodoskonalenia.

### 13.1 Podmoduły Labu

#### Experiment Orchestrator
Definiuje i uruchamia eksperymenty.

#### Hypothesis Engine
Tworzy i utrzymuje hipotezy poprawy.

#### Failure Mining Engine
Analizuje porażki, regresje i kosztowne sukcesy.

#### Strategy Compiler
Kompiluje wyniki badań do postaci:
- `InsightPack`,
- `FailurePatternPack`,
- `PolicyPatchProposal`,
- `WorkflowImprovementProposal`,
- `ProviderRoutingProposal`.

#### Safe Rollout Manager
Zarządza shadow, canary, promotion i rollback.

### 13.2 Zasada

Lab nie może kończyć na raporcie. Lab musi produkować **wdrażalne artefakty wiedzy**.

---

## 14. Independent Auditor

Audytor jest oddzielnym działem o ograniczonych uprawnieniach wykonawczych.

Rola:
- wydawanie niezależnych werdyktów,
- kontrola zgodności z politykami,
- nadzór nad zmianami wysokiego ryzyka,
- ocena procesu samodoskonalenia,
- potwierdzanie lub blokowanie promocji zmian do Stable Lane.

Audytor powinien działać w możliwie odseparowanym torze dowodowym i logicznym.

---

## 15. Mesh i federacja wiedzy

`RAE Mesh` służy do wymiany wyłącznie zatwierdzonej wiedzy.

### 15.1 Co może być wymieniane

- `InsightPack`
- `FailurePatternPack`
- `BenchmarkSuite`
- `BehaviorContractPack`
- `PolicyPack`

### 15.2 Czego nie wymieniać domyślnie

- pełnych memory store'ów,
- surowych danych klientów,
- sekretów,
- wrażliwych logów i post-mortem bez anonimizacji,
- prywatnych eksperymentów bez zgody.

### 15.3 Wymagania

Każda wymiana powinna mieć:
- zgodę (`ConsentGrant`),
- provenance,
- scope,
- TTL,
- etykietę wrażliwości,
- wersję kontraktu.

---

## 16. Governance, bezpieczeństwo i obserwowalność

### 16.1 Governance

System powinien wspierać co najmniej:
- ISO 27001,
- ISO 42001,
- Hard Frames,
- Zero Regression,
- polityki kosztowe,
- polityki prywatności i consent.

### 16.2 Evidence i provenance

Każda ważna akcja powinna generować:
- `trace_id`,
- `ActionRecord`,
- `DecisionEvidenceRecord`,
- `OutcomeRecord`,
- opcjonalnie `FailureLearningRecord`.

### 16.3 Observability

Warstwa telemetry powinna obejmować:
- latency,
- cost,
- success/failure rate,
- quality gate pass/fail,
- drift,
- rollout outcomes,
- insight production,
- rollback count.

---

## 17. Profile uruchomieniowe

System powinien wspierać profile:

### `local`
Pojedyncza instancja lokalna, niski koszt, minimum zależności.

### `secure`
Zwiększona izolacja, bardziej restrykcyjne polityki.

### `mobile`
Lekki runtime, ograniczone capability, nacisk na zużycie zasobów.

### `factory`
Pełna fabryka z działami, control plane i telemetryką.

### `research`
Tryb badawczy, rozszerzone capability eksperymentalne i Improvement Plane.

---

## 18. Kolejność implementacji

### Faza 0 — Konstytucja systemu

Cel: ustalić kanoniczne kontrakty i semantykę.

Zakres:
- zamrożenie modeli `rae-core`,
- definicja resource model,
- definicja `FactorySpec`,
- definicja capability contracts,
- definicja kompatybilności wersji.

Deliverables:
- `rae-core` schemas,
- `FactorySpec` v1,
- `CapabilityContract` v1,
- dokument kompatybilności.

### Faza 1 — Minimalny Control Plane

Cel: przejście z ręcznego spinania do zarządzania stanem fabryki.

Zakres:
- registry działów,
- registry capability,
- parser `FactorySpec`,
- health/status pane,
- reconcile loop v1,
- evidence router v1,
- lifecycle ops v1.

Deliverables:
- `RAE-Suite Control Plane` MVP,
- deklaratywny start fabryki,
- podstawowa widoczność stanu.

### Faza 2 — Independent Auditor

Cel: oddzielny tor werdyktu i governance.

Zakres:
- moduł Auditora,
- `AuditVerdict`,
- integracja z policy gates,
- obsługa zmian high-risk.

Deliverables:
- działający Independent Auditor,
- formalny gate audytowy.

### Faza 3 — Improvement Plane MVP

Cel: bezpieczny tor samodoskonalenia obok produkcji.

Zakres:
- `Experiment`, `Hypothesis`, `CandidateStrategy`,
- offline evaluation,
- `ShadowRun`,
- `CanaryRollout`,
- `PromotionDecision`,
- `RollbackDecision`.

Deliverables:
- Improvement Plane MVP,
- pierwsze bezpieczne eksperymenty.

### Faza 4 — RAE-Lab Evolution Engine

Cel: uczynić Lab aktywnym silnikiem poprawy, a nie tylko analitykiem.

Zakres:
- Experiment Orchestrator,
- Hypothesis Engine,
- Failure Mining,
- Strategy Compiler,
- Safe Rollout Manager,
- `InsightPack` i `FailurePatternPack`.

Deliverables:
- aktywny system generowania wdrażalnych lekcji.

### Faza 5 — RAE Fabric

Cel: capability-driven routing i lattice.

Zakres:
- capability registry v2,
- linkowanie capability,
- routing cost-aware / risk-aware,
- contract validation,
- fabric telemetry.

Deliverables:
- produkcyjny routing po capability.

### Faza 6 — Mesh v1

Cel: federacja doświadczenia za zgodą.

Zakres:
- `MeshPeer`,
- `ConsentGrant`,
- `MeshExchangeEnvelope`,
- import/export packów wiedzy,
- polityki zaufania.

Deliverables:
- działający Mesh v1 dla wybranych paczek wiedzy.

---

## 19. Kryteria akceptacji architektury v3

Architektura v3 zostaje uznana za wdrożoną, gdy:

1. `rae-core` ma wersjonowane kanoniczne kontrakty i modele danych.
2. `RAE-Suite` uruchamia fabrykę na podstawie `FactorySpec`, nie ręcznych zależności.
3. Działy komunikują się przez capability contracts i routing control plane.
4. Każda ważna akcja zostawia evidence w `rae-core`.
5. Improvement Plane działa obok Stable Lane i nie omija gate'ów.
6. Lab prowadzi eksperymenty i produkuje insight packs.
7. Auditor wydaje niezależne werdykty dla zmian wysokiego ryzyka.
8. Mesh wymienia paczki wiedzy za zgodą i z provenance.

---

## 20. Otwarte pytania

1. Jaki jest minimalny zestaw rekordów `rae-core`, który należy zamrozić w pierwszej kolejności?
2. Jak agresywnie wprowadzać `FactorySpec` do istniejących repo bez blokowania bieżącego rozwoju?
3. Jakie capability powinny być obowiązkowe dla każdego działu, a jakie opcjonalne?
4. Jak rozdzielić polityki globalne od polityk per-factory/per-tenant?
5. Jakie mechanizmy podpisu/provenance wdrożyć dla packów wiedzy w Mesh?
6. Czy Improvement Plane ma mieć osobny storage/runtime czy współdzielić część warstwy pamięci z runtime'em produkcyjnym?

---

## 21. Podsumowanie

RAE-Suite v3 definiuje przejście:

- od agregatu modułów do **Control Plane fabryki**,
- od pamięci dokumentów do **pamięci działań, efektów, porażek i eksperymentów**, 
- od twardych zależności między modułami do **capability lattice**,
- od ręcznej orkiestracji do **desired state i reconcile**,
- od biernej analityki do **bezpiecznego samodoskonalenia**,
- od pojedynczej instancji do **federacji doświadczenia w Mesh**.

To czyni z RAE-Suite nie tylko narzędzie, ale zalążek **otwartego systemu operacyjnego dla refleksyjnych organizmów agentowych**.
