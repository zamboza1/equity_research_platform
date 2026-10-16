import math

import pytest

from app.engine.macro_engine import MacroEngine


def test_slope_significance_matches_independent_three_point_reference():
    result = MacroEngine.perform_factor_regression([1, 0, 2], [-1, 0, 1], "factor")
    # OLS gives slope 1/2, R² 1/4 and t=1/√3 with one residual degree of freedom.
    # The df=1 Student t CDF is 1/2 + atan(t)/π, giving a two-sided p-value of 2/3.
    expected_p = 1 - 2 * math.atan(1 / math.sqrt(3)) / math.pi
    assert result.beta == pytest.approx(.5)
    assert result.r_squared == pytest.approx(.25)
    assert result.p_value == pytest.approx(expected_p)


def test_zero_slope_does_not_report_significance():
    result = MacroEngine.perform_factor_regression([1, -2, 1], [-1, 0, 1], "factor")
    assert result.beta == pytest.approx(0, abs=1e-12)
    assert result.p_value == pytest.approx(1)


@pytest.mark.parametrize("returns,factor", [([3, 5], [1, 2]), ([3, 3, 3], [1, 2, 3])])
def test_unavailable_inference_is_explicit(returns, factor):
    result = MacroEngine.perform_factor_regression(returns, factor, "factor")
    assert result.p_value is None


@pytest.mark.parametrize("returns,factor", [
    ([1], [1]),
    ([1, 2], [1, 2, 3]),
    ([1, 2, 3], [1, 1, 1]),
    ([1, float("nan"), 3], [1, 2, 3]),
    ([1, 2, 3], [1, float("inf"), 3]),
    ([[1], [2], [3]], [1, 2, 3]),
])
def test_invalid_regression_inputs_are_rejected(returns, factor):
    with pytest.raises(ValueError):
        MacroEngine.perform_factor_regression(returns, factor, "factor")
