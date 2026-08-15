# Audyt Techniczny i Funkcjonalny RAE-Suite (Silicon Oracle v5.0)
## Część 6: Strażnik Jakości (rae-quality)

---

## 1. Analiza kodu i struktury modułu

Moduł Quality znajduje się w katalogu `/packages/rae-quality`. Odpowiada za weryfikację poprawności składniowej kodu, skanowanie luk bezpieczeństwa oraz ewaluację zaawansowania deweloperskiego proponowanych poprawek.

*   **Strażnik Jakości (`packages/rae-quality/main.py`):**
    *   *Rola:* Centralny punkt wejściowy `QualitySentinel` (udostępnia interfejsy MCP oraz endpoint `/v2/quality/audit`).
    *   *Działanie:* Wykonuje parsowanie AST, wylicza ocenę Seniority i w przypadku odrzucenia kodu wysyła sygnał interwencyjny do Phoenixa.
*   **Trójwarstwowy Sąd Jakości (`engines/governance/tribunal.py`):**
    *   *Rola:* Wielostopniowy audyt logiki biznesowej i bezpieczeństwa.
    *   *Etapy:*
        *   `Tier 1 (Partial Court)`: Szybkie, deterministyczne testy lokalne (odrzucanie zbyt krótkiego kodu lub plików z placeholderami "TODO"/"FIXME").
        *   `Tier 2 (Appellate Court)`: Semantyczna ocena kodu przez lokalny model LLM (Ollama) przy użyciu wyekstrahowanych z pamięci wytycznych projektowych (RAG).
        *   `Tier 3 (Supreme Court)`: Konsensus z użyciem modeli komercyjnych (Gemini/Claude) przy projektach oznaczonych jako krytyczne.
*   **Klasyfikator zaawansowania (`SeniorityRanker` w `main.py`):**
    *   *Rola:* Matematyczne wyliczenie punktacji na podstawie wzoru: $0.4 \cdot \text{Coverage} + 0.3 \cdot (1 - \text{Complexity}) + 0.3 \cdot \text{TypeSafety}$.
    *   *Wynik:* Przypisuje poziom od `Junior Developer` do `Advanced Senior`. Kod o wyniku poniżej `0.70` (lub niesklasyfikowany jako `Advanced Senior` w pętli Phoenix) jest automatycznie odrzucany.

---

## 2. Rzeczywiste Możliwości Techniczne

*   **Szybkie odrzucanie (Fail-Fast AST Check):**
    *   Przed wywołaniem jakichkolwiek modeli językowych, kod jest sprawdzany za pomocą systemowego modułu `ast.parse`. Jeśli kod zawiera błędy składniowe (SyntaxError), jest natychmiast odrzucany, co oszczędza 100% tokenów.
*   **Autonomiczna Interwencja (Active Intervention):**
    *   W przypadku odrzucenia kodu (werdykt `REJECTED`), Quality Sentinel nie tylko informuje o błędzie, ale za pomocą asynchronicznego zadania `asyncio.create_task` wysyła zgłoszenie na endpoint `/v2/bridge/interact`, budząc agenta Phoenix i zlecając mu natychmiastowe naprawienie wadliwego kodu na podstawie uzyskanej argumentacji sądu.

---

## 3. Porównanie: Specyfikacja vs Rzeczywistość

| Funkcjonalność / Rola | Jak jest opisane w specyfikacji | Jak działa w rzeczywistości (Kod źródłowy) | Wynik audytu |
| :--- | :--- | :--- | :--- |
| **Separacja Instancji Sądowych (Tier 2 vs Tier 3)** | Tier 2 (lokalny Ollama) i Tier 3 (zewnętrzny, zaawansowany SaaS) działają jako odrębne instancje podejmujące niezależne decyzje w celu uniknięcia stronniczości. | W środowisku deweloperskim i testowym, z powodu braku rozproszonych modeli lokalnych, `resolve_llm_runtime` często przekierowuje oba zapytania do tego samego nadrzędnego API (np. Gemini/Ollama), co sprawia, że podział na sąd apelacyjny i najwyższy jest bardziej logiczny niż fizyczny. | **Separacja logiczna (Wspólny backend)** |
| **Test Integrity Guard** | Blokowanie asercji mockowanych w testach w celu zapobiegania oszukiwaniu wskaźnika Coverage. | Klasa `TestIntegrityGuard` jest poprawnie zaimplementowana w jądrze, lecz w rzeczywistej pętli Tribunal (`tribunal.py`) nie jest ona aktywnie zintegrowana w ścieżce weryfikacji. | **Niedokończona integracja** |
| **Fail-Fast AST Check** | Natychmiastowe odrzucenie kodu o złej składni. | Zaimplementowane w `main.py` za pomocą parsera `ast.parse` i działające poprawnie. | **Zgodne ze specyfikacją** |
| **Autonomiczna Interakcja (Sentinel -> Phoenix)** | Automatyczne zlecanie poprawek agentowi Phoenix przy odrzuceniu. | Zaimplementowane poprawnie za pomocą asynchronicznych zapytań HTTP do Bridge API. | **Zgodne ze specyfikacją** |
