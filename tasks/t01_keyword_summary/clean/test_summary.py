from summary import keyword_summary


def test_counts_and_shares():
    result = keyword_summary("the cat and the hat and the bat", k=2)
    assert result["total"] == 8
    assert result["top"] == [("the", 3, 0.375), ("and", 2, 0.25)]


def test_ties_are_broken_by_word_order():
    result = keyword_summary("pear apple pear apple plum", k=2)
    assert result["total"] == 5
    assert result["top"] == [("apple", 2, 0.4), ("pear", 2, 0.4)]


def test_punctuation_and_case_are_ignored():
    result = keyword_summary("Dog! dog? DOG.", k=1)
    assert result["total"] == 3
    assert result["top"] == [("dog", 3, 1.0)]


def test_empty_text():
    assert keyword_summary("", k=3) == {"total": 0, "top": []}
