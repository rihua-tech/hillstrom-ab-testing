# Phase 2 Statistical Simulation Validation

> **SYNTHETIC SIMULATION RESULTS — NO HILLSTROM OUTCOMES USED.**

## Design and methods

Master seed: `20261113`. Replications: 2,000 per scenario. Allocation: Control/M/W = 21,334/21,333/21,333 (64,000 total).

Each scenario uses its own deterministic child stream spawned from the master seed. Both contrasts share the same Control sample in every replication. Risk differences use treatment minus Control. Percentage points appear only as presentation units.

The score-test wrapper explicitly uses the statsmodels 0.14.6 default small-sample correction (`correction=True`). HC3 robust OLS explicitly uses normal inference (`use_t=False`). The confirmatory rule remains Holm-adjusted p < 0.05; individual intervals are not simultaneous.

A five-replication benchmark of the direct 64,000-row adjusted and unadjusted statsmodels fits had a 0.0376-second median, projecting about 2.5 minutes for 4,000 regression replications. Because that was below the 30-minute optimization threshold, the workflow retains direct row-level OLS/HC3 and uses no custom sufficient-statistic shortcut.

## A1–A3: unadjusted A/A diagnostics

| Scenario | p | Measure | Rejections / 2,000 | Rate | MCSE | Diagnostic bounds | Status |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| A1 | 0.005 | M - Control FPR | 98 / 2000 | 4.900% | 0.483% | 3.538%–6.462% | PASS |
| A1 | 0.005 | W - Control FPR | 98 / 2000 | 4.900% | 0.483% | 3.538%–6.462% | PASS |
| A1 | 0.005 | two-test Holm FWER | 92 / 2000 | 4.600% | 0.468% | ≤ 6.462% | PASS |
| A2 | 0.010 | M - Control FPR | 92 / 2000 | 4.600% | 0.468% | 3.538%–6.462% | PASS |
| A2 | 0.010 | W - Control FPR | 89 / 2000 | 4.450% | 0.461% | 3.538%–6.462% | PASS |
| A2 | 0.010 | two-test Holm FWER | 86 / 2000 | 4.300% | 0.454% | ≤ 6.462% | PASS |
| A3 | 0.020 | M - Control FPR | 112 / 2000 | 5.600% | 0.514% | 3.538%–6.462% | PASS |
| A3 | 0.020 | W - Control FPR | 86 / 2000 | 4.300% | 0.454% | 3.538%–6.462% | PASS |
| A3 | 0.020 | two-test Holm FWER | 80 / 2000 | 4.000% | 0.438% | ≤ 6.462% | PASS |

FWER is the fraction of replications with at least one Holm rejection, not the average individual rejection rate. Conservative FWER is not a failure.

## B: unadjusted known-effect validation

| Contrast | True RD | Mean RD | Bias (MCSE) | Empirical SD | Mean CI width | Coverage (count) | MCSE | Bounds | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M - Control | 0.0050000 | 0.0049553 | -0.0000447 (0.0000324) | 0.0014470 | 0.0056343 | 94.550% (1891/2000) | 0.508% | 93.538%–96.462% | PASS |
| W - Control | 0.0000000 | -0.0000247 | -0.0000247 (0.0000300) | 0.0013418 | 0.0053218 | 95.200% (1904/2000) | 0.478% | 93.538%–96.462% | PASS |

Coverage tests whether each individual Newcombe interval contains its true risk difference; it does not test whether the interval contains zero.

## C: regression-adjusted known-effect validation

The fixed DGP uses P(X=1)=0.10. Conditional probabilities are Control/W: 0.002 at X=0 and 0.182 at X=1; M: 0.007 and 0.187. All are valid, and analytic marginal probabilities are 0.020, 0.025, and 0.020.

