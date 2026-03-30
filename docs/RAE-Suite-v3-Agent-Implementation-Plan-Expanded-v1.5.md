# RAE-Suite v3 — Agent Implementation Plan (Expanded)
**Wersja:** 1.5 Expanded  
**Data:** 2026-03-28  
**Bazuje na:** oryginalnym pliku `RAE-Suite-v3-Agent-Implementation-Plan.md` + rozszerzenia wykonawcze  
**Tryb planu:** Zachowuje pełny oryginał i rozwija go zamiast upraszczać

> Ta wersja zachowuje cały oryginalny plan implementacji i rozszerza go o strategię migracji,
> behavioral contracts, kanoniczny model kosztu, politykę kompatybilności i doprecyzowania wykonawcze po review. Nic z oryginalnego
> planu nie zostało skrócone ani usunięte.

---

# RAE-Suite v3 — Agent Implementation Plan
**Wersja:** 1.0  
**Data:** 2026-03-28  
**Bazuje na:** RFC `RAE-Suite-v3-Architecture-Plan.md` (Draft v1, 2026-03-27)  
**Tryb planu:** Gotowy do wykonania przez agenty RAE-Hive / RAE-Phoenix  

---

## Zasady dla agentów

1. **Nie refaktoruj tego, co działa** — ewolucja, nie rewolucja.
2. **Każda zmiana jest committem z opisem w formacie `feat(scope): opis`.**
3. **Każda faza kończy się przejściem przez quality gate** (testy + lint + coverage).
4. **Fazy są sekwencyjne** — Faza N nie startuje, dopóki Faza N-1 nie ma zielonych testów.
5. **Jeśli trafiasz na niejasność** — zapisz pytanie jako `OPEN_QUESTION.md` w katalogu fazy i kontynuuj to co możesz.

---

## Rozstrzygnięcia po review v1.4

Ta wersja planu rozstrzyga krytyczne niejednoznaczności z review wykonawczego oraz dopina brakujące elementy implementacyjne:

1. **BehaviorSignal vs BehaviorViolation**
   - działy emitują `BehaviorSignal`,
   - tylko Auditor emituje `BehaviorViolation`,
   - reguła jest zakodowana także w modelach danych, a nie tylko opisana narracyjnie.

2. **Behavior models**
   - dodane są pełne modele `BehaviorGuarantee`, `BehaviorSignal`, `BehaviorViolation`, `DepartmentBehaviorContract`,
   - `collect_behavior_signals()` ma deterministyczne reguły mapowania oraz passthrough dla już ustrukturyzowanych sygnałów.

3. **Behavioral verification**
   - `evaluate_behavioral_contract()` ma referencyjną implementację,
   - weryfikacja jest deterministyczna: filtracja po `department`, `guarantee_id` i `severity`, a następnie budowa `BehaviorViolation` bez zgadywania.

4. **Cost model**
   - `CostVector` przechowuje wyłącznie koszty surowe,
   - `CostPolicy` i `BudgetEnvelope` są zdefiniowane jawnie,
   - `NCU` jest liczone funkcją `compute_ncu()` na podstawie `CostPolicy`.

5. **Budget enforcement**
   - `BudgetChecker` ma wspólny `Protocol`,
   - ten sam kontrakt obowiązuje w fazach Control Plane, Improvement Plane i Safe Rollout.

6. **Router kosztowy v1**
   - ranking jest deterministyczny i leksykograficzny,
   - bez niekalibrowanych wag i bez ukrytego `reliability_score`,
   - jawnie zdefiniowane są fallbacki dla pustej telemetry historycznej.

7. **Kompatybilność wersji**
   - używamy `packaging.version`,
   - zabronione są heurystyki `startswith()` / wildcard-matching dla semver.

8. **FactorySpec schema sync**
   - `factory_spec_v1.yaml` musi być zsynchronizowany z polami `costModel` i `behaviorContractRef`,
   - acceptance criteria zabraniają `additionalProperties: true` dla tych sekcji.

9. **Strategy Compiler outputs**
   - dodane są jawne modele `PolicyPatchProposal`, `WorkflowImprovementProposal`, `ProviderRoutingProposal`,
   - Lab ma zdefiniowane typy wyjściowe zamiast narracyjnego opisu.

10. **Faza -1**
   - dokumenty migracyjne mają jawne acceptance criteria i checklistę jakości.

---

## Mapa repozytoriów

| Repo | Rola v3 | Priorytet |
|---|---|---|
| `RAE-Suite` | Control Plane fabryki | ★★★★★ |
| `RAE-agentic-memory` | Runtime pamięci (zgodny z rae-core) | ★★★★★ |
| `RAE-Phoenix` | Dział planowania | ★★★★☆ |
| `RAE-Hive` | Dział wykonania | ★★★★☆ |
| `RAE-Quality` | Dział kontroli jakości | ★★★☆☆ |
| `RAE-Lab` | Improvement Plane | ★★★☆☆ |
| `RAE-openclaw` | Zewnętrzny agent (utrzymaj obecne ramy) | ★★☆☆☆ |

---

## FAZA 0 — Konstytucja systemu (`rae-core` schemas)

**Cel:** Zamrozić kanoniczne kontrakty danych. Wszystkie kolejne fazy bazują na tych typach.  
**Repo docelowe:** `RAE-Suite` (katalog `contracts/`) + każde sub-repo tworzy własny `rae_core/` import  
**Czas szacowany:** 3–5 dni roboczych agenta

---

### TASK-0.1 — Utworzenie pakietu `rae-core` jako shared Python package

**Lokalizacja:** `RAE-Suite/packages/rae-core/`

```
packages/rae-core/
├── pyproject.toml
├── README.md
└── src/
    └── rae_core/
        ├── __init__.py
        ├── version.py          # wersja kontraktów, np. "1.0.0"
        ├── models/
        │   ├── __init__.py
        │   ├── factory.py      # Factory, Department, AgentRole
        │   ├── capability.py   # Capability, CapabilityContract
        │   ├── workflow.py     # Workflow, Task, Artifact
        │   ├── evidence.py     # ActionRecord, DecisionEvidenceRecord, OutcomeRecord
        │   ├── failure.py      # FailureLearningRecord
        │   ├── policy.py       # PolicyDecisionRecord
        │   ├── audit.py        # AuditVerdict
        │   ├── improvement.py  # Experiment, ExperimentRun, Hypothesis, CandidateStrategy,
        │   │                   # ImprovementProposal, ShadowRun, CanaryRollout,
        │   │                   # PromotionDecision, RollbackDecision,
        │   │                   # InsightPack, FailurePatternPack, BenchmarkSuite
        │   └── mesh.py         # MeshPeer, MeshExchangeEnvelope, ConsentGrant
        └── schemas/
            ├── factory_spec_v1.yaml    # kanoniczny schemat FactorySpec YAML
            └── capability_contract_v1.yaml
```

**Implementacja modeli — używaj Pydantic v2:**

```python
# packages/rae-core/src/rae_core/models/evidence.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid

class ActionRecord(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department: str
    role: str
    action_type: str
    goal: str
    tools_used: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str

class DecisionEvidenceRecord(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_summary: str
    reasoning_summary: str
    policy_basis: Optional[str] = None
    input_refs: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    cost: Optional[float] = None

class OutcomeRecord(BaseModel):
    outcome_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str
    result: str  # "success" | "failure" | "partial"
    quality_result: Optional[str] = None
    latency_ms: Optional[int] = None
    cost: Optional[float] = None
    observed_effect: Optional[str] = None
```

```python
# packages/rae-core/src/rae_core/models/factory.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AgentRole(BaseModel):
    role_id: str
    department: str
    responsibilities: List[str]
    allowed_capabilities: List[str]
    escalation_path: Optional[str] = None

class Department(BaseModel):
    name: str
    engine: str  # "phoenix" | "hive" | "quality" | "lab" | "auditor"
    capabilities: List[str]
    risk_class: str = "medium"  # "low" | "medium" | "high" | "critical"
    allowed_models: List[str] = Field(default_factory=list)
    required_policies: List[str] = Field(default_factory=list)
    status: str = "inactive"

class FactorySpec(BaseModel):
    api_version: str = "rae.dev/v1"
    kind: str = "Factory"
    metadata: Dict[str, Any]
    spec: Dict[str, Any]  # parsowany dalej przez Control Plane
```

```python
# packages/rae-core/src/rae_core/models/improvement.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid

class Hypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str
    motivation: str
    target_metric: str
    origin: Literal["lab", "quality", "auditor", "memory"]

class Experiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_ref: str
    baseline: str
    candidate: str
    dataset_refs: List[str] = Field(default_factory=list)
    risk_class: str = "low"
    budget_limit: Optional[float] = None
    success_criteria: str

class ExperimentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    mode: Literal["offline", "shadow", "canary"]
    metrics: dict = Field(default_factory=dict)
    result: Optional[str] = None  # "pass" | "fail" | "inconclusive"
    trace_id: str

class InsightPack(BaseModel):
    pack_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str
    title: str
    insights: List[str]
    source_experiments: List[str]
    applicable_to: List[str]
    ttl_days: Optional[int] = None

class FailurePatternPack(BaseModel):
    pack_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str
    patterns: List[dict]  # [{pattern, frequency, guardrail, retry_recommendation}]
    source_failures: List[str]
```

**TASK-0.1 Acceptance Criteria:**
- `python -m pytest packages/rae-core/tests/` — 100% pass
- Wszystkie modele importowalne przez: `from rae_core.models.evidence import ActionRecord`
- `pyproject.toml` z wersją `0.1.0`
- Brak circular imports

---

### TASK-0.2 — Schemat `FactorySpec` v1 YAML

**Lokalizacja:** `RAE-Suite/contracts/factory_spec_v1.yaml`

```yaml
# contracts/factory_spec_v1.yaml
# Schemat JSONSchema-compatible dla FactorySpec YAML

$schema: "http://json-schema.org/draft-07/schema#"
title: FactorySpec
type: object
additionalProperties: false
required: [apiVersion, kind, metadata, spec]
properties:
  apiVersion:
    type: string
    enum: ["rae.dev/v1"]
  kind:
    type: string
    enum: ["Factory"]
  metadata:
    type: object
    additionalProperties: true
    required: [name]
    properties:
      name:
        type: string
      labels:
        type: object
  spec:
    type: object
    additionalProperties: false
    required: [profile, departments]
    properties:
      profile:
        type: string
        enum: ["local", "secure", "mobile", "factory", "research"]
      memory:
        type: object
        additionalProperties: false
        properties:
          runtime:
            type: string
          meshEnabled:
            type: boolean
          consentMode:
            type: string
            enum: ["explicit", "implicit", "disabled"]
      costModel:
        type: object
        additionalProperties: false
        required: [baseUnit, weights]
        properties:
          baseUnit:
            type: string
            enum: ["NCU"]
          currency:
            type: string
          weights:
            type: object
            additionalProperties:
              type: number
      departments:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [name, engine, capabilities]
          properties:
            name:
              type: string
            engine:
              type: string
            capabilities:
              type: array
              items:
                type: string
            risk_class:
              type: string
              enum: ["low", "medium", "high", "critical"]
            behaviorContractRef:
              type: string
      policies:
        type: array
        items:
          type: string
      gates:
        type: array
        items:
          type: string
      improvement:
        type: object
        additionalProperties: false
        properties:
          enabled:
            type: boolean
          requireShadowBeforeCanary:
            type: boolean
          requireRollbackPlan:
            type: boolean
          experimentBudget:
            type: object
            additionalProperties: false
            properties:
              dailyNCU:
                type: number
              monthlyNCU:
                type: number
```

