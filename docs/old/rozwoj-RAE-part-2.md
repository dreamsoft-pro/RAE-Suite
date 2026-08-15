Najważniejszym wzorcem do zaadaptowania z pliku jest kombinacja:

Event Sourcing + CQRS + idempotencja + asynchroniczne kolejki + Saga + bezpieczny replay.

To zmieniłoby RAE z zestawu zaawansowanych modułów w system, który po awarii potrafi wznowić zadanie dokładnie od właściwego kroku, nie wykonać operacji dwukrotnie i odtworzyć cały tok decyzji.

RAE-Suite jest już podzielone na wyspecjalizowane moduły Memory, Phoenix, Hive, Quality i Lab, a README deklaruje federacyjne prompty, streaming, OTEL i trajectory replay. Jednocześnie aktualny kod nadal zawiera miejsca prototypowe, symulowane i niespójne kontraktowo.

Ocena wzorców pod kątem RAE-Suite
Wzorzec	Dopasowanie	Stan w RAE	Rekomendacja
Event Sourcing + CQRS	10/10	częściowo istnieje przez MAES	P0
Idempotency + retry with jitter	10/10	fragmentaryczne	P0
Async Request–Reply + Pub/Sub	9/10	brak wspólnego brokera wykonawczego	P0/P1
Claim Check	9/10	istnieją URI artefaktów, brak jednolitego kontraktu	P0
Saga + kompensacje	9/10	rollback i handoff istnieją osobno	P1
Circuit Breaker + graceful degradation	9/10	dobra specyfikacja, brak pełnej implementacji	P1
Cache Aside i ochrona cache	8/10	cache semantyczny jest prototypowy	P1
API Gateway	8/10	control plane może przejąć tę rolę	P1
Kubernetes patterns	7/10	potrzebne po ustabilizowaniu wykonania	P2
Kafka, sharding, operator K8s	3–6/10 obecnie	przedwczesne bez danych o obciążeniu	później
1. Event Sourcing i CQRS jako kręgosłup RAE

Plik przedstawia Event Sourcing jako zapisywanie pełnej sekwencji zmian zamiast jedynie aktualnego stanu. Pozwala to odtwarzać stan historyczny, wykonywać rollback i tworzyć ślad audytowy. CQRS oddziela modele zapisu od zoptymalizowanych modeli odczytu.

RAE ma już bardzo dobry fundament: MinimumAuditableEvent zawiera między innymi:

event_id,
parent_event_id,
monotoniczny sequence_no,
trace_id,
risk_class,
payload_hash,
policy_bundle_hash,
podpis,
identyfikator Evidence Pack i Execution Receipt.

To jest praktycznie gotowy format zdarzenia domenowego. Brakuje jednak centralnego, trwałego EventStore, który byłby źródłem prawdy dla wykonania.

Rekomendowana granica Event Sourcingu

Nie zapisywałbym event-sourcingowo wszystkiego. Objąłbym nim wyłącznie:

cykl życia zadania,
decyzje agentów,
wywołania narzędzi,
wyniki Quality Gate,
zmiany ryzyka i polityki,
zatwierdzenia,
rollbacki i kompensacje,
zapisy do pamięci,
promocję eksperymentów.

Duże pliki, logi, patche i konteksty powinny trafiać do Artifact Store, a zdarzenie powinno zawierać wyłącznie URI i hash.

Docelowy podział

Write model:

RAE Event Store
└── append-only MAES events

Read models / projekcje CQRS:

task_status_projection
trace_timeline_projection
quality_projection
cost_projection
module_health_projection
incident_projection
model_performance_projection

Portal, Grafana i API nie powinny za każdym razem rekonstruować całej historii. Powinny czytać gotowe projekcje.

2. Idempotencja i kontrolowane ponawianie

Plik słusznie wskazuje, że idempotencja jest konieczna dla API, operacji bazodanowych oraz przetwarzania wiadomości z kolejek. Ponowne przetworzenie wiadomości nie może powodować powtórnych skutków ubocznych.

W RAE powinien powstać wspólny klucz:

idempotency_key =
SHA-256(
    tenant_id
    + project_id
    + trace_id
    + step_id
    + action
    + normalized_input_hash
)

Każdy ToolGateway, agent, worker i endpoint mutujący powinien sprawdzać go przed rozpoczęciem operacji.

Aktualny ToolGateway zapisuje context_hash, tool_input_hash, tool_output_hash i lokalny log JSONL, ale nie posiada trwałego rejestru idempotencji.

Retry policy

Plik porównuje retry liniowy, wykładniczy i ich warianty z jitterem, zwracając uwagę na ryzyko zsynchronizowanych „retry storms”.

Dla RAE domyślną strategią powinno być:

exponential backoff
+ full jitter
+ max_attempts
+ max_elapsed_time
+ retry budget
+ klasyfikacja błędu

