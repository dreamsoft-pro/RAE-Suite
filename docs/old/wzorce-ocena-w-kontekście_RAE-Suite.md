Po przejrzeniu repo aktualizuję ocenę: RAE-suite jest dalej, niż zakładałem w poprzednim planie. Nie trzeba już projektować od zera audytowalności, Hard Frames, pamięci, hybrydowego wyszukiwania czy modułowej fabryki. To już jest w dużej części rozpisane i częściowo zaimplementowane.

Najważniejsza zmiana w planie: priorytet przesuwa się z “zaprojektować architekturę” na “doprowadzić istniejące moduły do spójnego, wykonywalnego, testowalnego kontraktu produkcyjnego”.

Repo główne opisuje RAE-Suite jako „Global AI Engineering Factory” z modułami: rae-agentic-memory, RAE-Phoenix, RAE-Hive, RAE-Quality, RAE-Lab oraz wspólną telemetrią i standardami audytu. W docker-compose.yml realnie stoją osobne usługi: Postgres/pgvector, Redis, Qdrant, memory API, suite control plane, lab, quality, phoenix, hive i openclaw.

Najważniejszy wniosek

RAE-suite ma już szkielet fabryki. Brakuje jeszcze twardego kręgosłupa wykonawczego.

Czyli masz:

✅ moduły
✅ Docker Compose
✅ pamięć agentową
✅ Qdrant/Postgres/Redis
✅ MCP/SSE kierunek
✅ hybrydowe wyszukiwanie
✅ podstawowy routing kosztowy
✅ kontrakty audytowe MAES / EvidencePack / ExecutionReceipt
✅ Quality / Hive / Lab / Phoenix jako osobne role
✅ plan ISO / Oracle Sentinel

Ale krytyczne luki są tutaj:

❌ brak pełnego end-to-end trace przez wszystkie moduły
❌ brak prawdziwego trajectory replay / fork-from-step
❌ MAES istnieje, ale nie wszystkie moduły emitują go konsekwentnie
❌ część modułów ma nadal implementacje szkieletowe / mockowe
❌ Hive ma lokalny fallback przez shell=True, co osłabia Hard Frames
❌ Phoenix w głównym repo wygląda bardziej jak symulacja niż produkcyjny repair engine
❌ Lab jest koncepcyjnie ważny, ale kodowo jeszcze cienki
❌ router kosztowy jest prosty, nie ma jeszcze pełnego token-budget model routing
❌ cache i retrieval są dobre jako początek, ale nie mają jeszcze source-aware invalidation, drift detection i adaptive_k
Co już jest zrobione i zmienia plan
1. Oracle Sentinel / MAES jest już częściowo wdrożony

W dokumentach masz bardzo mocny kontrakt: deterministyczne artefakty, zero-warning policy, obowiązkowe @audited_operation, komunikacja przez MCP i sześciostopniowy flow od discovery do governance.

Co ważniejsze, to nie jest już tylko dokument. W kodzie istnieje MinimumAuditableEvent z:

event_id
parent_event_id
sequence_no
trace_id
risk_class
execution_mode
payload_hash
policy_bundle_hash
evidence_pack_hash
execution_receipt_id
signing_key_id
signature
validation_status

Masz też modele ToolInvocationEvent, PhoenixRepairIteration, GuardrailAuditRecord, ServiceRecoveryProfile, IncidentScope i ISOAuditRecord.

Aktualizacja planu: nie projektować MAES od nowa. Trzeba teraz zrobić AuditEventEmitter jako wspólną bibliotekę i wymusić, żeby każdy moduł emitował MAES identycznie.

2. Compliance auditor już istnieje, ale trzeba go podłączyć do życia systemu

Masz ComplianceAuditor, który sprawdza podpisy, łańcuch zdarzeń, wykrywa braki sekwencji, złamane parent linki, wycieki sekretów i zanieczyszczenie ledgerów symulacją.

Są też testy dla integralności MAES chain: podpis, poprawny łańcuch, brak root eventu, luka w sekwencji i broken link.

Aktualizacja planu: nie zaczynać od „czy mamy audyt?”. Mamy. Teraz potrzebny jest ciągły audyt runtime:

każdy request → trace_id
każdy moduł → MAES event
każde narzędzie → ToolInvocationEvent
każdy wynik → ExecutionReceipt
każda paczka dowodowa → EvidencePack
każdy błąd → ComplianceFinding
3. RAE-agentic-memory jest mocnym fundamentem

