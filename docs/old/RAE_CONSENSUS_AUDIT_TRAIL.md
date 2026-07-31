# RAE-Suite OpenRouter Multi-Model Consensus Audit Trail
**Data wykonania:** 2026-07-31 06:44:33

## Krok 1: GPT-5.6 Luna Pro (openai/gpt-5.6-luna-pro)
**Rola:** Logic & Domain Model Audit  
**Czas:** 06:45:18  

### Wynik Audytu i Rekomendacje:

# Audyt logiki domenowej RAE-Suite

## 0. Zakres i ograniczenia audytu

Audyt opiera się wyłącznie na przedstawionej wersji planu. Nie można potwierdzić pełnej zgodności z `docs/rozwoj-RAE-part-1.md`, ponieważ treść tego dokumentu nie została dołączona, a część nazw w planie jest zastąpiona przez `[PERSON_NAME]` lub `[ADDRESS]`.

Wnioski poniżej wskazują:

- niespójności widoczne w aktualnym planie,
- brakujące pojęcia domenowe,
- niepełne przejścia maszyny stanów,
- niewystarczającą semantykę DTO,
- rekomendowaną wersję rozszerzoną planu.

---

# 1. Ocena ogólna

Plan poprawnie identyfikuje główne problemy:

- fałszywy `SUCCESS`,
- deklaratywne, a nie egzekwowane `CapabilityContract`,
- zbyt statyczny `ModelRouter`,
- niedojrzały `CognitivePlanner`,
- brak pełnej pętli: planowanie → wykonanie → dowód → walidacja → eskalacja,
- potrzebę event sourcingu i replay.

Jednocześnie obecny model jest jeszcze bardziej **listą komponentów i zadań implementacyjnych** niż spójnym modelem domenowym. Brakuje jednoznacznego rozdzielenia:

1. intencji wykonania,
2. planu wykonania,
3. autoryzacji,
4. fizycznego wykonania,
5. dowodu wykonania,
6. weryfikacji dowodu,
7. decyzji końcowej,
8. kompensacji lub eskalacji.

Najpoważniejszy problem polega na tym, że `ExecutionReceipt` jest traktowany jako artefakt techniczny, podczas gdy powinien być **niezmiennym dowodem domenowym**, na podstawie którego dopiero można nadać zadaniu stan `VERIFIED_SUCCESS`.

---

# 2. Lista dostrzeżonych luk i rekomendacji

## 2.1. Brak rozdzielenia stanu zadania od stanu wykonania

W planie występuje `SUCCESS`, ale nie ma jasności, czy oznacza on:

- zakończenie procesu agenta,
- zakończenie kroku,
- poprawne wykonanie narzędzia,
- przejście testów,
- zaakceptowanie wyniku przez Quality Gate,
- podpisanie i zweryfikowanie `ExecutionReceipt`.

Rekomendacja: rozdzielić co najmniej trzy poziomy:

```text
Task lifecycle
  CREATED → PLANNED → AUTHORIZED → EXECUTING → VERIFIED_SUCCESS

Step lifecycle
  PENDING → DISPATCHED → RUNNING → OBSERVED → VERIFIED / FAILED

Decision lifecycle
  PROPOSED → EVALUATED → ACCEPTED / REJECTED / ESCALATED
```

Nie należy używać jednego `SUCCESS` dla wszystkich tych znaczeń.

---

## 2.2. `SUCCESS` nie może być nadawany na podstawie samego exit code

`exit_code = 0` nie dowodzi, że:

- wykonano właściwe polecenie,
- wykonano je w odpowiednim workspace,
- testy objęły oczekiwany zakres,
- artefakty pochodzą z tego samego wykonania,
- nie przekroczono uprawnień lub zasobów,
- diff odpowiada badanemu commitowi,
- wynik jest aktualny względem wersji repozytorium.

Rekomendacja: uznać `exit_code` za jeden z faktów obserwacyjnych, a nie za warunek wystarczający.

Minimalna reguła:

```text
VERIFIED_SUCCESS =
  execution completed
  AND command provenance is valid
  AND workspace/base revision is valid
  AND capability policy was enforced
  AND required checks passed
  AND artifacts are content-addressed
  AND receipt signature/hash is valid
  AND Quality Gate accepted the result
```

