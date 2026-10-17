from report import keyword_report


def test_three_way_tie_comes_out_in_word_order():
    result = keyword_report("delta charlie bravo alpha delta charlie", k=3)
    assert result["top"] == [("charlie", 2, 0.3333), ("delta", 2, 0.3333),
                             ("alpha", 1, 0.1667)]


def test_hyphenated_token_is_one_word():
    result = keyword_report("well-known well-known well", k=2)
    assert result["count"] == 3
    assert result["top"][0] == ("well-known", 2, 0.6667)


def test_k_larger_than_vocabulary():
    result = keyword_report("solo solo", k=5)
    assert result["top"] == [("solo", 2, 1.0)]