---

### TASK-0.3 — Canonical `FactorySpec` przykład dla RAE-Suite main

**Lokalizacja:** `RAE-Suite/factory.yaml`

```yaml
apiVersion: rae.dev/v1
kind: Factory
metadata:
  name: rae-suite-main
  labels:
    env: production
    version: "3.0.0"
spec:
  profile: factory
  memory:
    runtime: rae-agentic-memory
    meshEnabled: false
    consentMode: explicit
  departments:
    - name: planning
      engine: phoenix
      capabilities:
        - plan.refactor
        - plan.migration
        - plan.feature
      risk_class: medium
    - name: production
      engine: hive
      capabilities:
        - execute.container_command
        - execute.playwright_audit
        - execute.script
      risk_class: high
    - name: quality
      engine: quality
      capabilities:
        - scan.sast
        - scan.coverage
        - validate.behavior_contract
      risk_class: medium
    - name: lab
      engine: lab
      capabilities:
        - run.experiment
        - run.shadow
        - publish.insight_pack
        - mine.failures
      risk_class: low
    - name: auditor
      engine: auditor
      capabilities:
        - issue.audit_verdict
        - review.high_risk_change
      risk_class: critical
  policies:
    - iso42001
    - hardFrames
    - zeroRegression
    - costBudget
  gates:
    - quality.mustPass
    - auditor.requiredForHighRisk
  improvement:
    enabled: true
    requireShadowBeforeCanary: true
    requireRollbackPlan: true
    experimentBudget:
      daily: 100
      monthly: 2000
```

---

## FAZA 1 — Minimalny Control Plane

**Cel:** RAE-Suite czyta `FactorySpec` i zarządza stanem fabryki.  
**Repo docelowe:** `RAE-Suite`  
**Czas szacowany:** 5–8 dni roboczych agenta  
**Dependency:** Faza 0 ukończona ✓

---

### TASK-1.1 — Control Plane core module

**Lokalizacja:** `RAE-Suite/src/control_plane/`

```
src/control_plane/
├── __init__.py
├── factory_loader.py       # parsuje factory.yaml → FactorySpec
├── department_registry.py  # rejestr działów i ich statusów
├── capability_registry.py  # rejestr capability z kontraktami
├── reconcile_loop.py       # desired state vs actual state
├── lifecycle_ops.py        # start/stop/replace modułów
├── evidence_router.py      # wysyła ActionRecord do rae-core storage
├── governance_loop.py      # pilnuje policy, budżetów, quality gates
├── routing_loop.py         # dobiera capability i wykonawcę do task
└── health.py               # health/status endpoint
```

**Implementacja `factory_loader.py`:**

```python
import yaml
import jsonschema
from pathlib import Path
from rae_core.models.factory import FactorySpec

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "factory_spec_v1.yaml"

class FactoryLoader:
    def __init__(self, spec_path: str):
        self.spec_path = Path(spec_path)

    def load(self) -> FactorySpec:
        with open(self.spec_path) as f:
            raw = yaml.safe_load(f)
        self._validate(raw)
        return FactorySpec(**raw)

    def _validate(self, raw: dict):
        with open(SCHEMA_PATH) as f:
            schema = yaml.safe_load(f)
        jsonschema.validate(raw, schema)
```

**Implementacja `department_registry.py`:**

```python
from typing import Dict, Optional
from rae_core.models.factory import Department
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DepartmentEntry:
    department: Department
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    endpoint: Optional[str] = None

class DepartmentRegistry:
    def __init__(self):
        self._registry: Dict[str, DepartmentEntry] = {}

    def register(self, dept: Department, endpoint: str = None):
        self._registry[dept.name] = DepartmentEntry(department=dept, endpoint=endpoint)

    def heartbeat(self, dept_name: str):
        if dept_name in self._registry:
            self._registry[dept_name].last_heartbeat = datetime.utcnow()

    def get(self, dept_name: str) -> Optional[DepartmentEntry]:
        return self._registry.get(dept_name)

    def list_active(self) -> list[str]:
        cutoff = 60  # sekund
        now = datetime.utcnow()
        return [
            name for name, entry in self._registry.items()
            if entry.last_heartbeat and
               (now - entry.last_heartbeat).seconds < cutoff
        ]

    def health_snapshot(self) -> dict:
        return {
            name: {
                "status": "active" if name in self.list_active() else "stale",
                "capabilities": entry.department.capabilities,
                "endpoint": entry.endpoint,
            }
            for name, entry in self._registry.items()
        }
```

**Implementacja `reconcile_loop.py`:**

```python
import asyncio
import logging
from rae_core.models.factory import FactorySpec
from .department_registry import DepartmentRegistry

logger = logging.getLogger(__name__)

class ReconcileLoop:
    """
    Porównuje desired state (FactorySpec) z actual state (DepartmentRegistry).
    Uruchamia co INTERVAL sekund. Dryfujące działy są flagowane, nie wyłączane.
    """
    INTERVAL = 30  # sekund

    def __init__(self, spec: FactorySpec, registry: DepartmentRegistry):
        self.spec = spec
        self.registry = registry
        self.drift_log: list[dict] = []

    async def run(self):
        while True:
            self._reconcile()
            await asyncio.sleep(self.INTERVAL)

    def _reconcile(self):
        desired = {d["name"] for d in self.spec.spec.get("departments", [])}
        actual = set(self.registry.list_active())

        missing = desired - actual
        unexpected = actual - desired

        for dept_name in missing:
            logger.warning(f"DRIFT: Department '{dept_name}' desired but not active")
            self.drift_log.append({
                "type": "missing_department",
                "department": dept_name,
                "action": "alert"
            })

        for dept_name in unexpected:
            logger.info(f"DRIFT: Department '{dept_name}' active but not in spec")
            self.drift_log.append({
                "type": "unexpected_department",
                "department": dept_name,
                "action": "log"
            })
```

**Implementacja `evidence_router.py`:**

```python
from rae_core.models.evidence import ActionRecord, OutcomeRecord, DecisionEvidenceRecord
from typing import Protocol

class EvidenceStore(Protocol):
    def save_action(self, record: ActionRecord) -> None: ...
    def save_outcome(self, record: OutcomeRecord) -> None: ...
    def save_decision(self, record: DecisionEvidenceRecord) -> None: ...

class EvidenceRouter:
    """
    Warstwa pośrednia — Control Plane zapisuje tu evidence,
    router decyduje gdzie to trafia (rae-agentic-memory / local log / Mesh).
    """
    def __init__(self, store: EvidenceStore):
        self._store = store

    def record_action(self, record: ActionRecord):
        self._store.save_action(record)

    def record_outcome(self, record: OutcomeRecord):
        self._store.save_outcome(record)

    def record_decision(self, record: DecisionEvidenceRecord):
        self._store.save_decision(record)
```

**Implementacja `health.py` (FastAPI endpoint):**

```python
from fastapi import FastAPI
from .department_registry import DepartmentRegistry

def create_health_router(registry: DepartmentRegistry):
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/status")
    def status():
        return {
            "factory": "rae-suite-main",
            "departments": registry.health_snapshot(),
        }

    return router
```

**TASK-1.1 Acceptance Criteria:**
- `factory_loader.py` — parsuje `factory.yaml` bez błędów, rzuca `ValidationError` dla złego YAML
- `department_registry.py` — `heartbeat()` + `list_active()` + `health_snapshot()` działają
- `reconcile_loop.py` — wykrywa missing/unexpected departments po 30s
- `evidence_router.py` — zapisuje do mock store w testach
- `GET /status` zwraca health snapshot

---

### TASK-1.2 — Capability Registry z routing

**Lokalizacja:** `RAE-Suite/src/control_plane/capability_registry.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from rae_core.models.factory import Department

@dataclass
class CapabilityEntry:
    capability_id: str
    department: str
    risk_class: str = "medium"
    cost_weight: float = 1.0
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None

class CapabilityRegistry:
    def __init__(self):
        self._entries: Dict[str, CapabilityEntry] = {}

    def register_from_department(self, dept: Department):
        for cap_id in dept.capabilities:
            self._entries[cap_id] = CapabilityEntry(
                capability_id=cap_id,
                department=dept.name,
                risk_class=dept.risk_class,
            )

    def resolve(self, capability_id: str) -> Optional[CapabilityEntry]:
        return self._entries.get(capability_id)

    def route_task(self, required_capability: str, risk_filter: str = None) -> Optional[str]:
        """Zwraca nazwę działu zdolnego obsłużyć capability."""
        entry = self.resolve(required_capability)
        if not entry:
            return None
        if risk_filter and entry.risk_class != risk_filter:
            return None
        return entry.department
```

---

### TASK-1.3 — Main entrypoint Control Plane

**Lokalizacja:** `RAE-Suite/src/main.py`

```python
import asyncio
import uvicorn
from fastapi import FastAPI
from control_plane.factory_loader import FactoryLoader
from control_plane.department_registry import DepartmentRegistry
from control_plane.capability_registry import CapabilityRegistry
from control_plane.reconcile_loop import ReconcileLoop
from control_plane.health import create_health_router

app = FastAPI(title="RAE Control Plane", version="3.0.0")

async def startup():
    loader = FactoryLoader("factory.yaml")
    spec = loader.load()

    dept_registry = DepartmentRegistry()
    cap_registry = CapabilityRegistry()

    for dept_data in spec.spec.get("departments", []):
        from rae_core.models.factory import Department
        dept = Department(**dept_data)
        dept_registry.register(dept)
        cap_registry.register_from_department(dept)

    reconciler = ReconcileLoop(spec, dept_registry)

    app.state.spec = spec
    app.state.dept_registry = dept_registry
    app.state.cap_registry = cap_registry

    asyncio.create_task(reconciler.run())

app.add_event_handler("startup", startup)
app.include_router(create_health_router(None), prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=False)
```

---

## FAZA 2 — Independent Auditor

**Cel:** Wydzielony dział z niezależnym torem werdyktów.  
**Repo docelowe:** `RAE-Suite/src/departments/auditor/`  
**Czas szacowany:** 3–4 dni roboczych agenta  
**Dependency:** Faza 1 ukończona ✓

---

### TASK-2.1 — Moduł Auditora

**Lokalizacja:** `RAE-Suite/src/departments/auditor/`

```
src/departments/auditor/
├── __init__.py
├── auditor_engine.py        # główna logika Auditora
├── policy_checker.py        # sprawdzanie zgodności z politykami
├── verdict_store.py         # przechowywanie AuditVerdict
└── api.py                   # FastAPI router dla działu
```

**Implementacja `auditor_engine.py`:**

```python
from rae_core.models.audit import AuditVerdict
from rae_core.models.improvement import ImprovementProposal
from .policy_checker import PolicyChecker
from .verdict_store import VerdictStore
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class AuditorEngine:
    """
    Independent Auditor — wydaje werdykty dla zmian high-risk.
    Działa w izolowanym torze: NIE ma dostępu do wykonania zadań produkcyjnych.
    """

    RISK_REQUIRES_AUDIT = {"high", "critical"}

    def __init__(self, checker: PolicyChecker, store: VerdictStore):
        self.checker = checker
        self.store = store

    def review_proposal(self, proposal: ImprovementProposal) -> AuditVerdict:
        findings = []
        required_actions = []

        # Sprawdź polityki
        policy_issues = self.checker.check(proposal)
        findings.extend(policy_issues)

        # Sprawdź evidence
        if not proposal.evidence_refs:
            findings.append("NO_EVIDENCE: Propozycja nie ma referencji do evidence.")
            required_actions.append("Dodaj referencje do ExperimentRun lub ActionRecord.")

        # Sprawdź wymagania promowania
        if not proposal.promotion_requirements:
            findings.append("NO_PROMOTION_REQUIREMENTS: Brak wymagań promocji.")
            required_actions.append("Zdefiniuj promotion_requirements.")

        status = "approved" if not findings else "requires_changes"

        verdict = AuditVerdict(
            verdict_id=str(uuid.uuid4()),
            subject_ref=proposal.proposal_id,
            status=status,
            severity="high" if len(findings) > 2 else "medium",
            findings=findings,
            required_actions=required_actions,
            approved_by="auditor-engine-v1",
        )

        self.store.save(verdict)
        logger.info(f"Audit verdict for {proposal.proposal_id}: {status}")
        return verdict

    def can_promote(self, proposal_id: str) -> bool:
        verdicts = self.store.get_by_subject(proposal_id)
        if not verdicts:
            return False
        latest = sorted(verdicts, key=lambda v: v.verdict_id)[-1]
        return latest.status == "approved"
```

