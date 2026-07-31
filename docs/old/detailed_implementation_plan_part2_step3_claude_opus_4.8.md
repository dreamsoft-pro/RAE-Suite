<!-- Plan Część 2 po Kroku 3: Claude Opus 4.8 (anthropic/claude-opus-4.8) -->

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