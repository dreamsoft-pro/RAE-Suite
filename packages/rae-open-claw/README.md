# OpenClaw within RAE-Suite

OpenClaw serves as the **Strategic Agentic Gateway** for the Silicon Oracle RAE Suite. It provides the Model Context Protocol (MCP) interface and the Control UI for managing agentic workflows across the distributed cluster (Laptop + Node 1).

## 🛡️ Hard Frames Architecture

OpenClaw in RAE-Suite operates under the **Hard Frames** security paradigm, ensuring a contained and non-bypassable environment for AI agents.

### Core Pillars:

1.  **Network Isolation (Phase 1)**
    - The gateway is bound to specific LAN interfaces.
    - Direct access is restricted to the internal `rae-internal` network.
    - Cross-node communication (Laptop <-> Node 1) is secured via verified endpoints.

2.  **Protocol Exclusivity (Phase 2)**
    - Mandatory authentication tokens for all gateway operations.
    - Origin validation for the Control UI (preventing CSRF and unauthorized access).
    - Strict enforcement of the Agentic Pattern + Security Contract.

3.  **Runtime Hardening (Phase 3)**
    - **Read-Only Filesystem**: The application source code (`dist/`) is mounted as read-only.
    - **Capability Dropping**: The container drops all Linux capabilities (`cap_drop: ALL`).
    - **Privilege Escalation Prevention**: `no-new-privileges:true` is enforced.
    - **Isolated Workspaces**: Agents only have write access to designated `/workspace` and `~/.openclaw` directories.

## 🚀 Deployment

To start OpenClaw in the recommended secure mode, use:

```bash
docker compose -f docker-compose.secure.yml up -d
```

### Configuration
Key configuration is stored in `~/.openclaw/openclaw.json`. 
In **Hard Frames** mode, the system automatically detects the environment and applies the appropriate security policy.

---
*Silicon Oracle v3.2 - Agentic Context Injected*
