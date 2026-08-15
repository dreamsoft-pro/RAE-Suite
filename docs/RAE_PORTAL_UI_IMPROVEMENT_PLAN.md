
# Plan Udoskonalenia Interfejsu RAE-PORTAL: Wizualizacja Modułów, Logów Execution Ledger i Wyszukiwarka Multimodalna

## 1. Cel Architektoniczny
Obecny portal RAE-PORTAL posiada zbyt ubogi interfejs użytkownika (UI), uniemożliwiający szczegółowy podgląd działań poszczególnych modułów suity oraz brak jakiejkolwiek zaawansowanej wyszukiwarki zdarzeń, faktów i audytów.
Plan ma na celu przekształcenie RAE-PORTAL w pełnowymiarowy, nowoczesny panel kontrolny (Command Center) dla całej fabryki agentycznej RAE-Suite.

## 2. Główne Moduły i Nowe Dedykowane Widoki w RAE-PORTAL
1. **RAE-Supervisor Dashboard**: Widok stanu klastra, autoryzacji Autonomy Kernel, logów kontenerów Docker, trasowania zadań oraz historii decyzji CEO.
2. **RAE-Quality Tribunal Inspector**: Przeglądarka 3-poziomowych audytów jakościowych, głosowań konsensusowych LLM, raportów statycznych Ruff/Mypy/Coverage i blokad wdrożeniowych.
3. **RAE-Lab Kaizen Observatory**: Wykresy wskaźników długu technicznego (Lean Score, Complexity Index), telemetria MAB (Multi-Armed Bandit) oraz historyczne trendy wydajności.
4. **RAE-Memory Subconscious Explorer**: Podgląd 4 warstw pamięci (Episodic, Semantic, Working, Reflective), wizualizacja grafu wiedzy, statusy wyczyszczenia PII i bezpieczników Circuit Breakers.
5. **RAE-Phoenix & RAE-CLR Lab**: Inspektor procesów samonaprawy kodu, odtworzenia transakcyjnych outboxów, re-playa zdarzeń oraz badań R&D.
6. **A2A & Mesh Route Monitor**: Mapa połączeń peer-to-peer agentów, weryfikacja podpisów cyfrowych, tokeny capability Keycloak oraz metryki OTel/Prometheus.

## 3. Globalna Wyszukiwarka Multimodalna (RAE Global Search)
- **Wyszukiwanie Hybrydowe (Full-Text + Vector Semantic Search)**: Błyskawiczne przeszukiwanie logów execution ledger (`RAE_EXECUTION_LEDGER.jsonl`), faktów pamięciowych, transakcji outbox i śladów audytowych.
- **Filtry Wielowymiarowe**: Po module (`rae-supervisor`, `rae-memory`, itp.), statusie ryzyka (`R0` do `R6`), czasie (timestamp range), dzierżawcy (`tenant_id`) oraz identyfikatorze transakcji (`message_id`/`trace_id`).
- **Anonimizacja PII w UI**: Automatyczne maskowanie wrażliwych danych w widokach portalu zgodnie z normami ISO 27001 / ISO 42001.


---

## Rekomendacje i Audyt: GPT-5.6 Luna Pro (Domena UI, Hierarchia Widoków Modułów RAE-PORTAL, Schematy Komponentów i Filtry Wyszukiwania)
# Analiza i rekomendacje dla RAE-PORTAL

Poniższa ocena opiera się na przedstawionym planie. Nie zakładam, że wymienione moduły i źródła danych są już dostępne produkcyjnie — część rekomendacji wymaga najpierw potwierdzenia istniejących kontraktów API, schematów zdarzeń i modelu uprawnień.

---

## 1. Analiza braków w obecnym RAE-PORTAL

### 1.1. Brak nadrzędnego modelu informacji

Plan poprawnie identyfikuje moduły, ale nie definiuje jeszcze wspólnego modelu nawigacji i relacji między obiektami:

- zadaniem,
- decyzją,
- zdarzeniem,
- transakcją,
- agentem,
- audytem,
- faktem pamięciowym,
- incydentem,
- wdrożeniem,
- tenantem.

Bez takiego modelu portal może stać się zbiorem niezależnych dashboardów. Operator powinien móc przejść jedną ścieżką:

```text
Agent → Zadanie → Trace → Execution Ledger → Decyzja → Audyt → Artefakt / Incydent
```

### 1.2. Brak widoku operacyjnego typu Command Center

Niezbędny jest widok natychmiastowej oceny stanu systemu:

- czy system działa,
- które moduły są zdegradowane,
- czy występują blokady jakościowe,
- czy rośnie liczba błędów,
- czy Autonomy Kernel ograniczył autonomię,
- czy występują opóźnienia w pamięci lub routingu,
- czy wymagane są działania operatora.

Obecny plan wymienia dane, ale nie definiuje hierarchii alarmów ani sposobu odróżnienia:

- awarii,
- ostrzeżenia,
- trendu,
- informacji historycznej,
- wymaganej akcji.

### 1.3. Brak jednolitego modelu statusów i ryzyka

Filtry `R0–R6` są użyteczne, ale powinny mieć centralną definicję:

| Poziom | Znaczenie | Przykładowa reakcja UI |
|---|---|---|
| `R0` | Informacyjne / brak istotnego ryzyka | neutralny status |
| `R1` | Niskie ryzyko operacyjne | obserwacja |
| `R2` | Ryzyko wymagające uwagi | ostrzeżenie |
| `R3` | Istotne ryzyko jakościowe lub bezpieczeństwa | eskalacja |
| `R4` | Poważne ryzyko operacyjne | ograniczenie funkcji |
| `R5` | Krytyczne ryzyko | blokada lub izolacja |
| `R6` | Krytyczne naruszenie / stan awaryjny | natychmiastowy incident response |

Wymagane są również:

- kolorystyka niezależna od samego koloru,
- tekstowa etykieta poziomu,
- timestamp nadania ryzyka,
- źródło klasyfikacji,
- uzasadnienie,
- osoba lub mechanizm, który zmienił status,
- historia zmian.

### 1.4. Brak projektowanego Execution Ledger Explorer

`RAE_EXECUTION_LEDGER.jsonl` nie powinien być prezentowany wyłącznie jako surowy log. Potrzebne są trzy poziomy widoku:

1. **Lista zdarzeń**
2. **Panel szczegółów zdarzenia**
3. **Powiązany kontekst audytowy i transakcyjny**

Minimalny model zdarzenia powinien obejmować:

```json
{
  "event_id": "evt_123",
  "timestamp": "2026-01-01T12:00:00Z",
  "tenant_id": "tenant_a",
  "module": "rae-supervisor",
  "event_type": "task.completed",
  "status": "success",
  "risk_level": "R1",
  "message_id": "msg_123",
  "trace_id": "trace_456",
  "parent_event_id": "evt_122",
  "actor_type": "agent",
  "actor_id": "agent_7",
  "decision_id": "dec_42",
  "redaction_state": "masked",
  "payload_ref": "obj://ledger/evt_123"
}
```

Ważne: payload nie powinien być ładowany do UI bez kontroli dostępu. Lista wyników powinna korzystać z projekcji indeksowej, a nie z pełnego parsowania JSONL po stronie przeglądarki.

### 1.5. Brak rozdzielenia danych operacyjnych, audytowych i diagnostycznych

Portal powinien jasno rozdzielać:

- **widok operacyjny** — co dzieje się teraz,
- **widok audytowy** — co się wydarzyło i kto może to potwierdzić,
- **widok diagnostyczny** — dlaczego wystąpił problem,
- **widok eksperymentalny** — dane R&D, replay, Phoenix i CLR.

Dane eksperymentalne nie powinny mieszać się z oficjalnym stanem audytowym.

### 1.6. Brak zdefiniowanego kontraktu anonimizacji PII

Samo „maskowanie PII w UI” jest niewystarczające. Trzeba określić:

- jakie typy PII są wykrywane,
- czy maskowanie następuje przed indeksowaniem,
- czy możliwy jest kontrolowany reveal,
- kto może odsłonić dane,
- czy reveal jest audytowany,
- czy wyszukiwanie odbywa się po wartości jawnej, zmaskowanej czy po tokenie,
- jak obsługiwane są dane w embeddingach.

Rekomendowany model:

```text
Źródło → klasyfikacja PII → tokenizacja/maskowanie → indeks → UI
```

Nie należy polegać wyłącznie na maskowaniu po stronie frontendu. Użytkownik z dostępem do API mógłby ominąć UI.

### 1.7. Brak modelu uprawnień i separacji tenantów

Plan wymienia `tenant_id`, ale nie opisuje kontroli dostępu. Potrzebne są co najmniej:

- RBAC dla ról operacyjnych,
- ABAC dla tenantów, środowisk i poziomów ryzyka,
- row-level security,
- filtrowanie danych na poziomie API,
- audyt prób dostępu,
- osobne uprawnienia do:
  - przeglądania,
  - eksportu,
  - reveal PII,
  - replay,
  - uruchomienia naprawy,
  - zmiany konfiguracji,
  - zatwierdzania blokady jakościowej.

### 1.8. Brak zasad dotyczących świeżości i kompletności danych

Każdy dashboard powinien pokazywać:

- czas ostatniej aktualizacji,
- opóźnienie ingestu,
- zakres czasowy,
- kompletność danych,
- źródło,
- status synchronizacji,
- informację o możliwej niepełności.

Przykład:

```text
Dane aktualne: 12:04:31 UTC
Opóźnienie ingestu: 4,2 s
Kompletność ostatnich 15 min: 99,97%
Źródło: Execution Ledger Index
```

---

# 2. Szczegółowe poprawki i rozszerzenia UI/UX

## 2.1. Proponowana architektura informacji

### Główna nawigacja

```text
Overview
├── Command Center
├── Execution Ledger
├── Global Search
├── Agents & Mesh
├── Quality Tribunal
├── Memory Explorer
├── Kaizen Observatory
├── Phoenix & CLR
├── Incidents
└── Audit & Access
```

### Stały pasek kontekstowy

Na każdej stronie powinny być widoczne:

- tenant,
- środowisko: `dev / staging / production`,
- zakres czasu,
- aktywna tożsamość operatora,
- poziom dostępu,
- stan połączenia realtime,
- ostatnia synchronizacja,
- liczba aktywnych alarmów,
- przycisk eksportu, jeśli użytkownik ma uprawnienia.

## 2.2. Command Center

### Układ

#### Wiersz KPI

- aktywne zadania,
- błędy z ostatnich 15 minut,
- średnie i p95 latency,
- liczba zdarzeń `R4–R6`,
- stan Autonomy Kernel,
- stan Quality Gate,
- opóźnienie Execution Ledger,
- dostępność agentów.

#### Panel „Requires Attention”

Najważniejszy element strony. Powinien agregować wyłącznie sytuacje wymagające działania:

- zablokowane wdrożenia,
- przekroczenia progów ryzyka,
- niedostępne agenty,
- błędy replay,
- Circuit Breaker w stanie `OPEN`,
- nieudane audyty,
- zalegające transakcje outbox.

#### Oś zdarzeń

Chronologiczna lista najważniejszych zdarzeń z możliwością:

- filtrowania modułem,
- filtrowania poziomem ryzyka,
- przejścia do trace,
- przejścia do audytu,
- przypięcia zdarzenia do incydentu.

#### Stan modułów

Każdy moduł powinien posiadać kartę:

```text
RAE-Memory
Status: Degraded
R3
Latency p95: 840 ms
Circuit Breaker: HALF_OPEN
Ostatnia anomalia: 12:03:18 UTC
[View details]
```

Nie należy używać wyłącznie ikon lub kolorów.

## 2.3. Execution Ledger Explorer

### Widok listy

Tabela powinna obsługiwać:

- sortowanie po czasie i ryzyku,
- wirtualizację wierszy,
- kolumny konfigurowalne przez użytkownika,
- zapisane widoki,
- masowe zaznaczanie,
- eksport wyników zgodny z uprawnieniami,
- paginację kursorem zamiast offsetu dla dużych zbiorów.

Rekomendowane kolumny:

| Kolumna | Cel |
|---|---|
| Timestamp | porządek czasowy |
| Event type | typ zdarzenia |
| Module | źródło |
| Status | wynik |
| Risk | priorytet |
| Trace ID | korelacja |
| Message ID | transakcja |
| Actor | agent / użytkownik / system |
| Tenant | separacja kontekstu |
| Redaction | stan anonimizacji |

### Panel szczegółów

Po kliknięciu zdarzenia panel boczny powinien pokazać:

- metadane,
- payload po redakcji,
- timeline zdarzenia,
- parent/child events,
- trace,
- powiązane decyzje,
- powiązane fakty pamięciowe,
- wynik audytu,
- historię zmian,
- działania dostępne dla operatora.

Działania destrukcyjne, takie jak replay lub uruchomienie naprawy, powinny wymagać:

1. dodatkowego potwierdzenia,
2. wskazania powodu,
3. opcjonalnego ticketu/incydentu,
4. rejestracji operatora,
5. idempotency key.

## 2.4. Global Search

### Zakres

Wyszukiwarka powinna przeszukiwać osobne typy obiektów:

- zdarzenia Execution Ledger,
- trace i spany,
- decyzje,
- fakty pamięciowe,
- audyty,
- incydenty,
- agenty,
- artefakty,
- transakcje outbox,
- raporty jakościowe.

Wyniki należy grupować według typu, zamiast prezentować jedną niejednorodną listę.

### Tryby wyszukiwania

#### 1. Exact search

Dla:

- `message_id`,
- `trace_id`,
- `event_id`,
- `tenant_id`,
- `agent_id`.

#### 2. Full-text search

Dla:

- komunikatów,
- opisów decyzji,
- raportów,
- uzasadnień audytowych.

#### 3. Semantic search

Dla pytań w rodzaju:

```text
„Pokaż ostatnie decyzje związane z blokadą wdrożenia pamięci”
```

Wynik semantyczny powinien zawsze zawierać:

- score podobieństwa,
- źródło,
- dokładny fragment dopasowania,
- timestamp,
- typ obiektu,
- ograniczenia zastosowanego indeksu.

Nie należy ukrywać faktu, że wynik jest semantyczny, a nie dokładny.

### Pasek filtrów

Rekomendowane filtry:

- moduł,
- typ obiektu,
- event type,
- status,
- `R0–R6`,
- zakres czasu,
- tenant,
- environment,
- `message_id`,
- `trace_id`,
- agent,
- wersja,
- źródło danych,
- stan PII,
- status audytu,
- confidence score.

Filtry powinny być:

- wielokrotnego wyboru,
- widoczne jako chipy,
- łatwe do usunięcia pojedynczo,
- zapisywalne jako saved search,
- współdzielone tylko zgodnie z uprawnieniami.

### Wynik wyszukiwania

Każdy wynik powinien zawierać:

```text
[Typ obiektu] Tytuł / fragment
Module: rae-memory
Risk: R3
Timestamp: 2026-01-01 12:03:18 UTC
Trace: trace_456
Tenant: tenant_a
Match: semantic / full-text / exact
Redaction: masked
```

### Ranking hybrydowy

Praktyczny model:

```text
final_score =
  w_exact * exact_score +
  w_text * full_text_score +
  w_vector * semantic_score +
  w_recency * recency_score +
  w_risk * risk_priority
```

Wagi powinny być konfigurowalne po stronie backendu i obserwowalne w telemetrii. Nie należy promować zdarzeń krytycznych wyłącznie dlatego, że mają wysoki risk score — relevance i ryzyko powinny być prezentowane osobno.

## 2.5. Filtry czasowe i strefy czasowe

UI powinno obsługiwać:

- UTC jako domyślną strefę systemową,
- lokalną strefę użytkownika jako opcję,
- zakres absolutny,
- zakres względny: `ostatnie 15 min`, `24 h`, `7 dni`,
- granice włącznie/wyłącznie,
- wizualizację luk w danych.

Każdy eksport powinien zapisywać:

- zakres,
- strefę czasową,
- moment wykonania,
- aktywne filtry,
- użytkownika,
- wersję schematu.

## 2.6. Anonimizacja PII w interfejsie

### Stany wizualne

- `Unclassified` — dane nie zostały sklasyfikowane,
- `Clean` — brak wykrytego PII,
- `Masked` — dane zanonimizowane,
- `Restricted` — dostęp ograniczony,
- `Reveal available` — kontrolowane odsłonięcie możliwe,
- `Reveal denied` — brak uprawnień.

### Zasady reveal

Odsłonięcie powinno:

- wymagać uprawnienia,
- wymagać podania powodu,
- być logowane,
- mieć ograniczony czas,
- nie ujawniać całego payloadu, jeśli wystarczy pojedyncze pole,
- być wyłączone dla eksportów domyślnych.

### PII w wyszukiwaniu semantycznym

Embeddingi nie powinny być tworzone bezpośrednio z surowego PII. Rekomendowane jest:

- usunięcie lub tokenizacja PII przed embeddingiem,
- przechowywanie mapowania tokenów poza indeksem semantycznym,
- oddzielne polityki retencji,
- kontrola możliwości odtworzenia danych.

## 2.7. Audytowalność UI

Każda akcja operatorska powinna generować zdarzenie audytowe:

```text
actor_id
actor_role
tenant_id
action
resource_type
resource_id
timestamp
reason
before_state
after_state
request_id
trace_id
result
```

Dotyczy to również operacji pozornie tylko odczytowych, jeśli mają wpływ na bezpieczeństwo:

- reveal PII,
- eksport danych,
- uruchomienie replay,
- pobranie pełnego payloadu,
- zmiana filtrów w trybie uprzywilejowanym,
- zatwierdzenie lub odrzucenie audytu.

## 2.8. Dostępność i ergonomia

Minimalne wymagania:

