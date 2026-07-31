# 🗜️ Hard Frames Rollout & Integration Plan: RAE-Suite v3.4+ (Revision 2)

## 0. Document Contract

This document is normative for the rollout and operation of Hard Frames in RAE-Suite
v3.4 and later. Revision 2 adds normative supply-chain integrity (§8), application
security testing (§13), and vulnerability management (§14) requirements.

The target state-machine semantics are defined by `Hard Frames: Architectural Analysis`.
Where this rollout plan is more restrictive during migration, this plan governs until the
restriction is removed by a signed Constitution amendment.

### 0.1 Normative Language

The terms **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are interpreted as binding Quality Tribunal requirements.

### 0.2 Path Invariant

All repository paths, policy references, evidence references, and artifact names exposed
to agents MUST be project-relative.

Absolute host paths:

- MUST NOT appear in agent-visible contracts, prompts, evidence manifests, or memory;
- MAY exist only inside trusted runtime internals;
- MUST be converted to validated project-relative paths before serialization;
- MUST NOT be accepted from model-generated output.

Path validation MUST reject:

- `..` traversal;
- paths escaping through symlinks;
- absolute paths;
- NUL bytes;
- device files, FIFOs, and sockets unless explicitly permitted;
- hard links to files outside the sandbox workspace;
- mount points created by the workload.

The path validator is a mandatory fuzz target under §13.6.

### 0.3 Enforcement Authority

The Quality Tribunal MUST block promotion or deployment when any mandatory gate in this
document fails.

A deviation requires:

1. a signed Constitution amendment;
2. an updated policy version;
3. an updated transition-table digest where state semantics change;
4. regression tests;
5. a migration and rollback plan.

Emergency disablement MAY reduce Hard Frames availability but MUST NOT silently downgrade
a hard-mode run to ordinary or shadow mode.

---

## 1. Purpose, Security Boundary, and Non-Goals

### 1.1 Guarantees

When operating in `hard` mode, RAE-Suite guarantees:

- a versioned and runtime-enforced sequence of legal frame transitions;
- no LLM authority to mutate frame state directly;
- typed and canonical frame input/output envelopes;
- capability resolution before tool availability;
- capability sealing for the lifetime of the run;
- isolated, resource-bounded sandbox execution;
- default-deny network access;
- content-addressed evidence;
- authenticated and tamper-evident transition records;
- idempotent ledger and memory operations;
- fail-closed handling of contract violations;
- deterministic sequence validation in replay mode;
- signature- and provenance-verified sandbox images at admission time;
- a signed and verified policy bundle at runtime startup.

### 1.2 Qualified Cryptographic Guarantee

RAE-Suite provides cryptographic authenticity, integrity, and tamper evidence.

The term “non-repudiation” MUST NOT be used as an absolute or legal guarantee unless the
deployment additionally provides independently audited key custody (§12.2), RFC 3161 or
equivalent trusted timestamping, and an external append-only anchor (§12.3).

### 1.3 Security Boundary

The trusted computing base includes:

- `RAERuntime`;
- the compiled transition table;
- policy and schema loaders;
- the sandbox provisioning broker;
- the egress proxy and network policy controller;
- the signing service;
- the Decision Ledger writer;
- the artifact importer;
- the Memory Writeback adapter;
- Quality Tribunal policy and verification code;
- the build and release pipeline that produces runtime code, images, and signed policy
  bundles (§8.4);
- the artifact registry and its access controls (§8.6);
- the key management service or HSM backing the signing service (§12.2).

LLM output, tool output, sandbox files, logs, downloaded data, A2A messages, third-party
dependencies before verification, and registry content before signature verification are
untrusted.

Docker containers share the host kernel. Docker isolation alone MUST NOT be represented as
a complete security boundary for hostile code. Risk policy MUST select a stronger runtime
such as gVisor or Kata Containers when the configured risk threshold requires it.

The threat model MUST explicitly include a supply-chain attacker capable of publishing
malicious dependency versions, tampering with registry content, and compromising a
non-hermetic build step.

### 1.4 Explicit Non-Guarantees

Hard Frames does not guarantee:

- semantic correctness of model output;
- safety of arbitrary third-party or hostile native code;
- prevention of kernel-runtime vulnerabilities;
- recovery of irreversible external state;
- cross-tenant isolation;
- hardware-backed attestation;
- model-weight provenance;
- real-time performance;
- legal non-repudiation.

Cross-tenant workloads MUST NOT share a Hard Frames deployment until a separate
cross-tenant isolation design is approved.

Although model-weight provenance is not guaranteed, the model identifier, version, and
serving-endpoint identity used in each run MUST be recorded in the run envelope and
evidence manifest to support replay analysis and incident scoping.

### 1.5 External Side-Effect Restriction

The v3.4 sequence contains `DRY_RUN` but no `EXECUTE` or `APPLY` frame.

Therefore, in v3.4:

- sandbox-local writes are provisional;
- network access, when authorized, MUST be read-only at the application-policy level;
- tools MUST NOT perform irreversible external mutations;
- credentials capable of external mutation MUST NOT be injected;
- approved artifacts MAY be returned or staged for a separate trusted workflow, subject to
  the artifact content-scanning requirements of §7.3;
- Hard Frames MUST NOT claim to authorize production deployment or external mutation.

Adding real external execution requires a Constitution amendment and an explicit
`EXECUTE` or `APPLY` frame.

---

## 2. Canonical State Machine

### 2.1 Success Sequence

The only legal success sequence is:

    INTENT
      → RISK_ASSESSMENT
      → CAPABILITY_CONTRACT
      → SANDBOX_PROVISION
      → DRY_RUN
      → QUALITY_GATE
      → EVIDENCE_PACK
      → DECISION_LEDGER
      → MEMORY_WRITEBACK
      → SUCCEEDED

No success frame may be skipped, repeated, entered out of order, or executed concurrently
with another frame for the same run.

### 2.2 Failure Sequence

A failure detected in any non-terminal frame is converted by `RAERuntime` into a typed
`FailureEnvelope` and routed through:

    CURRENT_FRAME
      → ROLLBACK
      → ESCALATION
      → FAILED_ESCALATED

A workload or transition handler MUST NOT directly select `ROLLBACK`, `ESCALATION`, or a
terminal state.

If rollback itself fails, the runtime MUST:

- preserve the original failure;
- append rollback failure details;
- continue to `ESCALATION`;
- mark the run `FAILED_ESCALATED`;
- quarantine any workspace whose cleanup cannot be verified.

### 2.3 Transition-Table Invariants

The compiled transition table MUST satisfy all of the following:

- the success subgraph is one simple, acyclic path;
- every success frame has exactly one success successor;
- every non-terminal operational frame can emit a runtime failure event;
- no transition targets an earlier success frame;
- `SUCCEEDED` and `FAILED_ESCALATED` are the only terminal states;
- terminal states have no outbound transitions;
- transition handlers cannot introduce dynamic edges;
- the table is versioned and content-addressed.

The transition table, schemas, and enforcement policies MUST be distributed as a signed
policy bundle. `RAERuntime` MUST verify the bundle signature and digest at startup and
MUST refuse to start in hard mode with an unverifiable bundle (§8.7).