RAE-agentic-memory nie jest zwykłym vector DB. README jasno opisuje cel: walka z Reasoning Drift, przechowywanie nie tylko informacji, ale też powodu decyzji. Ma 6 warstw pamięci: sensory, episodic, working, semantic, long-term i reflective.

Memory API ma już middleware tenant/session/budget, OpenTelemetry, Prometheus oraz wiele routerów: memory, bridge, compliance, evaluation, graph, hybrid search, reflections, tuning, token savings, federation.

Aktualizacja planu: nie budować oddzielnej pamięci dla RAE-suite. Trzeba zbudować nad tym Context Broker, który używa istniejących warstw pamięci, ale układa kontekst hierarchicznie i z budżetem tokenów.

Zaktualizowany plan RAE-suite
Etap 0 — porządkowanie repo i źródeł prawdy

To jest mały, ale ważny etap.

W .gitmodules widać kilka modułów, w tym rae-agentic-memory, rae-hive, rae-quality, rae-lab, rae-phoenix, rae-open-claw, ale też osobny wpis rae-phenix, który wygląda jak potencjalny historyczny/stary wariant nazwy.

Do zrobienia:

1. Uporządkować nazewnictwo: Phoenix / Phenix / Feniks.
2. Dodać RAE-suite module registry:
   - module_name
   - repo_url
   - branch
   - commit_sha
   - port
   - health_endpoint
   - capability_contract_id
3. Dodać suite.lock z wersjami submodułów.
4. Usunąć albo oznaczyć stare dokumenty jako superseded.
5. Zrobić README_STATUS.md: co działa, co jest mockiem, co jest planem.

To jest ważne, bo teraz dokumentacja momentami wygląda mocniej niż implementacja.

Etap 1 — wspólny AuditEventEmitter dla wszystkich modułów

To powinien być pierwszy prawdziwy etap techniczny.

Obecnie MAES i auditor istnieją, ale moduły nie są jeszcze spójnie spięte. Przykład: PhoenixEngine w głównym repo emituje eventy z sequence_no=0, payload_hash="n/a" i signature="sig-mock", czyli to jest raczej szkic niż produkcyjny event chain.

Do zrobienia:

rae_audit/
  emitter.py
  trace_context.py
  signer.py
  redactor.py
  evidence_pack_writer.py

Minimalny interfejs:

async with audit_trace(
    module_id="rae-hive",
    task_id=task_id,
    risk_class=RiskClass.R2,
    execution_mode=ExecutionMode.DRY_RUN_ONLY,
) as trace:
    await trace.emit(AuditableEventType.TASK_RECEIVED, payload)
    result = await run_tool(...)
    await trace.emit(AuditableEventType.TOOL_INVOKED, result)
    await trace.receipt(...)

Definition of Done:

1. Każdy trace zaczyna się od sequence_no=0.
2. Każdy kolejny event ma parent_event_id poprzedniego eventu.
3. Każdy payload jest redagowany przed zapisem.
4. Surowy payload nie trafia do pamięci bez hash + redaction_status.
5. ComplianceAuditor przechodzi end-to-end test dla ścieżki:
   Suite → Hive → Quality → Phoenix → Lab → Memory.
Etap 2 — prawdziwy trajectory replay

To teraz najważniejszy brak względem wzorców produkcyjnych.

Masz audyt, ale jeszcze nie widzę pełnego mechanizmu:

rae replay run_id
rae replay run_id --from-step 6
rae replay run_id --override tool_output.json
rae diff run_a run_b
rae fork run_id --from-step 4

Obecny auditor sprawdza, czy łańcuch zdarzeń jest poprawny, ale replay musi umieć odtworzyć przebieg agenta.

Do zapisu przy każdym kroku:

trace_id
step_id
parent_step_id
module_id
agent_id
model_name
model_version
prompt_template_hash
context_hash
tool_name
tool_input_hash
tool_output_hash
raw_output_uri
redacted_output_uri
decision
quality_gate_result_id
execution_receipt_id
evidence_pack_hash

Definition of Done:

1. Można odtworzyć pełny flow bez wykonywania komend.
2. Można odtworzyć flow do kroku N i od tego miejsca puścić live.
3. Można porównać dwa przebiegi.
4. Można sprawdzić, czy inny model podjąłby lepszą decyzję na tym samym kontekście.