- WCAG 2.2 AA,
- pełna obsługa klawiatury,
- widoczny focus,
- semantyczne nagłówki,
- alternatywne oznaczenie statusu poza kolorem,
- tryb wysokiego kontrastu,
- responsywność co najmniej dla laptopa i dużego tabletu,
- ograniczenie animacji,
- jasne komunikaty błędów,
- poprawna obsługa czytników ekranu dla tabel i wykresów.

Wykres powinien mieć także wersję tabelaryczną lub tekstowe podsumowanie.

## 2.9. Wydajność i skalowanie

### Frontend

- virtualized tables,
- lazy loading szczegółów,
- debounce wyszukiwania,
- anulowanie nieaktualnych zapytań,
- cache filtrów i metadanych,
- streaming wyników dla długich zapytań,
- ograniczenie rozmiaru payloadu.

### Backend i indeks

- indeks czasowy,
- indeks po `tenant_id`,
- indeks po `trace_id`, `message_id`, `event_id`,
- indeks po module i risk level,
- osobne indeksy full-text i vector,
- cursor-based pagination,
- preagregowane dane dla dashboardów,
- asynchroniczny eksport,
- limit kosztownych zapytań semantycznych.

### SLO dla wyszukiwarki

Przykładowe cele:

| Operacja | Cel |
|---|---:|
| Exact lookup | p95 < 300 ms |
| Full-text search | p95 < 1 s |
| Hybrid search | p95 < 2,5 s |
| Otwarcie szczegółu | p95 < 500 ms |
| Dashboard overview | p95 < 2 s |
| Aktualizacja realtime | < 5 s od ingestu |

Wartości te należy potwierdzić na podstawie wolumenu danych i wymagań operacyjnych.

---

# 3. Ocena z perspektywy domeny UI, logów, audytowalności i filtrów wyszukiwania

## 3.1. UI/UX

Najważniejsza zmiana nie polega na dodaniu większej liczby wykresów, lecz na zbudowaniu spójnego przepływu pracy operatora:

```text
Wykryj → Zrozum → Skoreluj → Oceń ryzyko → Podejmij akcję → Zweryfikuj → Zapisz audyt
```

Każdy widok powinien odpowiadać na trzy pytania:

1. Co się wydarzyło?
2. Dlaczego to ma znaczenie?
3. Co operator może zrobić dalej?

Należy unikać:

- dashboardów przeładowanych KPI,
- wykresów bez progów i kontekstu,
- kolorów bez tekstowych etykiet,
- ukrywania źródła danych,
- automatycznych akcji bez potwierdzenia,
- mieszania danych bieżących z historycznymi.

## 3.2. Execution Ledger

Ledger powinien być traktowany jako źródło audytowalnego przebiegu wykonania, a nie zwykły log aplikacyjny.

Rekomendowane zabezpieczenia:

- niezmienność rekordów,
- checksum lub hash chain,
- jednoznaczny `event_id`,
- wersjonowanie schematu,
- podpis lub pochodzenie źródła, jeśli wymagane,
- wykrywanie luk w sekwencji,
- retencja i polityka usuwania,
- korelacja z `trace_id` i `message_id`,
- oddzielenie zdarzeń systemowych od opisów generowanych przez LLM.

UI powinien wyraźnie pokazywać, czy opis jest:

- surowym zdarzeniem,
- streszczeniem,
- inferencją modelu,
- wynikiem klasyfikatora,
- decyzją zatwierdzoną przez człowieka.

## 3.3. Global Search

Wyszukiwarka powinna mieć deterministyczną ścieżkę dla identyfikatorów i kontekstową dla zapytań semantycznych.

Priorytet wyszukiwania:

1. dokładne ID,
2. filtr tenant/environment,
3. full-text,
4. semantic search,
5. korelacja z trace i zdarzeniami powiązanymi.

Kluczowa zasada: wynik wyszukiwania nie może przekraczać uprawnień użytkownika. Najpierw należy zastosować politykę dostępu, dopiero później ranking.

## 3.4. Filtry

Filtry nie powinny być implementowane wyłącznie jako parametry interfejsu. Ich walidacja musi zachodzić na backendzie.

Należy zabezpieczyć:

- izolację tenantów,
- maksymalny zakres czasu,
- limity wyników,
- ochronę przed kosztownymi zapytaniami,
- walidację identyfikatorów,
- kontrolę zapytań semantycznych,
- bezpieczny eksport,
- ochronę przed enumeracją danych.

Warto dodać filtr:

```text
Data provenance:
- native event
- derived metric
- LLM summary
- human verified
- inferred
```

To szczególnie ważne dla audytów i decyzji.

## 3.5. Mechanizmy audytowe

Portal powinien posiadać osobny **Audit Trail Viewer**, który pozwala sprawdzić:

- kto wykonał akcję,
- na jakim obiekcie,
- z jakiego powodu,
- jaki był stan przed i po,
- jaki był wynik,
- czy akcja była automatyczna czy ręczna,
- jaka polityka ją autoryzowała.

Dla akcji krytycznych należy stosować zasadę czterech oczu, np. dla:

- odsłonięcia PII wysokiej wrażliwości,
- uruchomienia masowego replay,
- wyłączenia Circuit Breaker,
- odblokowania Quality Gate,
- zmiany polityki autonomii.

---

# 4. Proponowane kontrakty API

## 4.1. Wyszukiwanie

```http
POST /api/v1/search
```

```json
{
  "query": "blokada wdrożenia pamięci",
  "mode": "hybrid",
  "tenant_ids": ["tenant_a"],
  "modules": ["rae-memory", "rae-quality"],
  "risk_levels": ["R3", "R4", "R5"],
  "time_range": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-02T00:00:00Z"
  },
  "object_types": ["event", "audit", "decision"],
  "page_size": 50,
  "cursor": null
}
```

Odpowiedź powinna zawierać:

```json
{
  "results": [],
  "next_cursor": "opaque_cursor",
  "search_id": "search_123",
  "applied_policies": [
    "tenant_isolation",
    "pii_masking",
    "role_based_access"
  ],
  "index_as_of": "2026-01-02T00:00:03Z"
}
```

## 4.2. Szczegóły zdarzenia

```http
GET /api/v1/events/{event_id}
```

Powinna istnieć możliwość pobrania:

- metadanych,
- bezpiecznego payloadu,
- trace,
- zdarzeń nadrzędnych i podrzędnych,
- audytów,
- powiązanych decyzji,
- stanu redakcji.

## 4.3. Akcje operatorskie

```http
POST /api/v1/events/{event_id}/replay
POST /api/v1/incidents/{incident_id}/acknowledge
POST /api/v1/pii/{resource_id}/reveal
```

Każda akcja powinna wymagać:

```json
{
  "reason": "Analiza przyczyny incydentu INC-123",
  "ticket_id": "INC-123",
  "idempotency_key": "unique-request-key"
}
```

---

# 5. Kryteria akceptacji MVP

## Command Center

- [ ] Operator widzi stan wszystkich głównych modułów.
- [ ] Każdy alarm posiada poziom ryzyka, źródło i timestamp.
- [ ] Można przejść z alarmu do trace i szczegółów zdarzenia.
- [ ] Widoczna jest świeżość oraz kompletność danych.
- [ ] Status nie opiera się wyłącznie na kolorze.

## Execution Ledger

- [ ] Można filtrować po module, tenant, statusie, ryzyku i czasie.
- [ ] Można wyszukać `event_id`, `message_id` i `trace_id`.
- [ ] Szczegóły są ładowane dopiero po wyborze rekordu.
- [ ] Payload jest redagowany zgodnie z polityką dostępu.
- [ ] Historia akcji operatorskich jest dostępna w audit trail.

## Global Search

- [ ] Działa exact, full-text i hybrid search.
- [ ] Wyniki są grupowane według typu obiektu.
- [ ] Wyniki są filtrowane przed rankingiem przez polityki dostępu.
- [ ] Każdy wynik ujawnia źródło dopasowania.
- [ ] Zapytania mają identyfikator i są mierzalne telemetrycznie.
- [ ] Istnieje paginacja kursorem i limit kosztu zapytań.

## PII

- [ ] Maskowanie następuje przed przekazaniem danych do UI.
- [ ] Reveal wymaga uprawnienia i powodu.
- [ ] Reveal jest audytowany.
- [ ] Eksport domyślnie nie zawiera danych jawnych.
- [ ] Dane PII nie trafiają bezpośrednio do embeddingów.

---

# 6. Priorytety wdrożenia

## Etap 1 — fundament

1. Ujednolicenie schematu zdarzeń.
2. Model uprawnień i izolacji tenantów.
3. Centralne definicje statusów i `R0–R6`.
4. API Execution Ledger.
5. PII redaction service.
6. Audit trail dla akcji operatorskich.

## Etap 2 — MVP operacyjne

1. Command Center.
2. Execution Ledger Explorer.
3. Exact i full-text search.
4. Filtry wielowymiarowe.
5. Trace detail view.
6. Saved searches.
7. Eksport asynchroniczny.

## Etap 3 — wyszukiwanie multimodalne

1. Indeks wektorowy.
2. Hybrid ranking.
3. Semantic query explanations.
4. Wyszukiwanie po relacjach i grafie wiedzy.
5. Korelacja zdarzeń, decyzji, audytów i pamięci.

## Etap 4 — funkcje zaawansowane

1. Replay i Phoenix z kontrolą czterech oczu.
2. Live topology A2A/Mesh.
3. Predykcja degradacji.
4. Automatyczne grupowanie incydentów.
5. Trendy Kaizen i rekomendacje jakościowe.

---

## Wniosek

Plan ma właściwy kierunek, ale wymaga przesunięcia akcentu z „dodania wielu paneli” na:

- wspólny model obiektów,
- bezpieczną i audytowalną warstwę danych,
- jednoznaczne statusy ryzyka,
- kontrolę dostępu przed rankingiem wyników,
- rozdzielenie danych surowych, pochodnych i inferowanych,
- operacyjny przepływ od wykrycia do weryfikacji działania.

Największą wartością RAE-PORTAL będzie nie liczba wykresów, lecz możliwość udzielenia wiarygodnej odpowiedzi:

> **Co się wydarzyło, jaki był tego wpływ, skąd pochodzi informacja, kto mógł ją zobaczyć lub zmienić i jakie działanie jest bezpieczne w tym momencie?**


---

## Rekomendacje i Audyt: DeepSeek R1 (Adversarial Review UI: Wydajność Zapytania Wyszukiwania, Stronicowanie, Wyścigi WebSockets & Wycieki PII w UI)
### **1. Analiza braków w obecnym planie RAE-PORTAL**  
**(Adversarial Review UI: Wyścigi, Wycieki PII, WebSockets)**  

#### **1.1 Wyścigi zasobów (Race Conditions) w UI**  
- **Problem**: Brak mechanizmów zapobiegających konfliktom przy równoległych akcjach operatorskich (np. równoczesny "reveal PII" i "replay" dla tego samego zdarzenia).  
- **Skutki**: Niespójność stanu systemu (np. odsłonięcie PII podczas replayu transakcji), uszkodzenie danych śledzenia.  
- **Brakujące elementy**:  
  - Transakcyjne blokady optymistyczne/pesymistyczne dla operacji modyfikujących stan (np. `version_id` w zdarzeniach).  
  - Wizualne blokowanie przycisków akcji podczas przetwarzania.  

#### **1.2 Wycieki PII przez WebSockets**  
- **Problem**: Dane przesyłane w trybie real-time (WebSockets) omijają mechanizmy redakcji UI.  
- **Przykładowy scenariusz**:  
  ```js
  // WebSocket payload bez redakcji:
  { event: "memory.update", data: "PESEL: 12345678901" }
  ```  
- **Brakujące elementy**:  
  - Middleware redakcyjny dla strumieni WebSocket.  
  - Separacja kanałów WebSocket według poziomu dostępu (np. `wss://raeportal/events?risk_level=R0-R2`).  

#### **1.3 Podatności XSS w dynamicznych payloadach**  
- **Problem**: Renderowanie niestrukturyzowanych JSON w panelu szczegółów umożliwia wstrzyknięcie kodu.  
- **Brakujące elementy**:  
  - Sanityzacja HTML przed wyświetleniem payloadu (np. DOMPurify).  
  - CSP (Content Security Policy) z restrykcyjnymi dyrektywami.  

#### **1.4 Wycieki metadanych przez błędy ładowania**  
- **Problem**: Błędy HTTP 403/500 ujawniają wrażliwe metadane (np. `event_id` niedostępnych zdarzeń).  
- **Przykład**:  
  ```json
  { "error": "Access denied to event: evt_789 (tenant: military)" }
  ```  
- **Brakujące elementy**:  
  - Ujednolicone komunikaty błędów bez szczegółów technicznych.  
  - Maskowanie identyfikatorów w odpowiedziach dla nieautoryzowanych zasobów.  

#### **1.5 Nieskorygowane opóźnienia w synchronizacji stanu**  
- **Problem**: Rozbieżności między stanem UI a backendem (np. wyświetlanie przestarzałej wersji zdarzenia po reveal PII).  
- **Skutki**: Wyciek danych przy odświeżeniu interfejsu podczas trwającej sesji reveal.  
- **Brakujące elementy**:  
  - Mechanizm unieważniania cache UI po zmianie stanu redakcji.  
  - Sygnalizacja WebSocket o unieważnieniu lokalnego stanu.  

---

### **2. Szczegółowe poprawki i rozszerzenia UI/UX**  
**(Implementacja mechanizmów obronnych)**  

#### **2.1 Bezpieczna komunikacja real-time**  
- **WebSocket Gateway z redakcją**:  
  ```python
  # Pseudokod serwera WebSocket
  async def websocket_handler(tenant_id, user_role):
      events = subscribe_to_ledger(tenant_id)
      async for event in events:
          redacted_event = pii_redactor.redact(event, user_role)  # Redakcja w czasie rzeczywistym
          await websocket.send(redacted_event)
  ```  
- **Zabezpieczenia**:  
  - Walidacja tokenów JWT dla każdej ramki WebSocket.  
  - Odrzucanie zdarzeń o `risk_level > R3` bez uprawnień.  

#### **2.2 Transakcyjny interfejs operatorski**  
- **Mechanizm idempotentności dla akcji**:  
  ```http
  POST /api/v1/actions/reveal-pii
  Headers: X-Idempotency-Key: {uuid}
  Body: { "event_id": "evt_123", "reason": "Audit INC-456" }
  ```  
- **Implementacja UI**:  
  - Blokada przycisku po kliknięciu + spinner.  
  - Automatyczne generowanie `idempotency_key` na sesję.  

#### **2.3 Sanityzacja dynamicznych payloadów**  
- **Komponent SafeJSONViewer**:  
  ```jsx
  const SafeJSONViewer = ({ data }) => (
    <pre>{DOMPurify.sanitize(JSON.stringify(data, null, 2))}</pre>
  );
  ```  
