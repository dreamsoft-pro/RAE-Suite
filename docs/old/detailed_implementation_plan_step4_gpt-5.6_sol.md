<!-- Plan po Kroku 4: GPT-5.6 Sol (openai/gpt-5.6-sol) -->

# Audyt Performance & Resource — RAE-Suite v1.2

## 1. Zwięzła recenzja

Plan v1.2 poprawia kontrakty i separację modułów, ale nie definiuje jeszcze **ilościowych granic wydajnościowych**. Największe ryzyka to:

1. `ModelRouter` nie uwzględnia niepewności estymacji tokenów, opóźnień ogonowych ani rezerwacji budżetu.
2. Brakuje kontraktów backpressure, fairness i przeciążenia dla pub/sub.
3. Cache semantyczny nie ma polityki izolacji tenantów, walidacji trafień ani kontroli kosztu embeddingów.
4. Pamięć operacyjna nie ma limitów bajtowych, admission control ani polityki degradacji.
5. Weryfikacja testów i zapis `ExecutionReceipt` mogą stać się dominującym kosztem ścieżki krytycznej.
6. Brakuje benchmarków bazowych, SLO oraz metodyki eksperymentów RAE-Lab.
7. Plan zawiera również niekompletne fragmenty (`typesc`, `[ADDRESS]`, `[PERSON_NAME]`), które muszą zostać usunięte przed uznaniem kontraktów za kompilowalne.

---

# 2. Luki i rekomendacje

## 🔴 P0 — Krytyczne ryzyka wydajnościowe

### P0.1. Router optymalizuje estymatę punktową zamiast ryzyka

Samo `costEstimate` jest niewystarczające. `expected_tokens` i latency mają rozkłady z ciężkim ogonem, a nie jedną wartość. Router może wybrać model tani średnio, ale regularnie przekraczający deadline lub budżet.

**Rekomendacje:**

- estymować osobno:
  - tokeny wejściowe,
  - tokeny wyjściowe,
  - koszt,
  - `p50/p95/p99` latency,
  - prawdopodobieństwo powodzenia bez repair cycle;
- podejmować decyzję na podstawie ograniczeń:
  - `P(cost <= budget)`,
  - `P(latency <= deadline)`,
  - minimalnego wymaganego quality score;
- stosować rezerwację budżetu przed dispatch i rozliczenie po wykonaniu;
- kalibrować estymatory online według modelu, regionu, klasy zadania i długości kontekstu;
- przechowywać wersję polityki routingu w `ExecutionReceipt`.

### P0.2. Brak admission control i backpressure

Limit zasobów pojedynczego workera nie chroni całego systemu przed przeciążeniem. Bez kontroli napływu kolejki będą rosły aż do przekroczenia deadline’ów i presji pamięciowej.

**Rekomendacje:**

- ograniczyć liczbę zadań `queued + in-flight` per tenant i per capability;
- użyć bounded queues;
- wprowadzić jawne wyniki `Accepted | Deferred | Rejected`;
- stosować weighted fair queuing zamiast czystego FIFO;
- odrzucać lub opóźniać zadania, których deadline jest już nierealny;
- retry z jitterem i limitem retry budget;
- DLQ tylko dla diagnostyki, nie jako nieskończona kolejka ponowień.

### P0.3. `ExecutionReceipt` może blokować ścieżkę krytyczną

Jeżeli każdy test, log i artefakt generuje synchroniczny zapis do bazy, koszt I/O oraz contention szybko zdominują czas wykonania.

**Rekomendacje:**

- synchronicznie zapisywać jedynie minimalny, trwały `ReceiptCommit`;
- duże logi i artefakty zapisywać w object storage;
- w receipt przechowywać referencje i hashe;
- grupować zdarzenia w append-only batches;
- stosować hash-chain lub Merkle root do wykrywania modyfikacji;
- asynchronicznie wykonywać enrichment, kompresję i indeksowanie;
- nie uznawać zadania za zakończone, dopóki minimalny receipt nie jest trwały.

### P0.4. Brak rozróżnienia testów obowiązkowych i adaptacyjnych