---

## 2.3. `ExecutionReceipt` nie zawiera pełnej semantyki dowodu

Obecne DTO jest dobrym szkicem, ale nie wystarcza do audytowalnego wykonania.

Brakuje między innymi:

- wersji bazowej repozytorium,
- commit hash i workspace identity,
- canonical hash polecenia oraz parametrów,
- identyfikatora wykonawcy/runtime,
- wersji obrazu kontenera lub środowiska,
- faktycznych limitów i faktycznego zużycia zasobów,
- zakresu testów i ich kompletności,
- listy artefaktów z hashami, rozmiarami i typami,
- informacji o cache,
- informacji o retry,
- resultu Quality Gate,
- naruszeń polityki,
- podpisu lub mechanizmu integralności,
- czasu rozpoczęcia i zakończenia,
- przyczyny niepowodzenia,
- korelacji z eventami i trace.

Dodatkowo `git_diff_hash` jest niejednoznaczny. Należy określić, czy hash dotyczy:

- patcha względem `base_commit`,
- drzewa plików,
- finalnego commita,
- listy zmienionych plików,
- kanonicznego serializowanego diffu.

Rekomendacja: hash powinien być obliczany nad jednoznacznie zdefiniowaną reprezentacją kanoniczną.

---

## 2.4. `capability_compliance: true` jest zbyt słabym polem

Boolean nie pozwala ustalić:

- jakie ograniczenia obowiązywały,
- które operacje podlegały kontroli,
- czy kontrola była pre- czy post-execution,
- jakie były limity,
- jakie było faktyczne zużycie,
- czy wystąpiło naruszenie,
- czy ograniczenie zostało wymuszone przez sandbox,
- czy wynik jest wiarygodny mimo naruszenia.

Rekomendacja: zastąpić boolean strukturą:

```json
{
  "policy_id": "cap-policy-v3",
  "contract_version": "openclaw-2.1",
  "required_capabilities": ["repo.read", "repo.write", "test.execute"],
  "granted_capabilities": ["repo.read", "repo.write", "test.execute"],
  "enforcement_mode": "HARD",
  "limit_observations": [],
  "compliance_status": "COMPLIANT"
}
```

---

## 2.5. Brak rozróżnienia `FAILED`, `BLOCKED`, `REJECTED`, `CANCELLED` i `ABORTED`

Są to różne sytuacje domenowe:

- `FAILED` — wykonanie wystartowało, ale zakończyło się błędem,
- `BLOCKED` — wykonanie nie mogło wystartować z powodu polityki, braku uprawnień lub zasobów,
- `REJECTED` — plan lub wynik został odrzucony przez politykę albo Quality Gate,
- `CANCELLED` — użytkownik/system anulował zadanie,
- `ABORTED` — wykonanie przerwano awaryjnie,
- `EXPIRED` — przekroczono deadline lub TTL,
- `PARTIALLY_COMPLETED` — część planu została wykonana, ale całość nie została potwierdzona.

Bez tych stanów system będzie zmuszony kodować różne znaczenia w jednym `FAILED`.

---

## 2.6. Brak stanów oczekiwania

W systemie agentowym wykonanie często nie kończy się od razu. Potrzebne są stany:

- `WAITING_FOR_APPROVAL`,
- `WAITING_FOR_RESOURCE`,
- `WAITING_FOR_DEPENDENCY`,
- `WAITING_FOR_TOOL`,
- `WAITING_FOR_HUMAN`,
- `PAUSED`.

Bez nich retry i wznowienie będą mylone z ponownym uruchomieniem.

---

## 2.7. Ryzyko jest klasyfikowane zbyt statycznie

Plan słusznie przewiduje dynamiczną klasyfikację ryzyka, ale umieszcza ją dopiero w P2. To zbyt późno.

Ryzyko jest potrzebne już przed:

- wyborem modelu,
- autoryzacją planu,
- przyznaniem capability,
- uruchomieniem narzędzia,
- zatwierdzeniem automatycznej naprawy.

Ponadto ryzyko nie powinno być tylko wartością `LOW/MEDIUM/HIGH`. Potrzebne są:

- wynik ryzyka,
- klasyfikacja,
- powody,
- wersja polityki,
- źródła danych,
- confidence,
- zakres obowiązywania,
- moment ponownej oceny.

Ryzyko powinno być monotonicznie podwyższane, gdy plan zyskuje nowe skutki uboczne, ale jego obniżenie powinno wymagać jawnej rekalkulacji i nowej autoryzacji.

---

## 2.8. Brak rozróżnienia ryzyka planu, kroku i operacji

Przykład:

- całe zadanie: `MEDIUM`,
- krok modyfikujący konfigurację produkcyjną: `CRITICAL`,
- polecenie `git diff`: `LOW`.

Jedna klasyfikacja na poziomie zadania jest niewystarczająca.

Rekomendacja:

```text
task risk
plan risk
step risk
tool operation risk
residual risk after controls
```

Efektywne ryzyko wykonania powinno być co najmniej:

```text
effective_risk =
  max(task_risk, plan_risk, step_risk, operation_risk)
```

z możliwością podwyższenia przez reguły typu „always critical”.

---

## 2.9. Model routingu nie opisuje pełnej decyzji

`ModelRoutingDecision` zawiera wybrany model, fallback i koszt, ale nie zapisuje, dlaczego inne modele zostały odrzucone oraz jakie ograniczenia obowiązywały.

Brakuje:

- listy kandydatów,
- wyników kandydatów,
- funkcji scoringowej i jej wersji,
- confidence,
- wymaganych narzędzi,
- ograniczeń bezpieczeństwa i prywatności,
- lokalizacji danych,
- wymaganej latencji,
- budżetu całkowitego,
- maksymalnej liczby retry,
- reguły fallbacku,
- powodów odrzucenia,
- wersji metryk z RAE-Lab,
- faktycznego modelu użytego po wykonaniu,
- informacji o zmianie routingu w trakcie zadania.

Należy odróżnić:

```text
RoutingDecision — decyzja przed wywołaniem modelu
ModelInvocationReceipt — dowód faktycznego wywołania
```

Wybrany model może nie być modelem faktycznie użytym, np. wskutek timeoutu, fallbacku lub awarii dostawcy.

---

## 2.10. Brak budżetu i polityki kosztowej jako obiektu domenowego

`estimated_cost_usd` nie wystarcza. System potrzebuje:

- budget per task,
- budget per step,
- budget per tenant/project,
- budget for retries,
- budget for escalation,
- actual cost,
- reservation,
- refund/unused budget,
- policy on exceeding budget.

W przeciwnym razie router może podjąć lokalnie poprawną decyzję, która przekroczy globalny budżet zadania.

---

## 2.11. Capability Contract nie jest jeszcze kontraktem egzekwowalnym

Samo egzekwowanie limitów w `ToolGateway` nie rozwiązuje całego problemu. Trzeba zdefiniować:

- kto nadaje capability,
- na jaki czas,
- dla jakiego taska, stepu i workspace,
- czy capability można delegować,
- czy jest revocable,
- jakie są warunki użycia,
- jak wygląda odmowa,
- jak zapisuje się dowód odmowy,
- czy narzędzia są transakcyjne lub kompensowalne.

Capability powinno być związane z konkretnym kontekstem:

```text
tenant_id
project_id
task_id
plan_id
step_id
workspace_id
principal_id
policy_version
expiry
```

---

## 2.12. Brak ochrony przed TOCTOU

Jeżeli plan i autoryzacja są tworzone w jednym stanie repozytorium, a wykonanie odbywa się później, repozytorium lub polityka mogą się zmienić.

Należy sprawdzać przed wykonaniem:

- czy `base_commit` nadal obowiązuje,
- czy plan nie został zmodyfikowany,
- czy capability nadal jest ważne,
- czy polityka nie zmieniła wersji,
- czy ryzyko nie wzrosło,
- czy workspace nie został zmieniony przez inny proces.

---

## 2.13. Brak idempotencji na poziomie operacji

Klucz P3:

```text
tenant_id + project_id + trace_id + step_id + action + input_hash
```

jest dobrym kierunkiem, ale prawdopodobnie niewystarczającym.

Należy uwzględnić co najmniej:

- `workspace_id`,
- `tool_version`,
- `policy_version`,
- `base_revision`,
- `attempt_no`,
- `idempotency_key`,
- typ operacji,
- semantykę efektu ubocznego.

Idempotencja odczytu jest prostsza niż idempotencja zapisu. Dla operacji nieodwracalnych wymagany jest mechanizm:

- deduplikacji,
- lease,
- fencing token,
- kompensacji,
- albo jawnego `non_idempotent=true`.

---

## 2.14. Brak modelu kompensacji

Jeżeli plan wykonuje kilka operacji i krok 4 kończy się błędem, system musi wiedzieć:

- czy cofnąć kroki 1–3,
- czy pozostawić częściowy rezultat,
- czy utworzyć rollback plan,
- czy wymagać akceptacji człowieka,
- czy rollback sam wymaga nowej autoryzacji.

Wymagany jest model `CompensationPlan` lub przynajmniej relacja:

```text
ExecutionStep → compensating_step
```

---

## 2.15. Quality Gate i Quality Tribunal nie mają jasno zdefiniowanego autorytetu

Nie jest określone:

- czy Tribunal może nadać `VERIFIED_SUCCESS`,
- czy tylko rekomenduje decyzję,
- czy są testy obowiązkowe niezależnie od głosowania,
- jak traktowane są sprzeczne wyniki,
- czy jeden model może zawetować wynik,
- jaki jest próg quorum,
- co dzieje się przy braku quorum,
- czy Tribunal może zaakceptować wynik z ostrzeżeniami,
- jak kalibrowane są wagi modeli.

Rekomendacja: Tribunal powinien być **dowodem walidacyjnym**, ale nie powinien omijać twardych invariantów wykonania. Żaden consensus LLM nie może zastąpić nieudanego testu obowiązkowego ani naruszenia capability.

---

## 2.16. Phoenix Auto-Repair może tworzyć nieograniczoną pętlę

Brakuje:

- maksymalnej liczby iteracji,
- budżetu napraw,
- wzrostu ryzyka po każdej iteracji,
- warunku stagnacji,
- wykrywania regresji,
- odróżnienia nowego problemu od tego samego problemu,
- konieczności ponownej autoryzacji po zmianie zakresu.

Każda automatyczna naprawa powinna tworzyć nową wersję planu lub nowy `repair_attempt`, a nie nadpisywać poprzedni dowód.

---

# 3. Spójność modelu, maszyny stanów i ryzyka

## 3.1. Ocena zgodności z `rozwoj-RAE-part-1.md`

Na podstawie samego planu nie można potwierdzić pełnej zgodności z dokumentem źródłowym. Można jednak wskazać następujące warunki, które muszą być spełnione:

| Obszar | Stan w planie | Ocena |
|---|---|---|
| MAES / MinimumAuditableEvent | Wspomniane, ale bez pełnego kontraktu | Niepełne |
| Task State Machine | Wspomniana, brak jawnego diagramu i guardów | Niepełne |
| Risk Classification | Jest, ale dynamiczna wersja dopiero w P2 | Niespójne czasowo |
| Capability Contracts | Są deklaratywne, plan przewiduje hard enforcement | Kierunek poprawny |
| Execution Proof | `ExecutionReceipt` jest zbyt ub

---

## Krok 2: DeepSeek R1 (deepseek/deepseek-r1)
**Rola:** Deep Runtime & Concurrency Audit  
**Czas:** 06:47:12  

### Wynik Audytu i Rekomendacje:

### **Audyt Runtime, Współbieżności i Bezpieczeństwa Stanu**  
Przeprowadziłem głęboki audyt runtime i współbieżności RAE-Suite, skupiając się na kluczowych obszarach ryzyka. Poniżej przedstawiam listę luk oraz zaktualizowany plan z uwzględnieniem poprawek.

---

### **1. Wykryte Luki i Rekomendacje**  
#### **1.1. Zagrożenia współbieżności w stateless workerach**  
- **Problem**: Brak mechanizmu **lease'owania zadań** przy skalowaniu horyzontalnym. Wielu workerów może równocześnie pobrać to samo zadanie, prowadząc do:  
  - Duplikacji wykonania (np. wielokrotny `git commit`).  
  - Wyścigów o zasoby (np. współdzielony workspace).  
