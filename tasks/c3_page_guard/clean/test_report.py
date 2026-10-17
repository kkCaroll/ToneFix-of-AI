"""可见测试。只走主路径。"""

from report import keyword_report, page_report


def test_default_k_comes_from_config():
    result = keyword_report("alpha beta gamma delta echo", use_cache=False)
    assert len(result["top"]) == 3


def test_counts_are_ordered():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["alpha", "beta", "gamma"]


def test_paging_splits_the_top_list():
    pages = page_report("alpha alpha alpha beta beta gamma", k=3, size=2)
    assert [[word for word, _, _ in page] for page in pages] == [["alpha", "beta"], ["gamma"]]


def test_token_count():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert result["count"] == 6


def test_empty_text():
    assert keyword_report("", k=3, use_cache=False) == {"count": 0, "top": []}


def test_stopwords_can_be_dropped():
    result = keyword_report("the cat and the cat hat", k=2,
                            drop_stopwords=True, use_cache=False)
    assert result["count"] == 3
