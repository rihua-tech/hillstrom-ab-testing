# 01 — Experiment Analysis Plan

**Project:** Marketing Campaign A/B/n Testing & Causal Impact Analysis  
**Dataset:** Hillstrom / MineThatData E-Mail Analytics Challenge (historical randomized experiment)  
**Repository:** `hillstrom-ab-testing`  
**Plan version:** 1.0-draft | **Prepared:** 2026-11-13  
**Status:** OUTCOME-BLIND DRAFT — **not frozen until committed to Git**  
**Planned freeze evidence:** First Git commit containing this file; record commit SHA in the analysis log when the commit is made.

> **Integrity statement.** This is a *pre-specified analysis plan* written before this project's treatment-arm outcome analysis. The underlying experiment is public and historical; this is **not** an original-trial pre-registration. No group-level treatment effects, conversion results, visit results, revenue results, or outcome-derived model selections have been examined for this project while preparing this plan. Public experiment design and data definitions are permitted sources. Changes after the freeze commit must be transparently versioned and labeled deviations or exploratory analyses; the Git history must be retained.

## 1. Business question and scope

**Question:** Do merchandise-promotion emails causally increase purchase conversion relative to no email, and what incremental business value might their effects create?

The original experiment randomly assigned approximately 64,000 customers to one of three arms, with a two-week post-email observation window:

| Arm | Raw `segment` value | Role |
| --- | --- | --- |
| Control | `No E-Mail` | No promotional email |
| Treatment M | `Mens E-Mail` | Men's-merchandise email |
| Treatment W | `Womens E-Mail` | Women's-merchandise email |

**Unit of randomization and analysis:** Customer. **Target population for this analysis:** Customers eligible for and represented by the historical experiment. The primary causal claim concerns **assignment to an email strategy (intention to treat)**, not whether an email was opened or read. Extrapolation beyond the trial population requires separate assumptions.

**Main assumptions and limitations:** Documented random assignment; no material cross-customer interference; reliable measurement of the two-week outcomes; consistent treatment definitions; and no selection on post-treatment behavior. Neither email-open data nor profit/cost data are assumed to be observed. Interpret findings in the historical experiment's setting, not as a guaranteed effect for a current campaign.

## 2. Data contract (definitions only; not outcome summaries)

The expected fields are defined by public documentation. **Do not inspect or compute treatment-level outcome summaries before the freeze commit.**

| Type | Field(s) | Intended use |
| --- | --- | --- |
| Assignment | `segment` | Three randomized arms |
| Primary outcome | `conversion` | 1 = any purchase in the two-week outcome window, 0 = none |
| Secondary outcomes | `visit`, `spend` | Any visit; dollars spent in the same window |
| Pre-treatment numeric | `recency`, `history` | Months since prior purchase; historical spending |
| Pre-treatment binary | `newbie`, `mens`, `womens` | New-customer flag and past department purchases |
| Pre-treatment categorical | `channel`, `zip_code`, `history_segment` | Historical purchase channel, location class, historical spend band |

`history_segment` is redundant with the underlying `history` measurement for regression adjustment and will not be included as an additional adjustment covariate. All definitions and legal values will be checked at data ingestion, not assumed valid.

**Source-of-truth references:**
- Hillstrom, *MineThatData E-Mail Analytics And Data Mining Challenge* (2008): https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html
- Scikit-uplift documentation (republished experiment and field definitions): https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html

**Dataset provenance, file checksum, exact file location and download date:** To be recorded in Phase 1 *after* this plan is frozen. The raw dataset should remain outside version control unless its redistribution rights are explicitly verified.

## 3. Estimands, primary metric, and hypotheses

For customer \(i\), let \(Y_i(a)\) be the binary potential purchase outcome under assignment to arm \(a\). For \(a \in \{M,W\}\), the average intention-to-treat effect on conversion is

\[
\Delta_a = E[Y_i(a)] - E[Y_i(0)]
\]

where 0 indicates Control. The analysis estimates **absolute conversion-rate differences** (percentage points), not odds ratios, as the primary effect measures.

**Primary metric:** `conversion`, proportion of **all randomized customers** with `conversion == 1` in each arm; no conditioning on visits, opens, or purchasers.

**Confirmatory family (exactly two hypotheses):**

| ID | Contrast | Null hypothesis | Alternative | Test |
| --- | --- | --- | --- | --- |
| H1 | M − Control | \(\Delta_M = 0\) | \(\Delta_M \ne 0\) | Two-sided two-independent-proportion score test |
| H2 | W − Control | \(\Delta_W = 0\) | \(\Delta_W \ne 0\) | Two-sided two-independent-proportion score test |

