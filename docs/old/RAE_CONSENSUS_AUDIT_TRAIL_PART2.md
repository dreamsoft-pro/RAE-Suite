# RAE-Suite Part 2 OpenRouter Multi-Model Consensus Audit Trail
**Data wykonania:** 2026-07-31 07:53:42

## Krok 1: GPT-5.6 Luna Pro (openai/gpt-5.6-luna-pro)
**Rola:** Logic & Domain Model Audit (Event Sourcing, CQRS & Saga)  
**Czas:** 07:54:23  

### Wynik Audytu i Rekomendacje:

# Audyt logiczny RAE-Suite Część 2

## 1. Ocena ogólna

Kierunek architektoniczny jest poprawny: Event Store, CQRS, Transactional Outbox, Claim Check, idempotencja, Saga oraz dwa rodzaje Circuit Breakerów tworzą sensowny fundament dla audytowalnej autonomii.

Model nie jest jednak jeszcze domknięty domenowo. Najważniejsze problemy to:

1. **Niejednoznaczne źródło prawdy** — Redis Streams nie może być traktowany jako źródło stanu procesu; powinien być wyłącznie transportem.
2. **Błędnie zdefiniowana idempotencja** — `trace_id` w kluczu idempotencji powoduje, że ponowienie logicznie tego samego polecenia może otrzymać inny klucz.
3. **Brak pełnego modelu cyklu życia Sagi** — opisano `execute()` i `compensate()`, ale nie zdefiniowano stanów, timeoutów, niepewnego wyniku, anulowania ani eskalacji do człowieka.
4. **Brak Inbox/ deduplikacji konsumenta** — Outbox zabezpiecza publikację, ale nie zabezpiecza przed wielokrotnym przetworzeniem komunikatu.
5. **Zbyt mocne gwarancje wykonania** — „identyczny ExecutionReceipt” jest osiągalny, ale nie oznacza dokładnie jednokrotnego wykonania skutku ubocznego.
6. **Niedookreślony Claim Check** — brakuje kontroli dostępu, wersjonowania artefaktu, ochrony przed podmianą URI, skanowania oraz polityki usuwania.
7. **Brak formalnego modelu zdarzeń i wersjonowania** — potrzebne są `aggregate_id`, `aggregate_version`, `causation_id`, `correlation_id`, typ zdarzenia i polityka kompatybilności.
8. **Replay miesza dwa różne pojęcia** — replay zdarzeń do odbudowy projekcji oraz ponowne wykonanie działania powinny być osobnymi operacjami.
9. **Semantic Watchdog nie powinien bezpośrednio zatrzymywać procesu** — powinien publikować decyzję domenową, np. `SemanticStagnationDetected`, obsługiwaną przez politykę workflow.
10. **Brak stanów manualnej interwencji** — proces powinien umieć przejść do `PAUSED`, `MANUAL_REVIEW_REQUIRED` i `UNKNOWN_OUTCOME`.

---

# Zaktualizowany plan rozwoju

```markdown
# RAE-Suite Część 2: Flow & Audytowalna Autonomia

## 1. Cele i gwarancje

RAE-Suite zapewnia:

- trwały zapis historii domenowej,
- asynchroniczne i odporne na awarie wykonywanie poleceń,
- audytowalny stan procesów i Sag,
- bezpieczne ponowienia przy semantyce at-least-once delivery,
- deduplikację poleceń i komunikatów,
- replay projekcji bez skutków ubocznych,
- jawne zarządzanie kompensacją i niepewnym wynikiem,
- zatrzymywanie pętli transportowych i semantycznych.

System nie deklaruje ogólnego `exactly-once side effect`.
Gwarancja brzmi:

> at-least-once delivery + idempotent command handling + deduplikacja + trwały ExecutionReceipt.

---

## 2. Granice odpowiedzialności

### 2.1 Event Store

Event Store jest źródłem prawdy dla:

- stanu agregatów domenowych,
- historii zmian,
- stanu Sagi,
- decyzji workflow,
- wyników wykonania,
- kompensacji,
- blokad i eskalacji.

Event Store nie jest kolejką.

### 2.2 Command Store

Command Store przechowuje:

- przyjęte polecenia,
- klucz idempotencji,
- status przetwarzania,
- wynik końcowy,
- `ExecutionReceipt`,
- powiązane `correlation_id` i `causation_id`.

### 2.3 Transactional Outbox

Outbox znajduje się w tej samej transakcji co zapis zdarzeń i zmian Command Store.

Transakcja:

1. waliduje polecenie,
2. aktualizuje agregat,
3. zapisuje zdarzenia,
4. zapisuje wpisy Outbox,
5. zapisuje lub aktualizuje Command Store.

Dopiero po zatwierdzeniu transakcji publisher wysyła komunikat do brokera.

### 2.4 Broker

Redis Streams lub inny broker jest transportem:

- zapewnia consumer groups,
- retry,
- visibility timeout,
- DLQ,
- priorytety,
- backpressure.

Utrata wiadomości z brokera nie może oznaczać utraty stanu domenowego.

---

## 3. Model zdarzenia domenowego

```typescript
export interface DomainEvent<T = unknown> {
  readonly eventId: string;
  readonly eventType: string;
  readonly eventVersion: number;

  readonly aggregateType: string;
  readonly aggregateId: string;
  readonly aggregateVersion: number;

  readonly tenantId: string;
  readonly projectId?: string;

  readonly occurredAt: string;
  readonly correlationId: string;
  readonly causationId?: string;

  readonly actor: {
    readonly type: 'USER' | 'AGENT' | 'SYSTEM' | 'WORKER';
    readonly id: string;
  };

  readonly payload: T;
  readonly metadata: Record<string, string>;
}
```

Wymagania:

- zdarzenia są niemutowalne,
- `aggregateVersion` jest kontrolowane optymistyczną kontrolą współbieżności,
- typ i wersja zdarzenia są jawne,
- zmiany kontraktu wymagają upcastera lub nowej wersji zdarzenia,
- payload nie zawiera dużych danych — używa `ArtifactRef`.

---

## 4. Command Store i idempotencja

### 4.1 Klucz idempotencji

Klucz nie powinien być wyprowadzany z `trace_id`, ponieważ trace może zmienić się podczas ponowienia.

Preferowany model:

```text
idempotency_key =
  client_provided_key
  + tenant_id
  + command_type