**Dodaj model do `rae-core`:**

```python
# packages/rae-core/src/rae_core/models/audit.py

from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class AuditVerdict(BaseModel):
    verdict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_ref: str
    status: str  # "approved" | "rejected" | "requires_changes"
    severity: str = "medium"  # "low" | "medium" | "high" | "critical"
    findings: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
```

**TASK-2.1 Acceptance Criteria:**
- `AuditorEngine.review_proposal()` zwraca `AuditVerdict` dla dowolnej `ImprovementProposal`
- Propozycja bez evidence → verdict `requires_changes`
- Propozycja z evidence i wymaganiami → verdict `approved`
- `can_promote()` zwraca False dla braku verdyktu lub rejected

---

### TASK-2.2 — Policy gate integration w Control Plane

**Lokalizacja:** `RAE-Suite/src/control_plane/governance_loop.py`

```python
from rae_core.models.improvement import ImprovementProposal, PromotionDecision
from departments.auditor.auditor_engine import AuditorEngine
import logging

logger = logging.getLogger(__name__)

class GovernanceLoop:
    """
    Pilnuje policy gates przed każdą promocją do Stable Lane.
    """
    def __init__(self, auditor: AuditorEngine):
        self.auditor = auditor

    def evaluate_promotion(self, proposal: ImprovementProposal) -> PromotionDecision:
        verdict = self.auditor.review_proposal(proposal)

        approved = verdict.status == "approved"
        reason = "Approved by auditor" if approved else f"Blocked: {', '.join(verdict.findings)}"

        return PromotionDecision(
            proposal_id=proposal.proposal_id,
            approved=approved,
            reason=reason,
            verdict_ref=verdict.verdict_id,
        )
```

**Dodaj model do `rae-core`:**

```python
# packages/rae-core/src/rae_core/models/improvement.py — uzupełnienie

class PromotionDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    approved: bool
    reason: str
    verdict_ref: Optional[str] = None

class RollbackDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_ref: str  # id taska / deploymentu
    reason: str
    triggered_by: str  # "auditor" | "quality" | "governance" | "manual"
```

---

## FAZA 3 — Improvement Plane MVP

**Cel:** Bezpieczny tor samodoskonalenia obok produkcji.  
**Repo docelowe:** `RAE-Suite/src/improvement_plane/` + integracja z `RAE-Lab`  
**Czas szacowany:** 6–8 dni roboczych agenta  
**Dependency:** Faza 2 ukończona ✓

---

### TASK-3.1 — Improvement Plane core

**Lokalizacja:** `RAE-Suite/src/improvement_plane/`

```
src/improvement_plane/
├── __init__.py
├── hypothesis_manager.py    # zarządzanie hipotezami
├── experiment_manager.py    # tworzenie i śledzenie eksperymentów
├── shadow_runner.py         # uruchamia shadow runs (bez wpływu na prod)
├── canary_manager.py        # ograniczone wdrożenie + auto-rollback
├── promotion_gate.py        # bramka przed Stable Lane
└── improvement_store.py     # persystencja Hypothesis, Experiment, ExperimentRun
```

**Implementacja `shadow_runner.py`:**

```python
import logging
from rae_core.models.improvement import ExperimentRun, Experiment
from rae_core.models.evidence import ActionRecord
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ShadowRunner:
    """
    Uruchamia shadow run — równoległy przebieg kandydackiej strategii
    bez wpływu na produkcję. Wyniki trafiają wyłącznie do Improvement Store.
    """

    def __init__(self, improvement_store, evidence_router):
        self.store = improvement_store
        self.evidence = evidence_router

    def run(self, experiment: Experiment, input_data: dict) -> ExperimentRun:
        run_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        logger.info(f"[SHADOW] Starting shadow run {run_id} for experiment {experiment.experiment_id}")

        # Rejestruj akcję w evidence trail
        self.evidence.record_action(ActionRecord(
            department="lab",
            role="shadow_runner",
            action_type="shadow_run",
            goal=f"Shadow evaluation of experiment {experiment.experiment_id}",
            tools_used=["shadow_runner"],
            trace_id=trace_id,
        ))

        # Tutaj: wywołaj kandydacką strategię z input_data
        # WAŻNE: wynik NIE trafia do żadnego produkcyjnego storage
        metrics = self._execute_candidate(experiment.candidate, input_data)

        result = "pass" if self._meets_criteria(metrics, experiment.success_criteria) else "fail"

        run = ExperimentRun(
            run_id=run_id,
            experiment_id=experiment.experiment_id,
            mode="shadow",
            metrics=metrics,
            result=result,
            trace_id=trace_id,
        )

        self.store.save_run(run)
        logger.info(f"[SHADOW] Run {run_id} completed: {result}")
        return run

    def _execute_candidate(self, candidate: str, input_data: dict) -> dict:
        # Placeholder — w implementacji: wywołaj faktyczną strategię kandydacką
        return {"latency_ms": 0, "success_rate": 0.0, "cost": 0.0}

    def _meets_criteria(self, metrics: dict, criteria: str) -> bool:
        # Placeholder — w implementacji: eval kryteriów (może być expression)
        return True
```

**Implementacja `promotion_gate.py`:**

```python
from rae_core.models.improvement import (
    ImprovementProposal, PromotionDecision, RollbackDecision, ExperimentRun
)
from typing import List
import logging

logger = logging.getLogger(__name__)

REQUIRED_GATES = [
    "has_shadow_run",
    "shadow_passed",
    "has_rollback_plan",
    "auditor_approved",
]

class PromotionGate:
    """
    Bramka przed Stable Lane. Każda zmiana musi przejść WSZYSTKIE gate'y.
    Jeśli którykolwiek nie przejdzie — automatyczny rollback.
    """

    def __init__(self, auditor_engine, improvement_store):
        self.auditor = auditor_engine
        self.store = improvement_store

    def evaluate(self, proposal: ImprovementProposal) -> PromotionDecision:
        failures = []

        runs: List[ExperimentRun] = self.store.get_runs_for(proposal.proposal_id)
        shadow_runs = [r for r in runs if r.mode == "shadow"]

        if not shadow_runs:
            failures.append("has_shadow_run: Brak shadow run.")

        if shadow_runs and not any(r.result == "pass" for r in shadow_runs):
            failures.append("shadow_passed: Żaden shadow run nie przeszedł.")

        if not proposal.promotion_requirements:
            failures.append("has_rollback_plan: Brak promotion_requirements.")

        if not self.auditor.can_promote(proposal.proposal_id):
            failures.append("auditor_approved: Brak zatwierdzonego werdyktu Auditora.")

        if failures:
            logger.warning(f"Promotion BLOCKED for {proposal.proposal_id}: {failures}")
            return PromotionDecision(
                proposal_id=proposal.proposal_id,
                approved=False,
                reason="; ".join(failures),
            )

        logger.info(f"Promotion APPROVED for {proposal.proposal_id}")
        return PromotionDecision(
            proposal_id=proposal.proposal_id,
            approved=True,
            reason="All gates passed.",
        )
```

---

## FAZA 4 — RAE-Lab Evolution Engine

**Cel:** Lab jako aktywny silnik eksperymentów, nie tylko analityk.  
**Repo docelowe:** `RAE-Lab` (osobne repo)  
**Czas szacowany:** 8–10 dni roboczych agenta  
**Dependency:** Faza 3 ukończona ✓

---

### TASK-4.1 — Submoduły RAE-Lab

**Struktura docelowa `RAE-Lab`:**

```
RAE-Lab/
├── pyproject.toml
├── src/
│   └── rae_lab/
│       ├── __init__.py
│       ├── experiment_orchestrator.py    # definiuje i uruchamia eksperymenty
│       ├── hypothesis_engine.py          # tworzy hipotezy z obserwacji
│       ├── failure_mining_engine.py      # analizuje FailureLearningRecord
│       ├── strategy_compiler.py          # kompiluje wyniki do InsightPack etc.
│       └── safe_rollout_manager.py       # shadow → canary → promote/rollback
└── tests/
```

**Implementacja `hypothesis_engine.py`:**

```python
from rae_core.models.improvement import Hypothesis
from rae_core.models.failure import FailureLearningRecord
from rae_core.models.evidence import OutcomeRecord
from typing import List
import uuid
import logging

logger = logging.getLogger(__name__)

class HypothesisEngine:
    """
    Tworzy hipotezy na podstawie:
    - FailureLearningRecord (pattern recognition)
    - OutcomeRecord (quality degradation signals)
    - InsightPack (strategiczne wskazówki)
    """

    def generate_from_failures(self, failures: List[FailureLearningRecord]) -> List[Hypothesis]:
        hypotheses = []

        # Grupuj po failure_type
        by_type: dict = {}
        for f in failures:
            by_type.setdefault(f.failure_type, []).append(f)

        for failure_type, records in by_type.items():
            if len(records) >= 2:  # recurring pattern
                common_lesson = records[0].lesson_learned or "nieznana lekcja"
                h = Hypothesis(
                    hypothesis_id=str(uuid.uuid4()),
                    statement=f"Zmiana guardrail dla '{failure_type}' zredukuje powtórzenia.",
                    motivation=f"Wzorzec wykryty {len(records)}x. Przykład: {common_lesson}",
                    target_metric="failure_rate",
                    origin="lab",
                )
                hypotheses.append(h)
                logger.info(f"Generated hypothesis: {h.hypothesis_id} for pattern '{failure_type}'")

        return hypotheses

    def generate_from_outcomes(self, outcomes: List[OutcomeRecord]) -> List[Hypothesis]:
        hypotheses = []
        failures = [o for o in outcomes if o.result == "failure"]
        failure_rate = len(failures) / max(len(outcomes), 1)

        if failure_rate > 0.15:
            h = Hypothesis(
                hypothesis_id=str(uuid.uuid4()),
                statement="Wysoki failure rate sugeruje problem z current strategy.",
                motivation=f"Failure rate: {failure_rate:.1%} (próg: 15%)",
                target_metric="success_rate",
                origin="lab",
            )
            hypotheses.append(h)

        return hypotheses
```

**Implementacja `failure_mining_engine.py`:**