- **Polityka CSP**:  
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'nonce-{random}'; connect-src wss://raeportal.example.com;
  ```  

#### **2.4 Kontrola widoczności dla danych wrażliwych**  
- **Mechanizm "Reveal Shield"**:  
  - Zasłona półprzezroczysta nad redagowanymi polami.  
  - Wymaganie ponownego uwierzytelnienia (np. PIN) przed odsłonięciem.  
  - Automatyczne ukrywanie po 30s bez aktywności.  

#### **2.5 Synchronizacja stanu z wersjonowaniem**  
- **Nagłówki ETag dla zdarzeń**:  
  ```http
  GET /api/v1/events/evt_123
  ETag: "a1b2c3d4"
  ```  
- **Reakcja UI na zmiany**:  
  - Wyświetlanie komunikatu: _"Dane zostały zaktualizowane. Odśwież, aby zobaczyć najnowszą wersję"_.  
  - Blokada reveal dla nieaktualnych wersji.  

---

### **3. Rekomendacje z perspektywy Adversarial Review UI**  
**(Testy odpornościowe i wzorce bezpieczeństwa)**  

#### **3.1 Testy penetracyjne dla scenariuszy edge-case**  
- **Wyścigi zasobów**:  
  Symuluj 100 równoległych żądań reveal PII do tego samego zdarzenia. Oczekuj:  
  - Maksymalnie 1 udany reveal.  
  - 99 odpowiedzi `HTTP 423 Locked`.  
- **Ataki XSS przez payload JSON**:  
  Wstrzyknij ładunek: `{"comment": "<img src=x onerror=alert(document.cookie)>"}`. Oczekuj:  
  - Sanityzacji do `{"comment": "[redacted]"}`.  
  - Zablokowania wykonania skryptu.  

#### **3.2 Wzorce bezpieczeństwa dla WebSockets**  
- **Segmentacja kanałów**:  
  ```text
  /low-risk: R0-R2 events (no PII)  
  /high-risk: R3+ events (requires auth upgrade)
  ```  
- **Monitorowanie anomalii**:  
  - Alarm przy >100 połączeń/sekundę z jednego IP.  
  - Automatyczne blokowanie przy próbach enumeracji `event_id`.  

#### **3.3 Ochrona przed wyciekami przez cache przeglądarki**  
- **Kontrola nagłówków HTTP**:  
  ```http
  Cache-Control: no-store, max-age=0  
  Pragma: no-cache  
  ```  
- **Walidacja stanu przy ponownym wejściu**:  
  - Wymaganie ponownego uwierzytelnienia po wznowieniu zakładki przeglądarki.  
  - Czyszczenie sessionStorage po zamknięciu karty.  

#### **3.4 Audyt interakcji UI**  
- **Rejestracja wszystkich akcji operatorskich**:  
  ```json
  {
    "action": "pii_reveal",
    "event_id": "evt_123",
    "ui_state": "event_detail_view",
    "timestamp": "2026-01-01T12:00:00Z",
    "user_actions": ["hover", "scroll", "click"]
  }
  ```  
- **Korelacja z logami backendu**:  
  Automatyczne flagowanie rozbieżności między logami UI a API.  

#### **3.5 Zasady fail-safe dla UI**  
- **Tryb awaryjny przy wykryciu anomalii**:  
  - Automatyczne przejście do widoku tylko do odczytu przy >5% błędów API.  
  - Wyłączenie WebSockets przy utracie synchronizacji czasowej >10s.  
- **Mechanizm samoobrony**:  
  Automatyczne wylogowanie przy wykryciu nietypowych wzorców interakcji (np. 100 kliknięć/sekundę).  

---

### **Podsumowanie implementacyjne**  
| Komponent         | Ryzyko          | Rozwiązanie                          | Priorytet |
|-------------------|-----------------|--------------------------------------|-----------|
| WebSockets        | Wyciek PII      | Redakcja strumieni + segmentacja     | CRITICAL  |
| Akcje operatorskie| Wyścigi zasobów | Idempotency Key + blokady UI         | HIGH      |
| Dynamiczny payload| XSS             | DOMPurify + CSP                      | HIGH      |
| Cache przeglądarki| Wyciek danych   | `no-store` + walidacja stanu         | MEDIUM    |
| Komunikaty błędów | Wyciek metadanych| Ujednolicone odpowiedzi              | MEDIUM    |

> **Pilne działania**:  
> 1. Implementacja middleware redakcyjnego dla WebSockets.  
> 2. Integracja `X-Idempotency-Key` w interfejsie operatorskim.  
> 3. Testy penetracyjne komponentu SafeJSONViewer.  
> 4. Audyt polityki CSP pod kątem luk XSS.  

Raport szczegółowy z testami Adversarial UI zostanie dostarczony w formacie SARFA (Security Adversarial Review Findings Assessment). Czy potrzebujesz dodatkowych specyfikacji dla któregokolwiek komponentu?


---

## Rekomendacje i Audyt: Claude Opus 4.8 (Architektura Komponentów, Design System UX, Maszyny Stanów i Typowane REST/OpenAPI dla Portalu)

# Audyt RAE-PORTAL: Grok 4.8 — Frontend Architecture, Design System, Component Contracts & Typed REST/OpenAPI

**Domena:** Architektura frontendowa, System projektowy (Design System), kontrakty komponentów oraz typowane API (OpenAPI-first).
**Kontekst:** Uzupełniam analizy GPT-5.6 Luna Pro (model obiektów, PII, audytowalność) oraz DeepSeek R1 (adversarial: race conditions, WebSockets, XSS). Skupiam się na **warstwie inżynierskiej frontendu** — tam, gdzie te rekomendacje muszą zostać zmaterializowane jako kod produkcyjny.

---

## 1. Analiza braków w obecnym planie RAE-PORTAL

### 1.1. Brak zdefiniowanej architektury frontendowej

Plan opisuje **co** ma być wyświetlane, ale nie **jak** ma być zbudowany frontend. Brakuje decyzji o:

| Obszar | Brak w planie | Konsekwencja |
|---|---|---|
| Model renderowania | SPA vs SSR/RSC | Brak strategii dla dużych ledgerów i SEO-N/A dashboardów |
| State management | Server state vs client state | Ryzyko chaosu przy realtime + filtrach |
| Struktura modułowa | Monolit vs micro-frontends | 6 modułów o różnym cyklu życia bez izolacji |
| Routing i deep-linking | Brak specyfikacji | Niemożność współdzielenia widoków (kluczowe dla audytu!) |
| Fetching layer | Ad-hoc vs typed client | Brak spójności z kontraktami API |

**Krytyczne:** Bez **deep-linkowalnego stanu** (filtry, zakres czasu, tenant w URL) portal audytowy jest bezużyteczny — operator nie może przekazać linku „zobacz to samo co ja”.

### 1.2. Brak Design System jako źródła prawdy

Trzy audyty wymagają dziesiątek stanów wizualnych (R0–R6, `Masked/Restricted/Reveal`, `Degraded/OPEN/HALF_OPEN`), ale nikt nie zdefiniował **systemu tokenów projektowych**. Bez tego każdy moduł zaimplementuje ryzyko `R4` innym odcieniem czerwieni.

### 1.3. Brak kontraktów komponentów (component contracts)

GPT-5.6 i DeepSeek opisują komponenty (`SafeJSONViewer`, `Reveal Shield`, panel szczegółów), ale jako **fragmenty implementacji, nie kontrakty**. Brakuje:
- typowanych propsów,
- zdefiniowanych stanów (loading/error/empty/partial),
- polityki dostępności per komponent,
- wariantów i granic odpowiedzialności.

### 1.4. Brak OpenAPI-first i generowania typów

Plan zawiera przykłady endpointów (`POST /api/v1/search`), ale **nie jako specyfikację OpenAPI**. To oznacza:
- brak single source of truth dla typów FE↔BE,
- ręczne, rozjeżdżające się interfejsy TypeScript,
- brak walidacji runtime odpowiedzi (krytyczne przy PII!).

### 1.5. Brak strategii dla stanów niepewności danych

Wszystkie audyty podkreślają: dane pochodne, LLM-inference, świeżość, luki. Ale **nie ma komponentowego wzorca** reprezentowania niepewności/prowenancji w UI.

### 1.6. Brak spójnej obsługi błędów i pustych stanów

DeepSeek słusznie wskazuje wyciek metadanych w błędach — ale brak **systemowego kontraktu error-handling** na froncie (error boundaries, fallbacki, degradacja).

---

## 2. Szczegółowe poprawki i rozszerzenia UI/UX

### 2.1. Rekomendowana architektura frontendowa

```text
┌─────────────────────────────────────────────────────────┐
│  RAE-PORTAL Shell (App Router / RSC)                      │
│  ├── Auth & Session Boundary (RBAC/ABAC context)         │
│  ├── Global Context Bar (tenant/env/time/identity)       │
│  └── Realtime Provider (WebSocket, redagowany kanał)     │
├─────────────────────────────────────────────────────────┤
│  Feature Modules (lazy-loaded, izolowane)                │
│  ├── command-center   ├── ledger-explorer                │
│  ├── global-search    ├── agents-mesh                    │
│  ├── quality-tribunal ├── memory-explorer                │
│  ├── phoenix-clr      ├── incidents / audit-trail        │
├─────────────────────────────────────────────────────────┤
│  Shared Layer                                            │
│  ├── @rae/design-system  (tokens, primitives)           │
│  ├── @rae/api-client     (generated from OpenAPI)       │
│  ├── @rae/query          (server-state, TanStack Query) │
│  └── @rae/audit-hooks    (auto-logowanie akcji UI)      │
└─────────────────────────────────────────────────────────┘
```

**Kluczowe decyzje:**

1. **RSC + Server Actions** dla widoków read-heavy (ledger, search) → payload nie przechodzi przez klienta bez potrzeby (wspiera PII).
2. **Rozdzielenie server-state (TanStack Query) i client-state (URL + Zustand)**:
   - Server-state: dane z API (cache, invalidation, ETag).
   - Client-state: filtry, zaznaczenia, layout.
3. **Filtry i kontekst w URL (nuqs/searchParams)** — deep-linking obowiązkowy dla audytowalności.
4. **Micro-frontends opcjonalnie** przez Module Federation tylko jeśli zespoły są niezależne; domyślnie monorepo z izolacją per feature.

### 2.2. Design System — hierarchia tokenów

Trójwarstwowa architektura tokenów (zgodna z podejściem DTCG):

```text
┌── Primitive tokens ──┐   ┌── Semantic tokens ──┐   ┌── Component tokens ──┐
│ color.red.500        │→  │ risk.critical.bg    │→  │ risk-badge.R6.bg      │
│ color.amber.400      │   │ risk.warning.bg     │   │ status-dot.degraded   │
│ space.4              │   │ surface.elevated    │   │ ledger-row.height     │
└──────────────────────┘   └─────────────────────┘   └───────────────────────┘
```

#### Tokeny ryzyka (single source of truth dla R0–R6)

```json
{
  "risk": {
    "R0": { "label": "Info",      "bg": "{color.slate.100}",  "fg": "{color.slate.700}",  "icon": "circle",        "pattern": "none" },
    "R1": { "label": "Low",       "bg": "{color.blue.100}",   "fg": "{color.blue.800}",   "icon": "info",          "pattern": "none" },
    "R2": { "label": "Moderate",  "bg": "{color.amber.100}",  "fg": "{color.amber.900}",  "icon": "triangle",      "pattern": "diagonal" },
    "R3": { "label": "Elevated",  "bg": "{color.orange.100}", "fg": "{color.orange.900}", "icon": "triangle-fill", "pattern": "diagonal" },
    "R4": { "label": "Severe",    "bg": "{color.red.100}",    "fg": "{color.red.900}",    "icon": "alert",         "pattern": "dense" },
    "R5": { "label": "Very High", "bg": "{color.red.200}",    "fg": "{color.red.950}",    "icon": "alert-fill",    "pattern": "dense" },
    "R6": { "label": "Critical",  "bg": "{color.red.600}",    "fg": "{color.white}",      "icon": "octagon-fill",  "pattern": "solid" }
  }
}
```

> **Zgodność z WCAG:** każdy poziom ryzyka niesie `label` (tekst) + `icon` + `pattern` — nigdy sam kolor. Realizuje wymóg GPT-5.6 („kolorystyka niezależna od koloru”) i WCAG 2.2 AA na poziomie systemu, nie ad-hoc.

### 2.3. Kontrakty kluczowych komponentów

#### `<RiskBadge />` — kanoniczna reprezentacja ryzyka

```typescript
interface RiskBadgeProps {
  level: RiskLevel;                    // 'R0' | ... | 'R6' (z typów OpenAPI)
  classifiedAt?: string;               // ISO timestamp nadania
  classifiedBy?: ClassificationSource; // 'system' | 'llm' | 'human' | 'classifier'
  reason?: string;                     // uzasadnienie (tooltip)
  size?: 'sm' | 'md' | 'lg';
  showHistory?: boolean;               // link do historii zmian ryzyka
}
// Zawsze renderuje: kolor + ikona + wzór + etykieta tekstowa.
// A11y: role="status", aria-label pełny opis, tooltip klawiaturowy.
```

#### `<RedactedField />` — zunifikowana obsługa PII (materializuje DeepSeek „Reveal Shield”)

```typescript
type RedactionState =
  | 'unclassified' | 'clean' | 'masked'
  | 'restricted' | 'reveal-available' | 'reveal-denied';

interface RedactedFieldProps {
  value: string;                    // ZAWSZE zmaskowana wartość z API
  state: RedactionState;
  fieldPath: string;                // np. "payload.customer.pesel"
  resourceId: string;
  onReveal?: (ctx: RevealContext) => Promise<RevealResult>;
  revealTtlSeconds?: number;        // domyślnie 30s (auto-hide)
  requireStepUp?: boolean;          // ponowne uwierzytelnienie (PIN/MFA)
}

interface RevealContext {
  fieldPath: string;
  reason: string;                   // wymagane
  ticketId?: string;
  idempotencyKey: string;           // generowany automatycznie
}
```

**Wbudowane zabezpieczenia (spełnia DeepSeek + GPT-5.6):**
- reveal tylko per-pole, nigdy cały payload,
- auto-hide po TTL + przy blur/utracie fokusu karty,
- step-up auth przed odsłonięciem wysokiej wrażliwości,
- każdy reveal wywołuje `@rae/audit-hooks` → zdarzenie audytowe,
- wartość nigdy nie trafia do `sessionStorage`/logów FE.

#### `<SafeJSONViewer />` — bezpieczna prezentacja payloadu

```typescript
interface SafeJSONViewerProps {
  data: RedactedPayload;            // typ z OpenAPI, pola oznaczone redaction
  schemaRef?: string;               // wersja schematu do walidacji
  maxDepth?: number;                // ochrona przed głębokimi strukturami
  maxBytes?: number;                // limit rozmiaru (perf + DoS)
  onRevealField?: (path: string) => void;
}
```

**Implementacja:** renderowanie strukturalne (drzewo), **nie** `dangerouslySetInnerHTML`. Każda wartość string traktowana jako text-node (React escaping domyślny) + sanityzacja obiektów zagnieżdżonych. To silniejsze niż `DOMPurify` na `JSON.stringify` proponowany przez DeepSeek — eliminuje XSS u źródła, bo nigdy nie renderujemy HTML.

#### `<DataProvenanceTag />` — reprezentacja prowenancji (materializuje GPT-5.6 §3.4)

```typescript
type Provenance =
  | 'native-event' | 'derived-metric'
  | 'llm-summary' | 'human-verified' | 'inferred';

interface DataProvenanceTagProps {
  provenance: Provenance;
  confidence?: number;      // 0–1, tylko dla llm/inferred
  sourceRef?: string;
}
// Wizualnie odróżnia dane surowe od inferowanych — obowiązkowe przy audytach.
```

#### `<FreshnessIndicator />` — świeżość danych (materializuje GPT-5.6 §1.8)

```typescript
interface FreshnessIndicatorProps {
  asOf: string;              // ISO
  ingestLagMs: number;
  completeness?: number;     // 0–1 dla okna
  source: string;
  realtimeStatus: 'live' | 'delayed' | 'disconnected' | 'stale';
}
// Stan 'stale' → wymusza wizualne oznaczenie „dane mogą być nieaktualne".
```

### 2.4. Wzorzec stanów komponentu danych

Każdy komponent konsumujący dane MUSI obsłużyć pełny zestaw stanów (kontrakt DS):

```typescript
type DataViewState<T> =
  | { status: 'loading' }
  | { status: 'error'; error: NormalizedError }   // bez wycieku metadanych
  | { status: 'empty' }
  | { status: 'partial'; data: T; missing: string[] }  // luki w danych!
  | { status: 'stale'; data: T; asOf: string }
  | { status: 'ready'; data: T };
```

Stan `partial` i `stale` to bezpośrednia odpowiedź na wymóg „wizualizacja luk w danych” i „nie mieszać realtime z historycznymi”.

### 2.5. Typowany klient API i realtime (integracja z DeepSeek WebSockets)

```typescript
// Generowane z OpenAPI — pełna typizacja end-to-end
import { createRaeClient } from '@rae/api-client';

const client = createRaeClient({
  baseUrl: '/api/v1',
  // Runtime validation odpowiedzi (zod z OpenAPI) — wykrywa wyciek PII
  validateResponses: true,
  onSchemaViolation: (v) => auditLog.securityEvent('schema_violation', v),
});

// WebSocket z typowanymi, redagowanymi zdarzeniami + segmentacja kanałów
const realtime = client.subscribe({
  channel: 'ledger.events',
  riskCeiling: session.maxRiskLevel,   // segmentacja wg uprawnień (DeepSeek 3.2)
  tenantId: session.tenantId,
  onEvent: (evt: RedactedLedgerEvent) => { /* evt już zredagowany serwerowo */ },
  onInvalidate: (etag) => queryClient.invalidateQueries(...),  // sync stanu
});
```

---

## 3. Rekomendacje z perspektywy Grok 4.8

### 3.1. Architektura frontendowa

**Rekomendacja: Monorepo (Turborepo/Nx) + RSC-first + strict client boundaries.**

| Zasada | Uzasadnienie audytowe |
|---|---|
| **Server-first rendering** dla ledger/search | Payload z PII nie trafia do klienta bez potrzeby |
| **URL jako źródło stanu widoku** | Deep-linking = audytowalna reprodukowalność widoku |
| **Feature isolation** | 6 modułów o różnych cyklach; izolacja błędów (jeden moduł nie kładzie portalu) |
| **Zero client-side JSONL parsing** | Zgodnie z GPT-5.6 — tylko projekcje indeksowe, cursor pagination |

**Wzorzec bezpiecznej degradacji (materializuje DeepSeek 3.5 fail-safe):**

```typescript
// Global error boundary + circuit breaker na poziomie fetch
if (apiErrorRate > 0.05) portalMode.set('read-only');
if (clockDriftMs > 10_000) realtime.disable('clock-drift');
```

### 3.2. Design System UX

**Rekomendacja: DS jako oddzielny, wersjonowany pakiet z governance.**

1. **Tokeny w formacie DTCG** → jedno źródło dla web, eksportów PDF, ewentualnych natywnych klientów.
2. **Storybook + Chromatic** jako kontrakt wizualny i regresja (wizualne testy stanów R0–R6, redaction states).
3. **Accessibility jako gate CI**: `axe-core` + testy klawiaturowe w pipeline. Komponent bez a11y = build fail.
4. **Dual-representation obowiązkowe**: każdy wykres ma wariant tabelaryczny (`<Chart>` renderuje `<DataTable>` jako `aria` fallback) — realizuje GPT-5.6 §2.8.

```text
Governance DS:
  - zmiana tokenu ryzyka → wymaga approval security + design (4-eyes)
  - nowy komponent → kontrakt propsów + a11y audit + story przed merge
```

### 3.3. Component Contracts

**Rekomendacja: kontrakt = Typy + Stany + A11y + Wariancje, egzekwowany w CI.**

Każdy komponent współdzielony dostarcza:

```text
component/
├── Component.tsx          # implementacja
├── Component.types.ts     # propsy z typów OpenAPI (nie duplikowane!)
├── Component.stories.tsx  # wszystkie stany (loading/error/empty/partial/stale)
├── Component.a11y.test.ts # axe + keyboard
└── Component.contract.md  # granice odpowiedzialności, security notes
```

**Zasada nadrzędna dla komponentów PII/audytowych:** *fail-closed by default* — jeśli props `state` jest `undefined` lub nieznany, komponent renderuje `restricted`, nigdy nie ujawnia wartości.

### 3.4. Typowane REST / OpenAPI-first

**Rekomendacja: OpenAPI 3.1 jako single source of truth, generacja w obie strony.**

```text
openapi.yaml (source of truth)
   ├──→ @rae/api-client (TypeScript + zod runtime validators)
   ├──→ BE handlers (walidacja request/response)
   └──→ dokumentacja + kontrakt testy (Dredd/Schemathesis)
