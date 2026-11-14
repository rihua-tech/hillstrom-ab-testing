# Marketing Campaign A/B/n Testing & Causal Impact Analysis

**Dataset:** Hillstrom / MineThatData Email Marketing Experiment (~64,000 randomized customers; three arms)  
**Focus:** Randomized experimentation, statistical inference, causal ITT estimates, and business decision-making  
**Stack (implementation phases):** Python, SQL, pandas, SciPy, statsmodels  
**Project status:** **Phase 0 — outcome-blind planning; no experimental results analyzed**

## Research question

> Do merchandise-promotion emails causally increase customer conversion, and under what business cost and margin assumptions would the incremental impact justify a campaign?

## Analysis integrity

The analysis protocol is written **before this project's outcome analysis**, preserved in Git history, and explicitly named a **pre-specified analysis plan** — **not** a registration conducted before the original historical experiment.

Read **[`01-experiment-analysis-plan.md`](01-experiment-analysis-plan.md)** for exact metrics, estimands, hypotheses, Holm adjustment, subgroup scope, simulation validation, and decision rules. Phase 0 is not completed until that file has been committed to Git.

## Repository map

| Path | Purpose | Phase 0 state |
| --- | --- | --- |
| `01-experiment-analysis-plan.md` | Outcome-blind statistical analysis protocol | Draft, ready for review/commit |
| `data/README.md` | Provenance policy; no dataset included | Present |
| `src/` | Future reusable analysis modules | Empty |
| `tests/` | Future unit and simulation tests | Empty |
| `sql/` | Future independent data-quality reconciliation | Empty |
| `reports/` | Future business decision memo | Empty |
| `figures/` | Future final result figures | Empty |
| `.gitignore`, `.editorconfig` | Minimal project hygiene | Present |

## Phase boundaries

**Phase 0 (now):** Plan repository structure, write/review and Git-commit analysis plan. **No dataset download or outcome inspection.**

**Phases 1–5 (later):** Data validation/SRM → synthetic simulation validation → primary and secondary A/B/n inference (including adjustment/subgroups) → business memo → reproducible portfolio release. Each phase requires review before moving forward. The project stops at portfolio release; a dashboard, API, and web app are deliberately out of scope.

## Dataset attribution

Original experiment: Kevin Hillstrom, *MineThatData E-Mail Analytics And Data Mining Challenge* (2008): https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html

Data-dictionary reference: https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html

The data have **not** been downloaded or analyzed as part of Phase 0. The eventual download source, timestamp, usage terms and SHA-256 checksum will be documented before analysis. Raw data are intentionally excluded from this repository skeleton.

## Reproducing analysis

Not yet available. Environment setup, dependency versions, execution commands, and testing instructions will be added in the implementation phases **after the analysis plan is committed**. No provisional results or notebooks are published at Phase 0.