Uruchamianie pełnego zestawu testów po każdym repair cycle może prowadzić do multiplikacji kosztu:

`liczba cykli × pełny test suite × zapis dowodów`.

**Rekomendacje:**

- obowiązkowe testy compliance/security zawsze wykonywać w pełni;
- pozostałe testy wybierać przez impact analysis;
- po lokalnej naprawie uruchamiać najpierw testy dotknięte zmianą;
- pełny gate uruchamiać przed finalnym verdict;
- cache’ować tylko wyniki deterministyczne, związane z hashem wejścia, środowiska i toolchainu.

---

## 🟠 P1 — Routing, kolejki i cache

### P1.1. Brak jawnej funkcji celu routera

`rationale: string` jest audytowalne dla człowieka, lecz nie wystarcza do reprodukcji decyzji.

**Rekomendacja:** zapisywać ustrukturyzowany score:

```text
utility =
  quality_weight * expected_quality
  - cost_weight * expected_cost
  - latency_weight * deadline_risk
  - failure_weight * retry_risk
```

Wagi i ograniczenia muszą być wersjonowane.

### P1.2. Fallback może zwielokrotnić koszt

Statyczny `fallbackChain` może uruchamiać droższe modele po błędach, które nie są naprawialne przez zmianę modelu.

**Rekomendacje:**

- fallback wyłącznie dla typowanych klas błędów;
- wspólny budget envelope dla wszystkich prób;
- maksymalna liczba route attempts;
- brak hedgingu dla operacji z efektami ubocznymi;
- hedged requests tylko dla bezpiecznych, idempotentnych wywołań i po przekroczeniu adaptacyjnego progu latency.

### P1.3. Brak kontraktu dostarczenia pub/sub

Plan powinien jawnie przyjąć semantykę, np. **at-least-once + idempotent consumer**. Exactly-once na poziomie całego systemu byłoby kosztowne i zwykle pozorne.

**Rekomendacje:**

- transactional outbox dla publikacji powiązanych ze zmianą stanu;
- inbox/deduplication po `MessageId`;
- partycjonowanie po `tenant/task`, jeśli wymagana jest kolejność;
- brak globalnego porządku;
- TTL dla deduplikacji;
- ack dopiero po trwałym commit wymaganej zmiany.

### P1.4. Cache semantyczny bez granic bezpieczeństwa

Podobieństwo embeddingów nie jest dowodem równoważności. Trafienie może być niepoprawne lub ujawnić dane między tenantami.

**Rekomendacje:**

Klucz logiczny cache powinien obejmować co najmniej:

- tenant lub jawnie zatwierdzoną domenę współdzielenia,
- wersję modelu i prompt template,
- wersję polityki,
- capability/security scope,
- hash narzędzi i środowiska,
- klasę danych,
- normalized input.

Stosować:

- prefiltry metadanych przed wyszukiwaniem wektorowym;
- minimalny próg podobieństwa kalibrowany per workload;
- tani walidator trafienia;
- TTL i invalidację po zmianie polityki/modelu;
- negative caching tylko dla krótkotrwałych, bezpiecznych błędów;
- limit kosztu embeddingów i minimalny oczekiwany reuse.

### P1.5. Brak ochrony przed cache stampede

**Rekomendacje:**

- request coalescing/single-flight;
- probabilistic early refresh;
- stale-while-revalidate tylko dla danych, których polityka na to pozwala;
- limit współbieżnych missów per klucz/model.

---

## 🟡 P2 — Pamięć operacyjna i testy

### P2.1. Limity tokenów nie są limitami pamięci

Ten sam kontekst może mieć różny koszt w pamięci procesu, KV cache lub transportach.

**Rekomendacje:**

- limity w bajtach i tokenach;
- budżety per tenant/task/worker;
- podział na:
  - `PINNED` — nieusuwalne dane aktywnego kroku,
  - `RECOMPUTABLE` — możliwe do odtworzenia,
  - `EVICTABLE` — cache,
  - `DURABLE_REF` — uchwyty do danych poza RAM;