**Inference specification:**
1. Use `statsmodels.stats.proportion.test_proportions_2indep` with `compare="diff"`, `method="score"`, and `alternative="two-sided"`, or the equivalent documented score-test function, with the implementation pinned and validated before results are interpreted.
2. Correct **only the two primary-test p-values together** using Holm's step-down method (`statsmodels.stats.multitest.multipletests(method="holm", alpha=0.05)`). This controls family-wise error for the two confirmatory questions.
3. Report the observed difference in **percentage points**, the **unadjusted 95% Newcombe/Wilson-score confidence interval** for each risk difference (`confint_proportions_2indep(..., compare="diff", method="newcomb", alpha=0.05)`), raw p-value, Holm-adjusted p-value, and inference decision. Also report relative lift only when the control rate is nonzero, labeled descriptive.
4. **Interpretation rule:** The Holm-adjusted p-value determines confirmatory significance; the separately reported 95% per-comparison confidence interval is **not** a simultaneous family-wise 95% interval. Its exclusion or inclusion of zero is not substituted for the Holm decision.
5. A statistically supported **positive** effect requires both `adjusted p < 0.05` and a positive risk-difference estimate. A significant negative effect is evidence of harm, not success. Non-significance is insufficient evidence, **not proof of no effect**.

**Between-treatment comparison:** M vs W is **not** part of the confirmatory family. Differences between their estimated effects may be shown descriptively for decision context, but no statistically established superiority claim may be made without a separately disclosed, appropriately adjusted head-to-head analysis (labeled exploratory here).

**No post-hoc power analysis or data-driven success threshold:** Effect magnitudes and uncertainty are primary. Do not choose a minimum detectable effect after inspecting outcomes. No minimum practical effect is imposed without known campaign economics; business sensitivity analysis will supply decision context instead.

## 4. Secondary metrics (not confirmatory success gates)

| Metric | Definition / denominator | Estimand | Method and interpretation |
| --- | --- | --- | --- |
| Visit rate | Mean of `visit` across **all assigned customers** | Absolute risk difference vs Control | Two-sided two-proportion score test and unadjusted Newcombe 95% CI |
| Revenue per assigned customer | Mean `spend` including **zero spenders** | Difference in USD/customer vs Control | Two-sided Welch test of mean difference, unadjusted 95% Welch CI; stratified bootstrap (2,000 resamples within arm) for sensitivity to skew |

These metrics are **supporting/exploratory** and cannot replace the primary conversion hypothesis after seeing results. To reduce misleading secondary discoveries, report Holm-adjusted p-values across the **four** secondary contrast–metric tests as a **separate exploratory family** (M and W for visit; M and W for revenue). Their correction is **not** mixed with the two primary tests, and findings will not be called confirmatory.

Do **not** analyze spend *per purchaser* as an ITT causal revenue outcome: conditioning on purchasers selects on a post-treatment variable. Average order value among converters, if later shown at all, must be clearly marked descriptive and noncausal.

## 5. Data quality and randomization diagnostics — ordered gates

Phase 1 will execute these checks **before** primary treatment-effect tables or hypothesis tests are produced.

1. **Data provenance and schema:** Store data source, retrieval date, SHA-256 hash, expected column list, types, legal treatment labels and observed row count. Reconcile any discrepancy with documentation without silently changing the denominator.
2. **One record per randomized customer:** Check row grain using available identifiers. If no unique customer ID is provided, exact duplicate feature/outcome rows are **not** proof of duplicated customers; never automatically drop them.
3. **Validity:** Check missing or invalid `segment`, `conversion`, `visit`, `spend`, nonbinary flags, negative spending, and internal inconsistencies. Report counts, not just percentages. **Do not encode missing outcomes as zero.**
4. **Missing outcomes:** The confirmatory analysis is paused if any primary-outcome or assignment data are missing or invalid. Investigate data provenance and the possibility of outcome-dependent missingness before proceeding; document a plan deviation if a defensible strategy is required. Never select a missing-data method by its effect on significance.
5. **Sample Ratio Mismatch:** Provided the published ~1:1:1 random-assignment design applies to the delivered file, run a chi-square goodness-of-fit test of observed arm counts vs equal expected counts. Flag `p < 0.001` as a serious diagnostic requiring investigation and hold confirmatory interpretation pending resolution. A nonsignificant SRM test does **not** prove randomization worked; a small p-value does **not** by itself diagnose the cause.
6. **Pre-treatment balance:** Check the treatment groups for `recency`, `history`, `mens`, `womens`, `newbie`, `channel`, `zip_code`; report standardized mean differences and categorical distributions. Use `|SMD| > 0.10` as a **review flag**, not as an automatic basis for dropping observations or switching estimators. Do not choose covariates according to the outcome differences they produce.
7. **Audit trail:** Preserve all discovered exceptions and actions in a dated analysis log. Keep an SQL-based row-count/arm-count cross-check in scope for implementation, but do not write SQL or inspect the data in Phase 0.

