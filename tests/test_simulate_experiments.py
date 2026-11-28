"""Small deterministic checks for synthetic scenario construction and summaries."""

from types import SimpleNamespace

import numpy as np
import pytest

from src import simulate_experiments
from src.simulate_experiments import (
    ALLOCATION,
    MASTER_SEED,
    _run_unadjusted_aa,
    _summarize_known_effect,
    conditional_probabilities,
    fixed_assignments,
    marginal_probabilities,
    run_all_scenarios,
    simulate_unadjusted_counts,
)


def test_fixed_allocation_and_shared_three_arm_construction():
    assignments = fixed_assignments()

    assert tuple(np.bincount(assignments)) == ALLOCATION
    assert assignments.size == 64_000


def test_conditional_probabilities_are_valid_and_have_locked_margins():
    known_effect = conditional_probabilities(0.02)
    adjusted_aa = conditional_probabilities(0.01, (0.0, 0.0))

    assert np.all((known_effect >= 0) & (known_effect <= 1))
    assert known_effect == pytest.approx(
        np.array(((0.002, 0.182), (0.007, 0.187), (0.002, 0.182)))
    )
    assert marginal_probabilities(known_effect) == pytest.approx(
        (0.02, 0.025, 0.02)
    )
    assert marginal_probabilities(adjusted_aa) == pytest.approx((0.01,) * 3)


def test_unadjusted_generator_returns_one_joint_three_arm_experiment():
    first = simulate_unadjusted_counts(np.random.default_rng(123), (0.01,) * 3)
    second = simulate_unadjusted_counts(np.random.default_rng(123), (0.01,) * 3)

    assert first.shape == (3,)
    assert np.array_equal(first, second)


def test_both_contrasts_receive_the_same_control_count(monkeypatch):
    controls = []

    def fake_score(t_count, t_n, c_count, c_n):
        controls.append((c_count, c_n))
        return SimpleNamespace(p_value=0.5)

    monkeypatch.setattr(simulate_experiments, "score_test_risk_difference", fake_score)
    _run_unadjusted_aa(np.random.default_rng(10), 0.01, 2)

    assert controls[0] == controls[1]
    assert controls[2] == controls[3]


def test_fpr_and_fwer_are_replication_event_rates_not_averages(monkeypatch):
    p_values = iter((0.01, 0.01, 0.03, 0.80, 0.80, 0.80, 0.80, 0.80))

    def fake_score(*args):
        return SimpleNamespace(p_value=next(p_values))

    monkeypatch.setattr(simulate_experiments, "score_test_risk_difference", fake_score)
    result = _run_unadjusted_aa(np.random.default_rng(11), 0.01, 4)

    assert result["comparisons"]["M - Control"]["rejection_count"] == 2
    assert result["comparisons"]["W - Control"]["rejection_count"] == 1
    assert result["holm_fwer"]["rejection_count"] == 1
    assert result["holm_fwer"]["rate"] == pytest.approx(0.25)


def test_coverage_checks_truth_not_zero():
    summary = _summarize_known_effect(
        estimates=np.array((0.004, 0.006)),
        lows=np.array((0.003, 0.004)),
        highs=np.array((0.007, 0.008)),
        true_effect=0.005,
    )

    assert summary["coverage"] == 1.0
    assert summary["coverage_count"] == 2


def test_fixed_seed_reproduces_every_small_scenario_exactly():
    first = run_all_scenarios(master_seed=MASTER_SEED, replications=3)
    second = run_all_scenarios(master_seed=MASTER_SEED, replications=3)

    assert first == second
    assert tuple(first["scenarios"]) == ("A1", "A2", "A3", "B", "C", "D")
    assert first["design"]["shared_control_within_replication"] is True
    assert "SYNTHETIC" in first["label"]


@pytest.mark.parametrize(
    ("seed", "replications"),
    [(-1, 2), (MASTER_SEED, 1), (MASTER_SEED, 2.5)],
)
def test_invalid_simulation_controls_raise(seed, replications):
    with pytest.raises(ValueError):
        run_all_scenarios(master_seed=seed, replications=replications)


def test_invalid_probability_inputs_raise():
    with pytest.raises(ValueError):
        conditional_probabilities(0.5)
    with pytest.raises(ValueError):
        marginal_probabilities(np.ones((2, 2)))
    with pytest.raises(ValueError):
        simulate_unadjusted_counts(np.random.default_rng(1), (0.1, 0.2))