```

Jeżeli klient nie dostarcza klucza:

```text
derived_key =
  SHA-256(
    tenant_id
    + aggregate_id
    + command_type
    + canonical_input_hash
    + logical_attempt_id
  )
```

`trace_id` służy do korelacji i obserwowalności, nie do identyfikacji tej samej operacji.

### 4.2 Status polecenia

```typescript
export type CommandStatus =
  | 'ACCEPTED'
  | 'DISPATCHED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'RETRY_SCHEDULED'
  | 'DLQ'
  | 'CANCELLED'
  | 'UNKNOWN_OUTCOME'
  | 'MANUAL_REVIEW_REQUIRED';
```

Command Store musi przechowywać:

```typescript
export interface CommandRecord {
  readonly commandId: string;
  readonly idempotencyKey: string;
  readonly commandType: string;
  readonly inputHash: string;

  readonly tenantId: string;
  readonly aggregateId?: string;
  readonly correlationId: string;

  readonly status: CommandStatus;
  readonly attempt: number;
  readonly lastErrorCode?: string;

  readonly executionReceipt?: ExecutionReceipt;
  readonly createdAt: string;
  readonly updatedAt: string;
}
```

Powtórzenie tego samego klucza powinno zwrócić istniejący rekord i zapisany rezultat, a nie utworzyć nowe wykonanie.

---

## 5. Inbox i Outbox

### 5.1 Outbox

```typescript
export interface OutboxMessage {
  readonly messageId: string;
  readonly eventId: string;
  readonly topic: string;
  readonly partitionKey: string;
  readonly payload: unknown;

  readonly status: 'PENDING' | 'PUBLISHED' | 'FAILED';
  readonly attempts: number;
  readonly nextAttemptAt?: string;
  readonly createdAt: string;
}
```

### 5.2 Inbox

Każdy konsument musi utrzymywać Inbox:

```typescript
export interface InboxRecord {
  readonly consumerName: string;
  readonly messageId: string;
  readonly receivedAt: string;
  readonly processedAt?: string;
  readonly resultHash?: string;
}
```

Unikalny indeks:

```text
(consumer_name, message_id)
```

Procesowanie komunikatu:

1. rozpocznij transakcję,
2. spróbuj zapisać Inbox,
3. jeśli wpis już istnieje — pomiń komunikat,
4. wykonaj zmianę domenową,
5. zapisz zdarzenia i ewentualne Outbox,
6. zatwierdź transakcję.

---

## 6. Claim Check i Artifact Store

```typescript
export interface ArtifactRef {
  readonly artifactId: string;
  readonly tenantId: string;
  readonly uri: string;

  readonly sha256: string;
  readonly sizeBytes: number;
  readonly mediaType: string;
  readonly schemaVersion?: string;

  readonly classification: 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';
  readonly encryptionKeyId?: string;

  readonly scanStatus:
    | 'NOT_SCANNED'
    | 'SCANNING'
    | 'SCANNED_SAFE'
    | 'REDACTED'
    | 'REJECTED';

  readonly retentionPolicy: string;
  readonly expiresAt?: string;
  readonly createdAt: string;
}
```

Wymagania:

- `uri` nie może samodzielnie nadawać dostępu; dostęp musi być autoryzowany,
- odczyt powinien używać krótkotrwałych signed URLs lub tokenów,
- worker weryfikuje `sha256` po pobraniu,
- artefakt jest przypisany do `tenant_id` i polityki dostępu,
- skanowanie antywirusowe, DLP i redakcja odbywają się przed udostępnieniem,
- usunięcie artefaktu jest osobnym zdarzeniem audytowym,
- nie wolno usuwać artefaktu wymaganego przez niezamkniętą Sagę,
- duże payloady są przechowywane poza Event Store; zdarzenie zawiera wyłącznie `ArtifactRef`.

---

## 7. Saga Coordinator

Saga jest trwałym procesem orkiestrującym, a nie transakcją rozproszoną.

### 7.1 Stany Sagi

```typescript
export type SagaStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'WAITING'
  | 'PAUSED'
  | 'COMPENSATING'
  | 'COMPLETED'
  | 'FAILED'
  | 'COMPENSATED'
  | 'COMPENSATION_FAILED'
  | 'UNKNOWN_OUTCOME'
  | 'MANUAL_REVIEW_REQUIRED'
  | 'CANCELLED';
```

### 7.2 Stany kroku

```typescript
export type SagaStepStatus =
  | 'PENDING'
  | 'DISPATCHED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'RETRY_SCHEDULED'
  | 'TIMED_OUT'
  | 'UNKNOWN_OUTCOME'
  | 'COMPENSATING'
  | 'COMPENSATED'
  | 'COMPENSATION_FAILED'
  | 'SKIPPED'
  | 'MANUAL_REVIEW_REQUIRED';
```

### 7.3 Kontrakt kroku

```typescript
export interface SagaStep<TPayload = unknown> {
  readonly stepId: string;
  readonly action: string;
  readonly order: number;

  readonly execute: (payload: TPayload) => Promise<StepResult>;
  readonly compensate?: (payload: TPayload) => Promise<CompensateResult>;

  readonly compensationMode:
    | 'REQUIRED'
    | 'BEST_EFFORT'
    | 'NOT_APPLICABLE'
    | 'MANUAL';

  readonly timeoutMs: number;
  readonly retryPolicy: RetryPolicy;

  readonly idempotencyScope:
    | 'STEP'
    | 'COMMAND'
    | 'EXTERNAL_RESOURCE';