```python
from rae_core.models.failure import FailureLearningRecord
from rae_core.models.improvement import FailurePatternPack
from typing import List
from collections import Counter
import uuid

class FailureMiningEngine:
    """
    Analizuje FailureLearningRecord i produkuje FailurePatternPack.
    Szuka: recurring failure_type, kosztownych wasted_cost, missing guardrails.
    """

    MIN_PATTERN_COUNT = 2
    HIGH_COST_THRESHOLD = 50.0  # jednostki kosztu

    def mine(self, records: List[FailureLearningRecord]) -> FailurePatternPack:
        type_counts = Counter(r.failure_type for r in records)
        recurring = {t: c for t, c in type_counts.items() if c >= self.MIN_PATTERN_COUNT}

        costly = [r for r in records if (r.wasted_cost or 0) >= self.HIGH_COST_THRESHOLD]

        patterns = []
        for failure_type, frequency in recurring.items():
            sample = next(r for r in records if r.failure_type == failure_type)
            patterns.append({
                "pattern": failure_type,
                "frequency": frequency,
                "guardrail": sample.future_guardrail or "undefined",
                "retry_recommendation": sample.retry_recommendation or "manual review",
                "avg_cost": sum(
                    r.wasted_cost or 0 for r in records if r.failure_type == failure_type
                ) / frequency,
            })

        return FailurePatternPack(
            pack_id=str(uuid.uuid4()),
            version="1.0.0",
            patterns=patterns,
            source_failures=[r.failure_id for r in records],
        )
```

**Dodaj model do `rae-core`:**

```python
# packages/rae-core/src/rae_core/models/failure.py

from pydantic import BaseModel, Field
from typing import Optional
import uuid

class FailureLearningRecord(BaseModel):
    failure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    failure_type: str
    failure_stage: str
    impact_scope: str = "local"  # "local" | "department" | "factory"
    wasted_cost: Optional[float] = None
    root_cause_hypothesis: Optional[str] = None
    lesson_learned: Optional[str] = None
    future_guardrail: Optional[str] = None
    retry_recommendation: Optional[str] = None
```

**TASK-4.1 Acceptance Criteria:**
- `HypothesisEngine.generate_from_failures()` — dla 3 rekordów tego samego `failure_type` generuje ≥1 hipotezę
- `FailureMiningEngine.mine()` — dla 5 rekordów z 2 typami generuje FailurePatternPack z 2 wzorcami
- `StrategyCompiler` produkuje `InsightPack` lub `PolicyPatchProposal` z listy ExperimentRun
- Testy pokrycia ≥70% dla nowych modułów

---

## FAZA 5 — RAE Fabric (capability-driven routing)

**Cel:** Produkcyjny routing zadań po capability, nie po nazwach modułów.  
**Repo docelowe:** `RAE-Suite/src/fabric/`  
**Czas szacowany:** 5–6 dni roboczych agenta  
**Dependency:** Faza 4 ukończona ✓

---

### TASK-5.1 — RAE Fabric module

**Lokalizacja:** `RAE-Suite/src/fabric/`

```
src/fabric/
├── __init__.py
├── capability_lattice.py    # graf linków między capability
├── cost_aware_router.py     # routing z uwzględnieniem kosztu i ryzyka
├── contract_validator.py    # walidacja input/output vs schemat capability
└── fabric_telemetry.py      # metryki latency, cost, success/failure per capability
```

**Implementacja `cost_aware_router.py`:**

```python
from dataclasses import dataclass
from typing import Optional, List
from control_plane.capability_registry import CapabilityRegistry, CapabilityEntry
import logging

logger = logging.getLogger(__name__)

@dataclass
class RoutingDecision:
    capability_id: str
    department: str
    estimated_cost: float
    risk_class: str
    reason: str

class CostAwareRouter:
    """
    Dobiera wykonawcę dla capability z uwzględnieniem:
    - risk_class (nie przekraczaj dozwolonego ryzyka)
    - cost_weight (preferuj tańszych wykonawców)
    - availability (heartbeat w rejestrze)
    """

    def __init__(self, cap_registry: CapabilityRegistry, dept_registry):
        self.caps = cap_registry
        self.depts = dept_registry

    def route(
        self,
        capability_id: str,
        max_risk: str = "high",
        budget: Optional[float] = None,
    ) -> Optional[RoutingDecision]:
        entry: Optional[CapabilityEntry] = self.caps.resolve(capability_id)
        if not entry:
            logger.warning(f"Capability '{capability_id}' not found in registry")
            return None

        risk_order = ["low", "medium", "high", "critical"]
        if risk_order.index(entry.risk_class) > risk_order.index(max_risk):
            logger.warning(f"Capability '{capability_id}' risk {entry.risk_class} exceeds max {max_risk}")
            return None

        active = self.depts.list_active()
        if entry.department not in active:
            logger.warning(f"Department '{entry.department}' for '{capability_id}' not active")
            return None

        return RoutingDecision(
            capability_id=capability_id,
            department=entry.department,
            estimated_cost=entry.cost_weight,
            risk_class=entry.risk_class,
            reason="Routed by CostAwareRouter",
        )
```

---

## FAZA 6 — Mesh v1 (federacja wiedzy)

**Cel:** Wymiana zatwierdzonej wiedzy między instancjami RAE za zgodą.  
**Repo docelowe:** `RAE-Suite/src/mesh/`  
**Czas szacowany:** 6–8 dni roboczych agenta  
**Dependency:** Faza 5 ukończona ✓

---

### TASK-6.1 — Mesh core

**Lokalizacja:** `RAE-Suite/src/mesh/`

```
src/mesh/
├── __init__.py
├── mesh_peer_registry.py    # rejestr zaufanych peerów
├── consent_manager.py       # ConsentGrant CRUD i walidacja
├── exchange_envelope.py     # tworzenie MeshExchangeEnvelope
├── exporter.py              # eksport InsightPack / FailurePatternPack
└── importer.py              # import + weryfikacja provenance i TTL
```

**Klucze zasady Mesh — embedded w kodzie jako docstring:**

```python
# src/mesh/exporter.py

"""
RAE Mesh Exporter — zasady wymiany:

CO MOŻNA EKSPORTOWAĆ (domyślnie):
  - InsightPack (zatwierdzone przez Lab)
  - FailurePatternPack (zanonimizowane)
  - BenchmarkSuite
  - BehaviorContractPack
  - PolicyPack

CZEGO NIE WOLNO EKSPORTOWAĆ (hard block):
  - Pełny memory store
  - Surowe dane klientów
  - Sekrety i tokeny
  - Wrażliwe logi bez anonimizacji
  - Prywatne eksperymenty bez ConsentGrant

KAŻDA WYMIANA WYMAGA:
  - ConsentGrant z scope i TTL
  - provenance (skąd pochodzi pack)
  - sensitivity_label
  - contract_version
"""

from rae_core.models.mesh import MeshExchangeEnvelope, ConsentGrant, MeshPeer
from rae_core.models.improvement import InsightPack, FailurePatternPack
from typing import Union
import uuid
from datetime import datetime, timedelta

ALLOWED_PACK_TYPES = {InsightPack, FailurePatternPack}
BLOCKED_TYPES_KEYWORDS = ["secret", "token", "password", "raw_memory", "customer_data"]

class MeshExporter:
    def __init__(self, consent_manager):
        self.consent = consent_manager

    def export(
        self,
        pack: Union[InsightPack, FailurePatternPack],
        target_peer: MeshPeer,
        consent_grant: ConsentGrant,
    ) -> MeshExchangeEnvelope:
        if type(pack) not in ALLOWED_PACK_TYPES:
            raise ValueError(f"Pack type {type(pack)} is not allowed for Mesh export.")

        if not self.consent.is_valid(consent_grant, target_peer.peer_id):
            raise PermissionError(f"No valid ConsentGrant for peer {target_peer.peer_id}")

        return MeshExchangeEnvelope(
            envelope_id=str(uuid.uuid4()),
            source_instance="rae-suite-main",
            target_peer_id=target_peer.peer_id,
            pack_type=type(pack).__name__,
            pack_id=pack.pack_id,
            consent_ref=consent_grant.grant_id,
            expires_at=datetime.utcnow() + timedelta(days=consent_grant.ttl_days or 30),
            sensitivity_label="internal",
            contract_version="1.0.0",
        )
```

**Dodaj modele do `rae-core`:**

```python
# packages/rae-core/src/rae_core/models/mesh.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class MeshPeer(BaseModel):
    peer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    endpoint: str
    trust_level: str = "peer"  # "self" | "peer" | "federated" | "untrusted"
    public_key: Optional[str] = None

class ConsentGrant(BaseModel):
    grant_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grantor: str
    grantee: str
    scope: List[str]  # ["InsightPack", "FailurePatternPack"]
    ttl_days: int = 30
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = False

class MeshExchangeEnvelope(BaseModel):
    envelope_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_instance: str
    target_peer_id: str
    pack_type: str
    pack_id: str
    consent_ref: str
    expires_at: datetime
    sensitivity_label: str = "internal"
    contract_version: str = "1.0.0"
```

---

## Integracja z istniejącymi modułami

### RAE-agentic-memory — zmiany wymagane przez v3

Implementuj `EvidenceStore` protokół (wymagany przez Control Plane TASK-1.1):

```python
# W RAE-agentic-memory — nowy plik: src/rae_memory/evidence_adapter.py

from rae_core.models.evidence import ActionRecord, OutcomeRecord, DecisionEvidenceRecord
from rae_core.models.failure import FailureLearningRecord

class MemoryEvidenceStore:
    """
    Adapter: rae-agentic-memory jako backend dla EvidenceRouter Control Plane.
    Zapisuje ActionRecord / OutcomeRecord do istniejącego memory store.
    """

    def __init__(self, memory_client):
        self._client = memory_client  # istniejący klient RAE-agentic-memory

    def save_action(self, record: ActionRecord) -> None:
        # Mapuj na istniejący format memory store
        self._client.store(
            layer="working_memory",
            content={
                "type": "action_record",
                "data": record.model_dump(),
            },
            tags=["evidence", "action", record.department],
        )

    def save_outcome(self, record: OutcomeRecord) -> None:
        self._client.store(
            layer="long_term_memory",
            content={
                "type": "outcome_record",
                "data": record.model_dump(),
            },
            tags=["evidence", "outcome", record.result],
        )

    def save_failure(self, record: FailureLearningRecord) -> None:
        self._client.store(
            layer="reflective_memory",
            content={
                "type": "failure_learning",
                "data": record.model_dump(),
            },
            tags=["failure", "learning", record.failure_type],
        )
```

### RAE-Phoenix — capability registration

W `RAE-Phoenix` dodaj startup hook, który rejestruje się w Control Plane:

```python
# RAE-Phoenix/src/phoenix/startup.py

import httpx
import logging

logger = logging.getLogger(__name__)

CONTROL_PLANE_URL = "http://rae-suite:8090"
PHOENIX_CAPABILITIES = ["plan.refactor", "plan.migration", "plan.feature"]

async def register_with_control_plane(endpoint: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CONTROL_PLANE_URL}/api/v1/departments/register",
                json={
                    "name": "planning",
                    "engine": "phoenix",
                    "capabilities": PHOENIX_CAPABILITIES,
                    "risk_class": "medium",
                    "endpoint": endpoint,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info(f"Phoenix registered with Control Plane: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to register Phoenix with Control Plane: {e}")
```

Analogicznie dla RAE-Hive, RAE-Quality, RAE-Lab.

### RAE-openclaw — bez zmian

RAE-openclaw pozostaje opancerzony swoimi Hard Frames. Jedyna zmiana: dodaj capability `execute.openclaw_task` do jego opcjonalnego profilu, żeby Control Plane mógł go routować.

---

## Docker Compose dla v3

**Lokalizacja:** `RAE-Suite/docker-compose.v3.yml`