## 6. Covariate adjustment / precision analysis (pre-specified secondary analysis)

Use **regression adjustment**, not a choice made after observing whether CUPED improves results. The **unadjusted two-proportion tests remain the confirmatory analyses**, regardless of adjusted results.

- **Model:** Linear probability regression of `conversion` on the two treatment indicators and **pre-treatment** covariates, with heteroskedasticity-robust `HC3` standard errors. Use a fully interacted specification between treatment indicators and centered covariates (Lin-style adjustment). Center features using the pooled randomized sample; the treatment coefficients then represent effects at the pooled covariate mean. For categorical features, use prespecified pooled one-hot encoding and centering.
- **Locked adjustment covariates:** `log1p(history)`, `recency`, `newbie`, `mens`, `womens`, categorical `channel`, and categorical `zip_code`; omit `history_segment` as redundant. Do not use `visit`, `conversion`, or `spend` as predictors.
- **Pre-treatment missing values:** For numerical covariates, median-impute using the pooled (treatment-blind) distribution and add missingness indicators; for categorical covariates, use an explicit `Missing` category. These operations are defined without outcome labels. Invalid historical spend values must be investigated before logarithmic transformation.
- **Reporting:** Compare adjusted and unadjusted estimates, HC3 standard errors, and 95% intervals. Compute the descriptive variance-reduction quantity \(1 - (SE_{adj}/SE_{unadj,HC3})^2\) using **comparable HC3 SEs** from the unadjusted and adjusted regressions. This quantity may be negative. Do **not** substitute the adjusted significance result for the primary Holm decision.
- **No guaranteed gain:** If historical features are weakly predictive, report negligible or adverse precision changes. CUPED is not required as a second competing technique in this fixed-scope project.

## 7. Pre-specified heterogeneous treatment effects

**Only two baseline moderators**, selected on business relevance before outcome inspection:

| Moderator | Pre-specified split | Business rationale |
| --- | --- | --- |
| `newbie` | 1 vs 0 | New vs existing customers may respond differently |
| `history` | Above vs at/below the **pooled, treatment-blind pre-treatment median** | Prior customer value may modify campaign response |

For each moderator, fit a linear probability model containing indicators for M and W, the moderator, and **both treatment × moderator interactions**. Use HC3 standard errors. There are **four interaction tests total** (two email arms × two moderators); apply Holm correction **across all four** at 0.05 and report both adjusted and unadjusted p-values. Report subgroup-specific ITT conversion differences and 95% intervals as descriptive context.

**Interpretation:** A statistically significant effect within one subgroup and a nonsignificant effect in another **does not** demonstrate a significant subgroup difference; the relevant evidence is the interaction test. Such analyses remain secondary and are not a license to search additional splits. No random half-sample split is planned because it would reduce power.

## 8. Statistical-code validation — simulation-only, no observed-data calibration

**Purpose:** Independently assess that test logic, p-value adjustment, effect estimates, and confidence intervals behave as expected **before accepting experiment interpretations**. Simulated customers are not the Hillstrom customers.

- **Reproducibility:** Fixed pseudorandom seed `20261113`; **2,000 independent simulation replications per scenario**; three randomly assigned arms per replication with approximately 1:1:1 assignment; simulated total sample size `n = 64,000` (based on public design metadata only).
- **A/A scenario:** Bernoulli purchase outcomes with the **same** synthetic baseline probability `p = 0.02` in all three arms. Record empirical false-positive rate for each **unadjusted** primary test, and empirical family-wise error rate (probability of ≥1 false positive) for the **two-test Holm family**. The unadjusted rate should be statistically compatible with 0.05, while Holm FWER should be **at most 0.05 in expectation**. Use a three-Monte-Carlo-SE tolerance for diagnostic checks; do not demand exactly 5% observed false positives.
- **Known-effect scenario:** Synthetic `p_Control = 0.02`, `p_M = 0.025`, `p_W = 0.02`, so true risk differences are +0.005 and 0. Evaluate average estimated bias and coverage of each **unadjusted 95% Newcombe interval**. The sample mean bias must fall within three empirical Monte Carlo standard errors of zero, and coverage must be compatible with 95% using a three-Monte-Carlo-SE diagnostic band.
- **Adjustment scenario:** Separately generate a synthetic baseline covariate that **predicts** the binary outcome while treatment remains randomized. Check that the HC3 adjustment estimates the known treatment effect without material bias; compare precision with unadjusted estimates. If a nonpredictive synthetic covariate is also used as a negative control, no precision improvement is expected.
- **Validation review:** Record per-scenario estimates, error rates, confidence interval coverage, tolerances, and run seed. Debug code or document assumptions if diagnostics fail. No adjustment method can be declared 'better' just because it appears favorable on the historical observed outcomes.

