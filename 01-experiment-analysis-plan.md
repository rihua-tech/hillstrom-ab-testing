# 01 — Experiment Analysis Plan

**Project:** Marketing Campaign A/B/n Testing & Causal Impact Analysis  
**Dataset:** Hillstrom / MineThatData E-Mail Analytics Challenge (historical randomized experiment)  
**Repository:** `hillstrom-ab-testing`  
**Plan version:** 1.1 (proposed post-freeze amendment) | **Original prepared:** 2026-11-13 | **Revised:** 2026-11-14\
**Status:** Original v1.0 baseline already committed; **v1.1 is not frozen until the new Git commit is pushed**. No treatment-arm-level outcome analysis has been performed for this project.\
**Original baseline commit:** [`d6fe8f00970805510cfc0af36483a14e486d09f9`](https://github.com/rihua-tech/hillstrom-ab-testing/commit/d6fe8f00970805510cfc0af36483a14e486d09f9) (`docs: freeze outcome-blind experiment analysis plan`).\
**v1.1 evidence (pending):** Record the new commit SHA and optional `plan-v1.1` tag after push. Do not rewrite the original commit.

> **Integrity statement and limited prior exposure.** This is a *pre-specified analysis plan* for the analysis of a public historical experiment, **not** a pre-registration of the original trial. Before the original Git commit, an AI-assistant message mentioned an **approximate pooled purchase-conversion rate (~0.9%)**. This value was **not independently verified**, and is **not an arm-specific outcome or treatment effect**. No treatment-arm-specific conversion, visit, or revenue results; treatment-effect estimates; or hypothesis-test results were examined in preparing the original plan or this amendment. The supplementary baseline scenarios in v1.1 were chosen **after that limited pooled-rate exposure** and must not be represented as fully outcome-blind. The original frozen methods remain in Git history; changes in v1.1 are explicitly classified below. Never rewrite history to hide deviations.

## 1. Business question and scope

**Question:** What is the causal effect of assigning customers to each merchandise-promotion email on two-week purchase conversion versus no email, and under what assumed margins and email costs might each strategy generate positive incremental contribution?

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

**No observed-effect post-hoc power or data-driven success threshold:** Effect magnitudes and uncertainty are primary. Do not calculate retrospective power using observed treatment effects, select a success threshold based on significance, or reinterpret a detectable effect as the minimum *business-important* effect. Without verified campaign economics, business sensitivity analysis supplies decision context.

### Design-based sensitivity / minimum detectable effect (MDE) — illustrative

These are **approximate detection limits**, **not** estimates from the historical treatment arms and **not** formal power calculations of the original trial. Assume three equally sized arms from a nominal total of `N = 64,000` (`n ≈ 21,333` per arm), a two-sided normal-approximation two-proportion test, **80% power**, and `alpha = 0.025` for each treatment-versus-control calculation. Using 0.025 represents the **conservative first-step threshold** of the two-test Holm procedure; Holm is step-down and does not always use 0.025 for every hypothesis. The actual confirmatory analysis will still use the locked score tests and Holm correction.

| Hypothetical control conversion | Approximate detectable absolute increase | Approximate treatment conversion |
| --- | ---: | ---: |
| 0.5% | +0.233 percentage points | 0.733% |
| 1.0% | +0.319 percentage points | 1.319% |
| 2.0% | +0.439 percentage points | 2.439% |

The table uses a normal approximation with arcsine/Cohen's *h* for unequal proportions and equal arm sizes; its figures are **rounded scenario calculations**, not exact finite-sample score-test or joint-Holm power guarantees. Baseline rates `{0.005, 0.01, 0.02}` are **hypothetical scenarios selected after the unverified pooled-rate remark (~0.9%) had been seen**, and should not be described as wholly outcome-blind. No observed effect size was used. This exercise communicates *power limitations*; it does not add a third confirmatory test or change the decision threshold.

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
- **Relationship to CUPED:** CUPED and Lin-style regression adjustment both use pre-treatment information to improve precision. Standard single-covariate CUPED is a simpler control-variate adjustment; the pre-specified fully interacted Lin regression is **not equivalent** to standard CUPED. No separate CUPED estimator will be built merely to add another method.
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

- **Reproducibility:** Fixed pseudorandom seed `20261113`; **2,000 independent replications per scenario**; three randomized arms per replication at approximately 1:1:1; simulated total `n = 64,000` (from public design metadata). Use simulated data **only**, never actual treatment-arm outcomes to choose simulation parameters.
- **Unadjusted A/A scenarios:** Independently simulate Bernoulli purchase outcomes with **no effect** and the same synthetic baseline probability in all arms, for **each** `p ∈ {0.005, 0.01, 0.02}`. Record each score test's unadjusted 5% false-positive rate and the probability of **one or more rejections after two-test Holm correction**. Use three-Monte-Carlo-SE tolerance bands around the appropriate 0.05 reference (the Holm FWER should not materially exceed 0.05), not an exact 5% pass requirement. Simulate the *joint three-arm design* with a shared Control; the two tests are dependent.
- **Known-effect scenario (unchanged):** Synthetic `p_Control = 0.02`, `p_M = 0.025`, `p_W = 0.02`, giving true risk differences +0.005 and 0. Check average bias and **per-comparison unadjusted 95% Newcombe CI coverage**, with three-Monte-Carlo-SE diagnostic bands. Do not mistake those intervals for simultaneous Holm-adjusted intervals.
- **Regression-adjusted known-effect scenario (retained):** Separately simulate a predictive **pre-treatment** covariate with randomized treatment. Check that the fixed HC3 fully interacted Lin regression estimates the known effect without material bias; compare adjusted and unadjusted precision. No precision gain is guaranteed.
- **Regression-adjusted A/A scenario (added in v1.1):** Use a predictive pre-treatment covariate and a **zero treatment effect** at synthetic baseline `p = 0.01`. Across **2,000 replications**, assess both HC3 Lin treatment tests' nominal two-sided 5% false-positive rates and their **two-test Holm family-wise error rate**. These are validation diagnostics for a *secondary* estimator, not substitutes for the locked confirmatory unadjusted tests. Report Monte Carlo uncertainty and investigate material inflation.
- **Validation review:** Record scenario definitions, estimates, Monte Carlo uncertainty, false-positive rates, family-wise rates, bias, confidence interval coverage, and seed. Debug code or document model/test assumptions if diagnostics fail; never tune the method to historical observed outcomes.

Because both contrasts share Control, their null test statistics are **dependent**. Use complete three-arm simulations rather than independently sampled contrast p-values. The expanded low-rate simulation settings are v1.1 supplements, not conditions asserted at the original freeze.

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

**Change control after plan freeze:** Preserve the original baseline commit and transparently version later edits. Record the new SHA once committed and pushed. Distinguish editorial clarification from *pre-analysis methodological additions*, and label any changes made after arm-level results as exploratory/post-hoc. Never rewrite Git history to conceal changes.

### Plan change log (post-baseline amendment)

| Version | Timing and provenance | Change classification | What changed |
| --- | --- | --- | --- |
| v1.0 baseline | First public Git commit `d6fe8f0` (2026-11-14 UTC) | Original pre-analysis baseline | Locked conversion ITT estimands, two primary contrasts, score tests, Holm correction, secondary metrics, regression adjustment, moderator set, simulation core and business decision rules. Although labeled `draft` in that file, it was committed before treatment-arm outcome analysis. |
| v1.1 proposed | 2026-11-14; **commit SHA pending** | Transparency + editorial clarifications | Disclosed unverified pooled conversion-rate remark (~0.9%); aligned research question and document status; clarified relationship between CUPED and Lin. |
| v1.1 proposed | 2026-11-14; **commit SHA pending** | **Pre-arm-level-outcome methodological supplements (not present in v1.0)** | Added hypothetical design-based MDE scenarios, low-baseline unadjusted A/A settings, and regression-adjusted A/A error-rate diagnostics. These supplement validation; they do not alter the original primary hypotheses, alpha, tests, decision rule, or subgroup scope. |

**Audit follow-up:** After the v1.1 changes are reviewed locally, commit and push them **before accessing arm-level outcomes**; optionally add an annotated `plan-v1.1` tag. Record the resulting commit SHA in the GitHub commit record or a separate analysis log; do not try to embed a commit's own SHA in the file being committed. A Git tag is a useful reference but not an immutable timestamp guarantee. A SHA-256 digest may also be stored in an independent analysis log; it is not evidence of scientific pre-registration.

## 11. Phase gates and definition of done

| Phase | Deliverables | Acceptance criteria | Boundary |
| --- | --- | --- | --- |
| **0 — Foundation (baseline complete; v1.1 update pending)** | Repository skeleton, README, `.gitignore`, this plan | Original baseline committed (`d6fe8f0`); v1.1 amendment reviewed/pushed before any arm-level outcome analysis | No dataset download, arm-level outcome preview, statistical code, or result claims |
| **1 — Data integrity** | Provenance, quality checks, SRM, baseline balance, audit log, SQL reconciliation | Reproducible ingestion; exceptions resolved/documented; gate status recorded | No undocumented data pruning or hypothesis changes |
| **2 — Simulation validation** | Implement inferential methods against synthetic A/A, known-effect, and predictive-covariate scenarios | Validate false positives, Holm FWER, bias, and CI coverage **before outcome inference** | No calibration to Hillstrom outcomes |
| **3 — Experiment inference** | Primary conversion contrasts, Holm correction, secondary visit/spend, adjusted regression, two moderators | Correct hypothesis families; estimates, uncertainty, and limits reported | No metric shopping or uncontrolled subgroup search |
| **4 — Business decision** | Decision memo, fixed sensitivity grid, limitations | Revenue/profit distinction; conditional recommendation; uncertainty shown | No invented costs |
| **5 — Portfolio release** | Reproduction instructions, final README, tests, figures, concise findings | Clean reproducible run; peer-style review; Git commit history | **Stop scope expansion; transition to applications** |

**Phase 0 baseline was committed as `d6fe8f0`.** The v1.1 supplements must receive a **separate** commit before accessing arm-level outcome data. An uncommitted local file is not a frozen amendment.

## 12. Methods references

- `statsmodels` score test: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.score_test_proportions_2indep.html
- `statsmodels` two-independent-proportion confidence intervals: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html
- `statsmodels` Holm multiplicity adjustment: https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

*No observed Hillstrom treatment-group result is included in this document. An approximate, unverified pooled-rate remark previously seen in an AI response is disclosed above.*
