import pytest
from rae_contracts import RiskClass
from core.cognitive_planner import CognitivePlanner, CognitivePlan, PlannerBranch

@pytest.mark.asyncio
async def test_cognitive_planner_generation_and_mcts():
    planner = CognitivePlanner()
    intent = "Refactor the database adapter to support async batching"
    
    plan = await planner.plan_task(
        intent=intent,
        payload={},
        risk_class=RiskClass.R4
    )
    
    # Verify the plan matches specifications
    assert isinstance(plan, CognitivePlan)
    assert plan.intent == intent
    assert plan.risk_class == RiskClass.R4
    assert len(plan.branches) >= 3
    
    # Verify branches
    selected_count = 0
    for branch in plan.branches:
        assert isinstance(branch, PlannerBranch)
        assert branch.branch_id is not None
        assert branch.name in ["Async Batching Pipeline", "Thread-Pool Executor Wrapper", "Event-Driven Message Queue Broker"]
        assert 0.0 <= branch.viability_score <= 1.0
        assert len(branch.simulated_impacts) == 3  # step 1, 2, 3
        assert branch.critique_feedback != ""
        if branch.is_selected:
            selected_count += 1
            assert branch.branch_id == plan.selected_branch_id
            
    assert selected_count == 1
    assert plan.win_probability > 0.0
    assert plan.planning_duration_ms > 0.0

@pytest.mark.asyncio
async def test_cognitive_planner_general_fallback():
    planner = CognitivePlanner()
    intent = "Some completely unrelated request"
    
    plan = await planner.plan_task(
        intent=intent,
        payload={},
        risk_class=RiskClass.R2
    )
    
    assert isinstance(plan, CognitivePlan)
    assert len(plan.branches) >= 3
    # Check that fallback branch names are generated
    branch_names = [b.name for b in plan.branches]
    assert "Direct Inline Refactoring" in branch_names
    assert "Facade Pattern Isolation" in branch_names
    assert "Distributed Strategy Pattern" in branch_names

def test_cognitive_planner_prm_evaluator():
    planner = CognitivePlanner()
    
    # Safe step
    safe_score = planner._evaluate_step_prm("Step 3: Verification", "Run coverage and compliance checks in sandbox.")
    assert safe_score == 1.0
    
    # Unsafe step with absolute path
    unsafe_path_score = planner._evaluate_step_prm("Step 2: Copy Config", "Copy configuration from /home/user/config.yaml")
    assert unsafe_path_score < 1.0
    
    # Unsafe step with credentials and no redaction
    unsafe_secret_score = planner._evaluate_step_prm("Step 1: Get Secret", "Retrieve private api token for connection")
    assert unsafe_secret_score < 1.0
    
    # native build with sandbox should be ok, but native build without sandbox is penalized
    unsafe_native = planner._evaluate_step_prm("Step 2: Compile native module", "Compile rust extension directly on host")
    assert unsafe_native < 1.0
    
    safe_native = planner._evaluate_step_prm("Step 2: Compile native module", "Compile rust extension inside secure verification sandbox")
    assert safe_native == 1.0

@pytest.mark.asyncio
async def test_cognitive_planner_adaptive_search_depth():
    planner = CognitivePlanner()
    
    # Low complexity intent, low risk
    iterations_low = planner._determine_iterations(RiskClass.R1, "Simple format fix")
    assert iterations_low == 20
    
    # High complexity intent, high risk
    iterations_high = planner._determine_iterations(RiskClass.R4, "Refactor and optimize the database adapter for higher performance")
    # Base for R4 is 80, boosted by 1.5 because of "optimize" and "performance" -> 120
    assert iterations_high == 120
    
    # Verify execution with boost still works successfully
    plan = await planner.plan_task(
        intent="Refactor and optimize database adapter",
        payload={},
        risk_class=RiskClass.R3
    )
    assert plan.win_probability > 0.0

@pytest.mark.asyncio
async def test_cognitive_planner_consensus_chain(monkeypatch):
    import os
    monkeypatch.setenv("RAE_PLANNING_FLOW", "consensus_chain")
    planner = CognitivePlanner()
    intent = "Design a low-latency caching layer for pgpool"
    
    plan = await planner.plan_task(
        intent=intent,
        payload={},
        risk_class=RiskClass.R3
    )
    
    assert isinstance(plan, CognitivePlan)
    assert plan.intent == intent
    assert len(plan.branches) == 1
    assert plan.branches[0].name == "Consensus Refined Path"
    assert "Consensus Chain (Luna -> R1 -> Opus -> Sol -> Fable)" in plan.branches[0].architectural_approach
    assert plan.win_probability == 0.98
    assert "Model openai/gpt-5.6-luna-pro review completed successfully." in plan.branches[0].critique_feedback

