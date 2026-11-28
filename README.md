# Marketing Campaign A/B/n Testing & Causal Impact Analysis

**Dataset:** Hillstrom / MineThatData Email Marketing Experiment (~64,000 randomized customers; three arms)  
**Focus:** Randomized experimentation, statistical inference, causal ITT estimates, and business decision-making  
**Stack (implementation phases):** Python, SQL, pandas, SciPy, statsmodels  
**Project status:** Phases 0–1 complete. Phase 2 synthetic validation implemented
and ready for independent review; Issue #4 outcome inference has not begun.

## Business question

**Do promotional emails actually make more customers buy, and when is sending them worth the cost?**

Specifically: compared with no email, how does each promotion (men's and women's) affect two-week purchase conversion, and under what margin and sending-cost assumptions is it worth sending?

Formal estimands: [Analysis Plan §3](01-experiment-analysis-plan.md#3-estimands-primary-metric-and-hypotheses).

## Project at a glance

- **Primary outcome:** Two-week purchase conversion among all randomized customers (ITT).
- **Comparison:** Men's and women's merchandise emails **separately** versus randomized no-email Control (not a confirmatory head-to-head email comparison).
- **Core methods:** Two-proportion score tests, effect sizes, individual 95% confidence intervals, Holm family-wise correction, and regression-adjusted precision analysis.
- **Validation:** SRM / baseline balance, synthetic A/A and known-effect simulations, documented plan changes and limitations.
- **Decision output:** Conditional incremental-contribution scenarios from estimated revenue, **assumed** margins and email costs; no fabricated ROI or observed profit claims.

## Analysis integrity

The original plan was preserved in the [first Git commit](https://github.com/rihua-tech/hillstrom-ab-testing/commit/d6fe8f00970805510cfc0af36483a14e486d09f9) before this project's **treatment-arm outcome analysis**. The v1.1 amendment was then preserved in a [separate commit](https://github.com/rihua-tech/hillstrom-ab-testing/commit/258866fd23f3b82c07827f55bd0f37467d941295) and annotated tag, `plan-v1.1`. This is a **pre-specified analysis plan for a historical public experiment**, **not** an original-trial pre-registration. A prior AI-assistant remark about an **unverified pooled conversion rate (~0.9%)** is explicitly disclosed; the v1.1 methodological supplements were selected after that limited pooled-outcome exposure. Confirmation that no arm-level results were examined before the freezes remains a **user attestation**, not something independently verifiable from code or Git history. This later edit only reconciles outdated documentation status after the `plan-v1.1` tag.

Read **[`01-experiment-analysis-plan.md`](01-experiment-analysis-plan.md)** for the locked estimands, primary tests and Holm rule, supplementary MDE scenarios, regression adjustment, simulation validation, and change log.

## Repository map

| Path | Purpose | Current state |
| --- | --- | --- |
| `01-experiment-analysis-plan.md` | Pre-specified plan + versioned pre-arm-level-outcome amendment | v1.0 and v1.1 committed; v1.1 tagged |
| `data/README.md` | Provenance policy; no dataset included | Present |
| `src/` | Reusable validation and inference modules | Phases 1–2 implemented |
| `tests/` | Unit and deterministic simulation tests | Phases 1–2 implemented |
| `sql/` | Independent data-quality reconciliation | Phase 1 implemented |
| `reports/` | Audit and synthetic-validation reports | Phases 1–2 implemented |
| `figures/` | Future final result figures | Empty |
| `.gitignore`, `.editorconfig` | Minimal project hygiene | Present |

## Phase 2 synthetic validation

The reusable inference code and all six frozen synthetic scenarios are implemented.
See the [simulation validation report](reports/simulation-validation.md) and
[machine-readable results](reports/simulation-results.json). These artifacts contain
synthetic results only and do not expose or calibrate to Hillstrom treatment-arm
outcomes. Independent statistical and technical acceptance is still required before
Issue #4.

Reproduce the full 2,000-replication workflow separately from CI:

```powershell
.\.venv\Scripts\python.exe -m src.simulate_experiments
```

## Phase boundaries

**Phase 0:** Complete. The original baseline and the separately documented **v1.1 methodological supplement** were recorded in Git, with v1.1 tagged `plan-v1.1`. Project records state that no dataset was downloaded or analyzed in Phase 0; confirmation of no prior arm-level outcome inspection remains a user-attestation item. Limited exposure to an unverified pooled-rate remark is disclosed.

**Phases 1–2:** Data validation/SRM is complete. Synthetic simulation validation is
implemented and awaiting independent review.

**Phases 3–5 (not started):** Primary and secondary A/B/n inference (including
adjustment/subgroups) → business memo → reproducible portfolio release. Each phase
requires review before moving forward. The project stops at portfolio release; a
dashboard, API, and web app are deliberately out of scope.

## Dataset attribution

Original experiment: Kevin Hillstrom, *MineThatData E-Mail Analytics And Data Mining Challenge* (2008): https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html

Data-dictionary reference: https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html

No raw data have been downloaded or analyzed for this project in Phase 0. The eventual download source, timestamp, usage terms and SHA-256 checksum will be documented in Phase 1. Raw data are intentionally excluded from the repository.

## Reproducing analysis

Not yet available. Environment setup, dependency versions, execution commands, and testing instructions will be added in the implementation phases **after the completed Phase 0 plan freeze**. No provisional results or notebooks are published at Phase 0.
