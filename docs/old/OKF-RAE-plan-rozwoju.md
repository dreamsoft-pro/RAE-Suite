# OKF-RAE — plan rozwoju warstwy zarządzania wiedzą, autorytetem i dowodami

## 1. Cel dokumentu

RAE ma już strukturę fabryki obejmującą:

- pamięć,
- planowanie,
- wykonanie,
- jakość,
- audyt,
- eksperymenty,
- warstwę ciągłego doskonalenia,
- modele działań,
- dowody decyzji,
- wyniki,
- porażki,
- eksperymenty,
- pakiety wiedzy i doświadczeń.

Dlatego nie należy budować obok niego osobnego systemu „OKF-RAG”. Należy rozszerzyć obecny RAE o warstwę zarządzania wiedzą, która rozróżnia:

1. różne klasy wiedzy,
2. poziomy autorytetu,
3. aktualność i zakres obowiązywania,
4. źródła prawdy,
5. dowody wspierające decyzję,
6. konflikty pomiędzy źródłami,
7. proces awansu obserwacji do wiedzy kanonicznej.

Proponowana nazwa warstwy:

> **RAE Knowledge Governance Layer**

Jej zadaniem nie jest zastąpienie istniejącej pamięci RAE, mechanizmu hybrydowego wyszukiwania ani modeli RAG. Jej zadaniem jest określenie, **które źródło ma prawo rozstrzygać dane pytanie**, jak silne są dowody i czy decyzja może zostać wykonana.

Najważniejsza zasada:

> RAE nie powinno pytać wyłącznie „co najbardziej pasuje semantycznie?”, lecz również „które źródło ma prawo rozstrzygać to pytanie, w jakim zakresie i na jaki moment czasu?”.

To odróżnia warstwę governance od prostego mechanizmu wyszukiwania podobnych fragmentów.

Cele niefunkcjonalne warstwy obejmują również:

- przewidywalne opóźnienie rozstrzygania,
- ograniczenie liczby odczytów z Postgresa i zewnętrznych źródeł,
- bezpieczne cache’owanie wyników zależnych od zakresu i uprawnień,
- kompaktową serializację obiektów przechowywanych w Redisie,
- kontrolę dużych payloadów i kosztów TOAST w PostgreSQL,
- ochronę bazy przez PgBouncer i budżety połączeń,
- asynchroniczne wykonywanie kosztownych operacji poza ścieżką synchroniczną,
- idempotentność i backpressure w kolejkach,
- odporność na stampede, retry storm oraz przeciążenie adapterów.

Cele bezpieczeństwa i zgodności obejmują dodatkowo:

- kryptograficzne łańcuchowanie artefaktów audytowych (Hash Chaining) gwarantujące niezaprzeczalność i wykrywalność manipulacji dowodami decyzji,
- audytowalność zgodną z ISO/IEC 27001 (bezpieczeństwo informacji) oraz ISO/IEC 42001 (zarządzanie systemami AI), z jawnym mapowaniem kontroli,
- optymistyczną kontrolę współbieżności (OCC guards) dla wszystkich mutacji wiedzy kanonicznej i rejestru,
- bezpieczną migrację w trybie Dual-Write z pomiarem rozbieżności i jawną procedurą cutover oraz rollback,
- wielopoziomową archiwizację z Cold Storage, WORM, legal hold i testowanymi procedurami odtworzenia,
- rozdzielenie ról i kluczy kryptograficznych podpisujących artefakty audytowe od kluczy operacyjnych.

---

## 1a. Zasady architektoniczne audytu typów

Ta sekcja definiuje reguły, które obowiązują we wszystkich modelach domenowych w tym dokumencie. Zostały wprowadzone w wyniku audytu architektonicznego i mają pierwszeństwo nad przykładami z dalszych sekcji, jeśli pojawi się rozbieżność.

### 1a.1. Typowanie nominalne

Domena RAE operuje na wielu identyfikatorach będących „gołymi” stringami lub UUID-ami. Powoduje to ryzyko pomyłkowego przekazania `knowledge_id` tam, gdzie oczekiwany jest `source_ref`, ponieważ oba są strukturalnie typu `str`. Wprowadzamy typowanie nominalne oparte na odrębnych klasach i `NewType`.

```python
from __future__ import annotations

from typing import Any, NewType, TypeVar
from uuid import UUID

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class _Brand:
    """
    Marker fantomowy dla typowania nominalnego.
    """

    __slots__ = ()


BrandT = TypeVar("BrandT", bound=str)


class BrandedStr(str):
    """
    Bazowa klasa dla identyfikatorów tekstowych o nominalnej tożsamości.

    Każdy branded identifier dziedziczy z tej klasy, dzięki czemu:
    - w runtime zachowuje się jak str,
    - jest kompatybilny z serializacją,
    - w warstwie typów jest odrębnym typem.
    """

    __slots__ = ()

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(min_length=1),
        )


class KnowledgeId(BrandedStr):
    __slots__ = ()


class SourceRef(BrandedStr):
    __slots__ = ()


class ClaimId(BrandedStr):
    __slots__ = ()


class EvidenceId(BrandedStr):
    __slots__ = ()


class ConflictId(BrandedStr):
    __slots__ = ()


class ScopeId(BrandedStr):
    __slots__ = ()


class OwnerId(BrandedStr):
    __slots__ = ()


class AgentId(BrandedStr):
    __slots__ = ()


class TaskId(BrandedStr):
    __slots__ = ()


class DecisionRef(BrandedStr):
    __slots__ = ()


class ExperimentRef(BrandedStr):
    __slots__ = ()


class FailureRef(BrandedStr):
    __slots__ = ()


class ExecutionId(BrandedStr):
    __slots__ = ()


class TenantId(BrandedStr):
    __slots__ = ()


class ProjectId(BrandedStr):
    __slots__ = ()


class CacheNamespace(BrandedStr):
    __slots__ = ()


class QueueName(BrandedStr):
    __slots__ = ()


class ObjectRef(BrandedStr):
    __slots__ = ()


class AuditChainId(BrandedStr):
    __slots__ = ()


class ArchiveRef(BrandedStr):
    __slots__ = ()


class KeyRef(BrandedStr):
    __slots__ = ()


RequestId = NewType("RequestId", UUID)
BundleId = NewType("BundleId", UUID)
ResolutionDecisionId = NewType("ResolutionDecisionId", UUID)
ProposalId = NewType("ProposalId", UUID)
CollectorRunId = NewType("CollectorRunId", UUID)
LockId = NewType("LockId", UUID)
StagingTransactionId = NewType("StagingTransactionId", UUID)
QueueMessageId = NewType("QueueMessageId", UUID)
AuditEntryId = NewType("AuditEntryId", UUID)
OccVersion = NewType("OccVersion", int)
FencingToken = NewType("FencingToken", int)
```

Zasada: **żadna nowa właściwość identyfikująca nie powinna być typu `str` ani `UUID` bezpośrednio**. Powinna korzystać z jednego z typów nominalnych powyżej lub nowego brandu utworzonego według tego samego wzorca.

### 1a.2. Agnostyczność technologiczna domeny

Domena nie może zależeć od typów specyficznych dla środowiska uruchomieniowego. Obowiązują następujące reguły:

- do reprezentacji surowych bajtów używamy `collections.abc.Buffer` w kontraktach oraz `bytes`, `memoryview` lub `bytearray` w implementacji,
- w dokumentacji cross-language reprezentacją bajtów jest `Uint8Array` lub jej odpowiednik,
- domena nie zna formatu MessagePack; kodowanie i dekodowanie należy do infrastruktury cache lub transportu,
- czas jest zawsze `datetime` w UTC z jawną strefą,
- ścieżki, URI i lokalizatory są neutralnymi typami tekstowymi,
- I/O, sieć, storage, cache, kolejki i konkurencja nie należą do modeli domenowych,
- modele domenowe są czystymi, niemutowalnymi strukturami danych,
- duże payloady są w domenie reprezentowane przez referencję, checksum i metadane, a nie przez wymuszenie konkretnego magazynu.

```python
from collections.abc import Buffer


class BinaryPayload(BrandedStr):
    """
    Neutralny lokalizator danych binarnych.
    """

    __slots__ = ()


def normalize_bytes(data: Buffer) -> bytes:
    """
    Granica konwersji do neutralnej reprezentacji bajtów.
    """
    return bytes(data)
```

### 1a.3. Generyczne konteksty

Rozstrzyganie wiedzy przebiega przez kilka faz: retrieval, normalizacja, ocena, budowa dowodów. Aby uniknąć niejawnego stanu i przenoszenia luźnych słowników, wprowadzamy jawny, generyczny kontekst rozstrzygania parametryzowany profilem oraz typem ładunku fazy.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar


class ResolutionProfile(StrEnum):
    NORMATIVE_COMPLIANCE = "normative_compliance"
    CONTRACT_CONFORMANCE = "contract_conformance"
    CURRENT_RUNTIME_STATE = "current_runtime_state"
    ARCHITECTURAL_INTENT = "architectural_intent"
    EMPIRICAL_EFFECTIVENESS = "empirical_effectiveness"
    HISTORICAL_CONTEXT = "historical_context"
    GENERAL_ADVICE = "general_advice"


PayloadT = TypeVar("PayloadT")
NextPayloadT = TypeVar("NextPayloadT")


@dataclass(frozen=True, slots=True)
class ResolutionContext(Generic[PayloadT]):
    request_id: RequestId
    profile: ResolutionProfile
    as_of: datetime
    policy_version: str
    resolver_version: str
    tenant_id: TenantId | None
    project_id: ProjectId | None
    agent_id: AgentId | None
    payload: PayloadT
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def advance(
        self,
        next_payload: NextPayloadT,
        *,
        note: str | None = None,
    ) -> ResolutionContext[NextPayloadT]:
        new_diagnostics = (
            (*self.diagnostics, note)
            if note is not None
            else self.diagnostics
        )
        return ResolutionContext(
            request_id=self.request_id,
            profile=self.profile,
            as_of=self.as_of,
            policy_version=self.policy_version,
            resolver_version=self.resolver_version,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            agent_id=self.agent_id,
            payload=next_payload,
            diagnostics=new_diagnostics,
        )
```

Fazy resolvera stają się funkcjami kształtu `ResolutionContext[A] -> ResolutionContext[B]`, co zapewnia audytowalność i eliminuje ukryty stan.

### 1a.4. Staging Area

Zmiany wiedzy kanonicznej nie mogą być stosowane bezpośrednio ani cząstkowo. Wprowadzamy **Staging Area** — mechanizm makiety transakcji, w którym proponowane zmiany są odkładane, walidowane i weryfikowane w izolacji, zanim zostaną commitnięte.

Staging Area jest agnostyczna technologicznie: nie zakłada konkretnego backendu Git, bazy ani storage. Definiuje jedynie kontrakt transakcyjny domeny. Szczegółowe modele znajdują się w sekcji 14a.

### 1a.5. Zasady wydajnościowe na granicach domeny

Wydajność jest odpowiedzialnością warstwy aplikacyjnej i infrastrukturalnej, ale jej kontrakty muszą być jawne:

- cache nie może zmieniać semantyki resolution,
- klucz cache musi obejmować kontekst autoryzacji, zakres, profil, wersję polityki, wersję resolvera i `as_of` lub kubełek czasu,
- cache nie może podnosić autorytetu danych,
- ujemne wyniki mogą być cache’owane tylko krótko,
- pełne payloady nie mogą być bezwarunkowo duplikowane pomiędzy PostgreSQL, Redisem i storage obiektowym,
- payload przekraczający ustalony próg powinien być przechowywany poza gorącym wierszem i wskazywany przez referencję,
- duże zadania nie mogą blokować synchronicznego request path,
- każda asynchroniczna operacja musi być idempotentna,
- retry musi mieć limit, exponential backoff i jitter,
- połączenia do PostgreSQL muszą przechodzić przez kontrolowany pool lub PgBouncer,
- cache i kolejki muszą mieć jawne limity pamięci, rozmiaru elementu i czasu retencji.

### 1a.6. Optymistyczna kontrola współbieżności (OCC guards)

Każda mutacja wiedzy kanonicznej, rejestru źródeł i statusu konfliktu podlega optymistycznej kontroli współbieżności. Blokady pesymistyczne (lease, advisory locks) są mechanizmem pomocniczym; źródłem poprawności jest OCC.

Zasady:

- każdy mutowalny logicznie zasób posiada monotoniczną wersję `occ_version` inkrementowaną przy każdej zaakceptowanej zmianie,
- każda operacja zapisu deklaruje `expected_version`; niezgodność powoduje odrzucenie z jawnym błędem konfliktu OCC, nigdy ciche nadpisanie,
- commit Staging Area weryfikuje jednocześnie `base_registry_version` oraz `occ_version` wszystkich modyfikowanych rekordów (multi-record compare-and-set w jednej transakcji bazodanowej),
- operacje z efektami zewnętrznymi (Git push, publikacja outbox) używają fencing tokenów wyprowadzonych z wersji OCC,
- konflikt OCC jest zdarzeniem audytowalnym: rejestrowany jest zasób, oczekiwana i faktyczna wersja, aktor oraz decyzja (retry, abort, eskalacja),
- retry po konflikcie OCC wymaga ponownego preflightu, jeżeli zmieniona wersja dotyczy danych wejściowych walidacji.

```python
from pydantic import BaseModel, ConfigDict, Field


