# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 7: Laboratorium Ewolucyjne (rae-lab)

---

## 1. Analiza kodu i struktury modułu

Moduł Lab znajduje się w katalogu `/packages/rae-lab`. Odpowiada za zbieranie metryk systemowych, przeprowadzanie eksperymentów optymalizacyjnych na historycznych danych (Offline Replay) oraz dynamiczne strojenie systemu.

*   **Agregator Metryk (`packages/rae-lab/metrics_aggregator.py`):**
    *   *Rola:* Uruchamia serwer FastAPI (port `8011` w sieci internal), zbiera telemetrię i udostępnia interfejsy MCP.
    *   *Komponenty:*
        *   `MABTuner`: Klasa stroiciela optymalizacyjnego, wyliczająca wagi dla routera kosztów na bazie algorytmu Multi-Armed Bandit (MAB).
        *   `LabObservatory`: Zarządca bazy telemetrycznej w pamięci RAM (zabezpieczonej limitem do 1000 wpisów w celu uniknięcia przecieku pamięci).
*   **Menedżer Eksperymentów (`core/experiment_manager.py`):**
    *   *Rola:* Zarządzanie plikami eksperymentalnymi w katalogu `./experiments` i rejestrowanie skanów wysyłanych przez Quality Sentinel.

---

## 2. Rzeczywiste Możliwości Techniczne

*   **Dynamiczne wyliczanie wag MAB (Cost/Performance Optimization):**
    *   `MABTuner` automatycznie wylicza wagi dla optymalizacji kosztów wejściowych/wyjściowych tokenów, czasu wykonania oraz dokładności (wzór: $\alpha \cdot \text{Accuracy} + \beta \cdot (1 - \text{Latency}) + \gamma \cdot (1 - \text{Cost})$).
    *   **Zabezpieczenie przed dominacją (Anti-Looping Rule):** Wagi są normalizowane, a ich wartości są ściśle ograniczone do przedziału $[0.05, 0.85]$. Chroni to system przed całkowitym wyłączeniem jednego z czynników (np. ignorowaniem kosztu na rzecz szybkości).
*   **Bezpieczne gromadzenie danych w pamięci (Telemetry Retention):**
    *   Aby uniknąć przepełnienia pamięci RAM kontenera deweloperskiego przy intensywnej pracy, tablica metryk jest ograniczona do 1000 elementów (działa jako bufor kołowy FIFO).

---

## 3. Porównanie: Specyfikacja vs Rzeczywistość

| Funkcjonalność / Rola | Jak jest opisane w specyfikacji | Jak działa w rzeczywistości (Kod źródłowy) | Wynik audytu |
| :--- | :--- | :--- | :--- |
| **Integracja MAB z Routerem Kosztów (CostAwareRouter)** | Wyliczone wagi MAB są przekazywane do `CostAwareRouter` w jądrze RAE w celu dynamicznego sterowania trasowaniem zapytań deweloperskich. | Klasa `CostAwareRouter` (w pliku `src/fabric/cost_aware_router.py`) nie wykorzystuje wag ($\alpha, \beta, \gamma$) wyliczanych przez `MABTuner`. W rzeczywistości sortuje ona kandydatów statycznie według ryzyka, przewidywanego NCU, wskaźnika awaryjności oraz opóźnienia. Wagi z MABTuner pozostają wyłącznie w pamięci RAM kontenera Lab i nie mają wpływu na proces trasowania. | **KRYTYCZNA ROZBIEŻNOŚĆ (Brak integracji wag MAB z routerem)** |
| **Offline Replay & Learning** | Automatyczne testowanie nowych modeli na podstawie historycznych logów i wybieranie lepszych alternatyw. | Moduł zapisuje pliki JSON eksperymentów do katalogu `./experiments` w celach diagnostycznych, natomiast automatyczne wyciąganie wniosków w celu rekonfiguracji modeli nie jest zaimplementowane w ścieżce produkcyjnej (jest to realizowane manualnie przez skrypt `smoke_test.py`). | **Częściowa automatyzacja (Brak pętli zwrotnej)** |
| **Ochrona przed wyczerpaniem pamięci** | Dynamiczne czyszczenie telemetryczne w celu zachowania stabilności kontenera. | Działa poprawnie. Bufor FIFO ogranicza tablicę telemetryczną do maksymalnie 1000 zdarzeń. | **Zgodne ze specyfikacją** |
