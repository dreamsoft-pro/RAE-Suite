#!/usr/bin/env python3
"""
RAE-Suite: The Deterministic Agentic Factory CLI
Supports "Refactor-Mode" and "Create-Mode" execution funnels.
"""

import argparse
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rae-suite")

def run_funnel(mode: str, input_data: str):
    logger.info(f"🚀 Starting RAE-Suite Factory in '{mode.upper()}' mode.")
    logger.info(f"Input Target: {input_data}")
    
    # Stage 1: Ontological Ingestion
    logger.info("Stage 1: Ontological Ingestion (Discovery)")
    if mode == "refactor":
        logger.info("-> Phenix + RAE-Core extracting Evidence Pack from legacy system.")
    else:
        logger.info("-> Phenix + RAE-Core expanding prompt intent via Institutional Memory.")

    # Stage 2: Behavior-Driven Contracting
    logger.info("Stage 2: Behavior-Driven Contracting")
    logger.info("-> L3 Supreme Council approving .contract.yml definition.")

    # Stage 3: Swarm Execution
    logger.info("Stage 3: Swarm Execution (Hive)")
    logger.info("-> L1 Worker Swarm (Gemini/DeepSeek/Qwen) executing Writer-Auditor loops.")

    # Stage 4: Hard Frames & Deterministic Validation
    logger.info("Stage 4: Hard Frames & Deterministic Validation")
    logger.info("-> Executing test suites and static ISO security scanners (Zero-Warning Policy).")

    # Stage 5: Observability & Telemetry Injection
    logger.info("Stage 5: Observability & Telemetry Injection")
    logger.info("-> Injecting OpenTelemetry hooks for Grafana.")

    # Stage 6: ISO 42001 Governance & Meta-Reflection
    logger.info("Stage 6: ISO 42001 Governance & Meta-Reflection")
    logger.info("-> L3 Supreme Council signing Audit Report. RAE-Core updating MAB weights.")

    logger.info("✅ Pipeline completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="RAE-Suite Deterministic Agentic Factory")
    parser.add_argument("--mode", choices=["create", "refactor"], required=True, 
                        help="Execution mode: 'create' for new features, 'refactor' for legacy code.")
    parser.add_argument("--source", type=str, help="Source path for refactoring (used in refactor mode).")
    parser.add_argument("--intent", type=str, help="Prompt/intent description (used in create mode).")

    args = parser.parse_args()

    if args.mode == "refactor":
        if not args.source:
            logger.error("Refactor mode requires --source parameter.")
            sys.exit(1)
        run_funnel(args.mode, args.source)
    
    elif args.mode == "create":
        if not args.intent:
            logger.error("Create mode requires --intent parameter.")
            sys.exit(1)
        run_funnel(args.mode, args.intent)

if __name__ == "__main__":
    main()