  readonly irreversible: boolean;
}
```

### 7.4 Reguły wykonania

- każdy krok ma własny trwały status,
- wykonanie kroku jest idempotentne,
- po timeoutcie wynik może być `UNKNOWN_OUTCOME`, a nie automatycznie `FAILED`,
- kompensacja rozpoczyna się dopiero po ustaleniu, które kroki zakończyły się sukcesem,
- kompensacja przebiega w odwrotnej kolejności,
- brak kompensatora dla operacji odwracalnej jest błędem konfiguracji,
- operacje nieodwracalne wymagają polityki `MANUAL` lub wcześniejszej autoryzacji,
- błąd kompensacji nie jest ukrywany — kończy się `COMPENSATION_FAILED` lub `MANUAL_REVIEW_REQUIRED`,
- Saga może zostać wznowiona po awarii koordynatora.

### 7.5 Zdarzenia Sagi

Minimalny zestaw:

```text
SagaStarted
SagaPaused
SagaResumed
SagaCancelled
SagaStepDispatched
SagaStepStarted
SagaStepSucceeded
SagaStepFailed
SagaStepTimedOut
SagaStepUnknownOutcome
SagaCompensationStarted
SagaStepCompensationStarted
SagaStepCompensated
SagaStepCompensationFailed
SagaCompleted
SagaFailed
SagaManualReviewRequired
```

---

## 8. ExecutionReceipt

```typescript
export interface ExecutionReceipt {
  readonly receiptId: string;
  readonly commandId: string;
  readonly idempotencyKey: string;

  readonly status:
    | 'SUCCEEDED'
    | 'FAILED'
    | 'UNKNOWN_OUTCOME'
    | 'MANUAL_REVIEW_REQUIRED';

  readonly effectClass:
    | 'READ_ONLY'
    | 'REVERSIBLE'
    | 'IRREVERSIBLE';

  readonly resultHash?: string;
  readonly resultRef?: ArtifactRef;

  readonly executedAt?: string;
  readonly completedAt?: string;
  readonly attempts: number;
  readonly providerReceipts?: Record<string, string>;
}
```

Receipt jest trwałym wynikiem obsługi polecenia. Nie powinien sugerować, że efekt zewnętrzny nastąpił dokładnie raz, jeśli zewnętrzny system nie oferuje własnej idempotencji.

Dla efektów zewnętrznych należy stosować:

- idempotency key przekazywany do providera,
- deduplikację po stronie adaptera,
- query-after-timeout,
- `UNKNOWN_OUTCOME`,
- ręczne rozstrzygnięcie w razie braku możliwości weryfikacji.

---

## 9. Replay

Należy rozdzielić trzy tryby:

### 9.1 Projection replay

```text
rae replay --projection <name> --from <event_id>
```

- odczytuje zdarzenia,
- odbudowuje read model,
- nie wywołuje narzędzi ani efektów ubocznych.

### 9.2 Audit replay

```text
rae replay --audit <trace_id>
```

- odtwarza chronologię decyzji,
- rekonstruuje stan Sagi,
- generuje raport,
- nie publikuje nowych poleceń.

### 9.3 Controlled re-execution

```text
rae reexecute --command <command_id> --approval <approval_id>
```

- tworzy nowe polecenie,
- wymaga nowego klucza idempotencji,
- wymaga polityki i autoryzacji,
- nie jest mechanicznym ponownym uruchomieniem starego komunikatu,
- wykonuje tylko dozwolone kroki.

---

## 10. Circuit Breakery

### 10.1 Transport Circuit Breaker

Stan per zależność i operację:

```text
CLOSED -> OPEN -> HALF_OPEN -> CLOSED
```

Obsługiwane parametry:

- failure threshold,
- rolling window,
- cooldown,
- half-open probe limit,
- timeout,
- retry budget,
- provider-specific rate limits.

Nie wolno łączyć

---

## Krok 2: DeepSeek R1 (deepseek/deepseek-r1)
**Rola:** Deep Runtime & Concurrency Audit (Redis Streams & Semantic Watchdog)  
**Czas:** 07:55:04  

### Wynik Audytu i Rekomendacje:

**Audyt Runtime & Concurrency (Redis Streams & Semantic Watchdog):**

1. **Konkretne luki i rekomendacje:**

   **Redis Streams:**
   - **Problem:** Brak mechanizmu XCLAIM dla pending entries w przypadku awarii konsumenta. Consumer group może utknąć w nieskończonych retries.
   - **Rozwiązanie:** Wprowadź `DeadLetterCoordinator` monitorujący `XINFO GROUPS i XCLAIM` z timeoutem. Automatyczne przenoszenie do DLQ po N nieudanych próbach.
   
   **Semantic Watchdog:**
   - **Problem:** Brak `heartbeat` w krokach Sagi. Watchdog nie może odróżnić długiego przetwarzania od martwego bloku.
   - **Rozwiązanie:** Dodaj `SagaHeartbeat` event emitowany okresowo przez aktywne kroki. Brak heartbeatów przez M interwałów → `SemanticStagnationDetected`.

   **Idempotentność:**
   - **Problem:** Concurrent writes do Command Store z tym samym `idempotency_key` mogą powodować race condition.
   - **Rozwiązanie:** Wprowadź `ON CONFLICT DO UPDATE` z warunkiem `WHERE status NOT IN ('SUCCEEDED', 'FAILED')`.

   **Replay:**
   - **Problem:** Replay zdarzeń może nadpisać aktualny stan projekcji, jeśli nie używa snapshotów.
   - **Rozwiązanie:** Wymagaj jawnego `snapshot_id` w komendzie replay, blokuj repliki read-only podczas odbudowy.

   **Circuit Breaker:**
   - **Problem:** Brak separacji metryk transportowych (np. timeouty Redis) od semantycznych (np. biznesowe reguły stagnacji).
   - **Rozwiązanie:** Zdefiniuj dwa osobne typy CB w kodzie: `TransportCircuitBreaker` i `SemanticCircuitBreaker`.

---

**Zaktualizowany Plan (Kluczowe zmiany):**

```markdown
## 2.4 Broker (Redis Streams Specyfikacja)

