import cache
from report import keyword_report, page_report


def test_counts_and_shares():
    result = keyword_report("the cat and the hat and the bat", k=2)
    assert result["count"] == 8
    assert result["top"] == [("the", 3, 0.375), ("and", 2, 0.25)]


def test_ties_break_by_word_order():
    result = keyword_report("pear apple pear apple plum", k=2)
    assert result["top"] == [("apple", 2, 0.4), ("pear", 2, 0.4)]


def test_empty_text():
    assert keyword_report("", k=3) == {"count": 0, "top": []}


def test_stopwords_can_be_dropped():
    result = keyword_report("the cat and the cat hat", k=2, drop_stopwords=True)
    assert result["count"] == 3
    assert result["top"] == [("cat", 2, 0.6667), ("hat", 1, 0.3333)]


def test_default_k_comes_from_config():
    result = keyword_report("alpha alpha beta gamma delta echo")
    assert len(result["top"]) == 3


def test_cache_returns_the_same_object():
    cache.clear()
    first = keyword_report("alpha alpha beta", k=2)
    second = keyword_report("alpha alpha beta", k=2)
    assert first is second
    cache.clear()


def test_cache_can_be_bypassed():
    cache.clear()
    first = keyword_report("alpha alpha beta", k=2)
    second = keyword_report("alpha alpha beta", k=2, use_cache=False)
    assert first is not second
    assert first == second
    cache.clear()


def test_paging_splits_the_top_list():
    text = "alpha alpha alpha beta beta gamma"
    assert page_report(text, k=3, size=2) == [
        [("alpha", 3, 0.5), ("beta", 2, 0.3333)],
        [("gamma", 1, 0.1667)],
    ]
