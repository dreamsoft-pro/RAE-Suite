# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 4: Planista i Architekt (rae-phoenix)

---

## 1. Analiza kodu i struktury modułu

Moduł Phoenix znajduje się w katalogu `/packages/rae-phoenix`. Odpowiada za planowanie architektoniczne, automatyczne generowanie poprawek (refaktoryzację) oraz weryfikację poprawności działania aplikacji po zmianach.

*   **Silnik Refaktoryzatora (`packages/rae-phoenix/main.py`):**
    *   *Rola:* Główna klasa `PhoenixRefactorer` odbierająca zgłoszenia naprawcze (np. z Quality Sentinel lub od CEO).
    *   *Działanie:* Wywołuje pętlę zamkniętej samonaprawy (Closed-Loop Repair), dobiera odpowiednią wtyczkę językową (Recipe Selection), aplikuje zmiany i wysyła kod do ponownej weryfikacji w Quality Sentinel.
*   **System Wtyczek AST (`feniks/core/plugins/`):**
    *   *Rola:* Narzędzia do bezpośredniej modyfikacji kodu źródłowego na poziomie drzewa składniowego (AST) dla poszczególnych języków.
*   **Analizator Wpływu (`feniks/core/analysis/indexer.py`):**
    *   *Rola:* Konstruowanie indeksu zależności całego systemu w celu oszacowania strefy wpływu zmiany (Impact Zone). Pozwala określić, ile plików zależy od modyfikowanego modułu.

---

## 2. Rzeczywiste Możliwości Techniczne

*   **Zamknięta pętla samonaprawy (Closed-Loop Repair):**
    *   Phoenix podejmuje próby naprawy kodu, który nie przeszedł testów lub audytu jakości. Każda wygenerowana poprawka jest automatycznie odsyłana do `rae-quality` na endpoint `/v2/quality/audit`.
    *   **Twardy Kontrakt Weryfikacji (Hard Contract):** Kod jest uznawany za poprawny tylko wtedy, gdy przejdzie weryfikację w Quality Sentinel (`verdict == "PASSED"`) oraz jego poziom zaawansowania zostanie sklasyfikowany jako `advanced_senior` (wynik $\ge 0.90$).
*   **Wycofanie zmian (Rollback):**
    *   Jeżeli w wyznaczonym budżecie prób lub tokenów nie uda się osiągnąć wymaganego standardu, Phoenix automatycznie przerywa pętlę i przywraca oryginalny stan plików (rollback), oznaczając zadanie jako `FAILED_ESCALATED`.
*   **Ocena strefy wpływu (Impact Analysis):**
    *   Przed modyfikacją pliku system sprawdza, ile innych modułów od niego zależy. Informacja ta jest przekazywana do promptu naprawczego jako kontekst deweloperski, aby zapobiec regresjom.
*   **Szablonowanie kodu (Scaffolding):**
    *   Endpoint `/v2/phoenix/create` pozwala na automatyczne generowanie szkieletu kodu (np. według wzorca Clean Architecture) z użyciem wtyczek AST.

---

## 3. Porównanie: Specyfikacja vs Rzeczywistość

| Funkcjonalność / Rola | Jak jest opisane w specyfikacji | Jak działa w rzeczywistości (Kod źródłowy) | Wynik audytu |
| :--- | :--- | :--- | :--- |
| **Cognitive Planner (MCTS/ToT)** | Silnik planowania Monte Carlo Tree Search / Tree of Thoughts generuje 3 alternatywne scenariusze i wylicza dynamicznie szansę powodzenia (Win Probability) przed alokacją zasobów. | Klasa `CognitivePlanner` w `core/cognitive_planner.py` nie implementuje rzeczywistego algorytmu przeszukiwania drzewa MCTS ani ToT. Zamiast tego odpytuje model LLM o plan, a parametry takie jak szansa powodzenia czy wyselekcjonowana gałąź są zwracane w postaci statycznych/symulowanych struktur danych w celu przejścia walidacji kontraktu. | **Symulacja (Mock w kodzie)** |
| **Limit prób naprawczych (Max Attempts)** | W notatkach dotyczących stabilizacji kodu oraz unikania zapętlenia budżetu tokenów zdefiniowano limit maksymalnie 3 prób automatycznej naprawy przez Phoenixa. | W pliku `packages/rae-phoenix/main.py` (linia 67) limit ten jest wciąż ustawiony na `max_attempts = 5`. Stwarza to ryzyko nadmiernego zużywania tokenów i dłuższego oczekiwania przy trudnych błędach. | **Rozbieżność parametrów (max_attempts 5 vs 3)** |
| **Behavioral Verification System** | Wykonywanie migawek zachowania przed i po zmianie kodu (`BehaviorSnapshot`) i blokowanie zmian przy regresji. | Narzędzia do weryfikacji behawioralnej (`BehaviorComparisonEngine` w `feniks/core/behavior/`) są obecne w bibliotece, jednak w głównej pętli naprawczej `main.py` wdrożona jest wyłącznie bezpośrednia weryfikacja statyczno-semantyczna przez API Quality Sentinel. | **Częściowo nieaktywne w produkcji** |
| **Bezpieczny Rollback** | Pełne cofnięcie kodu na wypadek niepowodzenia. | Zaimplementowane prawidłowo. W przypadku wyczerpania prób lub tokenów pierwotny kod jest przywracany, a transakcja wycofywana. | **Zgodne ze specyfikacją** |
