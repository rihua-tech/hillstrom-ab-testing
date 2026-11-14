# Marketing Campaign A/B/n Testing & Causal Impact Analysis

**Dataset:** Hillstrom / MineThatData Email Marketing Experiment (~64,000 randomized customers; three arms)  
**Focus:** Randomized experimentation, statistical inference, causal ITT estimates, and business decision-making  
**Stack (implementation phases):** Python, SQL, pandas, SciPy, statsmodels  
**Project status:** **Phase 0 baseline committed; v1.1 plan supplement pending commit. No treatment-arm outcomes analyzed.**

## Research question

> What is the causal effect of assigning customers to each merchandise-promotion email on two-week purchase conversion versus no email, and under what assumed margins and email costs might each strategy generate positive incremental contribution?

## Project at a glance

- **Primary outcome:** Two-week purchase conversion among all randomized customers (ITT).
- **Comparison:** Men's and women's merchandise emails **separately** versus randomized no-email Control (not a confirmatory head-to-head email comparison).
- **Core methods:** Two-proportion score tests, effect sizes, individual 95% confidence intervals, Holm family-wise correction, and regression-adjusted precision analysis.
- **Validation:** SRM / baseline balance, synthetic A/A and known-effect simulations, documented plan changes and limitations.
- **Decision output:** Conditional incremental-contribution scenarios from estimated revenue, **assumed** margins and email costs; no fabricated ROI or observed profit claims.

## Analysis integrity

The original plan was preserved in the [first Git commit](https://github.com/rihua-tech/hillstrom-ab-testing/commit/d6fe8f00970805510cfc0af36483a14e486d09f9) before this project's **treatment-arm outcome analysis**. This is a **pre-specified analysis plan for a historical public experiment**, **not** an original-trial pre-registration. A prior AI-assistant remark about an **unverified pooled conversion rate (~0.9%)** is explicitly disclosed; no arm-level results have been examined. Proposed v1.1 additions are documented separately and must be committed before outcome analysis.

Read **[`01-experiment-analysis-plan.md`](01-experiment-analysis-plan.md)** for the locked estimands, primary tests and Holm rule, supplementary MDE scenarios, regression adjustment, simulation validation, and change log.

## Repository map

| Path | Purpose | Phase 0 state |
| --- | --- | --- |
| `01-experiment-analysis-plan.md` | Pre-specified plan + versioned pre-arm-level-outcome amendment | Original committed; v1.1 pending |
| `data/README.md` | Provenance policy; no dataset included | Present |
| `src/` | Future reusable analysis modules | Empty |
| `tests/` | Future unit and simulation tests | Empty |
| `sql/` | Future independent data-quality reconciliation | Empty |
| `reports/` | Future business decision memo | Empty |
| `figures/` | Future final result figures | Empty |
| `.gitignore`, `.editorconfig` | Minimal project hygiene | Present |

## Phase boundaries

**Phase 0:** Original baseline recorded in Git; current task is the separately documented **v1.1 methodological supplement** (commit + push before arm-level outcome access). No dataset was downloaded or analyzed in Phase 0; limited exposure to an unverified pooled-rate remark is disclosed.

**Phases 1–5 (later):** Data validation/SRM → synthetic simulation validation → primary and secondary A/B/n inference (including adjustment/subgroups) → business memo → reproducible portfolio release. Each phase requires review before moving forward. The project stops at portfolio release; a dashboard, API, and web app are deliberately out of scope.

## Dataset attribution

Original experiment: Kevin Hillstrom, *MineThatData E-Mail Analytics And Data Mining Challenge* (2008): https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html

Data-dictionary reference: https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html

No raw data have been downloaded or analyzed for this project in Phase 0. The eventual download source, timestamp, usage terms and SHA-256 checksum will be documented in Phase 1. Raw data are intentionally excluded from the repository.

## Reproducing analysis

Not yet available. Environment setup, dependency versions, execution commands, and testing instructions will be added in the implementation phases **after the analysis plan is committed**. No provisional results or notebooks are published at Phase 0.
