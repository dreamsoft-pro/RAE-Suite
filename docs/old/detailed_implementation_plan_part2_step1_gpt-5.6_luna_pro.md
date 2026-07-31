<!-- Plan Część 2 po Kroku 1: GPT-5.6 Luna Pro (openai/gpt-5.6-luna-pro) -->

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