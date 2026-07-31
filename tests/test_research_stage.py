import pytest
from core.research_stage import RAEResearchEngine, ResearchReport


def test_research_engine_valid_hypothesis():
    """RAEResearchEngine must validate valid refactoring hypotheses prior to execution."""
    engine = RAEResearchEngine(research_id="res_100")

    hypotheses = [
        {"id": "H1", "statement": "Refactoring apps/orders to use Pydantic V2 will improve type safety"},
        {"id": "H2", "statement": "Adding unit tests for payment validator ensures contract compliance"},
    ]

    report = engine.evaluate_refactoring_hypotheses(
        task_description="Refactor apps/orders validation",
        target_files=["apps/orders/validator.py"],
        hypotheses=hypotheses
    )

    assert report.ready_for_execution
    assert len(report.hypotheses_tested) == 2
    assert report.hypotheses_tested[0].is_valid


def test_research_engine_rejected_hypothesis():
    """RAEResearchEngine must reject invalid/violating hypotheses and block execution."""
    engine = RAEResearchEngine(research_id="res_101")

    hypotheses = [
        {"id": "H1", "statement": "Introduce forbidden global mutable state in singleton"},
    ]

    report = engine.evaluate_refactoring_hypotheses(
        task_description="Refactor singleton module",
        target_files=["core/singleton.py"],
        hypotheses=hypotheses
    )

    assert not report.ready_for_execution
    assert "Revise Refactoring Hypotheses" in report.recommended_strategy