The transition-table digest MUST be pinned in the run envelope at `INTENT` and MUST remain
unchanged for that run.

### 2.4 State Mutation Authority

Only `RAERuntime` may commit frame-state changes.

A transition handler may return a proposed typed output, but it MUST NOT:

- update the current frame;
- append directly to the Decision Ledger;
- invoke a later-frame handler;
- provision undeclared capabilities;
- mutate the run policy;
- select its successor frame.

State commits MUST use compare-and-swap semantics over:

- run identifier;
- expected current frame;
- transition sequence number;
- transition-table digest;
- policy digest.

A stale or duplicate commit MUST fail closed unless it is an exact idempotent replay.

---

## 3. Transition Ownership

The 1:1 invariant applies to transition handlers, not to supporting services.

| Transition | Authorized Handler | Required Output |
|---|---|---|
| `INTENT → RISK_ASSESSMENT` | Intent Classification Handler | `IntentEnvelope` |
| `RISK_ASSESSMENT → CAPABILITY_CONTRACT` | Risk Assessment Handler | `RiskEnvelope` |
| `CAPABILITY_CONTRACT → SANDBOX_PROVISION` | Capability Resolution Handler | `CapabilityContract` |
| `SANDBOX_PROVISION → DRY_RUN` | Sandbox Provision Handler | `SandboxReceipt` |
| `DRY_RUN → QUALITY_GATE` | Dry-Run Execution Handler | `ExecutionResult` |
| `QUALITY_GATE → EVIDENCE_PACK` | Quality Tribunal Handler | `QualityVerdict` |
| `EVIDENCE_PACK → DECISION_LEDGER` | Evidence Assembly Handler | `EvidenceManifest` |
| `DECISION_LEDGER → MEMORY_WRITEBACK` | Decision Commit Handler | `LedgerReceipt` |
| `MEMORY_WRITEBACK → SUCCEEDED` | Memory Writeback Handler | `MemoryReceipt` |
| `CURRENT_FRAME → ROLLBACK` | Runtime Failure Router | `FailureEnvelope` |
| `ROLLBACK → ESCALATION` | Rollback Handler | `RollbackReceipt` |
| `ESCALATION → FAILED_ESCALATED` | Escalation Handler | `EscalationReceipt` |

Supporting services MAY be shared by handlers but MUST NOT independently mutate frame
state.

`RAERuntime` is the loop driver and state authority; it does not own a normal success
transition.

---

## 4. Typed Contracts and Canonicalization

### 4.1 Envelope Requirements

Every frame input and output MUST include:

- `run_id`;
- `transition_id`;
- `sequence_number`;
- source and target frames;
- schema version;
- transition-table digest;
- policy digest;
- capability-contract digest where available;
- sandbox image digest where applicable;
- model identity where applicable (§1.4);
- monotonic runtime timestamp;
- wall-clock timestamp for audit only;
- content digest;
- parent transition digest;
- idempotency key.

Unknown fields MUST be rejected in hard mode.

### 4.2 Serialization

Cryptographic digests and signatures MUST operate on one documented canonical
serialization format.

Canonicalization MUST define:

- field ordering;
- Unicode normalization;
- integer representation;
- timestamp representation;
- absent versus null fields;
- binary encoding;
- map ordering;
- duplicate-key rejection.

Pretty-printed JSON, raw logs, filesystem ordering, and Python object representations MUST
NOT be used as signature inputs.

The canonical serializer and deserializer are mandatory fuzz targets under §13.6.

### 4.3 Schema Evolution

Schemas MUST use explicit versions.

A hard-mode run MUST NOT switch schema versions after `INTENT`. Backward-compatible readers
MAY be added, but replay MUST verify the original schema version and digest.

---

## 5. Execution Modes and Enforcement Resolution

### 5.1 Modes

| Mode | Frame Validation | Side Effects | Evidence | Violation Behavior |
|---|---|---|---|---|
| `ordinary` | Advisory | Existing local policy | Journaled | Warn and audit |
| `shadow` | Full parallel validation | Existing local policy; no authority from shadow result | Journaled and diffed | Record violation, do not halt legacy path |
| `hard` | Mandatory | Sandbox-provisional only | Signed and sealed | Fail closed |
| `replay` | Recorded sequence only | None | Verified, no normal writes | Fail on mismatch |

`shadow` validates what Hard Frames would permit. It does not “enforce non-blockingly,” and
its result MUST NOT grant capabilities or authorize execution.

### 5.2 Enforcement Levels

Per-frame enforcement levels are:

1. `OFF`
2. `AUDIT`
3. `SHADOW`
4. `ENFORCE`

Resolution MUST be deterministic:

    effective_level =
        max(global_minimum, frame_policy_level, risk_override_level)

The maximum is taken using the ordering above.

Additional rules:

- `hard` sets `global_minimum = ENFORCE`;
- `shadow` sets `global_minimum = SHADOW`;
- `ordinary` sets `global_minimum = AUDIT`;
- `replay` uses a separate verification-only policy;
- no frame-level configuration may weaken the global minimum;
- risk overrides may only increase enforcement;
- any invalid or missing policy resolves to `ENFORCE` in hard mode.

---

## 6. Capability Contract

### 6.1 Contract Contents

The `CapabilityContract` MUST enumerate:

- allowed tool identifiers and versions;
- allowed executable digests;
- permitted project-relative path prefixes;
- read, write, create, and delete permissions;
- network policy;
- environment-variable allowlist;
- secret references, if any;
- maximum runtime;
- resource profile;
- sandbox runtime class;
- artifact-output limits;
- log-output limits;
- allowed subprocess behavior;
- syscall-profile identifier;
- image digest;
- policy expiration.

Capabilities MUST be deny-by-default and specific. Wildcard tool, path, host, port, or
environment access is forbidden in hard mode.

### 6.2 Sealing

The contract MUST be content-addressed and sealed before sandbox provisioning.

After sealing:

- it MUST NOT be expanded;
- a requested additional capability MUST terminate the run;
- reduction is permitted only by creating a derived, more restrictive contract with a new
  digest and an auditable runtime event;
- the sandbox MUST receive only the effective reduced contract.

### 6.3 Secret Handling

Hard mode SHOULD operate without secrets.

Where read-only credentials are unavoidable:

- credentials MUST be short-lived;
- scope MUST match the contract;
- credentials MUST be delivered through a dedicated secret mechanism, not image layers,
  command-line arguments, or normal environment logging;
- secret values MUST never enter evidence packs;
- signing keys MUST never enter the sandbox;
- credentials capable of external mutation are forbidden in v3.4.

---

## 7. Sandbox Isolation Baseline

### 7.1 Runtime Classes

Risk policy MUST select one of:

- `container-standard`: rootless or user-namespace-remapped OCI container;
- `container-hardened`: OCI container using gVisor or an approved equivalent;
- `microvm`: Kata Containers or an approved microVM runtime;
- `deny`: execution prohibited.

Unknown or unsupported runtime classes MUST resolve to `deny`.

High-risk native binaries, untrusted package installation, or parser fuzzing MUST NOT use
`container-standard`.

### 7.2 Mandatory Container Controls

Every hard-mode sandbox MUST have:

- a unique run identity;
- a fresh container or microVM;
- no container reuse across runs;
- a read-only root filesystem;
- a bounded writable workspace;
- a bounded `/tmp`, preferably `tmpfs`;
- an empty or minimal `/dev`;
- no privileged mode;
- no host PID namespace;
- no host IPC namespace;
- no host UTS namespace;
- no host network namespace;
- no host user namespace unless explicitly approved for the runtime;
- no host devices;
- no Docker, containerd, CRI, or BuildKit socket;
- no host SSH agent socket;
- no arbitrary Unix-domain socket mounts;
- all Linux capabilities dropped by default;
- `no-new-privileges`;
- an approved seccomp profile;
- an approved AppArmor or SELinux profile where supported;
- masked and read-only sensitive kernel filesystems;
- private or slave mount propagation;
- core dumps disabled;
- a non-root workload user;
- immutable image selection by digest with admission-time signature and provenance
  verification (§8.3).

The workload user MUST NOT map to host root. Root inside a user namespace MUST still be
treated as privileged within that namespace and minimized.

### 7.3 Filesystem Layout and Artifact Import

The sandbox SHOULD expose only:

- a read-only source snapshot;
- a writable bounded work directory;
- a bounded temporary directory;
- a write-only or runtime-mediated result channel.

The host project worktree MUST NOT be bind-mounted writable in hard mode.

Artifact import MUST be performed by trusted runtime code after container termination.
The importer MUST reject:

- absolute paths;
- escaping symlinks;
- hard-link escapes;
- device nodes;
- sockets;
- FIFOs unless explicitly allowed;
- setuid or setgid bits;
- unexpected executable files;
- files exceeding contract limits;
- archives with traversal or decompression-bomb behavior.

In addition to structural checks, imported artifacts MUST pass content scanning before
being returned or staged for any trusted workflow:

- malware scanning with an approved, regularly updated engine;
- secret scanning for credentials, tokens, and private keys;
- format-policy enforcement (only artifact types declared in the capability contract);
- a recorded scan verdict in the evidence manifest.

A failed content scan MUST quarantine the artifact and route the run into the failure
sequence. The importer, including its archive-extraction path, is a mandatory fuzz target
under §13.6.

### 7.4 Image Supply Chain (Summary)

Sandbox images MUST comply with the full supply-chain requirements of §8. In summary,
they MUST:

- be referenced by immutable digest;
- be built through an approved hermetic, isolated builder (§8.4);
- have a signed SBOM in an approved format (§8.2);
- pass vulnerability, license, and malware policy (§8, §14);
- have signed provenance attestations (§8.4);
- be signed by an approved image authority and verified at admission (§8.3);
- avoid compilers, shells, and package managers unless required by the profile;
- define a non-root user;
- contain no embedded credentials.

Mutable tags MAY be used for development discovery but MUST resolve to a pinned digest
before a hard-mode run begins.

### 7.5 Docker Daemon Isolation

The trusted runtime MUST NOT grant agents or sandbox workloads access to the Docker API.

If Docker is used:

- rootless Docker is preferred where compatible;
- otherwise user-namespace remapping MUST be enabled;
- the daemon MUST be dedicated to the RAE-Suite security domain;
- authorization plugins or an equivalent broker SHOULD restrict runtime operations;
- the daemon socket MUST be accessible only to the trusted provisioning broker;
- workload containers MUST NOT create sibling containers;
- host bind mounts MUST be allowlisted by trusted configuration.

A compromised Docker daemon is considered a trusted-computing-base compromise and MUST
trigger deployment quarantine.

---

## 8. Supply Chain Integrity

### 8.1 Scope

Supply-chain requirements apply to all of the following artifact classes:

- sandbox images and their base images;
- the trusted runtime code and its third-party dependencies;
- signed policy bundles (transition table, schemas, seccomp, LSM, network, and resource
  policies);
- tool binaries exposed inside sandboxes;
- Quality Tribunal verification code;
- build tooling used to produce any of the above.

### 8.2 SBOM

Every artifact class in §8.1 MUST have a Software Bill of Materials that is:

- generated at build time by the trusted builder, not post hoc;
- in CycloneDX or SPDX format, one format chosen deployment-wide;
- complete to the resolved-dependency level, including transitive dependencies;
- content-addressed and signed by the build identity;
- stored alongside the artifact and retrievable by digest;
- referenced by digest from the evidence manifest of every hard-mode run that uses the
  artifact.

SBOMs are inputs to continuous vulnerability re-scanning (§14.1) and license policy
enforcement (§8.5).

### 8.3 Signing and Admission Verification

Artifact signing MUST use Cosign (Sigstore) or an approved equivalent.

Requirements:

- signing identities MUST be backed by a KMS or HSM (keyed mode), or use short-lived
  certificate-based identities (keyless mode) only if the deployment's identity provider
  and certificate authority are within the approved trust policy;
- every signature MUST be recorded in a transparency log (Rekor or an approved private
  transparency log);
- signature verification MUST occur at admission time: the sandbox provisioning broker
  MUST verify, before launch, the image signature, digest, provenance attestation, and
  SBOM presence against the deployment trust policy, and MUST fail closed on any
  verification failure;
- verification results, including the verified signer identity and transparency-log
  entry reference, MUST be recorded in the `SandboxReceipt` and evidence manifest;
- registry-side or cluster-side admission controllers MAY provide additional enforcement
  but MUST NOT replace broker-side verification.

Trust policy (allowed signers, allowed identities, allowed transparency logs) MUST itself
be part of the signed policy bundle (§8.7).

### 8.4 Build Provenance

Builds of all §8.1 artifacts MUST:

- run in isolated, ephemeral build environments dedicated to the RAE-Suite security
  domain;
- be hermetic to the extent supported: pinned inputs, no unpinned network fetches during
  build, and recorded resolved inputs otherwise;
- produce signed in-toto/SLSA provenance attestations recording source revision, builder
  identity, build parameters, and materials;
- meet SLSA Build Level 2 at minimum before Phase 8 (hard-mode canary), with SLSA Build
  Level 3 as the target before Phase 10 (hard mode default);
- require two-person review for changes to trusted runtime code, policy bundles, and
  build definitions;
- deny build-time access to production signing keys other than through the signing
  service's build-signing endpoint.

The build pipeline is part of the trusted computing base (§1.3). Compromise of the build
pipeline MUST be treated as a TCB compromise and trigger deployment quarantine (§21).

### 8.5 Dependency Hygiene

For trusted runtime code and images:

- all dependencies MUST be pinned by version and cryptographic hash (for Python:
  hash-checked lockfiles enforced at install time);
- dynamic dependency installation at runtime is forbidden in the TCB;
- new or upgraded dependencies MUST pass SCA scanning (§13.2), license policy, and
  review before merge;
- license policy MUST define permitted, restricted, and forbidden licenses; violations
  block the Tribunal gate;
- dependency-confusion protections MUST be in place: internal package namespaces MUST be
  reserved or resolved only from the internal registry.

### 8.6 Registry Security

The artifact registry MUST:

- be private and require authenticated, least-privilege access;
- enforce immutability of pushed digests;
- restrict write access to the trusted build pipeline identity;
- log all pushes and permission changes to the audit stream;
- be mirrored, if at all, only through integrity-verified pull-through caches.

