# Board B 044701 Stable Terminal Readback v1

Run id: `20260512T045841+0800-codex-board-b-044701-stable-terminal-readback-v1`

Source run: `20260512T044701-codex-source-label-single-atom-qualifier-scan-v1`

Gate result: `044701_stable_terminal_readback_v1=single_atom_scored_no_full_acceptance_no_promotion`

## Readback

- The prior reopened-writer guard observed an active writer against `044701`, so Board B could not consume it then.
- A fresh process readback at `2026-05-12T04:58:17+0800` and `2026-05-12T04:58:30+0800` showed no remaining `90697/90743/91172` source-label writer PIDs.
- The terminal source packet hashes were stable across both readbacks.
- Source gate result: `source_label_single_atom_qualifier_scan_v1=single_atom_scored_no_full_acceptance`.
- Source row count: `248440`.
- Accepted single-atom confidence-95 labels: `[]`.
- Promotion fields stayed false: `accepted_rows_added=0`, `new_confidence_gate=false`, `source_control_evidence_acquired=false`, `canonical_merge=false`, `downstream_promotion_rerun=false`, `strict_full_objective=false`, `trade_usable=false`, `update_goal=false`.
- Best single-atom rules for Bear, Bull, Crisis, and Sideways all failed required calibration, heldout-market, heldout-time, and test Wilson 95 lower-bound checks.

## Stable Hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `command-output/source_label_single_atom_qualifier_scan.exit` | `2` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `command-output/source_label_single_atom_qualifier_scan.stdout.json` | `3920` | `fde7df9752ca476746e7140ff4511690de4ba66a949f25a7d48ac29ca3769804` |
| `command-output/source_label_single_atom_qualifier_scan.stderr.txt` | `0` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `source-label-single-atom-qualifier-scan-v1/source_label_single_atom_qualifier_scan_v1.json` | `3919` | `1b224fb3f052b551889531319085e1795bf892a6b1ac0997c9eadc6051972e23` |
| `source-label-single-atom-qualifier-scan-v1/source_label_single_atom_qualifier_scan_v1.md` | `1741` | `3f4abf4cde43c050c7cea65e328a326af7273998515db97009fad28cd9429412` |
| `checks/source_label_single_atom_qualifier_scan_v1_assertions.out` | `469` | `0173219ba2909ed9af09a8754aaef1715e8ea9388226e70e00d094310cc25c3d` |

## Gate

- `diagnostic_only:044701_stable_terminal_readback`.
- `fail_closed:no_single_atom_confidence_95_labels`.
- `fail_closed:all_best_rules_wilson95_below_threshold`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Keep `034002` as the fail-closed cursor. The next qualifying Board B action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, then selected-data Auto-Quant/factor-research with nonzero mature rooted observations and downstream preservation through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