Because both contrasts share a control, their null test statistics are **dependent**; the A/A family-wise evaluation must simulate the complete three-arm experiment, not treat two p-values as independent.

## 9. Business impact and decision policy

**Incremental conversion per 1,000 eligible customers:** \(1000 \times \widehat{\Delta}_a\).  
**Incremental revenue per targeted customer (USD):** \(\widehat{\mu}_{spend,a} - \widehat{\mu}_{spend,0}\), where each mean includes zero spenders.  
**Illustrative incremental revenue at scale \(N\):** \(N \times (\widehat{\mu}_{spend,a} - \widehat{\mu}_{spend,0})\).  
**Illustrative incremental contribution (not observed profit):**

\[
N \times \left[m\,\left(\widehat{\mu}_{spend,a}-\widehat{\mu}_{spend,0}\right)-c\right]
\]

where \(m\) is an **assumed** contribution margin on incremental revenue and \(c\) is **assumed** incremental email delivery/creative cost **per targeted customer** relative to Control. Any fixed/setup costs not represented by \(c\) must be disclosed separately.

**Fixed sensitivity grid, explicitly hypothetical:** Margin `m` ∈ {20%, 40%, 60%}; cost `c` ∈ {$0.01, $0.05, $0.20} per targeted customer; normalize results to `N = 10,000` eligible customers. These are **scenario assumptions**, not historical campaign cost measurements. Avoid claiming observed ROI or profit.

**Decision logic:**
- Label an arm **statistically supported positive on conversion** only if it passes the primary Holm rule and its conversion effect is positive.
- Discuss whether a positive business contribution survives the fixed margin/cost scenarios; conversion significance **alone** does not demonstrate profitability.
- If results are inconclusive, recommend collecting more evidence in a newly designed prospective experiment rather than claiming the null is true.
- If both arms appear useful, compare estimated *scenario-based* business contribution and uncertainty, but do not claim that one email is statistically superior to the other without an explicitly identified head-to-head test.
- Any rollout recommendation is hypothetical and conditional on assumptions, seasonality, reproducibility, and the historical population's applicability today.

## 10. Reporting, transparency, and reproducibility

The final reporting package will include: an executive summary, a comparison table with risk differences / per-comparison 95% CIs / raw and adjusted p-values, reproducible data-quality and SRM evidence, limited subgroup analyses, an adjustment comparison, simulation validation, a cost/margin sensitivity table, limitations, and a **Business Decision Memo**. SQL can be used for independent counts and audit reconciliation; Python remains the single source of inferential logic.

**No invented results, no post-treatment adjustment, no significance-driven metric changes, no dashboard, no web app, and no new unrelated models or projects.**

**Change control after plan freeze:** Record the original SHA, changed section, rationale, and timestamp in a `Deviations from pre-specified plan` section to be added at the first deviation. Distinguish prerequired fixes, sensitivity analyses, and post-hoc discoveries. Never rewrite Git history to conceal changes.

## 11. Phase gates and definition of done

| Phase | Deliverables | Acceptance criteria | Boundary |
| --- | --- | --- | --- |
| **0 — Foundation (current)** | Repository skeleton, README, `.gitignore`, this plan | Plan review; commit with timestamp and SHA **before** exposure to outcomes | No dataset download, outcome preview, statistical code, or result claims |
| **1 — Data integrity** | Provenance, quality checks, SRM, baseline balance, audit log, SQL reconciliation | Reproducible ingestion; exceptions resolved/documented; gate status recorded | No undocumented data pruning or hypothesis changes |
| **2 — Simulation validation** | Implement inferential methods against synthetic A/A, known-effect, and predictive-covariate scenarios | Validate false positives, Holm FWER, bias, and CI coverage **before outcome inference** | No calibration to Hillstrom outcomes |
| **3 — Experiment inference** | Primary conversion contrasts, Holm correction, secondary visit/spend, adjusted regression, two moderators | Correct hypothesis families; estimates, uncertainty, and limits reported | No metric shopping or uncontrolled subgroup search |
| **4 — Business decision** | Decision memo, fixed sensitivity grid, limitations | Revenue/profit distinction; conditional recommendation; uncertainty shown | No invented costs |
| **5 — Portfolio release** | Reproduction instructions, final README, tests, figures, concise findings | Clean reproducible run; peer-style review; Git commit history | **Stop scope expansion; transition to applications** |

**Phase 0 is not accepted until an actual Git commit containing this plan exists.** A downloaded plan file alone is a draft, not proof of pre-specification.

## 12. Methods references

- `statsmodels` score test: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.score_test_proportions_2indep.html
- `statsmodels` two-independent-proportion confidence intervals: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html
- `statsmodels` Holm multiplicity adjustment: https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

*No observed Hillstrom treatment-group result is included in this document.*
