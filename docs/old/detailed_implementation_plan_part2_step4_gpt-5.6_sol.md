<!-- Plan Część 2 po Kroku 4: GPT-5.6 Sol (openai/gpt-5.6-sol) -->

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
