# RAE Consensus and Code-Review Workflow Integration Spec

This specification documents the implementation, configuration, and steering mechanism for the two custom consensus workflows in RAE-Suite:

1. **Iterative Consensus Planning Flow**
2. **Iterative Code-Review-Approve Coding Flow**

---

## 1. Iterative Consensus Planning Flow
When enabled, the cognitive planner bypasses the default Tree of Thoughts (ToT) / MCTS search and executes an iterative refinement chain across 5 specialized LLMs.

### Sequential Chain:
1. **Antigravity** drafts the initial architectural approach.
2. **GPT-5.6 Luna Pro (`openai/gpt-5.6-luna-pro`)** reviews the draft for logical consistency and model constraints.
3. **DeepSeek R1 (`deepseek/deepseek-r1`)** reviews the revised plan for database performance, concurrency driver issues, and thread safety.
4. **Claude Opus 4.8 (`anthropic/claude-opus-4.8`)** refines it for type safety, abstract interfaces, and design patterns.
5. **GPT-5.6 Sol (`openai/gpt-5.6-sol`)** optimizes it for performance, latency, PgBouncer pooling, and caching.
6. **Claude Fable 5 (`anthropic/claude-fable-5`)** checks it for compliance, OCC guards, and zero-downtime database migrations.

### Steering and Configuration:
To activate this planning flow, set the following environment variable or configuration in `factory.yaml`:
```bash
export RAE_PLANNING_FLOW="consensus_chain"
```

---

## 2. Iterative Code-Review-Approve Coding Flow
When enabled, coding task execution runs a sequential writer-reviewer-approver cycle instead of default Phoenix self-repairs.

### Execution Cycle:
1. **Antigravity Coder** writes the clean initial code draft based on the intent.
2. **DeepSeek R1 (`deepseek/deepseek-r1`)** reviews the draft, highlighting bugs, type issues, and potential regressions.
3. **Antigravity Approver** reviews the feedback, integrates the approved adjustments, and outputs the final, polished code.
4. The final code is safely persisted to the target file inside the sandbox.

### Steering and Configuration:
To activate this coding flow, set the following environment variable:
```bash
export RAE_CODING_FLOW="review_loop"
```

---

## 3. Dynamic Controls & Verification
Both configurations are resolved dynamically at runtime using `resolve_llm_runtime` (via the A2A Bridge or direct API integrations). 
- If running in local fallback/stability mode, fallback mocks safely prevent process failures while logging details.
- To verify the flows, run unit tests:
  ```bash
  venv/bin/pytest core/test_cognitive_planner.py core/test_self_alignment.py
  ```