- admission control przed alokacją;
- high/low watermarks;
- degradacja przez summarization lub offload, nie przez losowy OOM;
- zakaz automatycznego skracania dowodów compliance.

### P2.2. Brak polityki jakości summarization

Kompakcja pamięci może usunąć warunek istotny dla bezpieczeństwa.

**Rekomendacja:** każdy summary powinien zawierać:

- hash źródła,
- wersję summarizera,
- zakres objętych wiadomości,
- listę zachowanych invariantów,
- confidence oraz informację, czy wymagany jest powrót do źródła.

### P2.3. Cache testów może ukrywać regresje

Cache jest poprawny tylko wtedy, gdy klucz obejmuje wszystkie wejścia wpływające na wynik.

**Klucz testu powinien uwzględniać:**

- hash kodu i zależności,
- identyfikator testu,
- konfigurację,
- obraz wykonawczy,
- toolchain,
- architekturę,
- zmienne środowiskowe z allowlisty,
- seed,
- politykę sandboxa.

Testy flaky powinny być oznaczane i wyłączane z cache.

---

## 🔵 P3 — Obserwowalność i RAE-Lab

### P3.1. Brak SLO i performance budgets

Bez celów liczbowych nie można stwierdzić, czy optymalizacja jest poprawą.

Minimalny zestaw:

- end-to-end latency `p50/p95/p99`;
- queue wait time;
- model first-token i completion latency;
- deadline miss rate;
- koszt per successful task;
- token prediction error;
- cache hit rate oraz validated hit rate;
- test-selection ratio;
- receipt commit latency;
- memory high-water mark;
- retry amplification;
- fairness per tenant.

### P3.2. Eksperymenty RAE-Lab muszą być kontrolowane

RAE-Lab powinien porównywać polityki routingu i cache na tym samym, wersjonowanym workloadzie.

**Wymagania:**

- replay zanonimizowanych trace’ów;
- stały seed i wersja datasetu;
- warm-up przed pomiarem;
- osobne wyniki cold/warm cache;
- raport p50/p95/p99, kosztu i jakości;
- przedziały ufności;
- shadow mode przed aktywacją nowej polityki;
- canary per tenant/workload;
- automatyczny rollback po przekroczeniu guardrail.

---

# 3. Zaktualizowane sekcje planu — v1.3 Performance & Resource

## Sekcja 0A: Invarianty wydajnościowe

```text
PERF-1  Bounded Work: każda kolejka, retry loop, pula workerów i cache ma limit.
PERF-2  Admission Before Allocation: zasoby są rezerwowane przed dispatch.
PERF-3  Deadline-Aware Routing: router nie wybiera ścieżki, która z dużym
        prawdopodobieństwem przekroczy deadline.
PERF-4  Budget Conservation: fallbacki i repair cycles współdzielą jeden budżet.
PERF-5  Durable Minimal Receipt: zakończenie wymaga trwałego minimalnego dowodu,
        ale nie synchronicznego zapisu wszystkich artefaktów.
PERF-6  Tenant Isolation: kolejki, cache, pamięć i budżety są izolowane per tenant.
PERF-7  Evidence Preservation: optymalizacje nigdy nie usuwają wymaganych dowodów.
PERF-8  Measured Changes: zmiana polityki wymaga benchmarku RAE-Lab i guardrails.
```

---

## Sekcja 4.2: ModelRouter — kontrakt wydajnościowy