```typescript
export interface RedisStreamsConfig {
  consumerGroup: string;
  consumerName: string; // Unikalny per worker
  maxDeliveries: number; // Przed DLQ
  claimTimeoutMs: number; // Czas na XCLAIM
  dlqStreamSuffix: string; // np. ":dlq"
  priorityWeights: Record<string, number>; // Priorytety strumieni
  backpressureThreshold: number; // Maksymalny backlog per consumer
}

// Przetwarzanie wiadomości:
async function processMessage() {
  const messages = await XREADGROUP(...);
  for (const msg of messages) {
    try {
      await procesuj(msg);
      await XACK(...);
    } catch (error) {
      if (msg.deliveryCount >= config.maxDeliveries) {
        await XDEL(...);
        await XADD(config.dlqStreamSuffix, ...);
      } else {
        await XCLAIM(...); // Przejęcie do ponownej próby
      }
    }
  }
}
```

## 5.3 Inbox (Redis Implementacja)

```typescript
// Atomiczne rejestrowanie przetworzenia wiadomości
const LUA_INBOX_SCRIPT = `
  if redis.call("EXISTS", KEYS[1]) == 0 then
    redis.call("HSET", KEYS[1], 
      "message_id", ARGV[1], 
      "received_at", ARGV[2]
    )
    return 1
  else
    return 0
  end
`;

async function tryProcess(messageId: string) {
  const key = `inbox:${consumerName}:${messageId}`;
  const result = await redis.eval(
    LUA_INBOX_SCRIPT, 
    1, 
    key, 
    messageId, 
    new Date().toISOString()
  );
  return result === 1; // Czy przetworzyć?
}
```

## 7.6 Saga Timeout i Heartbeaty

```typescript
// W kroku Sagi:
interface SagaStep {
  // ...
  heartbeatIntervalMs?: number; // Wymagany dla długich kroków
  timeoutAction: 'FAIL' | 'COMPENSATE' | 'ESCALATE';
}

// Koordynator emituje SagaStepHeartbeat co heartbeatIntervalMs
// Brak 3 kolejnych heartbeatów → timeout
```

## 10. Circuit Breaker (Rozszerzenie)

### 10.3 Semantic Circuit Breaker

```typescript
export interface SemanticBreakerState {
  breakerId: string;
  status: 'GUARDED' | 'TRIPPED' | 'BYPASSED';
  tripConditions: {
    stagnationIntervalMs: number;
    maxHeartbeatSkips: number;
    errorPatterns: string[]; // Np. ['ValidationError', 'Timeout']
  };
  actions: {
    onTrip: 'PAUSE_SAGA' | 'CANCEL_PROCESS' | 'NOTIFY';
    onClear: 'RESUME' | 'REQUIRE_MANUAL_APPROVAL';
  };
  stats: {
    consecutiveTimeouts: number;
    lastHeartbeatAt: string;
  };
}

// Integracja z Sagą:
saga.on('SagaStepHeartbeat', (event) => {
  breaker.updateHeartbeat(event.sagaId);
});

breaker.on('trip', (event) => {
  sagaRepository.updateStatus(event.sagaId, 'PAUSED');
  eventStore.publish(new SemanticBreakerTripped(event));
});
```

## 11. Replay Integrity

