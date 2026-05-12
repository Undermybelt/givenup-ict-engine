# Board B 045830/045926 Terminal Readback v1

Run id: `20260512T050517+0800-codex-board-b-045830-045926-terminal-readback-v1`

Source runs:
- `20260512T045830-codex-source-label-extra-trees-threshold-screen-v1`
- `20260512T045926-codex-source-label-three-atom-qualifier-miner-v1`

Gate result: `045830_045926_terminal_readback_v1=terminal_fail_closed_no_promotion`

## Readback

- Both previously active writer families were absent during the terminal readback.
- Hashes for both source packets were stable across two reads.
- `045830` terminated with exit content `143`, stdout `0` bytes, stderr `227` bytes, and no report/assertions payload. It is not consumable confidence evidence.
- `045926` exited `0` and produced report/assertions payloads, but gate result was `source_label_three_atom_qualifier_miner_v1=three_atom_scored_no_full_acceptance`.
- `045926` scored `248440` rows and accepted no three-atom confidence-95 labels: `accepted_three_atom_confidence_95_labels=[]`.
- `045926` promotion fields stayed false: `accepted_rows_added=0`, `new_confidence_gate=false`, `source_control_evidence_acquired=false`, `canonical_merge=false`, `downstream_promotion_rerun=false`, `strict_full_objective=false`, `trade_usable=false`, and `update_goal=false`.

## 045926 Best Gates

| Label | Accepted 95 | Min Support | Min Wilson95 | Kind | Blockers |
|---|---:|---:|---:|---|---|
| `Bear` | `false` | `26` | `0.6435280915` | `3_atom_conjunction` | calibration below 0.95; heldout market support below 50; heldout/test Wilson below 0.95 |
| `Bull` | `false` | `181` | `0.7986296577` | `3_atom_conjunction` | calibration, heldout market, heldout time, and test Wilson below 0.95 |
| `Crisis` | `false` | `520` | `0.4324193032` | `1_atom_conjunction` | calibration, heldout market, heldout time, and test Wilson below 0.95 |
| `Sideways` | `false` | `3421` | `0.3659108855` | `2_atom_conjunction` | calibration, heldout market, heldout time, and test Wilson below 0.95 |

## Stable Hashes

| File | Bytes | SHA-256 |
|---|---:|---|
| `045830/command-output/source_label_extra_trees_threshold_screen.exit` | `4` | `9d9b18720961e9b4689fd763b85e7b6f36160ccd3a8a1c9ddc5103bb0f66c396` |
| `045830/command-output/source_label_extra_trees_threshold_screen.stdout.json` | `0` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `045830/command-output/source_label_extra_trees_threshold_screen.stderr.txt` | `227` | `664ad5d057ec2b4da0dafa47497c2d7d2bb19dc8ef7303250e63e153c663e898` |
| `045926/command-output/source_label_three_atom_qualifier_miner.exit` | `2` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `045926/command-output/source_label_three_atom_qualifier_miner.stdout.json` | `4332` | `109c944106e317eb28f348aa34662a4c6f0183d2fcc6c2e40b864f24ff6a4e3d` |
| `045926/command-output/source_label_three_atom_qualifier_miner.stderr.txt` | `0` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `045926/source-label-three-atom-qualifier-miner-v1/source_label_three_atom_qualifier_miner_v1.json` | `4331` | `67325ce596db8ff0a8f0bf13dea94900aee958e23087050efa517aa242539a28` |
| `045926/checks/source_label_three_atom_qualifier_miner_v1_assertions.out` | `467` | `5a414fd5b42927f1b65542f6bf7317b72fcc6e6fbc8282c0cb56dfc3561ab7b5` |

## Gate

- `diagnostic_only:045830_045926_terminal_readback`.
- `fail_closed:045830_exit143_no_payload`.
- `fail_closed:045926_no_three_atom_confidence_95_labels`.
- `fail_closed:no_new_confidence_gate`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Keep `034002` as the fail-closed cursor. The next qualifying Board B action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data Auto-Quant/factor-research that emits nonzero mature rooted branch observations and preserves the branch path through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
