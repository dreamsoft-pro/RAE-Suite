# RAE-Suite — Finalny Iteracyjny Plan Dopasowania (Wersja Zatwierdzona Konsensusem)

**Status:** ZATWIERDZONY (konsensus Claude Fable 5 × GPT-5.6 Sol)
**Klasyfikacja:** Dokumentacja produkcyjna — zgodność ISO 27001 / ISO 42001
**Język obowiązujący:** polski (kod, schematy i identyfikatory pozostają w formie kanonicznej — angielskiej)
**Zasada nadrzędna:** Zero-Drift — niniejszy dokument jest jedynym źródłem prawdy (Single Source of Truth) dla planu dopasowania RAE-Suite.

---

## 0. Nadrzędne Zasady RAE (niezmienne, obowiązujące we wszystkich iteracjach)

| Zasada | Definicja operacyjna |
|---|---|
| **Zero-Drift** | Żaden kontrakt, schemat, polityka ani prompt nie może zmienić się bez jawnej wersji, podpisu i bramki CI. Dryf środowiska, polityki lub planu **natychmiast unieważnia** wyniki spekulatywne i zatwierdzenia. |
| **RAE-First** | Walidacja, autoryzacja i egzekwowanie kontraktów następują **przed** jakimkolwiek efektem ubocznym, wywołaniem modelu lub wykonaniem spekulatywnym. Odrzucenie deterministyczne zawsze poprzedza kosztowną ocenę. |
| **Kontrakty Bezpieczeństwa (Security Contracts)** | Każda granica (API, worker, sandbox, model gateway) posiada jawny, wersjonowany, egzekwowany maszynowo kontrakt. Pola wrażliwe są wykluczone **konstrukcyjnie**, nie konwencją. |
| **Nazwane Wektory (Named Vectors)** | Każdy wektor zagrożenia posiada stały identyfikator (`V-xx`), właściciela, kontrolę mitygującą oraz test regresyjny. Wektor bez testu nie jest uznawany za zmitygowany. |
| **Exactly-Once Effects** | Gwarantujemy dokładnie-jednokrotny **efekt**, nie dokładnie-jednokrotne dostarczenie. Poprawność zapewniają klucze idempotencji, ograniczenia unikalności i transakcyjne przejścia stanów — nigdy sam broker ani blokada Redis. |
| **Dual-Write / Dual-Enforcement** | Poprawność chroniona jest równolegle w dwóch warstwach: baza danych (constraints, wersjonowanie, fencing) oraz warstwa aplikacyjna (Pydantic, Rego, FSM). Awaria jednej warstwy nie może osłabić drugiej. |

---

## 1. Decyzje Architektoniczne (obowiązujące bezwarunkowo)

### 1.1 Kanoniczne schematy przewodowe, oddzielne modele runtime
- **Protobuf** jest kanonicznym schematem komunikacji międzyserwisowej (wire schema).
- Z definicji Protobuf generujemy lub walidujemy:
  - rygorystyczne modele żądań Pydantic,
  - jawne DTO odpowiedzi Pydantic,
  - typy domenowe i adaptery.
- **Zakaz bezwzględny:** eksponowanie obiektów Protobuf lub modeli persystencji SQLAlchemy bezpośrednio przez FastAPI.
- Modele ORM mogą być generowane tam, gdzie to bezpieczne, ale ograniczenia bazodanowe i relacje pozostają jawnymi migracjami/modelami.

### 1.2 Ścisłe granice (Strict Boundaries)
```text
DTO żądania API  →  komenda domenowa   →  encja persystencji
encja persystencji →  wynik domenowy   →  DTO odpowiedzi API
```
Pola wrażliwe — `jti`, sygnatury, surowe `graph_data`, tokeny zdolności (capability tokens), wewnętrzne hashe — są wykluczone **konstrukcyjnie** (brak pól w DTO), a nie przez filtrowanie.

### 1.3 Jawne wersjonowanie
- Prefiks `/v1` wprowadzamy **przed** włączeniem `extra="forbid"`.
- Zmiany `/v2` wyłącznie przez adaptery translacyjne.
- `buf breaking` oraz diff kompatybilności OpenAPI są **obowiązkowymi bramkami CI**.

### 1.4 Exactly-once effects, nie exactly-once delivery
- Celery + Redis = dostarczenie co-najmniej-raz (at-least-once).
- Widoczne dla użytkownika zachowanie dokładnie-raz osiągamy przez: utrwalone klucze idempotencji, ograniczenia unikalności, transakcyjne przejścia stanów, deterministyczne ponowne użycie wyniku.

---

## 2. ITERACJA 1 — Architektura, Kontrakty, FSM i Model Zagrożeń

**Cel:** Ustanowić wersjonowane kontrakty, granice domenowe, semantykę stanów i budżety operacyjne, zanim powstanie jakikolwiek kod wykonawczy.