```markdown
### 9.4 Replay Locking

- Replay projekcji musi blokować zapis do danego agregatu do czasu ukończenia.
- Użyj `SELECT ... FOR UPDATE` w Event Store podczas replay.
- Wersjonowanie snapshotów z `watermark` dla spójności temporalnej.

### 9.5 Replay Guard

```typescript
// Sprawdź przed reexecution:
function canReexecute(commandId: string) {
  const original = commandStore.get(commandId);
  return original.effectClass !== 'IRREVERSIBLE' 
    && original.status === 'SUCCEEDED'
    && !sagaRepository.isActive(original.correlationId);
}
```

## 12. Transactional Outbox (Redis Optymalizacja)

```typescript
// Batchowe publikowanie z Outbox do Redis Streams
// Użyj XADD z MAXLEN dla kontroli zużycia pamięci
async function publishOutbox() {
  const messages = await outboxRepository.getPending();
  const pipeline = redis.pipeline();
  messages.forEach(msg => {
    pipeline.xadd(
      msg.topic, 
      'MAXLEN', '~', config.maxStreamLength,
      '*', 
      'payload', JSON.stringify(msg.payload)
    );
    pipeline.updateOutboxStatus(msg.id, 'PUBLISHED');
  });
  await pipeline.exec();
}
```

---

## Krok 3: Claude Opus 4.8 (anthropic/claude-opus-4.8)
**Rola:** Types & Architecture Audit (ArtifactRef, Control Plane & Safe Replay)  
**Czas:** 07:55:59  

### Wynik Audytu i Rekomendacje:

# Audyt Typów i Architektury — RAE-Suite Część 2
## Types & Architecture Audit (ArtifactRef, Control Plane & Safe Replay)

---

## 1. Lista Uwag, Luk i Rekomendacji

### 1.1 Ścisłość Typowania (Branded Types)

| # | Luka | Ryzyko | Rekomendacja |
|---|------|--------|--------------|
| T1 | `ArtifactRef` nie istnieje w planie — payloady są luźnymi `JSON.stringify(msg.payload)`. Brak referencji do artefaktów binarnych/dużych. | Wrzucanie dużych blobów do Redis Streams (utrata pamięci, `MAXLEN` odcina dane audytowe). | Wprowadź `ArtifactRef` (branded) jako wskaźnik do Content-Addressable Store (CAS). W Stream trzymamy tylko `ArtifactRef` + hash. |
| T2 | `SagaId`, `CommandId`, `IdempotencyKey`, `CorrelationId` są zwykłymi `string`. | Zamiana argumentów (`canReexecute(commandId)` vs `correlationId`) niewykrywalna w kompilacji. | Branded types z `unique symbol`. Konstruktory walidujące (smart constructors). |
| T3 | `SagaStep` nie ma dyskryminatora typu kroku (`kind`). `timeoutAction` i `heartbeatIntervalMs` są opcjonalne bez zależności. | Krok bez kompensacji może dostać `timeoutAction: 'COMPENSATE'`. | Discriminated union `SagaStep` z wymuszonym `compensation` gdy `compensable: true`. |
| T4 | Brak typu `EffectClass` — używany jako string literal `'IRREVERSIBLE'` bez definicji. | Literówki, brak wyczerpującego `switch`. | Zdefiniuj enum/union `EffectClass` + exhaustive checks. |
| T5 | `Record<string, number>` dla `priorityWeights` — brak ograniczenia kluczy do znanych strumieni. | Niepoprawne klucze przechodzą kompilację. | `Record<StreamName, PriorityWeight>` z brandowanym `StreamName`. |

### 1.2 Control Plane / Izolacja Wykonania (Docker Proxy)

| # | Luka | Ryzyko | Rekomendacja |
|---|------|--------|--------------|
| C1 | **Brak jakiejkolwiek warstwy Control Plane** dla wykonania kroków w kontenerach. Plan nie adresuje `/var/run/docker.sock`. | Bezpośredni dostęp do socketu Dockera = root-equivalent na hoście (escape całego node’a). | **Nigdy** nie montuj `docker.sock` do workerów. Wprowadź `DockerControlPlaneProxy` — allow-list API. |
| C2 | Brak izolacji sieciowej/zasobowej per krok Sagi. | Krok „ucieka” poza swój budżet CPU/RAM/net. | `ExecutionSandboxSpec` (limity, read-only rootfs, no-new-privileges, seccomp). |
| C3 | Brak podpisu/tożsamości wywołań Control Plane. | Spoofing komend uruchomienia. | mTLS + `ControlPlaneToken` (short-lived, scoped per SagaId). |

### 1.3 Kompensacja Sagi & Safe Replay

| # | Luka | Ryzyko | Rekomendacja |
|---|------|--------|--------------|
| S1 | `canReexecute` zwraca `boolean` — traci powód odmowy. | Brak audytu decyzji o odmowie replay. | Zwracaj `ReplayDecision` (Result-type z powodem). |
| S2 | Replay bez izolacji efektów zewnętrznych — `SELECT ... FOR UPDATE` chroni tylko DB, nie efekty side-effect. | Replay może wywołać realne komendy do świata zewnętrznego. | Tryb `ReplayMode: 'DRY_RUN' \| 'REBUILD_PROJECTION' \| 'LIVE'`; sandbox side-effectów w trybie replay. |
| S3 | Kompensacja nie jest idempotentna kontraktowo. | Podwójna kompensacja przy retry watchdog. | `CompensationKey` (branded) + Inbox dla kompensacji. |
| S4 | `SemanticBreakerState.status` (`GUARDED`) i `SagaStatus` (`PAUSED`) nie mają wspólnego, spójnego modelu przejść. | Rozjazd stanów breaker↔saga. | Jawna maszyna stanów + typy przejść. |
| S5 | Lua Inbox nie ma TTL ani wersjonowania — rośnie w nieskończoność. | Redis OOM. | TTL + `schemaVersion` w rekordzie inbox. |

---

## 2. Zaktualizowany, Rozszerzony Plan

```markdown
# RAE-Suite Część 2 — v2 (Types & Safe Autonomy)

## 0. Fundament Typów (Branded Primitives)
```

```typescript
// ── core/branding.ts ──────────────────────────────────────────
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

// Smart constructor helper (Result-based)
export type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

// ── Branded identifiers ───────────────────────────────────────
export type SagaId          = Brand<string, 'SagaId'>;
export type CommandId       = Brand<string, 'CommandId'>;
export type CorrelationId   = Brand<string, 'CorrelationId'>;
export type IdempotencyKey  = Brand<string, 'IdempotencyKey'>;
export type CompensationKey = Brand<string, 'CompensationKey'>;
export type StreamName      = Brand<string, 'StreamName'>;
export type ConsumerName    = Brand<string, 'ConsumerName'>;
export type SnapshotId      = Brand<string, 'SnapshotId'>;
export type Watermark       = Brand<bigint, 'Watermark'>;        // monotoniczna
export type PriorityWeight  = Brand<number, 'PriorityWeight'>;   // 0..1

// UUID-validating constructor (przykład)
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function makeSagaId(v: string): Result<SagaId, 'INVALID_UUID'> {
  return UUID_RE.test(v)
    ? { ok: true, value: v as SagaId }
    : { ok: false, error: 'INVALID_UUID' };
}

// IdempotencyKey wymaga scope+hash — nie dowolny string
export function makeIdempotencyKey(
  scope: string, payloadHash: string,
): IdempotencyKey {
  return `${scope}:${payloadHash}` as IdempotencyKey;
}
```

### 0.1 ArtifactRef — Content-Addressable, nie inline

```typescript
// ── core/artifact.ts ──────────────────────────────────────────
export type ContentHash = Brand<string, 'ContentHash'>; // sha256:...

/**
 * Do Redis Streams / EventStore NIGDY nie trafia surowy blob.
 * Trafia ArtifactRef -> wskaźnik do CAS (S3/MinIO/FS) + integralność.
 */
export interface ArtifactRef {
  readonly kind: 'ArtifactRef';
  readonly uri: string;             // cas://bucket/sha256:...
  readonly contentHash: ContentHash;
  readonly sizeBytes: number;
  readonly mediaType: string;       // application/json, image/png...
  readonly encoding?: 'gzip' | 'zstd' | 'none';
}

// Payload w streamie = mały envelope; duże dane przez ref.
export type StreamPayload<T> =
  | { mode: 'inline'; data: T }                     // tylko < threshold
  | { mode: 'ref'; ref: ArtifactRef };

export const INLINE_MAX_BYTES = 16 * 1024; // ponad → wymuszony ArtifactRef
```

---

## 2.4 Broker (Redis Streams) — Typowana Specyfikacja

```typescript
export interface RedisStreamsConfig {
  consumerGroup: string;
  consumerName: ConsumerName;
  maxDeliveries: number;
  claimTimeoutMs: number;
  dlqStream: StreamName;                              // pełna nazwa, nie suffix
  priorityWeights: ReadonlyMap<StreamName, PriorityWeight>;
  backpressureThreshold: number;
  inlineMaxBytes: number;                             // = INLINE_MAX_BYTES
}

