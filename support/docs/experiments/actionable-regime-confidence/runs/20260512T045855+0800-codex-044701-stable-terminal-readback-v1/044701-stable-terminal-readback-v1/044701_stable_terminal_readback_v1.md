# 044701 Stable Terminal Readback v1

Snapshot: `20260512T045855+0800`

This is a diagnostic readback of `20260512T044701-codex-source-label-single-atom-qualifier-scan-v1` after the active writer family exited and hashes stabilized.

## Evidence

- Board hash before writeback: `34a12fc2b338f4042f6517560dbf78e3651334f307d739190a273bf689a03258`.
- Writer PIDs `90697/90743/91172` were no longer present in `ps -p`.
- Command exit content: `0`.
- `source_label_single_atom_qualifier_scan.exit`: `2` bytes, sha256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3ab86aa`.
- `source_label_single_atom_qualifier_scan.stdout.json`: `3920` bytes, sha256 `fde7df9752ca476746e7140ff4511690de4ba66a949f25a7d48ac29ca3769804`.
- `source_label_single_atom_qualifier_scan.stderr.txt`: `0` bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- `source_label_single_atom_qualifier_scan_v1.json`: `3919` bytes, sha256 `1b224fb3f052b551889531319085e1795bf892a6b1ac0997c9eadc6051972e23`.

## Result

- `gate_result`: `source_label_single_atom_qualifier_scan_v1=single_atom_scored_no_full_acceptance`.
- `accepted_single_atom_confidence_95_labels`: `[]`.
- `promotion_status.accepted_rows_added=0`.
- `promotion_status.canonical_merge=false`.
- `promotion_status.downstream_promotion_rerun=false`.
- `promotion_status.source_control_evidence_acquired=false`.
- `promotion_status.strict_full_objective=false`.
- `promotion_status.trade_usable=false`.
- `promotion_status.update_goal=false`.

Per-label single-atom gates all failed the required Wilson 95 lower-bound checks:

| label | accepted | min_split_support | min_split_wilson95_lcb | blockers |
|---|---:|---:|---:|---|
| Bear | false | 455 | 0.4249084736 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Bull | false | 12677 | 0.5353234712 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Crisis | false | 520 | 0.4324193032 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Sideways | false | 5770 | 0.3488806669 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |

## Gate

- `diagnostic_only:044701_stable_terminal_readback`
- `fail_closed:no_single_atom_confidence_95_labels`
- `fail_closed:all_single_atom_wilson95_below_threshold`
- `accepted_rows_added=0`
- `canonical_merge_allowed=false`
- `downstream_rerun_allowed=false`
- `blocked:user_selected_historical_data_missing`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not promote from `044701`. Keep `034002` as the fail-closed cursor. The next qualifying Board B action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, then selected-data Auto-Quant with nonzero mature rooted branch observations through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