```

**Kluczowe rozszerzenia schematu (materializują wszystkie 3 audyty):**

```yaml
components:
  schemas:
    RedactedLedgerEvent:
      type: object
      required: [event_id, timestamp, tenant_id, risk_level, redaction_state, provenance]
      properties:
        event_id:      { type: string, pattern: '^evt_[a-z0-9]+$' }
        risk_level:    { $ref: '#/components/schemas/RiskLevel' }
        redaction_state: { $ref: '#/components/schemas/RedactionState' }
        provenance:    { $ref: '#/components/schemas/Provenance' }   # GPT-5.6
        payload_ref:   { type: string }   # NIGDY inline payload w liście
        x-rae-pii-fields:                  # metadane pól wrażliwych
          type: array
          items: { type: string }

  responses:
    Error:                                 # ujednolicony błąd (DeepSeek 1.4)
      description: Bezpieczny błąd bez wycieku metadanych
      content:
        application/json:
          schema:
            type: object
            required: [code, request_id]
            properties:
              code: { type: string, enum: [unauthorized, not_found, forbidden, rate_limited, conflict] }
              request_id: { type: string }   # korelacja, ZERO szczegółów zasobu
```

**Nagłówki kontraktowe w OpenAPI (spójne z DeepSeek):**

```yaml
parameters:
  - { in: header, name: If-Match, schema: { type: string } }       # ETag / optimistic lock
  - { in: header, name: X-Idempotency-Key, schema: { type: string } }
responses:
  '423': { description: Locked — konflikt równoczesnej operacji (race condition) }
  '412': { description: Precondition Failed — stan zmieniony (ETag mismatch) }
```

**Runtime response validation** to nie luksus — przy PII to **kontrola bezpieczeństwa**: jeśli backend przypadkiem zwróci niezredagowane pole, walidator zod (`redaction_state` vs obecność wartości) wykrywa naruszenie i blokuje render + loguje incydent.

---

## Podsumowanie — priorytety wdrożeniowe (perspektywa Grok 4.8)

| Priorytet | Element | Realizuje wymóg | Etap |
|---|---|---|---|
| **CRITICAL** | OpenAPI 3.1 + generowany typed client z runtime validation | Spójność typów, wykrywanie wycieku PII | 1 |
| **CRITICAL** | Design tokens R0–R6 + redaction states (fail-closed) | WCAG, spójność ryzyka | 1 |
| **HIGH** | Kontrakty `<RedactedField>`, `<SafeJSONViewer>`, `<RiskBadge>` | PII, XSS, audytowalność | 1–2 |
| **HIGH** | URL-state architecture (deep-linking) | Reprodukowalność audytowa | 2 |
| **HIGH** | Typowany WebSocket z segmentacją kanałów | Realtime bez wycieku PII | 2 |
| **MEDIUM** | Stany `partial`/`stale`/`empty` + `<FreshnessIndicator>` | Świeżość, luki danych | 2 |
| **MEDIUM** | Storybook + axe CI gate + visual regression | DS governance, a11y | 2–3 |
| **MEDIUM** | `<DataProvenanceTag>` w wynikach search/audit | Rozróżnienie surowe/inferowane | 3 |

### Wniosek

Trzy poprzednie audyty zdefiniowały **model, bezpieczeństwo i odporność adwersaryjną**. Moja domena zamyka pętlę inżynierską:

> **Jeśli kontrakt (OpenAPI) i Design System są źródłem prawdy, to bezpieczeństwo PII, spójność ryzyka i audytowalność przestają być kwestią dyscypliny programisty — stają się gwarantowane przez typy, testy CI i fail-closed defaults.**

To przesuwa RAE-PORTAL z „poprawnie zaprojektowanego” na **„niemożliwego do niepoprawnego zaimplementowania”** — co jest właściwym celem dla systemu audytowalnego klasy ISO 27001 / ISO 42001.

Czy chcesz, abym rozwinął pełną specyfikację OpenAPI 3.1 dla endpointów portalu lub szczegółowy kontrakt Storybook dla komponentów PII?


---

## Rekomendacje i Audyt: GPT-5.6 Sol (Optymalizacja Szybkości Skanowania, Indeksowanie Wyszukiwarki, Embedded Grafana/OTel & Footprint)
# Audyt RAE-PORTAL — optymalizacja renderowania, telemetryka, Embedded Grafana/OTel i footprint

## Ocena ogólna

Plan jest dojrzały w obszarach bezpieczeństwa, audytowalności, wyszukiwania i kontraktów komponentowych. Nadal brakuje jednak kompletnej strategii dotyczącej:

- kosztu renderowania dużych zbiorów,
- zarządzania pamięcią przeglądarki,
- wydajności wykresów i grafów,
- bezpiecznego osadzania Grafany,
- telemetryki samego portalu,
- kontroli kosztu zapytań obserwowalności,
- budżetów paczek frontendowych,
- degradacji na słabszych stacjach operatorskich.

Najważniejsza zasada:

> RAE-PORTAL nie może poprawiać obserwowalności klastra kosztem pogorszenia działania klastra, backendu telemetrycznego albo stacji operatora.

---

# 1. Analiza braków w obecnym planie RAE-PORTAL

## 1.1. Brak jawnych budżetów wydajnościowych frontendu

SLO dla API są zdefiniowane, ale nie ma budżetów dla przeglądarki:

- rozmiaru JavaScript,
- czasu hydratacji,
- liczby węzłów DOM,
- zużycia pamięci,
- czasu renderowania tabeli,
- liczby punktów na wykresie,
- liczby aktywnych subskrypcji realtime,
- kosztu długiej sesji operatorskiej.

Rekomendowane wartości początkowe:

| Metryka | Budżet początkowy |
|---|---:|
| Initial JS, gzip | `< 250 KB` dla shell |
| JS pojedynczego modułu lazy-loaded | `< 150 KB` |
| LCP | `< 2,5 s` p75 |
| INP | `< 200 ms` p75 |
| CLS | `< 0,1` |
| Hydratacja shell | `< 1 s` na referencyjnym laptopie |
| Długie zadania głównego wątku | `< 50 ms` |
| Węzły DOM w widoku tabeli | `< 2 000` |
| Pamięć po 30 min pracy | `< 300 MB` |
| Wzrost pamięci po 2 h | `< 20%` od stanu ustalonego |
| Aktywne subskrypcje realtime | maks. 1 współdzielone połączenie na kartę |
| Punkty renderowane na wykresie | zwykle `< 5 000` po downsamplingu |

Budżety należy zweryfikować testami na rzeczywistych stacjach operatorów, nie tylko na komputerach deweloperskich.

## 1.2. Brak modelu renderowania dla dużych zbiorów danych

Plan wymienia wirtualizację, ale nie definiuje jej granic. Jest to niewystarczające dla:

- milionów zdarzeń Execution Ledger,
- dużych trace’ów,
- grafu wiedzy,
- topologii agentów,
- wieloserii Prometheus,
- długich sesji realtime.

Nie należy przekazywać do przeglądarki całego zbioru, a następnie go wirtualizować. Wirtualizacja ogranicza DOM, ale nie usuwa kosztu:

- transferu,
- parsowania JSON,
- przechowywania obiektów w pamięci,
- sortowania,
- filtrowania,
- garbage collection.

Wymagany jest model:

```text
Server-side filtering
→ server-side aggregation/downsampling
→ cursor pagination
→ ograniczone okno danych
→ wirtualizacja renderowanego fragmentu
```

## 1.3. Zbyt szerokie założenie RSC-first

Server Components są dobrym wyborem dla:

- początkowego shell,
- statycznych metadanych,
- wyników read-heavy,
- kontroli dostępu przed serializacją.

Nie powinny jednak być traktowane jako uniwersalne rozwiązanie dla:

- tabel z częstą zmianą filtrów,
- strumieni realtime,
- drag/zoom wykresów,
- Trace Waterfall,
- grafów Canvas/WebGL,
- paneli Grafana,
- interaktywnych inspektorów.

Rekomendowany model hybrydowy:

```text
Server-rendered shell i polityki
+ client islands dla interakcji
+ Web Workers dla ciężkich transformacji
+ backendowe agregacje dla dużych danych
```

Należy też pamiętać, że RSC nie gwarantuje ochrony PII. Każdy obiekt przekazany do komponentu klienckiego zostaje zserializowany. Granica bezpieczeństwa nadal musi znajdować się w API i warstwie polityk.

## 1.4. Brak strategii dla wykresów i grafów

Plan wymienia:

- wykresy Kaizen,
- topologię A2A/Mesh,
- graf wiedzy,
- trace i spany,
- realtime telemetry.

Nie definiuje technologii renderowania ani progów przełączenia:

| Skala | Zalecane renderowanie |
|---|---|
| do ok. 500 elementów | SVG |
| 500–10 000 elementów | Canvas |
| powyżej 10 000 / intensywne animacje | WebGL, po redukcji danych |
| bardzo duże grafy | agregacja klastrów po stronie backendu |

SVG dla dziesiątek tysięcy węzłów spowoduje blokowanie głównego wątku i problemy z dostępnością. Canvas/WebGL poprawiają wydajność, ale wymagają równoległej reprezentacji tekstowej lub tabelarycznej.

## 1.5. Brak polityki cardinality i kosztu zapytań Prometheus/OTel

Panel obserwowalności może sam generować bardzo kosztowne zapytania. Szczególnie ryzykowne są:

- regexy na szerokich zakresach,
- nieograniczone `group by`,
- etykiety o wysokiej kardynalności,
- `trace_id`, `message_id` i `user_id` jako label metryki,
- zbyt długie zakresy czasowe z wysoką rozdzielczością,
- automatyczne odświeżanie wielu niewidocznych paneli.

`trace_id`, `message_id`, `event_id` powinny być atrybutami logów lub spanów, a nie labelami Prometheus.

Brakuje:

- query governor,
- limitu serii,
- limitu punktów,
- timeoutu,
- cache zapytań,
- downsamplingu,
- oznaczenia kosztu zapytania,
- kontroli minimalnego kroku czasowego.

## 1.6. Embedded Grafana nie ma zdefiniowanego modelu bezpieczeństwa

Osadzanie Grafany przez zwykły iframe może wprowadzić:

- niespójne RBAC i ABAC,
- możliwość zmiany tenanta w parametrze URL,
- wyciek dashboardów między tenantami,
- problemy z cookies i SSO,
- clickjacking,
- niespójny audit trail,
- obchodzenie redakcji PII,
- niekontrolowane zapytania do źródeł danych,
- trudności z CSP.

Nie należy przekazywać tokenów dostępowych Grafany w URL ani przechowywać ich w `localStorage`.

Preferowana kolejność:

1. natywne komponenty RAE dla krytycznych workflow,
2. obraz/rendering serwerowy dla paneli tylko do odczytu,
3. bezpieczny iframe przez dedykowany broker,
4. bezpośredni dostęp do Grafany wyłącznie dla administratorów observability.

## 1.7. Brak telemetryki samego RAE-PORTAL

Portal musi obserwować również siebie. Obecny plan koncentruje się na systemach prezentowanych przez portal, ale nie definiuje:

- frontend RUM,
- Web Vitals,
- czasu odpowiedzi interfejsu,
- czasu od kliknięcia do wyniku,
- czasu renderowania tabel,
- utraty eventów WebSocket,
- reconnectów,
- błędów schematu,
- błędów komponentów,
- zużycia pamięci,
- wydajności długich sesji.

Bez tego nie da się stwierdzić, czy problem pochodzi z:

- backendu,
- sieci,
- przeglądarki,
- renderera wykresu,
- Grafany,
- strumienia realtime.

## 1.8. Ryzyko wycieku PII przez telemetrykę frontendową

OTel/RUM może przypadkowo przechwycić:

- treść zapytania wyszukiwarki,
- identyfikatory tenantów,
- `trace_id` i `message_id`,
- fragment payloadu,
- tekst błędu,
- URL z filtrami,
- dane wpisane w formularzu reveal,
- nazwy zasobów.

Dane telemetryczne portalu muszą być redagowane przed eksportem. Nie wolno eksportować:

- pełnych URL-i z query string,
- treści payloadów,
- tekstu zapytań semantycznych bez klasyfikacji,
- wartości odsłoniętych pól PII,
- sekretów lub tokenów.

## 1.9. Brak strategii długiej sesji i zarządzania pamięcią

Command Center może działać przez wiele godzin. Typowe źródła wycieków to:

- niezamknięte subskrypcje WebSocket,
- nieusuwane listenery,
- nieograniczony cache TanStack Query,
- buforowanie wszystkich odebranych zdarzeń,
- zatrzymywanie dużych obiektów przez closures,
- instancje wykresów niewyczyszczone przy unmount,
- niezwolnione obiekty `Blob` i `ObjectURL`,
- wielu workerów na jeden widok.

Plan powinien przewidywać testy typu soak: 2, 8 i 24 godziny.

## 1.10. Brak rozróżnienia pomiędzy opóźnieniem danych i opóźnieniem UI

Operator powinien widzieć oddzielnie:

```text
Event occurred at
Ingested at
Indexed at
Delivered at
Rendered at
```

W przeciwnym razie napis „opóźnienie 4,2 s” jest niejednoznaczny. Może oznaczać opóźnienie:

- emitera,
- kolektora OTel,
- indeksu,
- API,
- WebSocket,
- renderowania przeglądarki.

---

# 2. Szczegółowe poprawki i rozszerzenia UI/UX

## 2.1. Warstwowy model renderowania

Rekomendowana architektura:

```text
RAE-PORTAL Shell
├── Server-rendered auth/context/navigation
├── Lazy-loaded feature routes
├── Client islands
│   ├── Ledger table
│   ├── Search results
│   ├── Trace waterfall
│   ├── Time-series charts
│   └── Knowledge/Mesh graph
├── Shared WebSocket coordinator
├── Web Worker pool
└── Observability adapter
    ├── RAE telemetry API
    ├── Grafana broker
    ├── Prometheus-compatible query API
    └── OTel trace/log correlation API
```

### Zasady

- shell nie może importować bibliotek wykresowych,
- biblioteki grafowe są ładowane dopiero po wejściu do konkretnego widoku,
- każda trasa ma osobny bundle,
- nieaktywne panele nie wykonują odświeżeń,
- ciężkie transformacje trafiają do Workera albo backendu,
- klient nigdy nie parsuje pełnego JSONL.

## 2.2. Execution Ledger — wydajne okno zdarzeń

### Kontrakt komponentu

```typescript
interface VirtualLedgerTableProps {
  query: LedgerQuery;
  pageSize?: 50 | 100 | 200;
  rowHeightMode?: 'compact' | 'comfortable';
  liveMode?: boolean;
  maxBufferedEvents?: number; // np. 500
  onOpenEvent: (eventId: string) => void;
  onQueryCostChange?: (cost: QueryCost) => void;
}
```

### Zachowanie realtime

Nowe zdarzenia nie powinny automatycznie przesuwać tabeli, gdy operator analizuje starszy rekord.

```text
┌─────────────────────────────────────┐
│ 37 nowych zdarzeń                   │
│ [Załaduj] [Włącz automatyczne śledzenie] │
└─────────────────────────────────────┘
```

Wymagania:

- bufor z twardym limitem,
- deduplikacja po `event_id`,
- kolejność po `sequence_no`, nie tylko `timestamp`,
- wykrywanie luk,
- kontrola backpressure,
- pauza przy niewidocznej karcie,
- reset kursora po zmianie filtrów,
- zachowanie pozycji scrolla po prependzie.

### Niedozwolony wzorzec

```typescript
setEvents(previous => [...previous, event]);
```

przy nieograniczonym strumieniu.

Zamiast tego wymagany jest bounded ring buffer albo kontrolowane unieważnienie aktualnego okna.

## 2.3. Trace Waterfall

Trace z tysiącami spanów powinien używać:

- wirtualizowanych wierszy,
- Canvas dla osi czasu,
- DOM tylko dla widocznych etykiet,
- grupowania po service/module,
- zwijania powtarzalnych spanów,
- server-side critical path,
- progressive disclosure.

### Kontrakt

```typescript
interface TraceWaterfallProps {
  traceId: string;
  timeOrigin: string;
  spans: TraceSpanProjection[];
  criticalPath?: string[];
  maxVisibleSpans?: number;
  renderingMode?: 'auto' | 'svg' | 'canvas';
  onSpanSelect: (spanId: string) => void;
}
```

Tryb `auto` powinien dobierać renderer na podstawie liczby spanów i możliwości urządzenia.

## 2.4. Wykresy telemetryczne

### Kanoniczny komponent

```typescript
interface TelemetryTimeSeriesProps {
  queryId: string;                 // identyfikator zapytania zatwierdzonego
  variables: Record<string, string>;
  timeRange: TimeRange;
  refreshPolicy: 'manual' | '15s' | '30s' | '1m';
  maxSeries?: number;
  maxPointsPerSeries?: number;
  preferredRenderer?: 'auto' | 'svg' | 'canvas';
  showTableFallback?: boolean;
  provenance: DataProvenance;
  onOpenInGrafana?: () => void;
}
```

UI nie powinien przyjmować dowolnego PromQL od zwykłego operatora. Preferowany model:

```text
queryId + walidowane variables
```

zamiast:

```text
rawQuery = "sum(rate(...)) by (...)"
```

Zapobiega to kosztownym i nieautoryzowanym zapytaniom.

### Widoczny kontekst wykresu

Każdy panel powinien pokazywać:

- źródło danych,
- zakres czasowy,
- krok agregacji,
- moment aktualizacji,
- opóźnienie ingestu,
- liczbę serii,
- zastosowany downsampling,
- informację o danych częściowych,
- link do trace/logów, jeśli dostępny.

Przykład:

```text
Źródło: Prometheus / rae-prod
Zakres: ostatnie 30 min
Krok: 15 s
Serie: 18/18
Downsampling: średnia 5 s → 15 s
Aktualizacja: 12:04:31 UTC
```

## 2.5. Query Cost Indicator

Przed wykonaniem potencjalnie drogiego zapytania UI powinien prezentować koszt:

```typescript
interface QueryCostIndicatorProps {
  estimatedSeries: number;
  estimatedSamples: number;
  estimatedBytes?: number;
  classification: 'low' | 'moderate' | 'high' | 'blocked';
  reason?: string;
  suggestedResolution?: string;
}
```

Przykładowe zachowanie:

```text
Koszt zapytania: Wysoki
Szacowane próbki: 8,4 mln
Zakres zostanie automatycznie zagregowany do kroku 60 s.
```

Backend pozostaje stroną egzekwującą limity. UI jedynie wyjaśnia decyzję.

## 2.6. Bezpieczny Embedded Grafana

### Rekomendowany model

```text
Browser
  → RAE-PORTAL
    → Grafana Embed Broker
      → Grafana
        → tenant-scoped datasource