export interface StreamMessage<T> {
  streamId: string;                 // XADD id (ms-seq)
  streamName: StreamName;
  deliveryCount: number;
  correlationId: CorrelationId;
  idempotencyKey: IdempotencyKey;
  payload: StreamPayload<T>;        // inline lub ArtifactRef
}
```

```typescript
// Przetwarzanie z rozdzieleniem błędów transport/semantyka
type ProcessOutcome =
  | { kind: 'ACK' }
  | { kind: 'RETRY'; reason: TransportError }
  | { kind: 'DLQ';   reason: SemanticError | 'MAX_DELIVERIES' };

async function processMessage<T>(msg: StreamMessage<T>): Promise<void> {
  const outcome = await handle(msg);
  switch (outcome.kind) {
    case 'ACK':
      await XACK(msg.streamName, group, msg.streamId);
      return;
    case 'RETRY':
      if (msg.deliveryCount >= config.maxDeliveries) {
        return toDlq(msg, 'MAX_DELIVERIES');
      }
      // pozostaw w PEL — DeadLetterCoordinator wykona XCLAIM po timeoucie
      return;
    case 'DLQ':
      return toDlq(msg, outcome.reason);
  }
}
```

---

## 3. Control Plane & Izolacja Wykonania (Docker Proxy)

> **Zasada twarda:** żaden worker/krok Sagi nie ma dostępu do
> `/var/run/docker.sock`. Cały ruch przez `DockerControlPlaneProxy`
> z allow-listą, mTLS i scoped tokenami.

```typescript
// ── control-plane/proxy.ts ────────────────────────────────────
export type ControlPlaneToken = Brand<string, 'ControlPlaneToken'>; // short-lived JWT

/** Dozwolone operacje — allow-list (deny-by-default). */
export type DockerVerb =
  | 'container.create'
  | 'container.start'
  | 'container.stop'
  | 'container.logs'
  | 'container.inspect';
// UWAGA: brak 'exec', 'volume.mount(hostPath)', 'privileged'

---

## Krok 4: GPT-5.6 Sol (openai/gpt-5.6-sol)
**Rola:** Performance & Resource Audit (Cache-Aside, Singleflight & Outbox)  
**Czas:** 07:56:48  

### Wynik Audytu i Rekomendacje:

# Audyt Performance & Resource — RAE-Suite Część 2

## 1. Zwięzła recenzja

Plan prawidłowo ogranicza rozmiar wiadomości przez `ArtifactRef`, rozdziela błędy transportowe od semantycznych i wprowadza podstawy bezpiecznego replay. Brakuje jednak mechanizmów chroniących system przed stampede cache, przeciążeniem Redis Streams oraz niespójnością między EventStore, Outbox i publikacją zdarzeń.

Najważniejsze poprawki:

1. Dodać **singleflight**, TTL jitter, stale-while-revalidate i kontrolowane negative caching.
2. Zdefiniować semantyczny klucz cache obejmujący tenant, model, wersję promptu i polityki bezpieczeństwa.
3. Zastąpić deklaratywne `priorityWeights` rzeczywistym schedulerem z ochroną przed starvation.
4. Zapisywać zdarzenie domenowe i rekord Outbox w **jednej transakcji**.
5. Przyjąć semantykę **at-least-once + idempotent Inbox**, nie „exactly once”.
6. W API Gateway zwracać `202 Accepted` z zasobem operacji zamiast utrzymywać długie połączenie.
7. Uzupełnić SLO, metryki przepływu, backpressure i alerty oparte na wieku najstarszej wiadomości, nie wyłącznie długości kolejki.

---

## 2. Lista luk i rekomendacji

### 2.1 Cache semantyczny

| # | Luka | Ryzyko | Rekomendacja |
|---|---|---|---|
| P1 | Brak singleflight/request coalescing. | Wiele identycznych cache missów uruchamia ten sam kosztowny model lub workflow. | Lokalny singleflight per instancja; opcjonalnie krótka blokada rozproszona dla najdroższych operacji. |
| P2 | Brak TTL jitter. | Jednoczesne wygasanie dużej liczby wpisów i fala żądań do backendu. | `effectiveTTL = baseTTL × random(0.85, 1.15)`. |
| P3 | Brak stale-while-revalidate. | Wygasły wpis zawsze powoduje wzrost latencji użytkownika. | Rozdzielić `freshUntil` i `staleUntil`; tylko jeden proces odświeża dane. |
| P4 | Brak zasad negative caching. | Powtarzane zapytania o nieistniejące lub deterministycznie odrzucone dane obciążają backend. | Cache’ować tylko stabilne wyniki typu `NOT_FOUND`/deterministic validation, z krótkim TTL. Nie cache’ować timeoutów, `429` i `5xx`. |
| P5 | Nieokreślony semantyczny klucz cache. | Wyciek między tenantami albo zwrot odpowiedzi wygenerowanej przez inną wersję modelu/polityki. | Klucz musi zawierać tenant, model, wersję promptu, normalizowany input, uprawnienia i wersję polityki. |
| P6 | Brak wersjonowanej invalidacji. | Opóźnione zdarzenie może unieważnić nowszy wpis lub przywrócić stary wynik. | Invalidation event z `entityVersion`; stosować compare-and-delete albo versioned namespace. |
| P7 | Brak limitów pamięci i maksymalnego rozmiaru wpisu. | Cache staje się magazynem blobów i konkuruje ze Streams. | Osobne instancje/pule Redis dla cache i brokera; duże wyniki przez `ArtifactRef`. |
| P8 | Blokada rozproszona bez fencing tokenu byłaby niewystarczająca. | Proces po utracie lease może nadpisać nowszy wynik. | Wykorzystywać monotoniczny `generation`/fencing token przy zapisie wyniku. |

### 2.2 Redis Streams, priorytety i backpressure