### 2.1 Instrukcje krok po kroku

**Krok 1 — Inwentaryzacja architektury**
1. Sporządź ADR (Architecture Decision Record) dla każdego komponentu: API, planner, silnik polityk, trybunał, workery, Redis, PostgreSQL, sandbox, bramki modeli.
2. Przypisz jawnego właściciela każdemu kontraktowi i każdej tabeli persystencji. Kontrakt bez właściciela blokuje merge.

**Krok 2 — Kanoniczne definicje typów**
1. Zdefiniuj komunikaty międzyserwisowe w Protobuf.
2. Zdefiniuj **zamknięte** enumy (Protobuf enum lub Python `StrEnum`) dla:
   - stanu zadania (task state),
   - ryzyka narzędzia (tool risk),
   - wyniku przejścia (transition outcome),
   - klasyfikacji ponowień (retry classification).
3. Nigdy nie używaj ponownie usuniętych numerów pól Protobuf — oznaczaj je `reserved`.

**Krok 3 — Rygorystyczna walidacja na krawędzi (RAE-First)**
1. Wszystkie modele żądań Pydantic v2:
   ```python
   ConfigDict(extra="forbid", strict=True)
   ```
2. Ogranicz na granicy API: dodatnie wersje, ograniczone głębokości, budżety tokenów, TTL, hashe, wagi.
3. Obsłuż jawnie obecność skalarów proto3: `optional`, typy wrapper lub adaptery świadome obecności pola.

**Krok 4 — Oddzielne DTO odpowiedzi**
1. Każda trasa FastAPI deklaruje `response_model=`.
2. Decyzja o `response_model_exclude_none` jest jawna i udokumentowana per trasa.
3. Napisz testy bezpieczeństwa weryfikujące, że pola wewnętrzne **nie mogą** pojawić się w serializowanych odpowiedziach.

**Krok 5 — Maszyna stanów (FSM)**
1. Zdefiniuj legalne przejścia i stany terminalne.
2. Utrzymaj rozdzielność `APPROVED` i `COMPLETED` — to odrębne stany o odrębnej semantyce.
3. Każde przejście zawiera:
   - `graph_version`,
   - termin przejścia (transition deadline),
   - klucz idempotencji,
   - klasyfikację awarii/ponowienia,
   - akcję kompensacyjną.
4. `/v1` mapuje `APPROVED` i `COMPLETED` na `legacy_done` tam, gdzie wymagane.

**Krok 6 — Model zagrożeń z Nazwanymi Wektorami**

| ID | Wektor | Kontrola pierwotna |
|---|---|---|
| **V-01** | Replay i przeterminowane zatwierdzenia | JWT: `jti`, `exp`, wiązanie do hashy planu/diffu |
| **V-02** | Dostęp międzytenantowy (cross-tenant) | `tenant_id` w każdym constraincie i kluczu cache |
| **V-03** | Ucieczka z sandboxa | nsjail, seccomp, AppArmor/SELinux, testy regresyjne |
| **V-04** | Rozproszona awaria częściowa | sagi, kompensacje idempotentne, deadliny |
| **V-05** | Utrata blokady Redis/PostgreSQL | fencing tokens, poprawność w DB |
| **V-06** | Wygłodzenie puli połączeń (pool starvation) | separacja pul API/workery, budżet połączeń |
| **V-07** | Prompt injection | pakiety dowodowe, referencje przez hash, sanityzacja |
| **V-08** | Wyciek wrażliwych DTO | wykluczenie konstrukcyjne, testy serializacji |
| **V-09** | Nieograniczona konsumpcja zasobów MCTS/ToT | budżety węzłów/tokenów/czasu (Iteracja 4) |

Każdy wektor `V-xx` musi posiadać: właściciela, kontrolę, test regresyjny w CI.

**Krok 7 — Bramki kompatybilności w CI**
1. `buf breaking` względem poprzedniego schematu produkcyjnego.
2. Diff żądań/odpowiedzi OpenAPI.
3. Weryfikacja migracji w modelu expand → migrate → contract.
4. Reguły wdrażania nowych claimów JWT (optional-then-required, patrz Iteracja 5).

### 2.2 Kryteria akceptacji (Iteracja 1)
- [ ] Nieprawidłowe enumy, zerowe wersje grafu, nieskończone floaty i nieznane pola żądań odrzucane **na krawędzi**.
- [ ] Żaden endpoint nie serializuje bezpośrednio obiektu ORM ani persystencyjnego Protobuf.
- [ ] Bramki kompatybilności są wymaganymi kontrolami CI.
- [ ] Każdy wektor V-01…V-09 ma przypisany test regresyjny.

---

## 3. ITERACJA 2 — Persystencja, Współbieżność i Praca w Tle

