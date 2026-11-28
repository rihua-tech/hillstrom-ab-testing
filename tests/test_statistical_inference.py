"""Deterministic tests for the frozen Phase 2 statistical methods."""

import math

import numpy as np
import pytest
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
)
from statsmodels.stats.proportion import (
    test_proportions_2indep as statsmodels_score_test,
)

from src.statistical_inference import (
    absolute_risk_difference,
    bias_mcse,
    fit_lin_and_unadjusted_hc3,
    holm_adjust,
    newcombe_risk_difference_interval,
    proportion_mcse,
    reference_diagnostic_bounds,
    score_test_risk_difference,
    variance_reduction,
)


def test_risk_difference_uses_treatment_minus_control_probability_scale():
    result = absolute_risk_difference(30, 1_000, 20, 1_000)

    assert result == pytest.approx(0.01)
    assert 100 * result == pytest.approx(1.0)


def test_score_test_agrees_with_pinned_statsmodels_call():
    result = score_test_risk_difference(300, 10_000, 240, 10_000)
    expected = statsmodels_score_test(
        300,
        10_000,
        240,
        10_000,
        compare="diff",
        method="score",
        alternative="two-sided",
        correction=True,
    )

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)


def test_newcombe_interval_agrees_with_pinned_statsmodels_call():
    result = newcombe_risk_difference_interval(300, 10_000, 240, 10_000)
    expected = confint_proportions_2indep(
        300,
        10_000,
        240,
        10_000,
        compare="diff",
        method="newcomb",
        alpha=0.05,
        correction=True,
    )

    assert (result.low, result.high) == pytest.approx(expected)


def test_holm_adjustment_and_strict_decisions_agree_with_statsmodels():
    p_values = (0.01, 0.04)
    result = holm_adjust(p_values)
    expected = multipletests(p_values, method="holm", alpha=0.05)

    assert result.reject == tuple(expected[0])
    assert result.adjusted_p_values == pytest.approx(expected[1])
    assert result.reject == (True, True)


def test_holm_decision_is_strict_at_adjusted_alpha():
    result = holm_adjust((0.025, 0.50))

    assert result.adjusted_p_values[0] == pytest.approx(0.05)
    assert result.reject == (False, False)


def test_lin_model_centers_at_pooled_mean_and_matches_explicit_statsmodels():
    assignments = np.repeat(np.arange(3), 8)
    covariate = np.tile((0, 0, 0, 0, 1, 1, 1, 1), 3)
    outcomes = np.array(
        [0, 0, 0, 1, 0, 1, 1, 1]
        + [0, 0, 1, 1, 1, 1, 1, 1]
        + [0, 0, 0, 0, 0, 0, 1, 1]
    )

    result = fit_lin_and_unadjusted_hc3(outcomes, assignments, covariate)

    pooled_mean = covariate.mean()
    centered = covariate - pooled_mean
    m = (assignments == 1).astype(float)
    w = (assignments == 2).astype(float)
    design = np.column_stack(
        (np.ones(outcomes.size), m, w, centered, m * centered, w * centered)
    )
    expected = sm.OLS(outcomes, design).fit(cov_type="HC3", use_t=False)
    assert result.pooled_x_mean == pytest.approx(0.5)
    for index, estimate in zip((1, 2), result.adjusted, strict=True):
        assert estimate.estimate == pytest.approx(expected.params[index])
        assert estimate.standard_error == pytest.approx(expected.bse[index])
        assert estimate.p_value == pytest.approx(expected.pvalues[index])
        assert estimate.ci_low < estimate.ci_high
    assert result.robust_inference_distribution == "normal"


def test_unadjusted_hc3_fit_uses_identical_experiment_and_expected_differences():
    assignments = np.repeat(np.arange(3), 8)
    covariate = np.tile((0, 0, 0, 0, 1, 1, 1, 1), 3)
    outcomes = np.array(
        [0, 0, 0, 1, 0, 1, 1, 1]
        + [0, 0, 1, 1, 1, 1, 1, 1]
        + [0, 0, 0, 0, 0, 0, 1, 1]
    )

    result = fit_lin_and_unadjusted_hc3(outcomes, assignments, covariate)

    assert result.unadjusted[0].estimate == pytest.approx(
        outcomes[8:16].mean() - outcomes[:8].mean()
    )
    assert result.unadjusted[1].estimate == pytest.approx(
        outcomes[16:].mean() - outcomes[:8].mean()
    )


def test_mcse_bias_and_diagnostic_formulas():
    assert proportion_mcse(0.05, 2_000) == pytest.approx(
        math.sqrt(0.05 * 0.95 / 2_000)
    )
    bounds = reference_diagnostic_bounds(0.95, 2_000)
    expected = 3 * math.sqrt(0.95 * 0.05 / 2_000)
    assert bounds.low == pytest.approx(0.95 - expected)
    assert bounds.high == pytest.approx(0.95 + expected)
    assert bias_mcse((-0.01, 0.0, 0.01)) == pytest.approx(
        np.std((-0.01, 0.0, 0.01), ddof=1) / math.sqrt(3)
    )


def test_variance_reduction_uses_comparable_hc3_standard_errors():
    assert variance_reduction(0.8, 1.0) == pytest.approx(0.36)
    assert variance_reduction(1.2, 1.0) == pytest.approx(-0.44)


@pytest.mark.parametrize(
    "call",
    [
        lambda: absolute_risk_difference(11, 10, 1, 10),
        lambda: score_test_risk_difference(1.5, 10, 1, 10),
        lambda: holm_adjust((0.2, float("nan"))),
        lambda: proportion_mcse(1.1, 100),
        lambda: variance_reduction(1.0, 0.0),
    ],
)
def test_invalid_statistical_inputs_raise(call):
    with pytest.raises((TypeError, ValueError)):
        call()


def test_rank_deficient_lin_design_raises_instead_of_hiding_failure():
    assignments = np.repeat(np.arange(3), 4)
    outcomes = np.tile((0, 1, 0, 1), 3)
    constant_covariate = np.zeros(12)

    with pytest.raises(ValueError, match="rank deficient"):
        fit_lin_and_unadjusted_hc3(outcomes, assignments, constant_covariate)