Ten etap robi z RAE system debugowalny, a nie tylko „agentowy”.

Etap 3 — uszczelnienie Hive, bo to jest najbardziej ryzykowna warstwa

RAE-Hive ma już bardzo dobry kierunek: @audited_operation, sandbox, Git worktree, Docker bez sieci, limit RAM i CPU.

Ale jest krytyczna rzecz: jeśli Docker jest niedostępny, Hive przechodzi na lokalne wykonanie przez shell=True. To jest wygodne developersko, ale z punktu widzenia Hard Frames niebezpieczne.

Zmiana planu:

1. Local fallback tylko w trybie dev i tylko po jawnej fladze.
2. W production fallback = BLOCKED.
3. Dodać command allowlist / denylist.
4. Zastąpić shell=True bezpieczniejszym trybem dla znanych komend.
5. Każde wykonanie ma tworzyć ToolInvocationEvent.
6. stdout/stderr przechodzą przez redactor.
7. Każdy wynik dostaje EvidencePack.
8. Docker image musi mieć digest, nie tylko nazwę.
9. Dodać read_only, no-new-privileges, cap_drop, seccomp profile.

To jest ważniejsze niż nowe funkcje agentowe.

Etap 4 — Quality jako brama, nie tylko skaner

RAE-Quality ma SAST, coverage, TestIntegrityGuard i tribunal. Potrafi odrzucać kod przy spadku coverage albo wzroście podatności, a przy odrzuceniu budzi Phoenix.

Ale perform_static_audit zwraca tekst typu "ACCEPTED..." albo "REJECTED...", zamiast pełnego QualityGateResult. Tymczasem kontrakt QualityGateResult już istnieje i jest dużo mocniejszy: status, coverage before/after, mutation score, vulnerability counts, test integrity itd.

Zmiana planu:

1. Każdy audit zwraca QualityGateResult.
2. Każdy QualityGateResult jest zapisywany jako MAES + EvidencePack.
3. Phoenix nie może działać bez QualityGateResult.
4. Quality nie wysyła „gołego” taska do Phoenix.
5. Quality generuje ApprovalPack dla R3+.
6. Quality ma baseline_profile_id per projekt.
Etap 5 — Phoenix: z mocka do bezpiecznej pętli naprawczej

W repo głównym core/phoenix_engine.py jest dobry szkic pętli naprawczej: max 5 prób, hash błędu, hash patcha, PhoenixRepairIteration, QualityGate, stop condition.

Ale obecnie patch jest symulowany, sukces jest ustawiony mockowo na trzecią próbę, a eventy mają mockowe podpisy.

Jednocześnie osobne repo RAE-Phoenix/Feniks jest dużo bardziej dojrzałe: ma analizę kodu, meta-reflection, budget controller, behavior guard, AngularJS migration recipes, CLI, API, observability i status implementacji wielu elementów.

Kluczowy problem: w README Phoenix/Feniks integracja z RAE jest oznaczona jako tylko częściowa — 30%.

Zmiana planu:

1. Nie rozwijać mockowego PhoenixEngine jako osobnego mózgu.
2. Użyć RAE-Phoenix/Feniks jako realnego silnika analizy/refaktoryzacji.
3. W głównym RAE-Suite zostawić Phoenix adapter:
   - przyjmuje RepairRequest
   - uruchamia Feniks
   - wymusza dry-run
   - przekazuje patch do Hive
   - przekazuje wynik do Quality
   - zapisuje PhoenixRepairIteration
4. Każda iteracja musi mieć:
   - patch_diff_hash
   - quality_gate_result_id
   - evidence_pack_hash
   - rollback_plan_id
   - final_decision
Etap 6 — Context Broker nad RAE-agentic-memory

RAE Memory ma warstwy pamięci, MCP, hybrid search i reflective memory. To jest bardzo mocny fundament.

Hybrid search już robi multi-strategy: vector, semantic, graph, fulltext, dynamic weighting i LLM reranking.

Ale obecnie głębokość jest nadal oparta o mnożniki k * 3, k * 2, k * 2, a potem finalnie przycinana do k. To jest dobre jako start, ale nie jest jeszcze adaptacyjne adaptive_k.

Do zrobienia:

1. Context Broker:
   - bierze task
   - robi risk assessment
   - pobiera pamięć
   - liczy trust_score
   - układa kontekst warstwowo
   - tnie kontekst według budżetu tokenów
   - generuje context_hash

2. Adaptive retrieval:
   - zawsze pobierz większą pulę, np. 50
   - sprawdź rozkład score
   - jeśli top wynik mocno odstaje, wybierz małe k
   - jeśli wyniki są zbite, rozszerz k
   - reranking tylko wtedy, gdy jest niepewność

3. Memory poisoning defense:
   - trust_score < 0.4: odrzucić
   - 0.4–0.7: tylko jako advisory
   - >0.7: wolno użyć w planowaniu
   - R6/quarantine: tylko jako ostrzeżenie, nigdy jako rekomendacja

To bezpośrednio wzmacnia wcześniejszy wzorzec „hierarchiczne przycinanie kontekstu”.

Etap 7 — embedding drift i source-aware cache

Cache istnieje. Ma TTL, klucze po query/tenant/project/filter i prostą invalidację.

Ale to jeszcze nie jest cache produkcyjny dla systemu agentowego. Brakuje:

source_hash
embedding_model_version
chunker_version
prompt_hash
policy_bundle_hash
semantic_neighborhood_id
volatility_score
probabilistic_revalidation

Do zrobienia:

1. Cache key = query + tenant + project + filters + source_version + embedding_profile + prompt_hash.
2. Dodać volatility_score.
3. Dodać rewalidację probabilistyczną.
4. Przy zmianie źródła usuwać semantyczną rodzinę cache, nie tylko jeden klucz.
5. Dodać embedding drift detector.

Model EmbeddingProfile już ma miejsce na provider, model, dimension, distance, model_hash i tokenizer_hash. To jest dobry zaczep pod drift detection.

Etap 8 — routing modeli według kosztu, jakości i ryzyka

Masz już dwa elementy:

Middleware budżetowy, który blokuje request, jeśli tenant przekroczył budżet.
CostAwareRouter, który wybiera agenta według ryzyka, estimated_ncu, failure_rate_30d i latency_p50_s.

Ale to jeszcze nie jest pełny routing LLM. Potrzebujesz:

ModelRegistry:
  model_id
  provider
  local/api
  context_window
  cost_input
  cost_output
  latency_p50
  latency_p95
  quality_score_by_task_type
  supports_json_schema
  supports_tools
  supports_vision
  max_risk_class

TaskEstimate:
  input_tokens
  expected_output_tokens
  risk_class
  quality_floor
  deadline_ms
  max_cost

Routing powinien wybierać nie tylko agenta, ale też model:

FAQ / proste klasyfikacje → mały lokalny model
analiza PHP/SQL/security → mocniejszy model
porównanie architektury → reasoning model
walidacja patcha → niezależny reviewer model
szybki routing narzędzi → mały klasyfikator
Etap 9 — Lab jako prawdziwe centrum eksperymentów

RAE-Lab jest dobrze opisany jako obserwatorium: eksperymenty, metryki, token econometrics, latency i feedback do memory.

Ale obecny kod jest jeszcze cienki: main.py tylko składa HypothesisEngine, ExperimentOrchestrator, StrategyCompiler, SafeRolloutManager, a endpoint eksperymentu odpala offline replay z pustym datasetem. SafeRolloutManager ma tylko przejścia offline → shadow → canary → promoted, bez bramek jakościowych.

Do zrobienia:

1. Lab pobiera trajectory z RAE Memory.
2. Lab uruchamia shadow evaluation.
3. Lab porównuje:
   - model A vs model B
   - prompt v1 vs prompt v2
   - retrieval config A vs B
   - agent strategy A vs B
4. Lab promuje zmianę tylko jeśli:
   - jakość wzrosła
   - koszt nie przekroczył budżetu
   - latency p95 OK
   - brak regresji safety
   - ComplianceAuditor PASS
5. Lab zapisuje MABRouterUpdate.

To jest miejsce na wzorce: shadow model evaluation, replay, MAB, cold-path distillation później.

