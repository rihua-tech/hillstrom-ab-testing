# Dataset handling policy

**Phase 0:** No raw or processed Hillstrom experiment data are present. No treatment-group outcome values have been inspected or computed.

**After the analysis-plan freeze commit:** Acquire the original/public data from a documented source. Record URL, retrieval timestamp, license/redistribution status, exact file name, SHA-256 hash, known schema, and any transformations before analyzing outcomes.

Keep raw and intermediate data out of Git by default. Do not silently remove duplicates, impute missing outcomes as zero, or filter records using post-treatment behavior. See `../01-experiment-analysis-plan.md` for outcome-blind quality gates.
