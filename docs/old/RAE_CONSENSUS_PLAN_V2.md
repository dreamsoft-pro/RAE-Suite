<!-- Plan po Konsensusie 5 AI z uwzględnieniem mandatu RAE-Core Lightweight (Mobile/Windows/Mesh) oraz Autonomicznej Egzekucji AI -->

# Szczegółowy Iteracyjny Plan Rozwoju RAE-Suite (Wersja v2.1 - Lightweight Core & AI Autonomous Execution)

**Data zatwierdzenia:** 2026-07-31  
**Kontekst:** Na podstawie analizy `docs/rozwoj-RAE-part-1.md`, `docs/rozwoj-RAE-part-2.md`, 5-etapowego cyklu audytowego OpenRouter (Luna Pro, DeepSeek R1, Opus 4.8, Sol 5.6, Fable 5 / Opus 5) oraz **krytycznych wytycznych architektonicznych**:
1. **Brak harmonogramów kalendarzowych:** Zadania są realizowane sekwencyjnie i bezinterwencyjnie przez autonomiczne agenty AI (AI-Agent Autonomous Sequence).
2. **Mandat RAE-Core Lightweight:** Rdzeń RAE musi pozostać ultraminimalny, lekki, szybki w uruchamianiu i uniwersalny — gotowy do działania w trybach **Mobile (iOS/Android/Edge)**, **Windows Desktop/Laptop** oraz **Mesh (Distributed Peer-to-Peer Cluster Nodes)**.

---

## 0. Mandat Architektoniczny: RAE-Core Lightweight & Agnostic Runtime

```text
CORE-1  Zero Heavy Bloat: RAE-Core NIE MOŻE zawierać ciężkich bibliotek ML (np. sentence-transformers, torch, cuda) w pakiecie bazowym.
CORE-2  Universal Portability: Kod rdzenia musi uruchamiać się bez zmian w środowiskach Mobile (Termux/iOS edge), Windows (Native/WSL2) i Linux Mesh.
CORE-3  Remote / Cluster Offloading: Ciężka inferencja LLM, wektoryzacja i ewaluacja RAE-Lab są oddelegowywane przez api (LiteLLM, OpenRouter) lub węzły klastra (KUBUS, PIOTREK).
CORE-4  Minimal Memory Footprint: Zużycie RAM rdzenia w trybie bezczynności < 50MB, czas startu procesów < 500ms.
```

---

## 1. Podsumowanie Wyników Konsensusu i Rekomendacje

### 1.1 Diagnoza Stanu Bazowego
- RAE-Suite posiada solidną strukturę modułową (Memory, Phoenix, Hive, Quality, Lab, MAES event store, Git worktree isolation), ale cierpi na **niedostateczną głębię semantyki wykonania**:
  - `CognitivePlanner` używa statycznych heurystyk tekstowych zamiast grafu zależności repozytorium (AST, testy, wykonanie).
  - `ModelRouter` posiada bogaty DTO, ale używa sztywnych reguł klas ryzyka i ignoruje tokeny, opóźnienia i metryki z RAE-Lab.
  - Ścieżki wykonania potrafią zwrócić `SUCCESS` bez rzeczywistego wykonania operacji i dowodu z testów.
  - Limity `CapabilityContract` są deklaratywne zamiast być twardo egzekwowane w runtime.

---

## 2. Zidentyfikowane Kluczowe Ryzyka i Zakres Poprawek (Fazy P0 - P3)

### 🔴 Faza P0 — Fundament Runtime, Twarde Kontrakty i Dowody Execucji
1. **Zero Fake Success Guarantee:** Domyślny stan `SUCCESS` musi zostać zastąpiony obowiązkowym dowodem wykonania `ExecutionReceipt` (hash diffu Git, kod wyjścia testów, suma SHA-256 artefaktów).
2. **Twarde Egzekwowanie Limitów (Hard Capability Enforcement):** `ToolGateway` odrzuca operacje naruszające limity CPU, RAM, czasu wykonania i klasy ryzyka przed ich uruchomieniem (`Admission Control`).
3. **Estymacja Wydajnościowa Routera:** Samo `costEstimate` jest niewystarczające. `ModelRouter` wylicza rozkłady kwantyli (`p50/p95/p99`) dla opóźnienia i tokenów oraz rezerwuje budżet atomowo.