```yaml
version: "3.9"

services:
  rae-control-plane:
    build:
      context: .
      dockerfile: Dockerfile.control-plane
    ports:
      - "8090:8090"
    volumes:
      - ./factory.yaml:/app/factory.yaml:ro
    environment:
      - RAE_PROFILE=factory
      - MEMORY_ENDPOINT=http://rae-memory:8080
    depends_on:
      - rae-memory
    networks:
      - rae-internal

  rae-memory:
    image: dreamsoft-pro/rae-agentic-memory:latest
    ports:
      - "8080:8080"
    networks:
      - rae-internal

  rae-phoenix:
    image: dreamsoft-pro/rae-phoenix:latest
    environment:
      - CONTROL_PLANE_URL=http://rae-control-plane:8090
      - SELF_ENDPOINT=http://rae-phoenix:8081
    networks:
      - rae-internal
    depends_on:
      - rae-control-plane

  rae-hive:
    image: dreamsoft-pro/rae-hive:latest
    environment:
      - CONTROL_PLANE_URL=http://rae-control-plane:8090
      - SELF_ENDPOINT=http://rae-hive:8082
    networks:
      - rae-internal
    depends_on:
      - rae-control-plane

  rae-quality:
    image: dreamsoft-pro/rae-quality:latest
    environment:
      - CONTROL_PLANE_URL=http://rae-control-plane:8090
      - SELF_ENDPOINT=http://rae-quality:8083
    networks:
      - rae-internal
    depends_on:
      - rae-control-plane

  rae-lab:
    image: dreamsoft-pro/rae-lab:latest
    environment:
      - CONTROL_PLANE_URL=http://rae-control-plane:8090
      - SELF_ENDPOINT=http://rae-lab:8084
    networks:
      - rae-internal
    depends_on:
      - rae-control-plane

networks:
  rae-internal:
    driver: bridge
```

---

## Quality Gates per faza

Każda faza musi przejść przez te gate'y przed startem kolejnej:

| Gate | Narzędzie | Próg |
|---|---|---|
| Unit tests | `pytest` | 100% pass |
| Coverage | `pytest-cov` | ≥70% nowych modułów |
| Type check | `mypy` | 0 errors |
| Linting | `ruff` | 0 errors |
| Import test | `python -c "from rae_core.models import *"` | pass |
| API contract | `jsonschema.validate(factory.yaml, schema)` | pass |

---

## Odpowiedzi na Otwarte Pytania RFC (sekcja 20)

| # | Pytanie | Odpowiedź implementacyjna |
|---|---|---|
| 1 | Minimalny zestaw rekordów rae-core do zamrożenia | ActionRecord, OutcomeRecord, FailureLearningRecord, AuditVerdict, FactorySpec — Faza 0 |
| 2 | Jak agresywnie wprowadzać FactorySpec? | Ewolucyjnie — factory.yaml jest opcjonalne w Faza 1, wymagane od Faza 2 |
| 3 | Capability obowiązkowe vs opcjonalne | Obowiązkowe: przynajmniej 1 capability per dział. Reszta deklaratywna w spec |
| 4 | Polityki globalne vs per-factory | Globalne w `policies[]` w FactorySpec; per-department w `required_policies` Departmentu |
| 5 | Mechanizm podpisu dla Mesh packów | TTL + scope w ConsentGrant; podpis kryptograficzny — Faza 6 V2 (poza aktualnym scope) |
| 6 | Improvement Plane — osobny storage? | Współdzieli rae-agentic-memory z osobnymi tagami: `improvement`, `experiment`, `shadow` |

---

## Podsumowanie dla agentów

```
FAZA 0: rae-core schemas (Pydantic v2, YAML schema, FactorySpec)
         └── Output: packages/rae-core/ z modelami i schematami

FAZA 1: Control Plane MVP (factory_loader, dept_registry, cap_registry, reconcile, health)
         └── Output: RAE-Suite/src/control_plane/ + main.py + GET /status

FAZA 2: Independent Auditor (auditor_engine, policy_checker, governance_loop)
         └── Output: RAE-Suite/src/departments/auditor/ + integracja z Control Plane

FAZA 3: Improvement Plane MVP (shadow_runner, canary_manager, promotion_gate)
         └── Output: RAE-Suite/src/improvement_plane/

FAZA 4: RAE-Lab Evolution Engine (hypothesis, failure_mining, strategy_compiler)
         └── Output: RAE-Lab/src/rae_lab/ (osobne repo)

FAZA 5: RAE Fabric (capability_lattice, cost_aware_router, contract_validator)
         └── Output: RAE-Suite/src/fabric/

FAZA 6: Mesh v1 (peer_registry, consent_manager, exporter, importer)
         └── Output: RAE-Suite/src/mesh/
```

**Liczy się:** każda faza = działający kod + testy + quality gate = commit do main.


---

# ROZSZERZENIA I KOREKTY v1.1 — ZACHOWUJĄCE PEŁNY ORYGINALNY PLAN

**Cel tej sekcji:** zachować cały oryginalny plan implementacji bez skracania, a jednocześnie
dodać brakujące elementy wskazane w przeglądzie:

1. strategię migracji istniejącego ekosystemu do v3,
2. behavioral contracts dla działów jako całości,
3. kanoniczny model kosztu,
4. politykę kompatybilności wersji kontraktów,
5. mapę zmian do istniejących faz i tasków.

Ta sekcja **nie unieważnia** wcześniejszych faz i tasków. Ona je **uzupełnia, doprecyzowuje i rozszerza**.
W przypadku sprzeczności, pierwszeństwo ma:
1. bezpieczeństwo migracji,
2. kompatybilność `rae-core`,
3. możliwość rollbacku,
4. zachowanie działającej produkcji.

---

## ERRATA-0 — Dlaczego potrzebne są rozszerzenia

Oryginalny plan dobrze opisuje docelową architekturę i kolejność budowy nowych warstw (`rae-core`,
Control Plane, Auditor, Improvement Plane, Fabric, Mesh), ale pozostawia niedopowiedziane trzy
praktyczne kwestie wykonawcze:

- **jak przejść z istniejącego kodu do v3 bez rewrite-first,**
- **jak Audytor ma oceniać zachowanie działu, a nie tylko kompletność payloadów,**
- **co dokładnie oznacza “koszt” w systemie i jak go liczyć.**

Wdrożenie bez tych rozszerzeń groziłoby:
- nadmiernym przepisywaniem modułów,
- pustą semantyką `CostAwareRouter`,
- zbyt proceduralnym audytem,
- rozjechaniem się kontraktów między repozytoriami.

---

## FAZA -1 — Migration Baseline (NOWA FAZA POPRZEDZAJĄCA FAZĘ 0)

**Cel:** dodać warstwę kompatybilności, inwentaryzację integracji i matrycę migracyjną zanim
zacznie się zamrażanie nowych kontraktów `rae-core`.

**Repozytorium główne:** `RAE-Suite`  
**Repozytoria współpracujące:** wszystkie  
**Tryb wdrożenia:** adapter-first / strangler-first

### TASK-M-1.1 — Inwentaryzacja punktów integracyjnych

Utwórz w `RAE-Suite/docs/migration/` zestaw plików:

```
docs/migration/
├── repo_inventory.md
├── integration_points.md
├── legacy_endpoints_matrix.md
├── evidence_gap_analysis.md
├── cost_telemetry_gap_analysis.md
└── behavioral_gap_analysis.md
```

Każdy plik ma zawierać:

- aktualne endpointy, CLI, eventy, joby, wejścia/wyjścia,
- zależności od środowiska, plików, zmiennych env i ścieżek lokalnych,
- które miejsca już mają telemetry, które jej nie mają,
- które miejsca już zapisują jakieś post-mortemy / metryki / wyniki do pamięci,
- które moduły mają stabilne zachowanie, a które są eksperymentalne.

**Acceptance Criteria:**
- każdy z pięciu głównych działów ma oddzielną kartę inwentaryzacyjną,
- istnieje lista wszystkich znanych integration points typu:
  - HTTP API,
  - CLI,
  - job queues,
  - wpis do pliku / JSONL,
  - direct import,
  - docker volume contract,
- istnieje tabela “current behavior vs target v3 contract”.

---

### TASK-M-1.2 — Klasyfikacja migracyjna repozytoriów

W `docs/migration/repo_inventory.md` utwórz kanoniczną tabelę:

| Repo | Rola obecna | Rola v3 | Typ migracji | Uwagi |
|---|---|---|---|---|
| `RAE-Suite` | spinka, compose, uruchamianie | Control Plane | **rewrite / redesign core** | najwyższy priorytet |
| `RAE-agentic-memory` | pamięć / runtime | Memory Runtime | **adapter-first** | zachować działające API, dopiąć `EvidenceStore` |
| `RAE-Phoenix` | planowanie / refaktor | Department: Planning | **wrap + selective refactor** | zachować engine, dodać registry / evidence / contracts |
| `RAE-Hive` | wykonanie | Department: Production | **wrap-first** | zachować executor, dopiąć capability facade |
| `RAE-Quality` | skanowanie / gate'y | Department: Quality | **wrap + harden** | dodać verdict semantics |
| `RAE-Lab` | badania / analityka | Improvement Plane | **partial rewrite** | część istniejących funkcji zostaje, część przechodzi do nowej warstwy |
| `RAE-openclaw` | agent zewnętrzny | optional execution engine | **isolate / minimal adapter** | tylko capability expose, bez przebudowy |

**Typy migracji:**
- `adapter-first` — najpierw adapter i kompatybilność,
- `wrap-first` — moduł zostaje, ale dostaje facade v3,
- `hardening` — dopinamy kontrakty, telemetry, testy, bez dużej przebudowy,
- `partial rewrite` — tylko tam, gdzie zmienia się natura systemu,
- `rewrite / redesign core` — pełna nowa warstwa, jeśli obecna nie odpowiada roli v3.

---

### TASK-M-1.3 — Strangler Plan per repo

Dla każdego repo utwórz jeden dokument `docs/migration/<repo>_strangler_plan.md` z sekcjami:

1. **Current Stable Behavior**
2. **Legacy Interfaces**
3. **v3 Facade**
4. **Deprecated Paths**
5. **Migration Cutpoints**
6. **Rollback Strategy**
7. **Final Ownership in v3**

Przykład dla `RAE-Phoenix`:

- current stable behavior:
  - generowanie planów,
  - refaktor recipes,
  - analiza kodu,
- legacy interfaces:
  - CLI,
  - API,
  - bezpośredni import bibliotek,
- v3 facade:
  - `/department/phoenix/plan`,
  - `plan.refactor`,
  - `plan.migration`,
- deprecated paths:
  - bezpośrednie wywołania spoza control plane,
- rollback strategy:
  - możliwość ominięcia control plane i powrotu do legacy path,
- final ownership:
  - planowanie i strategia zmian.

**Acceptance Criteria:**
- każdy moduł ma jawny strangler plan,
- dla każdego modułu istnieje przynajmniej jeden rollback path,
- żaden moduł nie wymaga “big bang migration”,
- każdy `strangler_plan.md` ma sekcję **migration cutpoints** z minimum 3 punktami przejęcia ruchu,
- każdy `strangler_plan.md` ma sekcję **legacy interfaces** z listą realnych punktów wejścia/wyjścia,
- każdy `strangler_plan.md` ma sekcję **acceptance checklist** zawierającą:
  - zidentyfikowane zależności runtime,
  - wskazany owner końcowy w v3,
  - rollback path zweryfikowany opisowo,
  - oznaczenie strategii migracji (`adapter-first` / `wrap-first` / `partial rewrite` / `rewrite`).


**Minimalny szablon checklisty jakości dokumentu:**

```md
## Acceptance Checklist
- [ ] opisano Current Stable Behavior bez ogólników
- [ ] wypisano wszystkie znane Legacy Interfaces
- [ ] zdefiniowano v3 Facade z nazwami capability / endpointów
- [ ] wskazano co najmniej 3 Migration Cutpoints
- [ ] opisano minimum 1 Rollback Strategy
- [ ] oznaczono typ migracji
- [ ] wskazano Final Ownership in v3
```