```

Broker powinien:

- mapować tożsamość RAE na rolę Grafany,
- wymuszać tenant i środowisko,
- generować krótko żyjące sesje,
- ograniczać listę dashboardów i zmiennych,
- blokować dowolne datasource’y,
- logować otwarcie panelu i eksport,
- usuwać niedozwolone parametry URL,
- nie przekazywać tokenu do kodu aplikacji.

### Kontrakt komponentu

```typescript
interface EmbeddedObservabilityPanelProps {
  dashboardUid: string;
  panelId?: number;
  tenantId: string;
  environment: Environment;
  timeRange: TimeRange;
  variables: Record<string, string>;
  mode: 'interactive' | 'read-only' | 'snapshot';
  fallback: 'native-chart' | 'server-image' | 'message';
}
```

### Wymagane zabezpieczenia

- `sandbox` dla iframe,
- allowlista `frame-src`,
- zakaz tokenów w query string,
- `SameSite` i krótka ważność sesji,
- brak anonimowego dostępu,
- tenant ustalany po stronie serwera,
- synchronizacja czasu przez kontrolowany `postMessage`,
- walidacja `origin` i schematu każdej wiadomości,
- brak ogólnego `allow-same-origin allow-scripts`, jeśli nie jest niezbędny,
- osobny audit event dla otwarcia, drill-down i eksportu.

### UX

Osadzony panel powinien być jawnie oznaczony:

```text
Panel zewnętrzny: Grafana
Dane: production / tenant_a
Ostatnia synchronizacja: 12:04:31 UTC
[Otwórz w Grafanie]
```

Nie może wyglądać jak natywny komponent, jeśli ma inne zasady odświeżania lub dostępu.

## 2.7. OTel w przeglądarce

### Zalecany zakres instrumentacji

Automatycznie:

- navigation timing,
- resource timing z allowlistą,
- Core Web Vitals,
- błędy JavaScript,
- błędy chunk loading,
- czasy kontrolowanych żądań API.

Ręcznie:

- `search.submit`,
- `search.first_result`,
- `ledger.page_loaded`,
- `event.detail_opened`,
- `trace.rendered`,
- `grafana.panel_ready`,
- `websocket.reconnect`,
- `schema.validation_failed`,
- `ui.read_only_mode_enabled`.

### Przykładowy span

```json
{
  "name": "rae.portal.search",
  "attributes": {
    "rae.search.mode": "hybrid",
    "rae.result.count_bucket": "10-49",
    "rae.filter.count": 4,
    "rae.time_range_bucket": "1h-24h",
    "rae.cache.hit": false
  }
}
```

Nie wolno eksportować:

```text
search.query
payload.value
pii.revealed_value
authorization
cookie
raw_url_query
tenant_name
```

Jeżeli potrzebna jest korelacja, należy stosować pseudonimizowane identyfikatory o ograniczonej retencji.

### Sampling

Rekomendacja:

- 100% błędów bezpieczeństwa i naruszeń schematu,
- 100% krytycznych operacji operatorskich w audit trail,
- 5–10% zwykłych trace’ów frontendowych,
- adaptacyjne zwiększanie próbkowania przy anomaliach,
- niezależne kanały dla audytu i telemetryki technicznej.

Audit trail nie może być próbkowany.

## 2.8. Współdzielony koordynator WebSocket

Każdy widget nie powinien otwierać własnego połączenia.

```typescript
interface RealtimeSubscription {
  topic: string;
  tenantId: string;
  environment: Environment;
  filters: RealtimeFilter;
  priority: 'critical' | 'normal' | 'background';
  maxRatePerSecond?: number;
}
```

Koordynator powinien zapewniać:

- jedno połączenie na kartę,
- multipleksowanie tematów,
- heartbeat,
- exponential backoff z jitterem,
- resume token lub sequence number,
- deduplikację,
- kontrolę przepływu,
- limit bufora,
- zawieszanie subskrypcji tła,
- całkowite usunięcie cache po zmianie tenanta,
- renegocjację uprawnień po zmianie sesji.

W przypadku luki:

```text
Utracono 14 zdarzeń między seq=1840 a seq=1855.
Widok został oznaczony jako częściowy.
[Odtwórz brakujący zakres]
```

## 2.9. Query lifecycle i anulowanie żądań

Każda zmiana filtrów musi:

1. anulować poprzednie zapytanie przez `AbortController`,
2. zwiększyć lokalny `request generation`,
3. odrzucić spóźnioną odpowiedź,
4. nie zastępować nowszych danych starszymi.

```typescript
interface QueryExecutionState<T> {
  requestId: string;
  generation: number;
  status: 'queued' | 'running' | 'streaming' | 'complete' | 'cancelled' | 'failed';
  data?: T;
  progress?: number;
}
```

Samo debounce nie rozwiązuje race conditions.

## 2.10. Zarządzanie cache

Cache powinien być klasyfikowany według wrażliwości:

| Klasa | Przykład | Polityka |
|---|---|---|
| Public metadata | nazwy modułów | cache pamięciowy |
| Tenant-scoped | wyniki wyszukiwania | krótki cache, czyszczenie przy zmianie tenanta |
| Sensitive | payload po redakcji | minimalny cache |
| Revealed PII | odsłonięte pole | bez cache |
| Audit action | potwierdzenie operacji | bez cache przeglądarki |

Dodatkowe zasady:

- brak persistencji TanStack Query dla danych wrażliwych,
- brak Service Workera cache’ującego API audytowe,
- `no-store` dla reveal i payloadów,
- usuwanie całego tenant-scoped cache przy wylogowaniu i zmianie kontekstu,
- ograniczone `gcTime`,
- klucze cache zawierające tenant, environment i zakres polityki.

## 2.11. Footprint pakietów frontendowych

### Zasady

- jedna biblioteka wykresowa, nie kilka,
- brak pełnych bibliotek ikon,
- importy per-komponent,
- dynamiczny import edytorów i rendererów grafowych,
- brak Monaco Editor w podstawowym bundle,
- daty przez lekkie API lub natywne `Intl`,
- brak polyfilli dla niewspieranych, przestarzałych przeglądarek,
- automatyczna analiza duplikatów zależności.

### Gate CI

```text
- bundle size diff
- route chunk size
- duplicate package detection
- tree-shaking verification
- source-map inspection
- Web Vitals synthetic test
- memory soak test
```

Merge powinien zostać zablokowany po przekroczeniu budżetu bez jawnego zatwierdzenia.

## 2.12. Tryby jakości i ograniczeń urządzenia

Portal może automatycznie dobrać poziom szczegółowości:

```typescript
type RenderingQuality = 'full' | 'reduced' | 'minimal';
```

Przykłady:

- `full`: Canvas/WebGL, częste odświeżanie,
- `reduced`: mniej punktów i brak animacji,
- `minimal`: tabela zamiast grafu, ręczne odświeżanie.

Zmiana trybu nie może zmieniać znaczenia danych ani ukrywać alarmów. Dotyczy wyłącznie sposobu prezentacji.

## 2.13. Panel diagnostyczny portalu

Dla uprawnionych operatorów warto dodać widok:

```text
Portal Diagnostics
├── wersja UI i schematu API
├── status połączenia
├── RTT do API
├── opóźnienie WebSocket
├── aktywne subskrypcje
├── liczba elementów cache
├── zużycie pamięci, jeśli dostępne
├── status Grafana broker
├── ostatnie schema violations
└── tryb: normal / degraded / read-only
```

Nie może zawierać sekretów, surowych tokenów ani danych innych tenantów.

---

# 3. Rekomendacje z punktu widzenia optymalizacji renderowania, telemetryki, Embedded Grafana/OTel i footprint

## 3.1. Optymalizacja renderowania

### Priorytetowe decyzje

1. **Server-side reduction przed wirtualizacją.**
2. **Canvas dla dużych osi czasu i wykresów.**
3. **WebGL tylko dla rzeczywiście dużych grafów.**
4. **Web Worker dla bezpiecznych transformacji CPU-heavy.**
5. **Brak nieograniczonych list realtime.**
6. **Minimalizacja Client Components i zakresu hydratacji.**
7. **Wyłączanie pracy paneli poza viewportem.**

Nie należy przenosić do Workera surowego PII tylko po to, aby odciążyć główny wątek. Worker nie jest granicą bezpieczeństwa.

## 3.2. Telemetryka RAE-PORTAL

Należy ustanowić osobny zestaw SLI:

| SLI | Znaczenie |
|---|---|
| Search interaction latency | kliknięcie → pierwszy użyteczny wynik |
| Ledger navigation latency | wybór rekordu → szczegół |
| Trace render latency | pobranie → interaktywny waterfall |
| Realtime delivery lag | ingest → odebranie przez UI |
| Realtime render lag | odebranie → render |
| Schema violation rate | odpowiedzi niezgodne z kontraktem |
| Frontend error rate | błędy sesji |
| Memory growth | stabilność długiej sesji |
| Grafana panel readiness | inicjalizacja osadzonego panelu |
| Stale-view duration | czas prezentowania nieaktualnych danych |

Telemetria techniczna, analityka produktu i audit trail muszą być osobnymi strumieniami.

## 3.3. Embedded Grafana

Grafana powinna być narzędziem wspomagającym, a nie podstawą krytycznych workflow:

### Natywnie w RAE-PORTAL

- alarmy wymagające reakcji,
- stan Quality Gate,
- ryzyka R4–R6,
- Execution Ledger,
- trace correlation,
- reveal PII,
- replay,
- akcje audytowe.

### Możliwe do osadzenia z Grafany

- zaawansowane wykresy infrastrukturalne,
- eksploracyjne dashboardy SRE,
- trendy długookresowe,
- metryki eksperymentalne,
- drill-down dla ekspertów observability.

Akcja krytyczna nie może istnieć wyłącznie wewnątrz osadzonego panelu Grafany.

## 3.4. OTel i korelacja

Wspólny model korelacji powinien obejmować:

```text
ui_session_id
ui_action_id
request_id
trace_id
message_id
event_id
search_id
tenant_scope_hash
```

Zasady:

- `ui_session_id` krótko żyjący,
- brak bezpośredniego PII,
- propagacja `traceparent` tylko do zaufanych originów,
- brak nagłówków trace do zewnętrznych CDN i Grafany bez potrzeby,
- kontrolowana retencja,
- jawne oznaczenie źródła: frontend/backend/collector/index.

## 3.5. Footprint i długie sesje

Obowiązkowe testy przed produkcją:

### Test tabeli

- 100 tys. rekordów dostępnych backendowo,
- maks. 100–200 rekordów w pojedynczym oknie,
- ciągły scroll przez 15 minut,
- brak trwałego wzrostu DOM i pamięci.

### Test realtime

- 100 zdarzeń/s przez 60 minut,
- kontrolowane próbkowanie lub agregacja,
- brak nieograniczonego bufora,
- poprawne wykrywanie luk.

### Test trace

- 10 tys. spanów,
- przełączenie Canvas,
- interakcja bez długich blokad głównego wątku.

### Test soak

- sesje 2 h, 8 h i 24 h,
- cykliczna zmiana modułów,
- reconnecty WebSocket,
- zmiana tenanta,
- wielokrotne otwieranie wykresów i Grafany,
- weryfikacja zwolnienia pamięci.

## 3.6. Proponowane rozszerzenia API

### Bezpieczne zapytanie telemetryczne

```http
POST /api/v1/observability/query
```

```json
{
  "query_id": "module_latency_p95",
  "variables": {
    "module": "rae-memory",
    "environment": "production"
  },
  "time_range": {
    "from": "2026-01-01T11:00:00Z",
    "to": "2026-01-01T12:00:00Z"
  },
  "max_series": 50,
  "max_points_per_series": 1000
}
```

Odpowiedź:

```json
{
  "series": [],
  "resolution_ms": 15000,
  "downsampled": true,
  "partial": false,
  "query_cost": {
    "classification": "low",
    "samples_scanned": 184000
  },
  "source_as_of": "2026-01-01T12:00:03Z",
  "applied_policies": [
    "tenant_isolation",
    "series_limit",
    "query_allowlist"
  ]
}
```

### Sesja osadzonej Grafany

```http
POST /api/v1/observability/grafana-sessions
```

```json
{
  "dashboard_uid": "rae-memory-overview",
  "panel_id": 12,
  "tenant_id": "tenant_a",
  "environment": "production",
  "mode": "read-only",
  "time_range": {
    "from": "2026-01-01T11:00:00Z",
    "to": "2026-01-01T12:00:00Z"
  }
}
```

Odpowiedź powinna zawierać krótkotrwały, jednorazowy adres sesji — nigdy stały token.

## 3.7. Kryteria akceptacji

### Renderowanie

- [ ] Tabele używają server-side pagination i wirtualizacji.
- [ ] Zmiana filtra anuluje poprzednie zapytanie.
- [ ] Spóźniona odpowiedź nie nadpisuje nowszego stanu.
- [ ] Wykresy mają limity serii i punktów.
- [ ] Grafy automatycznie przełączają renderer.
- [ ] Nieaktywne panele zatrzymują odświeżanie.
- [ ] Po 8 godzinach sesji nie występuje nieograniczony wzrost pamięci.

### OTel

- [ ] Portal emituje Web Vitals i spany krytycznych interakcji.
- [ ] Telemetria nie zawiera PII ani pełnych query stringów.
- [ ] Audit trail nie jest próbkowany.
- [ ] Rejestrowane są opóźnienia ingest, delivery i render osobno.
- [ ] Propagacja trace jest ograniczona do zaufanych originów.

### Grafana

- [ ] Tenant i environment są wymuszane serwerowo.
- [ ] Tokeny nie trafiają do URL ani `localStorage`.
- [ ] `postMessage` waliduje origin i schemat.
- [ ] Otwarcie i eksport panelu są audytowane.
- [ ] Awaria Grafany nie blokuje natywnych funkcji krytycznych.
- [ ] Osadzone panele mają czytelne oznaczenie źródła.

### Footprint

- [ ] Shell spełnia budżet initial JS.
- [ ] Biblioteki wykresowe są ładowane dynamicznie.
- [ ] CI wykrywa wzrost bundle i duplikaty zależności.
- [ ] Wykonano testy pamięci 2 h, 8 h i 24 h.
- [ ] Cache wrażliwych danych nie jest utrwalany.
- [ ] Zmiana tenanta usuwa cache i subskrypcje poprzedniego kontekstu.

---

# Priorytety wdrożenia

| Priorytet | Działanie |
|---|---|
| **CRITICAL** | Budżety wydajności, query governor i limity cardinality |
| **CRITICAL** | Redakcja telemetryki frontendowej przed eksportem OTel |
| **CRITICAL** | Bezpieczny Grafana Embed Broker z izolacją tenantów |
| **HIGH** | Współdzielony koordynator WebSocket z backpressure |
| **HIGH** | Wirtualizacja połączona z server-side reduction |
| **HIGH** | Memory soak tests dla sesji operatorskich |
| **HIGH** | Rozdzielenie ingest lag, delivery lag i render lag |
| **MEDIUM** | Canvas/WebGL dla trace, grafów i dużych wykresów |
| **MEDIUM** | Query Cost Indicator i jawny downsampling |
| **MEDIUM** | CI bundle budgets oraz analiza duplikatów |
| **MEDIUM** | Panel Portal Diagnostics |

## Konkluzja

RAE-PORTAL powinien być projektowany jako **długotrwale działająca konsola operatorska**, a nie klasyczna aplikacja CRUD. Oznacza to konieczność kontrolowania jednocześnie:

```text
wolumenu danych
+ kosztu zapytań
+ kosztu renderowania
+ pamięci
+ strumieni realtime
+ bezpieczeństwa telemetryki
+ izolacji osadzonych narzędzi
```

Najważniejszym uzupełnieniem planu jest wprowadzenie mierzalnych budżetów i mechanizmów egzekwujących je po obu stronach interfejsu. Wydajność oraz footprint powinny być traktowane jak polityki bezpieczeństwa: **walidowane automatycznie, obserwowalne i domyślnie ograniczone**.


---

## Rekomendacje i Audyt: Fable 5 (Audytowalność ISO 27001/42001 w UI, Interfejs Human-in-the-Loop Approval & Ostateczna Synteza Planu)
# Audyt RAE-PORTAL — Claude
## Domena: Audytowalność ISO 27001/42001 w UI · Human-in-the-Loop Approval · Ostateczna Synteza Planu

> **Pozycjonowanie wobec poprzednich audytów**
> GPT-5.6 Luna Pro zdefiniowała **model obiektów i przepływ operatora**. DeepSeek R1 — **odporność adwersaryjną**. Grok 4.8 — **egzekwowalność przez kontrakty i Design System**. GPT-5.6 Sol — **koszt i obserwowalność samego portalu**.
> Brakuje ostatniej warstwy: **czy to, co portal pokazuje i co operator w nim robi, jest dowodem** — w sensie normatywnym (ISO/IEC 27001:2022, ISO/IEC 42001:2023, AI Act art. 12/14/26) i procesowym (kto zatwierdził, na jakiej podstawie, czy mógł, czy zrozumiał).
> Moja domena obejmuje też **rozstrzygnięcie sprzeczności między czterema audytami** — bez tego plan jest nie do wdrożenia, bo audyty lokalnie się wykluczają (§5).

---

# 1. Analiza braków w obecnym planie

## 1.1. Portal jest projektowany jako narzędzie audytu, ale nie jako **przedmiot** audytu

Cztery audyty traktują RAE-PORTAL jako *okno* na Execution Ledger. Tymczasem z chwilą, gdy operator może w nim wykonać `reveal PII`, `replay`, `unblock quality gate` — portal staje się **systemem przetwarzania o wysokim ryzyku**, który sam podlega audytowi.

Konsekwencje pominięte w planie:

| [PERSON_NAME] | [PERSON_NAME] |
|---|---|
| Audit trail UI [PERSON_NAME] w [PERSON_NAME] tej samej domenie zaufania co portal | [PERSON_NAME] portalu może modyfikować dowody własnych działań |
| Brak WORM/append-only sink poza kontrolą aplikacji | ISO 27001 A.5.33, A.8.34 niespełnione |
| Brak wersjonowania polityk dostępu | Nie da się odtworzyć, *[PERSON_NAME] wolno* było zobaczyć operatorowi w [PERSON_NAME] T |
| [PERSON_NAME] „portal read-only appliance” dla audytora zewnętrznego | Audytor otrzymuje konto operatora → naruszenie [PERSON_NAME] uprawnień |

## 1.2. Brak modelu Human-in-the-Loop — „four-eyes” pojawia się jako **wzmianka**, nie jako **maszyna stanów**

GPT-5.6 wymienia zasadę czterech oczu dla pięciu akcji. To niewystarczające. Brakuje:

- obiektu `ApprovalRequest` jako **first-class citizen** modelu domenowego,
- separacji obowiązków (SoD): [PERSON_NAME], zatwierdzający, wykonujący, weryfikujący,
- zakazu self-approval **i** zakazu zatwierdzania akcji własnego agenta (właściciel agenta ≠ neutralny recenzent),
- delegacji, zastępstw, nieobecności, wygasania uprawnień,
- SLA, eskalacji, timeoutów i **domyślnego zachowania po timeout** (fail-closed vs auto-deny),
- odwołania zgody (revocation) przed wykonaniem,
- rozróżnienia `approval` (zgoda na wykonanie) od `attestation` (poświadczenie faktu) od `acknowledgement` (przyjęcie do wiadomości) — trzy różne skutki prawne, w planie zlane w jedno.

## 1.3. Konflikt nierozpoznany: **redakcja PII vs. świadoma decyzja człowieka**

To najpoważniejsza luka konceptualna całego planu.

Wszystkie audyty wymagają maskowania PII przed dotarciem do UI. Jednocześnie plan wymaga, by człowiek zatwierdzał akcje krytyczne. Powstaje sprzeczność:

```text
Jeśli operator zatwierdza akcję, widząc payload zredagowany do "[MASKED]",
to jego zgoda nie jest zgodą świadomą (informed).
Audytor zapyta: "Na jakiej podstawie zatwierdzono?"
Odpowiedź "widziałem [MASKED]" jest niedopuszczalna dla R5/R6.
```

Plan nie definiuje **decision-sufficient disclosure** — minimalnego zakresu informacji wystarczającego do decyzji, przy zachowaniu minimalizacji danych (ISO 27001 A.8.11, ISO 42001 A.7).

## 1.4. Brak taksonomii przyczyn (reason codes)

Pola `reason: "Analiza przyczyny incydentu INC-123"` (GPT/DeepSeek) to **free text**. Free text jest nieanalizowalny: nie da się policzyć, ile revealów wykonano „w celu obsługi żądania podmiotu danych” vs „debug”. Bez kontrolowanego słownika:

- brak raportowalności dla przeglądu zarządzania (ISO 42001 kl. 9.3),
- brak wykrywania nadużyć wzorcowych,
- brak podstawy prawnej przetwarzania per akcja (RODO art. 6/9 — a reveal PII to przetwarzanie).

## 1.5. Brak „dowodowej” jakości eksportu

GPT proponuje eksport asynchroniczny z metadanymi. To eksport **operacyjny**, nie **dowodowy**. Brakuje:

- manifestu z hashami każdego pliku,
- podpisu organizacji (nie użytkownika) + znacznika czasu z zaufanego źródła,
- snapshotu **polityki dostępu i wersji schematu** w momencie eksportu,
- chain of custody (kto wygenerował, kto pobrał, ile razy, kiedy wygasa),
- deklaracji kompletności/niekompletności („eksport zawiera 1 240 z 1 262 rekordów; 22 wyłączone przez `tenant_isolation`”),
- odtwarzalnego renderu widoku (auditor: „pokaż mi to, co widział operator”).

## 1.6. Brak gwarancji negatywnej („czego nie widzę”)

Portal audytowy, który cicho odfiltrowuje wyniki przez polityki dostępu, **kłamie przez pominięcie**. GPT słusznie żąda „polityka przed rankingiem”, DeepSeek słusznie żąda „brak wycieku metadanych w błędach”. Te dwa wymagania są w napięciu i plan tego nie rozstrzyga:

```text
Wariant A: "Znaleziono 12 wyników"              → operator nie wie, że 40 ukryto (kłamstwo przez pominięcie)
Wariant B: "Znaleziono 12; 40 ukryto (tenant_b)" → wyciek istnienia tenant_b i wolumenu
```

## 1.7. Brak modelu retencji, legal hold i usuwania — przy jednoczesnym wymogu niezmienności ledgera

Plan wymaga hash chain i niezmienności (GPT §3.2) oraz „retencji i polityki usuwania” w jednym zdaniu. To fizycznie sprzeczne bez projektu kryptograficznego. Brak:

- crypto-shredding / tokenizacji z osobnym key store,
- rekordu „tombstone” zachowującego hash i metadane przy usuniętym payloadzie,
- UI dla legal hold (blokada usunięcia mimo upływu retencji),
- obsługi żądań podmiotów danych (DSR) w UI z powiązaniem do rekordów ledgera,
- wyświetlenia stanu: `retained / expiring / legal-hold / crypto-shredded / tombstoned`.

## 1.8. Brak fail-closed na niedostępność audit sink

Nigdzie nie zdefiniowano zachowania portalu, gdy **log audytowy jest niedostępny**. Domyślnie systemy pozwalają działać dalej (fail-open) — to dyskwalifikuje audytowalność: powstaje okno działań bez śladu.

## 1.9. Brak zaufanego źródła czasu jako kontroli dowodowej

Sol wspomina clock drift wyłącznie w kontekście WebSocket. Ale timestamp w zdarzeniu audytowym **jest dowodem**. ISO 27001 A.8.17 (synchronizacja zegarów) wymaga:

- jednego autorytatywnego źródła czasu dla ledgera,
- rozróżnienia `client_reported_at` (niezaufany) od `server_recorded_at` (zaufany) — w planie występuje jeden `timestamp`,
- widocznego statusu synchronizacji i blokady akcji krytycznych przy drifcie.

## 1.10. Brak modelu kompetencji i autoryzacji personalnej

ISO 27001 A.6.3 + ISO 42001 kl. 7.2: osoba sprawująca nadzór nad AI musi być **kompetentna**. Plan przypisuje uprawnienia rolom, ale nie wiąże ich z:

- potwierdzonym przeszkoleniem (ważność, wygaśnięcie),
- zakresem autoryzacji dla poziomu ryzyka (`R5+` wymaga innej kwalifikacji niż `R2`),
- rejestrem, kto zatwierdził nadanie uprawnienia (a to również akcja wymagająca 4 oczu).

## 1.11. Brak rozróżnienia sprawstwa: AI proposes, human disposes

GPT wprowadza `provenance` dla *danych*. Brakuje analogicznego modelu dla *decyzji*:

```text
Kto zaproponował?   agent / LLM / reguła / człowiek
Kto zatwierdził?    człowiek / autonomia (Autonomy Kernel) / brak (auto)
Kto wykonał?        system / człowiek
Kto zweryfikował?   człowiek / test / nikt
```

Bez tego nie da się odpowiedzieć na kluczowe pytanie AI Act art. 14 i ISO 42001: **gdzie kończy się autonomia systemu, a zaczyna odpowiedzialność człowieka**.

## 1.12. Brak rejestru niezgodności (nonconformity) i działań korygujących

Portal zbiera incydenty operacyjne, ale nie **niezgodności z SZBI/SZAI**. Te dwa obiekty są różne: incydent = zdarzenie operacyjne; niezgodność = naruszenie wymagania normy/polityki. ISO 42001 kl. 10.1–10.2 i ISO 27001 kl. 10 wymagają rejestru CAPA. Bez niego audyt certyfikacyjny nie ma czym się karmić.

## 1.13. Brak artefaktów dla przeglądu zarządzania i audytu wewnętrznego

ISO 42001 kl. 9.2/9.3 wymaga wejść do audytu wewnętrznego i przeglądu zarządzania. Plan generuje dane, ale nie **raporty zgodności**: pokrycie kontrolami, skuteczność nadzoru, statystyki HITL, trendy niezgodności.

## 1.14. Brak metryk **jakości nadzoru ludzkiego**

Portal mierzy latencję systemu, nie mierzy jakości człowieka w pętli. Brakuje wykrywania:

- rubber-stamping (zatwierdzenie w 1,2 s od otwarcia payloadu 40 kB),
- approval fatigue (spadek override rate przy wzroście wolumenu),
- koncentracji zatwierdzeń u jednej osoby (ryzyko SoD),
- ślepych plamek (alarmy `R4+` nigdy nieotwierane).

To bezpośrednio wymagane przez ISO 42001 (skuteczność nadzoru musi być monitorowana, a nie założona).

---

# 2. Szczegółowe poprawki i rozszerzenia UI/UX

## 2.1. Rozszerzenie nawigacji — trzy nowe filary

```text
Overview
├── Command Center
├── Execution Ledger
├── Global Search
├── Agents & Mesh
├── Quality Tribunal
├── Memory Explorer
├── Kaizen Observatory
├── Phoenix & CLR
├── Incidents
├── ▸ Approval Center          ← NOWE (HITL, kolejki, SoD, break-glass)
├── ▸ Evidence & Conformity    ← NOWE (paczki dowodowe, integralność, mapa kontroli, CAPA)
└── ▸ Audit & Access
    └── ▸ Auditor Mode         ← NOWE (osobna powłoka read-only, time-boxed)
