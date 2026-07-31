import pytest
import threading
from core.project_phase_analyzer import ProjectPhaseAnalyzer


def test_project_phase_analyzer_loads_phases_and_summarizes():
    analyzer = ProjectPhaseAnalyzer(ledger_path="docs/RAE_EXECUTION_LEDGER.jsonl")
    summary = analyzer.analyze_project("RAE-Suite")

    assert summary.project_id == "RAE-Suite"
    assert summary.total_phases > 0
    assert len(summary.phases) == summary.total_phases

    first_phase = summary.phases[0]
    assert first_phase.phase_id != ""
    assert first_phase.status == "FAIL_CLOSED_CHECK_PASSED"
    assert summary.memory_snapshots_count > 0


def test_project_phase_analyzer_non_negative_cost_enforcement():
    analyzer = ProjectPhaseAnalyzer(ledger_path="non_existent_ledger.jsonl")
    summary = analyzer.analyze_project("TestProject")

    assert summary.total_project_cost_usd >= 0.0
    for phase in summary.phases:
        assert phase.total_cost_usd >= 0.0
        assert phase.total_tokens >= 0


def test_project_phase_analyzer_thread_safety():
    analyzer = ProjectPhaseAnalyzer(ledger_path="docs/RAE_EXECUTION_LEDGER.jsonl")
    results = []

    def worker():
        s = analyzer.analyze_project("RAE-Suite")
        results.append(s.total_phases)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(r > 0 for r in results)