class OccGuard(BaseModel):
    """
    Deklaracja warunku wersji dla pojedynczego zasobu.

    Commit stosujący zbiór OccGuard jest atomowy: wszystkie warunki
    muszą być spełnione w tej samej transakcji, inaczej całość
    jest odrzucana.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    resource_ref: SourceRef
    knowledge_id: KnowledgeId | None = None
    expected_version: OccVersion
    fencing_token: FencingToken | None = None


class OccConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resource_ref: SourceRef
    expected_version: OccVersion
    actual_version: OccVersion
    detected_at: datetime
    actor: AgentId | None = None
```

---

## 2. Pozycja warstwy w architekturze RAE

```text
RAE-Suite
│
├── RAE Control Plane
│   ├── Task Intake
│   ├── Planner
│   ├── Execution Coordinator
│   ├── Quality
│   ├── Auditor
│   └── RAE-Lab
│
├── Knowledge Governance Layer
│   ├── Canonical Registry
│   ├── Knowledge Resolution API
│   ├── Knowledge Resolution Engine
│   ├── Authority Resolver
│   ├── Conflict Detector
│   ├── Evidence Builder
│   ├── Drift Detector
│   ├── Knowledge Staging Area
│   └── Knowledge Promotion Workflow
│
├── Audit and Compliance Plane
│   ├── Audit Chain Writer (Hash Chaining)
│   ├── Audit Chain Verifier
│   ├── Anchoring Service
│   ├── Compliance Control Mapper (ISO 27001 / ISO 42001)
│   └── Archival Orchestrator (Cold Storage)
│
├── Performance and Delivery Infrastructure
│   ├── L1 Process Cache
│   ├── Redis Distributed Cache
│   ├── MessagePack Codec
│   ├── Async Work Queue
│   ├── Payload Object Storage
│   ├── Cold Storage (WORM)
│   ├── PostgreSQL
│   └── PgBouncer
│
├── RAE-agentic-memory
│   ├── semantic memory
│   ├── episodic memory
│   ├── reflective memory
│   ├── failures
│   ├── experiments
│   └── learned strategies
│
├── Phoenix
├── Hive
├── Quality
├── Auditor
└── Lab
```

Szczegółowy przepływ rozwiązywania wiedzy:

```text
Agent lub Planner
        │
        ▼
Knowledge Resolution API
        │
        ▼
1. Authentication, authorization i scope normalization
        │
        ▼
2. Wyliczenie bezpiecznego cache key
        │
        ├──────────────► L1 cache
        │                    │
        │                    ▼ miss
        ├──────────────► Redis L2, MessagePack
        │                    │
        │                    ▼ miss
        ▼
3. Klasyfikacja intencji
        │
        ▼
4. Określenie wymaganego typu wiedzy i dowodu
        │
        ▼
5. Równoległe zapytanie do zarejestrowanych źródeł
        │
        ▼
6. Normalizacja wyników
        │
        ▼
7. Ocena autorytetu, aktualności, zakresu i integralności
        │
        ▼
8. Wykrycie konfliktów i dryfu
        │
        ▼
9. Budowa Evidence Bundle
        │
        ▼
10. Trwały zapis artefaktu audytowego + dopisanie wpisu do łańcucha hashy
        │
        ▼
11. Resolution Decision
        │
        ├──────────────► cache write
        ├──────────────► async post-processing
        ▼
Planner / Quality / Auditor / Execution
```

Warstwa nie powinna być nazywana routerem OKF/RAG. Odpowiedniejsza nazwa to:

> **Knowledge Resolution Engine**

Rozwiązuje on pytanie na podstawie źródeł, ich autorytetu, zakresu, aktualności oraz jawnych reguł rozstrzygania. Wewnętrznie każda faza operuje na `ResolutionContext[PayloadT]`.

---

## 3. Zasady projektowe

### 3.1. Nie tworzyć nowej pamięci

Knowledge Governance Layer nie jest kolejnym magazynem pamięci. Nie zastępuje:

- semantic memory,
- episodic memory,
- reflective memory,
- failure memory,
- experiment memory,
- istniejącego API pamięci,
- Qdranta,
- indeksów embeddingowych,
- mechanizmu hybrid search.

Dodaje natomiast:

- rejestr źródeł,
- wspólny kontrakt DTO,
- rozróżnienie klasy wiedzy,
- rozróżnienie autorytetu,
- rozstrzyganie konfliktów,
- budowę pakietu dowodów,
- kontrolowany proces awansu wiedzy,
- transakcyjną Staging Area dla zmian,
- kryptograficzny łańcuch artefaktów audytowych,
- wydajnościową warstwę cache i dostarczania wyników,
- kolejki dla operacji, które nie muszą być wykonane synchronicznie.

### 3.2. Nie kopiować źródeł prawdy

OpenAPI, JSON Schema, polityki, ADR-y i kontrakty powinny pozostać w swoich źródłach prawdy.

Indeks wyszukiwania może przechowywać:

- identyfikator wiedzy,
- URI lub ścieżkę,
- commit SHA,
- checksum,
- fragment dokumentu,
- metadane,
- embedding pomocniczy,
- poziom autorytetu.

Embedding służy wyłącznie do znalezienia kandydata. Nie jest źródłem prawdy.

Redis również nie jest źródłem prawdy. Może zawierać jedynie:

- cache wyników,
- cache rekordów rejestru,
- cache znormalizowanych adapterów,
- krótkotrwałe checkpointy,
- tokeny koordynacyjne,
- deduplikację kolejek,
- lease i blokady o ograniczonym TTL.

### 3.3. Retrieval i resolution to różne operacje

**Retrieval** odpowiada na pytanie:

> Jakie potencjalnie powiązane informacje znalazłem?

**Resolution** odpowiada na pytanie:

> Które z tych informacji mają prawo zostać użyte do rozstrzygnięcia pytania?

Nie wolno utożsamiać najwyższego cosine similarity z najwyższym autorytetem.

### 3.4. Klasa wiedzy i poziom autorytetu są niezależne

`knowledge_class` opisuje, czego dotyczy informacja.

`authority_level` opisuje, jaką moc rozstrzygającą ma informacja.

Przykłady:

- polityka bezpieczeństwa może być `normative/canonical`,
- wynik testu może być `empirical/observed`,
- wynik eksperymentu może być `empirical/approved`,
- doświadczenie agenta może być `episodic/observed`,
- zewnętrzny artykuł może być `external/untrusted`,
- aktualny stan deploymentu może być `operational/observed`.

Sama klasa wiedzy nie wystarcza do podejmowania decyzji.

### 3.5. Aktualność ma znaczenie

Dokument kanoniczny może określać pożądany stan, natomiast telemetryka może opisywać aktualny stan rzeczywisty. Nie jest to automatycznie sprzeczność.

Przykład:

- polityka: „TLS 1.3 jest wymagane”,
- runtime: „aktywny deployment nadal używa TLS 1.2”.

To nie oznacza, że runtime unieważnia politykę. Oznacza naruszenie lub dryf.

Reguła rozstrzygania musi uwzględniać:

- typ pytania,
- zakres,
- moment czasu,
- status źródła,
- świeżość,
- integralność,
- poziom autorytetu.

### 3.6. Domena jest czysta i niemutowalna

Modele domenowe:

- nie mają zależności od I/O, sieci, storage ani frameworków,
- używają typów nominalnych,
- nie posiadają metod z efektami ubocznymi,
- są niemutowalne wszędzie tam, gdzie reprezentują snapshot lub artefakt audytowy.

### 3.7. Cache jest optymalizacją, nie semantyką

Cache:

- nie może ukrywać aktywnego konfliktu krytycznego,
- musi uwzględniać wersje źródeł i polityk,
- musi respektować granice tenantów,
- musi przechowywać wyłącznie dane, do których odczytu uprawniony byłby odbiorca,
- musi mieć możliwość selektywnej invalidacji,
- nie może używać samego tekstu zapytania jako klucza,
- nie może przechowywać sekretów w postaci jawnej,
- musi zawierać wersję formatu serializacji.

### 3.8. Duży payload nie należy do gorącego wiersza

W PostgreSQL nie należy przechowywać bez ograniczeń pełnych dokumentów, trace’ów, raportów, binarnych załączników i dużych Evidence Bundle w tabelach często skanowanych.

Należy rozdzielić:

- metadane i pola filtrujące,
- zwięzły snapshot do szybkiego odczytu,
- pełny payload,
- payload binarny,
- historię wersji.

Pełny payload może zostać zapisany:

- w osobnej tabeli payloadów,
- w partycjonowanej tabeli archiwalnej,
- w storage obiektowym,
- jako skompresowany obiekt wskazywany przez `content_ref`.

### 3.9. Operacje kosztowne są asynchroniczne

Poza synchroniczną ścieżkę należy przenosić:

- generowanie embeddingów,
- reindeksację,
- pobieranie dużych artefaktów,
- rekonstrukcję pełnych Evidence Bundle,
- porównania driftu obejmujące wiele źródeł,
- okresowe odświeżanie cache,
- kompakcję i archiwizację,
- eksport audytowy,
- RAE-Lab comparison,
- notyfikacje,
- ciężkie walidacje niezależne od bieżącej decyzji,
- weryfikację ciągłości łańcucha hashy,
- migrację do Cold Storage.

Operacja krytyczna dla bieżącego wyniku pozostaje synchroniczna albo zwraca jawny status `partial`, `blocked` lub `pending`, zamiast udawać kompletne rozstrzygnięcie.

Wyjątkiem od pełnej asynchroniczności jest dopisanie wpisu do łańcucha hashy dla decyzji wysokiego ryzyka: hash wpisu musi być wyliczony i trwale zapisany zanim decyzja zostanie zwrócona. Anchoring zewnętrzny pozostaje asynchroniczny.

### 3.10. Artefakty audytowe są append-only i łańcuchowane

Każdy trwały artefakt audytowy (Evidence Bundle, Resolution Decision, wynik commitu Staging Area, formalne naruszenie) jest:

- niemutowalny po zapisie,
- dopisywany do łańcucha hashy per tenant (Hash Chaining),
- weryfikowalny bez zaufania do pojedynczego magazynu,
- korygowany wyłącznie przez nowy artefakt wskazujący poprzednika.

Szczegóły w sekcji 23a.

---

## 4. Klasy wiedzy

### 4.1. Normative

Wiedza normatywna określa, jakie reguły obowiązują.

Przykłady:

- polityki bezpieczeństwa,
- kontrakty agentów,
- zasady akceptacji,
- budżety,
- uprawnienia,
- FactorySpec,
- wymagania compliance,
- zasady routingu modeli,
- reguły dotyczące danych wrażliwych.

### 4.2. Architectural

Wiedza architektoniczna opisuje, jak system powinien być zbudowany.

Przykłady:

- ADR,
- diagramy,
- granice modułów,
- kontrakty API,
- schematy danych,
- zależności między komponentami,
- topologia systemu,
- zasady komunikacji między agentami.

### 4.3. Operational

Wiedza operacyjna opisuje aktualne lub deklarowane działanie systemu.

Przykłady:

- stan deploymentu,
- wersje usług,
- aktywne feature flags,
- stan kolejek,
- stan kontenerów,
- konfiguracja środowiska,
- aktywna wersja Keycloak,
- konfiguracja klienta OIDC,
- stan Kubernetes.

### 4.4. Empirical

Wiedza empiryczna wynika z pomiaru, testu lub eksperymentu.

Przykłady:

- benchmarki,
- wyniki SonarQube,
- wyniki Playwright,
- testy integracyjne,
- testy mutacyjne,
- wyniki canary,
- security scans,
- pomiary latency,
- wyniki eksperymentów RAE-Lab.

Wynik empiryczny powinien posiadać zakres, metodę pomiaru, timestamp oraz informację o środowisku.

### 4.5. Episodic

Wiedza epizodyczna opisuje zdarzenia z konkretnych zadań lub trajektorii.

Przykłady:

- trajektoria agenta,
- podjęte decyzje,
- błąd wykonania,
- rollback,
- użyte narzędzia,
- obserwowany rezultat,
- kontekst zadania,
- wcześniejsza porażka.

Wiedza epizodyczna nie staje się automatycznie wiedzą kanoniczną.

### 4.6. External

Wiedza zewnętrzna pochodzi spoza kontrolowanego środowiska RAE.

Przykłady:

- dokumenty,
- sieć,
- PDF,
- wiadomości,
- artykuły,
- dokumentacja dostawców,
- systemy zewnętrzne,
- odpowiedzi zewnętrznych modeli.

Wiedza zewnętrzna może być użyteczna, ale nie powinna samodzielnie zastępować aktywnej polityki ani kanonicznego kontraktu.

---

## 5. Poziomy autorytetu

### 5.1. `canonical`

Źródło prawdy zatwierdzone przez właściciela domeny i obowiązujące w określonym zakresie.

### 5.2. `approved`

Informacja została zatwierdzona, ale nie jest głównym źródłem normatywnym albo obowiązuje w ograniczonym zakresie.

### 5.3. `observed`

Informacja została zaobserwowana przez system, test, telemetrykę lub adapter.

### 5.4. `inferred`

Informacja została wywnioskowana przez RAE, model, agregator albo regułę analityczną.

Wniosek musi wskazywać:

- przesłanki,
- metodę inferencji,
- poziom pewności,
- czas powstania,
- autora lub komponent,
- możliwość odtworzenia.

### 5.5. `untrusted`

Informacja nie została zweryfikowana lub pochodzi z niekontrolowanego źródła.

`untrusted` może być użyte do generowania hipotez, ale nie powinno samodzielnie uzasadniać decyzji wysokiego ryzyka.

### 5.6. Rzeczywista kolejność rozstrzygania

Domyślna kolejność dla decyzji normatywnych:

1. aktywna polityka lub kontrakt,
2. kanoniczny schemat maszynowy,
3. zatwierdzona decyzja architektoniczna,
4. zatwierdzone instrukcje operacyjne,
5. aktualny stan runtime jako dowód stanu faktycznego,
6. zweryfikowany wynik testu lub eksperymentu,
7. pamięć doświadczeń RAE,
8. wiedza semantyczna RAG,
9. wiedza zewnętrzna,
10. wniosek modelu.

Ta lista nie jest bezwarunkowym rankingiem wszystkich pytań. Dla pytań o stan bieżący runtime może mieć pierwszeństwo przed dokumentacją. Dla pytań o to, co jest dozwolone, polityka pozostaje nadrzędna wobec obserwacji.

---

## 6. Kanoniczny model domenowy

Poniższe modele są kontraktem domenowym. Istniejące modele RAE, takie jak `DecisionEvidence`, `Outcome`, `Failure`, `Experiment`, `InsightPack` i `FailurePatternPack`, powinny zostać zachowane.

```python
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeClass(StrEnum):
    NORMATIVE = "normative"
    ARCHITECTURAL = "architectural"
    OPERATIONAL = "operational"
    EMPIRICAL = "empirical"
    EPISODIC = "episodic"
    EXTERNAL = "external"


class AuthorityLevel(StrEnum):
    CANONICAL = "canonical"
    APPROVED = "approved"
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNTRUSTED = "untrusted"


class KnowledgeLifecycleStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"


class SourceType(StrEnum):
    GIT = "git"
    OPENAPI = "openapi"
    JSON_SCHEMA = "json_schema"
    POLICY = "policy"
    ADR = "adr"
    RUNBOOK = "runbook"
    FACTORY_SPEC = "factory_spec"
    RAE_MEMORY = "rae_memory"
    EXPERIMENT = "experiment"
    TEST_REPORT = "test_report"
    SONARQUBE = "sonarqube"
    PLAYWRIGHT = "playwright"
    CI_CD = "ci_cd"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    TELEMETRY = "telemetry"
    OTEL = "otel"
    EXTERNAL_DOCUMENT = "external_document"
    EXTERNAL_API = "external_api"
    MODEL_INFERENCE = "model_inference"


class IntegrityStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"


class ScopeType(StrEnum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    SERVICE = "service"
    AGENT = "agent"
    TASK = "task"
    RESOURCE = "resource"


class KnowledgeScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_type: ScopeType
    scope_id: ScopeId
    environment: str | None = None
    region: str | None = None
    tenant_id: TenantId | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_ref: SourceRef
    locator: str | None = None
    repository: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    version: str | None = None
    fetched_at: datetime | None = None
    observed_at: datetime | None = None
    produced_by: str | None = None
    collector_run_id: CollectorRunId | None = None
    signature: BinaryPayload | None = None
    integrity_status: IntegrityStatus = IntegrityStatus.UNVERIFIED


class PayloadStorageClass(StrEnum):
    INLINE = "inline"
    DATABASE_EXTERNAL = "database_external"
    OBJECT_STORAGE = "object_storage"
    COLD_STORAGE = "cold_storage"
    SOURCE_ONLY = "source_only"


class KnowledgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    knowledge_id: KnowledgeId
    knowledge_class: KnowledgeClass
    authority_level: AuthorityLevel
    source_type: SourceType
    provenance: Provenance

    owner: OwnerId
    domain: str | None = None
    version: str | None = None
    occ_version: int = Field(default=1, ge=1)

    status: KnowledgeLifecycleStatus = KnowledgeLifecycleStatus.ACTIVE
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    scopes: tuple[KnowledgeScope, ...] = Field(default_factory=tuple)
    supersedes: tuple[KnowledgeId, ...] = Field(default_factory=tuple)
    superseded_by: KnowledgeId | None = None
    related_records: tuple[KnowledgeId, ...] = Field(default_factory=tuple)

    checksum: str = Field(
        pattern=r"^(sha256|sha384|sha512):[A-Fa-f0-9]{16,}$"
    )
    content_summary: str = Field(min_length=1)
    content_locator: str | None = None

    payload_storage_class: PayloadStorageClass = PayloadStorageClass.SOURCE_ONLY
    payload_size_bytes: int | None = Field(default=None, ge=0)
    payload_content_type: str | None = None
    payload_compression: str | None = None
    archive_ref: ArchiveRef | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    @field_validator("valid_until")
    @classmethod
    def validate_validity_interval(
        cls,
        value: datetime | None,
        info: Any,
    ) -> datetime | None:
        valid_from = info.data.get("valid_from")
        if value is not None and valid_from is not None and value <= valid_from:
            raise ValueError("valid_until must be later than valid_from")
        return value

    @field_validator(
        "created_at",
        "updated_at",
        "valid_from",
        "valid_until",
    )
    @classmethod
    def require_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value
```

### 6.1. Uwagi do `KnowledgeRecord`

Model:

- używa identyfikatorów nominalnych,
- jest niemutowalny,
- rozdziela klasę wiedzy i autorytet,
- wydziela pochodzenie,
- posiada status cyklu życia, w tym `archived` dla rekordów przeniesionych do Cold Storage,
- posiada zakres obowiązywania,
- przechowuje relacje zastępowania,
- waliduje przedział ważności,
- nie traktuje `content_summary` jako źródła prawdy,
- zawiera jawne metadane o lokalizacji i rozmiarze payloadu,
- umożliwia przechowywanie dużej treści poza gorącym rekordem,
- niesie `occ_version` używane przez OCC guards przy każdej mutacji logicznej (mutacja tworzy nowy snapshot z inkrementowaną wersją),
- może wskazywać `archive_ref` do manifestu archiwum Cold Storage.

`KnowledgeRecord` może wskazywać na:

- plik w Git,
- dokument OpenAPI,
- rekord pamięci,
- raport testowy,
- ślad OTEL,
- wynik eksperymentu,
- artefakt w storage,
- artefakt w Cold Storage,
- dokument zewnętrzny.

### 6.2. Reguła przechowywania payloadów

Domyślna polityka:

| Rozmiar payloadu | Zalecane przechowywanie |
|---|---|
| do 16 KiB | inline, jeśli odczytywany razem z rekordem |
| 16–256 KiB | osobna kolumna lub tabela payloadów, odczyt na żądanie |
| 256 KiB–2 MiB | osobna tabela payloadów lub storage obiektowy |
| powyżej 2 MiB | storage obiektowy, w bazie tylko referencja i checksum |
| payload binarny lub archiwum | storage obiektowy niezależnie od rozmiaru, poza uzasadnionymi wyjątkami |
| payload historyczny poza oknem retencji hot/warm | Cold Storage (WORM), w bazie manifest i checksum |

Progi są konfigurowalne i muszą zostać potwierdzone benchmarkiem na docelowym workloadzie.

---

## 7. Model twierdzeń i dowodów

```python
class ClaimPolarity(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class EvidenceStrength(StrEnum):
    DIRECT = "direct"
    CORROBORATED = "corroborated"
    INDIRECT = "indirect"
    HYPOTHESIS = "hypothesis"


class ExtractionMethod(StrEnum):
    STRUCTURED_FIELD = "structured_field"
    SCHEMA_PARSER = "schema_parser"
    RULE = "rule"
    HUMAN_REVIEW = "human_review"
    MODEL_EXTRACTION = "model_extraction"
    RUNTIME_PROBE = "runtime_probe"
    TEST_ASSERTION = "test_assertion"


class KnowledgeClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: ClaimId
    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object_value: Any

    polarity: ClaimPolarity = ClaimPolarity.SUPPORTS
    evidence_strength: EvidenceStrength = EvidenceStrength.INDIRECT

    knowledge_id: KnowledgeId
    source_ref: SourceRef
    scope: KnowledgeScope | None = None

    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    extraction_method: ExtractionMethod
    confidence: float = Field(ge=0.0, le=1.0)
    statement: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

Przykładowe twierdzenia:

```text
subject: endpoint:/companies
predicate: response.field
object_value: companyID
polarity: supports
source: openapi-main
```

```text
subject: endpoint:/companies
predicate: response.field.required
object_value: true
polarity: supports
source: openapi-main
```

```text
subject: endpoint:/companies
predicate: response.field.nullable
object_value: true
polarity: supports
source: integration-test-run-391
```

Dzięki temu konflikt może być wykryty semantycznie, a nie tylko tekstowo.

Duże wartości `object_value` nie powinny przechowywać pełnych dokumentów. Powinny wskazywać skróconą wartość, hash albo `ObjectRef`.

---

## 8. Wspólny kontrakt adapterów

Każdy adapter powinien zwracać wspólny, znormalizowany kontrakt.

```python
class RetrievalMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    semantic_score: float = Field(ge=0.0, le=1.0)
    lexical_score: float = Field(ge=0.0, le=1.0)
    hybrid_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


class RetrievedKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    knowledge_id: KnowledgeId
    content: str = Field(min_length=1)

    source_ref: SourceRef
    source_type: SourceType
    knowledge_class: KnowledgeClass
    authority_level: AuthorityLevel
    lifecycle_status: KnowledgeLifecycleStatus

    owner: OwnerId
    scopes: tuple[KnowledgeScope, ...] = Field(default_factory=tuple)
    provenance: Provenance

    observed_at: datetime | None = None
    version: str | None = None
    checksum: str | None = None

    retrieval_match: RetrievalMatch | None = None
    claims: tuple[KnowledgeClaim, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

Adaptery:

```text
Knowledge Resolution Engine
├── CanonicalSourceAdapter
├── RAEAgenticMemoryAdapter
├── GitRuntimeAdapter
├── OpenAPIAdapter
├── JsonSchemaAdapter
├── PolicyAdapter
├── FactorySpecAdapter
├── SonarAdapter
├── PlaywrightAdapter
├── CiCdAdapter
├── ContainerAdapter
├── KubernetesAdapter
├── TelemetryAdapter
├── OtelAdapter
└── ExternalKnowledgeAdapter
```

Kontrakt protokołu:

```python
from collections.abc import Buffer
from typing import Protocol, runtime_checkable


@runtime_checkable
class KnowledgeAdapter(Protocol):
    source_type: SourceType

    async def retrieve(
        self,
        ctx: ResolutionContext[Any],
        query: str,
        *,
        max_results: int,
    ) -> tuple[RetrievedKnowledge, ...]: ...

    def normalize_raw_bytes(self, data: Buffer) -> bytes:
        ...
```

Każdy adapter musi:

1. identyfikować źródło,
2. przekazywać pochodzenie,
3. przekazywać timestamp,
4. przekazywać checksum lub określać jego brak,
5. zwracać klasę wiedzy,
6. zwracać poziom autorytetu nadany przez rejestr,
7. oznaczać integralność,
8. nie zmieniać treści źródłowej,
9. nie podnosić samodzielnie poziomu autorytetu,
10. normalizować dane binarne,
11. wspierać deadline i anulowanie,
12. nie wykonywać nieograniczonych zapytań,
13. zwracać wyniki stronicowane lub limitowane,
14. nie pobierać pełnych dużych payloadów, jeśli wystarczają metadane i excerpt.

Adapter nie może samodzielnie uznać wyników zewnętrznego API za `canonical`.

### 8.1. Cache adapterów

Cache adaptera może przechowywać wyłącznie wynik po normalizacji. Klucz powinien zawierać:

- `source_ref`,
- hash znormalizowanego zapytania,
- zakres,
- tenant,
- profil,
- wersję źródła lub checkpoint,
- wersję normalizatora,
- limit wyników.

Freshness TTL źródła pozostaje nadrzędny. Cache adaptera nie może przedłużyć ważności obserwacji runtime.

---

## 9. Evidence Bundle

Wynik Knowledge Resolution Engine powinien być ustrukturyzowanym pakietem dowodów.

### 9.1. Evidence Item

```python
from uuid import uuid4


def _new_evidence_id() -> EvidenceId:
    return EvidenceId(str(uuid4()))


class EvidenceRole(StrEnum):
    PRIMARY = "primary"
    CORROBORATING = "corroborating"
    CONTEXT = "context"
    CONFLICTING = "conflicting"
    NEGATIVE = "negative"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: EvidenceId = Field(default_factory=_new_evidence_id)
    knowledge_id: KnowledgeId
    source_ref: SourceRef
    source_type: SourceType
    authority_level: AuthorityLevel

    claim_ids: tuple[ClaimId, ...] = Field(default_factory=tuple)
    excerpt: str | None = None
    locator: str | None = None
    checksum: str | None = None

    role: EvidenceRole
    relevance: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(ge=0.0, le=1.0)
    scope_match: float = Field(ge=0.0, le=1.0)
    integrity_score: float = Field(ge=0.0, le=1.0)
    authority_score: float = Field(ge=0.0, le=1.0)

    supports: tuple[ClaimId, ...] = Field(default_factory=tuple)
    contradicts: tuple[ClaimId, ...] = Field(default_factory=tuple)

    collected_at: datetime
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

`relevance`, `freshness`, `scope_match`, `integrity_score` i `authority_score` muszą być rozdzielone.

### 9.2. Conflict

```python
def _new_conflict_id() -> ConflictId:
    return ConflictId(str(uuid4()))


class ConflictType(StrEnum):
    VERSION = "version"
    SEMANTIC = "semantic"
    SCOPE = "scope"
    TEMPORAL = "temporal"
    RUNTIME_DRIFT = "runtime_drift"
    POLICY_VIOLATION = "policy_violation"
    INTEGRITY = "integrity"
    DUPLICATE_IDENTITY = "duplicate_identity"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"


class ConflictSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    WAIVED = "waived"
    BLOCKED = "blocked"


class KnowledgeConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: ConflictId = Field(default_factory=_new_conflict_id)
    subject: str = Field(min_length=1)

    source_a: SourceRef
    source_b: SourceRef
    knowledge_id_a: KnowledgeId | None = None
    knowledge_id_b: KnowledgeId | None = None

    claim_a: ClaimId | None = None
    claim_b: ClaimId | None = None

    conflict_type: ConflictType
    severity: ConflictSeverity
    status: ConflictStatus = ConflictStatus.OPEN

    preferred_source: SourceRef | None = None
    resolution_rule: str | None = None
    rationale: str | None = None

    detected_at: datetime
    detected_by: str
    requires_human_review: bool = False
    blocks_execution: bool = False

    resolution_refs: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### 9.3. Resolution Status

```python
def _new_bundle_id() -> BundleId:
    return BundleId(uuid4())


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    RESOLVED_WITH_WARNING = "resolved_with_warning"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"
    NO_EVIDENCE = "no_evidence"
    PARTIAL = "partial"


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: BundleId = Field(default_factory=_new_bundle_id)
    query: str = Field(min_length=1)
    task_id: TaskId | None = None
    decision_id: DecisionRef | None = None
    execution_id: ExecutionId | None = None

    resolution_profile: ResolutionProfile

    evidence: tuple[EvidenceItem, ...] = Field(default_factory=tuple)
    claims: tuple[KnowledgeClaim, ...] = Field(default_factory=tuple)
    conflicts: tuple[KnowledgeConflict, ...] = Field(default_factory=tuple)

    selected_sources: tuple[SourceRef, ...] = Field(default_factory=tuple)
    rejected_sources: tuple[SourceRef, ...] = Field(default_factory=tuple)
    unresolved_questions: tuple[str, ...] = Field(default_factory=tuple)

    confidence: float = Field(ge=0.0, le=1.0)
    evidence_coverage: float = Field(ge=0.0, le=1.0)
    resolution_status: ResolutionStatus

    generated_at: datetime
    resolver_version: str
    policy_version: str

    supersedes_bundle: BundleId | None = None

    requires_quality_review: bool = False
    requires_auditor_review: bool = False
    blocks_execution: bool = False

    bundle_hash: str | None = None
    prev_bundle_hash: str | None = None
    audit_chain_id: AuditChainId | None = None
    chain_sequence: int | None = Field(default=None, ge=0)

    metadata: dict[str, Any] = Field(default_factory=dict)
```

Pola `bundle_hash`, `prev_bundle_hash`, `audit_chain_id` i `chain_sequence` są wypełniane w momencie trwałego zapisu przez Audit Chain Writer (sekcja 23a). `bundle_hash` jest wyliczany z kanonicznej, deterministycznej serializacji bundle z wyzerowanymi polami łańcucha. Bundle bez uzupełnionego łańcucha nie może być podstawą decyzji wysokiego ryzyka.

`EvidenceBundle` wskazuje istniejące:

- `DecisionEvidence`,
- `Outcome`,
- `Failure`,
- `Experiment`,
- `FailurePatternPack`,
- `InsightPack`,
- `ActionTrace`.

### 9.4. Wydajne przechowywanie Evidence Bundle

Pełny bundle może być duży. Należy przechowywać oddzielnie:

1. nagłówek bundle:
   - identyfikatory,
   - status,
   - confidence,
   - policy version,
   - resolver version,
   - flags,
   - pola łańcucha hashy;
2. indeks źródeł i konfliktów;
3. pełny dokument serializowany;
4. duże excerpt lub załączniki.

Synchroniczne zapytania listujące bundle nie powinny pobierać pełnego payloadu. Pełny dokument jest pobierany wyłącznie przez endpoint szczegółowy lub eksport audytowy.

`bundle_hash` obejmuje pełny dokument, dlatego rekonstrukcja bundle z payloadu (w tym z Cold Storage) musi być weryfikowana względem hasha z nagłówka i łańcucha.

---

## 10. Knowledge Resolution Request i Response

```python
def _new_request_id() -> RequestId:
    return RequestId(uuid4())


class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: RequestId = Field(default_factory=_new_request_id)
    query: str = Field(min_length=1)

    task_id: TaskId | None = None
    agent_id: AgentId | None = None
    project_id: ProjectId | None = None
    environment: str | None = None
    tenant_id: TenantId | None = None

    resolution_profile: ResolutionProfile

    required_knowledge_classes: tuple[KnowledgeClass, ...] = Field(
        default_factory=tuple
    )
    required_source_types: tuple[SourceType, ...] = Field(
        default_factory=tuple
    )

    as_of: datetime | None = None
    max_age_seconds: int | None = Field(default=None, ge=0)
    min_authority: AuthorityLevel | None = None

    allowed_scope: tuple[KnowledgeScope, ...] = Field(default_factory=tuple)
    include_external: bool = False
    include_untrusted: bool = False

    fail_on_critical_conflict: bool = True
    require_reproducible_evidence: bool = False
    max_results_per_source: int = Field(default=20, ge=1, le=500)

    metadata: dict[str, Any] = Field(default_factory=dict)
```

```python
def _new_decision_id() -> ResolutionDecisionId:
    return ResolutionDecisionId(uuid4())


class ResolutionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: ResolutionDecisionId = Field(default_factory=_new_decision_id)
    selected_claim_ids: tuple[ClaimId, ...] = Field(default_factory=tuple)
    selected_source_refs: tuple[SourceRef, ...] = Field(default_factory=tuple)

    decision_summary: str = Field(min_length=1)
    authority_rule_applied: str = Field(min_length=1)
    rejected_or_overridden_claims: tuple[ClaimId, ...] = Field(
        default_factory=tuple
    )

    status: ResolutionStatus
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)

    created_at: datetime
```

```python
class ResolutionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: RequestId
    evidence_bundle: EvidenceBundle
    decision: ResolutionDecision

    latency_ms: int = Field(ge=0)
    fallback_used: bool = False
    legacy_result_hash: str | None = None
```

### 10.1. Kontrakt odpowiedzi asynchronicznej

```python
class AsyncResolutionStatus(StrEnum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


class AsyncResolutionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: RequestId
    message_id: QueueMessageId
    status: AsyncResolutionStatus
    status_locator: str
    accepted_at: datetime
    retry_after_seconds: int | None = Field(default=None, ge=0)
```

API może zwrócić `202 Accepted`, jeśli:

- request przekracza budżet synchroniczny,
- wymaga pobrania dużych artefaktów,
- obejmuje kosztowną analizę wielu źródeł,
- profil dopuszcza wynik odroczony,
- operacja nie blokuje bezpośrednio krytycznego wykonania.

---

## 11. Hierarchia autorytetu i reguły rozstrzygania

### 11.1. Autorytet nie jest pojedynczym rankingiem

Nie należy implementować rozstrzygania jako prostego:

```text
canonical > approved > observed > inferred > untrusted
```

Źródła odpowiadają na różne pytania. Resolver najpierw wybiera profil, a dopiero potem stosuje reguły autorytetu.

### 11.2. Przykładowe reguły profili

#### `normative_compliance`

1. aktywna polityka,
2. kontrakt,
3. kanoniczny schemat,
4. zatwierdzony ADR,
5. wynik audytu,
6. runtime jako dowód naruszenia,
7. pozostałe źródła.

#### `contract_conformance`

1. aktywne OpenAPI,
2. JSON Schema,
3. kontrakt zdarzenia,
4. testy kontraktowe,
5. implementacja runtime,
6. dokumentacja opisowa,
7. pamięć agenta,
8. źródła zewnętrzne.

#### `current_runtime_state`

1. świeży, zweryfikowany probe runtime,
2. telemetryka,
3. stan Kubernetes lub kontenera,
4. pipeline deploymentu,
5. konfiguracja deklaratywna,
6. dokumentacja kanoniczna jako stan oczekiwany,
7. pamięć historyczna.

#### `architectural_intent`

1. aktywny ADR,
2. granice modułów,
3. kontrakt architektoniczny,
4. zatwierdzone diagramy,
5. implementacja,
6. runbook,
7. pamięć doświadczeń.

#### `empirical_effectiveness`

1. powtarzalny wynik eksperymentu,
2. zweryfikowany benchmark,
3. test integracyjny,
4. wynik canary,
5. obserwacja produkcyjna,
6. pojedynczy epizod,
7. wniosek modelu.

### 11.3. Reguła świeżości

Świeżość nie może podnosić poziomu autorytetu. Może wpływać na użyteczność źródła w profilu dotyczącym aktualnego stanu.

### 11.4. Reguła zakresu

Źródło może rozstrzygać wyłącznie w swoim zakresie.

Zakres obejmuje:

- projekt,
- usługę,
- środowisko,
- region,
- tenant,
- agenta,
- typ zasobu,
- przedział czasu,
- domenę biznesową.

### 11.5. Cache i reguły autorytetu

Wynik cache jest ważny tylko wtedy, gdy nadal obowiązują:

- ta sama wersja polityki,
- ta sama wersja resolvera,
- zgodna wersja rejestru,
- zgodny zakres,
- zgodny tenant,
- nieprzekroczony maksymalny wiek dowodów,
- brak zdarzenia invalidacyjnego dla źródła,
- zgodna wersja algorytmu autoryzacji.

Cache hit nie może pominąć sprawdzenia uprawnień.

---

## 12. Conflict Detection

RAE powinno automatycznie wykrywać sprzeczności. Nie wolno cicho wybierać jednego fragmentu i odrzucać pozostałych bez śladu audytowego.

### 12.1. Przykłady konfliktów

#### Konflikt wersji

```text
ADR mówi PostgreSQL 17.
docker-compose używa PostgreSQL 16.
runbook mówi PostgreSQL 15.
```

#### Konflikt kontraktu

```text
OpenAPI deklaruje pole wymagane.
Backend zwraca je czasami jako null.
Test integracyjny akceptuje null.
```

#### Konflikt polityki

```text
Polityka mówi, że refresh token nie może być przechowywany w localStorage.
Kod klienta zapisuje refresh token w localStorage.
```

#### Konflikt zakresu

```text
Reguła obowiązuje w produkcji.
Resolver próbuje zastosować ją do środowiska testowego.
```

#### Konflikt czasowy

```text
Dokument obowiązywał przed migracją.
Runtime pochodzi już z okresu po migracji.
```

#### Konflikt integralności

```text
Indeks wskazuje checksum inną niż checksum pobranego pliku.
```

### 12.2. Reakcje na konflikt

| Poziom | Domyślna reakcja |
|---|---|
| `info` | Zapisz w Evidence Bundle |
| `warning` | Kontynuuj z ostrzeżeniem |
| `high` | Wymagana ocena Quality lub Auditor |
| `critical` | Zablokuj wykonanie |

`blocks_execution` musi być wyliczane przez politykę.

### 12.3. Formalne naruszenie

```text
Adapter / dział / test / runtime
              │
              ▼
      sygnał lub konflikt
              │
              ▼
      Knowledge Conflict
              │
              ▼
          Quality
              │
              ▼
          Auditor
              │
              ▼
      formalne naruszenie
```

Formalne naruszenie jest artefaktem audytowym i podlega Hash Chaining zgodnie z sekcją 23a.

### 12.4. Inwalidacja cache po konflikcie

Wykrycie konfliktu powinno publikować zdarzenie invalidacyjne obejmujące:

- powiązane `knowledge_id`,
- źródła,
- scope,
- tenant,
- wersję rejestru,
- typ konfliktu.

Dla konfliktów `high` i `critical` należy unieważnić:

- cache gotowego resolution,
- cache znormalizowanych rekordów źródeł,
- negatywny cache dotyczący braku konfliktu.

---

## 13. Kanoniczna wiedza jako kod

```text
knowledge/
├── architecture/
│   ├── adr/
│   ├── diagrams/
│   └── boundaries/
├── contracts/
│   ├── openapi/
│   ├── json-schema/
│   ├── events/
│   └── capabilities/
├── policies/
│   ├── security/
│   ├── quality/
│   ├── budgets/
│   └── agent-behavior/
├── operations/
│   ├── runbooks/
│   ├── recovery/
│   └── provisioning/
├── domains/
│   ├── auth/
│   ├── editor/
│   ├── billing/
│   └── tenants/
├── experiments/
│   ├── approved/
│   └── archived/
└── registry.yaml
```

### 13.1. Kolejność preferowanych formatów

1. Pydantic lub JSON Schema,
2. OpenAPI,
3. policy DSL lub YAML,
4. FactorySpec,
5. ADR,
6. Markdown,
7. Mermaid lub PlantUML.

### 13.2. Rejestr źródeł

```yaml
version: "1.0"

sources:
  - id: openapi-main
    type: openapi
    knowledge_class: architectural
    authority: canonical
    owner: api-team
    path: contracts/openapi/openapi.yaml
    repository: git://rae-suite
    branch: main
    scope:
      - type: project
        id: rae-suite
      - type: environment
        id: all
    validation:
      required: true
      schema_check: true
      signed: true
    cache:
      metadata_ttl_seconds: 300
      content_ttl_seconds: 60
      stale_while_revalidate_seconds: 120

  - id: security-policy-refresh-token
    type: policy
    knowledge_class: normative
    authority: canonical
    owner: security
    path: policies/security/refresh-token.yaml
    scope:
      - type: service
        id: auth
      - type: environment
        id: production
    cache:
      metadata_ttl_seconds: 300
      content_ttl_seconds: 60

  - id: runtime-kubernetes-production
    type: kubernetes
    knowledge_class: operational
    authority: observed
    owner: platform-team
    endpoint: https://kubernetes-api.internal
    freshness_ttl_seconds: 60
    cache:
      metadata_ttl_seconds: 15
      content_ttl_seconds: 10
      stale_while_revalidate_seconds: 0
```

Rejestr powinien być wersjonowany, walidowany i podlegać kontroli zmian. Każda wersja rejestru posiada `occ_version` i jest chroniona przez OCC guards przy commicie Staging Area.

---

## 14. Read Path i Write Path

### 14.1. Read Path

```text
Agent
  │
  ▼
Knowledge Resolution API
  │
  ▼
Authentication and authorization
  │
  ▼
Scope filtering
  │
  ▼
L1/L2 cache lookup
  │
  ▼
Hybrid retrieval
  │
  ▼
Authority resolution
  │
  ▼
Conflict detection
  │
  ▼
Evidence Bundle
  │
  ▼
Durable write + audit chain append
  │
  ▼
Cache population and async post-processing
```

Read path musi respektować:

- uprawnienia agenta,
- zakres tenantów,
- klasyfikację danych,
- środowisko,
- polityki bezpieczeństwa,
- wymagany poziom autorytetu,
- ograniczenia danych wrażliwych,
- budżet czasu,
- maksymalny rozmiar odpowiedzi,
- dopuszczalny poziom stale data.

### 14.2. Write Path

```text
Agent
  │
  ▼
KnowledgeChangeProposal
  │
  ▼
Staging Area
  │
  ▼
Evidence validation
  │
  ▼
Quality validation
  │
  ▼
Auditor / domain owner review
  │
  ▼
StagingTransaction.commit()  ◄── OCC guards + fencing token
  │
  ▼
canonical source update
  │
  ▼
registry update
  │
  ├──────────────► transactional outbox
  ├──────────────► audit chain append
  ▼
re-index queue
  │
  ├──────────────► cache invalidation queue
  └──────────────► drift re-evaluation queue
```

```python
def _new_proposal_id() -> ProposalId:
    return ProposalId(uuid4())


class ChangeType(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DEPRECATE = "deprecate"
    SUPERSEDE = "supersede"
    REVOKE = "revoke"


class RiskClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProposalStatus(StrEnum):
    DRAFT = "draft"
    VALIDATING = "validating"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"
    ROLLED_BACK = "rolled_back"


class KnowledgeChangeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: ProposalId = Field(default_factory=_new_proposal_id)
    target_ref: SourceRef
    target_knowledge_id: KnowledgeId | None = None

    change_type: ChangeType
    rationale: str = Field(min_length=1)
    proposed_content_hash: str | None = None
    proposed_content_ref: BinaryPayload | None = None

    evidence_refs: tuple[EvidenceId, ...] = Field(min_length=1)
    related_decision_ids: tuple[DecisionRef, ...] = Field(default_factory=tuple)
    related_experiment_ids: tuple[ExperimentRef, ...] = Field(
        default_factory=tuple
    )
    related_failure_ids: tuple[FailureRef, ...] = Field(default_factory=tuple)

    risk_class: RiskClass
    validation_plan: tuple[str, ...] = Field(min_length=1)
    rollback_plan: str = Field(min_length=1)

    requested_by: AgentId
    owner: OwnerId
    status: ProposalStatus = ProposalStatus.DRAFT

    created_at: datetime
    updated_at: datetime
    approved_by: tuple[OwnerId, ...] = Field(default_factory=tuple)
    merged_commit_sha: str | None = None
```

Agent nie może bezpośrednio:

- zmienić `authority_level` na `canonical`,
- usunąć źródła bez śladu,
- nadpisać aktywnej polityki,
- oznaczyć konfliktu jako rozwiązanego bez uprawnień,
- zmienić checksumu bez zmiany źródła,
- dopisać dowodu po fakcie bez czasu i pochodzenia,
- ominąć Staging Area,
- ominąć OCC guards ani modyfikować `occ_version` poza commit path,
- modyfikować ani usuwać wpisów łańcucha hashy.

### 14.3. Transactional Outbox

Commit zmiany i publikacja zdarzeń nie mogą tworzyć okna niespójności. Jeżeli źródłem stanu jest PostgreSQL, należy zastosować transactional outbox:

1. commit danych i wpisu outbox następuje w tej samej transakcji,
2. worker publikuje zdarzenie,
3. publikacja jest idempotentna,
4. rekord outbox otrzymuje status dostarczenia,
5. retry nie tworzy duplikatu logicznego,
6. konsument deduplikuje po `event_id`.

Outbox obsługuje:

- reindeksację,
- invalidację cache,
- odświeżenie materialized views,
- drift detection,
- notyfikacje,
- audyt,
- dual-write reconciliation (sekcja 17.2a),
- zadania archiwizacyjne Cold Storage.

---

## 14a. Knowledge Staging Area — transakcyjne zmiany wiedzy

### 14a.1. Zasady transakcyjności

- **Izolacja**: zmiana jest widoczna tylko w obrębie swojej transakcji.
- **Atomowość**: commit stosuje wszystkie operacje albo żadną.
- **Weryfikowalność**: przechowywany jest snapshot stanu bazowego.
- **Odwracalność**: przed commitem rollback jest bezkosztowy.
- **Niemutowalność snapshotów**: zmiana tworzy nowy rekord.
- **Optymistyczna kontrola konkurencji**: commit sprawdza `base_registry_version` oraz `occ_version` każdego modyfikowanego rekordu przez zbiór `OccGuard` w jednej transakcji bazodanowej; niezgodność którejkolwiek wersji odrzuca cały commit.
- **Fencing**: operacje z efektami zewnętrznymi (push do Git, publikacja outbox) niosą fencing token wyprowadzony z wersji OCC; utracony lease nie może wykonać efektu zewnętrznego.
- **Krótka transakcja bazodanowa**: walidacje zewnętrzne odbywają się przed finalnym commitem.
- **Brak I/O sieciowego wewnątrz transakcji DB**: finalna transakcja nie czeka na Git, modele ani zewnętrzne API.
- **Audytowalność commitu**: wynik commitu (sukces lub odrzucenie OCC) jest dopisywany do łańcucha hashy.

### 14a.2. Modele Staging Area

```python
from uuid import uuid4


def _new_txn_id() -> StagingTransactionId:
    return StagingTransactionId(uuid4())


class StagingOperationKind(StrEnum):
    ADD = "add"
    REPLACE = "replace"
    DEPRECATE = "deprecate"
    SUPERSEDE = "supersede"
    REMOVE = "remove"


class StagingStatus(StrEnum):
    OPEN = "open"
    PREFLIGHT_OK = "preflight_ok"
    PREFLIGHT_FAILED = "preflight_failed"
    COMMITTED = "committed"
    ABORTED = "aborted"
    OCC_REJECTED = "occ_rejected"


class StagedOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: StagingOperationKind
    target_ref: SourceRef
    target_knowledge_id: KnowledgeId | None = None
    staged_record: KnowledgeRecord | None = None
    staged_payload: BinaryPayload | None = None
    expected_occ_version: OccVersion | None = None
    rationale: str = Field(min_length=1)


class PreflightIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: ConflictSeverity
    message: str = Field(min_length=1)
    related_conflict: ConflictId | None = None
    blocks_commit: bool = False


class StagingTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_id: StagingTransactionId = Field(default_factory=_new_txn_id)
    proposal_id: ProposalId
    base_registry_version: str = Field(min_length=1)

    operations: tuple[StagedOperation, ...] = Field(default_factory=tuple)
    occ_guards: tuple[OccGuard, ...] = Field(default_factory=tuple)
    detected_conflicts: tuple[KnowledgeConflict, ...] = Field(
        default_factory=tuple
    )
    preflight_issues: tuple[PreflightIssue, ...] = Field(default_factory=tuple)

    status: StagingStatus = StagingStatus.OPEN
    opened_by: AgentId
    opened_at: datetime
    updated_at: datetime
    committed_commit_sha: str | None = None
    committed_registry_version: str | None = None
    fencing_token: FencingToken | None = None

    def stage(self, operation: StagedOperation) -> StagingTransaction:
        return self.model_copy(
            update={
                "operations": (*self.operations, operation),
                "status": StagingStatus.OPEN,
            }
        )

    def with_preflight(
        self,
        conflicts: tuple[KnowledgeConflict, ...],
        issues: tuple[PreflightIssue, ...],
    ) -> StagingTransaction:
        blocking = any(issue.blocks_commit for issue in issues) or any(
            conflict.severity is ConflictSeverity.CRITICAL
            for conflict in conflicts
        )
        return self.model_copy(
            update={
                "detected_conflicts": conflicts,
                "preflight_issues": issues,
                "status": (
                    StagingStatus.PREFLIGHT_FAILED
                    if blocking
                    else StagingStatus.PREFLIGHT_OK
                ),
            }
        )

    def can_commit(self) -> bool:
        return self.status is StagingStatus.PREFLIGHT_OK


class StagingCommitResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_id: StagingTransactionId
    committed: bool
    new_registry_version: str | None = None
    commit_sha: str | None = None
    applied_operations: tuple[StagingOperationKind, ...] = Field(
        default_factory=tuple
    )
    occ_conflicts: tuple[OccConflict, ...] = Field(default_factory=tuple)
    rejection_reason: str | None = None
    committed_at: datetime | None = None
    audit_entry_id: AuditEntryId | None = None
```

### 14a.3. Protokół Staging Area

```python
from typing import Protocol


class StagingArea(Protocol):
    async def open(
        self,
        proposal: KnowledgeChangeProposal,
        *,
        opened_by: AgentId,
    ) -> StagingTransaction: ...

    async def stage(
        self,
        txn: StagingTransaction,
        operation: StagedOperation,
    ) -> StagingTransaction: ...

    async def preflight(
        self,
        txn: StagingTransaction,
    ) -> StagingTransaction: ...

    async def commit(
        self,
        txn: StagingTransaction,
    ) -> StagingCommitResult: ...

    async def abort(
        self,
        txn: StagingTransaction,
        *,
        reason: str,
    ) -> StagingTransaction: ...
```

### 14a.4. Integracja z Write Path

1. `open` tworzy transakcję powiązaną z propozycją i zamraża `base_registry_version` oraz wersje OCC wszystkich rekordów wejściowych.
2. `stage` odkłada operacje wraz z `expected_occ_version`.
3. `preflight` uruchamia detekcję konfliktów i walidację oraz buduje kompletny zbiór `occ_guards`.
4. Quality i Auditor oceniają transakcję.
5. `commit` jest możliwy wyłącznie, gdy `can_commit()` jest prawdą; commit weryfikuje wszystkie `occ_guards` atomowo w jednej transakcji bazodanowej.
6. Niezgodność wersji zwraca `StagingCommitResult` z `occ_conflicts` i statusem `OCC_REJECTED`; nic nie zostaje zastosowane.
7. commit zapisuje outbox oraz dopisuje wpis do łańcucha hashy (Audit Chain Writer) w tej samej ścieżce trwałości.
8. workery asynchronicznie wykonują reindeksację i invalidację.
9. `abort` przed commitem jest bezkosztowy i również pozostawia ślad audytowy.

---

## 15. Proces awansu wiedzy

```text
obserwacja
   │
   ▼
episodic memory
   │
   ▼
powtarzalny wzorzec
   │
   ▼
FailurePatternPack / InsightPack
   │
   ▼
eksperyment RAE-Lab
   │
   ▼
potwierdzony wynik
   │
   ▼
propozycja zmiany
   │
   ▼
Staging Area
   │
   ▼
Quality validation
   │
   ▼
Auditor / owner review
   │
   ▼
commit (OCC guards) + outbox + audit chain append
   │
   ├──────────────► re-index
   ├──────────────► cache invalidation
   └──────────────► drift re-evaluation
   │
   ▼
canonical knowledge
```

### 15.1. Przykład awansu wiedzy

1. Agent zauważa, że model X źle wykonuje migracje SQL.
2. Zapisuje epizod.
3. Kolejne błędy tworzą wzorzec.
4. Powstaje `FailurePatternPack`.
5. RAE-Lab porównuje modele X, Y i Z.
6. Quality potwierdza wyniki.
7. Powstaje `ProviderRoutingProposal`.
8. Propozycja przechodzi Staging Area.
9. Właściciel domeny zatwierdza zmianę.
10. Commit przenosi regułę do polityki z weryfikacją OCC.
11. Outbox inicjuje reindeksację.
12. Cache zależny od polityki zostaje unieważniony.
13. Kolejne decyzje wskazują Evidence Bundle i commit, a łańcuch hashy wiąże decyzję z konkretną wersją polityki.

### 15.2. Warunki awansu do `canonical`

- znane źródło pochodzenia,
- integralność treści,
- określony właściciel,
- zdefiniowany zakres,
- określony okres obowiązywania,
- jawny Evidence Bundle,
- walidacja Quality,
- review właściciela,
- plan rollbacku,
- wersjonowanie,
- brak nierozwiązanych konfliktów krytycznych,
- pomyślny preflight,
- atomowy commit z OCC guards,
- wpis w łańcuchu hashy,
- zdarzenie invalidacyjne,
- potwierdzenie reindeksacji.

---

## 16. Integracja z istniejącą pamięcią RAE

Nie należy zmieniać istniejącego API pamięci w pierwszej fazie.

```text
Knowledge Resolution Engine
├── CanonicalSourceAdapter
├── RAEAgenticMemoryAdapter
├── GitRuntimeAdapter
├── SonarAdapter
├── PlaywrightAdapter
├── TelemetryAdapter
└── ExternalKnowledgeAdapter
```

| Istniejący artefakt RAE | Klasa wiedzy | Domyślny autorytet |
|---|---|---|
| ActionTrace | episodic | observed |
| DecisionEvidence | empirical lub episodic | observed |
| Outcome | empirical | observed |
| Failure | episodic | observed |
| FailurePatternPack | episodic | approved po walidacji |
| Experiment | empirical | observed lub approved |
| InsightPack | empirical/episodic | inferred lub approved |
| LearnedStrategy | episodic | inferred |
| Policy | normative | canonical |
| FactorySpec | normative/architectural | canonical |

Mapowanie może zostać nadpisane przez rejestr, ale nie przez pojedynczy wynik retrieval.

Cache adaptera pamięci powinien preferować identyfikatory i skrócone reprezentacje. Pełne trajektorie i trace’y powinny być ładowane leniwie.

---

## 17. Tryby kompatybilności

Kolejność trybów migracyjnych:

```text
legacy → observe → dual_write → enforce
```

### 17.1. `legacy`

- istniejący retrieval pozostaje źródłem wyniku,
- resolver nie wpływa na decyzję,
- błędy resolvera nie blokują agenta,
- można rejestrować minimalne metryki.

### 17.2. `observe`

```text
stary wynik → używany
nowy wynik → porównywany i logowany
konflikty → rejestrowane
różnice → przekazywane asynchronicznie do RAE-Lab
```

Należy mierzyć:

- różnicę źródeł,
- różnicę twierdzeń,
- koszt,
- opóźnienie,
- konflikty,
- potencjalne blokady,
- błędny wybór autorytetu,
- cache hit ratio,
- koszt odczytów PostgreSQL,
- rozmiar payloadów,
- opóźnienie kolejki.

### 17.2a. `dual_write` — okres migracji

W okresie migracji magazynów i kontraktów (legacy retrieval store → Knowledge Governance Layer, stary format Evidence → Evidence Bundle, inline payload → externalized payload) obowiązuje tryb Dual-Write.

Zasady Dual-Write:

1. **Primary-first**: zapis do magazynu prymarnego (legacy w fazie wczesnej, nowego po cutover) jest warunkiem powodzenia operacji; zapis wtórny jest wykonywany po nim.
2. **Zapis wtórny przez outbox**: zapis do magazynu wtórnego przechodzi przez transactional outbox, aby awaria wtórnego zapisu nie mogła cicho zgubić danych — wpis outbox powstaje w transakcji primary.
3. **Idempotentność**: oba zapisy używają wspólnego `idempotency_key` wyprowadzonego z identyfikatora artefaktu; retry nie tworzy duplikatu logicznego.
4. **Brak podwójnej prawdy**: przez cały okres dual-write dokładnie jeden magazyn jest źródłem odczytu (read path nie miesza wyników); przełączenie odczytu jest oddzielną, jawną decyzją cutover.
5. **Reconciliation**: cykliczny worker porównuje checksumy artefaktów w obu magazynach i raportuje `dual_write_divergence_rate`; każda rozbieżność jest zdarzeniem audytowalnym z klasyfikacją przyczyny.
6. **Naprawa deterministyczna**: rozbieżność naprawiana jest zawsze z magazynu prymarnego do wtórnego, nigdy odwrotnie i nigdy automatycznie w kierunku primary.
7. **Cutover gate**: przełączenie primary jest dozwolone dopiero, gdy divergence utrzymuje się poniżej progu (domyślnie 0.1%) przez zdefiniowane okno (domyślnie 7 dni), a wszystkie rozbieżności mają wyjaśnioną przyczynę.
8. **Rollback**: procedura rollback przywraca poprzedni primary bez utraty danych — zapisy z okresu po cutover są odtwarzane z outbox i reconciliacji.
9. **Audyt**: włączenie, cutover i wyłączenie dual-write są wpisami w łańcuchu hashy.

```python
class DualWriteRole(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class DualWriteDivergence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: ObjectRef
    idempotency_key: str = Field(min_length=1)
    primary_checksum: str | None = None
    secondary_checksum: str | None = None
    detected_at: datetime
    tenant_id: TenantId | None = None
    classified_cause: str | None = None
    repaired_at: datetime | None = None
```

### 17.3. `enforce`

Resolver odpowiada za:

- dobór dowodów,
- rozstrzyganie autorytetu,
- wykrywanie konfliktów,
- wymaganie review,
- blokowanie wykonania.

```yaml
knowledge_resolution:
  mode: observe
  fallback_to_legacy: true
  block_on_critical_conflict: false
  record_comparison_metrics: true
  require_evidence_for_high_risk: true
  require_reproducible_evidence: false
  max_evidence_age_seconds: 86400

  synchronous_budget_ms: 1200
  async_fallback_enabled: true

  dual_write:
    enabled: false
    primary: legacy
    secondary: governance
    reconciliation_interval_seconds: 300
    divergence_alert_threshold: 0.001
    cutover_window_days: 7
    repair_direction: primary_to_secondary

  cache:
    l1_enabled: true
    l1_max_entries: 10000
    l1_default_ttl_seconds: 15
    redis_enabled: true
    redis_codec: msgpack
    redis_compression_threshold_bytes: 65536
    redis_max_item_bytes: 1048576
    default_ttl_seconds: 120
    stale_while_revalidate_seconds: 30
    negative_ttl_seconds: 10

  profiles:
    normative_compliance:
      min_authority: approved
      allow_untrusted: false
      block_on_critical_conflict: true

    contract_conformance:
      min_authority: observed
      allow_untrusted: false
      block_on_critical_conflict: true

    current_runtime_state:
      max_evidence_age_seconds: 300
      prefer_observed: true
      block_on_stale_runtime: false
```

---

## 18. Metryki wdrożenia

Podstawowe metryki funkcjonalne:

- `canonical_hit_rate`,
- `conflict_detection_rate`,
- `stale_knowledge_rate`,
- `unsupported_decision_rate`,
- `evidence_coverage`,
- `source_diversity`,
- `resolution_latency`,
- `fallback_rate`,
- `wrong_authority_selection_rate`,
- `knowledge_drift_count`,
- `proposal_acceptance_rate`,
- `critical_conflict_block_rate`,
- `false_conflict_rate`,
- `evidence_reproducibility_rate`,
- `resolver_error_rate`,
- `legacy_new_resolution_disagreement_rate`,
- `staging_preflight_failure_rate`,
- `staging_commit_success_rate`.

Metryki bezpieczeństwa i zgodności:

- `audit_chain_verification_failure_count`,
- `audit_chain_append_latency_p95`,
- `audit_chain_anchor_lag_seconds`,
- `occ_conflict_rate`,
- `occ_rejected_commit_count`,
- `dual_write_divergence_rate`,
- `dual_write_reconciliation_lag_seconds`,
- `dual_write_repair_count`,
- `cold_storage_archival_success_rate`,
- `cold_storage_restore_latency_p95`,
- `cold_storage_integrity_check_failure_count`,
- `legal_hold_violation_count`,
- `retention_policy_exception_count`.

Metryki wydajnościowe:

- `resolution_latency_p50`,
- `resolution_latency_p95`,
- `resolution_latency_p99`,
- `adapter_latency_p95`,
- `l1_cache_hit_ratio`,
- `redis_cache_hit_ratio`,
- `cache_stale_served_rate`,
- `cache_stampede_prevented_total`,
- `redis_payload_bytes`,
- `redis_decode_latency`,
- `postgres_query_latency_p95`,
- `postgres_rows_scanned`,
- `postgres_connections_active`,
- `pgbouncer_client_wait_seconds`,
- `pgbouncer_pool_saturation`,
- `pgbouncer_server_connections`,
- `toast_fetch_bytes`,
- `large_payload_externalization_rate`,
- `queue_depth`,
- `queue_oldest_message_age`,
- `queue_processing_latency`,
- `queue_retry_rate`,
- `queue_dead_letter_rate`,
- `outbox_delivery_lag`,
- `worker_saturation`,
- `async_completion_latency`.

### 18.1. Evidence coverage

```text
evidence_coverage =
decyzje z kompletnym Evidence Bundle /
wszystkie decyzje wymagające dowodu
```

### 18.2. Unsupported decision rate

Decyzja jest unsupported, jeżeli:

- nie posiada Evidence Bundle,
- Bundle nie ma źródeł pierwotnych,
- dowody są poza zakresem,
- wszystkie źródła są `untrusted`,
- istnieje nierozwiązany konflikt krytyczny,
- poziom pewności jest niższy od wymaganego,
- Bundle wysokiego ryzyka nie posiada wpisu w łańcuchu hashy.

### 18.3. Wrong authority selection rate

Metryka uwzględnia:

- profil rozstrzygania,
- zakres,
- świeżość,
- status źródła,
- poprawność reguły.

### 18.4. Drift count

Dryf zawiera:

- źródło oczekiwanego stanu,
- źródło stanu rzeczywistego,
- zakres,
- czas wykrycia,
- severity,
- status,
- właściciela obsługi.

### 18.5. SLO wydajnościowe

Proponowane cele początkowe:

| Operacja | SLO |
|---|---|
| cache hit L1 | p95 poniżej 5 ms |
| cache hit Redis | p95 poniżej 25 ms |
| synchroniczne resolution bez źródeł zewnętrznych | p95 poniżej 800 ms |
| synchroniczne resolution ze źródłami runtime | p95 poniżej 1500 ms |
| zapis nagłówka Evidence Bundle | p95 poniżej 100 ms |
| dopisanie wpisu do łańcucha hashy | p95 poniżej 50 ms |
| anchoring łańcucha hashy | lag poniżej 1 h |
| opóźnienie outbox | p95 poniżej 5 s |
| invalidacja cache | p95 poniżej 10 s |
| reindeksacja małego dokumentu | p95 poniżej 30 s |
| kolejka krytyczna | najstarsza wiadomość poniżej 30 s |
| kolejka standardowa | najstarsza wiadomość poniżej 5 min |
| odtworzenie artefaktu z Cold Storage (warm restore) | p95 poniżej 15 min |

SLO muszą być kalibrowane na podstawie benchmarków i nie mogą zastępować wymagań poprawności.

---

## 19. Wdrożenie iteracyjne

### Faza 0 — Inwentaryzacja bez zmian runtime

Zidentyfikować:

- aktualne typy pamięci,
- API pamięci,
- magazyny,
- modele danych,
- miejsca wywołań retrieval,
- polityki,
- źródła runtime,
- dane eksperymentalne,
- modele dowodów,
- źródła aktualizacji wiedzy,
- uprawnienia do zapisu,
- rozmiary payloadów,
- częstotliwość odczytów,
- obecne połączenia do PostgreSQL,
- potencjalne źródła cache,
- zadania nadające się do kolejki,
- istniejące artefakty audytowe podlegające łańcuchowaniu,
- wymagania retencji i legal hold per klasa danych.

Rezultat:

```text
knowledge-source-inventory.yaml
```

### Faza 1 — Canonical Registry

Dodać rejestr wiedzy bez zmiany sposobu działania agentów.

### Faza 2 — Adaptery

Dodać adaptery i testy kontraktowe.

### Faza 3 — Evidence Bundle

Planner otrzymuje dodatkowo:

- `EvidenceBundle`,
- `ResolutionDecision`,
- konflikty,
- nierozstrzygnięte pytania,
- confidence,
- flagę blokady.

### Faza 3a — Audit Chain

Wdrożyć Audit Chain Writer i Verifier (sekcja 23a):

- łańcuchowanie nowych Evidence Bundle i wyników commitów,
- backfill hashy dla artefaktów historycznych (osobny łańcuch `historical`),
- cykliczna weryfikacja ciągłości,
- anchoring zewnętrzny.

### Faza 4 — Shadow resolution

RAE-Lab porównuje:

- trafność,
- koszt,
- opóźnienie,
- liczbę błędów,
- liczbę konfliktów,
- niewspierane decyzje,
- błędne wybory autorytetu,
- fałszywe konflikty.

### Faza 4a — Obserwowalność storage i połączeń

Przed wdrożeniem cache należy zebrać baseline:

- p50, p95 i p99 zapytań,
- liczbę połączeń,
- cache hit ratio PostgreSQL,
- rozmiary tabel i indeksów,
- udział TOAST,
- rozmiary najczęściej pobieranych rekordów,
- średni i maksymalny rozmiar Evidence Bundle,
- koszt serializacji JSON,
- kolejki oczekiwania na połączenie.

### Faza 4b — L1 i Redis L2

Wdrożyć:

- lokalny cache metadanych,
- Redis jako cache rozproszony,
- MessagePack,
- versioned cache envelope,
- TTL z jitterem,
- single-flight,
- stale-while-revalidate,
- invalidację po outbox.

Najpierw cache’ować dane o wysokim odczycie i niskiej zmienności:

- rejestr źródeł,
- reguły profili,
- znormalizowane metadane,
- gotowe rozstrzygnięcia o krótkim TTL.

### Faza 4c — PgBouncer

Wdrożyć PgBouncer w trybie transaction pooling dla usług stateless. Zweryfikować kompatybilność ORM i sterowników.

### Faza 4d — Externalizacja dużych payloadów

Dodać:

- osobną tabelę payloadów,
- storage obiektowy,
- content-addressed keys,
- leniwe pobieranie,
- migrację dużych rekordów,
- politykę retencji.

### Faza 4e — Kolejki asynchroniczne

Przenieść do kolejek:

- reindeksację,
- embeddingi,
- drift scans,
- eksporty,
- RAE-Lab comparison,
- invalidację wtórnych cache,
- archiwizację,
- weryfikację łańcucha hashy,
- dual-write reconciliation.

### Faza 4f — Dual-Write i migracja magazynów

Dla każdej migracji magazynu (legacy → governance, inline → externalized payload, hot → cold):

1. włączyć dual-write z legacy jako primary,
2. uruchomić reconciliation i mierzyć divergence,
3. sklasyfikować i wyeliminować przyczyny rozbieżności,
4. po spełnieniu cutover gate przełączyć odczyt na nowy magazyn,
5. przełączyć primary,
6. utrzymać dual-write w odwróconej roli przez okres bezpieczeństwa,
7. wyłączyć dual-write i zarchiwizować legacy zgodnie z retencją,
8. każdy krok wpisać do łańcucha hashy.

### Faza 4g — Cold Storage

Wdrożyć Archival Orchestrator (sekcja 26.8):

- klasy retencji,
- manifesty archiwalne,
- WORM i object lock,
- legal hold,
- testowane procedury restore,
- cykliczne testy integralności archiwów.

### Faza 5 — Authority enforcement

Najpierw:

- OpenAPI,
- JSON Schema,
- FactorySpec,
- polityki bezpieczeństwa,
- budżety,
- kontrakty agentów,
- uprawnienia,
- kontrakty zdarzeń.

### Faza 6 — Knowledge promotion pipeline

```text
memory → insight → experiment → proposal → staging → review → commit → canonical
```

### Faza 7 — Runtime drift detection

Porównywać:

```text
stan deklarowany ↔ stan rzeczywisty
```

### Faza 8 — Autonomiczne naprawy dokumentacji

Agent może tworzyć PR-y wyłącznie przez Staging Area, z dowodami, testami, review, rollbackiem i preflightem.

---

## 20. Przykład działania w RAE

### Zadanie

> Zmień autoryzację RAE na Keycloak.

### Knowledge Resolution Engine pobiera

#### Canonical

- kontrakt tokenu,
- ADR dotyczący Keycloak,
- politykę bezpieczeństwa,
- OpenAPI,
- schemat ról,
- kontrakt klienta OIDC,
- FactorySpec środowiska.

#### Runtime

- aktualny `docker-compose`,
- działającą wersję Keycloak,
- konfigurację klienta OIDC,
- aktywne referencje do sekretów,
- status kontenerów,
- konfigurację ingress,
- telemetrykę błędów logowania.

#### Agentic memory

- wcześniejsze błędy z refresh tokenami,
- wcześniejsze decyzje dotyczące `sub`,
- wyniki testów Socket.IO,
- epizody rollbacku,
- problemy z wygasaniem sesji.

#### Empirical

- testy integracyjne,
- wyniki Playwright,
- security scans,
- testy odświeżania tokenów,
- testy multi-tenant,
- wyniki canary.

### Wykryty konflikt

```text
ADR:
refresh token wyłącznie w BFF.

Kod klienta:
refresh token zapisywany w localStorage.

Polityka bezpieczeństwa:
refresh token nie może być dostępny dla JavaScriptu aplikacji.
```

### Rezultat

```text
conflict_type: policy_violation
severity: critical
status: blocked
blocks_execution: true
requires_quality_review: true
requires_auditor_review: true
```

Wykonanie zostaje zablokowane. Decyzja blokująca zostaje trwale zapisana i dopisana do łańcucha hashy. Cache dla powiązanej polityki i wcześniejszych rozstrzygnięć zostaje unieważniony. Asynchronicznie tworzone są:

- zadanie Quality,
- zadanie Auditor,
- wpis drift detection,
- zdarzenie do RAE-Lab,
- re-evaluation wcześniejszych aktywnych decyzji zależnych od tej polityki.

---

## 21. Przykład rozstrzygania kontraktu

### Pytanie

> Czy endpoint `/companies` może zwrócić pole `companyID` jako `null`?

System znajduje:

1. aktualne OpenAPI,
2. JSON Schema odpowiedzi,
3. starą dokumentację Markdown,
4. pamięć agenta,
5. wynik testu integracyjnego.

OpenAPI:

```yaml
companyID:
  type: string
  nullable: false
  required: true
```

Test integracyjny:

```text
actual response: companyID = null
```

Resolver tworzy:

```text
resolution_profile: contract_conformance
decision: kontrakt nie dopuszcza null
runtime_status: wykryto naruszenie kontraktu
conflict_type: runtime_drift
severity: high
blocks_execution: zależnie od operacji
```

Wynik:

- kontrakt nie dopuszcza `null`,
- runtime zwrócił `null`,
- system jest niezgodny z kontraktem.

Cache key obejmuje commit OpenAPI, wersję schematu i środowisko testu. Zmiana któregokolwiek z tych elementów unieważnia wynik.

---

## 22. Integracja z jakością, audytem i RAE-Lab

### 22.1. Quality

Quality odpowiada za:

- kompletność dowodów,
- walidację wyników testów,
- ocenę ryzyka,
- klasyfikację konfliktów,
- weryfikację planów walidacyjnych,
- ocenę propozycji zmian,
- ocenę preflight.

### 22.2. Auditor

Auditor odpowiada za:

- formalne naruszenia,
- akceptację wyjątków,
- kontrolę ścieżki audytowej,
- ocenę naruszeń polityk,
- rozstrzyganie konfliktów wymagających uprawnień,
- weryfikację nadrzędnych źródeł,
- autoryzację commitów wysokiego ryzyka,
- okresową weryfikację ciągłości łańcucha hashy,
- nadzór nad legal hold i wyjątkami retencji,
- utrzymanie mapowania kontroli ISO 27001/42001 (sekcja 34).

### 22.3. RAE-Lab

RAE-Lab odpowiada za:

- porównywanie legacy i resolvera,
- eksperymenty z regułami autorytetu,
- analizę false positives,
- analizę false negatives,
- badanie wpływu nowych dowodów,
- walidację promocji wiedzy,
- pomiar kosztu i opóźnienia,
- porównywanie retrievalu.

Porównania RAE-Lab powinny być wykonywane asynchronicznie i nie blokować odpowiedzi użytkownika.

---

## 23. Wymagania dotyczące audytowalności

Minimalny ślad audytowy zawiera:

- `request_id`,
- `bundle_id`,
- `decision_id`,
- zadanie,
- agenta,
- profil,
- wersję resolvera,
- wersję polityki,
- źródła zapytane,
- źródła wybrane,
- źródła odrzucone,
- checksumy,
- commit SHA,
- timestamp,
- konflikty,
- regułę autorytetu,
- uzasadnienie,
- wynik decyzji,
- fallback,
- blokadę,
- referencje do dowodów,
- identyfikator Staging Area,
- wynik preflight,
- wynik commitu,
- konflikty OCC,
- wersję formatu serializacji,
- checksum trwałego payloadu,
- identyfikator i sekwencję wpisu w łańcuchu hashy.

Nie wolno modyfikować historycznego Evidence Bundle. Korekta tworzy nowy bundle.

Cache nie jest częścią trwałego śladu audytowego. Cache może przyspieszać odczyt, ale trwały artefakt musi znajdować się w storage audytowym.

---

## 23a. Hash Chaining dowodów decyzji

### 23a.1. Cel

Łańcuch hashy zapewnia, że:

- artefakty audytowe nie mogą zostać niepostrzeżenie zmodyfikowane, usunięte ani dopisane wstecznie,
- kolejność decyzji jest kryptograficznie utrwalona,
- audytor zewnętrzny może zweryfikować kompletność śladu bez zaufania do operatora bazy danych,
- spełnione są wymagania dowodowe ISO/IEC 27001 (integralność zapisów) i ISO/IEC 42001 (rozliczalność decyzji systemu AI).

### 23a.2. Model łańcucha

Łańcuch jest prowadzony per tenant (oraz osobny łańcuch systemowy dla artefaktów globalnych). Każdy trwały artefakt audytowy — Evidence Bundle, Resolution Decision wysokiego ryzyka, wynik commitu Staging Area, formalne naruszenie, zdarzenie dual-write cutover, manifest archiwalny — generuje wpis.

```python
def _new_audit_entry_id() -> AuditEntryId:
    return AuditEntryId(uuid4())


class AuditArtifactType(StrEnum):
    EVIDENCE_BUNDLE = "evidence_bundle"
    RESOLUTION_DECISION = "resolution_decision"
    STAGING_COMMIT = "staging_commit"
    STAGING_ABORT = "staging_abort"
    FORMAL_VIOLATION = "formal_violation"
    DUAL_WRITE_TRANSITION = "dual_write_transition"
    ARCHIVAL_MANIFEST = "archival_manifest"
    RETENTION_EXCEPTION = "retention_exception"


class AuditChainEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entry_id: AuditEntryId = Field(default_factory=_new_audit_entry_id)
    chain_id: AuditChainId
    sequence: int = Field(ge=0)

    artifact_type: AuditArtifactType
    artifact_ref: ObjectRef
    artifact_checksum: str = Field(
        pattern=r"^(sha256|sha384|sha512):[A-Fa-f0-9]{16,}$"
    )

    prev_entry_hash: str | None = None
    entry_hash: str = Field(
        pattern=r"^(sha256|sha384|sha512):[A-Fa-f0-9]{16,}$"
    )

    tenant_id: TenantId | None = None
    actor: AgentId | None = None
    created_at: datetime

    signing_key_ref: KeyRef | None = None
    signature: BinaryPayload | None = None
```

### 23a.3. Reguły łańcucha

- `entry_hash = H(canonical_serialization(entry bez entry_hash i signature) || prev_entry_hash)`,
- pierwszy wpis łańcucha ma `prev_entry_hash = None` i jest genesis entry zapisanym przy tworzeniu tenanta,
- `sequence` jest ściśle monotoniczna bez luk; przydział sekwencji jest chroniony przez OCC (compare-and-set na głowie łańcucha),
- serializacja kanoniczna jest deterministyczna (posortowane klucze, UTC, stabilne kodowanie enumów) i wersjonowana,
- tabela wpisów jest append-only: brak `UPDATE` i `DELETE` na poziomie uprawnień bazodanowych, wymuszone triggerem i grantami,
- wpisy dla decyzji wysokiego ryzyka są dopisywane w tej samej ścieżce trwałości co artefakt, przed zwróceniem odpowiedzi,
- wpisy dla artefaktów niskiego ryzyka mogą być dopisywane przez kolejkę krytyczną z zachowaniem kolejności per chain,
- korekta artefaktu nigdy nie modyfikuje wpisu — powstaje nowy artefakt i nowy wpis z relacją `supersedes`.

### 23a.4. Podpisy i klucze

- wpisy mogą być dodatkowo podpisywane kluczem asymetrycznym zarządzanym w KMS/HSM,
- klucz podpisujący audyt jest odseparowany od kluczy operacyjnych (szyfrowanie danych, TLS),
- rotacja klucza tworzy wpis `chain key rotation`; stare podpisy pozostają weryfikowalne przez `signing_key_ref`,
- dostęp do klucza podpisującego ma wyłącznie Audit Chain Writer (zasada least privilege, ISO 27001 A.8.2/A.8.24).

### 23a.5. Anchoring

Okresowo (domyślnie co godzinę oraz przy każdym commicie wysokiego ryzyka) głowa łańcucha jest kotwiczona poza systemem:

- zapis digestu głowy do niezależnego magazynu WORM,
- opcjonalnie znacznik czasu RFC 3161 (TSA),
- opcjonalnie commit digestu do dedykowanego repozytorium Git z podpisem.

Anchoring uniemożliwia przepisanie całego łańcucha przez podmiot kontrolujący bazę.

### 23a.6. Weryfikacja

Audit Chain Verifier działa jako zadanie cykliczne (kolejka standardowa) i na żądanie audytora:

- weryfikuje ciągłość `sequence` i `prev_entry_hash`,
- porównuje `artifact_checksum` z faktycznym artefaktem (w tym artefaktami odtworzonymi z Cold Storage — próbkowanie),
- weryfikuje podpisy i kotwice,
- każde niepowodzenie podnosi `audit_chain_verification_failure_count`, tworzy konflikt `integrity` o severity `critical` i eskaluje do Auditora,
- wynik weryfikacji jest raportem zgodności przechowywanym jako artefakt audytowy.

---

## 24. Bezpieczeństwo i kontrola dostępu

Knowledge Resolution API sprawdza:

- tożsamość agenta,
- rolę agenta,
- projekt,
- tenant,
- środowisko,
- klasę danych,
- zakres zasobu,
- dopuszczalne klasy wiedzy,
- dopuszczalne poziomy autorytetu,
- możliwość odczytu źródła,
- możliwość tworzenia propozycji,
- możliwość commitu Staging Area,
- możliwość odczytu łańcucha audytowego i archiwów.

Wiedza zewnętrzna i nieufna jest izolowana od:

- sekretów,
- polityk wewnętrznych,
- danych tenantów,
- danych osobowych,
- danych uwierzytelniających,
- instrukcji wykonawczych.

### 24.1. Bezpieczeństwo cache

Klucz cache musi obejmować security context lub jego nieodwracalny hash:

- tenant,
- projekt,
- role lub policy decision version,
- klasyfikację danych,
- zakres.

Zabronione jest:

- współdzielenie wpisu między tenantami bez formalnego dowodu identycznych uprawnień,
- umieszczanie sekretów w kluczach Redis,
- przechowywanie danych osobowych bez szyfrowania i retencji,
- logowanie pełnego payloadu cache,
- używanie globalnego cache dla wyników zależnych od ACL.

### 24.2. Bezpieczeństwo kolejek

Wiadomości kolejkowe powinny zawierać głównie identyfikatory i referencje. Nie należy kopiować dużych lub wrażliwych payloadów do brokera.

Wymagane są:

- szyfrowanie transportu,
- ACL per queue,
- ograniczenie rozmiaru wiadomości,
- podpis lub checksum envelope,
- ochrona przed replay,
- kontrolowana retencja,
- redakcja telemetryki,
- deduplikacja.

### 24.3. Zarządzanie kluczami i separacja ról

- klucze szyfrujące dane (at rest), klucze TLS i klucze podpisujące łańcuch audytowy są odrębne i zarządzane w KMS z audytem użycia,
- rotacja kluczy jest zaplanowana i audytowalna; utrata klucza podpisującego nie unieważnia historycznych weryfikacji (klucze archiwalne pozostają dostępne do weryfikacji),
- role są rozdzielone: operator systemu nie może modyfikować łańcucha audytowego; Auditor nie posiada uprawnień zapisu wiedzy kanonicznej; Audit Chain Writer nie posiada uprawnień odczytu payloadów wykraczających poza wyliczenie checksumu,
- dostęp do Cold Storage jest ograniczony do Archival Orchestrator (zapis) i procedur restore z zatwierdzeniem (odczyt),
- wszystkie operacje uprzywilejowane (legal hold, wyjątek retencji, replay dead-letter, ręczna naprawa dual-write) wymagają podwójnej autoryzacji i tworzą wpis w łańcuchu hashy.

---

## 25. Warstwa wydajnościowa: cache, Redis i MessagePack

### 25.1. Wielopoziomowa architektura cache

```text
Request
  │
  ▼
L0: request-scoped memoization
  │
  ▼
L1: bounded in-process cache
  │
  ▼
L2: Redis distributed cache
  │
  ▼
PostgreSQL / source adapters / object storage
```

#### L0

Cache w obrębie pojedynczego requestu:

- eliminuje duplikaty wywołań adaptera,
- nie wymaga TTL,
- jest automatycznie usuwany po zakończeniu requestu,
- powinien wykorzystywać single-flight dla identycznych kluczy.

#### L1

Cache procesu:

- bardzo niski latency,
- ograniczony liczbą wpisów i pamięcią,
- krótkie TTL,
- polityka LRU lub TinyLFU,
- brak gwarancji spójności między instancjami,
- invalidacja przez zdarzenia best effort.

#### L2 Redis

Cache rozproszony:

- współdzielony między instancjami,
- przechowuje znormalizowane rekordy i wyniki resolution,
- używa MessagePack,
- posiada TTL z jitterem,
- stosuje limity rozmiaru wpisu,
- nie jest trwałym źródłem audytowym.

### 25.2. Klucz cache

Klucz powinien powstawać z kanonicznego, deterministycznego dokumentu:

```text
schema_version
resolver_version
policy_version
registry_version
resolution_profile
normalized_query_hash
tenant_id
project_id
environment
authorization_context_hash
required_knowledge_classes
required_source_types
allowed_scope_hash
include_external
include_untrusted
as_of_bucket
max_age_seconds
source_version_vector
```

Przykład:

```text
rae:kr:v3:resolution:
sha256(
  tenant |
  project |
  profile |
  normalized_query |
  policy_version |
  registry_version |
  auth_context_hash |
  scope_hash |
  source_version_vector
)
```

Nie należy wstawiać pełnego zapytania ani sekretów do nazwy klucza.

### 25.3. TTL i inwalidacja

Zalecana strategia hybrydowa:

- TTL ogranicza skutki zgubionej invalidacji,
- zdarzenia unieważniają cache po zmianach,
- wersje źródeł powodują naturalny cache miss,
- jitter zmniejsza równoczesne wygasanie,
- stale-while-revalidate jest dozwolone tylko dla profili, które akceptują stale data.

Przykładowe TTL:

| Dane | TTL |
|---|---|
| registry metadata | 5 min |
| canonical document metadata | 1–5 min |
| canonical content | 30–120 s |
| runtime state | 5–30 s |
| telemetry aggregate | 10–60 s |
| negative result | 5–15 s |
| gotowe resolution normatywne | 30–120 s |
| gotowe resolution runtime | 5–20 s |
| policy parser output | do zmiany wersji, z TTL bezpieczeństwa |

### 25.4. Ochrona przed cache stampede

Wymagane mechanizmy:

- request coalescing,
- single-flight per key,
- distributed lease o krótkim TTL,
- TTL jitter,
- stale-while-revalidate,
- probabilistic early refresh,
- limit równoległych refreshy,
- fallback do stale wyłącznie zgodnie z profilem.

Blokada odświeżenia nie może być długim lockiem globalnym. Jej utrata nie może naruszać poprawności.

### 25.5. MessagePack w Redis

MessagePack jest preferowany względem JSON dla złożonych cache entries, ponieważ:

- redukuje rozmiar danych,
- zachowuje typy liczbowe i binarne,
- zmniejsza narzut parsowania tekstu,
- ogranicza transfer sieciowy,
- dobrze współpracuje z immutable DTO.

Każdy wpis powinien mieć versioned envelope:

```python
from typing import Any


class CacheEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(ge=1)
    codec: str
    compression: str | None = None
    created_at: datetime
    expires_at: datetime
    stale_until: datetime | None = None
    payload_checksum: str
    payload: bytes
    metadata: dict[str, Any] = Field(default_factory=dict)
```

W praktycznej implementacji envelope może być strukturą MessagePack, a nie modelem Pydantic zapisywanym jako JSON.

### 25.6. Reguły serializacji MessagePack

- jawna `schema_version`,
- daty kodowane jako epoch microseconds UTC albo standardowy extension type,
- UUID kodowany jako 16 bajtów,
- enumy kodowane jako stabilne string values,
- branded strings kodowane jako string,
- brak dowolnej serializacji obiektów wykonawczych,
- brak `pickle`,
- limit głębokości i liczby elementów,
- walidacja po dekodowaniu,
- checksum payloadu,
- nieznana wersja powoduje cache miss, nie błąd requestu.

### 25.7. Kompresja

Nie należy kompresować każdego wpisu. Kompresję włączać powyżej progu, np. 64 KiB.

Preferencje:

- małe wpisy: MessagePack bez kompresji,
- średnie tekstowe wpisy: MessagePack + Zstandard,
- już skompresowane dane binarne: bez dodatkowej kompresji,
- wpisy powyżej maksymalnego rozmiaru: nie trafiają do Redis, tylko do storage obiektowego.

Przykładowe limity:

```yaml
redis_cache:
  codec: msgpack
  compression:
    algorithm: zstd
    threshold_bytes: 65536
    level: 3
  limits:
    max_uncompressed_item_bytes: 4194304
    max_stored_item_bytes: 1048576
    max_collection_items: 5000
```

### 25.8. Polityka pamięci Redis

Redis powinien być oddzielony logicznie lub fizycznie od mechanizmów wymagających innej retencji.

Zalecenia:

- osobny cluster lub co najmniej osobny deployment dla cache,
- `maxmemory` ustawione jawnie,
- polityka `allkeys-lfu` albo `volatile-lfu` zależnie od przeznaczenia,
- wszystkie wpisy cache mają TTL,
- unikać `KEYS`; używać `SCAN` wyłącznie operacyjnie,
- nie wykonywać masowej invalidacji przez skanowanie namespace,
- invalidować przez wersję namespace lub indeks zależności,
- monitorować fragmentation ratio i evictions,
- korzystać z pipeline dla niezależnych operacji,
- Lua stosować wyłącznie dla małych, ograniczonych atomowych operacji.

### 25.9. Cache dużych bundle

Redis nie powinien być magazynem pełnych, wielomegabajtowych Evidence Bundle.

Do Redis trafia:

- nagłówek,
- status,
- wybrane źródła,
- skrócone konflikty,
- `payload_ref`,
- checksum,
- wersja.

Pełny bundle pozostaje w trwałym storage.

---

## 26. PostgreSQL, TOAST i model przechowywania dużych payloadów

### 26.1. Rozdzielenie hot i cold data

Zalecany model:

```text
knowledge_record
├── identyfikatory
├── authority
├── class
├── scope selectors
├── lifecycle
├── occ_version
├── checksum
├── content_summary
├── payload_ref
├── payload_size
└── timestamps

knowledge_payload
├── knowledge_id
├── payload_version
├── content_type
├── compression
├── payload
├── checksum
└── created_at

evidence_bundle_header
├── bundle_id
├── request_id
├── status
├── confidence
├── flags
├── versions
├── bundle_hash
├── audit_chain_id
├── chain_sequence
└── generated_at

evidence_bundle_payload
├── bundle_id
├── payload
├── checksum
├── compression
└── created_at

audit_chain_entry (append-only)
├── entry_id
├── chain_id
├── sequence
├── artifact_type
├── artifact_ref
├── artifact_checksum
├── prev_entry_hash
├── entry_hash
├── signing_key_ref
├── signature
└── created_at
```

Zapytania listujące i filtrujące powinny dotykać wyłącznie tabel nagłówkowych.

### 26.2. TOAST

TOAST pomaga przechowywać duże wartości, ale nie jest darmowym storage obiektowym.

Ryzyka:

- detoasting przy odczycie pełnej kolumny,
- większy WAL,
- koszt aktualizacji dużych wierszy,
- bloat,
- autovacuum obciążone dużymi wersjami rekordów,
- nieprzewidywalne latency,
- przypadkowe pobieranie payloadów przez ORM,
- koszt replikacji.

Reguły:

1. nie używać `SELECT *` dla tabel z dużymi kolumnami,
2. oddzielić payload od metadanych,
3. nie aktualizować dużego payloadu przy każdej zmianie statusu,
4. stosować append-only wersje payloadu,
5. pobierać payload tylko przez dedykowane repozytorium,
6. mierzyć `pg_column_size`, rozmiar TOAST i WAL,
7. nie tworzyć indeksów na pełnych dużych dokumentach,
8. unikać duplikowania payloadu w JSONB metadata,
9. rozważyć `STORAGE EXTERNAL` dla danych, których nie warto kompresować,
10. potwierdzić ustawienia benchmarkiem.

### 26.3. JSONB

JSONB jest właściwe dla ograniczonych, elastycznych metadanych, ale nie powinno zastępować wszystkich kolumn.

Pola używane do:

- filtrowania,
- joinów,
- sortowania,
- polityk retencji,
- zakresów tenantów,
- statusów,
- wersji

powinny być jawnie typowanymi kolumnami.

Indeksy GIN należy dodawać selektywnie. Szeroki GIN na stale zmienianym, dużym JSONB może znacząco zwiększyć koszt zapisu.

### 26.4. Indeksy

Przykładowe indeksy:

```sql
CREATE INDEX CONCURRENTLY idx_knowledge_active_scope
ON knowledge_record (
    tenant_id,
    project_id,
    knowledge_class,
    authority_level,
    updated_at DESC
)
WHERE lifecycle_status = 'active';

CREATE INDEX CONCURRENTLY idx_bundle_request
ON evidence_bundle_header (request_id);

CREATE INDEX CONCURRENTLY idx_bundle_generated
ON evidence_bundle_header (tenant_id, generated_at DESC);

CREATE INDEX CONCURRENTLY idx_outbox_pending
ON outbox_event (available_at, id)
WHERE delivered_at IS NULL;

CREATE UNIQUE INDEX CONCURRENTLY idx_audit_chain_sequence
ON audit_chain_entry (chain_id, sequence);
```

Wymagania:

- kolejność kolumn wynika z rzeczywistych predykatów,
- indeksy częściowe dla aktywnych danych,
- keyset pagination zamiast wysokiego `OFFSET`,
- analiza `EXPLAIN (ANALYZE, BUFFERS, WAL)`,
- usuwanie indeksów nieużywanych,
- brak indeksowania dużych payloadów,
- unikalny indeks `(chain_id, sequence)` wymusza brak luk i duplikatów w łańcuchu wraz z OCC na głowie łańcucha.

### 26.5. Partycjonowanie i retencja

Partycjonowanie rozważyć dla:

- Evidence Bundle o dużej skali,
- eventów audytowych,
- outbox history,
- checkpointów,
- telemetryki,
- wyników eksperymentów.

Najczęściej partycjonować po czasie i ewentualnie tenantach wysokiego wolumenu. Nie należy partycjonować tabel bez potwierdzonej potrzeby.

Retencja:

- aktywne nagłówki pozostają dostępne,
- payloady historyczne mogą przechodzić do storage archiwalnego,
- partycje wygaszane są przez detach/drop zamiast masowego `DELETE`,
- wygaszenie partycji zawierającej artefakty audytowe wymaga wcześniejszej archiwizacji do Cold Storage z manifestem i wpisem w łańcuchu hashy,
- artefakty objęte legal hold są wyłączone z wygaszania niezależnie od polityki retencji,
- wymagania compliance mają pierwszeństwo przed optymalizacją.

### 26.6. Autovacuum i bloat

Dla tabel o dużej częstotliwości zmian należy indywidualnie ustawić:

- `autovacuum_vacuum_scale_factor`,
- `autovacuum_analyze_scale_factor`,
- `autovacuum_vacuum_threshold`,
- `fillfactor`,
- limity kosztu autovacuum.

Duże payloady powinny być append-only, aby ograniczyć powstawanie kolejnych wersji TOAST.

### 26.7. Wzorzec dostępu do dużego payloadu

```text
GET /evidence-bundles/{id}
        │
        ▼
odczyt nagłówka
        │
        ├── brak uprawnień → 403
        ├── klient nie żąda payloadu → nagłówek
        ▼
odczyt payload_ref
        │
        ├── object storage → streaming
        ├── cold storage → restore workflow (async, 202)
        └── PostgreSQL payload table → chunked response
```

Payload powinien być streamowany. Nie należy buforować całego wielomegabajtowego dokumentu jednocześnie w kilku warstwach.

### 26.8. Cold Storage i archiwizacja

#### 26.8.1. Warstwy przechowywania

```text
Hot   → PostgreSQL / object storage standard  → dane aktywne i świeże
Warm  → object storage infrequent access      → dane poza aktywnym oknem, dostęp sporadyczny
Cold  → cold storage WORM (object lock)       → artefakty audytowe i historyczne, dostęp wyjątkowy
```

Domyślne okna (konfigurowalne per klasa danych i wymagania compliance):

| Klasa danych | Hot | Warm | Cold | Minimalna retencja |
|---|---|---|---|---|
| Evidence Bundle nagłówki | 12 mies. | do 36 mies. | dalej | zgodnie z compliance, min. 7 lat dla decyzji normatywnych |
| Evidence Bundle payloady | 3 mies. | do 12 mies. | dalej | jak wyżej |
| Audit chain entries | zawsze hot (małe wiersze) | — | kopie i kotwice w cold | pełny okres życia systemu |
| Payloady wiedzy historycznej | 6 mies. | do 24 mies. | dalej | wg właściciela domeny |
| Telemetria i checkpointy | 30 dni | 90 dni | opcjonalnie | operacyjna |

#### 26.8.2. Manifest archiwalny

Każda operacja archiwizacji tworzy niemutowalny manifest:

```python
class ArchivalTier(StrEnum):
    WARM = "warm"
    COLD = "cold"


class ArchivalManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    archive_ref: ArchiveRef
    tier: ArchivalTier
    tenant_id: TenantId | None = None

    artifact_refs: tuple[ObjectRef, ...] = Field(min_length=1)
    artifact_checksums: tuple[str, ...] = Field(min_length=1)
    manifest_checksum: str = Field(
        pattern=r"^(sha256|sha384|sha512):[A-Fa-f0-9]{16,}$"
    )

    encryption_key_ref: KeyRef
    compression: str | None = None
    total_size_bytes: int = Field(ge=0)

    retention_class: str = Field(min_length=1)
    retain_until: datetime | None = None
    legal_hold: bool = False

    created_at: datetime
    created_by: str = Field(min_length=1)
    audit_entry_id: AuditEntryId | None = None
```

#### 26.8.3. Reguły Cold Storage

- Cold Storage jest WORM: object lock w trybie compliance uniemożliwia nadpisanie i usunięcie przed `retain_until`,
- dane są szyfrowane at rest kluczem z KMS z osobnym `encryption_key_ref` per manifest; rotacja klucza nie wymaga przepisywania archiwów (envelope encryption),
- manifest jest dopisywany do łańcucha hashy — archiwum bez wpisu w łańcuchu nie jest ważnym archiwum,
- archiwizacja jest zadaniem klasy batch: idempotentna, wznawialna, z checksumem po stronie zapisu i weryfikacją po stronie odczytu,
- usunięcie danych z warstwy hot następuje wyłącznie po potwierdzonej weryfikacji integralności archiwum,
- legal hold blokuje wygaszanie manifestu i wszystkich wskazywanych artefaktów; nałożenie i zdjęcie legal hold wymaga podwójnej autoryzacji i wpisu w łańcuchu,
- geograficzna lokalizacja archiwów respektuje wymagania rezydencji danych tenantów.

#### 26.8.4. Restore

- restore jest operacją asynchroniczną (`202 Accepted` + receipt), autoryzowaną per artefakt,
- odtworzony artefakt jest weryfikowany względem checksumu z manifestu i hasha z łańcucha przed udostępnieniem,
- procedura restore jest testowana cyklicznie (co najmniej kwartalnie) na próbie losowej archiwów; wynik testu jest artefaktem audytowym,
- SLO restore: p95 poniżej 15 minut dla warstwy warm, zdefiniowany i zakomunikowany czas dla cold zgodnie z klasą storage,
- rekord `KnowledgeRecord` w statusie `archived` wskazuje `archive_ref`; resolver traktuje takie rekordy jako `historical_context`, nigdy jako rozstrzygające dla stanu bieżącego.

---

## 27. PgBouncer i zarządzanie połączeniami PostgreSQL

### 27.1. Cel

PgBouncer chroni PostgreSQL przed:

- nadmierną liczbą połączeń,
- skokami liczby instancji,
- połączeniem per async task,
- długim oczekiwaniem na handshake,
- wyczerpaniem `max_connections`.

### 27.2. Tryb poolingu

Dla stateless API i workerów preferowany jest:

```ini
pool_mode = transaction
```

Tryb session pooling pozostaje tylko dla komponentów, które rzeczywiście wymagają stanu sesji.

W transaction pooling należy unikać zależności od:

- trwałych tabel tymczasowych między transakcjami,
- session-level advisory locks,
- zmiennych sesyjnych utrzymywanych między transakcjami,
- `LISTEN/NOTIFY` przez zwykłe połączenie transakcyjne,
- założeń o przypięciu klienta do jednego backendu.

### 27.3. Prepared statements

Należy zweryfikować kompatybilność sterownika i PgBouncera. Dopuszczalne opcje:

- wyłączenie server-side prepared statements,
- użycie wsparcia PgBouncer dla prepared statements w kompatybilnej wersji,
- jawne skonfigurowanie driver statement cache,
- testy pod rolling deploymentem i reconnectami.

Nie wolno wdrożyć transaction pooling bez testów integracyjnych ORM.

### 27.4. Budżet połączeń

Całkowity budżet:

```text
max_connections PostgreSQL
- rezerwa administracyjna
- replikacja
- maintenance
- migracje
- monitoring
= budżet dla PgBouncer
```

Każda usługa otrzymuje limit:

```yaml
database:
  api:
    client_pool_size_per_instance: 10
    max_overflow: 0
    acquire_timeout_seconds: 2
  workers:
    client_pool_size_per_instance: 5
    max_overflow: 0
    acquire_timeout_seconds: 5
  pgbouncer:
    pool_mode: transaction
    default_pool_size: 30
    min_pool_size: 5
    reserve_pool_size: 5
    reserve_pool_timeout_seconds: 2
    max_client_conn: 1000
```

Pool aplikacyjny nie może tworzyć nadmiernego wielowarstwowego poolingu. Przy PgBouncerze pool klienta powinien być mały i ograniczony.

### 27.5. Timeouty

Zalecane mechanizmy:

- `connect_timeout`,
- krótki `pool_timeout`,
- `statement_timeout`,
- `lock_timeout`,
- `idle_in_transaction_session_timeout`,
- deadline propagowany z requestu.

Przykład:

```sql
SET LOCAL statement_timeout = '1500ms';
SET LOCAL lock_timeout = '250ms';
```

`SET LOCAL` musi działać wewnątrz transakcji i nie może być traktowane jako trwały stan sesji.

### 27.6. Długie transakcje

Zabronione jest:

- wywoływanie modeli wewnątrz transakcji,
- pobieranie zewnętrznego API wewnątrz transakcji,
- oczekiwanie na kolejkę wewnątrz transakcji,
- streamowanie odpowiedzi przy otwartej transakcji,
- wykonywanie pełnego preflight wewnątrz finalnego commitu.

### 27.7. Monitoring PgBouncer

Monitorować:

- `cl_active`,
- `cl_waiting`,
- `sv_active`,
- `sv_idle`,
- `maxwait`,
- `avg_wait_time`,
- `xact_count`,
- `query_count`,
- `avg_xact_time`,
- `avg_query_time`,
- wykorzystanie reserve pool,
- liczbę reconnectów,
- błędy uwierzytelnienia.

Alarmy:

- oczekujący klienci przez więcej niż 30 s,
- p95 acquire time powyżej budżetu,
- permanentna saturacja server pool,
- wzrost średniego czasu transakcji,
- przekroczenie budżetu połączeń.

---

## 28. Asynchroniczne kolejkowanie i backpressure

### 28.1. Klasy zadań

#### Krytyczne

- finalizacja trwałego Evidence Bundle,
- dopisanie wpisu do łańcucha hashy (poza ścieżką synchroniczną wysokiego ryzyka),
- formalna invalidacja po krytycznej zmianie,
- obsługa outbox,
- bezpieczeństwo i audyt.

#### Standardowe

- reindeksacja,
- embeddingi,
- drift detection,
- porównania RAE-Lab,
- odświeżanie cache,
- weryfikacja łańcucha hashy,
- dual-write reconciliation.

#### Batch

- archiwizacja do Cold Storage,
- kompakcja,
- pełne skany,
- eksporty,
- rekalkulacja historyczna,
- testy restore.

Klasy powinny używać oddzielnych kolejek lub priorytetów, aby batch nie blokował zadań krytycznych.

### 28.2. Envelope wiadomości

```python
def _new_message_id() -> QueueMessageId:
    return QueueMessageId(uuid4())


class QueuePriority(StrEnum):
    CRITICAL = "critical"
    STANDARD = "standard"
    BATCH = "batch"


class QueueMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message_id: QueueMessageId = Field(default_factory=_new_message_id)
    queue_name: QueueName
    message_type: str = Field(min_length=1)
    schema_version: int = Field(ge=1)

    tenant_id: TenantId | None = None
    request_id: RequestId | None = None

    idempotency_key: str = Field(min_length=1)
    priority: QueuePriority

    payload_ref: ObjectRef | None = None
    payload_checksum: str | None = None
    inline_payload: bytes | None = None

    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=5, ge=1)
    created_at: datetime
    available_at: datetime
    expires_at: datetime | None = None

    traceparent: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### 28.3. Rozmiar wiadomości

Domyślny limit inline:

```text
64 KiB
```

Większy payload trafia do trwałego storage, a wiadomość zawiera wyłącznie:

- referencję,
- checksum,
- content type,
- rozmiar,
- informacje autoryzacyjne niezbędne do ponownego sprawdzenia dostępu.

### 28.4. Idempotentność

Konsument musi być bezpieczny przy co najmniej jednokrotnym dostarczeniu.

Wzorce:

- unikalny `idempotency_key`,
- tabela processed messages,
- upsert,
- compare-and-set po wersji (OCC),
- content-addressed object keys,
- deterministyczny wynik,
- transactional inbox/outbox.

Nie należy zakładać exactly-once delivery oferowanego wyłącznie deklaratywnie przez brokera.

### 28.5. Retry

Retry wyłącznie dla błędów przejściowych:

- timeout,
- chwilowa niedostępność,
- rate limit,
- deadlock,
- serialization failure,
- przejściowy błąd sieci.

Nie retry’ować automatycznie:

- błędu walidacji,
- braku uprawnień,
- nieobsługiwanej wersji schematu,
- konfliktu domenowego,
- konfliktu OCC bez ponownego preflightu,
- uszkodzonego checksumu.

Strategia:

```text
delay = min(base * 2^attempt, max_delay) + jitter
```

Każda kolejka ma:

- maksymalną liczbę prób,
- maksymalny wiek wiadomości,
- dead-letter queue,
- procedurę replay,
- alert dla poison messages.

### 28.6. Backpressure

System musi ograniczać pobieranie pracy, gdy:

- PgBouncer jest nasycony,
- Redis ma wysokie latency,
- adapter zewnętrzny otworzył circuit breaker,
- pamięć workera przekracza limit,
- kolejka downstream rośnie,
- object storage zwalnia.

Mechanizmy:

- prefetch limit,
- bounded concurrency,
- dynamiczne zmniejszanie liczby workerów aktywnych,
- rate limit per tenant i source,
- priorytety,
- shedding zadań batch,
- `Retry-After`,
- status `partial` albo `accepted`.

### 28.7. Kolejka a stan domenowy

Broker nie jest źródłem prawdy. Stan zadania powinien znajdować się w trwałym magazynie:

- accepted,
- running,
- completed,
- failed,
- dead-lettered.

Usunięcie wiadomości nie może usuwać śladu audytowego operacji.

---

## 29. Concurrency, Resilience and Safety Guards

Mechanizmy tej sekcji należą do infrastruktury i adapterów.

### 29.1. Concurrency Model for Parallel Queries

```python
import asyncio
from collections.abc import Mapping


async def gather_sources(
    ctx: ResolutionContext[Any],
    adapters: Mapping[SourceRef, KnowledgeAdapter],
    query: str,
    *,
    per_source_timeout: float,
    max_results: int,
    global_limit: int,
) -> dict[
    SourceRef,
    tuple[RetrievedKnowledge, ...] | BaseException,
]:
    semaphore = asyncio.Semaphore(global_limit)

    async def run(
        adapter: KnowledgeAdapter,
    ) -> tuple[RetrievedKnowledge, ...]:
        async with semaphore:
            async with asyncio.timeout(per_source_timeout):
                return await adapter.retrieve(
                    ctx,
                    query,
                    max_results=max_results,
                )

    async with asyncio.TaskGroup() as task_group:
        tasks = {
            source: task_group.create_task(run(adapter))
            for source, adapter in adapters.items()
        }

    return {
        source: task.result()
        for source, task in tasks.items()
    }
```

Produkcja powinna dodatkowo:

- obsłużyć częściowe błędy,
- zachować deadline całego requestu,
- przerwać zbędne zadania po wystarczającym rozstrzygnięciu,
- stosować limit per source,
- oddzielić timeout kolejki od timeoutu wykonania.

Przykład:

```yaml
concurrency:
  max_parallel_queries: 20
  per_source_limit: 3
  queue_capacity: 100
  total_resolution_timeout_ms: 1500
  per_source_timeout_ms: 500
```

### 29.2. Advisory Locking System i OCC

```python
class LockType(StrEnum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


class KnowledgeLock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lock_id: LockId
    resource: str = Field(min_length=1)
    lock_type: LockType
    holder: AgentId
    expires_at: datetime
    fencing_token: FencingToken | None = None
```

Zasady:

- uporządkowane blokowanie zasobów,
- automatyczne wygaśnięcie lease,
- fencing token dla operacji zewnętrznych; token jest monotoniczny i weryfikowany przez odbiorcę efektu,
- brak session advisory locks przy PgBouncer transaction pooling,
- optymistyczna kontrola wersji (OCC guards, sekcja 1a.6) jako mechanizm podstawowy poprawności; lock jedynie redukuje częstotliwość konfliktów,
- utrata locka nie może naruszać poprawności — poprawność gwarantuje OCC przy commicie,
- blokady rozproszone nie zastępują constraints w bazie.

### 29.3. Crash Resilience

```python
class ResolutionStage(StrEnum):
    RETRIEVAL = "retrieval"
    NORMALIZATION = "normalization"
    CONFLICT_DETECTION = "conflict_detection"
    EVIDENCE_PERSISTENCE = "evidence_persistence"


class ResolutionCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: RequestId
    stage: ResolutionStage
    partial_results: tuple[RetrievedKnowledge, ...] = Field(
        default_factory=tuple
    )
    created_at: datetime
    ttl_seconds: int = Field(default=300, ge=1)
```

Wymagania:

- idempotentne requesty,
- durable Evidence Bundle przed odpowiedzią,
- atomiczny zapis z checksum,
- wpis w łańcuchu hashy w tej samej ścieżce trwałości dla decyzji wysokiego ryzyka,
- watchdog,
- requeue z fencingiem,
- deduplikacja,
- checkpoint zawierający referencje zamiast bardzo dużych wyników.

### 29.4. Memory Management for Async Operations

Nie należy polegać na `WeakValueDictionary` jako podstawowym cache, ponieważ modele Pydantic mogą nie wspierać weak references, a zachowanie takiego cache jest niedeterministyczne.

Preferowane są:

- bounded LRU lub TinyLFU,
- limit liczby wpisów,
- limit szacowanego rozmiaru,
- streaming,
- projekcja wyłącznie potrzebnych pól,
- jawne usunięcie dużych buforów,
- brak kopiowania payloadu przy każdym przejściu fazy,
- `memoryview` na granicach infrastruktury,
- okresowe recycle workerów tylko jako guard, nie jako substytut usunięcia wycieku.

### 29.5. Safety Guards

```python
class ResolutionResourceCaps(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_resolution_memory_mb: int = Field(default=512, ge=1)
    max_evidence_items: int = Field(default=500, ge=1)
    max_claims_per_bundle: int = Field(default=2000, ge=1)
    max_parallel_queries: int = Field(default=20, ge=1)
    per_source_limit: int = Field(default=3, ge=1)
    max_inline_payload_bytes: int = Field(default=65536, ge=1)
    max_redis_item_bytes: int = Field(default=1048576, ge=1)
    max_database_payload_bytes: int = Field(default=2097152, ge=1)
```

Mechanizmy:

- circuit breakers,
- timeouts,
- limity zasobów,
- bounded queues,
- commit guards (OCC + fencing),
- payload size guards,
- query row limits,
- statement timeout,
- rate limit per tenant,
- cancellation propagation.

### 29.6. Degradacja kontrolowana

Kolejność degradacji:

1. pominąć źródła opcjonalne,
2. zwrócić krótsze excerpt,
3. użyć dozwolonego stale cache,
4. przenieść post-processing do kolejki,
5. zwrócić `partial`,
6. zwrócić `accepted`,
7. zablokować, jeśli brak dowodów wymaganych bezpieczeństwem.

System nie może zamieniać awarii źródła na fałszywy status `resolved`.

Degradacja nigdy nie obejmuje pominięcia zapisu artefaktu audytowego ani wpisu w łańcuchu hashy dla decyzji wysokiego ryzyka — jeżeli zapis audytowy jest niemożliwy, decyzja wysokiego ryzyka jest blokowana.

---

## 30. Testy wydajnościowe i capacity planning

### 30.1. Profile obciążenia

Należy przygotować co najmniej:

- cache-heavy read,
- cold-cache read,
- runtime-heavy resolution,
- duży Evidence Bundle,
- równoczesną invalidację,
- burst po wdrożeniu polityki,
- reindeksację masową,
- awarię Redis,
- awarię adaptera,
- saturację PgBouncer,
- lag kolejki,
- poison message,
- retry storm,
- wysoki współczynnik konfliktów OCC przy równoległych commitach,
- masową archiwizację do Cold Storage,
- równoległy dual-write pod pełnym obciążeniem.

### 30.2. Benchmark serializacji

Porównać:

- JSON,
- MessagePack,
- MessagePack + Zstandard.

Mierzyć:

- rozmiar,
- czas encode,
- czas decode,
- alokacje pamięci,
- CPU,
- latency sieci,
- zachowanie dla małych i dużych obiektów.

MessagePack należy wdrożyć po potwierdzeniu korzyści na rzeczywistych DTO.

### 30.3. Benchmark PostgreSQL

Mierzyć:

- odczyt nagłówka bez payloadu,
- odczyt payloadu TOAST,
- odczyt payloadu z osobnej tabeli,
- odczyt ze storage obiektowego,
- zapis append-only,
- aktualizację dużego wiersza,
- wpływ na WAL,
- wpływ na autovacuum,
- PgBouncer acquire time,
- narzut append łańcucha hashy pod obciążeniem (contention na głowie łańcucha per tenant).

### 30.4. Testy chaosowe

Scenariusze:

- Redis niedostępny,
- utrata połowy workerów,
- restart PgBouncer,
- failover PostgreSQL,
- opóźniony object storage,
- zgubiona invalidacja,
- duplikat wiadomości,
- out-of-order event,
- wygaśnięcie lease,
- schema mismatch MessagePack,
- uszkodzony checksum,
- symulowana manipulacja wpisem łańcucha hashy (weryfikator musi wykryć),
- przerwanie archiwizacji w połowie manifestu (wznowienie idempotentne),
- rozbieżność dual-write wymuszona awarią zapisu wtórnego,
- niedostępny Cold Storage podczas restore,
- utrata dostępu do klucza podpisującego (procedura awaryjna, decyzje wysokiego ryzyka blokowane).

### 30.5. Capacity model

Minimalny model powinien uwzględniać:

```text
QPS resolution
× średnia liczba adapterów
× cache miss ratio
× średnia liczba zapytań DB
= bazowy query rate PostgreSQL
```

oraz:

```text
liczba zmian źródeł
× liczba zależnych indeksów
× średni koszt reindeksacji
= wymagany throughput workerów
```

Dla Redis:

```text
aktywny working set
× średni rozmiar wpisu
× narzut struktur Redis
× współczynnik headroom
= wymagane maxmemory
```

Dla łańcucha hashy:

```text
liczba decyzji audytowanych na sekundę per tenant
= górna granica throughput append per chain
(sekwencyjność per chain; skalowanie przez podział na tenantów)
```

Headroom nie powinien być mniejszy niż 30% bez potwierdzonego modelu operacyjnego.

---

## 31. Operacyjny plan konfiguracji

```yaml
knowledge_resolution:
  synchronous_budget_ms: 1200
  total_timeout_ms: 1800
  max_results_per_source: 20

  concurrency:
    max_parallel_queries: 20
    per_source_limit: 3
    queue_capacity: 100

  cache:
    l1:
      enabled: true
      max_entries: 10000
      max_memory_mb: 256
      default_ttl_seconds: 15

    redis:
      enabled: true
      codec: msgpack
      namespace_version: 3
      default_ttl_seconds: 120
      negative_ttl_seconds: 10
      stale_while_revalidate_seconds: 30
      compression:
        algorithm: zstd
        threshold_bytes: 65536
        level: 3
      limits:
        max_uncompressed_item_bytes: 4194304
        max_stored_item_bytes: 1048576

  payloads:
    inline_threshold_bytes: 16384
    database_external_threshold_bytes: 262144
    object_storage_threshold_bytes: 2097152
    stream_chunk_bytes: 262144

  database:
    statement_timeout_ms: 1500
    lock_timeout_ms: 250
    idle_in_transaction_timeout_ms: 5000
    application_pool_size: 10
    application_pool_overflow: 0
    acquire_timeout_ms: 2000

  pgbouncer:
    pool_mode: transaction
    default_pool_size: 30
    min_pool_size: 5
    reserve_pool_size: 5
    reserve_pool_timeout_seconds: 2
    max_client_conn: 1000

  queues:
    max_inline_payload_bytes: 65536
    critical:
      concurrency: 16
      max_attempts: 10
      oldest_message_slo_seconds: 30
    standard:
      concurrency: 32
      max_attempts: 5
      oldest_message_slo_seconds: 300
    batch:
      concurrency: 4
      max_attempts: 3
      oldest_message_slo_seconds: 3600

  circuit_breakers:
    failure_threshold: 5
    recovery_timeout_seconds: 30
    half_open_max_calls: 2

  audit_chain:
    enabled: true
    hash_algorithm: sha256
    sign_entries: true
    signing_key_ref: kms://rae/audit-chain-signer
    anchor_interval_seconds: 3600
    anchor_targets:
      - worm_object_storage
      - git_anchor_repo
    verify_interval_seconds: 21600
    verify_sample_cold_storage: true
    high_risk_synchronous_append: true

  occ:
    enabled: true
    max_commit_retries: 2
    retry_requires_preflight_on_input_change: true
    conflict_audit_enabled: true

  dual_write:
    enabled: false
    primary: legacy
    secondary: governance
    reconciliation_interval_seconds: 300
    divergence_alert_threshold: 0.001
    cutover_window_days: 7
    repair_direction: primary_to_secondary

  archival:
    enabled: true
    tiers:
      warm_after_days: 90
      cold_after_days: 365
    worm_mode: compliance
    encryption_key_ref: kms://rae/archival
    restore_requires_approval: true
    restore_test_interval_days: 90
    legal_hold_dual_authorization: true
```

Wartości są punktem startowym. Muszą zostać dostrojone na podstawie pomiarów.

---

## 32. Kryteria akceptacji produkcyjnej

Warstwa może przejść do `enforce`, jeżeli:

1. wszystkie źródła krytyczne mają właściciela i zakres,
2. cache key przeszedł testy izolacji tenantów,
3. cache nie zmienia wyników semantycznych,
4. invalidacja po zmianie polityki spełnia SLO,
5. Redis może zostać wyłączony bez utraty poprawności,
6. MessagePack ma wersjonowany envelope,
7. nieznany format cache powoduje bezpieczny miss,
8. duże payloady nie są pobierane przy listowaniu,
9. zmierzono wpływ TOAST,
10. PgBouncer przeszedł testy ORM i failover,
11. budżet połączeń jest egzekwowany,
12. żadna transakcja nie obejmuje zewnętrznego I/O,
13. kolejki są idempotentne,
14. istnieje dead-letter queue i procedura replay,
15. transactional outbox zapobiega utracie invalidacji,
16. system obsługuje duplikaty i out-of-order events,
17. metryki p95 i p99 spełniają SLO,
18. istnieją alarmy dla cache, PostgreSQL, PgBouncer i kolejek,
19. Evidence Bundle jest zapisany trwale przed zwróceniem wyniku wysokiego ryzyka,
20. degradacja nie może zamienić braku dowodu na fałszywe rozstrzygnięcie,
21. łańcuch hashy jest weryfikowalny end-to-end, a symulowana manipulacja jest wykrywana przez weryfikator w testach,
22. każda decyzja wysokiego ryzyka posiada wpis w łańcuchu hashy przed zwróceniem odpowiedzi,
23. OCC guards są egzekwowane na wszystkich commitach; konflikt wersji nigdy nie kończy się cichym nadpisaniem i jest audytowany,
24. dual-write przeszedł pełny cykl: włączenie, reconciliation z divergence poniżej progu przez wymagane okno, cutover i przetestowany rollback,
25. Cold Storage działa w trybie WORM, legal hold jest egzekwowany, a procedura restore została przetestowana na produkcyjnych archiwach z weryfikacją checksumów,
26. mapowanie kontroli ISO/IEC 27001 i ISO/IEC 42001 (sekcja 34) jest kompletne, a każdy wymagany dowód kontrolny jest generowany automatycznie,
27. klucze podpisujące audyt są odseparowane od kluczy operacyjnych, a rotacja kluczy została przetestowana bez utraty weryfikowalności historii.

---

## 33. Podsumowanie zgodności architektonicznej

- identyfikatory używają typów nominalnych,
- domena jest agnostyczna technologicznie,
- konteksty rozstrzygania są generyczne i niemutowalne,
- zmiany wiedzy przechodzą przez Staging Area,
- każdy commit jest chroniony przez OCC guards i fencing tokeny,
- artefakty audytowe są niemutowalne i łańcuchowane kryptograficznie (Hash Chaining) z zewnętrznym anchoringiem,
- migracje magazynów przebiegają w trybie Dual-Write z mierzoną rekonsyliacją, jawnym cutover i rollbackiem,
- cache jest wielopoziomowy i nie stanowi źródła prawdy,
- Redis używa wersjonowanego MessagePack,
- duże wpisy nie są bezwarunkowo przechowywane w Redisie,
- duże payloady są oddzielone od gorących rekordów PostgreSQL,
- TOAST jest monitorowany i nie zastępuje storage obiektowego,
- dane historyczne i audytowe przechodzą do Cold Storage (WORM) z manifestami, legal hold i testowanym restore,
- PgBouncer ogranicza liczbę połączeń,
- transakcje bazodanowe są krótkie,
- reindeksacja, invalidacja i analiza wtórna są asynchroniczne,
- kolejki zapewniają idempotentność, retry z jitterem i dead-letter handling,
- transactional outbox spina commit z publikacją zdarzeń,
- backpressure chroni PostgreSQL, Redis, adaptery i workery,
- audytowalność spełnia wymagania ISO/IEC 27001 i ISO/IEC 42001 z jawnym mapowaniem kontroli,
- poprawność, autorytet, audytowalność i integralność dowodów mają pierwszeństwo przed cache hit ratio i latency.

---

## 34. Mapowanie kontroli ISO/IEC 27001 i ISO/IEC 42001

Poniższe mapowanie wiąże mechanizmy tego dokumentu z kontrolami norm. Jest utrzymywane przez Auditora i aktualizowane przy każdej zmianie architektury. Każdy wiersz musi posiadać automatycznie generowany dowód kontrolny (raport, metrykę lub artefakt audytowy).

### 34.1. ISO/IEC 27001 (Annex A)

| Kontrola | Mechanizm w OKF-RAE | Dowód kontrolny |
|---|---|---|
| A.5.9 Inwentaryzacja informacji | Canonical Registry, knowledge-source-inventory | wersjonowany `registry.yaml`, raport inwentaryzacji |
| A.5.15 / A.5.18 Kontrola dostępu | Sekcja 24: ACL per tenant, scope, klasa danych | logi decyzji autoryzacyjnych, testy izolacji cache |
| A.5.28 Zbieranie dowodów | Evidence Bundle, Hash Chaining (23a) | wpisy `AuditChainEntry`, raporty weryfikatora |
| A.5.33 Ochrona zapisów | Append-only audit chain, WORM Cold Storage | konfiguracja object lock, testy manipulacji |
| A.8.2 Uprzywilejowane prawa dostępu | Separacja ról (24.3), podwójna autoryzacja | logi operacji uprzywilejowanych w łańcuchu |
| A.8.9 Zarządzanie konfiguracją | Rejestr wersjonowany, Staging Area, OCC | historia commitów, wyniki preflight |
| A.8.10 Usuwanie informacji | Polityki retencji (26.5, 26.8), legal hold | manifesty archiwalne, raporty retencji |
| A.8.12 Zapobieganie wyciekom danych | Izolacja untrusted, redakcja telemetryki, limity cache | testy izolacji, audyt kluczy Redis |
| A.8.13 Kopie zapasowe | Cold Storage, testy restore (26.8.4) | kwartalne raporty testów restore |
| A.8.16 Monitorowanie | Metryki sekcji 18, alarmy 27.7 | dashboardy, historia alertów |
| A.8.24 Kryptografia | KMS/HSM, podpisy łańcucha, envelope encryption | rejestr kluczy, wpisy rotacji w łańcuchu |
| A.8.32 Zarządzanie zmianą | Staging Area, Quality, Auditor review | `StagingCommitResult`, wpisy commitów |

### 34.2. ISO/IEC 42001 (system zarządzania AI)

| Wymaganie | Mechanizm w OKF-RAE | Dowód kontrolny |
|---|---|---|
| Rozliczalność decyzji AI | Resolution Decision + Evidence Bundle + Hash Chaining | pełny ślad decyzji z regułą autorytetu i uzasadnieniem |
| Zarządzanie danymi i pochodzeniem | Provenance, checksumy, integrity status | rekordy `Provenance`, metryki integralności |
| Nadzór człowieka | Quality i Auditor review, blokady konfliktów krytycznych | zadania review, wpisy formalnych naruszeń |
| Zarządzanie ryzykiem AI | RiskClass propozycji, profile rozstrzygania, blokady polityk | raporty ryzyka propozycji, `critical_conflict_block_rate` |
| Monitorowanie działania systemu AI | drift detection, RAE-Lab, metryki disagreement | raporty driftu, porównania legacy/resolver |
| Zarządzanie cyklem życia wiedzy modelowej | Knowledge promotion pipeline, lifecycle status | historia awansów, wpisy commitów w łańcuchu |
| Odwracalność i korekta | rollback plan, supersedes, nowe bundle zamiast edycji | relacje `supersedes`, plany rollbacku |
| Przejrzystość wobec audytora | eksport audytowy, weryfikowalny łańcuch, anchoring | raporty weryfikacji, kotwice zewnętrzne |

### 34.3. Utrzymanie mapowania

- mapowanie jest wiedzą kanoniczną klasy `normative` z właścicielem (Auditor) i podlega Staging Area,
- brak dowodu kontrolnego dla wymaganej kontroli jest konfliktem `policy_violation` o severity `high`,
- przegląd mapowania odbywa się co najmniej raz na kwartał oraz po każdej zmianie architektury warstwy,
- wynik przeglądu jest artefaktem audytowym dopisywanym do łańcucha hashy.