```

## 2.2. `ApprovalRequest` jako obiekt domenowy + maszyna stanów

```text
                 ┌──────────────┐
   utworzenie →  │   DRAFT      │
                 └──────┬───────┘
                        │ submit (z reason_code + evidence bundle)
                 ┌──────▼───────┐   expire (SLA)   ┌──────────┐
                 │ PENDING      ├─────────────────►│ EXPIRED  │ (fail-closed = deny)
                 │ (1st review) │                  └──────────┘
                 └──┬────────┬──┘
          approve   │        │ reject / request-info
                    │        └────────────────► REJECTED / INFO_REQUIRED
        ┌───────────▼──────────┐
        │ PENDING_SECOND       │  (tylko R4–R6 / akcje na liście dual-control)
        │ (SoD: inny człowiek, │
        │  inna sesja, inny MFA)│
        └───────┬──────────────┘
                │ approve (2nd)
        ┌───────▼──────────┐  revoke (przed exec)  ┌──────────┐
        │ APPROVED         ├──────────────────────►│ REVOKED  │
        │ (ważne do T+ttl) │                       └──────────┘
        └───────┬──────────┘
                │ execute (idempotency_key)
        ┌───────▼──────────┐        ┌──────────────┐
        │ EXECUTING        ├───────►│ FAILED       │
        └───────┬──────────┘        └──────────────┘
        ┌───────▼──────────┐
        │ EXECUTED         │
        └───────┬──────────┘
                │ post-verification (obowiązkowa dla break-glass i R5+)
        ┌───────▼──────────┐
        │ VERIFIED         │  ← dopiero ten stan zamyka ścieżkę audytową
        └──────────────────┘
```

**Zasady twarde:**

| Zasada | Egzekucja |
|---|---|
| `requester_id ≠ approver_id` | backend, 409 `self_approval_forbidden` |
| `approver_id ∉ owners(target_agent)` | backend, ABAC |
| Drugi zatwierdzający: inna tożsamość, **osobna sesja**, świeży MFA (`< 120 s`) | backend + UI step-up |
| Zgoda ma TTL (domyślnie 15 min dla `R5+`) | `approved_until` w kontrakcie |
| Timeout = **deny**, nigdy allow | polityka `on_timeout: "deny"` |
| Wykonanie bez `approval_id` niemożliwe | API zwraca `428 Precondition Required` |

## 2.3. Kontrakty komponentów (Design System — rozszerzenie pakietu Grok 4.8)

### `<ApprovalGate />` — brama akcji krytycznej

```typescript
interface ApprovalGateProps {
  action: PrivilegedAction;              // 'pii.reveal' | 'event.replay' | 'gate.unblock' | ...
  targetRef: ResourceRef;
  riskLevel: RiskLevel;
  policy: ApprovalPolicy;                // z serwera, NIE z kodu FE
  children: (ctx: GateContext) => ReactNode;
}

interface ApprovalPolicy {
  mode: 'none' | 'single' | 'dual-control' | 'break-glass-only';
  requiredRoles: string[];
  requireStepUp: boolean;
  minReviewSeconds: number;              // anty-rubber-stamp (patrz 2.12)
  requiredDisclosures: string[];         // pola, które MUSZĄ być odsłonięte przed zgodą
  reasonCodeSet: string;                 // id słownika
  ttlSeconds: number;
  onTimeout: 'deny';                     // literal — brak innej opcji w typie
}
```

> **Fail-closed by default (rozwinięcie zasady Grok 4.8):** jeśli `policy` jest `undefined`, `null` lub nierozpoznane, komponent renderuje akcję jako **niedostępną** z komunikatem „Polityka zatwierdzania niedostępna — akcja zablokowana”. Nigdy nie degraduje do `mode: 'none'`.

### `<ReasonCodePicker />` — kontrolowany słownik + uzasadnienie

```typescript
interface ReasonCodePickerProps {
  reasonCodeSet: string;
  value?: { code: string; freeText?: string; ticketId?: string };
  requireTicket?: boolean;
  requireFreeTextMinChars?: number;      // np. 40 dla R5+
  legalBasisRequired?: boolean;          // RODO art. 6/9 dla reveal PII
  onChange: (v: ReasonSelection) => void;
}
```

Taksonomia bazowa (`reason_code_set: rae.core.v1`):

| Kod | Znaczenie | Wymaga ticketu | Podstawa prawna |
|---|---|---|:---:|
| `INC_RCA` | Analiza przyczyny źródłowej incydentu | ✔ | uzasadniony interes |
| `DSR_ACCESS` | Realizacja żądania podmiotu danych | ✔ | obowiązek prawny |
| `DSR_ERASURE` | Realizacja żądania usunięcia | ✔ | obowiązek prawny |
| `REG_AUDIT` | Audyt regulacyjny / certyfikacyjny | ✔ | obowiązek prawny |
| `INT_AUDIT` | Audyt wewnętrzny SZBI/SZAI | ✔ | uzasadniony interes |
| `SEC_INVEST` | Postępowanie bezpieczeństwa | ✔ | uzasadniony interes |
| `QUALITY_DISPUTE` | Weryfikacja odwołania od decyzji Quality Tribunal | ✔ | uzasadniony interes |
| `MODEL_EVAL` | Ocena jakości modelu / kalibracja | ✔ | uzasadniony interes |
| `OPS_DEBUG` | Diagnostyka operacyjna | ✖ | **niedozwolone dla PII wysokiej wrażliwości** |
| `BREAK_GLASS` | Awaryjny dostęp poza procedurą | ✔ | wymaga przeglądu post-hoc |

Zakaz: `OPS_DEBUG` nie jest dopuszczalnym reason code dla `pii.reveal` na danych szczególnych kategorii — walidacja **backendowa**, nie tylko UI.

### `<DecisionSufficiencyPanel />` — rozwiązanie konfliktu z §1.3

Zamiast wyboru „maska albo pełny payload”, wprowadzam **trzeci tryb: ujawnienie decyzyjne**.

```typescript
interface DecisionSufficiencyPanelProps {
  approvalId: string;
  disclosures: Disclosure[];
  onDisclosureOpened: (fieldPath: string) => void;   // audytowane pojedynczo
}

