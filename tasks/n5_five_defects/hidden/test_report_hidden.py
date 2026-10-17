"""隐藏测试。覆盖与可见测试相同的行为，输入不同。"""

from report import keyword_report, page_report


def test_tie_order_hidden():
    result = keyword_report("kiwi plum kiwi plum fig", k=2, use_cache=False)
    assert [word for word, _, _ in result["top"]] == ["kiwi", "plum"]


def test_share_denominator_hidden():
    text = "red red red red green green green blue blue yellow"
    result = keyword_report(text, k=4, use_cache=False)
    assert [round(share, 4) for _, _, share in result["top"]] == [0.4, 0.3, 0.2, 0.1]


def test_token_count_hidden():
    result = keyword_report("Hello, world! Hello.", k=2, use_cache=False)
    assert result["count"] == 3


def test_hyphen_hidden():
    result = keyword_report("state-of-the-art state-of-the-art plain", k=2, use_cache=False)
    assert result["count"] == 3
    assert result["top"][0][0] == "state-of-the-art"


def test_default_k_hidden():
    result = keyword_report("a b c d e f", use_cache=False)
    assert len(result["top"]) == 3


def test_stopwords_hidden():
    result = keyword_report("a cat and a dog", k=2, drop_stopwords=True, use_cache=False)
    assert result["count"] == 2


def test_page_count_hidden():
    pages = page_report("x x x y y z", k=3, size=2)
    assert [[word for word, _, _ in page] for page in pages] == [["x", "y"], ["z"]]


def test_page_size_hidden():
    pages = page_report("x x x x y y y z z w", k=4)
    assert [[word for word, _, _ in page] for page in pages] == [["x", "y"], ["z", "w"]]