Nie należy ponawiać:

błędów polityki,
błędów walidacji,
braku uprawnień,
deterministycznych błędów kodu,
operacji z efektem ubocznym bez klucza idempotencji.

Ponawiane mogą być:

timeouty sieciowe,
HTTP 429,
wybrane HTTP 5xx,
tymczasowy brak modelu,
transient database errors,
chwilowy brak workera.

Po wyczerpaniu prób zadanie powinno trafić do Dead Letter Queue, a nie do kolejnej nieograniczonej pętli agentów.

3. Asynchroniczne wykonanie z Redis Streams

Plik opisuje:

Async Request–Reply,
Publisher–Subscriber,
Claim Check,
Priority Queue,
Saga,
Competing Consumers.

Są to wzorce bardzo dobrze pasujące do RAE.

Długie zadanie powinno być przyjmowane w następujący sposób:

POST /v1/tasks
Idempotency-Key: ...

HTTP/1.1 202 Accepted
Location: /v1/tasks/{task_id}

Następnie zadanie trafia do brokera, a klient sprawdza status lub otrzymuje zdarzenia przez SSE/WebSocket.

Nie wdrażałbym teraz Kafki

RAE ma już Redis w podstawowym stosie. Na pierwszym etapie wybrałbym:

Redis Streams,
consumer groups,
pending entries,
retry stream,
dead-letter stream,
priorytety zależne od klasy ryzyka.

Kafka ma sens później, gdy pojawią się potrzeby:

bardzo długiej retencji,
ogromnej liczby zdarzeń,
licznych niezależnych konsumentów,
ponownego przetwarzania wielkich strumieni,
CDC między wieloma systemami.

Dodanie jej obecnie zwiększyłoby głównie koszt operacyjny.

4. Claim Check dla promptów, patchy i logów

Claim Check polega na umieszczeniu dużego payloadu w osobnym magazynie i przesyłaniu w wiadomości tylko odwołania.

RAE częściowo już to robi: ToolGateway zapisuje output do pliku i umieszcza raw_output_uri w trajektorii.

Należy to sformalizować jako ArtifactRef:

class ArtifactRef:
    artifact_id: str
    uri: str
    sha256: str
    media_type: str
    size_bytes: int
    redaction_status: str
    encryption_key_id: str | None
    retention_policy: str

Do kolejki nie powinny trafiać bezpośrednio:

kompletne repozytoria,
duże konteksty,
stdout/stderr,
wygenerowane patche,
raporty SonarQube,
nagrania Playwright,
pełne odpowiedzi modeli.

To ograniczy rozmiary wiadomości, wycieki danych i liczbę kopii w systemie.

5. Saga jako model całego wykonania

Przepływ:

Suite → Hive → Quality → Phoenix → Quality → Lab → Memory

jest rozproszoną transakcją biznesową.

Plik rekomenduje Sagę do utrzymywania spójności między usługami bez klasycznych transakcji rozproszonych.

RAE ma już:

state machine w AutonomyKernel,
HandoffEnvelope,
RollbackPlan,
klasyfikację zakresu incydentu,
SLA rollbacku.

Brakuje trwałego koordynatora Sagi.

Każdy krok powinien posiadać:

execute()
compensate()
timeout
retry_policy
idempotency_key
required_capability
risk_limit
expected_event

Przykładowe kompensacje:

Operacja	Kompensacja
utworzenie worktree	usunięcie worktree
wygenerowanie patcha	oznaczenie patcha jako odrzucony
zastosowanie patcha	revert commit/worktree
zmiana konfiguracji	przywrócenie wersji poprzedniej
zapis pamięci	tombstone lub zdarzenie korygujące
publikacja guardraila	wycofanie wersji reguły
wdrożenie	rollback do poprzedniego obrazu

Nie należy usuwać błędnych zdarzeń z historii. Powinno się dopisywać zdarzenia kompensujące.

6. Circuit Breaker musi obejmować nie tylko sieć

PDF opisuje circuit breaker jako ochronę przed lawinowym obciążeniem systemu po awarii cache.

RAE potrzebuje dwóch rodzajów circuit breakera:

Transportowy

Dla:

modeli LLM,
Memory API,
Qdrant,
Redis,
SonarQube,
GitHub,
zewnętrznych narzędzi.

Stany:

CLOSED → OPEN → HALF_OPEN
Semantyczny

Dla sytuacji, w której system technicznie działa, lecz nie robi postępu:

Phoenix generuje ten sam patch,
Quality zwraca ten sam błąd,
dwa modele powtarzają identyczną argumentację,
agent wykonuje te same narzędzia,
wynik jakości się nie poprawia.

