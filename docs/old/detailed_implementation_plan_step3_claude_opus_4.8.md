<!-- Plan po Kroku 3: Claude Opus 4.8 (anthropic/claude-opus-4.8) -->

# Types & Architecture Audit — RAE-Suite (v1.1 → v1.2)

## Część I: Recenzja architektoniczna i typowania

Plan v1.1 jest solidny na poziomie runtime/współbieżności, ale **z perspektywy kontraktów i typów wykazuje krytyczne braki**. Poniżej lista luk uporządkowana wg severity.

---

### 🔴 P0 — Krytyczne braki kontraktowe

#### A1. Brak twardej definicji `CapabilityContract` i mechanizmu hard enforcement
Plan wielokrotnie odwołuje się do "polityki capability" (`tool_timeout`, `graceful_shutdown`), ale **nie definiuje samego kontraktu**. Bez tego enforcement jest iluzoryczny — brak single source of truth dla tego, co worker *może* zrobić.
- **Rekomendacja**: `CapabilityContract` jako typ zamknięty (sealed), walidowany runtime przez `ToolGateway` **przed** dispatch. Naruszenie → `CapabilityViolation`, nigdy silent fallback.

#### A2. Stringly-typed identyfikatory (anti-pattern)
`task_id`, `tenant_id`, `step_id`, `lease_id`, `container_id`, `idempotency_key` są luźnymi stringami. Ryzyko: przekazanie `task_id` tam, gdzie oczekiwany `step_id` — kompilator tego nie złapie. `idempotency_key = hash(...)` jako `text` to bomba zegarowa.
- **Rekomendacja**: **Branded Types** dla wszystkich ID (nominal typing).

#### A3. `conflict_resolution: "LAST_WRITE_WINS"` łamie integralność `compliance_evidence`
Sekcja 1.2 sama wskazuje ryzyko utraty `compliance_evidence`, po czym w 4.3 dopuszcza `LAST_WRITE_WINS`. **Dowody compliance nigdy nie mogą być nadpisane destrukcyjnie.** To sprzeczność wewnętrzna planu.
- **Rekomendacja**: `compliance_evidence` jako struktura append-only (monotoniczna). `LWW` dozwolony wyłącznie dla pól ulotnych (telemetria), nigdy dla dowodów.

#### A4. `state_version` jako `"timestamp_attemptNo_hash"` (opaque string)
Wersja stanu zaszyta w stringu uniemożliwia typowaną walidację optymistyczną i miesza trzy odrębne wymiary (czas, próba, treść).
- **Rekomendacja**: strukturalny `StateVersion` z monotonicznym `revision` (nie timestamp — clock skew) + `content_hash`.

---

### 🟠 P1 — Granice modułów i agnostyczność domeny

#### B1. Przeciek domeny do warstwy runtime
`git commit`, `base_commit`, `workspace_tarball`, Docker/Firecracker wyciekają do rdzenia. `CognitivePlanner` i `ModelRouter` nie powinny wiedzieć nic o Gicie ani Dockerze. To łamie agnostyczność domeny.
- **Rekomendacja**: wprowadzić warstwę `ExecutionSubstrate` (port) — Git/Docker/Firecracker to *adaptery*. Rdzeń operuje na abstrakcyjnych `WorkspaceRef` / `SubstrateCapability`.

#### B2. Niezdefiniowane granice `CognitivePlanner` ↔ `ModelRouter` ↔ `QualityTribunal`
Moduły są wymienione, ale brak kontraktów DTO między nimi. `QualityTribunal` używa "distributed locks" (4.3) — czemu tribunał ma stan współdzielony? To sygnał złej separacji odpowiedzialności.
- **Rekomendacja**: `QualityTribunal` musi być **pure/stateless** (verdict = f(evidence)). Jeśli potrzebuje locka — logika stanu została błędnie wciągnięta do tribunału.

#### B3. Brak kontraktu eskalacji `OpenCode/Hermes`
Eskalacja przekazuje `workspace_tarball + receipt_snapshot` — nieformalne. Brak typowanego `EscalationEnvelope` i typowanego wyniku (Hermes może zwrócić: resolved / needs-human / rejected).
- **Rekomendacja**: `EscalationEnvelope<TContext>` + `EscalationOutcome` jako discriminated union.

---

### 🟡 P2 — Spójność DTO i typów

- **C1.** `resource_usage` miesza jednostki (`cpu_ms` vs `cpu: "2 cores"` jako string). Ujednolicić do liczbowych, typowanych jednostek.
- **C2.** `retry_policy.backoff: "exponential(1s, 10s)"` — DSL w stringu. Powinno być strukturalne.
- **C3.** Brak typu wyniku wykonania jako **discriminated union** (`Succeeded | Failed | Aborted | TimedOut`). Obecnie statusy są rozsiane po stringach.
- **C4.** `max_repair_cycles = min(5, task_risk_factor * 3)` — `task_risk_factor` nietypowany; mieszanie `enum RiskLevel` z liczbą.

---

## Część II: Zaktualizowany plan (v1.2)

