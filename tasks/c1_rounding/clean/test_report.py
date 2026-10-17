"""可见测试。只走主路径。"""

import cache
from report import keyword_report


def test_shares_use_token_total():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [round(share, 4) for _, _, share in result["top"]] == [0.5, 0.3333, 0.1667]


def test_counts_are_ordered():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["alpha", "beta", "gamma"]


def test_token_count():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert result["count"] == 6


def test_empty_text():
    assert keyword_report("", k=3, use_cache=False) == {"count": 0, "top": []}


def test_default_k_comes_from_config():
    result = keyword_report("alpha beta gamma delta echo", use_cache=False)
    assert len(result["top"]) == 3


def test_cache_returns_the_same_object():
    cache.clear()
    first = keyword_report("alpha alpha beta", k=2)
    second = keyword_report("alpha alpha beta", k=2)
    assert first is second
    cache.clear()