Registry compromise MUST be handled as a TCB incident: affected digests MUST be
re-verified against transparency-log entries before further use.

### 8.7 Signed Policy Bundles

The transition table, schemas, enforcement policies, seccomp/LSM profiles, network
policies, resource profiles, and supply-chain trust policy MUST be packaged as a
content-addressed, signed policy bundle.

`RAERuntime` MUST at startup:

- verify the bundle signature against a pinned trust root;
- verify the bundle digest;
- refuse hard-mode operation on any verification failure;
- record the verified bundle digest in every run envelope.

Policy bundle updates follow §0.3 and MUST NOT be hot-applied to in-progress runs (§21.1).

### 8.8 VEX and Finding Disposition

Vulnerability findings against pinned artifacts that are assessed as not exploitable MUST
be documented as signed VEX (Vulnerability Exploitability eXchange) statements including
justification and reviewer identity. Unsigned or expired VEX statements MUST NOT suppress
gate failures. VEX statements MUST be re-reviewed when the affected component or its usage
changes.

---

## 9. Linux Namespace and Kernel Controls

### 9.1 Namespace Requirements

Each hard-mode sandbox MUST receive isolated:

- mount namespace;
- PID namespace;
- IPC namespace;
- UTS namespace;
- network namespace;
- cgroup membership;
- user namespace where supported by the selected runtime.

The runtime MUST verify effective namespace identifiers after launch rather than trusting
only requested configuration.

### 9.2 Seccomp

The default seccomp policy MUST deny at least:

- kernel module operations;
- raw I/O;
- unrestricted `ptrace`;
- `kexec`;
- mount and namespace creation not required by the workload;
- BPF operations not explicitly required;
- keyring operations not explicitly required;
- reboot and clock modification;
- privileged performance-monitoring access;
- creation of raw packet sockets.

Seccomp policy exceptions require:

- a named profile;
- a documented workload need;
- a risk review;
- tests proving the exception is restricted.

### 9.3 Kernel Hardening Preconditions

Production hard-mode nodes MUST document and verify:

- supported cgroups v2;
- supported LSM configuration;
- user-namespace policy;
- unprivileged BPF policy;
- protected symlink and hard-link settings;
- restricted kernel log access;
- current kernel security patch status against the patch cadence defined in §14.4;
- compatible overlay or snapshotter configuration.

Nodes that do not meet the selected runtime profile, or whose kernel patch status exceeds
the remediation SLA of §14.4, MUST reject provisioning.

---

## 10. Network Sandboxing

### 10.1 Default Policy

Hard-mode sandboxes MUST start with no network access.

For Docker, `network=none` or an equivalent isolated network namespace SHOULD be used when
the contract grants no egress.

The sandbox MUST NOT access:

- the host network;
- peer sandboxes;
- container control-plane sockets;
- cloud metadata services;
- link-local management endpoints;
- cluster control planes;
- internal services not explicitly listed.

### 10.2 Authorized Egress

When read-only egress is approved, traffic MUST pass through a host-controlled egress
gateway or proxy.

The policy MUST specify:

- protocol;
- destination hostname or CIDR;
- destination port;
- DNS policy;
- request method restrictions where applicable;
- byte and connection limits;
- expiration time.

Direct unrestricted internet access is forbidden.

TLS handling MUST be explicit:

- plaintext protocols to external destinations are forbidden unless a named policy
  exception exists;
- the gateway MUST enforce the destination allowlist at the connection level using
  verified SNI/hostname matching, or perform policy-approved TLS inspection with a
  deployment-scoped CA that never enters the sandbox;
- direct-to-IP TLS connections that bypass hostname policy MUST be blocked;
- certificate validation MUST NOT be disabled at the gateway;
- where TLS inspection is used, inspected content is untrusted evidence and subject to
  redaction (§12.5).

Network enforcement MUST cover both IPv4 and IPv6. Disabling only one address family is
insufficient.

### 10.3 DNS

Sandbox DNS MUST be mediated by an approved resolver.

The resolver or gateway MUST:

- enforce hostname allowlists;
- prevent rebinding to prohibited addresses;
- block metadata and link-local ranges;
- record bounded DNS evidence;
- apply response and query-size limits;
- prevent use of alternate DNS servers, including DNS-over-HTTPS and DNS-over-TLS to
  non-approved resolvers.

The DNS and egress policy evaluators are mandatory fuzz targets under §13.6.

### 10.4 A2A Bridge

The A2A Bridge MUST be external to workload containers.

Sandboxes MAY communicate with the bridge only through a capability-bound authenticated
relay. They MUST NOT receive:

- direct peer-container addresses;
- host IPC access;
- a shared writable socket;
- unrestricted message routing.

A2A messages MUST include run identity, sender identity, destination capability, sequence
number, size limit, and content digest.

The A2A relay is in scope for DAST under §13.5.

---

## 11. Resource Limits and Denial-of-Service Controls

### 11.1 cgroups v2

Hard-mode nodes MUST use cgroups v2 or an approved equivalent.

Each sandbox MUST have explicit limits for:

- memory;
- swap;
- CPU quota and period;
- process count;
- I/O bandwidth or weight where supported;
- wall-clock duration.

Defaults MUST be deny-by-exhaustion rather than inherited as unlimited.

### 11.2 Required Limits

Each resource profile MUST define at least:

- `memory.max`;
- `memory.high` where supported;
- swap policy;
- CPU quota;
- `pids.max`;
- open-file limit;
- maximum file size;
- maximum log bytes;
- maximum artifact bytes;
- maximum number of artifacts;
- maximum workspace bytes;
- maximum temporary-space bytes;
- maximum execution time;
- termination grace period.

Core-dump size MUST be zero unless a separately approved diagnostic profile is active.

### 11.3 Timeout and Termination

Timeout enforcement MUST occur outside the sandbox.

On timeout or cancellation, the runtime MUST:

1. revoke network access;
2. send the configured graceful termination signal;
3. wait only for the bounded grace period;
4. kill all processes in the sandbox cgroup;
5. verify that no descendant process remains;
6. collect bounded termination evidence;
7. destroy or quarantine the sandbox.

Killing only the initial process is insufficient.

### 11.4 OOM and Resource Evidence

The runtime MUST distinguish:

- workload exit;
- policy kill;
- timeout;
- OOM kill;
- PID exhaustion;
- storage exhaustion;
- infrastructure failure.

Resource counters and termination reasons MUST be included in the evidence manifest.

---

## 12. Evidence, Signing, and Decision Ledger

### 12.1 Evidence Pack

The evidence pack MUST include content-addressed references to:

- frame envelopes;
- transition-table digest;
- policy bundle digest and verification result;
- capability contract;
- sandbox runtime class;
- image digest, verified signer identity, and transparency-log reference (§8.3);
- SBOM digests of used artifacts (§8.2);
- model identity (§1.4);
- effective container configuration;
- namespace and cgroup verification;
- network policy;
- bounded stdout and stderr;
- execution exit reason;
- resource usage;
- Quality Tribunal verdict;
- imported artifact manifest, including content-scan verdicts (§7.3);
- redaction report;
- parent transition digest.

Logs and artifacts are untrusted evidence and MUST be size-bounded.

### 12.2 Signing Boundary and Key Management