```markdown
# Rozszerzony plan RAE-Suite (wersja 1.2 — Types & Architecture)

## Sekcja 0: Zasady Architektoniczne (Invarianty)

INV-1  Domain-Agnostic Core: rdzeń (Planner/Router/Tribunal) nie zna Git,
       Docker, Firecracker. Domena wchodzi wyłącznie przez porty/adaptery.
INV-2  Hard Enforcement: każdy CapabilityContract jest walidowany PRZED
       wykonaniem. Naruszenie => wyjątek typu CapabilityViolation. Zero
       silent fallback, zero best-effort.
INV-3  Branded Identity: wszystkie identyfikatory to typy nominalne.
INV-4  Append-Only Evidence: compliance_evidence jest monotoniczne.
INV-5  Pure Tribunal: QualityTribunal jest bezstanowy i deterministyczny.
INV-6  Total Results: każdy wynik operacji to discriminated union
       (brak wyjątków jako flow control poza granicą enforcement).

## Sekcja 1: Branded Types (fundament)

```typescript
// --- Nominal branding utility ---
type Brand<T, B extends string> = T & { readonly __brand: B };

export type TenantId     = Brand<string, 'TenantId'>;
export type TaskId       = Brand<string, 'TaskId'>;
export type StepId       = Brand<string, 'StepId'>;
export type AttemptNo    = Brand<number, 'AttemptNo'>;
export type LeaseId      = Brand<string, 'LeaseId'>;
export type IdempotencyKey = Brand<string, 'IdempotencyKey'>;
export type ContentHash  = Brand<string, 'ContentHash'>;   // sha256:...
export type WorkspaceRef = Brand<string, 'WorkspaceRef'>;  // agnostyczny uchwyt
export type ContainerRef = Brand<string, 'ContainerRef'>;  // adapter-level

// Smart constructors (jedyne wejście do brandowanego typu)
export const IdempotencyKey = {
  derive(p: {
    tenant: TenantId; task: TaskId; step: StepId;
    attempt: AttemptNo; inputHash: ContentHash;
  }): IdempotencyKey { /* sha256 kanonicznej serializacji */ }
};
```

## Sekcja 2: StateVersion i optymistyczna współbieżność (typowana)

```typescript
export interface StateVersion {
  readonly revision: Brand<number, 'Revision'>;  // monotoniczny licznik, NIE timestamp
  readonly contentHash: ContentHash;
  readonly writtenBy: LeaseId;                    // audytowalne autorstwo
}

export type ConflictPolicy =
  | { kind: 'REJECT' }                            // domyślne dla evidence
  | { kind: 'MERGE_APPEND' }                      // dla pól monotonicznych
  | { kind: 'LAST_WRITE_WINS'; scope: 'TELEMETRY_ONLY' }; // NIGDY dla evidence

// API: If-Match: <revision> => 412 przy mismatch
```

## Sekcja 3: CapabilityContract (Hard Enforcement)

```typescript
export interface CapabilityContract {
  readonly capabilityId: Brand<string, 'CapabilityId'>;
  readonly allowedOperations: ReadonlySet<OperationKind>;
  readonly resourceLimits: ResourceLimits;      // typowane, patrz Sekcja 6
  readonly timeouts: TimeoutPolicy;
  readonly isolation: IsolationLevel;           // 'PROCESS' | 'CONTAINER' | 'MICROVM'
  readonly networkPolicy: 'DENY_ALL' | 'ALLOWLIST';
}

export type EnforcementResult =
  | { ok: true; grant: CapabilityGrant }
  | { ok: false; violation: CapabilityViolation };

export interface CapabilityGate {
  // Wywoływane PRZED każdym dispatch. Brak grant => brak wykonania.
  authorize(req: ExecutionRequest, contract: CapabilityContract): EnforcementResult;
}

export interface CapabilityViolation {
  readonly code: 'RESOURCE_EXCEEDED' | 'OP_NOT_ALLOWED'
             | 'ISOLATION_TOO_WEAK' | 'NETWORK_DENIED';
  readonly detail: string;
  readonly nonRecoverable: boolean;  // => bezpośrednio do DLQ / eskalacja
}
```

## Sekcja 4: Granice modułów (porty i DTO)

### 4.1 CognitivePlanner (domain-agnostic)
```typescript
export interface PlanRequest {
  readonly tenant: TenantId;
  readonly task: TaskId;
  readonly goal: GoalSpec;                    // abstrakcyjny, bez Git/Docker
  readonly riskLevel: RiskLevel;              // enum, patrz 4.5
}
export interface ExecutionPlan {
  readonly steps: ReadonlyArray<PlannedStep>; // każdy z wymaganym Capability
  readonly requiredCapabilities: ReadonlySet<CapabilityId>;
}
```

### 4.2 ModelRouter
```typescript
export interface RouteDecision {
  readonly model: ModelRef;
  readonly rationale: string;
  readonly costEstimate: CostUnits;           // typowane, nie string
  readonly fallbackChain: ReadonlyArray<ModelRef>;
}
// Router NIE wykonuje — zwraca decyzję jako czystą funkcję kontekstu.
```

### 4.3 QualityTribunal (PURE, stateless — INV-5)
```typesc