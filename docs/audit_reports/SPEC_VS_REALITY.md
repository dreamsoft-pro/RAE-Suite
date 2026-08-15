# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 10: Różnice między Specyfikacją a Rzeczywistością (Delta Report)

---

## 1. Wstęp

Niniejszy raport zestawia obietnice techniczne zawarte w specyfikacjach, przewodnikach i manifestach (tzw. "Paper Architecture") z **faktycznym stanem implementacji w kodzie źródłowym i kontenerach produkcyjnych (Reality)**. 

Wskazanie tych rozbieżności jest kluczowe dla dalszego rozwoju suity, poprawy stabilności oraz uniknięcia błędnych założeń projektowych podczas integracji z zewnętrznymi systemami (np. Dreamsoft).

---

## 2. Zestawienie Rozbieżności (Critical Deltas)

### Delta 1: Brak Aktywnego Środowiska Celery (Maintenance)
*   **Jak opisuje specyfikacja:** Zadania konserwacyjne bazy danych, takie jak matematyczny rozpad ważności wspomnień (`decay_importance`), usuwanie zduplikowanych semantycznie rekordów oraz optymalizacja wektorowa, działają nieprzerwanie w tle, zarządzane przez Celery Worker oraz Celery Beat.
*   **Stan faktyczny w kodzie:** Kod zadań i definicja aplikacji Celery (`celery_app.py`, `background_tasks.py`) istnieją, jednak **żaden z kontenerów w produkcyjnym pliku `docker-compose.yml` nie uruchamia workerów ani harmonogramu Celery**.
*   **Konsekwencja:** Wspomnienia nigdy nie ulegają automatycznemu rozpadowi w tle w działającym systemie. Ważność wspomnień pozostaje statyczna, chyba że zostanie wywołany manualny skrypt testowy lub endpoint API.
*   **Rekomendacja:** Dodać serwisy `celery-worker` oraz `celery-beat` do głównego pliku `docker-compose.yml` z użyciem współdzielonego obrazu `rae-memory:latest`.

### Delta 2: Ulotność Punktów Kontrolnych Grafu (Temporal Graph)
*   **Jak opisuje specyfikacja:** Graf wiedzy (`TemporalGraph`) zapamiętuje powiązania między pojęciami, umożliwiając wykonywanie migawek systemu i ich późniejsze przywracanie (`restore_snapshot`) w celach audytowych ISO 27001 / ISO 42001.
*   **Stan faktyczny w kodzie:** Metody `create_snapshot` i `get_snapshot_at_time` w `TemporalGraphService` (`temporal_graph.py`) zapisują dane wyłącznie do wewnętrznej zmiennej słownikowej w pamięci RAM (`self._snapshots`). Brak jakiejkolwiek persystencji bazodanowej (PostgreSQL / Redis) dla tych struktur.
*   **Konsekwencja:** Dowolny restart kontenera `rae-memory` bezpowrotnie usuwa całą historię migawek grafu i stanów przejściowych wiedzy.
*   **Rekomendacja:** Zaimplementować zapis i odczyt migawek grafu przy użyciu PostgreSQL (np. jako blob JSONB w dedykowanej tabeli `graph_snapshots`).

### Delta 3: Symulowany Planista MCTS/ToT (Cognitive Planner)
*   **Jak opisuje specyfikacja:** Przed wykonaniem zadań o podwyższonym ryzyku, jądro autonomii uruchamia zaawansowany planista oparty o algorytmy Monte Carlo Tree Search oraz Tree of Thoughts, który generuje 3 alternatywne ścieżki i wylicza prawdopodobieństwo sukcesu deweloperskiego.
*   **Stan faktyczny w kodzie:** Klasa `CognitivePlanner` (`core/cognitive_planner.py`) zwraca predefiniowane, statyczne dane symulujące gałęzie drzewa decyzyjnego, aby spełnić wymagania walidacyjne jądra autonomii. Rzeczywiste przeszukiwanie drzewa MCTS nie jest wykonywane.
*   **Konsekwencja:** System nie analizuje alternatywnych ścieżek deweloperskich; wykonuje plan wygenerowany liniowo przez model LLM.
*   **Rekomendacja:** Zintegrować planistę z rzeczywistym generowaniem i oceną drzewa hipotez przez LLM lub usunąć symulację na rzecz jasnego opisu liniowego planowania.

### Delta 4: Pozorna Integracja MAB z Routerem Kosztów (Lab Tuner)
*   **Jak opisuje specyfikacja:** Optymalizator Multi-Armed Bandit (`MABTuner` w `rae-lab`) dynamicznie stroi wagi ($\alpha, \beta, \gamma$) dla routera zapytań `CostAwareRouter`, dopasowując balans między kosztami tokenów, czasem wykonania a dokładnością modeli.
*   **Stan faktyczny w kodzie:** `MABTuner` poprawnie wylicza wagi na podstawie zbieranej telemetrii, lecz router `CostAwareRouter` (`src/fabric/cost_aware_router.py`) w ogóle nie przyjmuje ani nie konsumuje tych wag. Router sortuje agentów według statycznych priorytetów (ryzyko, NCU, awaryjność).
*   **Konsekwencja:** Cała optymalizacja MAB w Laboratorium działa "w próżni" i nie wpływa na trasowanie zadań w klastrze.
*   **Rekomendacja:** Zmodyfikować metodę `route` w `CostAwareRouter`, aby przyjmowała aktualny wektor wag z Laboratorium i stosowała go do wyliczenia wielokryterialnej oceny kandydata.

### Delta 5: Uproszczona Zapora Semantyczna w OpenClaw
*   **Jak opisuje specyfikacja:** Zaawansowana, neuronowa zapora semantyczna (Semantic Firewall) analizuje wiadomości przychodzące z komunikatorów w celu detekcji ataków typu prompt injection oraz wycieku poufnych danych.
*   **Stan faktyczny w kodzie:** Zapora opiera się na prostych, statycznych regułach regex i dopasowaniu słów kluczowych.
*   **Konsekwencja:** Podatność na bardziej zaawansowane techniki wstrzykiwania instrukcji (jailbreak).
*   **Rekomendacja:** Dodać szybki lokalny klasyfikator (np. mały model ONNX) do analizy intencji wiadomości na poziomie wejściowym OpenClaw.

### Delta 6: Nieaktywny Skaner Asercji (Test Integrity Guard)
*   **Jak opisuje specyfikacja:** `TestIntegrityGuard` chroni przed oszukiwaniem metryk pokrycia kodu (Coverage) poprzez wykrywanie usuwania asercji z testów przez modele LLM.
*   **Stan faktyczny w kodzie:** Klasa istnieje, jednak nie jest podłączona do procesu decyzyjnego sądu jakości (`QualityTribunal`).
*   **Konsekwencja:** Modele teoretycznie mogą zmodyfikować testy tak, aby przechodziły pomyślnie bez rzeczywistego sprawdzania logiki (np. usuwając słowa kluczowe `assert`).
*   **Rekomendacja:** Zintegrować `TestIntegrityGuard` bezpośrednio w kroku `Tier 1` ewaluacji jakości w `tribunal.py`.
