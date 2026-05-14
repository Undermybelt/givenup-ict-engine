# 043932 Stable Terminal Readback v1

Snapshot: `20260512T045302+0800`

This is a diagnostic readback of `20260512T043932-codex-source-label-rule-qualifier-miner-v1` after the shared command-output files stopped changing and no direct miner writer remained visible.

## Evidence

- Board hash before writeback: `42cfded7806b11b9c02b9e3d6e4e55c9d01a5e972bbbe3c5c99fdc7f095b8b41`.
- Command exit content: `0`.
- `source_label_rule_qualifier_miner.exit`: `2` bytes, sha256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.
- `source_label_rule_qualifier_miner.stdout.json`: `3888` bytes, sha256 `d5fc065270136cc522a9510ee224725bf09c1a9f116abdf3547db66d6ba29020`.
- `source_label_rule_qualifier_miner.stderr.txt`: `0` bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- No direct `source_label_rule_qualifier_miner_v1.py` Python or `uv` writer remained visible; only watcher shell commands still matched the source path text.

## Result

- `gate_result`: `source_label_rule_qualifier_miner_v1=rules_scored_no_full_acceptance`.
- `accepted_rule_confidence_95_labels`: `[]`.

Per-label best-rule gates all failed the required Wilson 95 lower-bound checks:

| label | accepted | min_split_support | min_split_wilson95_lcb | blockers |
|---|---:|---:|---:|---|
| Bear | false | 134 | 0.566325058 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Bull | false | 338 | 0.7054974201 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Crisis | false | 1074 | 0.4729340579 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |
| Sideways | false | 3421 | 0.3659108855 | calibration, heldout_market, heldout_time, and test Wilson 95 below 0.95 |

## Gate

- `diagnostic_only:043932_stable_terminal_readback`
- `fail_closed:no_confidence_95_rule_labels`
- `fail_closed:all_best_rules_wilson95_below_threshold`
- `blocked:user_selected_historical_data_missing`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not promote from `043932`. The active board remains blocked by `user_selected_historical_data_missing`; the next qualifying Board B action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data Auto-Quant and downstream branch-path preservation through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
