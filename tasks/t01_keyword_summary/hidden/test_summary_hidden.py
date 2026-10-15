from summary import keyword_summary


def test_tie_order_on_a_larger_vocabulary():
    result = keyword_summary("zebra yak yak zebra ant", k=2)
    assert result["top"] == [("yak", 2, 0.4), ("zebra", 2, 0.4)]


def test_all_tied_words_come_out_in_word_order():
    result = keyword_summary("delta charlie bravo alpha", k=4)
    assert result["top"] == [("alpha", 1, 0.25), ("bravo", 1, 0.25),
                             ("charlie", 1, 0.25), ("delta", 1, 0.25)]


def test_hyphen_splits_into_two_tokens():
    result = keyword_summary("well-known well known", k=2)
    assert result["total"] == 4
    assert result["top"] == [("known", 2, 0.5), ("well", 2, 0.5)]


def test_apostrophe_is_kept_inside_a_token():
    result = keyword_summary("don't don't cant", k=2)
    assert result["total"] == 3
    assert result["top"] == [("don't", 2, 0.6667), ("cant", 1, 0.3333)]


def test_k_zero_gives_empty_top():
    result = keyword_summary("alpha alpha beta", k=0)
    assert result["total"] == 3
    assert result["top"] == []


def test_share_rounding_to_four_places():
    result = keyword_summary("alpha bravo charlie delta echo foxtrot golf", k=1)
    assert result["top"] == [("alpha", 1, 0.1429)]
