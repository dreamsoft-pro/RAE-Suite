# RAE Hive: Systemic Circuit Breaker & Semantic Watchdog
## Specification v1.0

### 1. The Problem: "Echo Loops" and "Silent Hangs"
Previous monitoring solutions (v0.1 - v0.9) failed because they relied on superficial metrics (container uptime, log tailing, CPU usage). This led to two fatal failure modes during autonomous operations on Node 1:
1.  **Echo Loops (Semantic Deadlock):** The Builder (L1) and Auditor (L2) get stuck in an infinite feedback loop. The Auditor repeatedly flags the same error, and the Builder repeatedly applies the same incorrect fix. The process is "active" but makes zero progress.
2.  **Silent Hangs:** The local inference model (DeepSeek/Qwen) stalls during generation without throwing an exception, causing the agent to wait indefinitely.

### 2. The Solution: Semantic Progress Monitoring
The new monitoring paradigm abandons log tailing in favor of **State-Based Semantic Monitoring** integrated directly with `RAE-Core`'s memory layers.

#### A. Semantic Loop Detection (Anti-Echo)
The Watchdog monitors the `episodic` layer for task transitions (`review` -> `in_progress` -> `review`).
*   **Rule (Max Retries):** If a specific task is rejected by the Auditor **3 times**.
*   **Rule (Semantic Similarity):** The Watchdog calculates the vector distance between the Auditor's rejection reasons. If similarity > 0.90, the agents are trapped in an Echo Loop.
*   **Action:** The Watchdog immediately changes the task status to `BLOCKED_LOOP`.

#### B. Heartbeat & AST State (Anti-Hang)
*   **Rule:** Agents must write a lightweight "Heartbeat" to the `working` layer every 60 seconds (e.g., "Analyzing AST node: FunctionDeclaration").
*   **Action:** If a heartbeat is missing for > 120 seconds, the Watchdog performs a Hard Reset of the specific agent container (`docker restart hive-builder`).

### 3. Automatic Correction Pipeline (Escalation)
When a task is marked as `BLOCKED_LOOP`, the system does not abandon it. It escalates to the **Supreme Council (L3)**.
1.  **Audit Trail Creation:** The Watchdog aggregates the failed attempts and writes a post-mortem to the `reflective` layer: *"Task X failed. Auditor demanded Y, Builder provided Z. Loop detected."*
2.  **L3 Intervention:** Gemini 3 Pro (L3) is awakened. It reads the post-mortem, the original Contract, and the Graph.
3.  **Strategic Pivot:** Gemini generates a *Correction Plan* (e.g., "The Builder lacks context about interface X. Modify the prompt to include file Y" or "Break this task into two smaller tasks").
4.  **Task Unlocking:** The task is reset to `pending` with the new, L3-injected context.

### 4. Implementation Details
*   **Component:** `SemanticWatchdog` (runs as a lightweight asynchronous task alongside the Orchestrator).
*   **Dependencies:** Requires `rae-core` for memory queries and vector similarity.
*   **Telemetry:** Every intervention (Circuit Break, Restart, Escalation) MUST be logged via OpenTelemetry (OTel) for Grafana visualization.
