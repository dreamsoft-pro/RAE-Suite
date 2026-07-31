import pytest
from core.portal_global_search import RAEGlobalSearchEngine, SearchQuery


def test_global_search_engine_query_and_pagination():
    engine = RAEGlobalSearchEngine()
    q = SearchQuery(query="A2A", limit=10, offset=0)
    resp = engine.search(q)

    assert resp.query == "A2A"
    assert resp.total_matches > 0
    assert len(resp.items) <= 10

    first_item = resp.items[0]
    assert "A2A" in first_item.headline or "A2A" in first_item.id
    assert first_item.snippet != ""


def test_global_search_engine_module_filtering():
    engine = RAEGlobalSearchEngine()
    q = SearchQuery(query="", module_filter="rae-memory")
    resp = engine.search(q)

    for item in resp.items:
        assert item.source_module == "rae-memory"
