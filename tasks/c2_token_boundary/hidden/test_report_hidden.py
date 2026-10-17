"""隐藏测试。覆盖可见测试没有走到的边界。"""

from report import keyword_report


def test_trailing_hyphen_is_not_part_of_token():
    result = keyword_report("cut- let's go", k=3, use_cache=False)
    assert sorted(word for word, _, _ in result["top"]) == ["cut", "go", "let's"]


def test_trailing_apostrophe_is_not_part_of_token():
    result = keyword_report("dogs' dogs' cats", k=2, use_cache=False)
    assert result["count"] == 3
    assert result["top"][0][0] == "dogs"


def test_apostrophe_inside_a_word_stays():
    result = keyword_report("don't don't stop", k=2, use_cache=False)
    assert result["top"][0][0] == "don't"