W repo istnieje bardzo dobra specyfikacja HIVE-CIRCUIT-BREAKER, opisująca wykrywanie pętli na podstawie podobieństwa semantycznego, heartbeat i eskalację. Jednak wyszukiwanie repo wskazuje obecnie implementację tylko w dokumencie, a nie działający SemanticWatchdog.

To jest jeden z najwyższych priorytetów.

Po otwarciu circuit breakera system powinien przechodzić do:

trybu tylko analitycznego,
odczytu z cache,
kolejki oczekującej,
ręcznego zatwierdzenia,
alternatywnego providera,
kontrolowanej degradacji.

Nie powinien automatycznie przechodzić do mniej bezpiecznego wykonania lokalnego.

7. Cache wymaga ochrony przed czterema klasami awarii

Plik pokazuje:

thundering herd,
cache penetration,
hot-key breakdown,
cache crash.

Aktualny ProbabilisticSemanticCache ma TTL, probabilistyczną walidację i usuwanie semantycznego sąsiedztwa. Problemem jest to, że:

cache działa w pamięci procesu,
wyszukiwanie jest liniowe po wszystkich wpisach,
_mock_validate_source() nie sprawdza rzeczywistego źródła,
brak wersji embeddingu i chunkera,
brak request coalescing,
brak negative cache,
po restarcie cały stan znika.
Należy dodać
TTL jitter
singleflight / request coalescing
negative caching
source_hash
source_version
embedding_model_hash
chunker_version
prompt_hash
policy_bundle_hash
tenant_id
project_id

Bloom Filter warto dodać dopiero wtedy, gdy pomiary pokażą dużą liczbę zapytań o nieistniejące zasoby.

8. API Gateway i control plane

Plik przypisuje API Gateway funkcje routingu, bezpieczeństwa, limitowania, agregowania odpowiedzi i cache.

Nie tworzyłbym nowej usługi tylko dlatego, że wzorzec istnieje. Obecny rae-suite lub rae-supervisor może zostać formalnym gatewayem, ale powinien przejąć odpowiedzialność za:

uwierzytelnianie,
autoryzację capability contracts,
rate limiting,
budżety tokenowe i kosztowe,
idempotency keys,
walidację schematów,
propagację traceparent,
przyjmowanie zadań asynchronicznych,
dostęp do statusu i rezultatów,
API composition.

Szczególnej uwagi wymaga rae-supervisor, który ma bezpośrednio zamontowany /var/run/docker.sock. To jest niemal pełny dostęp do hosta. Docelowo pomiędzy supervisorem a Dockerem powinien działać ograniczony execution proxy z allowlistą operacji.

9. Kubernetes — zaadaptować zasady, niekoniecznie od razu platformę

PDF wymienia między innymi health probes, deklarowanie zasobów, init containers, Jobs, service discovery, controller i operator.

Już w Docker Compose można zastosować część tych zasad:

healthcheck,
limity CPU i RAM,
restart policy,
oddzielne migracje/init,
read-only filesystem,
no-new-privileges,
cap_drop,
zależności oparte o zdrowie usługi.

OpenClaw ma już read_only, no-new-privileges i cap_drop: ALL. Pozostałe moduły nie mają jeszcze równie konsekwentnego profilu bezpieczeństwa.

Operator K8s dla RAE miałby sens dopiero po ustabilizowaniu:

kontraktów stanu,
event store,
Sagi,
health modelu,
polityk retry,
recovery procedures.

Inaczej Operator tylko zautomatyzuje niestabilne zachowania.

Krytyczne niespójności obecnej implementacji
Replay wykonuje skutki uboczne

rae replay ponownie uruchamia zapisane komendy przez ToolGateway. fork również wykonuje wszystkie wcześniejsze kroki, aby „odtworzyć stan”.

To nie jest bezpieczny replay audytowy.

Powinny istnieć tryby:

rae replay TRACE                  # bez skutków ubocznych
rae replay TRACE --simulate
rae replay TRACE --execute        # jawnie, po polityce i zatwierdzeniu
rae fork TRACE --from-step N

Dodatkowo CLI odczytuje z logu risk_class, ale ToolGateway nie zapisuje tego pola do replay_entry. Jest to konkretna niespójność kontraktu.

Nieprawidłowy trace jest po cichu zastępowany nowym

TraceContextPropagator.extract() generuje nowy trace przy brakującym lub niepoprawnym traceparent.

Dla zwykłej telemetrii jest to dopuszczalne. Dla audytu może przerwać łańcuch przyczynowy. Powinno dodatkowo powstać zdarzenie:

TRACE_CONTEXT_MISSING
TRACE_CONTEXT_INVALID
TRACE_CHAIN_RESTARTED
AutonomyKernel nadal zawiera dane symulowane

Kod zawiera między innymi:

domyślne powodzenie bez wykonania,
domyślne metryki Quality,
sztuczną zmianę metryk po „alignment rewrite”,
stały koszt tokenów,
stałe wartości efektywności,
hardkodowany routing modeli.

