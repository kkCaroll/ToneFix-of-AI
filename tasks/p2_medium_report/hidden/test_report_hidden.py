from report import keyword_report, page_report


def test_three_way_tie_comes_out_in_word_order():
    result = keyword_report("delta charlie bravo alpha delta charlie", k=3)
    assert result["top"] == [("charlie", 2, 0.3333), ("delta", 2, 0.3333),
                             ("alpha", 1, 0.1667)]


def test_tie_order_after_dropping_stopwords():
    result = keyword_report("the yak and the zebra", k=2, drop_stopwords=True)
    assert result["top"] == [("yak", 1, 0.5), ("zebra", 1, 0.5)]


def test_paging_keeps_the_ranking_order():
    text = "alpha alpha beta beta gamma delta"
    assert page_report(text, k=4, size=1) == [
        [("alpha", 2, 0.3333)],
        [("beta", 2, 0.3333)],
        [("delta", 1, 0.1667)],
        [("gamma", 1, 0.1667)],
    ]


def test_page_count_rounds_up():
    assert page_report("alpha beta gamma", k=3, size=2)[-1] == [("gamma", 1, 0.3333)]