```typescript
type Milliseconds = Brand<number, 'Milliseconds'>;
type TokenCount   = Brand<number, 'TokenCount'>;
type CostUnits    = Brand<number, 'CostUnits'>;
type Probability  = Brand<number, 'Probability'>; // [0, 1]
type PolicyVersion = Brand<string, 'PolicyVersion'>;

export interface Quantiles<T> {
  readonly p50: T;
  readonly p95: T;
  readonly p99: T;
}

export interface RouteBudget {
  readonly maxCost: CostUnits;
  readonly maxInputTokens: TokenCount;
  readonly maxOutputTokens: TokenCount;
  readonly deadlineMs: Milliseconds;
  readonly maxAttempts: number;
  readonly reservedRepairCost: CostUnits;
}

export interface ModelEstimate {
  readonly inputTokens: Quantiles<TokenCount>;
  readonly outputTokens: Quantiles<TokenCount>;
  readonly latencyMs: Quantiles<Milliseconds>;
  readonly expectedCost: CostUnits;
  readonly successProbability: Probability;
  readonly qualityProbability: Probability;
  readonly calibrationVersion: PolicyVersion;
}

export interface RouteCandidate {
  readonly model: ModelRef;
  readonly estimate: ModelEstimate;
  readonly feasible: boolean;
  readonly rejectionReasons: ReadonlyArray<
    | 'BUDGET_EXCEEDED'
    | 'DEADLINE_RISK'
    | 'QUALITY_TOO_LOW'
    | 'CAPABILITY_MISMATCH'
    | 'MODEL_UNAVAILABLE'
  >;
}

export interface RouteDecision {
  readonly selected: ModelRef;
  readonly candidates: ReadonlyArray<RouteCandidate>;
  readonly budgetReservation: BudgetReservation;
  readonly policyVersion: PolicyVersion;
  readonly fallbackRules: ReadonlyArray<FallbackRule>;
}

export interface FallbackRule {
  readonly on:
    | 'RATE_LIMITED'
    | 'TRANSIENT_PROVIDER_ERROR'
    | 'DEADLINE_RISK'
    | 'QUALITY_REJECTED';
  readonly model: ModelRef;
  readonly maxAdditionalCost: CostUnits;
}

export type RoutingResult =
  | { kind: 'ROUTED'; decision: RouteDecision }
  | { kind: 'NO_FEASIBLE_ROUTE'; reasons: ReadonlyArray<string> }
  | { kind: 'BUDGET_REJECTED'; required: CostUnits; available: CostUnits };
```

### Reguły routingu

1. Router filtruje kandydatów po capability, residency i policy.
2. Odrzuca kandydatów przekraczających budżet lub deadline guardrail.
3. Minimalizuje oczekiwany koszt przy zachowaniu minimalnej jakości.
4. Rezerwuje budżet atomowo przed dispatch.
5. Po wykonaniu rozlicza koszt rzeczywisty i aktualizuje kalibrację.
6. Nie wykonuje fallbacku dla błędów trwałych lub naruszeń capability.

---

## Sekcja 5: Pub/Sub, scheduling i backpressure

```typescript
type MessageId = Brand<string, 'MessageId'>;
type QueuePartition = Brand<string, 'QueuePartition'>;

export interface WorkEnvelope<T> {
  readonly messageId: MessageId;
  readonly tenant: TenantId;
  readonly task: TaskId;
  readonly payload: T;
  readonly partition: QueuePartition;
  readonly priority: 'INTERACTIVE' | 'NORMAL' | 'BATCH';
  readonly deadlineMs: Milliseconds;
  readonly attempt: AttemptNo;
  readonly idempotencyKey: IdempotencyKey;
}

export interface AdmissionLimits {
  readonly maxQueuedPerTenant: number;
  readonly maxInFlightPerTenant: number;
  readonly maxInFlightPerCapability: number;
  readonly maxQueueBytes: number;
  readonly maxRetryAmplification: number;
}

export type AdmissionDecision =
  | { kind: 'ACCEPTED'; reservation: ResourceReservation }
  | { kind: 'DEFERRED'; retryAfterMs: Milliseconds }
  | { kind: 'REJECTED'; reason: 'OVERLOADED' | 'DEADLINE_IMPOSSIBLE' | 'BUDGET' };

export interface RetryPolicy {
  readonly maxAttempts: number;
  readonly initialDelayMs: Milliseconds;
  readonly maxDelayMs: Milliseconds;
  readonly multiplier: number;
  readonly jitterRatio: number;
  readonly retryableErrors: ReadonlySet<RetryableErrorCode>;
}
```

### Semantyka wykonania

- Dostarczenie: `at-least-once`.
- Konsument: idempotentny.
- Publikacja zm