**Cel:** Trwałe snapshoty oraz idempotentne, izolowane zasobowo przetwarzanie asynchroniczne.

### 3.1 Instrukcje krok po kroku

**Krok 1 — Schemat snapshotów**
```sql
CREATE TABLE graph_snapshots (
    snapshot_id   UUID PRIMARY KEY,
    tenant_id     UUID NOT NULL,
    graph_version BIGINT NOT NULL CHECK (graph_version > 0),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_at      TIMESTAMPTZ NOT NULL,
    content_hash  BYTEA NOT NULL,
    graph_data    JSONB NOT NULL,
    UNIQUE (tenant_id, content_hash),
    UNIQUE (tenant_id, graph_version)
);
```
Przechowuj algorytm/wersję hasha **lub** standaryzuj długość `content_hash`, aby wykluczyć niejednoznaczne kodowania (Zero-Drift na poziomie danych).

**Krok 2 — Współbieżność**
1. Krótkie transakcje + optymistyczne sprawdzenia wersji.
2. `SERIALIZABLE` tylko dla przepływów, które tego wymagają; benchmarkuj względem atomowego zapisu warunkowego pod `READ COMMITTED`:
   ```sql
   UPDATE task_graphs
   SET graph_version = graph_version + 1, ...
   WHERE tenant_id = :tenant_id
     AND graph_version = :expected_version
   RETURNING graph_version;
   ```
3. Ponawiaj SQLSTATE `40001` i deadlocki z ograniczonym wykładniczym backoffem z jitterem.
4. Rozróżniaj wyniki (mapowanie kontraktowe, nie ad hoc):
   - nieaktualna oczekiwana wersja → `409 Conflict`,
   - duplikat treści już utrwalonej → zwróć/ponownie użyj istniejącego snapshotu, jeśli idempotentne,
   - wyczerpanie ponowień serializacji → `409` z metadanymi retry lub `503` przy przeciążeniu bazy.
5. `ON CONFLICT DO NOTHING` **musi** inspekcjonować `RETURNING`/liczbę wierszy — zero wierszy nie może być ślepo traktowane jako udany insert.

**Krok 3 — Izolacja pul połączeń**
1. Oddzielne poświadczenia i pule DB dla API i Celery.
2. Wymiaruj pule względem budżetu połączeń bazy — nigdy nie kopiuj stałych wartości:
   ```text
   total = repliki_API × limit_puli_API
         + procesy_workerów × limit_puli_workera
         + rezerwa migracje/beat/admin
   ```
3. Preferuj PgBouncer w trybie transaction pooling dla licznych krótkich transakcji.
4. **Zakaz:** trzymanie połączenia DB podczas oczekiwania na LLM, blokadę Redis lub sandbox.
5. Zweryfikuj kompatybilność advisory locks z poolingiem:
   - advisory locks PostgreSQL są zakresu sesji (chyba że transakcyjne),
   - lider beat używający blokady sesyjnej wymaga dedykowanego, niepoolowanego połączenia — albo blokady transakcyjnej z kompatybilnym projektem elekcji.

**Krok 4 — Niezawodność Celery**
1. `acks_late=True`, `task_reject_on_worker_lost=True`.
2. Utrwalaj stan idempotencji w PostgreSQL: klucz unikalny + transakcyjny UPSERT.
3. Ustaw spójnie limity soft/hard zadań oraz visibility timeout brokera (visibility timeout > hard limit + istotny margines).
4. Elekcja lidera beat oddzielona od wykonywania zadań workerów.
5. Testy weryfikują **exactly-once effect**, nie exactly-once delivery brokera.

**Krok 5 — Batching (na podstawie audytu wydajności)**
1. Cele odpowiednie do batchowania: embeddingi, scoring trybunału (ten sam model/schemat), inserty snapshotów, persystencja telemetrii, inwalidacje cache, jednorodne lekkie ewaluacje polityk. **Nie** batchuj heterogenicznych zadań długich z krótkimi.
2. Polityka podwójnych progów:
   ```text
   flush gdy item_count >= N
   lub oldest_item_age >= T
   lub estimated_tokens >= model_batch_limit
   ```
3. Punkty startowe (do benchmarkowania): batche DB/eventów 50–500 wierszy lub 25–100 ms; embeddingi 8–64 elementy lub 10–50 ms; batche sędziów LLM — małe, z rygorystycznym grupowaniem po deadlinach. **Nigdy** nie łącz w jednym batchu zadań o istotnie różnych deadlinach.
4. Konfiguracja workerów:
   - zadania długie/kosztowne: `worker_prefetch_multiplier=1`, niska współbieżność procesów, dedykowane kolejki,
   - zadania krótkie jednorodne: umiarkowanie wyższy prefetch **po pomiarze**; unikaj dużego prefetchu (ukrywa pracę w buforach lokalnych i psuje fairness),
   - zapisy DB: multi-row insert lub `COPY`; krótkie transakcje; nie trzymaj połączenia podczas gromadzenia batcha.
