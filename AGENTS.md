# Project Instructions

These instructions apply to the entire repository.

## Frozen analysis contract

- Follow `01-experiment-analysis-plan.md` as frozen at the annotated
  `plan-v1.1` tag.
- Do not change the research questions, hypotheses, primary metrics, estimands,
  statistical tests, multiplicity correction, confidence-interval methods,
  subgroup definitions, simulation criteria, or business decision rules.
- Work only on the phase explicitly authorized by the current task. Stop for
  review before beginning the next phase.

## Outcome protection

Until the inference stage in GitHub Issue #4 has been explicitly approved:

- Never calculate, print, visualize, log, preview, or otherwise expose
  treatment-arm-specific `conversion`, `visit`, or `spend` results. This
  includes counts, means, rates, distributions, quantiles, and row examples.
- During Phase 1, outcome columns may be checked only on pooled data for data
  types, missingness, legal values, and invalid-record counts.
- Assignment-only arm counts for sample-ratio-mismatch diagnostics are allowed.
  Pre-treatment covariate balance checks by arm are also allowed.
- Do not run unrestricted `groupby("segment").mean()`, unrestricted
  `describe()`, automated EDA, or any output preview that contains outcome
  columns. Review generated output as well as source code for leakage.

## Data and reporting boundaries

- Do not download experiment data without explicit authorization. Never commit
  raw experiment data; keep authorized raw data in the Git-ignored
  `data/raw/` directory.
- Do not generate experiment results, invent or fabricate findings, or imply
  that unexecuted analyses were performed.
- Do not expand the project into dashboards, APIs, web applications, notebooks,
  or unrelated infrastructure unless a later phase explicitly authorizes it.
- Require technical review of the current phase before progressing to another
  phase or issue.