Sandbox workloads MUST NOT possess signing keys.

The trusted signing service MUST sign only after independently verifying:

- run identity;
- transition sequence;
- policy digest;
- content digest;
- caller workload identity;
- authorization for the requested signature type.

Per-run or per-transition derived signing identities MAY be used, but private key material
MUST remain outside the workload sandbox.

Key management requirements:

- root and intermediate signing keys MUST reside in a KMS or HSM and MUST NOT be
  exportable in plaintext;
- signature algorithms MUST be explicitly versioned in the policy bundle, and the
  deployment MUST support algorithm rotation without invalidating verification of
  historical records;
- routine key rotation MUST occur on a documented schedule, and rotation MUST be
  exercised (not merely documented) before Phase 10;
- key usage MUST be logged and attributable to a service identity;
- deployments claiming timestamped evidence MUST use RFC 3161 or an equivalent trusted
  timestamping source for ledger anchoring.

### 12.3 Decision Ledger

The Decision Ledger MUST provide:

- append-only logical semantics;
- monotonic sequence numbers per run;
- canonical signed entries;
- parent-digest chaining;
- idempotent append keys;
- concurrent-write protection;
- durable commit receipts;
- periodic chain-head anchoring outside the primary ledger store (an external
  transparency log, write-once storage, or an approved equivalent).

A Merkle or hash chain without external anchoring MUST be described only as tamper-evident,
not deletion-proof.

### 12.4 Failure Records

Failures MUST produce signed failure records even when the success path never reaches
`EVIDENCE_PACK`.

The runtime failure journal is distinct from the success-path Decision Ledger transition.
On escalation, the final failure envelope and available evidence MUST be committed to the
failure ledger using an idempotent trusted-runtime operation.

### 12.5 Redaction

Evidence creation MUST apply deterministic redaction before persistence.

The redaction process MUST:

- remove known secrets and tokens;
- limit environment capture to an allowlist;
- avoid raw memory dumps;
- retain a redaction manifest;
- fail closed if mandatory redaction cannot complete.

The redaction engine is a mandatory fuzz target under §13.6.

---

## 13. Application Security Testing (SAST, SCA, DAST, Fuzzing)

### 13.1 Static Analysis (SAST)

All trusted-computing-base code (§1.3) MUST pass SAST on every merge to a release branch.

Requirements:

- an approved SAST toolchain with rulesets covering injection, path handling, unsafe
  deserialization, command execution, cryptographic misuse, race conditions, and
  insecure temporary-file usage;
- Critical and High findings block the Tribunal gate unless dispositioned with a signed,
  time-boxed waiver;
- dynamic code evaluation (`eval`, `exec`, dynamic imports of untrusted paths, pickle of
  untrusted data) is forbidden in the TCB and MUST be enforced by lint rules;
- SAST configuration is part of the signed policy bundle domain and requires review to
  change.

### 13.2 Software Composition Analysis (SCA)

- All TCB dependencies MUST be scanned against vulnerability databases on every merge and
  on the continuous cadence of §14.1;
- findings are gated by the severity thresholds and SLAs of §14.2;
- SCA operates on the SBOMs of §8.2 to ensure scan and deployment inventories match.

### 13.3 Secret Scanning

Secret scanning MUST run on:

- the repository, including history, on every merge;
- built images and policy bundles before signing;
- imported sandbox artifacts (§7.3);
- evidence packs as part of redaction verification.

A confirmed committed secret MUST trigger credential revocation before remediation is
considered complete.

### 13.4 Infrastructure and Policy Scanning

- Dockerfiles, container build definitions, orchestration manifests, and node
  configuration MUST pass IaC scanning against the controls of §7 and §9;
- seccomp, LSM, network, and resource policies MUST pass automated linting that verifies
  they are syntactically valid, deny-by-default, and free of wildcard grants forbidden
  by §6.1.

### 13.5 Dynamic Analysis (DAST)

The following network-exposed trusted services MUST undergo DAST in a staging environment
before each phase promotion from Phase 7 onward, and on a recurring schedule thereafter:

- the egress proxy and its administrative plane;
- the A2A relay;
- the signing service API;
- the Decision Ledger writer API;
- any Tribunal or replay verification endpoints.

DAST MUST include authenticated and unauthenticated scans, API fuzzing of exposed
endpoints against their schemas, authorization-bypass testing between run identities, and
TLS configuration testing. Critical and High findings block promotion.

### 13.6 Fuzzing

Coverage-guided fuzzing is REQUIRED for the following TCB parsers of untrusted input:

- the canonical serializer and deserializer (§4.2);
- envelope and schema validators;
- the path validator (§0.2);
- the artifact importer, including archive extraction (§7.3);
- the DNS and egress policy evaluators (§10.3);
- the redaction engine (§12.5);
- A2A message parsing.

Requirements:

- fuzz harnesses and seed corpora live in the repository (§22);
- a bounded fuzz budget runs in CI on every merge; extended continuous fuzzing runs on a
  scheduled basis;
- crashes and hangs are triaged within the SLAs of §14.2, with reproducers converted to
  regression tests;
- fuzzing of the importer and archive paths MUST execute in a `container-hardened` or
  stronger environment (§7.1).

### 13.7 Penetration Testing and External Audit

- An internal penetration test against the full stack (state machine, sandbox escape,
  network bypass, ledger forgery, supply-chain injection) MUST be completed before
  Phase 8 (hard-mode canary);
- an independent external security audit covering the TCB, supply chain, and isolation
  baseline MUST be completed, and its Critical/High findings remediated or formally
  risk-accepted by signed Tribunal record, before Phase 10 (hard mode as default);
- audit scopes and summary results (redacted as needed) MUST be referenced from the
  promotion record.

---

## 14. Vulnerability Management

### 14.1 Continuous Re-Scanning

Digest pinning is a point-in-time guarantee; it MUST be paired with continuous
re-assessment:

- all pinned image digests in active use MUST be re-scanned against current vulnerability
  data at least daily, using their SBOMs (§8.2);
- TCB runtime dependencies MUST be re-scanned on the same cadence;
- node kernel and container-runtime versions MUST be checked against advisories
  continuously;
- new findings against in-use digests MUST open tracked remediation items automatically.

### 14.2 Severity Thresholds and SLAs

The deployment MUST define severity thresholds and remediation SLAs. Defaults, which MAY
only be tightened without amendment:

| Severity | Gate Behavior | Remediation SLA (rebuild/redeploy) |
|---|---|---|
| Critical | Block build, promotion, and new hard-mode admission for affected profiles | 48 hours |
| High | Block build and promotion | 7 days |
| Medium | Warn; tracked | 30 days |
| Low | Tracked | Next scheduled rebuild |

Suppression of Critical/High findings is permitted only through signed VEX statements
(§8.8) or signed, time-boxed waivers.

### 14.3 Rebuild Cadence

Independent of findings, sandbox base images and TCB images MUST be rebuilt, re-scanned,
re-signed, and re-pinned on a documented schedule (at most monthly). Stale digests beyond
the schedule MUST fail the Tribunal build gate.

### 14.4 Kernel and Runtime Patching

- hard-mode nodes MUST apply kernel and container-runtime security patches within the
  SLAs of §14.2 based on advisory severity;
