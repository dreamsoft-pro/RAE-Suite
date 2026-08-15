"""RAE autonomy contracts.

Canonical Pydantic v2 schemas for the RAE autonomy kernel: risk assessment,
policy/capability enforcement, quality gating, evidence packing, ledgering,
state-machine auditing, and inter-module handoffs.

Contract-wide invariants:
    * ``extra="forbid"`` and ``strict=True`` on every model, including
      outbound response models (no unknown fields, no silent coercion).
      All models share ``CONTRACT_CONFIG`` so internal and outbound schemas
      cannot drift apart in strictness; ``validate_default=True`` guarantees
      defaults satisfy their own declared constraints.
    * Top-level entities use ``id`` as the primary key; foreign keys keep
      their descriptive ``<entity>_id`` names.
    * All timestamps are timezone-aware UTC. This is *enforced* by
      ``UtcDateTime`` (naive or non-UTC datetimes are rejected, never
      silently coerced); use ``utc_now`` for defaults.
    * ``schema_version`` fields follow the ``MAJOR.MINOR`` format
      (see ``SchemaVersion``).
    * Digest fields carry lowercase hex-encoded SHA-256 (see ``Sha256Hex``).
    * Plaintext secrets are never transported; restricted context is
      encrypted end-to-end (see ``RestrictedContextEntry``), and information
      classification is explicit on transport/retrieval envelopes (no
      silent defaults).
    * Response models omit internal/sensitive fields (primary keys, system
      signature tokens, internal hashes, internal FK references,
      orchestration and tracing internals); see the "RESPONSE MODELS"
      section.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any, Dict, Final, FrozenSet, List, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from rae_contracts.maes import ExecutionMode, RedactionStatus, RiskClass


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    """Enforce the contract-wide 'timezone-aware UTC' timestamp invariant."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "timestamp must be timezone-aware; naive datetimes are forbidden"
        )
    if value.utcoffset() != timedelta(0):
        raise ValueError(
            "timestamp must be UTC (zero UTC offset); convert to UTC before "
            "constructing contract objects"
        )
    return value


UtcDateTime = Annotated[
    datetime,
    AfterValidator(_ensure_utc),
    Field(description="Timezone-aware UTC timestamp"),
]

Sha256Hex = Annotated[
    str,
    Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Lowercase hex-encoded SHA-256 digest (64 characters)",
    ),
]

SchemaVersion = Annotated[
    str,
    Field(
        pattern=r"^\d+\.\d+$",
        description="Schema version in 'MAJOR.MINOR' format, e.g. '1.0'",
    ),
]

# Shared model configuration for every contract in this module.
# ``validate_default=True`` ensures defaults (e.g. schema_version="1.0")
# satisfy their own declared constraints.
CONTRACT_CONFIG = ConfigDict(extra="forbid", strict=True, validate_default=True)

# ==========================================
# SYSTEM ENUMS (Typing Hardening)
# ==========================================

class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    QUARANTINE = "QUARANTINE"

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SIMULATED_SUCCESS = "SIMULATED_SUCCESS"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    FAILED_ROLLBACK_REQUIRED = "FAILED_ROLLBACK_REQUIRED"
    FAILED_ESCALATED = "FAILED_ESCALATED"

class QualityStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    QUARANTINE = "QUARANTINE"
    NOT_REQUIRED = "NOT_REQUIRED"

class MemoryWritebackStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BYPASSED = "BYPASSED"
    BLOCKED = "BLOCKED"