| # | Luka | Ryzyko | Rekomendacja |
|---|---|---|---|
| P9 | Redis Streams nie zapewnia globalnego priorytetu wiadomości. | Samo `priorityWeights` nie zmienia kolejności dostarczania. | Osobne strumienie per klasa priorytetu oraz scheduler weighted/deficit round-robin. |
| P10 | Brak ochrony przed starvation. | Ciągły ruch krytyczny blokuje zadania normalne i batch. | Minimalny udział przepustowości i maksymalny czas oczekiwania dla każdej klasy. |
| P11 | `deliveryCount` nie jest natywnym polem wiadomości. | Błędne kwalifikowanie do DLQ. | Odczytywać liczbę dostarczeń z PEL/`XPENDING` albo utrzymywać ją atomowo w envelope/inbox. |
| P12 | Retry pozostawiony w PEL bez harmonogramu. | Hot-loop, niekontrolowany `XCLAIM`, brak backoff. | `XAUTOCLAIM` + `nextAttemptAt`, exponential backoff i jitter; opóźnione retry w osobnym mechanizmie. |
| P13 | `XACK` i zapis do DLQ mogą nie być atomowe. | Wiadomość może znaleźć się jednocześnie w PEL i DLQ albo zniknąć. | Lua: `XADD DLQ` + `XACK` w jednej operacji; w Redis Cluster oba klucze w tym samym hash slocie. |
| P14 | Brak bezpiecznej polityki trimowania. | `MAXLEN` może usunąć wiadomości potrzebne przez wolną grupę lub audyt. | Trimować na podstawie retention i watermarków grup; archiwum audytowe poza Redis. |
| P15 | Backpressure oparty tylko na liczbie wiadomości. | Krótka kolejka może być bardzo stara, a długa może być szybko opróżniana. | Sterować również przez oldest-message-age, PEL age, service time i saturation. |
| P16 | Brak limitu współbieżności per zależność/tenant. | Jeden tenant albo wolna zależność zużywa całą pulę workerów. | Bulkheady, weighted semaphore i limity per tenant/dependency. |
| P17 | Cache i Streams mogą współdzielić politykę eviction. | Eviction danych brokera lub presja pamięci cache wpływa na kolejkę. | Osobne Redis deployments lub co najmniej niezależne pule i `maxmemory-policy`. |

### 2.3 Outbox, EventStore i idempotencja

| # | Luka | Ryzyko | Rekomendacja |
|---|---|---|---|
| P18 | Brak Transactional Outbox. | Commit stanu bez publikacji albo publikacja bez commitowania stanu. | EventStore/domain state i Outbox zapisywać w jednej transakcji DB. |
| P19 | Możliwa sugestia „exactly once”. | Redis, sieć i retry nie zapewniają dokładnie jednokrotnego wykonania efektu. | At-least-once delivery + Inbox + idempotentne handlery. |
| P20 | Inbox TTL nie jest związany z oknem replay. | Po wygaśnięciu klucza stara wiadomość może zostać wykonana ponownie. | Retencja Inbox ≥ maksymalna retencja streamu, retry i replay; trwałe efekty finansowe przechowywać bez TTL w DB. |
| P21 | Brak partycjonowania Outbox. | Rosnący backlog i koszt skanowania tabeli. | Indeks `(status, available_at, id)`, `SKIP LOCKED`, partycjonowanie czasowe i batch publishing. |
| P22 | Brak optimistic concurrency dla agregatu. | Równoległe komendy tworzą niespójny strumień zdarzeń. | `expectedVersion` i unikalność `(aggregate_id, aggregate_version)`. |
| P23 | Brak watermarków projekcji. | API może zwrócić stary read model bez informacji o lag. | Każda projekcja przechowuje monotoniczny watermark; status operacji ujawnia stan materializacji. |

### 2.4 API Gateway i HTTP 202

| # | Luka | Ryzyko | Rekomendacja |
|---|---|---|---|
| P24 | Długie operacje mogą blokować żądanie HTTP. | Timeouty gatewaya, duża liczba otwartych połączeń i retry klientów. | `POST` zwraca `202 Accepted` po trwałym zapisie komendy/Outbox. |
| P25 | Brak kontraktu zasobu operacji. | Klient nie wie, czy zadanie zostało przyjęte, wykonane czy odrzucone. | `OperationId`, `Location`, `Retry-After`, status i opcjonalne SSE/webhook. |
| P26 | Możliwe zwrócenie `202` przed trwałym zapisem. | Klient dostaje potwierdzenie zadania, które może zostać utracone. | `202` dopiero po commitcie komendy oraz Outbox. |
| P27 | Brak deduplikacji retry klienta. | Timeout klienta powoduje utworzenie wielu Sag. | Wymagany `Idempotency-Key`; atomowa rejestracja i zwrot istniejącej operacji. |
| P28 | Polling może przeciążyć Gateway. | Lawina `GET /operations/{id}`. | `ETag`, `If-None-Match`, `Retry-After`, progresywny backoff i limit polling rate. |

---

# 3. Zaktualizowany plan

## 3.1 Typy podstawowe i DTO

```typescript
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

export type SagaId = Brand<string, 'SagaId'>;
export type CommandId = Brand<string, 'CommandId'>;
export type EventId = Brand<string, 'EventId'>;
export type OperationId = Brand<string, 'OperationId'>;
export type CorrelationId = Brand<string, 'CorrelationId'>;
export type CausationId = Brand<string, 'CausationId'>;
export type IdempotencyKey = Brand<string, 'IdempotencyKey'>;
export type StreamName = Brand<string, 'StreamName'>;
export type TenantId = Brand<string, 'TenantId'>;
export type CacheKey = Brand<string, 'CacheKey'>;
export type ContentHash = Brand<string, 'ContentHash'>;
export type AggregateVersion = Brand<number, 'AggregateVersion'>;
export type Watermark = Brand<bigint, 'Watermark'>;

export interface ArtifactRef {
  readonly kind: 'artifact-ref';
  readonly uri: string;
  readonly contentHash: ContentHash;
  readonly sizeBytes: number;
  readonly mediaType: string;
  readonly encoding: 'none' | 'gzip' | 'zstd';
}

export type StreamPayload<T> =
  | { readonly mode: 'inline'; readonly data: T }
  | { readonly mode: 'ref'; readonly ref: ArtifactRef };

export interface MessageEnvelope<T> {
  readonly schemaVersion: number;
  readonly messageId: EventId;
  readonly tenantId: TenantId;
  readonly correlationId: CorrelationId;
  readonly causationId?: CausationId;
  readonly idempotencyKey: IdempotencyKey;
  readonly occurredAt: string;
  readonly payload: StreamPayload<T>;
}
```