5. Retry: ponawiaj pojedyncze elementy; przy ponowieniu całego batcha każdy element zachowuje własny klucz idempotencji; dodaj jitter przeciw zsynchronizowanym falom retry.
6. Zadania długie dziel na checkpointy zamiast polegać na ekstremalnie dużych visibility timeout.

### 3.2 Kryteria akceptacji (Iteracja 2)
- [ ] Zabicie workera po efekcie ubocznym, lecz przed potwierdzeniem, **nie duplikuje efektu**.
- [ ] Ruch API zachowuje zarezerwowaną pojemność DB przy saturacji workerów.
- [ ] Wszystkie oczekiwane konflikty mają udokumentowane odpowiedzi inne niż 500.
- [ ] Batching poprawia przepustowość **bez** naruszania SLO opóźnienia kolejki (mierz wiek kolejki, nie długość).

---

## 4. ITERACJA 3 — Silnik Polityk i Sandboxing

**Cel:** Egzekwowanie zamkniętych zdolności (capabilities) **przed** jakimkolwiek wykonaniem spekulatywnym (zasada RAE-First).

### 4.1 Instrukcje krok po kroku

**Krok 1 — Zamknięta klasyfikacja narzędzi**
Zdefiniuj `PURE_READ_ONLY`, `ENVIRONMENT_OBSERVING`, `STATE_MUTATING` jako **zamknięty enum**. Nieznana klasyfikacja nie może się zdeserializować.

**Krok 2 — Autoryzacja**
Autoryzuj narzędzia przez Rego oraz krótkotrwałe, związane z audiencją (audience-bound) tokeny zdolności.

**Krok 3 — Izolacja wykonania**
Uruchamiaj narzędzia w `nsjail` lub równoważnej izolacji:
- system plików tylko-do-odczytu,
- minimalne zamontowane ścieżki,
- limity procesów i pamięci,
- allowlist seccomp,
- sieć domyślnie wyłączona,
- konfinacja AppArmor/SELinux.

**Krok 4 — Ograniczenie spekulacji**
Wykonanie spekulatywne ogranicz **wyłącznie** do `PURE_READ_ONLY`. Żadna gałąź spekulatywna nie może uzyskać poświadczeń mutujących stan.

**Krok 5 — Fingerprint środowiska**
Rejestruj fingerprint środowiska przed i po istotnych operacjach (podstawa inwalidacji Zero-Drift w Iteracji 4).

**Krok 6 — Mapowanie awarii (Kontrakt Bezpieczeństwa)**
| Awaria | Status |
|---|---:|
| odmowa capability / odmowa seccomp | `403` |
| timeout sandboxa | `504` lub retriable `503` |
| zniekształcone ciało żądania API | `422` |

### 4.2 Kryteria akceptacji (Iteracja 3)
- [ ] Nieznane klasyfikacje narzędzi nie mogą się zdeserializować.
- [ ] Żadna gałąź spekulatywna nie może uzyskać poświadczeń mutujących stan.
- [ ] Fuzzing polityk sandboxa i testy regresji ucieczki (wektor **V-03**) przechodzą w CI.

---

## 5. ITERACJA 4 — Planowanie Kognitywne, Wyszukiwanie Spekulatywne i Trybunał

**Cel:** Ograniczone (bounded) plany kandydackie z atomową persystencją i przewidywalnym kosztem, następnie deterministyczne kontrole przed ograniczonym, niezależnym osądem.

### 5.1 Część A — Planowanie i wyszukiwanie spekulatywne (MCTS/ToT)

**Krok 1 — Atomowa persystencja**
Utrwalaj kandydatów, oceny ryzyka, metadane modelu/wersji i rozliczenie tokenów **atomowo** (all-or-nothing).

**Krok 2 — Walidacja budżetów na krawędzi**
```python
token_budget: Annotated[int, Field(ge=0, le=MAX_TOKEN_BUDGET)]
depth:        Annotated[int, Field(ge=0, le=MAX_DEPTH)]
```
Używaj całkowitoliczbowego rozliczania tokenów z tokenizera modelu lub konserwatywnego estymatora całkowitego.

**Krok 3 — Niezależne limity globalne (wektor V-09)**
Egzekwuj równolegle: maks. węzły, maks. głębokość, budżet tokenów wejścia/wyjścia, maks. równoległe wywołania modeli, maks. wywołania narzędzi, deadline zegarowy (wall-clock), limity CPU i pamięci.

