import pytest
from core.portal_dashboards import PortalDashboardAggregator


def test_portal_dashboard_aggregator_returns_all_modules():
    aggregator = PortalDashboardAggregator()
    overview = aggregator.get_full_command_center_overview()

    assert overview["status"] == "ALL_SYSTEMS_OPERATIONAL"
    assert "supervisor" in overview
    assert "quality" in overview
    assert "lab" in overview
    assert "memory" in overview
    assert "phoenix_clr" in overview
    assert "mesh" in overview

    assert overview["supervisor"]["active_containers_count"] > 0
    assert overview["quality"]["coverage_percentage"] > 90.0
    assert overview["memory"]["episodic_memories_count"] > 0
    assert len(overview["mesh"]["active_nodes"]) >= 3
