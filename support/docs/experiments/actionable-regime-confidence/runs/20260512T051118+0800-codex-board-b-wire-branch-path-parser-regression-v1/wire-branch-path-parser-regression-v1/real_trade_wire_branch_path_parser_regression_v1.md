# Real-Trade Wire Branch-Path Parser Regression v1

Run id: `20260512T051118+0800-codex-board-b-wire-branch-path-parser-regression-v1`

Gate result: `real_trade_wire_branch_path_parser_regression_v1=parser_supported_no_promotion`

Purpose: verify that Auto-Quant real-trade JSONL records can carry the full rooted Board B branch path into `FeedbackRecord` without requiring a pre-existing `structural_feedback` object.

## Code Path

- `src/application/auto_quant/real_trades/wire.rs`
- Added optional record-level fields:
  - `regime_profit_branch_path`
  - `main_regime`
  - `sub_regime`
  - `sub_sub_regime_or_profit_factor`
  - `profit_factor`
- `into_feedback_record` now injects a `regime_profit_branch_path` factor usage and synthesizes `StructuralFeedbackRefs` when the record has a branch path but no explicit structural refs.
- Explicit-path-only records now parse `node_id`, `branch_id`, and `scenario_id` from the four-part `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` string.

## Verification

Command:

```bash
CARGO_TARGET_DIR=/tmp/ict-engine-codex-branch-path-wire-target-v2 cargo test regime_profit_branch_path --lib -- --nocapture
```

Result:

- `2` tests passed.
- `0` tests failed.
- `935` tests filtered out.
- Runtime: `8m 58s`.

Passing tests:

- `application::auto_quant::real_trades::wire::tests::record_level_regime_profit_branch_path_becomes_structural_feedback_and_factor_usage`
- `application::auto_quant::real_trades::wire::tests::explicit_regime_profit_branch_path_recovers_structural_segments_without_split_fields`

## Decision

This is parser/wire support only. It does not select historical data, create selected-data mature rooted observations, prove profitability, promote any candidate, or call `update_goal`.

The Board B gate remains blocked by `user_selected_historical_data_missing`.