**Krok 4 — Poprawna egzekucja deadline’ów**
**Nie** używaj `SIGXCPU` jako timeoutu zegarowego — limituje on wyłącznie CPU. Stosuj deadline aplikacyjny + terminację procesu/kontenera dla czasu rzeczywistego.

**Krok 5 — Kontrola eksplozji drzewa**
Dla współczynnika rozgałęzienia `b` i głębokości `d` pełne drzewo ma `N = (b^(d+1) − 1)/(b − 1)` węzłów (b=5, d=8 → 488 281 węzłów; ≥2 wywołania modelu na węzeł). Dlatego:
1. **Progressive widening** — nie rozwijaj wszystkich dzieci od razu:
   ```text
   children(n) ≤ k · visits(n)^α,   0 < α < 1
   ```
2. **Ewaluacja dwustopniowa** — tani filtr deterministyczny/kompaktowy model, kosztowny sędzia tylko dla top-kandydatów; batchuj wywołania ewaluatorów przy zgodnych schematach i deadlinach.
3. **Wczesna terminacja** — stop przy osiągnięciu progu pewności, marginesu nagrody lub polityki; stop, gdy oczekiwana wartość kolejnej ekspansji jest niższa niż jej szacowany koszt tokenowo-latencyjny.
4. **Deduplikacja stanów** — hashuj skanonizowane stany plannera; scalaj transpozycje; cache’uj wyniki ewaluatora kluczem: hash stanu + wersje modelu/polityki/promptu.
5. **Reuse prefiksów** — współdzielone prefiksy promptów; przechowuj delty gałęzi, nie kopiowane pełne historie; struktury niemutowalne/persystentne przeciw amplifikacji pamięci Pythona.
6. **Backpressure** — kontroler wyszukiwania jest właścicielem stałego semafora współbieżności; tworzenie dzieci nie może generować nieograniczonych tasków asyncio; anuluj zakolejkowane i trwające potomki po przycięciu przodka.

**Krok 6 — Startowa koperta produkcyjna (konserwatywnie)**
- głębokość: 3–5,
- żywy współczynnik rozgałęzienia: 2–4,
- równoległe wywołania modeli na zadanie: 2–4,
- twardy limit węzłów: 32–64,
- kosztowne wywołania sędziego: tylko top 2–5 kandydatów.

Podnoś limity **wyłącznie** gdy ewaluacje offline wykażą mierzalny zysk jakości na dodatkowy token i milisekundę. Śledź metrykę decyzyjną wartości krańcowej wyszukiwania:
```text
zysk jakości / dodatkowe 1000 tokenów
zysk jakości / dodatkowa sekunda
wskaźnik akceptacji planów / rozwinięty węzeł
```
Jeśli głębsze wyszukiwanie poprawia jakość znikomo, a podwaja tokeny lub p95 — routuj do silniejszego modelu single-pass.

**Krok 7 — Wiązanie zatwierdzeń (Zero-Drift)**
Zatwierdzenia wiąż z: ID zadania, hashem planu, hashem diffu, wersją planu, wersją polityki. Unieważniaj wyniki spekulatywne przy dryfie środowiska lub polityki.

### 5.2 Część B — Trybunał i integralność testów

**Krok 1 — Deterministyka najpierw (RAE-First)**
Uruchamiaj kontrole polityk, schematów, bezpieczeństwa i integralności testów **przed** wywołaniami trybunału LLM. Deterministyczne odrzucenie generuje **zero** wywołań modelu.

**Krok 2 — Niezależne pakiety dowodowe**
Buduj niezależne pakiety dowodowe dla sędziów; zapobiegaj wyciekowi dowodów między niezależnymi sędziami.

**Krok 3 — Referencje przez hash**
Zapobiegaj wielokrotnemu osadzaniu identycznego kontekstu repozytorium/testów w promptach sędziów — referencjonuj niemutowalne artefakty przez hash, przekazując tylko wąsko wyselekcjonowane fragmenty.

**Krok 4 — Integralność testów**
Stosuj AST diffing, bazy mutacyjne (mutation baselines) i kontrole delty pokrycia. Usunięcie `assert` lub jego konwersja na logowanie **musi** być wykrywana.

**Krok 5 — Fail-closed**
Brak dowodów lub niedostępność obowiązkowych sędziów → zamknięcie bezpieczne (odrzucenie). Zdefiniuj jawnie kworum i zachowanie w trybie zdegradowanym.

### 5.3 Kryteria akceptacji (Iteracja 4)
- [ ] Wyszukiwanie nie może przekroczyć żadnego limitu zasobowego o więcej niż jedną operację w locie.
- [ ] Anulowane gałęzie zwalniają zasoby modelu, Redis i bazy danych.
- [ ] Persystencja kandydatów jest all-or-nothing.
- [ ] Deterministyczne odrzucenie nie generuje wywołań modelu trybunału.
- [ ] Wyciek dowodów między niezależnymi sędziami jest uniemożliwiony.
- [ ] Usunięcie/degradacja `assert` jest wykrywana.

