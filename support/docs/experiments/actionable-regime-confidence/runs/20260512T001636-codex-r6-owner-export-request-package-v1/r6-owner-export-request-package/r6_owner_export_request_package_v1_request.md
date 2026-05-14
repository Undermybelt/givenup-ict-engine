# R6 Owner Export Request Package v1

Target intake root: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required files:
- `direct_manipulation_positive_rows.csv`
- `direct_manipulation_matched_controls.csv`
- `direct_manipulation_provenance.json`

Minimum distribution:
- Exact contract unchanged: V59 says exact-symbol debt is `2559` pairwise rows and exact-venue debt is `732`.
- Family contract path: requires explicit owner/user approval first, and V60 still fails on current rows.
- Missing species must include matched controls and provenance, not labels inferred from raw order book data.

After files arrive:
1. Run unchanged direct intake verifier.
2. Rerun chronological/symbol/venue or approved-family split calibration.
3. Rerun provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
4. Write the result back to the same Board A markdown before claiming acceptance.
