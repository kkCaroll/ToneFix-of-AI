from trimming import trim_report, trimmed_mean


def test_zero_fraction_matches_plain_mean():
    assert trimmed_mean([4, 1, 3, 2], 0) == 2.5


def test_trimming_uses_floor_not_round():
    values = [100, 10, 9, 8, 7, 6, 5, 4, 2, 1]
    assert trimmed_mean(values, 0.15) == 6.375


def test_report_with_zero_fraction():
    assert trim_report("1,2,3,4", 0) == {"n": 4, "mean": 2.5, "trimmed": 2.5}


def test_twenty_percent_on_five_values():
    assert trimmed_mean([1, 2, 3, 4, 100], 0.2) == 3.0


def test_unsorted_input_is_sorted_before_trimming():
    assert trimmed_mean([9, 1, 5], 0.3) == 5.0


def test_report_includes_count():
    report = trim_report("5, 5, 5, 5, 5", 0.2)
    assert report["n"] == 5
    assert report["mean"] == 5.0