---

### TASK-M-1.4 — Compatibility Layer skeleton

Utwórz w `RAE-Suite/src/compat/` następujące szkielety:

```
src/compat/
├── department_adapter.py
├── evidence_adapter.py
├── capability_adapter.py
├── behavioral_adapter.py
├── cost_adapter.py
└── legacy_task_adapter.py
```

Minimalne protokoły:

```python
from typing import Protocol, Any

class DepartmentAdapter(Protocol):
    def register_department(self) -> dict: ...
    def expose_capabilities(self) -> list[dict]: ...
    def expose_behavioral_contract(self) -> dict: ...
    def health(self) -> dict: ...

class EvidenceAdapter(Protocol):
    def emit_action(self, payload: dict) -> None: ...
    def emit_outcome(self, payload: dict) -> None: ...
    def emit_failure(self, payload: dict) -> None: ...

class CostAdapter(Protocol):
    def extract_cost_vector(self, raw: Any) -> dict: ...
```

**Cel:** zanim przebudujesz działy, zapewnij warstwę, przez którą można je podpiąć do v3.

---

## ROZSZERZENIE FAZY 0 — `rae-core` musi zawierać Behavioral + Cost + Compatibility

Oryginalna Faza 0 dobrze zamraża podstawowe schematy, ale należy ją **rozszerzyć** o nowe modele.

### TASK-0.1B — Modele behavioral contracts

Dodaj plik:
`packages/rae-core/src/rae_core/models/behavior.py`

```python
from __future__ import annotations

from typing import Any, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

VerificationMethod = Literal["payload_check", "outcome_check", "pattern_check"]
BehaviorSignalKind = Literal["self_report", "runtime_observation", "policy_signal", "telemetry_signal"]
BehaviorSeverity = Literal["low", "medium", "high", "critical"]


class BehaviorGuarantee(BaseModel):
    guarantee_id: str = Field(default_factory=lambda: str(uuid4()))
    statement: str
    verifiable: bool = True
    verification_method: VerificationMethod
    description: Optional[str] = None
    required_evidence_types: List[str] = Field(default_factory=list)


class BehaviorSignal(BaseModel):
    signal_id: str = Field(default_factory=lambda: str(uuid4()))
    department: str
    signal_kind: BehaviorSignalKind
    guarantee_id: Optional[str] = None
    trace_id: Optional[str] = None
    observed_payload: dict[str, Any] = Field(default_factory=dict)
    observed_outcome: dict[str, Any] = Field(default_factory=dict)
    reason: str
    emitted_by: str
    severity_hint: BehaviorSeverity = "medium"


class BehaviorViolation(BaseModel):
    violation_id: str = Field(default_factory=lambda: str(uuid4()))
    department: str
    guarantee_id: str
    observed_payload: dict[str, Any] = Field(default_factory=dict)
    reason: str
    severity: BehaviorSeverity = "medium"
    source_signal_ids: List[str] = Field(default_factory=list)
    issued_by: str = "auditor"


class DepartmentBehaviorContract(BaseModel):
    department: str
    version: str
    guarantees: List[BehaviorGuarantee] = Field(default_factory=list)
    forbidden_behaviors: List[str] = Field(default_factory=list)
    required_evidence: List[str] = Field(default_factory=list)
    escalation_rules: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
```

**Normatywna decyzja architektoniczna:**
- dział **może** emitować `BehaviorSignal`,
- dział **nie może** sam wystawiać `BehaviorViolation`,
- tylko **Auditor** (lub jego delegowany engine audytowy) może przekształcić sygnał w oficjalne `BehaviorViolation`.

To rozdziela:
- **obserwację** (`BehaviorSignal`),
- **werdykt** (`BehaviorViolation`).

**Acceptance Criteria:**
- kontrakty działów są importowalne z `rae_core.models.behavior`,
- istnieją testy walidujące serializację/deserializację modeli,
- każdy dział ma przykładowy kontrakt testowy,
- istnieje co najmniej jeden test pokazujący przepływ `BehaviorSignal -> BehaviorViolation`,
- dokumentacja wprost zabrania self-issuing `BehaviorViolation` przez działy.

### TASK-0.1C — Modele kosztu

Dodaj plik:
`packages/rae-core/src/rae_core/models/cost.py`

```python
from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class CostVector(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    wall_time_s: float = 0.0
    cpu_s: float = 0.0
    gpu_s: float = 0.0
    ram_gb_s: float = 0.0
    storage_gb_s: float = 0.0
    transfer_mb: float = 0.0
    external_api_currency: float = 0.0
    operator_minutes: float = 0.0


class CostPolicy(BaseModel):
    policy_id: str
    name: str
    weights: Dict[str, float] = Field(default_factory=dict)
    budget_ncu_daily: Optional[float] = None
    budget_ncu_monthly: Optional[float] = None
    budget_ncu_per_experiment: Optional[float] = None
    budget_ncu_per_action: Optional[float] = None
    currency: str = "USD"


class BudgetEnvelope(BaseModel):
    policy_id: str
    daily_limit_ncu: Optional[float] = None
    monthly_limit_ncu: Optional[float] = None
    per_experiment_limit_ncu: Optional[float] = None
    per_action_limit_ncu: Optional[float] = None
    hard_stop: bool = True
```

**Normatywna definicja kosztu w RAE:**
- `CostVector` przechowuje **surowe** składowe kosztu,
- `NCU` (Normalized Cost Unit) jest liczone **poza** `CostVector`, na podstawie `CostPolicy`,
- pola budżetowe i routingowe używają **NCU**, nie pojedynczego float bez semantyki.

**Referencyjna implementacja normalizacji:**

```python
from rae_core.models.cost import CostPolicy, CostVector


def compute_ncu(vector: CostVector, policy: CostPolicy) -> float:
    total = 0.0
    for field, weight in policy.weights.items():
        total += float(getattr(vector, field, 0.0)) * weight
    return total
```

**Acceptance Criteria:**
- `CostVector`, `CostPolicy` i `BudgetEnvelope` są importowalne z `rae_core.models.cost`,
- `compute_ncu()` ma testy jednostkowe na co najmniej 3 politykach,
- każda decyzja routingowa i każdy experiment budget używają NCU, nie anonimowego `float`,
- dokumentacja wyjaśnia różnicę między surowym kosztem a znormalizowanym NCU.

### TASK-0.1D — Rozszerzenie istniejących modeli evidence o `CostVector`

Zmień istniejące modele z TASK-0.1 tak, aby koszt nie był już prostym `Optional[float]`, tylko:

```python
from rae_core.models.cost import CostVector

class DecisionEvidenceRecord(BaseModel):
    ...
    cost_vector: Optional[CostVector] = None

class OutcomeRecord(BaseModel):
    ...
    cost_vector: Optional[CostVector] = None
```

**Reguła kompatybilności:** tymczasowo można utrzymać alias `cost: Optional[float]`,
ale tylko jako pole deprecated. Alias ten **nie mapuje do nieistniejącego pola w `CostVector`**.
Dopuszczalne są wyłącznie dwie strategie kompatybilności:
1. podczas odczytu legacy payloadu tworzysz `cost_vector` i wyliczasz NCU przez `compute_ncu(cost_vector, default_policy)`,
2. albo usuwasz alias w kolejnym breaking release zgodnie z semver.

`CostVector` przechowuje wyłącznie koszt surowy; NCU jest wartością wyliczaną funkcją, a nie polem modelu.

---

### TASK-0.1E — Modele kompatybilności kontraktów

Dodaj plik:
`packages/rae-core/src/rae_core/models/compatibility.py`

```python
from pydantic import BaseModel
from typing import Literal, List

class ContractCompatibility(BaseModel):
    contract_name: str
    current_version: str
    compatible_with: List[str]
    deprecated_versions: List[str] = []
    breaking_from: List[str] = []

class DeprecationPolicy(BaseModel):
    min_supported_minor_versions: int = 2
    deprecation_notice_required: bool = True
    breaking_change_requires_major: bool = True
```

---

### TASK-0.2A — Rozszerzenie schematu `FactorySpec` o koszt i behavioral requirements

Dopisz do `FactorySpec` następujące bloki:

```yaml
costModel:
  baseUnit: NCU
  currency: USD
  weights:
    input_tokens: 0.000001
    output_tokens: 0.000002
    wall_time_s: 0.01
    cpu_s: 0.01
    gpu_s: 0.20
    ram_gb_s: 0.005
    storage_gb_s: 0.001
    transfer_mb: 0.0005
    external_api_currency: 1.0
    operator_minutes: 2.0

departments:
  - name: planning
    engine: phoenix
    capabilities:
      - plan.refactor
    behaviorContractRef: contracts/behavior/phoenix_v1.yaml
```

oraz:

```yaml
improvement:
  enabled: true
  requireShadowBeforeCanary: true
  requireRollbackPlan: true
  experimentBudget:
    dailyNCU: 500
    monthlyNCU: 5000
```

**Wymóg synchronizacji schematu:**
po dodaniu `costModel` i `behaviorContractRef` musisz zaktualizować również `contracts/factory_spec_v1.yaml`.
FactoryLoader walidujący YAML przez `jsonschema` **musi** odrzucać brakujące lub błędne pola tych sekcji.
Nie wolno polegać na `additionalProperties: true` jako obejściu; nowe pola muszą być jawnie opisane w schemacie.

**Acceptance Criteria:**
- `factory.yaml` z `costModel` i `behaviorContractRef` przechodzi walidację,
- `factory.yaml` bez wymaganych pól `costModel.baseUnit` lub `costModel.weights` nie przechodzi walidacji,
- `factory.yaml` z nieznanym polem w `department` jest odrzucany.

---

## NOWA SEKCJA — Behavioral Contracts działów

Capability contract odpowiada na pytanie:
**“jak wywołać daną capability?”**

Behavioral contract odpowiada na pytanie:
**“jak ten dział ma się zachowywać jako instytucja w systemie?”**

To jest kluczowe dla Auditora.

### Behavioral Contract — Phoenix

Phoenix gwarantuje, że:
1. każdy plan posiada jasno wskazany **cel, ograniczenia, ryzyka, rekomendowaną ścieżkę i uzasadnienie**,
2. nie emituje planu high-risk bez `rollback_intent`,
3. nie proponuje refaktoru bez wskazania rodzaju expected impact,
4. jeśli confidence < zadanego progu, oznacza wynik jako wymagający eskalacji,
5. nie pomija dependencies wpływających na integralność planu.

**Forbidden behaviors:**
- plan bez evidence refs,
- plan bez risk classification,
- plan udający wysoką pewność przy niskiej jakości danych wejściowych.

### Behavioral Contract — Hive

Hive gwarantuje, że:
1. każde wykonanie ma `trace_id`,
2. każdy execution result ma exit semantics (`success`, `failure`, `partial`, `timeout`, `blocked`),
3. działania high-risk są jawnie oznaczane,
4. powstałe artefakty są referencjonowane w evidence trail,
5. zużycie zasobów jest raportowane do `CostVector`.

**Forbidden behaviors:**
- ukryte side-effecty poza zadeklarowaną capability,
- brak raportu o wykorzystaniu zasobów przy zadaniach wykonawczych,
- wykonanie bez audytowalnego outcome.

### Behavioral Contract — Quality

