# Mendeley Multifile Manipulation Gate

Run ID: `20260511T022630+0800-codex-mendeley-multifile-manipulation-gate`

This gate streams Mendeley row-level wash-trading ML samples from `/tmp` and keeps only aggregate metrics, rule summaries, and hashes in the repo.

## Result

- Accepted 95 `Manipulation`: False
- Gate: `blocked_mendeley_multifile_no_chronology_grade_95_rule`
- Raw data committed: false
- Thresholds relaxed: false
- Runtime code changed: false
- Fresh calibration rerun: true

## Files Evaluated

- LooksRare: rows 401125, sha256_match True, chronology `blocked_file_order_not_global_chronology`, accepted_rule_only False, best_min_wilson95_lcb 0.917286
- Blur: rows 3461736, sha256_match True, chronology `blocked_file_order_not_global_chronology`, accepted_rule_only False, best_min_wilson95_lcb 0.959330
- Gox: rows 5537252, sha256_match True, chronology `indirect_source_script_chronology`, accepted_rule_only False, best_min_wilson95_lcb 0.887193
- OpenSea: missing in `/tmp`, skipped

## Blockers

- no strict non-leaky rule passed train/calibration/test 95% Wilson lower-bound support and coverage gates with chronology-grade evidence
- NFT ML samples drop timestamp and are written in contractAddress,timestamp order, so file-order splits are not global chronological evidence
- missing raw files in /tmp: OpenSea

## Artifacts

- Report JSON: `manipulation-gate/mendeley_multifile_manipulation_gate_report.json`
- Rule summary CSV: `manipulation-gate/mendeley_multifile_rule_summary.csv`
- Assertions: `checks/mendeley_multifile_manipulation_gate_assertions.out`