class DistanceMetric(str, Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"

class NormalizationMethod(str, Enum):
    L1 = "l1"
    L2 = "l2"
    MAX = "max"
    NONE = "none"

class NetworkPolicy(str, Enum):
    DENY_ALL = "deny_all"
    ALLOW_WHITELISTED = "allow_whitelisted"
    SANDBOX_ONLY = "sandbox_only"

class InformationClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class MemoryLayer(str, Enum):
    SENSORY = "sensory"
    EPISODIC = "episodic"
    WORKING = "working"
    SEMANTIC = "semantic"
    LONG_TERM = "long_term"
    REFLECTIVE = "reflective"

class TaskState(str, Enum):
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    POLICY_CHECKED = "POLICY_CHECKED"
    CAPABILITY_CHECKED = "CAPABILITY_CHECKED"
    PLANNED = "PLANNED"
    DRY_RUN = "DRY_RUN"
    SANDBOX_EXECUTING = "SANDBOX_EXECUTING"
    VERIFYING = "VERIFYING"
    QUALITY_GATE = "QUALITY_GATE"
    EVIDENCE_PACKING = "EVIDENCE_PACKING"
    LEDGER_COMMIT = "LEDGER_COMMIT"
    MEMORY_WRITEBACK = "MEMORY_WRITEBACK"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    FAILED_ROLLBACK_REQUIRED = "FAILED_ROLLBACK_REQUIRED"
    FAILED_ESCALATED = "FAILED_ESCALATED"

# States in which the automated pipeline halts (success, rejection, or
# awaiting a human/compensating decision). Python enums cannot be extended
# via subclassing, so terminal-state semantics are expressed as this
# frozenset rather than as a separate Enum type.
TERMINAL_TASK_STATES: Final[FrozenSet[TaskState]] = frozenset(
    {
        TaskState.COMPLETED,
        TaskState.APPROVED,
        TaskState.REJECTED,
        TaskState.QUARANTINED,
        TaskState.NEEDS_APPROVAL,
        TaskState.FAILED_ROLLBACK_REQUIRED,
        TaskState.FAILED_ESCALATED,
    }
)

class VoteType(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"

# ==========================================
# CONTRACT DATA SCHEMAS (RAE-First: extra="forbid", strict=True)
# ==========================================

class EmbeddingProfile(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique profile identifier")
    provider: str = Field(..., description="API provider, e.g., 'ollama', 'openai'")
    model: str = Field(..., description="Model name, e.g., 'qwen-embed'")
    dimension: int = Field(..., gt=0, description="Vector dimensionality, e.g., 768")
    distance: DistanceMetric = Field(DistanceMetric.COSINE)
    normalization: NormalizationMethod = Field(
        NormalizationMethod.L2, description="Vector normalization method"
    )
    model_hash: Optional[Sha256Hex] = None
    tokenizer_hash: Optional[Sha256Hex] = None
    created_at: UtcDateTime = Field(default_factory=utc_now)
    active: bool = True

class CapabilityContract(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique capability contract identifier")
    allowed_risk_classes: List[RiskClass] = Field(
        default_factory=list,
        description="Risk classes this contract permits; empty means deny all",
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Explicitly allowed tool identifiers; empty means deny all",
    )
    denied_tools: List[str] = Field(
        default_factory=list,
        description="Explicitly denied tool identifiers (deny wins over allow)",
    )
    outbound_network_policy: NetworkPolicy = Field(NetworkPolicy.DENY_ALL)
    secret_access_allowlist: List[str] = Field(
        default_factory=list,
        description="Secret identifiers accessible under this contract",
    )
    max_token_budget: int = Field(..., gt=0)
    max_execution_time_seconds: int = Field(..., gt=0)

class PolicyBundle(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique policy bundle identifier")
    version: str
    bundle_hash: Sha256Hex = Field(
        ..., description="SHA-256 hash of the entire bundle contents"
    )
    valid_from: UtcDateTime
    valid_to: Optional[UtcDateTime] = None
    risk_matrix_version: str
    capability_contract_version: str
    secret_policy_version: str
    quality_gate_profile: str

    @model_validator(mode="after")
    def _check_validity_window(self) -> "PolicyBundle":
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError(
                "valid_to must be strictly after valid_from when set "
                f"(got valid_from={self.valid_from!r}, valid_to={self.valid_to!r})"
            )
        return self

class RiskAssessment(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique risk assessment identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    risk_class: RiskClass
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence of classifier [0.0-1.0]"
    )
    reasons: List[str] = Field(
        ..., min_length=1, description="Logical path audit reasons (non-empty)"
    )
    detected_sensitive_assets: List[str] = Field(
        default_factory=list,
        description="List of matched sensitive files or tables",
    )
    requires_human_review: bool = False
    assessed_at: UtcDateTime = Field(default_factory=utc_now)

class DecisionLedgerEntry(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique ledger entry identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    risk_class: RiskClass
    decision: DecisionType
    execution_mode: ExecutionMode = Field(ExecutionMode.LIVE)
    evidence_pack_hash: Sha256Hex = Field(
        ..., description="SHA-256 hash of the zipped ISO Evidence Pack"
    )
    evidence_pack_uri: str = Field(..., description="Storage URI of the Evidence Pack")
    policy_bundle_hash: Sha256Hex = Field(
        ..., description="Active Policy Bundle hash used for the decision"
    )
    signed_by: str = Field("rae-autonomy-kernel", description="Signature identifier")
    timestamp: UtcDateTime = Field(default_factory=utc_now)

class QualityGateResult(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(
        ...,
        description="Unique quality gate result identifier "
        "(referenced by ApprovalPack.quality_gate_result_id)",
    )
    status: QualityStatus
    existing_tests_passed: bool
    generated_tests_passed: Optional[bool] = None
    coverage_before: Optional[float] = Field(None, ge=0.0, le=100.0)
    coverage_after: Optional[float] = Field(None, ge=0.0, le=100.0)
    mutation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    critical_vulnerabilities: int = Field(0, ge=0)
    high_vulnerabilities: int = Field(0, ge=0)
    architecture_violations: int = Field(0, ge=0)
    test_integrity_passed: bool
    report_uri: Optional[str] = None

    @model_validator(mode="after")
    def _check_generated_tests(self) -> "QualityGateResult":
        if (
            self.status == QualityStatus.NEEDS_REVIEW
            and self.generated_tests_passed is None
        ):
            raise ValueError(
                "generated_tests_passed must be provided when status is "
                "NEEDS_REVIEW (the reviewer requires the generated-test outcome)"
            )
        return self

class EvidencePack(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique evidence pack identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    created_at: UtcDateTime = Field(default_factory=utc_now)
    artifacts: Dict[str, Sha256Hex] = Field(
        default_factory=dict,
        description="Per-artifact SHA-256 digests, e.g. {'sast_report': '9f2c...'}. "
        "Distinct from hash_sha256, which binds the whole packed archive",
    )
    logs_uri: Optional[str] = None
    quality_report_uri: Optional[str] = None
    dry_run_report_uri: Optional[str] = None
    vulnerability_report_uri: Optional[str] = None
    hash_sha256: Sha256Hex = Field(
        ...,
        description="SHA-256 digest of the packed archive; binds the pack to "
        "DecisionLedgerEntry.evidence_pack_hash (not derivable from the "
        "per-artifact digests above)",
    )
    retention_until: UtcDateTime = Field(
        ..., description="Retention deadline; must be after created_at"
    )
    redaction_status: RedactionStatus = RedactionStatus.REDACTED

    @model_validator(mode="after")
    def _check_retention(self) -> "EvidencePack":
        if self.retention_until <= self.created_at:
            raise ValueError(
                "retention_until must be strictly after created_at "
                f"(got created_at={self.created_at!r}, "
                f"retention_until={self.retention_until!r})"
            )
        return self

class ApprovalPack(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique approval pack identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    risk_class: RiskClass
    action_plan: str = Field(..., min_length=1, description="Human-readable action plan")
    expected_impact: str = Field(
        ..., min_length=1, description="Human-readable expected impact analysis"
    )
    dry_run_output_uri: str
    rollback_plan_id: str = Field(..., description="FK to RollbackPlan.id")
    quality_gate_result_id: str = Field(..., description="FK to QualityGateResult.id")
    safer_alternatives: List[str] = Field(default_factory=list)
    created_at: UtcDateTime = Field(default_factory=utc_now)

class RollbackPlan(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique rollback plan identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    risk_class: RiskClass
    strategy: str = Field(
        ..., min_length=1, description="Rollback strategy, e.g. 'snapshot_restore'"
    )
    snapshot_uri: Optional[str] = None
    commands: List[str] = Field(
        default_factory=list, description="List of safe recovery command steps"
    )
    verification_steps: List[str] = Field(
        default_factory=list, description="List of verification assertions"
    )
    estimated_recovery_time_seconds: Optional[int] = Field(None, gt=0)
    tested: bool = False
    created_at: UtcDateTime = Field(default_factory=utc_now)

class StateTransition(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    from_state: TaskState
    to_state: TaskState
    timestamp: UtcDateTime = Field(default_factory=utc_now)
    reason: Optional[str] = None
    actor: str = Field(..., description="Agent or module triggering state change")

class ExecutionReceipt(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique execution receipt identifier")
    goal_id: str = Field(..., description="Parent goal identifier")
    task_id: str = Field(..., description="Task identifier within the goal")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    module: str = Field(..., description="Module name, e.g., 'rae-hive'")
    agent_id: str = Field(..., description="Agent identifier executing the task")
    risk_class: RiskClass
    capability_contract_id: str = Field(..., description="FK to CapabilityContract.id")
    policy_decision: DecisionType
    execution_status: ExecutionStatus
    quality_status: QualityStatus
    execution_mode: ExecutionMode = Field(ExecutionMode.LIVE)
    sandbox_id: Optional[str] = None
    worktree_id: Optional[str] = None
    rollback_plan_id: Optional[str] = Field(
        None, description="FK to RollbackPlan.id, if a rollback plan was prepared"
    )
    evidence_pack_hash: Sha256Hex
    ledger_entry_id: str = Field(..., description="FK to DecisionLedgerEntry.id")
    memory_writeback_status: MemoryWritebackStatus
    final_state: TaskState
    state_transitions: List[StateTransition] = Field(
        default_factory=list,
        description="Ordered state machine audit trail; when non-empty it must "
        "form a continuous chain ending in final_state",
    )
    llm_provider: str
    llm_model: str
    prompt_template_version: str
    tool_versions: Dict[str, str] = Field(
        default_factory=dict, description="E.g. {'pytest': '8.2.0'}"
    )
    started_at: UtcDateTime = Field(..., description="Execution start (UTC)")
    finished_at: UtcDateTime = Field(..., description="Execution finish (UTC)")

    @model_validator(mode="after")
    def _check_consistency(self) -> "ExecutionReceipt":
        if self.finished_at < self.started_at:
            raise ValueError(
                "finished_at must not be earlier than started_at "
                f"(got started_at={self.started_at!r}, "
                f"finished_at={self.finished_at!r})"
            )
        if self.state_transitions:
            for previous, current in zip(
                self.state_transitions, self.state_transitions[1:]
            ):
                if current.from_state != previous.to_state:
                    raise ValueError(
                        "state_transitions must form a continuous chain: "
                        f"expected from_state={previous.to_state.value!r}, "
                        f"got {current.from_state.value!r}"
                    )
            last_state = self.state_transitions[-1].to_state
            if last_state != self.final_state:
                raise ValueError(
                    "final_state must equal the to_state of the last state "
                    f"transition (got final_state={self.final_state.value!r}, "
                    f"last transition to_state={last_state.value!r})"
                )
        return self

class ContextEnvelope(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique context envelope identifier")
    source_type: str = Field(
        "memory", description="Source indicator, e.g. 'memory', 'file', 'user'"
    )
    source_uri: str
    source_hash: Sha256Hex
    trust_score: float = Field(0.5, ge=0.0, le=1.0)
    information_class: InformationClass = Field(
        ...,
        description="Information classification of the retrieved content; "
        "explicit classification is mandatory (no silent default)",
    )
    redaction_status: RedactionStatus = Field(
        RedactionStatus.REDACTED,
        description="Redaction state of retrieved_content; secrets must be "
        "transported exclusively via RestrictedContextEntry, never inline",
    )
    tenant_id: str
    project_id: str
    memory_layer: MemoryLayer = Field(MemoryLayer.WORKING)
    created_at: UtcDateTime = Field(default_factory=utc_now)
    valid_until: UtcDateTime = Field(
        ..., description="Context expiry; must be after created_at"
    )
    token_cost: int = Field(
        0,
        ge=0,
        description="Model tokens consumed by retrieved_content, counted with "
        "the consuming model's tokenizer",
    )
    retrieved_content: str = Field(
        ...,
        max_length=100_000,
        description="Retrieved payload; must be redacted according to "
        "information_class before packing (see redaction_status). Hard "
        "defensive upper bound (~25k tokens) to prevent unbounded/PII-blob "
        "payloads",
    )
    allowed_uses: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_validity_window(self) -> "ContextEnvelope":
        if self.valid_until <= self.created_at:
            raise ValueError(
                "valid_until must be strictly after created_at "
                f"(got created_at={self.created_at!r}, "
                f"valid_until={self.valid_until!r})"
            )
        return self

class WorkflowStep(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique step identifier within the workflow")
    capability: str = Field(..., description="Capability required to execute this step")
    required_risk_class: RiskClass = Field(
        RiskClass.R1,
        description="Minimum risk class required to execute this step",
    )
    timeout_seconds: int = Field(120, gt=0)

class WorkflowDefinition(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique workflow definition identifier")
    name: str
    version: str
    entry_conditions: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkflowStep] = Field(
        ..., min_length=1, description="Ordered workflow steps (at least one)"
    )
    exit_conditions: Dict[str, Any] = Field(default_factory=dict)
    rollback_workflow_id: Optional[str] = Field(
        None, description="FK to a compensating WorkflowDefinition.id, if any"
    )

    @model_validator(mode="after")
    def _check_step_id_uniqueness(self) -> "WorkflowDefinition":
        step_ids = [step.id for step in self.steps]
        duplicates = sorted({sid for sid in step_ids if step_ids.count(sid) > 1})
        if duplicates:
            raise ValueError(
                "WorkflowStep ids must be unique within a workflow "
                f"(duplicates: {duplicates})"
            )
        return self

class RestrictedContextEntry(BaseModel):
    """Single encrypted context item for cross-module handoff.

    Plaintext secrets must never be transported inside a HandoffEnvelope;
    payloads are encrypted and referenced by a KMS key identifier.
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    key: str = Field(
        ..., min_length=1, description="Context key, e.g. 'db_credentials'"
    )
    ciphertext: str = Field(
        ...,
        min_length=1,
        description="Base64-encoded ciphertext of the context payload "
        "(plaintext is forbidden)",
    )
    key_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the KMS key used to encrypt the payload",
    )

class HandoffEnvelope(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique handoff identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    parent_span_id: Optional[str] = None
    source_module: str = Field(..., description="Originating module name")
    target_module: str = Field(..., description="Receiving module name")
    required_capabilities: List[str] = Field(default_factory=list)
    restricted_context_pack: List[RestrictedContextEntry] = Field(
        default_factory=list,
        description="Encrypted context entries; plaintext secrets are forbidden",
    )
    input_artifacts: List[str] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema of the expected output"
    )
    token_budget: int = Field(50_000, gt=0)
    timeout_seconds: int = Field(300, gt=0)
    information_class: InformationClass = Field(
        ...,
        description="Information classification of the handoff payload; must "
        "be classified explicitly (no silent default) for cross-module "
        "transport",
    )
    created_at: UtcDateTime = Field(default_factory=utc_now)

class OutcomeRecord(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique outcome record identifier")
    trace_id: str = Field(..., description="Distributed tracing correlation ID")
    span_id: str = Field(..., description="Span identifier for this outcome")
    parent_span_id: Optional[str] = None
    goal_id: str = Field(..., description="Parent goal identifier")
    task_id: str = Field(..., description="Task identifier within the goal")
    risk_class: RiskClass
    execution_status: ExecutionStatus
    execution_time_seconds: float = Field(..., ge=0.0)
    token_cost: int = Field(
        0,
        ge=0,
        description="Total input+output model tokens consumed by the task, "
        "counted with the executing model's tokenizer",
    )
    outcome_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: UtcDateTime = Field(default_factory=utc_now)

class ConsensusVote(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    agent_id: str = Field(..., description="Voting agent identifier")
    vote: VoteType
    weight: float = Field(1.0, gt=0.0, description="Voting weight; must be positive")
    reasoning: str = Field(
        ..., min_length=1, description="Audit reasoning behind the vote"
    )
    signature: str = Field(
        ...,
        description="Cryptographic signature over the vote payload "
        "(public verification material, not a secret)",
    )
    signature_alg: str = Field(
        "Ed25519",
        description="Algorithm used for `signature`, e.g. 'Ed25519'; required "
        "verification context alongside the signer's public key",
    )

class ConsensusProposal(BaseModel):
    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    id: str = Field(..., description="Unique consensus proposal identifier")
    task_id: str = Field(..., description="Task identifier under vote")
    risk_class: RiskClass
    votes: List[ConsensusVote] = Field(default_factory=list)
    final_decision: Optional[VoteType] = Field(
        None,
        description="Final consensus outcome; ABSTAIN is not a valid final decision",
    )
    created_at: UtcDateTime = Field(default_factory=utc_now)

    @field_validator("final_decision")
    @classmethod
    def _final_decision_not_abstain(
        cls, value: Optional[VoteType]
    ) -> Optional[VoteType]:
        if value is VoteType.ABSTAIN:
            raise ValueError(
                "final_decision must be APPROVE or REJECT; ABSTAIN is only "
                "valid for individual votes"
            )
        return value

# ==========================================
# RESPONSE MODELS (RAE-First: Sensitive Field Redaction)
#
# These models are used exclusively for outbound API responses.
# They intentionally omit internal/sensitive fields such as:
#   - database primary keys (`id`)
#   - system signature tokens (e.g. `signed_by`)
#   - internal ledger/evidence hashes (e.g. `evidence_pack_hash`,
#     `policy_bundle_hash`) and internal FK references (e.g. `ledger_entry_id`)
#   - orchestration internals (sandbox_id, worktree_id, state_transitions,
#     tool_versions), tracing internals (span_id, parent_span_id), and
#     internal metric blobs (outcome_metrics)
# They share CONTRACT_CONFIG with the internal contracts (strict=True,
# extra="forbid", validate_default=True) so outbound payloads cannot be
# silently coerced, and they mirror the internal models' field constraints.
# ==========================================

class RiskAssessmentResponse(BaseModel):
    """Public-facing view of a RiskAssessment.

    Omits the internal primary key (id).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    risk_class: RiskClass
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str] = Field(..., min_length=1)
    detected_sensitive_assets: List[str] = Field(default_factory=list)
    requires_human_review: bool
    assessed_at: UtcDateTime

class DecisionLedgerEntryResponse(BaseModel):
    """Public-facing view of a DecisionLedgerEntry.

    Omits the internal primary key (id), the internal ledger hashes
    (evidence_pack_hash, policy_bundle_hash), and the system signature
    token (signed_by).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    risk_class: RiskClass
    decision: DecisionType
    execution_mode: ExecutionMode
    evidence_pack_uri: str
    timestamp: UtcDateTime

class QualityGateResultResponse(BaseModel):
    """Public-facing view of a QualityGateResult.

    Omits the internal primary key (id) and the internal report storage
    location (report_uri).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    status: QualityStatus
    existing_tests_passed: bool
    generated_tests_passed: Optional[bool] = None
    coverage_before: Optional[float] = Field(None, ge=0.0, le=100.0)
    coverage_after: Optional[float] = Field(None, ge=0.0, le=100.0)
    mutation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    critical_vulnerabilities: int = Field(0, ge=0)
    high_vulnerabilities: int = Field(0, ge=0)
    architecture_violations: int = Field(0, ge=0)
    test_integrity_passed: bool

class EvidencePackResponse(BaseModel):
    """Public-facing view of an EvidencePack.

    Omits the internal primary key (id), internal artifact digests
    (artifacts), and the internal archive digest (hash_sha256).

    Report storage URIs are intentionally retained: they are the product
    of the pack and are required by consumers to fetch the redacted
    reports; disclosure is governed by redaction_status.
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    created_at: UtcDateTime
    logs_uri: Optional[str] = None
    quality_report_uri: Optional[str] = None
    dry_run_report_uri: Optional[str] = None
    vulnerability_report_uri: Optional[str] = None
    retention_until: UtcDateTime
    redaction_status: RedactionStatus

class ApprovalPackResponse(BaseModel):
    """Public-facing view of an ApprovalPack.

    Omits the internal primary key (id) and internal FK references
    (rollback_plan_id, quality_gate_result_id).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    risk_class: RiskClass
    action_plan: str = Field(..., min_length=1)
    expected_impact: str = Field(..., min_length=1)
    dry_run_output_uri: str
    safer_alternatives: List[str] = Field(default_factory=list)
    created_at: UtcDateTime

class RollbackPlanResponse(BaseModel):
    """Public-facing view of a RollbackPlan.

    Omits the internal primary key (id) and the internal snapshot
    storage location (snapshot_uri).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    risk_class: RiskClass
    strategy: str = Field(..., min_length=1)
    verification_steps: List[str] = Field(default_factory=list)
    estimated_recovery_time_seconds: Optional[int] = Field(None, gt=0)
    tested: bool
    created_at: UtcDateTime

class ExecutionReceiptResponse(BaseModel):
    """Public-facing view of an ExecutionReceipt.

    Omits the internal primary key (id), internal FK references
    (capability_contract_id, ledger_entry_id, rollback_plan_id), the
    internal ledger hash (evidence_pack_hash), and orchestration internals
    (sandbox_id, worktree_id, state_transitions, tool_versions).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    goal_id: str
    task_id: str
    trace_id: str
    module: str
    agent_id: str
    risk_class: RiskClass
    policy_decision: DecisionType
    execution_status: ExecutionStatus
    quality_status: QualityStatus
    execution_mode: ExecutionMode
    final_state: TaskState
    memory_writeback_status: MemoryWritebackStatus
    llm_provider: str
    llm_model: str
    prompt_template_version: str
    started_at: UtcDateTime
    finished_at: UtcDateTime

    @model_validator(mode="after")
    def _check_timestamps(self) -> "ExecutionReceiptResponse":
        if self.finished_at < self.started_at:
            raise ValueError(
                "finished_at must not be earlier than started_at "
                f"(got started_at={self.started_at!r}, "
                f"finished_at={self.finished_at!r})"
            )
        return self

class OutcomeRecordResponse(BaseModel):
    """Public-facing view of an OutcomeRecord.

    Omits the internal primary key (id), tracing internals (span_id,
    parent_span_id), and internal metric blobs (outcome_metrics).
    """

    model_config = CONTRACT_CONFIG

    schema_version: SchemaVersion = "1.0"
    trace_id: str
    goal_id: str
    task_id: str
    risk_class: RiskClass
    execution_status: ExecutionStatus
    execution_time_seconds: float = Field(..., ge=0.0)
    token_cost: int = Field(0, ge=0)
    created_at: UtcDateTime