---

## 6. ITERACJA 5 — Routing, Cache, Optymalizacja Kosztów, Bezpieczeństwo Zatwierdzeń i Sagi

**Cel:** Routing modeli constraint-first ze zwalidowanymi politykami i bezpiecznym fallbackiem; kryptograficzne wiązanie zatwierdzeń; odzyskiwalność awarii częściowych.

### 6.1 Część A — Routing i cache

**Krok 1 — Kontrakty routingu (Kontrakt Bezpieczeństwa)**
```python
class Weights(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    accuracy: Annotated[float, Field(ge=0, le=1)]
    latency:  Annotated[float, Field(ge=0, le=1)]
    cost:     Annotated[float, Field(ge=0, le=1)]

    @model_validator(mode="after")
    def validate_sum(self) -> "Weights":
        values = (self.accuracy, self.latency, self.cost)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("weights must be finite")
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("weights must sum to 1.0")
        return self
```
```python
def normalize(value: float, lower: float, upper: float) -> float:
    if not all(math.isfinite(v) for v in (value, lower, upper)):
        raise ValueError("normalize inputs must be finite")
    if upper <= lower:
        return 0.0
    clamped = max(lower, min(upper, value))
    return (clamped - lower) / (upper - lower)
```

**Krok 2 — Podpisane polityki (Zero-Drift)**
1. Podpisane polityki zawierają: `policy_version`, wagi, TTL, sygnaturę, ID klucza.
2. Weryfikuj sygnaturę i świeżość **przed** użyciem.
3. Sprawdzenia ograniczeń (constraints) **poprzedzają** scoring ważony.
4. Circuit breakery przełączają na ostatnią znaną dobrą podpisaną politykę lub wersjonowaną politykę statyczną.

**Krok 3 — Klucze cache (izolacja tenantów, wektor V-02)**
```text
tenant + auth_scope + model + model_revision
+ prompt_version + policy_version + tool_schema_version
+ normalized_input_hash
```
1. Cache dokładny (exact) najpierw — tani i przewidywalny.
2. Cache semantyczny wyłącznie dla operacji bezpiecznych, bezstanowych, niewrażliwych autoryzacyjnie.
3. **Zakaz bezwzględny:** ponowne użycie wyników zatwierdzeń, mutacji lub operacji wrażliwych środowiskowo na podstawie samego podobieństwa semantycznego.

**Krok 4 — Budżety tokenowe i konstrukcja promptów**
1. Odrębne pułapy etapowe: wejście planowania, wyjście planowania, podsumowania narzędzi, wejście/wyjście trybunału, narzut retry. Odrzucaj lub kompresuj **przed** wysłaniem żądania — `max_tokens` kontroluje wyłącznie wyjście.
2. Kanoniczna konstrukcja promptów: stabilna kolejność, deterministyczny JSON, współdzielone instrukcje w cache’owalnym prefiksie, stan gałęzi na końcu, jawne wersjonowanie szablonów.
3. Kompresja hierarchiczna: surowy output narzędzia → ustrukturyzowane fakty → podsumowanie gałęzi; zachowuj cytowania; nie streszczaj wielokrotnie istniejącego streszczenia — zachowaj wskaźnik do źródła.
4. Cele początkowe:
   - ≥ 50–70% statycznej treści promptu kwalifikuje się do prefix cachingu dostawcy,
   - < 10% zduplikowanych tokenów retrievalu na żądanie,
   - twardy limit tokenów per zadanie z ostrzeżeniem przy 70–80%,
   - tokeny spekulatywne/odrzucone raportowane oddzielnie od ścieżki zaakceptowanej.

**Krok 5 — Prędkość inferencji**
1. Minimalizuj prefill: redukuj powtarzany kontekst, używaj prompt cachingu dostawcy, preferuj retrieval małych fragmentów zamiast pełnego kontekstu repozytorium.
2. Kontroluj długość wyjścia: strukturalne, zwięzłe outputy; stop po skompletowaniu schematu; nie żądaj wyjaśnień, których nikt nie konsumuje.
3. Routuj etapowo: mały/szybki model dla klasyfikacji, przycinania, ekstrakcji, formatowania; silny model dla finalnej syntezy i niejednoznacznych decyzji wysokiego ryzyka; eskaluj tylko gdy wymagają tego progi pewności/polityki.
4. Ograniczaj współbieżność: semafor per dostawca i per tenant; propaguj deadliny do zakolejkowanych wywołań; anuluj potomków przy przycięciu gałęzi lub wygaśnięciu deadline’u.
5. Hedguj ostrożnie: hedging poprawia ogon latencji, lecz może niemal podwoić koszt tokenów — hedguj dopiero po opóźnieniu bliskim historycznego p95, wyłącznie dla wywołań idempotentnych wysokiego priorytetu; natychmiast anuluj przegranego.
6. Batchuj tylko kompatybilną inferencję: embeddingi i scoring sędziów tak; interaktywna generacja cierpi na head-of-line blocking przy zmiennych długościach wyjścia.