- nodes outside SLA MUST reject new hard-mode provisioning (§9.3);
- container-runtime and isolation-layer (gVisor, Kata) versions in use MUST be inventoried
  and covered by advisory monitoring.

### 14.5 Emergency Rebuild Path

An emergency rebuild-and-repin path MUST exist and be exercised before Phase 10:

- new digests are produced through the standard trusted pipeline (§8.4) — emergency does
  not bypass signing, SBOM, or provenance;
- in-progress runs remain pinned to their original digests or fail closed; digests are
  never hot-swapped within a run (§21.1);
- new hard-mode admissions switch to remediated digests atomically via policy bundle
  update (§8.7).

---

## 15. Quality Tribunal Gates

### 15.1 Build-Time Gates

The Quality Tribunal MUST verify:

- transition graph invariants;
- exactly one authorized handler per legal transition;
- no undeclared transition decorators;
- schemas reject unknown fields;
- canonicalization test vectors;
- policy and transition-table digests;
- signed policy bundle validity (§8.7);
- image digest pinning;
- image signature, provenance attestation, and SBOM presence and validity (§8.2–§8.4);
- dependency lockfile hash-pinning and SCA pass (§8.5, §13.2);
- license policy compliance (§8.5);
- SAST pass on TCB code (§13.1);
- secret-scanning pass (§13.3);
- IaC and policy-lint pass (§13.4);
- fuzz-harness presence and CI fuzz budget execution for all §13.6 targets;
- vulnerability findings within §14.2 thresholds, with valid VEX/waivers only;
- rebuild-cadence freshness of pinned digests (§14.3);
- seccomp and LSM profiles;
- default-deny network policy;
- cgroups v2 resource profiles;
- no privileged containers;
- no Docker socket mounts;
- no host namespace sharing;
- no writable host-worktree mount;
- no signing keys in images or sandbox configuration;
- project-relative path compliance.

### 15.2 Runtime Gates

Before entering `DRY_RUN`, the runtime MUST verify actual, not merely requested:

- image digest, signature, and provenance verification result (§8.3);
- runtime class;
- workload UID/GID mapping;
- read-only root;
- mount list and propagation;
- namespace isolation;
- dropped capabilities;
- `no-new-privileges`;
- seccomp profile;
- LSM profile where required;
- cgroup placement and limits;
- network policy;
- absence of prohibited sockets and devices.

A mismatch MUST destroy the sandbox and enter the failure sequence.

### 15.3 Adversarial Tests

The test suite MUST include attempts to:

- skip or repeat a frame;
- commit with a stale sequence number;
- mutate a sealed capability;
- invoke an undeclared tool;
- escape through symlinks or archives;
- mount or access the Docker socket;
- reach the host or metadata service;
- bypass DNS policy, including via DNS-over-HTTPS to non-approved resolvers;
- bypass the hostname allowlist via direct-IP TLS or domain fronting;
- use IPv6 when only IPv4 policy is configured;
- fork-bomb the sandbox;
- exhaust memory or disk;
- leave descendant processes after timeout;
- generate unbounded logs;
- smuggle secrets into evidence;
- smuggle malware or credentials through imported artifacts;
- forge or reorder ledger entries;
- replay against live tools;
- import device nodes or setuid artifacts;
- launch an unsigned image, an image with invalid provenance, or an image whose signer is
  outside trust policy;
- start the runtime with a tampered or unsigned policy bundle;
- resolve a mutable tag at run time instead of a pinned digest.

---

## 16. Replay Mode

Replay mode MUST:

- perform no tool execution;
- provision no network-enabled sandbox;
- resolve no live DNS;
- fetch no mutable external content;
- write no normal episodic or semantic memory;
- verify schemas, signatures, digests, ordering, and parent links;
- verify the recorded policy bundle and transition-table versions;
- verify image digests and recorded supply-chain verification results without launching
  the image;
- report the first mismatch and all safely detectable subsequent mismatches.

Replay output MUST be stored separately from the original run and MUST NOT alter the
original chain.

A diagnostic container MAY be used only if it has no network, receives read-only evidence,
and cannot write to normal memory or ledger stores.

---

## 17. Crash Consistency and Recovery

### 17.1 Run State

Persistent run state MUST include:

- current committed frame;
- expected sequence number;
- transition-table digest;
- policy digest;
- last committed transition digest;
- sandbox identifier, if active;
- ledger commit status;
- memory-writeback status.

### 17.2 Recovery Rules

After runtime restart:

- the policy bundle MUST be re-verified (§8.7) before resuming any hard-mode run;
- uncommitted handler output MUST be discarded or revalidated;
- an active sandbox MUST be treated as untrusted until identity and cgroup ownership are
  reverified;
- an unverified sandbox MUST be destroyed;
- duplicate ledger writes MUST use the original idempotency key;
- duplicate memory writes MUST be idempotent;
- a ledger-committed but memory-uncommitted run MAY resume only at
  `DECISION_LEDGER → MEMORY_WRITEBACK`;
- no earlier handler may be rerun after a later transition was durably committed.

### 17.3 Cleanup

Sandbox deletion is not itself proof of cleanup.

The runtime MUST verify:

- container or microVM termination;
- cgroup emptiness;
- network rule removal;
- temporary mount removal;
- secret revocation;
- workspace deletion or quarantine;
- release of runtime leases.

Cleanup failures MUST be escalated and observable.

---

## 18. Observability, Audit, and Runtime Threat Detection

### 18.1 Metrics

The trusted runtime MUST emit structured metrics for:

- runs by mode and terminal status;
- frame duration;
- transition violations;
- sandbox provisioning duration;
- image pull duration;
- admission verification failures (signature, provenance, SBOM);
- container startup duration;
- CPU, memory, PID, I/O, and disk usage;
- OOM and timeout counts;
- network denials;
- artifact rejection and content-scan verdicts;
- vulnerability re-scan findings by severity and SLA status;
- ledger append latency;
- signing latency;
- cleanup failure;
- shadow-versus-legacy divergence.

Metrics MUST use bounded-cardinality labels. Raw prompts, secrets, and unrestricted run IDs
MUST NOT be used as metric labels.

Security-relevant runtime logs MUST be separate from untrusted workload logs.

### 18.2 Runtime Threat Detection

Configuration-time verification (§15.2) MUST be complemented by live detection on
hard-mode nodes:

- an approved eBPF- or kernel-audit-based detection agent (Falco-class) MUST monitor for
  containment anomalies during sandbox lifetime, including unexpected process execution,
  privilege-transition attempts, sensitive-file access, container-runtime socket access,
  and unexpected outbound connection attempts;
- detection rules MUST be versioned alongside the policy bundle;
- Critical detections MUST trigger immediate sandbox termination and quarantine via the
  failure sequence, and MUST be evaluated against the automatic rollback triggers of
  §21.2;
- detection events are trusted-runtime evidence and MUST be included in the failure
  record where applicable;
- the detection agent runs on the host, outside sandbox reach, and its absence or
  failure on a node MUST block new hard-mode provisioning on that node.

---

## 19. Performance and Capacity Requirements

### 19.1 Measurement Method

Performance claims MUST be based on reproducible benchmarks with:

- hardware and kernel versions recorded;
- runtime class recorded;
- image cache state recorded;
- cold and warm-image cases separated;
- at least p50, p95, and p99 results;
- ordinary, shadow, and hard-mode comparisons;
- admission verification (signature/provenance) latency measured separately;
- CPU, memory, disk, and network saturation monitored.

### 19.2 Optimization Constraints

Performance optimization MUST NOT weaken isolation or supply-chain verification.

Permitted optimizations include:

- pre-pulling verified images;
- caching admission verification results keyed by digest and trust-policy version;
- content-addressed layer caching;
- local read-only registry mirrors with integrity verification;
- precompiled policy and schema caches derived from the verified bundle;
- connection pooling outside sandboxes;
- batched chain-head anchoring;
- snapshotter optimization;
- bounded tmpfs use.

The following are forbidden in hard mode:

- reusing a workload container across runs;
- retaining writable layers across runs;
- sharing writable workspaces;
- skipping namespace or cgroup verification;
- skipping or caching-past admission verification when the trust policy version changes;
- replacing digest pinning with mutable tags;
- disabling seccomp, LSM, network policy, or runtime threat detection for speed.

### 19.3 Initial Promotion Budgets

Before hard-mode promotion, the project MUST establish environment-specific budgets.

At minimum:

- cached-image sandbox startup p95 MUST be measured and approved;
- uncached image-pull latency MUST be tracked separately;
- admission verification latency MUST be bounded;
- transition-enforcement CPU overhead MUST be measured against ordinary mode;
- peak trusted-runtime memory per concurrent run MUST be bounded;
- evidence and log storage growth per run MUST be bounded;
- cleanup backlog MUST remain below the approved operational threshold.

A missed performance budget may block promotion, but it MUST NOT trigger silent security
downgrades.

---

## 20. Rollout Phases

### Phase 0 — Specification and Threat Model

Deliverables:

- canonical frame definitions;
- compiled transition table;
- threat model and trusted-computing-base inventory, explicitly including the
  supply-chain attacker and build pipeline (§1.3, §8.4);
- typed schemas;
- canonical serialization test vectors;
- capability-contract schema;
- runtime-class policy;
- resource profiles;
- network policy model;
- supply-chain trust policy: SBOM format, signing scheme, transparency log, SLSA target
  levels, severity thresholds and SLAs (§8, §14.2).

Exit criteria:

- graph invariants pass;
- all trust boundaries are documented;
- external side effects are explicitly disabled for v3.4;
- Quality Tribunal accepts the specification.

### Phase 1 — Runtime State Authority

Implement:

- runtime-only state mutation;
- compare-and-swap transitions;
- handler registry;
- idempotency keys;
- failure routing;
- terminal-state enforcement;
- crash-recovery state;
- signed policy bundle verification at startup (§8.7).

Exit criteria:

- frame skip, repeat, stale commit, and dynamic-edge tests fail closed;
- terminal states cannot be reopened;
- restart tests preserve sequence integrity;
- tampered-bundle startup tests fail closed;
- SAST, SCA, and secret-scanning pipelines (§13.1–§13.3) are operational and gating on
  TCB code.

### Phase 2 — Supply Chain and Container Isolation Baseline

Implement:

- hermetic build pipeline with signed provenance (§8.4);
- SBOM generation and signing (§8.2);
- Cosign signing and broker-side admission verification (§8.3);
- registry hardening (§8.6);
- dependency lockfile hash-pinning (§8.5);
- immutable image digests;
- rootless or user-namespace-remapped execution;
- read-only root;
- non-root user;
- capability dropping;
- `no-new-privileges`;
- seccomp;
- LSM profile;
- isolated namespaces;
- bounded writable workspace;
- Docker socket denial;
- artifact importer, including malware and secret scanning (§7.3).

Exit criteria:

- runtime verifies effective isolation;
- unsigned, tampered, and out-of-policy images are rejected at admission in tests;
- all filesystem escape tests pass;
- importer fuzz harnesses (§13.6) run in CI with no unresolved crashes;
- no sandbox can access the container daemon or host worktree;
- cleanup verification passes under crash tests.

### Phase 3 — cgroups and Resource Governance

Implement:

- cgroups v2 profiles;
- CPU, memory, swap, PID, I/O, disk, file, and log limits;
- external timeout supervisor;
- full-cgroup termination;
- OOM and exhaustion classification.

Exit criteria:

- fork bombs, memory exhaustion, disk exhaustion, and log floods remain contained;
- no descendant process survives termination;
- resource evidence is present and accurate.

### Phase 4 — Network Isolation and A2A Relay

Implement:

- no-network default;
- mediated DNS;
- authenticated egress proxy with explicit TLS handling (§10.2);
- IPv4 and IPv6 enforcement;
- metadata and link-local blocking;
- A2A relay with capability checks.

Exit criteria:

- prohibited host, peer, metadata, and internet access tests fail;
- DNS rebinding and alternate-resolver bypass tests fail;
- direct-IP TLS and domain-fronting bypass tests fail;
- authorized destinations remain usable within byte and time limits;
- A2A messages cannot bypass routing policy;
- initial DAST (§13.5) of the proxy and relay is complete with Critical/High findings
  remediated.

### Phase 5 — Evidence and Ledger Hardening

Implement:

- canonical evidence manifests;
- signing-service isolation with KMS/HSM-backed keys (§12.2);
- signed transition records;
- failure ledger;
- chain-head anchoring;
- deterministic redaction;
- durable idempotent ledger writes.

Exit criteria:

- signing keys are absent from sandboxes;
- altered, reordered, duplicated, and truncated records are detected;
- failure paths produce audit records;
- crash recovery does not duplicate logical commits;
- key rotation has been exercised in staging;
- DAST of the signing service and ledger APIs is complete with Critical/High findings
  remediated.

### Phase 6 — Ordinary-Mode Instrumentation

Deploy contracts in `ordinary` mode.

Requirements:

- no behavior change beyond warnings and audit;
- collect baseline latency and violation data;
- classify false positives;
- inventory undeclared tools, paths, and network use;
- establish performance and capacity budgets;
- continuous re-scanning (§14.1) and rebuild cadence (§14.3) operating on all pinned
  digests.

Exit criteria:

- representative workload coverage is approved;
- no unknown critical execution paths remain;
- baseline data is sufficient for shadow comparison;
- vulnerability remediation SLAs (§14.2) are being met in practice.

### Phase 7 — Shadow Rollout

Enable `shadow` incrementally by frame:

1. `INTENT`;
2. `RISK_ASSESSMENT`;
3. `CAPABILITY_CONTRACT`;
4. `SANDBOX_PROVISION`;
5. `DRY_RUN`;
6. remaining evidence and persistence frames.

Shadow results MUST NOT authorize capabilities or execution.

Exit criteria:

- zero unexplained sequence divergence for the approved observation window;
- contract false-positive rate is below the approved threshold;
- isolation configuration passes runtime verification;
- performance budgets are met;
- runtime threat detection (§18.2) is deployed on all shadow nodes;
- all critical violations have owners and remediation.

### Phase 8 — Hard-Mode Canary

Enable `hard` mode for an allowlisted low-risk workload class.

Canary requirements:

- default no network;
- no secrets;
- no external mutation;
- pinned, signed, provenance-verified images;
- bounded resource profile;
- automatic rollback to service unavailability, not ordinary mode;
- continuous Quality Tribunal and observability coverage;
- runtime threat detection active on all canary nodes.

Entry criteria:

- internal penetration test (§13.7) complete with Critical/High findings remediated;
- SLSA Build Level 2 achieved for all §8.1 artifact classes;
- emergency rebuild path (§14.5) exercised at least once.

Exit criteria:

- no unresolved critical isolation failure;
- no ledger integrity failure;
- no admission-verification bypass;
- cleanup success meets the approved target;
- latency and capacity remain within approved budgets;
- incident response has completed a live exercise.

### Phase 9 — Risk-Tier Expansion

Expand in order:

1. deterministic read-only tools;
2. local code analysis;
3. bounded compilation and tests;
4. approved package-dependent workloads;
5. high-risk workloads using hardened containers or microVMs.

Each tier requires its own:

- runtime class;
- seccomp profile;
- network policy;
- resource profile;
- image profile with SBOM, signature, and provenance under §8;
- benchmark;
- adversarial test suite;
- rollback criteria.

Tier 4 (package-dependent workloads) additionally requires dependency-source allowlisting
through the mediated egress policy and post-run artifact content scanning (§7.3).

### Phase 10 — Hard Mode as Default

Hard mode may become the default only when:

- all mandatory gates pass;
- ordinary-mode fallback is explicitly administrative and never automatic;
- unsupported workloads fail closed;
- replay verification is operational;
- ledger anchoring is operational;
- incident response and key rotation are tested;
- an independent external security audit (§13.7) is complete with Critical/High findings
  remediated or formally risk-accepted;
- SLSA Build Level 3 is achieved or a signed Tribunal record accepts documented residual
  risk at Level 2;
- continuous re-scanning, rebuild cadence, and patch SLAs (§14) have operated within
  target for the approved observation window;
- capacity planning covers expected concurrency;
- the Quality Tribunal signs the promotion record.

---

## 21. Rollback and Incident Response

### 21.1 Deployment Rollback

A deployment may roll back to a previous signed runtime, policy bundle, image, or
transition-table version. Rollback targets MUST themselves pass current vulnerability
policy (§14.2); rolling back onto a known-vulnerable version requires a signed waiver.

An in-progress run MUST remain pinned to its original versions or fail closed. It MUST NOT
silently migrate between transition tables or image digests.

### 21.2 Automatic Rollback Triggers

Deployment rollback or hard-mode admission suspension MUST be considered for:

- namespace or cgroup verification failure;
- Docker socket or host mount exposure;
- signing-key exposure;
- ledger integrity failure;
- network-policy bypass;
- admission-verification bypass or trust-policy violation;
- confirmed malicious dependency or image in the supply chain;
- Critical runtime threat detection (§18.2) indicating containment breach;
- surviving sandbox processes after cleanup;
- unexplained state-transition corruption;
- artifact importer escape;
- critical kernel or runtime vulnerability outside SLA (§14.4).

### 21.3 No Silent Downgrade

When hard mode is unavailable:

- new hard-mode runs MUST be rejected or queued;
- active runs MUST fail closed if their guarantees cannot be maintained;
- the system MUST NOT continue in shadow or ordinary mode under the same run identity.

### 21.4 Key Compromise

On suspected signing-key compromise:

- stop new signatures;
- rotate the key via the KMS/HSM procedure (§12.2);
- record the affected key identifier and time range;
- preserve prior evidence;
- mark affected records for re-verification, using transparency-log entries to bound the
  affected window;
- publish a signed incident and recovery anchor.

### 21.5 Supply-Chain Compromise

On confirmed or suspected compromise of a dependency, image, registry, or build pipeline:

- suspend hard-mode admission for affected profiles;
- identify affected digests via SBOMs and transparency-log records;
- quarantine affected artifacts and evidence for forensics;
- execute the emergency rebuild path (§14.5) from verified-clean sources;
- re-verify ledger and evidence records produced by runs that used affected artifacts;
- publish a signed incident record referencing affected digests and remediation digests.

---

## 22. Required Repository Layout

The implementation SHOULD use the following project-relative structure:

    hard_frames/
      state/
        frames.py
        transition_table.py
        runtime.py
        recovery.py
      contracts/
        intent.py
        risk.py
        capability.py
        sandbox.py
        execution.py
        quality.py
        evidence.py
        ledger.py
        memory.py
        failure.py
      policy/
        enforcement/
        capabilities/
        network/
        resources/
        runtimes/
        seccomp/
        lsm/
        trust/            # supply-chain trust policy: signers, logs, SLSA levels
        detection/        # runtime threat-detection rules
      supply_chain/
        sbom.py
        verify.py         # admission-time signature/provenance/SBOM verification
        provenance.py
        vex/
      sandbox/
        broker.py
        verifier.py
        importer.py
        scanner.py        # artifact malware/secret content scanning
        cleanup.py
      evidence/
        canonical.py
        redaction.py
        signing.py
        manifest.py
      ledger/
        writer.py
        verifier.py
        anchoring.py
      replay/
        verifier.py
      security/
        sast/             # SAST configuration and waivers
        dast/             # DAST profiles for trusted services
        fuzz/
          harnesses/
          corpora/
      tests/
        graph/
        contracts/
        isolation/
        resources/
        network/
        ledger/
        replay/
        supply_chain/
        adversarial/

Equivalent layouts require Quality Tribunal approval. Generated files, runtime evidence,
and scan outputs MUST remain outside source-controlled policy directories. Signed VEX
statements and waivers are source-controlled and reviewed.

---

## 23. Definition of Done

Hard Frames v3.4 is complete only when:

- the state machine is compiled, versioned, signed, and pinned per run;
- the runtime verifies its signed policy bundle at startup and fails closed otherwise;
- only `RAERuntime` can commit state transitions;
- every transition has one authorized handler;
- all contracts are strict and canonically serializable;
- capabilities are sealed before sandbox provisioning;
- hard-mode sandboxes meet the namespace, filesystem, kernel, network, and cgroup baseline;
- every sandbox image is SBOM-documented, signed, provenance-attested, and verified at
  admission time, with verification recorded in evidence;
- pinned digests are continuously re-scanned and rebuilt within policy cadence and SLAs;
- SAST, SCA, secret-scanning, IaC scanning, DAST, and fuzzing gates are operational and
  enforced on the trusted computing base;
- an internal penetration test and an external security audit have been completed with
  Critical/High findings remediated or formally risk-accepted;
- no sandbox receives container-control sockets or signing keys;
- imported artifacts pass structural and content scanning before crossing the trust
  boundary;
- external mutation is prohibited;
- evidence is bounded, redacted, signed, and content-addressed;
- success and failure records are durable and idempotent;
- chain heads are externally anchored;
- signing keys are KMS/HSM-backed and rotation has been exercised;
- replay performs no live execution or normal writes;
- crash recovery preserves frame, ledger, and policy-bundle consistency;
- runtime threat detection is active on all hard-mode nodes;
- adversarial isolation and supply-chain tests pass;
- performance budgets are measured and approved;
- hard-mode failure never silently downgrades enforcement;
- the Quality Tribunal has signed the final promotion record.