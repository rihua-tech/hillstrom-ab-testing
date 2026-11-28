# Dataset handling policy

**Current Phase 1 status:** The raw Hillstrom dataset has been acquired locally
under `data/raw/`. It is Git-ignored and remains untracked. No processed
Hillstrom dataset is present.

**After the analysis-plan freeze commit:** Acquire the original/public data from a documented source. Record URL, retrieval timestamp, license/redistribution status, exact file name, SHA-256 hash, known schema, and any transformations before analyzing outcomes.

Keep raw and intermediate data out of Git by default. Do not silently remove duplicates, impute missing outcomes as zero, or filter records using post-treatment behavior. See `../01-experiment-analysis-plan.md` for outcome-blind quality gates.

## Phase 1.1 — Data provenance and acquisition

Kevin Hillstrom's 2008 [MineThatData E-Mail Analytics And Data Mining Challenge](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) is the experiment citation. The post links directly to the original CSV hosted by MineThatData at `www.minethatdata.com`, the file provider for this acquisition. The [scikit-uplift v0.3.1 documentation](https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html) identifies its own distribution as a copy of that challenge dataset.

| Field | Recorded value |
| --- | --- |
| Download URL | `http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv` |
| Final URL | Same as download URL, zero redirects |
| Source version | Original distribution dated `2008.03.20` in the filename. The server reported `Last-Modified: Fri, 21 Mar 2008 02:05:03 GMT` and `ETag: "3c8031-448e8ea0a51c0"`. |
| Retrieval completed (UTC) | `2026-11-26T19:36:41.510Z` |
| Local path | `data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv` |
| Size | `3964977` bytes |
| SHA-256 | `0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece` |
| Extraction or transformations | None. Saved the response bytes as delivered. |

The published HTTP URL returned `200 OK` and `text/csv`. The downloaded and saved byte counts matched `Content-Length`, and the file prefix did not indicate an HTML response. The HTTPS variant failed certificate validation. No provider-published checksum was verified for this CSV. The SHA-256 above fingerprints the locally retrieved artifact. Expected field definitions are in §2 of the frozen plan at `plan-v1.1`.

**Usage and redistribution.** Hillstrom's post offers the CSV for download as part of the challenge and invites readers to share their findings in the post's comments. No explicit dataset license or permission to redistribute the CSV was verified. Keep the raw file local and Git-ignored.

### Reacquire and verify (Windows PowerShell)

Run from the repository root. The recipe verifies an existing file in place and stages a fresh download under the ignored `data/raw/` directory before installing it.

```powershell
$name = 'Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
$url = 'http://www.minethatdata.com/' + $name
$sha256 = '0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece'
$raw = Join-Path (Get-Location).Path 'data\raw'
$file = Join-Path $raw $name

git check-ignore -q -- "data/raw/$name"
if ($LASTEXITCODE -ne 0) { throw 'The destination must be Git-ignored.' }
if (Test-Path -LiteralPath $file) {
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256 -ErrorAction Stop).Hash -ne $sha256) {
        throw 'The existing file has a different SHA-256 and was preserved.'
    }
} else {
    [void][IO.Directory]::CreateDirectory($raw)
    $stage = Join-Path $raw ('.hillstrom-' + [guid]::NewGuid().ToString('N') + '.partial')
    try {
        curl.exe --fail --silent --show-error --location --max-time 90 --output $stage -- $url
        if ($LASTEXITCODE -ne 0) { throw 'Hillstrom download failed.' }
        if ((Get-FileHash -LiteralPath $stage -Algorithm SHA256 -ErrorAction Stop).Hash -ne $sha256) {
            throw 'Downloaded file SHA-256 does not match the recorded artifact.'
        }
        [IO.File]::Move($stage, $file)
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage }
    }
}
Get-FileHash -LiteralPath $file -Algorithm SHA256
```

## Phase 1.2 — Schema validation