### 6.2 Część B — Zatwierdzenia kryptograficzne i sagi

**Krok 1 — Claimy zatwierdzeń (wektor V-01)**
Claimy zawierają: `task_id`, `plan_hash`, `diff_hash`, `policy_version`, `exp`, `iat`, `jti`, audience, issuer.

**Krok 2 — Walidacja hashy**
```regex
^sha256:[0-9a-f]{64}$
```

**Krok 3 — Ścisła walidacja JWT**
1. Dekoduj JWT i waliduj claimy przez rygorystyczny model Pydantic.
2. Mapowanie kontraktowe: zniekształcony/nieprawidłowy token → `401`; token poprawny, lecz nieautoryzowany → `403`, **nigdy** `422`.

**Krok 4 — Rollout claimów: optional-then-required**
1. Wprowadź claim jako opcjonalny; obserwuj metryki brakujących claimów.
2. Egzekwuj obowiązkowość dopiero po upływie maksymalnego czasu życia starych tokenów.
3. Tokeny wybite przed kompatybilnym wdrożeniem kroczącym pozostają ważne przez udokumentowane okno przejściowe.

**Krok 5 — Kompensacja sag (wektor V-04)**
1. Zaimplementuj kompensację z jawnymi deadline’ami i idempotentnymi handlerami `on_failure`.
2. Kompensacja może wykonać się wielokrotnie **bez kumulowania efektów**.

**Krok 6 — Inwalidacja przy dryfie (Zero-Drift)**
Unieważniaj zatwierdzenie, gdy zmieni się plan, diff, środowisko lub obowiązująca polityka.

### 6.3 Kryteria akceptacji (Iteracja 5)
- [ ] NaN i nieskończoności nigdy nie wchodzą do scoringu.
- [ ] Nieznane klucze zawodzą z sanityzowanym `422`.
- [ ] Wpisy cache nie mogą przekraczać granic tenantów ani wersji polityk.
- [ ] Testy partycji sieci i retry nie produkują nieautoryzowanego ukończenia.
- [ ] Kompensacja jest wielokrotnie wykonywalna bez efektów skumulowanych.
- [ ] Tokeny sprzed kompatybilnego wdrożenia ważne przez okno przejściowe.

---

## 7. Przekrojowy Kontrakt Błędów API

Sanityzowana, stabilna koperta:
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed",
    "fields": [
      {"path": "weights.accuracy", "reason": "out_of_range"}
    ],
    "request_id": "..."
  }
}
```
**Zakaz:** przekazywanie wartości nadesłanych, wewnętrzności Pydantic, stack trace’ów, szczegółów SQL, surowych danych promptów/narzędzi.

| Warunek | Status |
|---|---:|
| Naruszenie typu/schematu żądania | 422 |
| Nieprawidłowy token uwierzytelniający | 401 |
| Poprawna tożsamość bez wymaganej zdolności | 403 |
| Nieaktualna wersja optymistyczna | 409 |
| Duplikat żądania idempotentnego | poprzedni wynik lub 202/200 |
| Przeciążenie zależności (retriable) | 503 |
| Timeout sandboxa/zależności | 504 |

---

## 8. Przekrojowa Obserwowalność i SLO

**Każde przejście stanu rejestruje:** `trace_id`, tenant-safe request ID, typ zadania i przejścia, wersje polityki/modelu/promptu, deadline, opóźnienie kolejki, liczby tokenów, status cache, licznik retry.

**Metryki obowiązkowe:**
- histogramy latencji żądań i przejść,
- TTFT modeli i tokeny/s (osobno prefill i decode; kolejka, TTFT i latencja całkowita **osobno**),
- tokeny prompt/completion, tokeny odrzuconych gałęzi,
- hit ratio cache i przyczyna inwalidacji,
- Redis: p95/p99 akwizycji blokad, oczekiwanie/trzymanie/odnowienia/utraty, próby zapisów stale/fenced, liczba oczekujących per klucz,
- wiek kolejki Celery i współczynnik wypełnienia batchy, delay najstarszego elementu, RSS workera per batch, czas DB per element, efekty zduplikowane zablokowane idempotencją,
- utylizacja pul DB i czas oczekiwania, ponowienia serializacji,
- MCTS: węzły rozwinięte/przycięte/anulowane, skuteczność anulowania,
- p50/p95/p99 per model i wersja promptu; latencja zaoszczędzona vs tokeny dodane przez hedging,
- efektywność tokenów użytecznych: tokeny wejścia na ukończone zadanie, tokeny wyjścia na zaakceptowany plan, tokeny trybunału na finalną decyzję, procent powtórzonego prefiksu, koszt tokenowy skorygowany o cache.

**Zakaz:** surowe ID tenantów, prompty, JWT lub output narzędzi jako etykiety metryk.

---

## 9. Przekrojowe Zasady Blokad Redis (Dual-Enforcement)

Blokady Redis **nie są** źródłem prawdy dla przejść stanów. Poprawność zachowują ograniczenia unikalności/wersjonowanie PostgreSQL nawet przy wygaśnięciu blokady lub awarii Redis (wektor **V-05**).

**Poprawny projekt blokady — krok po kroku:**
1. Akwizycja z nieprzewidywalnym tokenem właściciela:
   ```text
   SET key owner_token NX PX lease_ms
   ```
2. Zwolnienie wyłącznie przez Lua, tylko jeśli przechowywany token nadal się zgadza.
3. Odnowienie przez skrypt Lua compare-and-expire.
4. **Fencing token** dla operacji, w których nieświeży właściciel mógłby pisać po wygaśnięciu leasingu — sam token blokady **nie** zapobiega zapisom stale.
5. Ograniczaj czas oczekiwania na akwizycję pozostałym deadline’em wywołującego.

**Wymiarowanie leasingu:**
```text
lease >= max(3 × p99 czasu sekcji krytycznej,
             twardy timeout operacji + margines schedulera/sieci)
