# Hillstrom data quality audit

## Phase 1.3 run — 2026-11-26

The local run completed at 2026-11-26T23:13:39.155Z on
`phase1/data-quality` from base commit `0a72f81`, with the Phase 1.3 working
changes. The [documented PowerShell recipe](../data/README.md#phase-13--field-quality-and-duplicate-looking-records)
matched the Phase 1.1 SHA-256 and passed the Phase 1.2 structure check.
Both the validator and the audit counted **64,000** data records. The audit
retained all records and exited `0` with status **REVIEW**.

### Pooled quality counts

| Fields | Missing per field | Invalid per field |
| --- | ---: | ---: |
| `recency`, `history_segment`, `history`, `mens`, `womens`, `zip_code`, `newbie`, `channel` | 0 | 0 |
| `segment` | 0 | 0 |
| `conversion` | 0 | 0 |
| `visit` | 0 | 0 |
| `spend` | 0 | 0 |

| Pooled consistency rule | Flagged records |
| --- | ---: |
| `history_outside_documented_band` | 0 |
| `positive_spend_with_no_purchase` | 0 |

The assignment and primary-outcome missing/invalid gate did not trigger a
confirmatory inference hold. This is the status of that gate only.

### Open review item

Exact matches across the eight pre-treatment fields produced **420**
duplicate-looking groups, covering **8,211** records. There were **7,791**
records beyond one per group. These counts describe equal profiles. Customer
uniqueness cannot be verified from this CSV because it has no unique customer
ID. Carry the source identifier limitation into technical review and retain
all records.

## Phase 1.4 SRM run — 2026-11-26

The local run completed at `2026-11-27T00:05:34.522Z` (November 26 in
America/New_York) on `phase1/data-quality` from base commit `b3c77d3`,
with the Phase 1.4 working changes. The [documented PowerShell recipe](../data/README.md#phase-14--sample-ratio-mismatch-srm)
matched the Phase 1.1 SHA-256, passed the Phase 1.2 structure check, and
reran Phase 1.3 with `REVIEW` and no `HOLD`. The Phase 1.3 duplicate-looking
profiles remain open for technical review. SRM counted all 64,000 assignments.

The original challenge links to the acquired CSV and documents random
assignment of about one third of customers to each arm. The scikit-uplift
description corroborates the design. [Original March archive](https://blog.minethatdata.com/2008/03/?m=1) ·
[Scikit-uplift data description](https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html#data-description)

| Assignment | Observed count | Observed proportion | Expected count (`N/3`) |
| --- | ---: | ---: | ---: |
| `No E-Mail` | 21,306 | 0.33290625 | 64000/3 ≈ 21333.333333333332 |
| `Mens E-Mail` | 21,307 | 0.332921875 | 64000/3 ≈ 21333.333333333332 |
| `Womens E-Mail` | 21,387 | 0.334171875 | 64000/3 ≈ 21333.333333333332 |

SciPy 1.16.3 returned Pearson χ² = `0.20253125000000002`, df = `2`, and
p = `0.9036929575604196`. The SRM status was **PASS** (exit `0`). The frozen
`p < 0.001` hold threshold did not trigger. This status applies to the
assignment-ratio gate.

The synthetic 10,400 / 9,800 / 9,800 case reproduced χ² = `24` and
p ≈ `0.000006144212353`, which triggers `HOLD`.

### SRM entry review for Phases 1.5–1.7

Rechecked at `2026-11-27T03:03:15.1558975Z` (November 26 in New York)
from `b3c77d3` with the existing Phase 1.4 working changes. The original
challenge archive links to the Phase 1.1 artifact and both source descriptions
support the equal-allocation reference. The PowerShell recipe matched the
provenance hash, passed schema validation, and completed the pooled quality
audit with `REVIEW` and no `HOLD`.

Read the SRM code, tests, recipe, and prior results. The counter consumes
only assignment cells, requires complete record coverage, and aborts on a
missing or illegal assignment. The test uses SciPy Pearson χ², `N/3` without
integer rounding, `df = 2`, and the strict unrounded `p < 0.001` rule. The
rerun reproduced all 64,000 assignments, the three counts above, χ²
`0.20253125000000002`, and p `0.9036929575604196`. All 11 SRM tests passed,
including the synthetic hold example and threshold boundary. No SRM fix
was required. The entry review passed with no unresolved hold.

## Phase 1.5 balance run — 2026-11-26

The run completed at `2026-11-27T03:07:33.5480918Z` (November 26 in New York)
on the same checksum-verified artifact after schema, pooled quality, and SRM.
The balance counter accounted for all 64,000 assignments.
For each of the seven covariates the valid denominators were 21,306 Control,
21,307 Men's, and 21,387 Women's, with zero missing and zero invalid per field
in each arm.

| Covariate | Level | Men's n/valid (proportion) | Control n/valid (proportion) | Women's n/valid (proportion) |
| --- | --- | ---: | ---: | ---: |
| mens | 0 | 9568/21307 (0.44905430) | 9519/21306 (0.44677556) | 9647/21387 (0.45106841) |
| mens | 1 | 11739/21307 (0.55094570) | 11787/21306 (0.55322444) | 11740/21387 (0.54893159) |
| womens | 0 | 9558/21307 (0.44858497) | 9638/21306 (0.45236084) | 9622/21387 (0.44989947) |
| womens | 1 | 11749/21307 (0.55141503) | 11668/21306 (0.54763916) | 11765/21387 (0.55010053) |
| newbie | 0 | 10621/21307 (0.49847468) | 10611/21306 (0.49802872) | 10624/21387 (0.49675036) |
| newbie | 1 | 10686/21307 (0.50152532) | 10695/21306 (0.50197128) | 10763/21387 (0.50324964) |
| channel | Multichannel | 2577/21307 (0.12094617) | 2606/21306 (0.12231296) | 2579/21387 (0.12058727) |
| channel | Phone | 9240/21307 (0.43366030) | 9327/21306 (0.43776401) | 9454/21387 (0.44204423) |
| channel | Web | 9490/21307 (0.44539353) | 9373/21306 (0.43992303) | 9354/21387 (0.43736849) |
| zip_code | Rural | 3243/21307 (0.15220350) | 3139/21306 (0.14732939) | 3181/21387 (0.14873521) |
| zip_code | Surburban | 9501/21307 (0.44590979) | 9625/21306 (0.45175068) | 9650/21387 (0.45120868) |
| zip_code | Urban | 8563/21307 (0.40188670) | 8542/21306 (0.40091993) | 8556/21387 (0.40005611) |

| Covariate or level | Men's − Control | Women's − Control | Women's − Men's |
| --- | ---: | ---: | ---: |
| recency | +0.00683153 | +0.00518001 | -0.00164913 |
| history | +0.00761287 | +0.00651072 | -0.00116071 |
| mens=0 | +0.00458243 | +0.00863093 | +0.00404846 |
| mens=1 | -0.00458243 | -0.00863093 | -0.00404846 |
| womens=0 | -0.00758911 | -0.00494643 | +0.00264265 |
| womens=1 | +0.00758911 | +0.00494643 | -0.00264265 |
| newbie=0 | +0.00089192 | -0.00255676 | -0.00344868 |
| newbie=1 | -0.00089192 | +0.00255676 | +0.00344868 |
| channel=Multichannel | -0.00418163 | -0.00528302 | -0.00110139 |
| channel=Phone | -0.00827619 | +0.00862304 | +0.01689952 |
| channel=Web | +0.01101385 | -0.00514798 | -0.01616206 |
| zip_code=Rural | +0.01365932 | +0.00395860 | -0.00970078 |
| zip_code=Surburban | -0.01174363 | -0.00108915 | +0.01065445 |
| zip_code=Urban | +0.00197228 | -0.00176291 | -0.00373519 |

**Balance review.** None of the 42 signed SMDs exceeded the unrounded absolute
`0.10` threshold, and none were undefined. The largest absolute SMD was
`0.01689952` for the Phone channel indicator in Women's minus Men's.
Balance status was `PASS` (exit `0`). All assignments were retained and no
change to the estimators or covariate set was indicated.

Technical self-review verified projection to the seven frozen pre-treatment
fields plus assignment, explicit valid denominators and missing/invalid
counts, sample numeric and Bernoulli indicator variances, and threshold
checks before formatting. The nine synthetic balance tests and targeted Ruff
check passed. Cases covered equal and shifted profiles, category proportions,
the threshold boundary, missing/invalid data, zero variance, and output
isolation. This review passed before SQL reconciliation.

## Phase 1.6 independent SQL reconciliation — 2026-11-26

The run completed at `2026-11-27T03:10:59.2108539Z` (November 26 in New York)
after replaying the checksum, schema, pooled quality, SRM, and balance gates.
The Python and SQL paths independently computed assignment counts, but shared
the same standard-library Python CSV parser. SQLite 3.49.1 received one parsed
assignment per record in an in-memory `segment`-only table and executed
[the count query](../sql/reconcile_assignments.sql). The SQL reconciliation is
therefore an independent aggregation and count check, not an independent
CSV-parser check.

| Population | Python schema / SRM | SQLite | SQLite − Python |
| --- | ---: | ---: | ---: |
| Total | 64,000 | 64,000 | 0 |
| No E-Mail | 21,306 | 21,306 | 0 |
| Mens E-Mail | 21,307 | 21,307 | 0 |
| Womens E-Mail | 21,387 | 21,387 | 0 |

SQLite counted zero missing and zero illegal labels. Its categories accounted
for all 64,000 records. Status was `PASS` (exit `0`), with no discrepancies to
investigate.

The Claude Code independent-review report also reproduced the assignment
counts using pandas' C parser. That separate reproduction provides
parser-diverse verification in addition to the shared-parser Python/SQL
reconciliation.

Technical self-review verified that the SQLite import projects one assignment
per source record, that SQL computes each count, and that the Python schema
and SRM counts enter only the comparison. The four synthetic tests passed,
covering exact reconciliation, labeled missing and illegal counts, a
same-total arm discrepancy, and inconsistent total accounting. Targeted
Ruff passed. This review passed before consolidated acceptance.

## Phase 1.7 consolidated acceptance

On November 26 in New York, the documented end-to-end run completed at
`2026-11-27T03:12:18.9358199Z` from `phase1/data-quality` at `b3c77d3`.
The Phase 1.1 SHA-256 matched, schema validation passed (12 fields and 64,000
records), and the pooled validity audit completed as `REVIEW` with no `HOLD`.
SRM, balance, and SQL reconciliation then passed in order. Their counts,
SMDs, and gate statuses reproduced the individual runs above. Each of the
12 categorical level summaries reconciled to its corresponding field and
arm denominator. The complete local pytest suite passed (55 tests) and
Ruff and Git whitespace checks passed.

### Technical review and open items

- Reviewed the tracked diff and every new file, including the existing SRM
  implementation and tests. Existing Phase 1.4 code, instructions, and run
  results were preserved. The annotated `plan-v1.1` tag and the working
  analysis plan matched their preflight identities.
- Reviewed code and generated output for outcome access, disclosure,
  denominators, and gate behavior. The pooled audit reports only the
  permitted quality counts for outcome fields. SRM and the SQLite loader
  project assignment only, and balance projects the seven frozen fields
  plus assignment. All 64,000 records were retained.
- The outcome-consistency implementation checks positive `spend` without
  `conversion`, but does not check `conversion` with zero `spend` or
  `conversion` without a `visit`. Resolve this review item before Issue #4,
  subject to documented dataset semantics. No additional validity rule is
  adopted in Phase 1.
- The 420 duplicate-looking pre-treatment groups remain a review item.
  The source lacks a unique customer ID, so customer uniqueness is
  unverified. The documented decision is to retain all observations.
- The raw CSV matched the provenance checksum, is ignored under
  `data/raw/`, and that directory has no tracked entries. Explicit dataset
  licensing, redistribution permission, and a provider checksum remain
  unverified as documented in Phase 1.1.
- Claude Code's independent review found no P0 or P1 defects; statistical
  correctness and research integrity passed. Technical acceptance for the
  exact working-tree changes remains conditional on remote CI.

### Issue #2 acceptance

| Task or completion criterion | Local assessment |
| --- | --- |
| Phase 1.0 development safeguards | Met. The reviewed PR #7 supplies the pinned environment, Ruff, pytest, and fast CI. |
| Authentic acquisition, provenance, terms, and raw-data protection | Met. Phase 1.1 records the source, timestamp, terms status, and SHA-256. |
| Schema, legal values, grain, and duplicate-looking records | Met within the identifier limitation. The schema and field checks ran, and the repeat-profile review retained all records. |
| Pooled outcome validity | Met for the implemented Phase 1 checks. Missing/invalid counts were checked only on pooled data; the documented outcome-consistency coverage limitation remains open before Issue #4. |
| Documented allocation and SRM | Met. The source supports 1:1:1 and the prespecified test passed. |
| Pre-treatment balance | Met. All seven covariates and three pairwise contrasts were evaluated with no review flags. |
| Independent SQL counts, audit decisions, reproducible tests | Met. All count differences were zero, the discrepancy tests passed, and the independent reviewer reproduced the counts with pandas' C parser. The Python and SQL paths share the standard-library Python CSV parser. |
| Provenance, checksum, terms status, and protection documented | Met. The raw CSV is local and ignored. |
| Reproducible Python/SQL diagnostics, transparent exceptions, passing CI | Pending remote CI on the exact changes. Local diagnostics, lint, and tests passed. |
| SRM/balance gates reviewed with outcome protection | Met in local self-review. Outputs contained assignment and pre-treatment diagnostics plus permitted pooled quality counts. |
