**Analiza i rekomendacje dla Kamienia Milowego 1:**

### 1. Spójność logiczna i model danych:
**Problem:** 
- Model `KnowledgeRecord` łączy pola z rejestru (`rae_knowledge_registry`) i rewizji (`rae_knowledge_revisions`), co prowadzi do niezgodności ze schematem bazy. Pola jak `authority_level` czy `source_type` istnieją w tabeli rewizji, a nie w rejestrze.
- Pole `supersedes` w modelu używa `KnowledgeIdValue` (ID z rejestru), podczas gdy w bazie relacje supersede między rewizjami są oparte na UUID rewizji.

**Rekomendacja:**
- Rozdziel model na `KnowledgeRegistry` (dane podstawowe) i `KnowledgeRevision` (metadane wersji).
- W polu `supersedes` używać UUID z `rae_knowledge_revisions.id` zamiast `knowledge_id`.

### 2. Multi-tenancy:
**Silne strony:**
- Wszystkie kluczowe tabele mają `tenant_id` z foreign key do `tenants.id`.
- Unikalne constrainty uwzględniają `tenant_id` (np. `uq_rae_knowledge_registry_tenant_knowledge`).

**Uwaga:**
- Aplikacja musi wymuszać filtrowanie po `tenant_id` we wszystkich zapytaniach. Sugeruję dodać middleware automatycznie dodające ten warunek.

### 3. Bezpieczeństwo i integralność:
**Silne strony:**
- Walidacja SHA256 na poziomie modelu i bazy (regex w constraintach).
- Mechanizm outbox z blokowaniem i kontrolą prób.
- Silne typowanie enumów w modelu i bazie.

**Ulepszenia:**
- W tabeli `rae_knowledge_supersedes` dodać check sprawdzający czy rewizje należą do tego samego tenanta (np. przez JOIN z `rae_knowledge_registry`).
- W modelu `KnowledgeRecord` dodać walidację długości `scope` (obecnie `max_length=100` w liście, ale brak ograniczenia w bazie).

### 4. Wydajność:
- Brak indeksu na `tenant_id` w tabeli `rae_governance_outbox` (pole `ix_rae_outbox_dispatch` używa `tenant_id` pośrednio).
- Dla dużych tenantów warto rozważyć partycjonowanie tabel po `tenant_id`.

### 5. Sugerowane poprawki w kodzie:

**a) Poprawa modelu Pydantic:**
```python
class KnowledgeRegistryBase(BaseModel):
    tenant_id: TenantIdValue
    knowledge_id: KnowledgeIdValue
    knowledge_class: KnowledgeClass
    owner: str = Field(min_length=1, max_length=100)
    scope: list[str] = Field(default_factory=list, max_length=100)
    generation: int = Field(ge=1, default=1)

class KnowledgeRevision(BaseModel):
    registry_id: UUID
    authority_level: AuthorityLevel
    source_type: KnowledgeSourceType
    source_ref: str = Field(min_length=1, max_length=2048)
    checksum: ChecksumSha256Value
    supersedes: list[UUID] = Field(default_factory=list)  # UUID rewizji
```

**b) Dodatkowy constraint w SQL:**
```python
# W tabeli rae_knowledge_supersedes:
sa.CheckConstraint(
    """
    EXISTS (
        SELECT 1 FROM rae_knowledge_revisions r1 
        JOIN rae_knowledge_registry reg1 ON r1.registry_id = reg1.id
        WHERE r1.id = superseding_revision_id AND reg1.tenant_id = ...
    )
    AND ... # analogicznie dla superseded_revision_id
    """,
    name="ck_rae_supersedes_same_tenant"
)
```

### 6. Weryfikacja migracji:
- Testy powinny sprawdzać przypadki cross-tenant (np. próba przypisania rewizji do innego tenanta).
- Dodać testy walidacji zakresów czasowych `valid_from`/`valid_until`.

**Podsumowanie:**
Implementacja jest solidna, ale wymaga dostosowania modeli Pydantic do struktury bazy i wzmocnienia mechanizmów cross-tenant. Po wprowadzeniu powyższych poprawek można zatwierdzić wdrożenie.