<!-- Plan po Kroku 2: DeepSeek R1 (deepseek/deepseek-r1) -->

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