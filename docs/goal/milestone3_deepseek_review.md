### Kompleksowy audyt kodu Kamienia Milowego 3

#### 1. Spójność logiczna i zgodność ze specyfikacją
- **Modele dowodowe**:
  - Poprawna implementacja DTO z walidacją pól (np. zakresy float 0.0-1.0, długości stringów)
  - Brakujące pola w `EvidenceBundle`:
    - `action_records` i `decision_records` z dokumentacji nie są zaimplementowane
    - `cost_vector` w bundle nieobsługiwany
  - `ResolutionStatus` w bundle nie uwzględnia wszystkich przypadków (np. eskalacji)

- **Silnik rozstrzygania**:
  - Mechanizm świeżości (half-life 30 dni) poprawny matematycznie
  - Dopasowanie zakresu (scope_match) - potencjalny błąd gdy scope jest pusty:
    ```python
    scope_match = 1.0 if not context.scope else ...  # Brakuje tego zabezpieczenia
    ```
  - Konfidencja jako średnia relewancji - uproszczenie, które może nie odzwierciedlać rzeczywistej pewności

#### 2. Niezawodność haszowania kanonicznego
- **Kwantyzacja floatów**:
  - Poprawnie zaokrąglane do 6 miejsc w `calculate_content_hash`
  - Brak kwantyzacji w `EvidenceItem` podczas tworzenia (mogą wpływać na późniejsze hash)

- **Spójność kanonicznego JSON**:
  - Poprawne użycie `sort_keys` i stałych separatorów
  - Potencjalny problem: sortowanie list wg kluczy z floatami po kwantyzacji
  - Brak obsługi specjalnych typów danych w `default=str` (np. Pydantic enums)

- **Bezpieczeństwo łańcucha audytowego**:
  - `previous_audit_hash` poprawnie włączony w payload
  - Brak weryfikacji spójności poprzedniego hasha w bundle

#### 3. Wykrywanie konfliktów
- **Problemy w grupowaniu**:
  ```python
  key = item.knowledge_id or item.source_ref  # Problem gdy knowledge_id="" i source_ref="A"
  ```
  Powinno być: `key = item.knowledge_id if item.knowledge_id is not None else item.source_ref`

- **Naiwna resolucja konfliktów**:
  - Tylko konflikty typu VERSION (ignorowane SEMANTIC, POLICY_VIOLATION)
  - Brak eskalacji dla wysokiej severities (zawsze RESOLVED_WITH_WARNING)
  - Uproszczony wybór "winnera" bez analizy treści

- **Brakujące mechanizmy**:
  - Nieobsługiwane wspieranie/kontradykcje (`supports/contradicts`)
  - Brak integracji z politykami (policy_version nie używana w resolucji)

#### 4. Audytowalność
- **Ślad audytowy**:
  - `bundle_id` i `generated_at` poprawnie w hashu audytowym
  - Brak sygnatury czasowej i podpisu cyfrowego

- **Problemy z integralnością**:
  ```python
  bundle.content_hash = ...  # Powinno być ustawiane w modelu, nie z zewnątrz
  ```
  Lepsze: automatyczne obliczanie w `EvidenceBundle` via `@model_validator`

- **Brakujące elementy**:
  - Brak logów operacyjnych w silniku
  - Nieprzechowywanie pełnej historii konfliktów

### Proponowane poprawki krytyczne

1. **Naprawa grupowania konfliktów**:
```python
# W engine.py, linia 93
key = item.knowledge_id if item.knowledge_id is not None else item.source_ref
```

2. **Dodanie brakujących pól do EvidenceBundle**:
```python
class EvidenceBundle(BaseModel):
    ...
    action_records: list[ActionRecord] = Field(default_factory=list, max_length=100)
    decision_records: list[DecisionEvidenceRecord] = Field(default_factory=list, max_length=100)
    cost_vector: CostVector | None = None
```

3. **Automatyczne hashowanie w modelu**:
```python
from pydantic import model_validator

class EvidenceBundle(BaseModel):
    ...
    @model_validator(mode='after')
    def compute_hashes(self):
        self.content_hash = calculate_content_hash(self)
        self.audit_hash = calculate_audit_hash(...)
        return self
```

4. **Rozszerzenie mechanizmu konfliktów**:
```python
# W engine.py
if sorted_items[0].authority_level == AuthorityLevel.UNTRUSTED:
    resolution_status = ResolutionStatus.BLOCKED
```

5. **Dodanie walidacji zakresu**:
```python
# W engine.py, obliczanie scope_match
scope_match = 1.0
if context.scope and candidate.metadata.get("scope"):
    item_scope = candidate.metadata["scope"]
    matches = [s for s in item_scope if s in context.scope]
    scope_match = len(matches) / len(item_scope) if item_scope else 0.0
```

### Zalecenia

1. **Zatwierdzić z poprawkami**:
   - Wdrożyć krytyczne poprawki z powyższej listy
   - Dodać testy dla przypadków brzegowych (np. puste scope, konflikty krytyczne)

2. **Dodatkowe usprawnienia**:
   ```python
   # W hashing.py - zabezpieczenie przed NaN
   round(x, 6) if not math.isnan(x) else 0.0
   ```

3. **Dokumentacja**:
   - Opisać algorytm half-life w docstringach
   - Udokumentować ograniczenia mechanizmu konfliktów

4. **Bezpieczeństwo**:
   - Dodać podpisy cyfrowe dla łańcucha audytowego
   - Rozważyć walidację previous_audit_hash w resolverze

Implementacja jest solidna, ale wymaga dopracowania kluczowych elementów przed wdrożeniem produkcyjnym. Szczególnie krytyczne są poprawki w mechanizmie konfliktów i integralności danych.