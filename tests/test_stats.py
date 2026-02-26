import math

from orchestration.write_ab_decision import diff_in_proportions_ci


def test_diff_in_proportions_ci_normal_case():
    # Control: 10% (10/100), Treatment: 12% (12/100)
    diff, lo, hi = diff_in_proportions_ci(0.10, 100, 0.12, 100)
    assert math.isclose(diff, 0.02, rel_tol=1e-9)
    assert lo is not None and hi is not None
    assert lo < diff < hi


def test_diff_in_proportions_ci_handles_zero_n():
    diff, lo, hi = diff_in_proportions_ci(0.0, 0, 0.2, 100)
    assert math.isclose(diff, 0.2, rel_tol=1e-9)
    assert lo is None and hi is None
