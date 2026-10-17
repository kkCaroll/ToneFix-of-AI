"""隐藏测试。覆盖可见测试没有走到的边界。"""

from report import keyword_report


def test_half_up_at_the_fourth_decimal():
    text = " ".join(["alpha"] * 29 + ["beta"] * 2 + ["gamma"])
    result = keyword_report(text, k=3, use_cache=False)
    assert [share for _, _, share in result["top"]] == [0.9063, 0.0625, 0.0313]


def test_half_up_on_a_rarer_word():
    text = " ".join(["alpha"] * 5 + ["beta"] * 27)
    result = keyword_report(text, k=2, use_cache=False)
    assert result["top"][-1][2] == 0.1563
