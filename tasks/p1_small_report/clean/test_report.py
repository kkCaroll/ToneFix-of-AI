from report import keyword_report


def test_counts_and_shares():
    result = keyword_report("the cat and the hat and the bat", k=2)
    assert result["count"] == 8
    assert result["top"] == [("the", 3, 0.375), ("and", 2, 0.25)]


def test_ties_break_by_word_order():
    result = keyword_report("pear apple pear apple plum", k=2)
    assert result["top"] == [("apple", 2, 0.4), ("pear", 2, 0.4)]


def test_empty_text():
    assert keyword_report("", k=3) == {"count": 0, "top": []}
