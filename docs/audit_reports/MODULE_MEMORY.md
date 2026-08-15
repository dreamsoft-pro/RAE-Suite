# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 3: Pamięć Poznawcza (rae-agentic-memory)

---

## 1. Analiza kodu i struktury modułu

Moduł pamięci znajduje się w pakiecie `/packages/rae-agentic-memory`. Jest to kluczowy element suity, realizowany jako aplikacja internetowa FastAPI (katalog `/apps/memory_api`), korzystająca z jądra `rae-core`.

*   **Silnik RAE Core (`packages/rae-agentic-memory/rae-core/rae_core/engine.py`):**
    *   *Rola:* Centralny sterownik zapisu i odczytu wspomnień. Odpowiada za rozdzielanie danych do odpowiednich warstw poznawczych.
*   **Wyszukiwanie Hybrydowe (`rae_core/search/` oraz `apps/memory_api/routes/hybrid_search.py`):**
    *   *Rola:* Koordynowanie wielomodelowych zapytań wektorowych oraz tekstowych.
*   **Graf Wiedzy (`apps/memory_api/services/temporal_graph.py`):**
    *   *Rola:* Mapowanie relacji semantycznych między pojęciami oraz wersjonowanie stanu grafu w czasie.
*   **P2P Federation Mesh (`apps/memory_api/api/v2/mesh.py` & `services/mesh_service.py`):**
    *   *Rola:* Bezpieczna synchronizacja wspomnień między rozproszonymi węzłami (Node1 Lumina, Node2 Julia, Node3 Piotrek) przy użyciu szyfrowania AES-GCM-SIV, wymiany kluczy ECDH oraz zapór klasyfikacji danych.

---

## 2. Rzeczywiste Możliwości Techniczne

*   **Pamięć Wielowarstwowa (Cognitive Layers):**
    *   *Sensory:* Tymczasowy bufor dla nieprzetworzonych danych (logi, OCR).
    *   *Working:* Pamięć podręczna aktywnego kontekstu (automatycznie czyszczona po zamknięciu zadania).
    *   *Episodic:* Chronologiczny dziennik zdarzeń agenta (zapisywany automatycznie przez Bridge).
    *   *Semantic:* Zanonimizowane, ogólne fakty wyekstrahowane z epizodów.
    *   *Reflective:* Wnioski wyższego rzędu i "Lessons Learned" syntezowane przez LLM.
*   **Named Vectors (Multi-Vector Space):**
    *   Przechowywanie osadzonych wektorów (embeddings) z różnych modeli w dedykowanych przestrzeniach wektorowych w Qdrant (np. `dense` o wymiarowości 384d lub `ollama` 768d). Zapewnia to pełną agnostyczność modelową i zapobiega utracie informacji przy zmianie modelu LLM.
*   **Kompaktowy Reranking poznawczy:**
    *   Dwuetapowe sortowanie. Pierwszy etap to szybkie filtrowanie matematyczne na bazie wagi poznawczej (wzór: $\alpha \cdot \text{relevance} + \beta \cdot \text{importance} + \gamma \cdot \text{recency}$). Drugi etap (opcjonalny, aktywowany przy niskim wskaźniku wiarygodności pierwszego etapu) to precyzyjny re-ranking za pomocą LLM.
*   **Izolacja bezpieczeństwa danych RESTRICTED:**
    *   Twarda walidacja w `RAECoreService`. Jeżeli pamięć zawiera poufne dane oznaczone klasą `RESTRICTED`, system uniemożliwia jej zapisanie w warstwach ogólnych (np. `Semantic` lub `Reflective`), ograniczając jej obecność wyłącznie do tymczasowej warstwy `Working` i wymuszając szyfrowanie.

---

## 3. Porównanie: Specyfikacja vs Rzeczywistość

| Funkcjonalność / Rola | Jak jest opisane w specyfikacji | Jak działa w rzeczywistości (Kod źródłowy) | Wynik audytu |
| :--- | :--- | :--- | :--- |
| **Wersjonowanie Grafu (Temporal Graph Snapshots)** | Możliwość wykonywania i przywracania punktów kontrolnych grafu wiedzy (`restore_snapshot`) w celu cofania relacji pojęciowych przy błędnych wnioskach. | Funkcje `create_snapshot` i `get_snapshot_at_time` w `TemporalGraphService` przechowują dane wyłącznie w pamięci RAM kontenera (`self._snapshots = {}`). Klasa ta nie zapisuje migawek do bazy PostgreSQL ani Redis. Po restarcie kontenera cała historia migawek ulega skasowaniu. | **KRYTYCZNA ROZBIEŻNOŚĆ (Brak persistency dla migawek grafu)** |
| **Matematyczny rozpad (Memory Decay)** | Ważność wspomnień zanika wykładniczo w czasie w tle, optymalizując przestrzeń i kontekst. | Algorytm rozpadu w `postgres.py` (`decay_importance`) jest w pełni zaimplementowany w czystym SQL i poprawnie rozróżnia pamięć świeżą (<7 dni) od przestarzałej (>30 dni). Jednak z powodu braku uruchomionego demona Celery, funkcja ta **nie jest wywoływana cyklicznie w tle**. | **Brak automatyzacji (Celery offline)** |
| **Named Vectors i Agnostyczność** | Zapisywanie embeddingów lokalnie bez wycieku danych na zewnątrz (Zero-Egress). | Działa poprawnie. Usługa `EmbeddingService` korzysta z lokalnego backendu ONNX (`onnx`) do bezwyjściowego generowania wektorów, a w przypadku jego braku automatycznie przełącza się na API LiteLLM. | **Zgodne ze specyfikacją** |
| **P2P Federation Mesh** | Bezpieczna synchronizacja rozproszona z weryfikacją zgody (Consent Grants) dla danych poufnych. | Kod w `/api/v2/mesh.py` poprawnie wdraża weryfikację kopert (envelopes), podpisywanie wyzwań oraz deszyfrowanie tokenów peerów za pomocą kluczy AES-GCM. Blokuje synchronizację danych poufnych bez aktywnego `ConsentGrant`. | **Zgodne ze specyfikacją** |
| **Brama bezpieczeństwa RESTRICTED** | Blokowanie danych poufnych poza warstwą roboczą. | Zaimplementowane w `rae_core/guards/security.py` i w pełni egzekwowane w `RAECoreService` przed zapisem w pamięci wektorowej. | **Zgodne ze specyfikacją** |