### 🟠 Faza P1 — Silniki Planowania, Routingu i Eskalacji AI
1. **CognitivePlanner oparty na Grafie:** Generowanie hipotez w ToT/MCTS zasilane grafem zależności AST, mapą pokrycia testowego i wywołaniami w piaskownicy dry-run.
2. **Eskalacja Dwuścieżkowa (OpenCode + Hermes):** Automatyczna eskalacja po przekroczeniu budżetu naprawy do dedykowanych silników kodowych.
3. **Idempotencja i At-Least-Once Pub/Sub:** Klucz idempotencji `SHA-256(tenant_id + project_id + trace_id + step_id + action + input_hash)` dla wszystkich mutujących operacji.

### 🟡 Faza P2 — Jakość, Samonaprawa i Dynamiczne Ryzyko
1. **Precyzyjna Pętla Phoenix:** Przekazywanie ustrukturyzowanych raportów błędów (`QualityGateReport` z AST diff i linter traces) do pętli samonaprawy.
2. **Dynamiczna Klasyfikacja Ryzyka:** Wyliczanie klasy ryzyka na podstawie skanu diffu Git, dotkniętych modułów i zestawu narzędzi.

### 🔵 Faza P3 — Trwałość Event Store, ISO i Integracja Mesh/Mobile
1. **Niezmienność Dowodów (SHA-256 Hash Chaining):** Tworzenie kryptograficznego łańcucha dowodów w `ExecutionReceipt` dla zgodności z normami ISO 27001 (bezpieczeństwo danych) oraz ISO 42001 (governance AI).
2. **Lekki EventStore dla Mobile/Windows/Mesh:** Projekcje CQRS w MAES EventStore zoptymalizowane pod kątem niskiego zużycia zasobów.
3. **Kontrolowane Eksperymenty RAE-Lab:** Automatyczna kalibracja wag routingu i cache na podstawie historycznych wyników benchmarków klastrowych.

---

## 3. Invarianty Architektoniczne RAE-Suite

```text
INV-1  Zero Fake Success: Zakończenie zadania wymaga trwałego ExecutionReceipt z przechodzącymi testami.
INV-2  Hard Capability Limits: Brak możliwości wykonania akcji przekraczającej CapabilityContract.
INV-3  Bounded Work & Memory: Wszystkie kolejki, cache, pętle retry i budżety posiadają twarde limity.
INV-4  Idempotent Mutations: Wszystkie operacje mutujące posiadają klucz idempotencji SHA-256.
INV-5  Chain-of-Evidence (ISO 42001/27001): Każdy ExecutionReceipt jest powiązany hashem z poprzednim zdarzeniem.
INV-6  Evidence-Based Phoenix Repair: Pętla samonaprawy Phoenix wymaga raportu AST/linter/test z Quality Gate.
INV-7  Lightweight Core First: Kod rdzenia RAE zachowuje pełną funkcjonalność bez lokalnych ciężkich modeli ML.
```

---

## 4. Specyfikacja Kontraktów i Typów (TypeScript Branded Types)

### 4.1 ExecutionReceipt (Dowód Wykonania)
```typescript
export type Brand<K, T> = K & { readonly __brand: T };

export type ReceiptId     = Brand<string, 'ReceiptId'>;
export type TaskId        = Brand<string, 'TaskId'>;
export type StepId        = Brand<string, 'StepId'>;
export type GitHash       = Brand<string, 'GitHash'>;
export type Sha256Hash    = Brand<string, 'Sha256Hash'>;
export type ArtifactUri   = Brand<string, 'ArtifactUri'>;

export interface TestExecutionResult {
  readonly command: string;
  readonly exitCode: number;
  readonly passedCount: number;
  readonly failedCount: number;
  readonly durationMs: number;
  readonly coveragePercentage?: number;
}

export interface ExecutionReceipt {
  readonly receiptId: ReceiptId;
  readonly taskId: TaskId;
  readonly stepId: StepId;
  readonly previousReceiptHash: Sha256Hash;
  readonly executionStatus: 'VERIFIED_SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED';
  readonly gitDiffHash: GitHash;
  readonly testResult: TestExecutionResult;
  readonly artifactUris: ReadonlyArray<ArtifactUri>;
  readonly capabilityCompliance: boolean;
  readonly isoAuditMetadata: {
    readonly iso42001PolicyId: string;
    readonly dataClassification: 'PUBLIC' | 'CONFIDENTIAL' | 'RESTRICTED';
  };
  readonly timestamp: string;
}
```

