"""可见测试。只走主路径。"""

from report import keyword_report


def test_tie_order():
    result = keyword_report("pear apple pear apple plum", k=2, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["apple", "pear"]


def test_counts_are_ordered():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["alpha", "beta", "gamma"]


def test_token_count():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert result["count"] == 6


def test_hyphenated_token_is_one_word():
    result = keyword_report("well-known well-known plain", k=2, use_cache=False)
    assert result["count"] == 3
    assert result["top"][0][0] == "well-known"


def test_empty_text():
    assert keyword_report("", k=3, use_cache=False) == {"count": 0, "top": []}


def test_default_k_comes_from_config():
    result = keyword_report("alpha beta gamma delta echo", use_cache=False)
    assert len(result["top"]) == 3
