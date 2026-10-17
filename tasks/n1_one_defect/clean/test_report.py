"""可见测试。

每条测试只断言与某一处缺陷相关的量，因此只修好一部分缺陷无法让全部测试转绿。
"""

import cache
from report import keyword_report, page_report


def test_tie_order():
    """同次时按词形升序。"""
    result = keyword_report("pear apple pear apple plum", k=2, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["apple", "pear"]


def test_counts_and_shares():
    """占比按参与统计的词元总数计算。"""
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [round(share, 4) for _, _, share in result["top"]] == [0.5, 0.3333, 0.1667]


def test_token_count():
    """计数是参与统计的词元总数。"""
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert result["count"] == 6


def test_hyphenated_token_is_one_word():
    """连字符连成的词算一个词元。"""
    result = keyword_report("well-known well-known plain", k=2, use_cache=False)
    assert result["count"] == 3
    assert result["top"][0][0] == "well-known"


def test_default_k_comes_from_config():
    """k 缺省时取配置里的默认词项个数。"""
    result = keyword_report("alpha beta gamma delta echo", use_cache=False)
    assert len(result["top"]) == 3


def test_empty_text():
    assert keyword_report("", k=3, use_cache=False) == {"count": 0, "top": []}


def test_stopwords_can_be_dropped():
    result = keyword_report("the cat and the cat hat", k=2,
                            drop_stopwords=True, use_cache=False)
    assert result["count"] == 3


def test_paging_splits_the_top_list():
    """总数不能被页大小整除时仍要出最后一页。"""
    pages = page_report("alpha alpha alpha beta beta gamma", k=3, size=2)
    assert [[word for word, _, _ in page] for page in pages] == [["alpha", "beta"], ["gamma"]]


def test_default_page_size_comes_from_config():
    """size 缺省时取配置里的默认页大小。"""
    pages = page_report("alpha alpha alpha alpha beta beta beta gamma gamma delta", k=4)
    assert [[word for word, _, _ in page] for page in pages] == [["alpha", "beta"], ["gamma", "delta"]]


def test_cache_returns_the_same_object():
    cache.clear()
    first = keyword_report("alpha alpha beta", k=2)
    second = keyword_report("alpha alpha beta", k=2)
    assert first is second
    cache.clear()
