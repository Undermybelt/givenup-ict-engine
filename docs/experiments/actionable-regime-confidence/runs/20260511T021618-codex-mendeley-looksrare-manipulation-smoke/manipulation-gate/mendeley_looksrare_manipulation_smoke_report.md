# Mendeley LooksRare Manipulation Smoke Gate

Run ID: `20260511T021618+0800-codex-mendeley-looksrare-manipulation-smoke`

## Result

- Raw file acquired: true (`/tmp/LooksRare_ml_samples.csv`)
- SHA-256 matches Mendeley metadata: true
- Rows: 401125
- Label counts: {'False': 237930, 'True': 163195}
- Explicit timestamp column present: false
- Best diagnostic minimum Wilson95 LCB: 0.878134
- Accepted 95 `Manipulation`: false

This is useful acquisition progress, but it is not root acceptance. The file lacks an explicit chronological key, and the unchanged single-threshold smoke gate found no rule that passes train, calibration, and test lower-bound checks.

## Files

- Report JSON: `manipulation-gate/mendeley_looksrare_manipulation_smoke_report.json`
- Rule summary: `manipulation-gate/mendeley_looksrare_rule_summary.csv`
- Assertions: `checks/mendeley_looksrare_manipulation_smoke_assertions.out`