Wymagania runtime:

- walidacja wszystkich branded types na granicach systemu,
- limit rozmiaru envelope, np. 16 KiB,
- payload powyżej limitu zapisywany w CAS,
- `PriorityWeight` walidowany runtime; typ brandowany sam nie gwarantuje zakresu,
- lista strumieni jako zamknięta unia lub walidowany rejestr, nie dowolny brandowany string.

---

## 3.2 Cache-Aside i singleflight

```typescript
export interface SemanticCacheDescriptor {
  tenantId: TenantId;
  modelId: string;
  modelVersion: string;
  promptVersion: string;
  policyVersion: string;
  authorizationScopeHash: string;
  normalizedInputHash: ContentHash;
}

export interface CachePolicy {
  freshTtlMs: number;
  staleTtlMs: number;
  negativeTtlMs: number;
  ttlJitterRatio: number;       // np. 0.15
  maxEntryBytes: number;
  singleflightTimeoutMs: number;
}

export type CachedValue<T> =
  | {
      kind: 'VALUE';
      value: StreamPayload<T>;
      entityVersion: bigint;
      generation: bigint;
      freshUntil: number;
      staleUntil: number;
    }
  | {
      kind: 'NEGATIVE';
      reason: 'NOT_FOUND' | 'DETERMINISTIC_REJECTION';
      entityVersion: bigint;
      staleUntil: number;
    };
```

### Algorytm odczytu

1. Zbudować klucz z kanonicznego i wersjonowanego deskryptora.
2. Zwrócić świeżą wartość natychmiast.
3. Dla wartości stale:
   - zwrócić ją, jeśli polityka dopuszcza,
   - uruchomić dokładnie jedno odświeżenie w tle.
4. Dla miss:
   - dołączyć do istniejącego singleflight,
   - lider pobiera dane i zapisuje cache.
5. Timeout, `429` i `5xx` nie tworzą negative cache.
6. Operacje z efektami ubocznymi nigdy nie korzystają z cache jako źródła decyzji o wykonaniu.

```typescript
interface Singleflight {
  do<T>(key: CacheKey, load: () => Promise<T>): Promise<T>;
}
```

Singleflight lokalny jest mechanizmem podstawowym. Blokada Redis powinna być używana tylko dla bardzo kosztownych missów; musi mieć krótki lease, losowy token i fencing generation.

### Invalidation

```typescript
export interface CacheInvalidated {
  kind: 'CACHE_INVALIDATED';
  tenantId: TenantId;
  namespace: string;
  entityId: string;
  entityVersion: bigint;
  occurredAt: string;
}
```

Konsument usuwa wpis tylko wtedy, gdy jego `entityVersion <= invalidation.entityVersion`. Preferowane są wersjonowane namespace’y dla zmian modelu, promptu i polityki.

---

## 3.3 Redis Streams i scheduler priorytetów

```typescript
export type PriorityClass = 'CRITICAL' | 'NORMAL' | 'BATCH';

export interface StreamClassConfig {
  stream: StreamName;
  priority: PriorityClass;
  weight: number;
  minCapacityShare: number;
  maxConcurrency: number;
  maxQueueAgeMs: number;
}

export interface RedisStreamsConfig {
  consumerGroup: string;
  consumerName: string;
  readCount: number;
  blockMs: number;
  claimTimeoutMs: number;
  maxDeliveries: number;
  maxInFlightPerConsumer: number;
  retryBaseMs: number;
  retryMaxMs: number;
  streams: readonly StreamClassConfig[];
  dlqStream: StreamName;
}
```

### Reguły przetwarzania

- Osobny stream dla każdej klasy priorytetu.
- Deficit weighted round-robin zamiast stałego odpytywania wyłącznie krytycznej kolejki.
- Rezerwacja minimalnej przepustowości dla `NORMAL` i `BATCH`.
- Limit współbieżności globalny, per tenant i per zależność.
- `XREADGROUP COUNT` dostrajany do czasu obsługi, nie ustawiany arbitralnie wysoko.
- `XAUTOCLAIM` uruchamiany w małych batchach.
- Retry wykorzystuje exponential backoff z jitterem.
- DLQ zawiera pełny envelope, powód, liczbę prób i `ArtifactRef`, ale nie duży blob.
- `XADD DLQ` i `XACK` wykonywane atomowo przez Lua.

Klucze używane przez jeden skrypt w Redis Cluster muszą mieć wspólny hash tag, np.:

```text


---

## Krok 5: Fable 5 (anthropic/claude-opus-5)
**Rola:** Reliability & ISO Auditability (Auditable Autonomy & Zero-Downtime)  
**Czas:** 07:57:54  

### Wynik Audytu i Rekomendacje:

# Audyt: Reliability & ISO Auditability — RAE-Suite Część 2 (Auditable Autonomy & Zero-Downtime)

## 0. Ocena ogólna

| Wymiar | Ocena | Komentarz |
|---|---|---|
| Cache semantyczny | 8/10 | [PERSON_NAME] dojrzały (singleflight, jitter, SWR, fencing). |
| Transport / Streams | 7,5/10 | Dobry scheduler i DLQ, [PERSON_NAME]. |
| Outbox / EventStore | 7/10 | At-least-once + Inbox poprawne, [PERSON_NAME] i kontroli spójności. |
| **[PERSON_NAME] (hash chaining, ISO 27001/42001)** | **2/10** | Praktycznie nieobecna — [PERSON_NAME] blokerem. |
| **Crash resilience workerów / zero lost tasks** | **4/10** | [PERSON_NAME], brak [PERSON_NAME],

---

