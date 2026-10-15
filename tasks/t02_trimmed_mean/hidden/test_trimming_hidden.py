from trimming import trim_report, trimmed_mean


def test_floor_rule_on_ten_values():
    values = [60, 12, 10, 9, 7, 6, 5, 3, 2, 1]
    assert trimmed_mean(values, 0.15) == 6.75


def test_floor_rule_on_six_values():
    values = [1, 2, 10, 3, 4, 40]
    assert trimmed_mean(values, 0.25) == 4.75


def test_zero_fraction_on_a_single_value():
    assert trimmed_mean([7], 0) == 7.0


def test_zero_fraction_on_two_values():
    assert trimmed_mean([2, 4], 0) == 3.0


def test_zero_fraction_on_unsorted_values():
    assert trimmed_mean([5, 1, 9, 3], 0) == 4.5


def test_quarter_fraction_on_four_values():
    assert trimmed_mean([1, 2, 3, 4], 0.25) == 2.5


def test_report_on_blank_text_raises():
    raised = False
    try:
        trim_report("   ", 0.1)
    except ValueError:
        raised = True
    assert raised


def test_report_whitespace_inside_the_text():
    report = trim_report("3, 1, 2", 0)
    assert report["n"] == 3
    assert report["trimmed"] == 2.0