interface Disclosure {
  fieldPath: string;
  purpose: string;                 // DLACZEGO to pole jest potrzebne do tej decyzji
  form:
    | { kind: 'derived'; label: string; value: string }   // "PESEL: poprawny format, region: 14, wiek: 41"
    | { kind: 'partial'; masked: string }                  // "***-***-**91"
    | { kind: 'match-proof'; matches: boolean }            // "wartość identyczna z INC-123: TAK"
    | { kind: 'full'; requiresDualControl: true };
  required: boolean;               // czy zgoda jest niemożliwa bez otwarcia
  openedAt?: string;
}
```

**Wzorzec:** operator w 90% przypadków nie potrzebuje wartości PII — potrzebuje **predykatu o wartości**. `match-proof` i `derived` pozwalają podjąć świadomą decyzję **bez ujawnienia danych**, co spełnia jednocześnie minimalizację (A.8.11) i świadomą zgodę (AI Act art. 14). Pełne odsłonięcie (`full`) jest ścieżką wyjątkową z dual-control.

### `<IntegrityBadge />` — weryfikowalność rekordu w UI

```typescript
interface IntegrityBadgeProps {
  recordRef: string;
  chainStatus: 'verified' | 'unverified' | 'broken' | 'gap-detected' | 'tombstoned';
  verifiedAt?: string;
  anchor?: { type: 'internal' | 'external-tsa' | 'transparency-log'; ref: string };
  sequenceNo?: number;
  onVerifyNow?: () => Promise<VerificationResult>;
}
// Renderuje: tekst + ikona + wzór (bez oparcia na kolorze) + tooltip z hashem skróconym.
// 'broken' / 'gap-detected' → wymusza baner na poziomie widoku, nie tylko badge.
```

### `<EvidencePackageDialog />` — eksport dowodowy

```typescript
interface EvidencePackageRequest {
  scope: { savedSearchId?: string; query?: SearchQuery; recordRefs?: string[] };
  purpose: ReasonSelection;               // wymagane
  includeRawPayloads: boolean;            // domyślnie false; true ⇒ dual-control
  includeRenderedViews: boolean;          // snapshot widoku (patrz 2.7)
  redactionProfile: 'audit-standard' | 'regulator-full' | 'internal-minimal';
  recipient: { type: 'internal' | 'external-auditor' | 'regulator'; identityRef: string };
  expiresInHours: number;                 // maks. 168
}
```

### `<AutonomyOversightIndicator />` — materializacja Autonomy Kernel w UI

```typescript
interface AutonomyOversightIndicatorProps {
  currentLevel: 'L0' | 'L1' | 'L2' | 'L3' | 'L4';  // L0 = tylko człowiek, L4 = pełna autonomia
  scope: { tenantId: string; environment: Environment; module?: string };
  authorizedBy: ActorRef;
  authorizedAt: string;
  expiresAt?: string;
  degradedReason?: string;                 // dlaczego kernel obniżył autonomię
  humanOverrideAvailable: boolean;
  onRequestOverride?: () => void;          // → ApprovalGate
}
```

Pasek kontekstowy portalu (Grok §2.1) rozszerzam o **poziom autonomii i tryb nadzoru** — operator musi zawsze wiedzieć, czy system działa sam, czy czeka na niego.

### `<ControlMappingTag />` — chip kontroli normatywnej

```typescript
interface ControlMappingTagProps {
  frameworks: Array<{
    framework: 'ISO27001:2022' | 'ISO42001:2023' | 'AI_ACT' | 'INTERNAL';
    controlId: string;                   // 'A.8.15', 'A.6.2.6', 'Art.14'
    status: 'evidence-available' | 'partial' | 'not-applicable';
  }>;
  compact?: boolean;
}
// Umieszczany na widokach i eksportach: audytor widzi, JAKI dowód ma przed sobą.
```

## 2.4. Approval Center — układ widoku

```text
┌─ Approval Center ─────────────────────────────────────────────────────────┐
│ [Do mojej decyzji: 3]  [Moje wnioski: 1]  [Break-glass review: 1]  [Log]  │
├───────────────────────────────────────────────────────────────────────────┤
│ ⚠ APR-2291 · pii.reveal · payload.customer.pesel                          │
│   Risk: R5 (Very High) ▨  Wnioskujący: op.kowalski (Tier-2)               │
│   Powód: DSR_ACCESS · ticket DSR-882 · podstawa: obowiązek prawny         │
│   Wymagane ujawnienia: 2/2 otwarte ✔   Min. czas przeglądu: 60 s (42 s)   │
│   SLA decyzji: 12 min 08 s  ·  Po upływie: ODMOWA (fail-closed)           │
│   Dual-control: wymagane · Ty byłbyś 1. z 2                               │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │ [Podgląd decyzyjny]  [Historia obiektu]  [Trace]  [Ledger]        │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│   [ Zatwierdź (wymaga MFA) ]  [ Odmów ]  [ Poproś o informacje ]          │
│   ℹ Twoja decyzja zostanie podpisana i nie może być usunięta.             │
└───────────────────────────────────────────────────────────────────────────┘
```

Elementy obowiązkowe w każdej karcie: poziom ryzyka (tekst+ikona+wzór), reason code, wymagane ujawnienia z licznikiem, SLA z jawnym skutkiem upływu, informacja o SoD, ostrzeżenie o nieusuwalności decyzji.

## 2.5. Break-glass — kontrolowany wyjątek

Bez break-glass ludzie obchodzą system (wspólne konta, kopie danych). Z break-glass bez kontroli — nie ma audytowalności. Model:

```typescript
interface BreakGlassRequest {
  justification: string;                  // min. 120 znaków
  reasonCode: 'BREAK_GLASS';
  incidentRef: string;                    // wymagane
  scope: { resourceRefs: string[]; maxDurationMinutes: 15 | 30 | 60 };
  notifyImmediately: ActorRef[];          // security officer + tenant DPO — nienegocjowalne
  postReviewDueWithinHours: 24;
}
```

Zachowanie UI:

- **czerwony, trwały baner sesji**: „BREAK-GLASS AKTYWNY · APR-2299 · wygasa 12:41 UTC · wszystkie akcje rejestrowane rozszerzenie”,
- automatyczne 100% samplowanie telemetrii (nadpisuje politykę Sol §2.7),
- automatyczne utworzenie **niezgodności** w rejestrze CAPA (nie incydentu — niezgodności),
- blokada zamknięcia karty bez wypełnienia raportu podsumowującego,
- kolejka `Break-glass review` z SLA 24 h i eskalacją do właściciela SZBI.

## 2.6. Anty-rubber-stamping — bez dark patterns

| Mechanizm | Uzasadnienie | Granica etyczna |
|---|---|---|
`minReviewSeconds` przed aktywacją „Zatwierdź” | dowód realnego przeglądu | 15 s dla R3, 60 s dla R5+, **nigdy dla akcji odmowy** — odmowa musi być natychmiast możliwa |
Wymóg otwarcia `required: true` disclosures | świadoma zgoda | licznik widoczny, brak ukrytych warunków |
Rejestracja `time_to_decision`, `disclosures_opened`, `scroll_depth` | metryka nadzoru | **agregaty**, nie inwigilacja indywidualna; retencja 90 dni |
Alert przy `p50 time_to_decision < minReview × 1.2` w kohorcie | wykrycie fatygi | raport do przeglądu zarządzania, nie do przełożonego |

> Nie stosujemy „quizów zrozumienia” ani sztucznych opóźnień na odmowie. Nadzór nie może być karą za korzystanie z nadzoru.

## 2.7. Odtwarzalny widok dowodowy (`ViewStateSnapshot`)

Kluczowe rozszerzenie: audytor musi móc zobaczyć **dokładnie to, co widział operator w chwili decyzji**, nie „to samo zapytanie dzisiaj”.

```json
{
  "view_state_id": "vs_01HQ...",
  "created_at": "2026-01-01T12:04:31.412Z",
  "actor_id": "op.kowalski",
  "route": "/ledger/evt_123",
  "url_state": { "filters": {...}, "time_range": {...}, "tenant": "tenant_a" },
  "data_as_of": "2026-01-01T12:04:29.100Z",
  "index_generation": 48213,
  "policy_version": "policy-2025.12.03",
  "redaction_profile": "operator-tier2",
  "ui_version": "portal-3.14.2",
  "api_schema_version": "v1.7.0",
  "rendered_digest": "sha256:9f2c...",
  "disclosures_opened": ["payload.customer.pesel#match-proof"],
  "content_ref": "obj://evidence/vs_01HQ.../render.json"
}
```

Realizuje wprost postulat Grok o deep-linkingu, ale podnosi go do rangi dowodu: deep-link odtwarza **dane historyczne + politykę historyczną**, nie stan bieżący. Każda decyzja HITL automatycznie tworzy `ViewStateSnapshot` i wiąże go z `approval_id`.

## 2.8. Panel integralności ledgera (Evidence & Conformity)

```text
Ledger Integrity
├── Hash chain: VERIFIED do seq=1 842 019 (ostatnia weryfikacja 12:00:04 UTC)
├── Luki w sekwencji: 1 wykryta  → seq 1 840 → 1 855 (14 zdarzeń)   ▨ GAP
│     Status: WYJAŚNIONA (INC-771, utrata połączenia kolektora)
├── Zakotwiczenie zewnętrzne: RFC 3161 TSA, ostatnie 12:00:05 UTC
├── Rekordy tombstoned: 42 (crypto-shredded, integralność zachowana)
├── Legal hold: 3 zakresy aktywne
├── Źródło czasu: NTP stratum 2, drift 3 ms  ✔
└── [Uruchom weryfikację]  [Eksportuj dowód integralności]
```

**Zasada:** wykryta i niewyjaśniona luka w sekwencji **musi** blokować wystawianie paczek dowodowych obejmujących ten zakres, z jawnym komunikatem — nie cichym pominięciem.

## 2.9. Cykl życia danych: retencja, legal hold, usunięcie

Rozstrzygnięcie sprzeczności „niezmienność vs usuwanie”:

```text
Rekord ledgera = [ metadane niezmienne ] + [ payload szyfrowany kluczem per-subject ]

Usunięcie (DSR_ERASURE):
  1. odnalezienie kluczy podmiotu (key store, oddzielny od ledgera)
  2. crypto-shred klucza  → payload nieodwracalnie nieodczytywalny
  3. zapis TOMBSTONE do ledgera (nowe zdarzenie, hash chain nieprzerwany)
  4. metadane, hashe i trace_id pozostają → audytowalność zachowana
  5. reindeksacja: usunięcie z indeksu FTS i wektorowego (osobne potwierdzenie!)
```

Komponent `<RetentionLifecycleBadge />` — stany: `retained` · `expiring-in-Nd` · `legal-hold` · `shred-pending` · `tombstoned` · `reindex-pending`.

> **Nieoczywisty wymóg:** indeks wektorowy jest osobnym miejscem przetwarzania. Usunięcie z ledgera bez usunięcia embeddingu = niezgodność. UI musi pokazywać `reindex-pending` do potwierdzenia z obu indeksów.

## 2.10. Rejestr niezgodności i CAPA

```text
Nonconformity NC-2026-014
├── Źródło: automatyczne (schema_violation × 37 w 15 min)
├── Naruszone wymaganie: ISO 27001 A.8.15 · polityka RAE-LOG-002
├── Powiązania: INC-771 · APR-2299 (break-glass) · trace_456
├── Klasyfikacja: major / minor / observation
├── Analiza przyczyn: [wypełniona przez: q.nowak, 2026-01-02]
├── Działanie korygujące: CAPA-88 (właściciel, termin, status)
├── Weryfikacja skuteczności: [oczekuje na 2026-02-01]
└── Wejście do przeglądu zarządzania: 2026-Q1 ✔
```

**Reguła automatyzacji:** wybrane zdarzenia generują niezgodność **obligatoryjnie**, bez decyzji operatora: użycie break-glass, `chainStatus: 'broken'`, `schema_violation` na polu PII, reveal bez zgody, wykonanie akcji przy niedostępnym audit sink.

## 2.11. Auditor Mode — osobna powłoka

| Cecha | Wartość |
|---|---|
Uprawnienia | wyłącznie odczyt; **żadna** mutacja nie jest renderowana (nie „disabled”, ale nieobecna) |
Zakres | zdefiniowany w mandacie audytowym: tenant, okno czasu, typy obiektów |
Czas | time-boxed, twarde wygaśnięcie sesji, brak przedłużenia bez nowego zatwierdzenia |
PII | domyślnie `restricted`; reveal wyłącznie przez dual-control z udziałem DPO |
Eksport | tylko `EvidencePackage` z manifestem; brak CSV ad-hoc |
Ślad | 100% akcji audytora rejestrowane i **widoczne dla audytowanego** (transparentność dwustronna, ISO 27001 A.8.34) |
Odizolowanie | osobny bundle, osobny origin, brak dostępu do WebSocket kanałów operacyjnych |

## 2.12. Fail-closed na audit sink + zaufany czas

```typescript
type AuditSinkHealth = 'healthy' | 'degraded' | 'unavailable';

// Reguła egzekwowana na backendzie, odzwierciedlona w UI:
// unavailable  → wszystkie akcje uprzywilejowane zablokowane (428/503 z kodem 'audit_sink_unavailable')
// degraded     → dozwolone R0–R2, blokada R3+
// clockDrift > 2000 ms → blokada wszystkich akcji wymagających approval
```

Baner systemowy: *„Rejestr audytowy niedostępny. Akcje uprzywilejowane zablokowane, aby zachować ciągłość śladu audytowego. Odczyt danych pozostaje dostępny.”* — komunikat wyjaśnia **dlaczego**, co redukuje presję na obejścia.

## 2.13. Rozstrzygnięcie gwarancji negatywnej (§1.6)

Wprowadzam **trójstopniową politykę ujawniania pominięć**, konfigurowalną per tenant:

| Tryb | Komunikat | Zastosowanie |
|---|---|---|
`transparent` | „12 wyników · 40 ukrytych przez politykę: `role_scope`” | wewnątrz jednego tenanta, gdzie liczność nie jest wrażliwa |
`aggregate` | „12 wyników · część rekordów wyłączona przez polityki dostępu” — bez liczby | domyślny, cross-scope |
`opaque` | „12 wyników” + `applied_policies` w metadanych odpowiedzi, bez informacji o pominięciach | konteksty o skrajnej wrażliwości (np. tenant o klauzuli) |

Warunki twarde:
- niezależnie od trybu, **`applied_policies` zawsze obecne w odpowiedzi API** i widoczne w UI jako chip „Wyniki filtrowane politykami: 3”,
- tryb `opaque` **musi być udokumentowany** jako świadome ograniczenie audytowalności i zaakceptowany przez właściciela ryzyka,
- w `EvidencePackage` deklaracja kompletności jest **obowiązkowa zawsze** (audytor dostaje informację, że eksport nie jest pełny, nawet gdy operator jej nie widzi).

## 2.14. Dostępność i język dowodu

Rozszerzenie do wymagań Grok/GPT (WCAG 2.2 AA):

- każda karta zatwierdzenia ma **pełne podsumowanie tekstowe** czytelne dla czytnika ekranu, w jednym `aria-describedby` (nie rozproszone po tabeli),
- `role="alertdialog"` dla dual-control i break-glass, focus trap, brak zamykania przez `Esc` bez potwierdzenia porzucenia,
- **dwujęzyczność dowodów**: `EvidencePackage` generowany z etykietami PL i EN, ponieważ odbiorcą może być organ krajowy i jednostka certyfikująca; wersja językowa jest częścią manifestu,
- brak animacji i auto-refresh w Approval Center — treść decyzji nie może się zmienić pod ręką operatora (jeśli obiekt się zmienił: `412` + jawny komunikat, zgodnie z DeepSeek §2.5).

---

# 3. Kontrakty API (rozszerzenie OpenAPI 3.1)

```http
POST   /api/v1/approvals                          # utworzenie wniosku
GET    /api/v1/approvals?queue=to-decide|mine|break-glass-review
POST   /api/v1/approvals/{id}/decide               # zatwierdzenie / odmowa
POST   /api/v1/approvals/{id}/revoke
POST   /api/v1/approvals/{id}/execute              # wymaga X-Idempotency-Key
POST   /api/v1/approvals/{id}/verify               # post-verification
GET    /api/v1/approvals/{id}/policy               # polityka z serwera (fail-closed w UI)

POST   /api/v1/evidence-packages
GET    /api/v1/evidence-packages/{id}/manifest
GET    /api/v1/integrity/ledger/verify?from_seq=&to_seq=
POST   /api/v1/view-states                         # snapshot widoku dowodowego
GET    /api/v1/view-states/{id}/replay             # odtworzenie widoku z polityką historyczną

