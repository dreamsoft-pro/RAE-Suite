# RAE OpenClaw - Bridge Skill (Hard Contract)
# This file is a marker for OpenClaw to index the mandatory RAE tools.

Skill: RAE-Suite-Bridge (Governance)
--------------------------------------
Constraint: NO_DIRECT_WRITE
All changes to the codebase MUST be performed via the 'trigger_refactoring' or 'assign_coding_task' tools.
Direct filesystem manipulation (e.g., using fs.writeFile) on project files is strictly forbidden by the RAE Protocol.

Mandatory Tools (mapped to RAE Bridge API):
1. run_quality_audit(code, project_id) -> MUST be called before any proposed change.
2. store_verified_memory(content, project_id) -> Persists knowledge into RAE Semantic Layer.
3. trigger_phoenix_fix(project_id, code, reason) -> Escalates repair to RAE-Phoenix.

Security Policy:
- X-Tenant-Id: default-tenant
- X-Project-Id: [Target Project]
- Enforcement: Quality Tribunal Tier 3 (Supreme Court)