- **Rozwiązanie**:  
  - Wprowadzić **distributed lock** (np. via Redis/Raft) z timeoutem.  
  - Klucz locka: `tenant_id + task_id + attempt_no`.  
  - Automatyczne zwalnianie locka przy `FAILED/TIMEOUT`.  

#### **1.2. Wyścigi w stanach współdzielonych**  
- **Problem**: `ExecutionReceipt` modyfikowany przez wiele wątków (Quality Gate, Phoenix Auto-Repair) bez wersjonowania. Ryzyko:  
  - Nadpisanie artefaktów przy równoległej walidacji i naprawie.  
  - Utrata `compliance_evidence` przy aktualizacji stanu.  
- **Rozwiązanie**:  
  - **Wersjonowanie stanu** (ETag/vector clock) w DTO:  
    ```json
    "state_version": "timestamp_attemptNo_hash",
    "conflict_resolution": "LAST_WRITE_WINS|MANUAL"
    ```  
  - Blokady optymistyczne w API (`If-Match: state_version`).  

#### **1.3. Niebezpieczna izolacja w ToolGateway**  
- **Problem**: Async workers współdzielą połączenia do narzędzi (np. Docker API), co może prowadzić do:  
  - Mieszania stdout/stderr między zadaniami.  
  - Wycieku pamięci przy długotrwałych operacjach.  
- **Rozwiązanie**:  
  - **Izolacja procesowa** per `step_id`:  
    - Uruchamianie narzędzi w kontenerach z cgroups (CPU/memory limits).  
    - Dedicated connection pool per worker.  
  - Timeouty: `tool_timeout` + `graceful_shutdown` w polityce capability.  

#### **1.4. Utrata stanu w pętlach naprawczych**  
- **Problem**: Brak **idempotentnych retry** w Phoenix Auto-Repair. Przy awarii:  
  - Częściowe wykonanie kroków naprawy bez możliwości odtworzenia.  
  - Niespójność między `base_commit` a faktycznym workspace.  
- **Rozwiązanie**:  
  - **Idempotency key** w każdym kroku:  
    ```text
    idempotency_key = hash(tenant_id + task_id + step_id + repair_attempt + input_snapshot)
    ```  
  - **Transactional outbox** dla zdarzeń naprawy.  

#### **1.5. Niewystarczająca obsługa wyjątków w Hermes**  
- **Problem**: Eskalacja do OpenCode/Hermes przy `ABORTED` nie gwarantuje:  
  - Zachowania artefaktów (np. tymczasowe pliki usuwane przed eskalacją).  
  - Izolacji kontekstu błędu (np. wyjątek w Hermes zaburza kolejkę).  
- **Rozwiązanie**:  
  - **Sandboxed escalation**: Hermes uruchamiany w kontenerze z snapshotem stanu.  
  - **Dead Letter Queue** dla nieudanych eskalacji z exponential backoff.  

---