| Contrast | Model | Mean RD | Bias (MCSE) | Empirical SD | Mean HC3 SE | Coverage (MCSE) | Diagnostics | Model VR | Empirical VR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| M - Control | Lin/HC3 | 0.0050330 | 0.0000330 (0.0000303) | 0.0013532 | 0.0013380 | 94.900% (0.492%) | bias PASS; coverage PASS | 13.209% | 13.094% |
| M - Control | Unadjusted HC3 | 0.0050516 | 0.0000516 (0.0000325) | 0.0014515 | 0.0014364 | 94.650% (0.503%) | bias PASS; coverage PASS | — | — |
| W - Control | Lin/HC3 | -0.0000172 | -0.0000172 (0.0000282) | 0.0012596 | 0.0012510 | 95.000% (0.487%) | bias PASS; coverage PASS | 14.765% | 14.212% |
| W - Control | Unadjusted HC3 | -0.0000107 | -0.0000107 (0.0000304) | 0.0013600 | 0.0013552 | 94.400% (0.514%) | bias PASS; coverage PASS | — | — |

Model-based variance reduction is calculated within each replication as `1 - (SE_adjusted / SE_unadjusted_HC3)^2` and then averaged. Empirical sampling-variance reduction instead compares the across-replication standard deviations. The predictive synthetic covariate was deliberately constructed for this validation; the gain is not an expectation for the real Hillstrom experiment, and no minimum gain was required.

## D: regression-adjusted A/A diagnostics

The fixed conditional probabilities are 0.001 at X=0 and 0.091 at X=1 in every arm, yielding analytic marginal p=0.010.

| Measure | Rejections / 2,000 | Rate | MCSE | Diagnostic bounds | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| M - Control FPR | 105 / 2000 | 5.250% | 0.499% | 3.538%–6.462% | PASS |
| W - Control FPR | 110 / 2000 | 5.500% | 0.510% | 3.538%–6.462% | PASS |
| two-test Holm FWER | 91 / 2000 | 4.550% | 0.466% | ≤ 6.462% | PASS |

Regression-adjusted analyses are secondary and do not replace the locked unadjusted score tests or Holm confirmatory rule.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m src.simulate_experiments
```

This command regenerates both this report and `reports/simulation-results.json` from the same calculations. CI runs small deterministic pytest simulations; the 2,000-replication workflow is intentionally separate.

## Limitations and readiness

These Monte Carlo diagnostics validate implementation behavior under the six specified synthetic DGPs only. They do not validate external validity, business value, real-data quality, or expected precision gain on Hillstrom data. Three-MC-SE bounds are diagnostics, not additional confirmatory tests.

No required diagnostic is outside its frozen bound, and no unresolved statistical or numerical concern was observed.

## Issue #3 acceptance checklist

| Criterion | Status | Evidence |
| --- | --- | --- |
| Seed 20261113, 2,000 replications, 64,000 customers | Met | Design metadata and all scenario denominators |
| Three unadjusted A/A scenarios with shared Control | Met | A1–A3 FPR and Holm FWER tables |
| Known-effect bias and individual Newcombe coverage | Met | Scenario B table |
| Predictive-covariate fully interacted Lin/HC3 validation | Met | Scenario C table |
| Adjusted A/A FPR and Holm FWER | Met | Scenario D table |
| MCSEs, three-MC-SE tolerances, bias, coverage, precision, tests | Met | This report, JSON artifact, and pytest suite |
| Optional nonpredictive-covariate negative control | Optional — deferred | Explicitly out of current required scope |
| Optional empirical power/MDE supplement | Optional — deferred | Frozen design-based MDE remains unchanged |
| All required scenarios reproducible with diagnostics | Met | Single documented command and fixed child RNG streams |
| Shared dependence, individual CIs, and Holm FWER handled correctly | Met | Joint experiments and focused deterministic tests |
| Adjusted analyses remain secondary; issues investigated | Met | Secondary label retained; no unresolved diagnostic failures |

**Phase 2 assessment: READY FOR INDEPENDENT REVIEW.** Independent statistical and technical acceptance is required before Issue #4.
