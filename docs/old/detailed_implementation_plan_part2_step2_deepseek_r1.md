<!-- Plan Część 2 po Kroku 2: DeepSeek R1 (deepseek/deepseek-r1) -->

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