Quality gwarantuje, że:
1. każdy verdict zawiera **scope**, **engine set**, **severity** i **evidence refs**,
2. `pass` bez wymaganego coverage lub bez wymaganego scope jest nieważny,
3. `fail` jest reprodukowalny lub oznaczony jako `non_reproducible_suspected`,
4. raport bezpieczeństwa nie ukrywa false positives — oznacza je jawnie,
5. quality gate zawsze zwraca binarny status plus uzasadnienie.

**Forbidden behaviors:**
- zielony verdict bez minimalnego dowodu,
- pass uzyskany przez ominięcie engine,
- nadpisanie fail do pass bez nowego evidence.

### Behavioral Contract — Lab

Lab gwarantuje, że:
1. każdy eksperyment ma hipotezę, baseline, success criteria i budget,
2. każdy experiment run ma zapisany mode (`offline`, `shadow`, `canary`),
3. insight pack ma provenance i applicability scope,
4. failure mining nie promuje strategii bez danych porównawczych,
5. propozycje zmian są pakowane jako `ImprovementProposal`, nie jako bezpośrednia mutacja produkcji.

**Forbidden behaviors:**
- bezpośrednia promocja eksperymentalnej strategii do stable lane,
- eksperyment bez rollback assumptions,
- insight bez odniesienia do źródła.

### Behavioral Contract — Independent Auditor

Auditor gwarantuje, że:
1. działa read-mostly wobec większości systemu,
2. werdykt zawiera podstawę polityczną i dowodową,
3. ocenia nie tylko formalną poprawność kontraktu, ale też spełnienie gwarancji działu,
4. high-risk promotion bez werdyktu Auditora jest nieważna, jeśli polityka tego wymaga,
5. każdy blokujący verdict jest wersjonowany i audytowalny.

**Forbidden behaviors:**
- arbitralne blokowanie bez evidence,
- verdict bez policy basis,
- modyfikacja produkcji w ramach działania audytowego.

---

## TASK-1.2B — Behavioral Contract Registry

Rozszerz Control Plane o registry kontraktów zachowania:

```
src/control_plane/behavior_registry.py
```

Minimalny interfejs:

```python
from rae_core.models.behavior import DepartmentBehaviorContract

class BehaviorRegistry:
    def __init__(self):
        self._contracts: dict[str, DepartmentBehaviorContract] = {}

    def register(self, contract: DepartmentBehaviorContract) -> None:
        self._contracts[contract.department] = contract

    def get(self, department: str) -> DepartmentBehaviorContract | None:
        return self._contracts.get(department)
```

Control Plane podczas rejestracji działu powinien wymagać:
- listy capability,
- endpointu health,
- behavioral contract,
- deklaracji cost telemetry support.

---

## TASK-2.1A — Auditor musi umieć weryfikować behavioral guarantees

Rozszerz `auditor_engine.py` o sprawdzanie:
- czy department dostarczył wszystkie wymagane evidence,
- czy outcome semantycznie odpowiada gwarancjom działu,
- czy wystąpiły `BehaviorSignal`, które po ocenie powinny przejść w `BehaviorViolation`.

Dodaj funkcje:

```python
from rae_core.models.behavior import (
    BehaviorSignal,
    BehaviorViolation,
    DepartmentBehaviorContract,
)


def collect_behavior_signals(observed_payloads: list[dict]) -> list[BehaviorSignal]:
    """
    Mapuje surowe payloady obserwacyjne do ustrukturyzowanych sygnałów.

    Minimalny kontrakt wejścia dla `observed_payloads`:
    {
        "department": "phoenix",
        "signal_kind": "self_report",
        "guarantee_id": "plan.has_risk_section",
        "summary": "Plan nie zawiera sekcji ryzyk",
        "observed_payload": {"plan_id": "p-123", "missing_sections": ["risks"]},
        "source": "phoenix"
    }

    Reguły mapowania v1:
    - `summary` -> `reason`
    - `source` -> `emitted_by`
    - brak `observed_outcome` oznacza pusty dict
    - brak `severity_hint` oznacza "medium"

    Jeżeli dział już emituje `BehaviorSignal`, funkcja może działać jako walidujący passthrough.
    """
    result: list[BehaviorSignal] = []
    for payload in observed_payloads:
        if isinstance(payload, BehaviorSignal):
            result.append(payload)
            continue
        result.append(
            BehaviorSignal(
                department=payload["department"],
                signal_kind=payload["signal_kind"],
                guarantee_id=payload.get("guarantee_id"),
                trace_id=payload.get("trace_id"),
                observed_payload=payload.get("observed_payload", {}),
                observed_outcome=payload.get("observed_outcome", {}),
                reason=payload.get("summary") or payload.get("reason") or "behavior signal",
                emitted_by=payload.get("source") or payload.get("emitted_by") or payload["department"],
                severity_hint=payload.get("severity_hint", "medium"),
            )
        )
    return result


def evaluate_behavioral_contract(
    contract: DepartmentBehaviorContract,
    signals: list[BehaviorSignal],
) -> list[BehaviorViolation]:
    """
    Referencyjna implementacja v1:
    - rozpatrujemy tylko sygnały powiązane z guarantee_id obecnym w kontrakcie,
    - każdy sygnał o severity_hint >= medium dla gwarancji oznacza violation,
    - auditor wystawia oficjalny werdykt i wiąże go z signal_id.

    Bardziej zaawansowane reguły (pattern_check, outcome_check, korelacja wielu sygnałów)
    mogą zostać dodane w v2, ale v1 musi być deterministyczne i wspólne.
    """
    guarantee_ids = {g.guarantee_id for g in contract.guarantees if g.verifiable}
    violations: list[BehaviorViolation] = []

    for signal in signals:
        if signal.department != contract.department:
            continue
        if not signal.guarantee_id or signal.guarantee_id not in guarantee_ids:
            continue
        if signal.severity_hint == "low":
            continue

        violations.append(
            BehaviorViolation(
                department=contract.department,
                guarantee_id=signal.guarantee_id,
                observed_payload=signal.observed_payload,
                reason=signal.reason,
                severity=signal.severity_hint,
                source_signal_ids=[signal.signal_id],
            )
        )

    return violations
```

**Reguła architektoniczna:**
- dział może emitować sygnały zachowania (`BehaviorSignal`),
- Auditor interpretuje te sygnały i wydaje oficjalne violations,
- verdict `BLOCKED` może być oparty wyłącznie na `BehaviorViolation`, nie na surowym sygnale.

**Acceptance Criteria:**
- Auditor potrafi zweryfikować co najmniej 1 guarantee dla każdego działu,
- verdict `BLOCKED` może być oparty na violation kontraktu zachowania,
- istnieją testy dla positive path, signal path i violation path,
- co najmniej jeden test pokazuje sytuację, w której dział self-reports problem jako `BehaviorSignal`, ale dopiero Auditor zamienia to na `BehaviorViolation`.

## NOWA SEKCJA — Kanoniczny model kosztu

### Dlaczego to jest potrzebne

W planie v3 koszt występuje w wielu miejscach:
- `DecisionEvidenceRecord`,
- `OutcomeRecord`,
- `Experiment.budget_limit`,
- `Capability.cost_weight`,
- `RoutingDecision.estimated_cost`,
- `FactorySpec.improvement.experimentBudget`.

Bez wspólnego modelu kosztu te pola pozostają jedynie sygnałami bez pełnej semantyki.

### Definicja kosztu w RAE

W RAE koszt jest **wektorem**, nie jedną liczbą.

#### Składniki surowe:
- tokeny wejściowe,
- tokeny wyjściowe,
- czas ścienny,
- CPU,
- GPU,
- RAM w czasie,
- storage w czasie,
- transfer,
- rzeczywisty koszt API,
- czas operatora / człowieka.

#### Składnik znormalizowany:
- `NCU` — Normalized Cost Unit.

`NCU` służy do:
- routing decision,
- budget enforcement,
- porównania eksperymentów,
- raportowania trendów,
- failure economics.

### TASK-3.1A — Cost telemetry pipeline

Rozszerz Improvement Plane i Fabric o wspólny pipeline kosztu:

```
src/shared/cost/
├── cost_extractor.py
├── cost_normalizer.py
├── budget_checker.py
├── cost_policies.py
└── wasted_cost.py
```

**Zadania:**
1. każdy dział emituje `CostVector`,
2. Control Plane normalizuje koszt przez `CostPolicy`,
3. BudgetChecker potrafi zatrzymać akcję lub rollout po przekroczeniu NCU,
4. Failure mining zapisuje `wasted_cost_ncu`.

**Normatywny interfejs v1:**

```python
from typing import Protocol

from rae_core.models.cost import BudgetEnvelope


class BudgetChecker(Protocol):
    def check(self, ncu: float, envelope: BudgetEnvelope) -> bool: ...
    def record_spend(self, ncu: float, trace_id: str) -> None: ...
    def remaining_daily(self) -> float: ...
```

Każda integracja w TASK-3.1A, TASK-4.1D i rolloutach Improvement Plane musi używać tego samego interfejsu.

### Przykładowa normalizacja

```python
def compute_ncu(vector: CostVector, policy: CostPolicy) -> float:
    total = 0.0
    for field, weight in policy.weights.items():
        total += getattr(vector, field, 0.0) * weight
    return total
```

### TASK-5.1A — Fabric CostAwareRouter musi pracować na `CostVector`, nie na float

Rozszerz router capability-driven tak, by wybór endpointów był **deterministyczny i implementowalny z dostępnych danych telemetrycznych**.

Uwzględniaj wyłącznie pola, które mają jawne źródło danych:
- `estimated_ncu` — liczone przez `compute_ncu(vector, policy)`,
- `risk_class` — z `CapabilityEntry.risk_class`,
- `failure_rate_30d` — z telemetry capability za ostatnie 30 dni; **gdy brak danych historycznych, domyślnie `0.0`**,
- `latency_p50_s` — z telemetry capability za ostatnie 30 dni; **gdy brak danych historycznych, domyślnie `float('inf')`**,
- `policy_compatible` — bool z `contract_validator` i `policy_engine`.

**Normatywna strategia rankingu v1:**
1. odfiltruj kandydatów niezgodnych z policy,
2. odfiltruj kandydatów o ryzyku powyżej `max_risk`,
3. sortuj leksykograficznie po:
   - `risk_rank ASC`,
   - `estimated_ncu ASC`,
   - `failure_rate_30d ASC`,
   - `latency_p50_s ASC`.

Referencyjna implementacja:

```python
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def candidate_sort_key(candidate: dict) -> tuple:
    failure_rate = candidate.get("failure_rate_30d")
    latency_p50 = candidate.get("latency_p50_s")

    return (
        RISK_ORDER[candidate["risk_class"]],
        candidate["estimated_ncu"],
        0.0 if failure_rate is None else failure_rate,
        float("inf") if latency_p50 is None else latency_p50,
    )
```

**Dlaczego tak:**
- brak "magicznych wag",
- brak ukrytego `reliability_score`,
- każdy składnik pochodzi z jawnego źródła,
- fallback dla pustej historii telemetrycznej jest jawnie zdefiniowany,
- agent może to wdrożyć bez zgadywania kalibracji.

**Ewolucja v2:**
Dopiero po zebraniu realnych danych można dodać model ważony lub ranking uczony przez Lab.

**Acceptance Criteria:**
- router nie używa niejawnych wag w v1,
- wszystkie pola rankingowe mają jawne źródło danych,
- istnieją testy pokazujące ranking co najmniej 3 kandydatów,
- dokumentacja explicite zabrania używania anonimowej sumy floatów jako domyślnej heurystyki v1.

## NOWA SEKCJA — Kompatybilność wersji i ewolucja kontraktów

### Zasady