Te wartości powinny zostać oznaczone jako SIMULATION_ONLY albo usunięte z produkcyjnej ścieżki.

Streaming może rozpocząć wykonanie przed ukończeniem planu

StreamingFunctionComposer natychmiast wywołuje handler po odebraniu kompletnego fragmentu STEP.

Powinno to być dozwolone wyłącznie dla kroków spełniających jednocześnie:

side_effect_free = true
speculative_allowed = true
idempotent = true
risk_class <= R1
Docelowa architektura wykonawcza
                         ┌─────────────────────┐
Client / Agent ─────────►│ RAE API Gateway     │
                         │ auth / policy / 202 │
                         └─────────┬───────────┘
                                   │
                      Command + idempotency key
                                   │
                         ┌─────────▼───────────┐
                         │ Command Store       │
                         │ + Transactional     │
                         │   Outbox            │
                         └─────────┬───────────┘
                                   │
                         ┌─────────▼───────────┐
                         │ Redis Streams       │
                         │ priority / retry /  │
                         │ DLQ / consumer grp  │
                         └─────────┬───────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
              Phoenix             Hive             Quality
                 │                 │                 │
                 └────────── Saga Coordinator ──────┘
                                   │
                         ┌─────────▼───────────┐
                         │ MAES Event Store    │
                         └─────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
               Projections     Artifact Store    RAE Memory
                    │
             Portal / Grafana / Lab

Transactional Outbox nie jest bezpośrednio opisany w PDF, ale jest koniecznym uzupełnieniem: zapobiega sytuacji, w której zapis do bazy się powiedzie, a publikacja do kolejki nie — albo odwrotnie.

Kolejność wdrożenia
Etap 0 — usunięcie niejasności źródła prawdy

README deklaruje „RAE-Suite v4.3”, podczas gdy najnowszy widoczny commit jest opisany jako release 3.8.1.

Należy ujednolicić:

wersję produktu,
wersje kontraktów,
wersje submodułów,
status implemented / prototype / mock / specification,
manifest funkcjonalności.

Istniejący dokument wzorce-ocena-w-kontekście_RAE-Suite.md jest już częściowo nieaktualny. Wskazuje jako braki między innymi Context Broker, adaptive retrieval i federacyjne prompty, podczas gdy obecny kod zawiera ContextBroker, FederatedPromptRegistry i StreamingFunctionComposer.

Etap 1 — durable execution
PostgreSQL Event Store dla MAES.
Command Store z idempotency key.
Transactional Outbox.
Artifact Store i Claim Check.
Projekcje CQRS.
Replay bez skutków ubocznych.
Prawdziwe podpisy i spójne sequence_no.
Etap 2 — komunikacja asynchroniczna
Redis Streams.
Consumer groups według capabilities.
HTTP 202 i status taska.
Retry z exponential jitter.
DLQ.
Priorytety według ryzyka i deadline.
Saga Coordinator i kompensacje.
Etap 3 — odporność
Transport Circuit Breaker.
Semantic Watchdog.
Heartbeat i progress events.
Cache singleflight i TTL jitter.
Source-aware cache invalidation.
Graceful degradation.
Usunięcie automatycznych niebezpiecznych fallbacków lokalnych.
Etap 4 — skalowanie na podstawie pomiarów

Dopiero wtedy rozważać:

Kafka,
Kubernetes Operator,
HA PostgreSQL/Redis/Qdrant,
sharding,
dynamiczne skalowanie workerów,
wielowęzłową realizację zadań.
Kryteria ukończenia kręgosłupa wykonawczego

System można uznać za produkcyjnie trwały, gdy:

Dwukrotne wysłanie tego samego polecenia zwraca ten sam ExecutionReceipt.
Zabicie workera w połowie zadania nie powoduje utraty zadania ani podwójnego efektu.
Replay domyślnie nie wykonuje komend.
Każdy krok ma jeden monotoniczny łańcuch MAES.
Każdy duży artefakt ma URI, hash i status redakcji.
Każdy retry jest ograniczony, sklasyfikowany i ma jitter.
Awaria modułu prowadzi do kompensacji, DLQ lub degradacji, a nie do niekontrolowanego fallbacku.
Dashboard pokazuje rzeczywiste, a nie hardkodowane koszty, opóźnienia i wyniki jakości.

Najważniejsza decyzja architektoniczna: nie dodawać teraz kolejnych „inteligentnych” wzorców agentowych. Najpierw połączyć istniejące elementy RAE przez Event Store, idempotencję, Outbox, Redis Streams, Sagę i bezpieczny replay. To obecnie da RAE-Suite większy wzrost autonomii i niezawodności niż wdrożenie kolejnego modelu, agenta lub warstwy abstrakcji.
