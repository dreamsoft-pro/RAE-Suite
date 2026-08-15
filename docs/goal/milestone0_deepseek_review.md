### Analiza i Uzupełnienie Inwentaryzacji Punktów Dostępu do Pamięci RAE

#### **Potwierdzenie Podstawowego Mapowania**
Podane mapowanie jest **poprawne w zakresie podstawowych punktów dostępu**, ale wymaga uzupełnienia o dodatkowe mechanizmy. Kluczowe elementy są poprawnie zidentyfikowane:

1. **Warstwa API** (FastAPI):  
   - `POST /v2/memories/query` → Odczyt  
   - `POST /v2/memories/store` → Zapis  
   - `POST /v2/search/hybrid` → Odczyt (hybrydowy)  

2. **Warstwa Serwisów**:  
   - `RAECoreService` (odczyt/zapis)  
   - `HybridSearchService` (odczyt pośredni)  

3. **Silnik RAE** (`RAEEngine`):  
   - `search_memories()` → Odczyt  
   - `store_memory()` → Zapis  

4. **Strategie Wyszukiwania**:  
   - Fizyczne zapytania do Qdrant/Postgres (strategie w `rae_core/search/strategies/`).

---

#### **Brakujące Punkty Dostępu (Ukryte Warstwy)**
Pominięto krytyczne elementy związane z **operacjami w tle, konsolidacją i utrzymaniem systemu**:

##### 1. **Zadania w Tle (Celery)**
   - **Memory Consolidation**:
     - **Cel**: Automatyczne łączenie powiązanych pamięci, usuwanie duplikatów.
     - **Punkty dostępu**:  
       - `apps/memory_api/tasks/consolidation.py` (lub podobne):  
         - `consolidate_memories()` → **Odczyt** (pobranie pamięci do konsolidacji) + **Zapis** (zapis skonsolidowanej pamięci).  
         - Wywołuje `RAECoreService.query_memories()` i `RAECoreService.store_memory()`.
   - **Batch Processing**:
     - Masowy import/eksport danych (np. z plików CSV) → Bezpośrednie wywołania `store_memory()`.

##### 2. **Mechanizm Konsolidacji Pamięci**
   - **Lokalizacja**: `rae-core/rae_core/consolidation/` (lub moduł `engine.py`):  
     - `consolidate()` → **Odczyt** (pobiera pamięci via `search_engine.search()`) + **Zapis** (zapisuje wynik via `storage.save()`).  
   - **Integracja z Celery**: Zadanie okresowe (np. co 24h) wyzwalające konsolidację.

##### 3. **Skrypty CLI (Command-Line)**
   - **Przykłady**:  
     - `python -m rae_core.tools.memory_importer` → **Zapis** (import pamięci z zewnętrznych źródeł).  
     - `python -m rae_core.tools.cleanup_old_memories` → **Odczyt** (filtrowanie) + **Zapis** (usuwanie).  
     - `python -m rae_core.tools.reindex` → **Odczyt** (baza SQL) + **Zapis** (Qdrant).  
   - **Użycie serwisów**: Wywołują `RAECoreService.store_memory()`, `clear_memories()`.

##### 4. **Testy Integracyjne/E2E**
   - **Lokalizacja**: `tests/integration/test_memory_api.py` (lub podobne):  
     - Testy zapisu/odczytu → Symulują API lub bezpośrednio używają `RAECoreService`.  
     - **Uwaga**: Mogą obejść warstwę API, wywołując serwisy bezpośrednio.

##### 5. **Mechanizmy Debugowania**
   - **Endpointy diagnostyczne** (np. `/debug/memory`):  
     - **Odczyt**: Podgląd stanu pamięci (wywołuje `list_memories()`).  
     - **Zapis**: Ręczna korekta danych (np. `force_store_memory`).

---

#### **Proponowana Końcowa Inwentaryzacja**
Poniższa tabela agreguje **wszystkie punkty dostępu**, w tym ukryte warstwy:

| **Warstwa**               | **Punkt Dostępu**                                 | **Typ**         | **Lokalizacja**                              |
|---------------------------|--------------------------------------------------|-----------------|---------------------------------------------|
| **API (FastAPI)**         | `POST /v2/memories/query`                        | Odczyt          | `api/v2/memory.py`                          |
|                           | `POST /v2/memories/store`                        | Zapis           | `api/v2/memory.py`                          |
|                           | `POST /v2/search/hybrid`                         | Odczyt          | `routes/hybrid_search.py`                    |
| **RAECoreService**        | `query_memories()`, `search_memories()`          | Odczyt          | `apps/memory_api/services/rae_core_service.py` |
|                           | `store_memory()`                                 | Zapis           |                                              |
|                           | `get_memory()`, `list_memories()`, `count_memories()` | Odczyt       |                                              |
|                           | `clear_memories()`                               | Zapis (usuń)    |                                              |
| **HybridSearchService**   | `search()`                                       | Odczyt          | `apps/memory_api/services/hybrid_search_service.py` |
| **RAEEngine**             | `search_memories()`                              | Odczyt          | `rae-core/rae_core/engine.py`               |
|                           | `store_memory()`                                 | Zapis           |                                              |
| **Strategie Wyszukiwania**| `search()` w strategiach (`anchor.py`, `vector.py` itd.) | Odczyt | `rae-core/rae_core/search/strategies/`    |
| **Celery (Background)**  | `consolidate_memories()`                         | Odczyt + Zapis  | `apps/memory_api/tasks/consolidation.py`    |
|                           | `batch_import_memories()`                        | Zapis           | `apps/memory_api/tasks/batch_processing.py` |
| **Skrypty CLI**           | `memory_importer`                                | Zapis           | `rae-core/tools/memory_importer.py`         |
|                           | `cleanup_old_memories`                           | Odczyt + Zapis  | `rae-core/tools/cleanup.py`                 |
|                           | `reindex`                                        | Odczyt + Zapis  | `rae-core/tools/reindex.py`                 |
| **Konsolidacja**          | `consolidate()`                                  | Odczyt + Zapis  | `rae-core/rae_core/consolidation.py`        |
| **Debug**                 | `GET /debug/memory`                              | Odczyt          | `routes/debug.py`                           |

---

#### **Rekomendacje dla Warstwy Governance**
1. **Monitorowanie Celery**:  
   - Śledź zadania `consolidate_memories` i `batch_import_memories` (logowanie operacji odczytu/zapisu).
2. **Kontrola CLI**:  
   - Wymagaj autoryzacji dla skryptów (np. via `RAE_CLI_AUTH_TOKEN`).
3. **Testy w Środowisku Produkcyjnym**:  
   - Wyłącz bezpośredni zapis/odczyt pamięci w testach (używaj mocków).
4. **Endpointy Debugowe**:  
   - Ogranicz dostęp (np. tylko dla roli `admin`).
5. **Audyt Strategii**:  
   - Monitoruj wywołania `search()` w strategiach (np. logowanie zapytań do Qdrant/Postgres).

> **Kluczowy wniosek**: Ukryte punkty dostępu (szczególnie **Celery** i **CLI**) są krytyczne dla bezpieczeństwa i integralności danych. Wdrożenie Governance powinno objąć **wszystkie warstwy**, nie tylko API i serwisy.