1. `rae-core` jest **źródłem prawdy** dla kontraktów.
2. Zmiana niekompatybilna wymaga **major version bump**.
3. Zmiana kompatybilna może wejść jako **minor**.
4. Aliasy deprecated utrzymuj przez minimum 2 wersje minor.
5. Mesh exchange musi odrzucać paczki z nieobsługiwaną wersją kontraktu.

### TASK-0.1F — `version.py` i rejestr zgodności

Rozszerz `version.py` o:

```python
CONTRACT_VERSION = "1.1.0"
SUPPORTED_SERIES = [(1, 0), (1, 1)]
MESH_MIN_SUPPORTED = "1.0.0"
```

Dodaj helper oparty na `packaging.version`:

```python
from packaging.version import InvalidVersion, Version


def is_contract_compatible(current: str, other: str) -> bool:
    try:
        current_v = Version(current)
        other_v = Version(other)
    except InvalidVersion:
        return False

    if other_v < Version(MESH_MIN_SUPPORTED):
        return False
    if current_v.major != other_v.major:
        return False
    return (other_v.major, other_v.minor) in SUPPORTED_SERIES
```

**Dependency normatywne:**
- użyj `packaging.version`,
- nie implementuj kompatybilności przez `startswith()` ani wildcard string matching.

### TASK-6.1A — Mesh importer/exporter musi weryfikować wersje

Każdy `MeshExchangeEnvelope` powinien zawierać:
- `contract_version`,
- `schema_family`,
- `compatibility_level`.

Importer:
- akceptuje compatible,
- odrzuca incompatible,
- zapisuje reason do evidence trail.

---

## ROZSZERZENIE FAZY 4 — Lab jako silnik samodoskonalenia, nie tylko agregator

Oryginalna Faza 4 dobrze wprowadza submoduły Labu. Należy ją jeszcze doprecyzować tak, by Lab był
rzeczywiście “bocznym torem ewolucji”, a nie tylko analizą.

### TASK-4.1A — Experiment Orchestrator

Dodaj:
- definicję eksperymentu,
- loader datasetów benchmarkowych i historycznych replayów,
- możliwość uruchomień `offline`, `shadow`, `canary`,
- integrację z BudgetChecker.

### TASK-4.1B — Hypothesis Lifecycle

Każda hipoteza przechodzi stany:
- `draft`,
- `approved_for_test`,
- `running`,
- `validated`,
- `rejected`,
- `promoted`,
- `archived`.

Dodaj enum do `improvement.py` i testy przejść stanów.

### TASK-4.1C — Strategy Compiler

Lab musi generować:
- `InsightPack`,
- `FailurePatternPack`,
- `PolicyPatchProposal`,
- `WorkflowImprovementProposal`,
- `ProviderRoutingProposal`.

Te typy **muszą** istnieć jako jawne modele w:
`packages/rae-core/src/rae_core/models/improvement.py`

Minimalna wersja v1:

```python
from __future__ import annotations

from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PolicyPatchProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    source_experiment_id: Optional[str] = None
    target_policy_id: str
    rationale: str
    proposed_patch: dict[str, Any] = Field(default_factory=dict)
    expected_benefit: Optional[str] = None


class WorkflowImprovementProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    source_experiment_id: Optional[str] = None
    workflow_name: str
    rationale: str
    changed_steps: List[str] = Field(default_factory=list)
    expected_benefit: Optional[str] = None


class ProviderRoutingProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    source_experiment_id: Optional[str] = None
    capability_id: str
    current_provider: Optional[str] = None
    proposed_provider: str
    rationale: str
    expected_ncu_delta: Optional[float] = None
```

**Acceptance Criteria:**
- Strategy Compiler zwraca jawnie jeden z powyższych modeli,
- każdy model ma `proposal_id` i `rationale`,
- istnieje co najmniej 1 test serializacji/deserializacji dla każdego modelu.

### TASK-4.1D — Safe Rollout Manager

Dodaj reguły:
- brak promocji do stable lane bez offline evaluation,
- brak canary bez shadow (jeśli polityka tego wymaga),
- brak high-risk promotion bez rollback planu,
- brak promotion po przekroczonym budżecie eksperymentu.

---

## MAPA ZMIAN DO ISTNIEJĄCYCH FAZ ORYGINALNEGO PLANU

### Faza 0 — należy rozszerzyć o:
- `behavior.py`,
- `cost.py`,
- `compatibility.py`,
- aliasy deprecated dla `cost`,
- schema updates dla `FactorySpec`.

### Faza 1 — należy rozszerzyć o:
- `BehaviorRegistry`,
- `CostPolicyLoader`,
- `BudgetChecker`,
- wymóg rejestracji behavioral contracts.

### Faza 2 — należy rozszerzyć o:
- `evaluate_behavioral_contract`,
- `BehaviorViolation` as source for blocking verdict,
- walidację escalation rules.

### Faza 3 — należy rozszerzyć o:
- wspólny pipeline kosztu,
- logiczne stany eksperymentów,
- `wasted_cost_ncu`.

### Faza 4 — należy rozszerzyć o:
- pełny lifecycle hipotez,
- Strategy Compiler,
- Safe Rollout Manager.

### Faza 5 — należy rozszerzyć o:
- `CostAwareRouter` pracujący na `CostVector`,
- ranking z reliability i policy compatibility.

### Faza 6 — należy rozszerzyć o:
- walidację wersji kontraktów,
- import/export compatibility checks.

---

## DODATKOWE ZMIANY PER REPO — SZCZEGÓŁOWA MACIERZ

### `RAE-agentic-memory`

**Zachować:**
- istniejące runtime’y,
- istniejący storage i retrieval,
- istniejące profile środowiskowe.

**Dodać adapterem:**
- `MemoryEvidenceStore`,
- `MemoryCostStore`,
- support dla `BehaviorViolation` i `AuditVerdict`,
- tagowanie rekordów `experiment`, `shadow`, `canary`, `promotion`.

**Przepisać tylko jeśli konieczne:**
- wewnętrzne mapowanie rekordów do nowego `rae-core`, jeśli obecny format okaże się nieprzystający.

### `RAE-Phoenix`

**Zachować:**
- engine planowania,
- recipes,
- analitykę kodu,
- istniejące pipeline’y generacyjne.

**Dodać:**
- startup registration do Control Plane,
- capability expose,
- behavioral contract,
- emission `DecisionEvidenceRecord` i `OutcomeRecord`,
- `CostVector` dla sesji planowania/generacji.

**Nie przepisywać od razu:**
- rdzenia logiki planowania.

### `RAE-Hive`

**Zachować:**
- wykonawcze silniki,
- Playwright / CLI / infra ops.

**Dodać:**
- capability facade,
- behavioral contract,
- resource telemetry,
- standardowe exit semantics,
- artifact refs.

### `RAE-Quality`

**Zachować:**
- istniejące skanery i integracje.

**Dodać:**
- semantic verdict model,
- reproducibility flag,
- behavioral contract,
- mapowanie do `AuditVerdict`/`QualityGate` semantics.

### `RAE-Lab`

**Zachować:**
- agregację eksperymentów,
- analitykę trendów,
- reflective loops.

**Dopisać / częściowo przebudować:**
- Experiment Orchestrator,
- Hypothesis Engine,
- Strategy Compiler,
- Safe Rollout Manager,
- output packs zgodne z `rae-core`.

### `RAE-Suite`

**To repo przebudowuj najmocniej.**
Tu wchodzą:
- Control Plane,
- registries,
- reconcile,
- policy engine,
- budget engine,
- fabric,
- mesh orchestration,
- migration compatibility layer.

---

## NOWE QUALITY GATES (ROZSZERZENIE SEKCJI “Quality Gates per faza”)

Dopisz do tabeli oryginalnych gate’ów nowe pozycje:

| Gate | Narzędzie / mechanizm | Próg |
|---|---|---|
| Behavioral contract validation | testy kontraktów działów | 100% pass dla zdefiniowanych guarantees |
| Cost model validation | snapshot tests `CostVector -> NCU` | stabilne i udokumentowane |
| Compatibility checks | testy wersji kontraktów | brak nieobsługiwanych ścieżek |
| Migration path check | strangler tests / adapter tests | pass |
| Rollback test | dry-run rollback dla nowej fazy | pass |

---

## NOWE OTWARTE PYTANIA DO DOPRECYZOWANIA PRZEZ AGENTY

Utwórz lub rozszerz `OPEN_QUESTION.md` o te pytania:

1. Czy `external_api_currency` ma być zawsze przeliczane do jednej waluty referencyjnej?
2. Czy `operator_minutes` w NCU ma być aktywne tylko w profilach enterprise / factory?
3. Jakie minimalne guarantees są obowiązkowe per dział w wersji 1.0?
4. `[RESOLVED]` `BehaviorViolation` może być emitowane wyłącznie przez Auditora; działy emitują `BehaviorSignal` — patrz `TASK-0.1B` i `TASK-2.1A`.
5. Czy `wasted_cost_ncu` ma być liczone także dla sukcesów ekonomicznie nieopłacalnych?
6. Jak szeroki ma być compatibility window dla `MeshExchangeEnvelope`?

---

## REKOMENDOWANA KOLEJNOŚĆ REALNEJ PRACY (PRAKTYCZNA)

1. **FAZA -1 / Migration Baseline**  
   Inwentaryzacja, compatibility layer skeleton, matryca migracji.

2. **FAZA 0 rozszerzona**  
   `rae-core` + behavior + cost + compatibility.

3. **FAZA 1 rozszerzona**  
   Control Plane + registries + budget basics.

4. **Retrofit tylko dwóch działów pilotażowo:**  
   `Phoenix` i `Quality`  
   — bo na nich najlepiej sprawdzić behavioral contracts i verdict flow.

5. **FAZA 2 rozszerzona**  
   Auditor z behavioral verification.

6. **Retrofit `Hive`**  
   z pełnym `CostVector`.

7. **FAZA 3 i 4 rozszerzone**  
   Improvement Plane + Lab + hypothesis lifecycle.

8. **FAZA 5**  
   CostAwareRouter dopiero wtedy, gdy system ma realne dane kosztowe.

9. **FAZA 6**  
   Mesh dopiero po ustabilizowaniu kontraktów.

To jest ważne: **nie uruchamiaj pełnego Mesh przed stabilizacją `rae-core` i kompatybilności kontraktów**.

---

## KRÓTKA DEFINICJA “UKOŃCZENIA” PLANU

Plan można uznać za wdrożony poprawnie, gdy:

1. wszystkie główne repo mówią językiem `rae-core`,
2. każdy dział ma capability contract i behavioral contract,
3. koszt jest liczony jako `CostVector` i normalizowany do `NCU`,
4. Auditor ocenia zarówno zgodność techniczną, jak i zachowanie działu,
5. Lab prowadzi eksperymenty obok stable lane,
6. rollouty przechodzą przez shadow/canary/promotion/rollback,
7. Mesh wymienia tylko jawnie zatwierdzone packi i waliduje wersje kontraktów.

---

## PODSUMOWANIE ROZSZERZEŃ

Ta wersja planu:

- **zachowuje cały oryginalny dokument bez skracania,**
- dodaje **strategię migracji** dla istniejącego kodu,
- dodaje **behavioral contracts** jako warstwę potrzebną Auditorowi,
- dodaje **kanoniczny model kosztu** z `CostVector` i `NCU`,
- dodaje **politykę kompatybilności kontraktów**,
- doprecyzowuje, które fragmenty faz należy rozszerzyć i jak.

W praktyce oznacza to przejście z:
- dobrego planu architektury docelowej

do:
- **pełnego planu transformacji działającego ekosystemu do v3**.