### **2. Zaktualizowany Plan Rozwoju RAE-Suite**  
```markdown
# Rozszerzony plan RAE-Suite (wersja 1.1)

## Sekcja 4: Bezpieczeństwo Runtime i Współbieżność (P0-P1)

### 4.1. Model Współbieżności
- **Lease-based task distribution**:  
  - Workerzy uzyskują lease (min. 30s, max. 5min) via consensus store.  
  - `TaskDispatcher` weryfikuje lease przed dispatch.  
- **Stateless workers z lokalną cache**:  
  - Workerzy przechowują stan tymczasowy w `/scratch/{task_id}` z TTL=24h.  
  - Automatyczne czyszczenie po `state_version` mismatch.

### 4.2. ToolGateway (Async Safe)
```json
{
  "isolation_level": "PROCESS|CONTAINER",
  "resource_limits": {
    "cpu": "2 cores",
    "memory": "4GB",
    "max_workers_per_node": 10
  },
  "async_timeouts": {
    "dispatch": "5s",
    "execution": "task_timeout * 1.5"
  },
  "retry_policy": {
    "max_attempts": 3,
    "backoff": "exponential(1s, 10s)"
  }
}
```

### 4.3. ExecutionReceipt (rozszerzenie o bezpieczeństwo)
```json
{
  "runtime_evidence": {
    "container_id": "docker://sha256:...",
    "resource_usage": {
      "cpu_ms": 1200,
      "memory_mb": 350
    },
    "isolation_checksum": "sha256:...",
    "lease_id": "uuidv5+timestamp"
  },
  "concurrency_guards": {
    "state_version": "timestamp_attemptNo",
    "conflict_resolution": "MANUAL"
  }
}
```

### 4.4. Phoenix Auto-Repair Loop
1. **Idempotentne retry**:  
   - Generuj `repair_attempt_id` i `idempotency_key` przed każdą iteracją.  
   - Waliduj `base_commit` przed wykonaniem (TOCTOU guard).  
2. **Ograniczenia**:  
   - `max_repair_cycles = min(5, task_risk_factor * 3)`  
   - `risk_increase_per_cycle = MEDIUM → HIGH`  
3. **Rollback**:  
   - Automatyczny przy 3 kolejnych `PARTIALLY_COMPLETED`.  
   - Kompensacja via `compensating_step_id`.

### 4.5. Hermes Escalation Protocol
- **Sandboxing**:  
  - Hermes otrzymuje snapshot: `workspace_tarball + receipt_snapshot`.  
  - Izolacja via Firecracker VM (microVM).  
- **Failure handling**:  
  - 3 nieudane própy → `ABORTED` z zapisem do `DeadLetterQueue`.  
  - Exponential backoff: `[1m, 5m, 15m]`.

## Sekcja 5: Harmonogram Wdrożenia (P0-P3)

### P0 (Critical Path)
- Lease-based task distribution (4.1).  
- Timeouty i izolacja ToolGateway (4.2).  
- Idempotency keys w Phoenix (4.4).

### P1 (High Risk)
- State versioning w ExecutionReceipt (4.3).  
- Hermes sandboxing (4.5).  
- Distributed locks dla Quality Tribunal.

### P2 (Medium Risk)
- Transakcyjny outbox dla zdarzeń naprawy.  
- Dynamiczne dostosowywanie `resource_limits` w runtime.

### P3 (Future)
- Automatyczne downgrade ryzyka po udanej kompensacji.  
- Integracja z distributed tracing (OpenTelemetry).
```

---

### **Podsumowanie Kluczowych Poprawek**  
1. **Zapobieganie wyścigom**: Leasy + wersjonowanie stanu eliminują duplikację zadań i nadpisywanie stanów.  
2. **Izolacja narzędzi**: Konteneryzacja + cgroups gwarantują, że awaria jednego narzędzia nie wpływa na inne.  
3. **Idempotencja napraw**: Klucze idempotentne i transakcyjny outbox zapewniają odporność na awarie.  
4. **Bezpieczna eskalacja**: Hermes w sandboxie z backoffem chroni przed kaskadowymi błędami.  

**Następne kroki**: Weryfikacja poprawek pod kątem wydajności (testy obciążeniowe 10k zadań równolegle) i implementacja mechanizmów P0.

---

## Krok 3: Claude Opus 4.8 (anthropic/claude-opus-4.8)
**Rola:** Types & Architecture Audit  
**Czas:** 06:48:18  

### Wynik Audytu i Rekomendacje:

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

---

## Krok 4: GPT-5.6 Sol (openai/gpt-5.6-sol)
**Rola:** Performance & Resource Audit  
**Czas:** 06:49:11  

### Wynik Audytu i Rekomendacje:

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

---

## Krok 5: Fable 5 (anthropic/claude-opus-5)
**Rola:** Reliability, Zero-Downtime & Quality Audit  
**Czas:** 06:50:16  

### Wynik Audytu i Rekomendacje:

# Audyt Reliability, Zero-Downtime & Quality — RAE-Suite v1.3 → v1.4

Zakres: konsensus Quality Tribunal, integralność i niezmienność dowodów (`ExecutionReceipt`, SHA-256 hash chaining, ISO 27001/42001), pętla samonaprawy Phoenix.
Werdykt ogólny: **plan v1.3 jest dojrzały wydajnościowo, ale niekompletny w warstwie dowodowej i decyzyjnej** — trzy najważniejsze mechanizmy jakościowe (Tribunal, Chain-of-Evidence, Phoenix) są wymieniane, lecz nie mają

---

