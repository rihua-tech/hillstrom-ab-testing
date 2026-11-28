"""Frozen Phase 2 statistical methods for synthetic validation.

All contrasts use treatment minus Control.  The confirmatory wrappers pin the
statsmodels APIs named in the frozen ``plan-v1.1`` analysis contract.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt

import numpy as np
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    test_proportions_2indep,
)

ALPHA = 0.05
Z_975 = float(norm.ppf(1 - ALPHA / 2))


@dataclass(frozen=True)
class TestResult:
    statistic: float
    p_value: float


@dataclass(frozen=True)
class Interval:
    low: float
    high: float


@dataclass(frozen=True)
class HolmResult:
    reject: tuple[bool, ...]
    adjusted_p_values: tuple[float, ...]


@dataclass(frozen=True)
class RegressionEstimate:
    estimate: float
    standard_error: float
    ci_low: float
    ci_high: float
    p_value: float


@dataclass(frozen=True)
class RegressionResults:
    adjusted: tuple[RegressionEstimate, RegressionEstimate]
    unadjusted: tuple[RegressionEstimate, RegressionEstimate]
    pooled_x_mean: float
    robust_inference_distribution: str = "normal"


def _validate_binomial(successes: int, observations: int) -> None:
    if not isinstance(successes, (int, np.integer)) or not isinstance(
        observations, (int, np.integer)
    ):
        raise TypeError("successes and observations must be integers")
    if observations <= 0:
        raise ValueError("observations must be positive")
    if not 0 <= successes <= observations:
        raise ValueError("successes must be between zero and observations")


def absolute_risk_difference(
    treatment_successes: int,
    treatment_observations: int,
    control_successes: int,
    control_observations: int,
) -> float:
    """Return treatment minus Control on the probability scale."""
    _validate_binomial(treatment_successes, treatment_observations)
    _validate_binomial(control_successes, control_observations)
    return (
        treatment_successes / treatment_observations
        - control_successes / control_observations
    )


def score_test_risk_difference(
    treatment_successes: int,
    treatment_observations: int,
    control_successes: int,
    control_observations: int,
) -> TestResult:
    """Run the locked two-sided score test for a zero risk difference.

    statsmodels 0.14.6 defaults ``correction=True`` for this API.  We pass it
    explicitly so the small-sample correction cannot change silently.
    """
    _validate_binomial(treatment_successes, treatment_observations)
    _validate_binomial(control_successes, control_observations)
    result = test_proportions_2indep(
        treatment_successes,
        treatment_observations,
        control_successes,
        control_observations,
        compare="diff",
        method="score",
        alternative="two-sided",
        correction=True,
    )
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    if not np.isfinite(statistic) or not np.isfinite(p_value):
        raise ArithmeticError("score test returned a non-finite result")
    return TestResult(statistic=statistic, p_value=p_value)


def newcombe_risk_difference_interval(
    treatment_successes: int,
    treatment_observations: int,
    control_successes: int,
    control_observations: int,
    *,
    alpha: float = ALPHA,
) -> Interval:
    """Return the individual Newcombe interval for treatment minus Control."""
    _validate_binomial(treatment_successes, treatment_observations)
    _validate_binomial(control_successes, control_observations)
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between zero and one")
    low, high = confint_proportions_2indep(
        treatment_successes,
        treatment_observations,
        control_successes,
        control_observations,
        compare="diff",
        method="newcomb",
        alpha=alpha,
        correction=True,
    )
    low = float(low)
    high = float(high)
    if not np.isfinite(low) or not np.isfinite(high) or low > high:
        raise ArithmeticError("Newcombe interval returned an invalid result")
    return Interval(low=low, high=high)


def holm_adjust(p_values: Sequence[float], *, alpha: float = ALPHA) -> HolmResult:
    """Apply the locked Holm correction to an explicitly supplied family."""
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("p_values must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError("p_values must be finite and between zero and one")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between zero and one")
    _, adjusted, _, _ = multipletests(values, alpha=alpha, method="holm")
    return HolmResult(
        # The frozen decision rule is explicitly adjusted p < alpha.
        reject=tuple(bool(value < alpha) for value in adjusted),
        adjusted_p_values=tuple(float(value) for value in adjusted),
    )


def _regression_estimate(
    result, parameter_index: int, alpha: float
) -> RegressionEstimate:
    estimate = float(result.params[parameter_index])
    standard_error = float(result.bse[parameter_index])
    p_value = float(result.pvalues[parameter_index])
    critical = float(norm.ppf(1 - alpha / 2))
    values = (estimate, standard_error, p_value)
    if not all(np.isfinite(value) for value in values) or standard_error <= 0:
        raise ArithmeticError("HC3 regression returned an invalid treatment estimate")
    return RegressionEstimate(
        estimate=estimate,
        standard_error=standard_error,
        ci_low=estimate - critical * standard_error,
        ci_high=estimate + critical * standard_error,
        p_value=p_value,
    )


def fit_lin_and_unadjusted_hc3(
    outcomes: np.ndarray,
    assignments: np.ndarray,
    covariate: np.ndarray,
    *,
    alpha: float = ALPHA,
) -> RegressionResults:
    """Fit locked Lin-style and comparable unadjusted LPMs with HC3.

    Assignment codes must be 0=Control, 1=M, and 2=W.  The binary synthetic
    covariate is centered at its pooled sample mean.  statsmodels robust fits
    use the normal reference distribution by default (``use_t=False``), which
    is asserted here and used for the supporting individual intervals.
    """
    y = np.asarray(outcomes, dtype=float)
    arm = np.asarray(assignments)
    x = np.asarray(covariate, dtype=float)
    if y.ndim != 1 or arm.ndim != 1 or x.ndim != 1:
        raise ValueError("outcomes, assignments, and covariate must be vectors")
    if not (y.size == arm.size == x.size) or y.size == 0:
        raise ValueError("input vectors must have the same positive length")
    if not np.all(np.isin(y, (0, 1))):
        raise ValueError("outcomes must be binary")
    if not np.all(np.isin(arm, (0, 1, 2))):
        raise ValueError("assignments must use codes 0, 1, and 2")
    if not np.all(np.isin(x, (0, 1))):
        raise ValueError("covariate must be binary")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between zero and one")
    if any(np.count_nonzero(arm == code) < 2 for code in (0, 1, 2)):
        raise ValueError("each assignment arm must contain at least two rows")

    pooled_mean = float(x.mean())
    centered = x - pooled_mean
    m = (arm == 1).astype(float)
    w = (arm == 2).astype(float)
    adjusted_design = np.column_stack(
        (np.ones(y.size), m, w, centered, m * centered, w * centered)
    )
    if np.linalg.matrix_rank(adjusted_design) != adjusted_design.shape[1]:
        raise ValueError("adjusted design matrix is rank deficient")
    unadjusted_design = adjusted_design[:, :3]

    adjusted_fit = sm.OLS(y, adjusted_design).fit(cov_type="HC3", use_t=False)
    unadjusted_fit = sm.OLS(y, unadjusted_design).fit(
        cov_type="HC3", use_t=False
    )
    if adjusted_fit.use_t or unadjusted_fit.use_t:
        raise AssertionError("robust inference unexpectedly used a t distribution")

    return RegressionResults(
        adjusted=tuple(
            _regression_estimate(adjusted_fit, index, alpha) for index in (1, 2)
        ),
        unadjusted=tuple(
            _regression_estimate(unadjusted_fit, index, alpha) for index in (1, 2)
        ),
        pooled_x_mean=pooled_mean,
    )


def proportion_mcse(proportion: float, replications: int) -> float:
    if not 0 <= proportion <= 1:
        raise ValueError("proportion must be between zero and one")
    if not isinstance(replications, (int, np.integer)) or replications <= 0:
        raise ValueError("replications must be a positive integer")
    return sqrt(proportion * (1 - proportion) / replications)


def reference_diagnostic_bounds(
    reference: float, replications: int, *, mcse_multiplier: float = 3
) -> Interval:
    if mcse_multiplier <= 0:
        raise ValueError("mcse_multiplier must be positive")
    uncertainty = mcse_multiplier * proportion_mcse(reference, replications)
    return Interval(
        low=max(0.0, reference - uncertainty),
        high=min(1.0, reference + uncertainty),
    )


def bias_mcse(errors: Sequence[float]) -> float:
    values = np.asarray(errors, dtype=float)
    if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)):
        raise ValueError("errors must contain at least two finite values")
    return float(values.std(ddof=1) / sqrt(values.size))


def variance_reduction(adjusted_se: float, unadjusted_hc3_se: float) -> float:
    """Return the frozen comparable-HC3 model-based variance reduction."""
    if not np.isfinite(adjusted_se) or adjusted_se < 0:
        raise ValueError("adjusted_se must be finite and nonnegative")
    if not np.isfinite(unadjusted_hc3_se) or unadjusted_hc3_se <= 0:
        raise ValueError("unadjusted_hc3_se must be finite and positive")
    return 1 - (adjusted_se / unadjusted_hc3_se) ** 2