The expected CSV header comes from the field names in
[`plan-v1.1` §2](https://github.com/rihua-tech/hillstrom-ab-testing/blob/plan-v1.1/01-experiment-analysis-plan.md#2-data-contract-definitions-only-not-outcome-summaries)
and the [scikit-uplift v0.3.1 field dictionary](https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html#fields).
The dictionary uses title case. Lowercasing its labels, with underscores
preserved (for example, `History_Segment` → `history_segment` and `Zip_Code` →
`zip_code`), gives the frozen analysis names and the expected literal CSV fields:

```text
recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend
```

| CSV fields | Role in the frozen analysis plan |
| --- | --- |
| `segment` | Randomized assignment to one of the three experiment arms |
| `conversion` | Primary outcome, purchase within two weeks |
| `visit`, `spend` | Secondary outcomes, any visit and dollars spent in the same two-week window |
| `recency`, `history` | Numeric pre-treatment covariates, months since prior purchase and historical spending |
| `newbie`, `mens`, `womens` | Binary pre-treatment covariates, new-customer status and prior purchases in the men's and women's departments |
| `channel`, `zip_code`, `history_segment` | Categorical pre-treatment fields, historical purchase channel, location class, and historical spend band |

The source contract includes `history_segment`. The frozen plan excludes it
from regression adjustment because `history` already contains the underlying
measure.

The validator requires each case-sensitive field name exactly once, in any order.
The intended grain is one record per randomized customer. The expected count is
64,000 data records, excluding the header, based on the documented experiment
size. The schema contains no unique customer ID, so a matching record count
cannot verify customer uniqueness. [Original challenge description](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) · [Scikit-uplift dataset description](https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html#data-description)

Run from the repository root in Windows PowerShell. The checksum gate uses the
SHA-256 recorded in Phase 1.1.

```powershell
$csv = 'data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
$expected = '0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece'
$actual = (Get-FileHash -LiteralPath $csv -Algorithm SHA256 -ErrorAction Stop).Hash
if ($actual -ne $expected) { throw "Checksum mismatch. Expected $expected, got $actual." }
.\.venv\Scripts\python.exe -m src.validate_schema $csv
```

The validator opens the explicit path read-only as UTF-8 CSV. It counts parsed
data records, including wrong-width records, and reports the total only if
parsing reaches the end. A malformed record stops parsing. Diagnostics use
field names from the contract, positions, widths, and counts. Unknown header
text and data values are kept out of output. Exit status `0` means the structure
and count passed. Exit status `1` means validation failed.

## Phase 1.3 — Field quality and duplicate-looking records

Run this PowerShell block from the repository root. It uses the Phase 1.1
SHA-256 and requires the Phase 1.2 structure gate before the field audit.

```powershell
$csv = 'data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
$expected = '0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece'
$actual = (Get-FileHash -LiteralPath $csv -Algorithm SHA256 -ErrorAction Stop).Hash
if ($actual -ne $expected) { throw "Checksum mismatch. Expected $expected, got $actual." }
.\.venv\Scripts\python.exe -m src.validate_schema $csv
if ($LASTEXITCODE -ne 0) { throw 'CSV structure validation failed.' }
.\.venv\Scripts\python.exe -m src.audit_data_quality $csv
```

### Field rules

Blank or whitespace-only cells count as missing. Each other cell can have one
invalid reason. The audit validates types and exact label spellings without
altering the file or its records.

| Fields | Validation rule | Basis |
| --- | --- | --- |
| `segment` | `No E-Mail`, `Mens E-Mail`, or `Womens E-Mail` | Frozen plan §1 enumerates raw assignment labels. |
| `recency` | Finite whole months, 0 through 12 inclusive | The challenge describes months since purchase and the twelve-month customer window. The same-file loader documents an integer type. |
| `history`, `spend` | Finite, nonnegative monetary values | The dictionary defines the spend measures, the lowest historical band starts at zero, and frozen plan §5 requires checking negative spend. |
| `mens`, `womens`, `newbie`, `visit`, `conversion` | Finite numeric indicators equal to 0 or 1 | The dictionary defines each as binary. |
| `zip_code` | `Urban`, `Rural`, or the source spelling `Surburban` | The original dictionary describes the suburban class as `Suburban`. The same-file loader and the author identify the raw spelling as `Surburban`. |
| `channel` | `Phone`, `Web`, or `Multichannel` | The same-file loader enumerates the exact labels. |
| `history_segment` | One of the seven documented source labels, from `1) $0 - $100` through `7) $1,000 +` | The same-file loader enumerates all seven labels. |

[Frozen plan `plan-v1.1`](https://github.com/rihua-tech/hillstrom-ab-testing/blob/plan-v1.1/01-experiment-analysis-plan.md) ·
[Original field definitions](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) ·
[Same-file loader and raw labels](https://uplift-sklearn.readthedocs.io/en/latest/_modules/libuplift/datasets/Hillstrom.html) ·
[Author's raw label clarification](https://blog.minethatdata.com/2026/11/an-entire-bs-in-statistics-rendered.html)

### Internal consistency and review gates

A consistency check requires all of its inputs to pass their individual field
rules. Each check reports a pooled count of flagged records.

| Rule | Basis | Severity |
| --- | --- | --- |
| `history_outside_documented_band` | `history_segment` categorizes the same prior-period spending recorded by `history`. A value outside its labeled dollar interval merits review. Shared endpoints are allowed in both adjacent bands because endpoint ownership is unspecified. | Review |
| `positive_spend_with_no_purchase` | `spend` records dollars spent and `conversion` records any purchase in the same two-week window. A positive spend paired with no purchase warrants investigation of the source definitions and recording. | Review |

The current implementation checks positive `spend` without `conversion`. It
does not check `conversion` with zero `spend` or `conversion` without a
`visit`. This coverage limitation is a review item to resolve before Issue #4,
subject to documented dataset semantics. It does not establish either omitted
combination as invalid or add a validity rule in Phase 1.

Consistency flags are counted separately from field validity. They report
a discrepancy without attributing it to a particular field. Missing or invalid
`conversion` or `segment` sets `HOLD` and explicitly pauses confirmatory
inference per frozen plan §5. Exit `2` means `HOLD`. Exit `0` means the audit
completed with `PASS` or `REVIEW`. Exit `1` means the CLI could not complete the
audit. A review finding stays open for technical review.

Duplicate-looking groups use exact CSV tokens across `recency`,
`history_segment`, `history`, `mens`, `womens`, `zip_code`, `newbie`, and
`channel`, including blank or invalid tokens. The audit counts groups of size
two or more, all records in those groups, and extra records beyond one per
group. Equal profiles can belong to different customers. The CSV has no
unique customer ID and all records are retained.

The CLI prints pooled quality counts, including missing and invalid totals
for `conversion`, `visit`, and `spend`, plus rule and gate status. See the
[dated audit log](../reports/data-quality-audit.md) for execution and follow-up.

## Phase 1.4 — Sample ratio mismatch (SRM)

Hillstrom's March 2008 challenge describes random assignment of approximately
one third of customers to each of the men's email, women's email, and no-email
arms. That post links directly to the same `2008.03.20.csv` URL recorded in
Phase 1.1. Scikit-uplift v0.3.1 identifies its dataset as a copy of the
MineThatData challenge dataset and repeats the three one-third allocations.
[Original March archive](https://blog.minethatdata.com/2008/03/?m=1) ·
[Challenge permalink](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) ·
[Scikit-uplift data description](https://www.uplift-modeling.com/en/v0.3.1/api/datasets/fetch_hillstrom.html#data-description)

Run from the repository root in PowerShell. This sequence verifies the Phase 1.1
hash, runs the Phase 1.2 structure check, and requires the Phase 1.3 audit to
complete without `HOLD` before starting SRM.

```powershell
$csv = 'data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
$expected = '0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece'
$actual = (Get-FileHash -LiteralPath $csv -Algorithm SHA256 -ErrorAction Stop).Hash
if ($actual -ne $expected) { throw "Checksum mismatch. Expected $expected, got $actual." }
.\.venv\Scripts\python.exe -m src.validate_schema $csv
if ($LASTEXITCODE -ne 0) { throw 'CSV structure validation failed.' }
.\.venv\Scripts\python.exe -m src.audit_data_quality $csv
$qualityExit = $LASTEXITCODE
if ($qualityExit -eq 2) { throw 'Phase 1.3 HOLD. SRM was not run.' }
if ($qualityExit -ne 0) { throw 'Phase 1.3 audit did not complete. SRM was not run.' }
.\.venv\Scripts\python.exe -m src.check_srm $csv
```

The SRM counter uses only `segment`. It retains every assignment and stops
before testing on a missing or illegal label. SciPy's Pearson chi-square test
uses `N/3` for each expected count, with no integer rounding and two degrees
of freedom. `p < 0.001` sets `HOLD` and pauses confirmatory interpretation
pending investigation. Exit `0` means the SRM gate did not trigger. Exit `1`
means the SRM input could not be tested, and exit `2` means SRM `HOLD`.
The gate checks the assignment proportions against the documented design.
[Frozen plan §5](https://github.com/rihua-tech/hillstrom-ab-testing/blob/plan-v1.1/01-experiment-analysis-plan.md#5-data-quality-and-randomization-diagnostics--ordered-gates)

See the [dated audit log](../reports/data-quality-audit.md#phase-14-srm-run--2026-11-26)
for the local execution and gate status.

## Phase 1.5 — Pre-treatment balance

After the Phase 1.4 gates, run the pre-treatment diagnostic from the repository
root with `.\.venv\Scripts\python.exe -m src.check_balance $csv`. It reads
`segment` for membership and the seven fields in frozen plan §5. The numeric
fields are `recency` and
`history` on their original scales. The binary fields are `mens`, `womens`,
and `newbie`. The nominal fields are `channel` and `zip_code`.

Use three signed diagnostic contrasts in this order: Men's minus Control,
Women's minus Control, and Women's minus Men's. For each, the SMD is
`(mean_left - mean_right) / sqrt((variance_left + variance_right) / 2)`.
Numeric variances are sample variances (`ddof = 1`). Each binary or nominal
level uses an indicator equal to one for that level and zero for all other
valid levels. Its mean is the valid-record proportion `p`, with variance
`p * (1 - p)`. Both levels of each binary field are shown, so their signed
SMDs mirror one another.

Each arm and field reports its full assignment total, valid denominator,
missing count, and invalid count. SMDs and categorical shares use valid
values for that field in each arm. All records remain in the population.
The Phase 1.3 validity rules are reused. A numeric value beyond the finite
floating-point range is also reported as invalid for this diagnostic.
Numeric diagnostics require at least two valid values per arm and indicators
require at least one. Insufficient values, zero pooled variance, or
non-finite SMDs are `UNDEFINED` and flagged for review.

`|SMD| > 0.10` is evaluated before display rounding. Findings (including
undefined diagnostics and missing or invalid values) set `REVIEW`. `PASS` and
`REVIEW` both exit `0`; unreadable or structurally invalid inputs exit `1`.
Balance flags are diagnostic review items. They preserve the full population
and the frozen analysis rules.

## Phase 1.6 — Independent SQL reconciliation

After the balance check, run
`.\.venv\Scripts\python.exe -m src.reconcile_assignments $csv` from the
repository root with the same verified CSV. Python and SQL independently
compute the assignment counts, but both paths share the same standard-library
Python CSV parser. The loader inserts one parsed `segment` value per data record
into an in-memory SQLite table. [The query](../sql/reconcile_assignments.sql)
uses `COUNT(*)` for the total and conditional counts for each exact arm, blank
or whitespace-only assignments, and other illegal labels. The query output
contains counts only.

The comparator checks the SQLite total against Python schema validation and the
three SQLite arm counts against the Python SRM counter. It also checks full
accounting, including missing and illegal labels. `PASS` exits `0`. Missing or
illegal labels, unavailable Python arm counts, incomplete accounting, or
a count difference produce `BLOCKED` and exit `2`. An unreadable or structurally
invalid input exits `1`. The reconciliation is an independent aggregation and
count check, not an independent CSV-parser check. The Claude Code
independent-review report also reproduced the assignment counts with pandas'
C parser, providing a parser-diverse verification. The earlier checks govern
the quality and SRM gates.

## Phase 1.7 — Full local Phase 1 workflow

Run from the repository root using the existing Windows virtual environment
and the local Phase 1.1 artifact. Each check completes before the next one.
A nonzero exit, including `HOLD` or a SQL blocker, stops the sequence.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $csv = 'data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
    $expected = '0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece'
    $actual = (Get-FileHash -LiteralPath $csv -Algorithm SHA256 -ErrorAction Stop).Hash
    if ($actual -ne $expected) { throw "Checksum mismatch. Expected $expected, got $actual." }
    "SHA-256 verified: $actual"

    $phase1Python = '.\.venv\Scripts\python.exe'
    $phase1Modules = @(
        'src.validate_schema',
        'src.audit_data_quality',
        'src.check_srm',
        'src.check_balance',
        'src.reconcile_assignments'
    )
    foreach ($phase1Module in $phase1Modules) {
        & $phase1Python -m $phase1Module $csv
        if ($LASTEXITCODE -ne 0) { throw "$phase1Module exited $LASTEXITCODE." }
    }
}
```

Local verification uses synthetic fixtures and the Git ignore rules:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
git diff --check
git check-ignore -v -- data/raw/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv
git ls-files -- data/raw/
```

See the [consolidated audit](../reports/data-quality-audit.md#phase-17-consolidated-acceptance)
for the executed checks, review decisions, and remaining limitations.
