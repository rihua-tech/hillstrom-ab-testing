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
