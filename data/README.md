# Dataset handling policy

**Phase 0:** No raw or processed Hillstrom experiment data are present. No treatment-group outcome values have been inspected or computed.

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