```
Odnawiaj co ~1/3 leasingu z jitterem. Przy nieudanym odnowieniu — **zatrzymaj lub ogrodź (fence)** dalszą pracę; nie zakładaj kontynuacji własności.

Przykład: p99 sekcji krytycznej 2 s, pauza schedulera/sieci 1 s → leasing początkowy 8–10 s, odnowienie co 2,5–3 s, oczekiwanie na akwizycję ≤ 500 ms dla żądania interaktywnego lub mały ułamek pozostałego deadline’u. **Nie** wybieraj arbitralnie dużych leasingów (np. 5 minut) — powodują długie przestoje po awarii workera.

**Dozwolone użycie:** tłumienie stampede cache, tłumienie zduplikowanych kosztownych obliczeń (dla single-flight: nietrafieni wywołujący krótko czekają na wartość cache zamiast agresywnie ponawiać akwizycję).
**Zabronione jako jedyna ochrona:** inkrementacje wersji grafu, zatwierdzenia, rozliczenia quasi-pieniężne, nieodwracalne mutacje narzędzi.

Wysoka kontencja blokad zwykle oznacza zbyt szeroki zakres blokady lub granulację klucza.

---

## 10. Działania Najwyższego Priorytetu (kolejność wykonania)

1. Wprowadzić wersjonowane DTO API i konstrukcyjnie uniemożliwić zwracanie obiektów persystencji ORM/Protobuf.
2. Zdefiniować semantykę konfliktów dla zero-wierszowych UPSERT-ów i wyczerpanych ponowień serializacji.
3. Dodać etapowe budżety tokenów, węzłów, współbieżności i czasu zegarowego **przed** włączeniem MCTS/ToT.
4. Używać blokad Redis wyłącznie jako mechanizmów optymalizacji/single-flight; poprawność chronić constraintami bazy i fencingiem.
5. Rozdzielić kolejki Celery i pule bazodanowe według klas obciążenia, następnie stroić batching danymi wieku kolejki i p99.
6. Zinstrumentować TTFT, tokeny prompt/completion, tokeny odrzuconych gałęzi, utraty blokad i współczynnik wypełnienia batchy **przed** jakimkolwiek skalowaniem modeli lub workerów.

---

## 11. Definicja Ukończenia Planu (Definition of Done)

Plan uznaje się za zrealizowany wyłącznie, gdy:
1. Wszystkie kryteria akceptacji Iteracji 1–5 są spełnione i pokryte automatycznymi testami w CI.
2. Każdy nazwany wektor V-01…V-09 posiada aktywny test regresyjny.
3. Bramki `buf breaking`, diff OpenAPI, kontrole expand/migrate/contract są wymaganymi kontrolami CI (nie opcjonalnymi).
4. Metryki z sekcji 8 są emitowane w środowisku produkcyjnym, a SLO zdefiniowane i alarmowane.
5. Audyt Zero-Drift potwierdza: brak niewersjonowanych kontraktów, promptów, polityk i schematów w obiegu produkcyjnym.

*Dokument zamknięty. Wszelkie zmiany wymagają nowej wersji, podpisu właściciela kontraktu i przejścia pełnych bramek kompatybilności — zgodnie z zasadą Zero-Drift.*