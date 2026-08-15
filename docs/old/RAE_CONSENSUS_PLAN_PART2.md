<!-- Plan Część 2 po Konsensusie 5 AI (Luna Pro, DeepSeek R1, Opus 4.8, Sol 5.6, Fable 5 / Opus 5) -->

# Szczegółowy Iteracyjny Plan Rozwoju RAE-Suite Część 2 (Wersja v2.1 - Flow & Auditable Autonomy)

**Data zatwierdzenia:** 2026-07-31  
**Kontekst:** Na podstawie analizy `docs/rozwoj-RAE-part-2.md`, opracowania `Linkedin_Posts_2024_Blue.pdf` oraz 5-etapowego cyklu audytowego OpenRouter:
1. **GPT-5.6 Luna Pro** (`openai/gpt-5.6-luna-pro`) — Audyt Logiki Domenowej (Event Sourcing, CQRS & Saga)
2. **DeepSeek R1** (`deepseek/deepseek-r1`) — Audyt Runtime i Współbieżności (Redis Streams, DLQ & Semantic Watchdog)
3. **Claude Opus 4.8** (`anthropic/claude-opus-4.8`) — Audyt Architektury i Typowania (`ArtifactRef`, Control Plane & Safe Replay)
4. **GPT-5.6 Sol** (`openai/gpt-5.6-sol`) — Audyt Wydajności (Cache-Aside Singleflight, Outbox & Latency)
5. **Fable 5 / Opus 5** (`anthropic/claude-opus-5`) — Audyt Audytowalnej Autonomii i Niezawodności ISO 27001/42001

---

## 1. Diagnoza Architektoniczna i Dyrektywy Płynnego Przepływu (Smooth Flow)

### 1.1 Stan Obiektu i Główny Problem
RAE-Suite posiada zaawansowane moduły (Memory, Phoenix, Hive, Quality, Lab, MAES, Worktree Isolation), lecz aktualny przepływ cierpi na **brak jednolitego kręgosłupa trwałego wykonania**:
1. **Brak Centralnego Store'a Zdarzeń:** Zdarzenia MAES są fragmentaryczne; brak trwałego `EventStore` z transactional outbox.
2. **Ryzyko Podwójnego Wykonania:** Brak trwałej rejestracji `idempotency_key` na poziomie `ToolGateway` i API Gateway.
3. **Niebezpieczny Replay:** Komenda `rae replay` potrafiła uruchamiać ponownie skutki uboczne.
4. **Pętle Bez Postępu (Semantic Loops):** Brak silnika `SemanticWatchdog` przerywającego bezowocne pętle samonaprawy Phoenix.
5. **Ciężkie Payloady w Kolejkach:** Przesyłanie dużych kontekstów i patchy bezpośrednio w wiadomościach zamiast wzorca `Claim Check` (`ArtifactRef`).

---

## 2. Zidentyfikowane Kluczowe Ryzyka i Zakres Poprawek (Fazy Etap 0 - Etap 3)

### 🔴 Faza Etap 0 — Ujednolicenie Źródła Prawdy i Manifestów
- Ujednolicenie wersji kontraktów i manifestów funkcjonalnych (`IMPLEMENTED`, `PROTOTYPE`, `SPECIFICATION`).
- Usunięcie symulowanych metryk ze ścieżki produkcyjnej.

### 🟠 Faza Etap 1 — Durable Execution & Transactional Outbox
- **MAES EventStore:** Centralne, trwałe źródło prawdy dla zdarzeń domenowych.
- **Transactional Outbox & Command Store:** Zapis stanu agregatu i wiadomości Outbox w jednej transakcji DB.
- **Claim Check (`ArtifactRef`):** Odciążenie wiadomości kolejkowych; przesyłanie odwołań URI + SHA-256.
- **Bezpieczny Replay Audytowy:** Tryb `rae replay TRACE` pozbawiony skutków ubocznych.

### 🟡 Faza Etap 2 — Redis Streams & Saga Coordinator
- **Redis Streams & Consumer Groups:** Asynchroniczne przetwarzanie `HTTP 202 Accepted` z priorytetyzacją.
- **Saga Coordinator:** Trwałe wywoływanie `execute()` oraz kompensacji `compensate()` po niepowodzeniach.
- **Exponential Backoff + Full Jitter & DLQ:** Ograniczenie ponowień do błędów przejściowych.

### 🔵 Faza Etap 3 — Podwójny Circuit Breaker & Utwardzony Cache
- **Transport Circuit Breaker:** Ochrona providerów LLM, Qdrant i Redis (`CLOSED` -> `OPEN` -> `HALF_OPEN`).
- **Semantic Watchdog:** Przerywanie pętli samonaprawy na podstawie badania podobieństwa wektorowego.
- **Cache-Aside Security:** Wdrożenie `singleflight` (request coalescing), TTL jitter i negative caching.

---

## 3. Specyfikacja Kontraktów i DTO (TypeScript Branded Types)

### 3.1 DTO ArtifactRef (Claim Check)
```typescript
export declare const __brand: unique symbol;
export type Brand<T, B extends string> = T & { readonly [__brand]: B };

export type ArtifactId = Brand<string, 'ArtifactId'>;
export type ContentHash = Brand<string, 'ContentHash'>;

export interface ArtifactRef {
  readonly kind: 'artifact-ref';
  readonly artifactId: ArtifactId;
  readonly uri: string;
  readonly contentHash: ContentHash;
  readonly sizeBytes: number;
  readonly mediaType: string;
  readonly redactionStatus: 'NOT_SCANNED' | 'SCANNED_SAFE' | 'REDACTED';
  readonly retentionPolicy: string;
}
```

### 3.2 Saga Step Contract
```typescript
export interface SagaStep<T> {
  readonly stepId: string;
  readonly action: string;
  readonly execute: (payload: T) => Promise<StepResult>;
  readonly compensate: (payload: T) => Promise<CompensateResult>;
  readonly timeoutMs: number;
  readonly idempotencyKey: string;
}
```

---

## 4. Audytowalna Autonomia i Zgodność ISO 27001 / ISO 42001

1. **SHA-256 Hash Chaining:** Kryptograficzny łańcuch dowodów w `MAES EventStore`.
2. **ISO 27001 Data Protection:** Odpowiednia klasyfikacja danych (`PUBLIC`, `CONFIDENTIAL`, `RESTRICTED`) z automatyczną redakcją sekretów przed zapisem.
3. **Docker Execution Proxy:** Ochrona gniazda `/var/run/docker.sock` przy użyciu proxy z twardą allowlistą komend.
4. **SLO Audytowalnej Autonomii:** 100% spójność odtwarzania śladów i 0 niekontrolowanych wywołań w trybie replay.