### 4.2 ModelRouter — Kontrakt Wydajnościowy
```typescript
export type Milliseconds   = Brand<number, 'Milliseconds'>;
export type TokenCount     = Brand<number, 'TokenCount'>;
export type CostUnits      = Brand<number, 'CostUnits'>;
export type Probability    = Brand<number, 'Probability'>;

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
}

export interface RouteDecision {
  readonly selectedModel: string;
  readonly fallbackModel: string;
  readonly budgetReservationId: string;
  readonly policyVersion: string;
  readonly rationale: string;
}
```

---

## 5. Quality Tribunal & Phoenix Auto-Repair Protocol

### 5.1 Panel Sędziowski (Multi-Model Consensus)
1. **Skład:** GPT-5.6, DeepSeek R1, Claude Opus, Claude Sonnet.
2. **Progi Akceptacji:**
   - Zadania `LOW/MEDIUM` risk: Min. 2/3 głosów akceptujących.
   - Zadania `HIGH/RESTRICTED` risk: Jednomyślność (3/3 lub 4/4) + 0 naruszeń bezpieczeństwa.
3. **Anulowanie Głosów:** Wymuszone unieważnienie głosu w przypadku wykrycia halucynacji (nieistniejące symbole w AST).

### 5.2 Phoenix Auto-Repair Workflow
1. Przejęcie raportu `QualityGateReport` z nieważnego wykonania.
2. Wygenerowanie ukierunkowanego patcha naprawczego.
3. Maksymalnie 3 pętle naprawy (`max_repair_cycles = 3`).
4. W przypadku niepowodzenia — automatyczna eskalacja dwuścieżkowa do OpenCode / Hermesa.

---

## 6. Autonomiczny Sekwencyjny Plan Wykonania Agentowego (AI Agent Execution Sequence)

Wdrożenie realizowane jest bezpośrednio przez zinstancjonowane agenty AI w układzie pętli autonomicznej (bez sztywnych ram kalendarzowych):

1. **Agent Batch 1 (P0):** Implementacja `ExecutionReceipt`, `CapabilityContract Hard Enforcement`, `Chain-of-Evidence` (SHA-256).
2. **Agent Batch 2 (P1):** Graph-based `CognitivePlanner`, Dynamic `ModelRouter` z kwantylami opóźnień, Eskalacja OpenCode + Hermes.
3. **Agent Batch 3 (P2):** Multi-Model `Quality Tribunal`, Phoenix Auto-Repair z AST feedback, Dynamic Risk Scanner.
4. **Agent Batch 4 (P3):** Event Sourcing & CQRS Projections w MAES EventStore dla trybów Mesh/Mobile/Windows, RAE-Lab Guardrails.

### Kluczowe Metryki Sukcesu (SLO):
1. **100% Zero Fake Success:** 0 stanów `SUCCESS` bez fizycznie potwierdzonego `ExecutionReceipt`.
2. **0 Capability Violations:** 0 przekroczeń limitów pamięci, CPU lub uprawnień narzędziowych w `ToolGateway`.
3. **25% Reduction in LLM Costs:** Obniżenie kosztów wywołań LLM przy zachowaniu wskaźnika jakości >= 0.90.
4. **100% ISO Auditability:** Pełna spójność łańcucha kryptograficznego SHA-256 dla wszystkich zdarzeń decyzyjnych.
5. **Mobile/Windows/Mesh Readiness:** 100% testów przechodzących w środowiskach z ograniczeniami pamięciowymi (<50MB footprint).