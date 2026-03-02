# RAE-Suite: The Deterministic Agentic Factory

Welcome to **RAE-Suite**, the first deterministic operating system for agentic software engineering. This suite is an ecosystem that transforms the uncertainty of Large Language Models (LLMs) into high-density, auditable, and industrial-grade software artifacts.

It implements the **"Architecture as a Service" (RaaS/CaaS)** model, where software is manufactured through a rigorous, 6-stage behavioral funnel governed by the **3x3x3 Council of Elders**.

## Operational Modes

RAE-Suite provides two distinct execution modes, executing the same underlying 6-stage funnel:

*   **Refactor-Mode (`--mode refactor`)**: Targets legacy systems. Extracts ontological intent from existing code to create a modernized "Mirror" (e.g. Operacja Lustro).
*   **Create-Mode (`--mode create`)**: Targets new features. Extracts ontological intent from human descriptions to build new systems from a "Zero-State" baseline.

## The Three Pillars of the Suite (Submodules)

1.  **[RAE-Core (Agnostic Core)](packages/rae-core):** The Institutional Memory ("Silicon Oracle"). Provides vector-deterministic persistence, semantic resonance, and the *Szubar Mode* for emergent induction.
2.  **[RAE-Hive](packages/rae-hive):** The Worker Swarm. Manages the asynchronous execution of *Writer-Auditor* pairs across distributed compute nodes.
3.  **[RAE-Phoenix](packages/rae-phoenix):** The Behavioral Engineer. Defines hard behavioral boundaries, manages ISO compliance, and translates intention into testable YAML contracts.

## The 6-Stage Production Funnel

1. **Ontological Ingestion (Discovery)**: Analyzes legacy UI/API or prompt to reconstruct the intent field.
2. **Behavior-Driven Contracting**: Generates `.contract.yml` (I/O schemas, side effects, time complexity).
3. **Swarm Execution**: The L1 Worker Swarm implements the code via Writer-Auditor feedback loops.
4. **Hard Frames & Deterministic Validation**: Physical execution of tests and security scanners (zero-warning policy).
5. **Observability & Telemetry Injection**: Injects OpenTelemetry (OTel) instrumentation for Grafana tracking.
6. **ISO 42001 Governance**: The L3 Supreme Council issues a Final Verdict, generating a signed Audit Report. RAE-Core updates MAB (Multi-Armed Bandit) weights.

## The 3x3x3 Council of Elders

Every critical decision requires a consensus of three specialized models at each layer (Configurable via `.env`):

| Layer | Type | Default Models (A / B / C) | Responsibility |
| :--- | :--- | :--- | :--- |
| **L1: Working** | Production | **Gemini 2.5 Flash / DeepSeek V3 / Qwen 2.5** | High-speed code generation, unit testing, static analysis. |
| **L2: Expert** | Auditing | **Claude 3.5 Sonnet / Gemini 1.5 Pro / GPT-4o** | Structural review, contract generation, semantic logic verification. |
| **L3: Supreme** | Final Verdict | **Claude 4.5 / Gemini 2.0 Pro / GPT-o1** | Behavioral symmetry, ISO compliance, final safety arbitration. |

## Quick Start

1. Initialize submodules:
```bash
git submodule update --init --recursive
```

2. Configure your `.env` (API keys, Council models).
3. Run the factory:
```bash
python rae_suite.py --mode create --intent "A new JWT authentication microservice"
python rae_suite.py --mode refactor --source ./legacy-app
```

## License
Open Source under the Apache 2.0 License.