Zaktualizowana mapa 11 wzorców względem obecnego RAE-suite
Wzorzec	Stan w RAE-suite	Nowy priorytet
Hierarchiczne przycinanie kontekstu	pamięć i search są, brak Context Broker	P1
Spekulatywne wykonanie narzędzi	dopiero po uszczelnieniu Hive	P4
Embedding drift detection	EmbeddingProfile jest, detektora brak	P2
Token-budget routing	middleware/router są, routing LLM jeszcze prosty	P2
Shadow evaluation	Lab ma kierunek, kod minimalny	P3
Probabilistic cache invalidation	cache jest, ale prosty	P3
Cold-path distillation	później, po zebraniu danych	P5
Streaming composition	później, UX/raporty	P5
Trajectory replay	audyt jest, replay brak	P1
Adaptive retrieval depth	hybrid search jest, adaptive_k brak	P1/P2
Federacyjne szablony promptów	nie widzę pełnego prompt registry	P1
Najkrótszy plan wykonawczy 10/10
Sprint 1 — „Trace albo stop”
Cel: każdy moduł emituje prawdziwy, spójny trace.

1. AuditEventEmitter
2. TraceContext
3. monotonic sequence_no
4. real payload_hash
5. real signature
6. save MAES do RAE Memory
7. e2e test: Suite → Hive → Quality → Phoenix → Lab
Sprint 2 — „Hive hardening”
Cel: koniec niekontrolowanego wykonania.

1. Wyłączyć local shell fallback w production.
2. Dodać allowlist/denylist komend.
3. Dodać ToolInvocationEvent.
4. Dodać redakcję stdout/stderr.
5. Dodać EvidencePack dla każdej komendy.
6. Dodać Docker security hardening.
Sprint 3 — „Replay engine”
Cel: da się odtworzyć każdy błąd.

1. rae replay <trace_id>
2. rae inspect <trace_id>
3. rae diff <trace_a> <trace_b>
4. rae fork <trace_id> --from-step N
5. replay bez wykonywania side-effectów
Sprint 4 — „Context Broker + adaptive retrieval”
Cel: agent dostaje właściwy kontekst, nie największy kontekst.

1. Context Broker
2. context_hash
3. trust_score
4. adaptive_k
5. reranking only-if-needed
6. logowanie odrzuconego kontekstu
Sprint 5 — „Phoenix/Feniks integration”
Cel: realna pętla naprawcza zamiast mocka.

1. Phoenix adapter do RAE-Phoenix/Feniks
2. RepairRequest
3. PatchPlan
4. dry-run patch
5. QualityGateResult
6. RollbackPlan
7. PhoenixRepairIteration
Sprint 6 — „Model Router”
Cel: tani model tam, gdzie wystarczy; mocny model tam, gdzie trzeba.

1. ModelRegistry
2. TaskEstimate
3. expected_output_tokens
4. quality_floor
5. fallback_model
6. shadow_model
7. koszt per trace
Sprint 7 — „Lab jako centrum ewaluacji”
Cel: RAE samo wie, co działa lepiej.

1. shadow evaluation
2. offline replay datasets
3. model/prompt/retrieval A/B
4. safe rollout gates
5. MABRouterUpdate
6. promotion only after evidence
Moja nowa ocena strategiczna

Poprzednio powiedziałbym: „trzeba zbudować produkcyjne wzorce wokół RAE”.

Po przejrzeniu repo powiedziałbym teraz inaczej:

RAE-suite już ma większość właściwych idei. Teraz trzeba zdjąć marketingowo-architektoniczną warstwę i doprowadzić wykonanie do żelaznej spójności.

Największa wartość jest w tym, że masz już bardzo dobre kierunki:

RAE-agentic-memory → pamięć i reasoning drift
Hive → wykonanie
Quality → brama jakości
Phoenix/Feniks → analiza/refaktoryzacja/migracje
Lab → eksperymenty i Kaizen
Oracle Sentinel → audytowalność
OpenClaw → bezpieczna warstwa narzędziowa

Największe ryzyko:

moduły wyglądają miejscami jak połączenie dojrzałych repozytoriów, planów strategicznych i implementacji prototypowych.

Dlatego następny najlepszy ruch to nie „dodawać kolejne wzorce AI”, tylko:

1. Jeden trace.
2. Jeden kontrakt.
3. Jeden sposób emisji eventów.
4. Jeden replay.
5. Jeden Context Broker.
6. Jeden Model Router.
7. Jeden Quality Gate.

Jeżeli to zrobisz, RAE-suite zacznie być nie tylko ambitną fabryką agentów, ale systemem, który można debugować, audytować, mierzyć i bezpiecznie rozwijać.