GET    /api/v1/conformity/control-coverage         # mapa kontroli ISO
POST   /api/v1/nonconformities
GET    /api/v1/oversight/metrics                   # metryki jakości HITL (agregaty)
GET    /api/v1/system/audit-sink-health
```

### `POST /api/v1/approvals/{id}/decide`

```json
{
  "decision": "approve",
  "reason": { "code": "DSR_ACCESS", "ticket_id": "DSR-882", "free_text": "...", "legal_basis": "legal_obligation" },
  "attestation": {
    "statement": "Zapoznałem się z zakresem ujawnienia i potwierdzam zasadność akcji.",
    "disclosures_opened": ["payload.customer.pesel#match-proof"],
    "view_state_id": "vs_01HQ...",
    "time_to_decision_ms": 61420
  },
  "step_up": { "method": "webauthn", "assertion_ref": "auth_9f2c", "verified_at": "2026-01-01T12:04:29Z" },
  "idempotency_key": "b2f0-..."
}
```

Nagłówki wymagane: `If-Match` (ETag wniosku), `X-Idempotency-Key`.

Odpowiedzi błędów (spójne z ujednoliconym schematem DeepSeek/Grok):

| Kod | `code` | Znaczenie |
|---|---|---|
`409` | `self_approval_forbidden` | naruszenie SoD |
`409` | `approver_conflict_of_interest` | zatwierdzający jest właścicielem obiektu/agenta |
`412` | `stale_approval_state` | wniosek zmieniony (ETag mismatch) |
`422` | `disclosure_requirements_unmet` | nieotwarte wymagane ujawnienia |
`422` | `min_review_time_not_elapsed` | anty-rubber-stamp |
`423` | `locked_by_concurrent_decision` | wyścig zatwierdzeń |
`428` | `second_approval_required` | brak drugiej zgody |
`503` | `audit_sink_unavailable` | fail-closed |

### Zdarzenie audytowe (rozszerzenie modelu GPT-5.6)

Do listy pól GPT dodaję jako **wymagane**:

```json
{
  "approval_id": "APR-2291",
  "reason_code": "DSR_ACCESS",
  "legal_basis": "legal_obligation",
  "view_state_id": "vs_01HQ...",
  "policy_version": "policy-2025.12.03",
  "client_reported_at": "2026-01-01T12:04:31.100Z",
  "server_recorded_at": "2026-01-01T12:04:31.412Z",
  "clock_skew_ms": 312,
  "decision_provenance": {
    "proposed_by": "llm:rae-lab/gpt-x",
    "approved_by": "human:op.kowalski",
    "executed_by": "system:rae-phoenix",
    "verified_by": "human:q.nowak"
  },
  "control_refs": ["ISO27001:A.8.15", "ISO42001:A.6.2.6", "AI_ACT:Art.14"],
  "sequence_no": 1842019,
  "prev_hash": "sha256:...",
  "record_hash": "sha256:..."
}
```

---

# 4. Rekomendacje domenowe

## 4.1. Mapowanie funkcji portalu na kontrole (mapowanie orientacyjne — do potwierdzenia z jednostką certyfikującą)

| Funkcja RAE-PORTAL | ISO/IEC 27001:2022 | ISO/IEC 42001:2023 | AI Act |
|---|---|---|---|
Execution Ledger + hash chain | A.5.33, A.8.15 | kl. 7.5, A.6.2.6 | art. 12 |
Zaufany czas, drift monitor | A.8.17 | — | art. 12 |
Redakcja PII, maskowanie | A.8.11, A.5.34 | A.7 | — |
Reveal z 4 oczami | A.8.2, A.8.3, A.5.15–5.18 | A.9.2 | — |
Approval Center / HITL | A.5.3 (SoD), A.8.2 | A.3, A.9.2 | **art. 14** |
Autonomy Level Indicator | — | A.6.2.6, A.9.4 | art. 14, 26 |
Data provenance / decision provenance | A.8.15 | A.7.4, A.8 | art. 13 |
Evidence Package + manifest | A.5.28, A.5.33 | kl. 7.5 | art. 12, 26 |
Auditor Mode | A.8.34 | kl. 9.2 | — |
Nonconformity / CAPA | kl. 10 | kl. 10.1–10.2 | — |
Oversight metrics | A.8.16 | kl. 9.1, 9.3 | art. 14(4) |
Retencja, crypto-shred, tombstone | A.8.10, A.5.31 | A.7.2 | — |
Kompetencje operatorów | A.6.3 | kl. 7.2 | art. 26(2) |
Impact assessment linkage | — | **A.5** (AI system impact assessment) | art. 27 (FRIA) |

> Rekomendacja: umieścić tę tabelę jako **żywy artefakt** w module `Evidence & Conformity` (widok `Control Coverage`), z automatycznym wskaźnikiem „czy dla kontroli X istnieje w systemie zapytanie zwracające dowód”. Audyt certyfikacyjny przechodzi się wtedy klikając, nie pisząc dokumenty.

## 4.2. Siedem zasad Human-in-the-Loop dla RAE-PORTAL

1. **Nadzór musi być możliwy, nie tylko formalny.** Człowiek nie może zatwierdzać tego, czego nie może zrozumieć — dlatego `DecisionSufficiencyPanel` jest warunkiem koniecznym, nie ozdobą.
2. **Zgoda jest zawsze na konkretny zakres i czas.** Brak zgód „ogólnych”, brak zgód bez TTL.
3. **Timeout znaczy odmowa.** Nigdy cisza jako zgoda.
4. **Sprawstwo jest rozdzielone i jawne.** Propozycja ≠ zatwierdzenie ≠ wykonanie ≠ weryfikacja.
5. **Odmowa jest tańsza niż zgoda.** Ścieżka „nie” musi być natychmiastowa i wolna od friction — inaczej system optymalizuje w stronę zgody.
6. **Wyjątek jest zaprojektowany.** Break-glass istnieje, jest ograniczony, natychmiast alarmowany i obowiązkowo rozliczany.
7. **Jakość nadzoru jest mierzona.** Nadzór, którego skuteczności nie mierzymy, jest tylko rytuałem — a rytuał nie jest kontrolą.

## 4.3. Domyślne progi nadzoru (propozycja polityki startowej)

| Poziom | Akcje | Tryb | Step-up | Min. review | TTL zgody |
|---|---|---|:---:|---:|---:|
`R0–R1` | odczyt, filtrowanie, saved search | brak | ✖ | — | — |
`R2` | eksport bez PII, acknowledge alarmu | single (self) | ✖ | — | — |
`R3` | reveal PII niskiej wrażliwości, replay pojedynczego zdarzenia | single (inny człowiek) | ✔ | 15 s | 30 min |
`R4` | replay masowy (≤100), eksport z PII, unblock quality gate (non-prod) | dual-control | ✔ | 30 s | 15 min |
`R5` | reveal danych szczególnych kategorii, wyłączenie Circuit Breaker | dual-control + DPO | ✔ | 60 s | 15 min |
`R6` | zmiana polityki autonomii, unblock quality gate (prod), replay masowy >100 | dual-control + właściciel ryzyka | ✔ | 90 s | 10 min |

---

# 5. Ostateczna synteza — rejestr konfliktów między audytami i rozstrzygnięcia

To sekcja krytyczna: bez niej zespół otrzymuje cztery wzajemnie sprzeczne specyfikacje.

| # | Konflikt | Stanowiska | **Rozstrzygnięcie** |
|---|---|---|---|
**C1** | Architektura renderowania | Grok: RSC-first · Sol: RSC to nie panaceum | **Sol ma rację.** RSC dla shell, polityk, metadanych i widoków read-only; client islands dla ledger table, trace waterfall, wykresów, realtime. RSC **nie jest** kontrolą PII — kontrolą jest warstwa polityk w API. |
**C2** | WebSockets | DeepSeek: segmentacja kanałów per risk (`/low-risk`, `/high-risk`) · Sol: jedno współdzielone połączenie | **Synteza:** jedno połączenie na kartę (footprint), ale **autoryzacja per subskrypcja** z `riskCeiling` wymuszanym serwerowo i osobnymi kluczami redakcji per topic. Segmentacja logiczna, nie transportowa. Wyjątek: kanał `break-glass`/`security` = osobne połączenie (izolacja awaryjna). |
**C3** | Ryzyko w rankingu wyszukiwania | GPT: nie promować krytycznych zdarzeń tylko za wysoki risk · plan: `w_risk` w scoringu | **GPT ma rację, z korektą:** `w_risk` pozostaje, ale wyłącznie jako **tie-breaker** przy zbliżonej relevance (Δscore < 5%) oraz jako osobna, jawnie oznaczona sekcja „Wysokie ryzyko w zakresie zapytania (N)”. Nigdy jako mnożnik relevance. |
**C4** | Komunikaty błędów | DeepSeek: zero metadanych w błędach · GPT: operator musi rozumieć, dlaczego nie widzi danych | **Rozdzielenie kanałów:** treść błędu bez metadanych zasobu + `request_id`; **uzasadnienie polityki** dostarczane osobnym, autoryzowanym endpointem `GET /api/v1/access-explanations/{request_id}` widocznym tylko dla uprawnionych. Plus polityka ujawniania pominięć z §2.13. |
**C5** | Niezmienność ledgera vs. usuwanie danych | GPT: immutability + retencja i usuwanie w jednym zdaniu | **Crypto-shredding + tombstone** (§2.9). Metadane i hash chain nietykalne; payload usuwalny przez zniszczenie klucza; obowiązkowe potwierdzenie deindeksacji FTS **i** wektorowej. |
**C6** | Redakcja PII vs. świadoma zgoda HITL | nierozpoznane w żadnym audycie | **`DecisionSufficiencyPanel`** — predykaty i wartości pochodne zamiast surowego PII; pełne odsłonięcie tylko przez dual-control. |
**C7** | Sampling telemetrii | Sol: 5–10% trace’ów frontendowych | **Uzupełnienie:** audit trail 0% samplowania (Sol zgadza się), **plus** 100% dla sesji break-glass, wszystkich akcji `R4+` i wszystkich odmów zatwierdzenia (odmowy są szczególnie cennym dowodem skuteczności nadzoru). |
**C8** | Grafana embedded | Sol: możliwa dla dashboardów eksploracyjnych | **Zgoda + twardy zakaz:** żadna akcja podlegająca zatwierdzeniu, żaden dowód wchodzący do `EvidencePackage` i żaden wskaźnik zgodności nie może pochodzić z osadzonego panelu. Grafana = warstwa eksploracyjna, nigdy dowodowa. |
**C9** | Min. czas przeglądu vs. INP < 200 ms (budżet Sol) | pozorny konflikt | **Rozdzielenie:** budżet responsywności dotyczy **UI**; `minReviewSeconds` dotyczy **procesu decyzyjnego**. Przycisk musi reagować natychmiast — pokazując licznik pozostałego czasu, nie zamrażając interfejsu. |
**C10** | Deep-linking (Grok) vs. brak wycieku przez URL/telemetrię (Sol/DeepSeek) | konflikt realny | **Deep-link zawiera wyłącznie `view_state_id` lub opaque `search_id`**, nigdy zapytania, tenantów ani ID zasobów w query string. Rozwiązanie stanu po stronie serwera z kontrolą dostępu. To jednocześnie realizuje odtwarzalność dowodową (§2.7). |

---

# 6. Zunifikowana roadmapa (synteza czterech audytów)

## Etap 0 — Fundament niepodlegający negocjacji *(brak = brak MVP)*

| # | Element | Właściciel audytu |
|---|---|---|
0.1 | Kanoniczny schemat zdarzenia + `sequence_no` + hash chain + `server_recorded_at` | GPT / Claude |
0.2 | OpenAPI 3.1 jako single source of truth + generowany klient z runtime validation | Grok |
0.3 | Model uprawnień RBAC+ABAC, izolacja tenantów, wersjonowanie polityk | GPT / Claude |
0.4 | PII redaction service **przed** indeksowaniem i przed WebSocket | GPT / DeepSeek |
0.5 | Audit sink append-only poza domeną zaufania portalu + **fail-closed** | **Claude** |
0.6 | Design tokens R0–R6 + redaction states, fail-closed defaults | Grok |
0.7 | Zaufane źródło czasu + monitor driftu | **Claude** |
0.8 | Taksonomia reason codes + `ApprovalPolicy` serwowana z backendu | **Claude** |

## Etap 1 — MVP operacyjne z audytowalnością

Command Center · Execution Ledger Explorer (server-side reduction + wirtualizacja) · exact + full-text search · filtry wielowymiarowe walidowane backendowo · trace detail · `<RedactedField>` · `<SafeJSONViewer>` · `<RiskBadge>` · **Approval Center (single + dual-control)** · **`ViewStateSnapshot`** · eksport asynchroniczny bez PII · budżety CI (bundle, axe, size).

## Etap 2 — Warstwa dowodowa i odpornościowa

`EvidencePackage` z manifestem i podpisem · panel integralności ledgera · **break-glass z przeglądem post-hoc** · Auditor Mode · współdzielony koordynator WebSocket z backpressure i resume · query governor + Query Cost Indicator · Grafana Embed Broker · redakcja telemetrii frontendowej · `<FreshnessIndicator>` + rozdzielenie ingest/delivery/render lag · memory soak 2/8/24 h.

## Etap 3 — Inteligencja i zgodność systemowa

Indeks wektorowy + hybrid ranking (z C3) · semantic query explanations · `DataProvenanceTag` · **rejestr niezgodności i CAPA** · **Control Coverage view** · **oversight metrics + wykrywanie rubber-stamping** · retencja/legal hold/crypto-shred UI · Canvas/WebGL dla grafów i trace.

## Etap 4 — Zaawansowane

Replay masowy z dual-control · live topology A2A/Mesh · predykcja degradacji · automatyczne grupowanie incydentów · rekomendacje Kaizen · pełna automatyzacja wejść do przeglądu zarządzania.

---

# 7. Lista zakazów twardych *(„nigdy nie wolno wdrożyć”)*

Rekomenduję umieszczenie tej listy w `CONTRIBUTING.md` i jako reguły lintera/CI:

1. Akcja uprzywilejowana wykonana bez `approval_id` (poza `mode: 'none'` z jawnej polityki serwerowej).
2. Zapis `reveal`, `replay`, `unblock` przy `audit_sink != healthy`.
3. Samozatwierdzenie lub zatwierdzenie przez właściciela obiektu docelowego.
4. Timeout zgody interpretowany jako zgoda.
5. Surowe PII w: embeddingu, telemetrii OTel, `sessionStorage`/`localStorage`, URL, logach FE, komunikatach błędów.
6. Token Grafany w URL, `localStorage` lub kodzie klienta.
7. Akcja krytyczna dostępna wewnątrz osadzonego panelu zewnętrznego.
8. Eksport bez deklaracji kompletności.
9. Wystawienie paczki dowodowej dla zakresu z niewyjaśnioną luką w sekwencji.
10. Usunięcie danych z ledgera bez potwierdzonej deindeksacji FTS **i** wektorowej.
11. `dangerouslySetInnerHTML` w dowolnej ścieżce renderującej dane z ledgera.
12. Domyślne zachowanie komponentu PII inne niż `restricted` przy nieznanym stanie.
13. Retroaktywna modyfikacja lub usunięcie zdarzenia audytowego akcji operatorskiej — również przez administratora.
14. Sampling audit trailu.

---

# 8. Kryteria akceptacji (uzupełnienie do MVP)

## Human-in-the-Loop

- [ ] `ApprovalRequest` istnieje jako obiekt z pełną maszyną stanów i historią.
- [ ] Samozatwierdzenie i konflikt interesu blokowane **backendowo** (test: 409).
- [ ] Drugi zatwierdzający wymaga innej tożsamości, innej sesji i świeżego MFA.
- [ ] Timeout zgody skutkuje odmową; udokumentowane testem.
- [ ] Odmowa dostępna natychmiast, bez `minReviewSeconds`.
- [ ] Każda zgoda wiąże `view_state_id`, `reason_code`, `disclosures_opened`, `time_to_decision_ms`.
- [ ] Break-glass: alarm natychmiastowy, automatyczna niezgodność, przegląd w 24 h.
- [ ] Zgoda ma TTL; wykonanie po wygaśnięciu niemożliwe (test: 412/428).

## Audytowalność

- [ ] Audit sink niedostępny ⇒ akcje uprzywilejowane zablokowane (test chaos).
- [ ] `client_reported_at` i `server_recorded_at` rozdzielone; drift > 2 s blokuje approvale.
- [ ] Hash chain weryfikowalny z UI; luka blokuje eksport dowodowy.
- [ ] `EvidencePackage` zawiera manifest, hashe, podpis organizacji, snapshot polityki, deklarację kompletności.
- [ ] `view_state_id` odtwarza widok z **historyczną** polityką i danymi as-of.
- [ ] Auditor Mode: brak mutacji w DOM, time-boxed, ślad widoczny dwustronnie.
- [ ] Każdy widok raportuje `control_refs` w eksporcie.

## Zgodność i nadzór

- [ ] Reason code z kontrolowanego słownika; `OPS_DEBUG` odrzucany dla danych szczególnych kategorii.
- [ ] Reveal wymaga podstawy prawnej dla klas PII objętych RODO art. 9.
- [ ] Widok `Control Coverage` zwraca dowód dla każdej zmapowanej kontroli.
- [ ] Niezgodności generowane automatycznie dla 5 zdefiniowanych zdarzeń.
- [ ] Metryki nadzoru raportowane jako agregaty z retencją 90 dni.
- [ ] `DSR_ERASURE` potwierdza deindeksację FTS i wektorową przed zamknięciem.

---

# 9. Konkluzja — czym naprawdę jest RAE-PORTAL

Cztery poprzednie audyty zbudowały odpowiedź na pytanie GPT-5.6: *„Co się wydarzyło, jak ważne, kto odpowiada, kto może to zobaczyć i na jakiej podstawie?”*

Moja domena dodaje pytanie o rząd wyższe — to, które zada audytor i organ nadzoru:

> **Kto pozwolił, czy mógł pozwolić, czy rozumiał, na co pozwala — i czy potrafisz to udowodnić po dwóch latach, gdy tej osoby już nie ma w organizacji, a schemat danych zmienił się trzy razy?**

Z tego wynika jedna decyzja architektoniczna, która przewyższa wszystkie pozostałe:

**`ApprovalRequest` i `ViewStateSnapshot` nie są funkcjami UI. Są rekordami Execution Ledger.**

Decyzja człowieka jest zdarzeniem w tym samym niezmiennym, hashowanym, wersjonowanym strumieniu co decyzja agenta. Nadzór ludzki przestaje być warstwą nad systemem, a staje się jego pierwszorzędnym obywatelem — z tą samą integralnością, prowenancją i odtwarzalnością.

To przesuwa RAE-PORTAL z pozycji **„panelu obserwacyjnego fabryki agentycznej”** na **„rejestr sprawstwa systemu autonomicznego”**. Pierwsze jest wygodą operacyjną. Drugie jest warunkiem, by fabryka agentyczna mogła legalnie działać w reżimie ISO 42001 i AI Act — i by w razie sporu organizacja miała czym się bronić.

Jeśli mam kontynuować, najwyższą wartość dodaną przyniosłoby teraz jedno z dwóch:
- **pełna specyfikacja OpenAPI 3.1 dla domeny `/approvals`, `/evidence-packages` i `/view-states`** (gotowa do generacji klienta i handlerów), albo
- **matryca dowodowa ISO 27001 + ISO 42001 → zapytanie w RAE-PORTAL → artefakt** — dokument, którym przechodzi się audyt certyfikacyjny bez pisania załączników.
