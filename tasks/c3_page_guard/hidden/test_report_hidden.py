"""隐藏测试。覆盖可见测试没有走到的边界。"""

import pytest

from paging import page_count
from report import keyword_report


def test_page_count_rejects_non_positive_size():
    with pytest.raises(ValueError):
        page_count(5, 0)
    with pytest.raises(ValueError):
        page_count(5, -1)


def test_page_count_rounds_up():
    assert page_count(5, 2) == 3
    assert page_count(4, 2) == 2


def test_shares_use_token_total():
    result = keyword_report("alpha alpha alpha beta beta gamma", k=3, use_cache=False)
    assert [round(share, 4) for _, _, share in result["top"]] == [0.5, 0.3333, 0.1667]
