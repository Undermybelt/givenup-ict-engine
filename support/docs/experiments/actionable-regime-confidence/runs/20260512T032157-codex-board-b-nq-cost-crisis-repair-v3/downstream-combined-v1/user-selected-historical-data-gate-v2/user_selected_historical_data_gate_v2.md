# User-Selected Historical Data Gate v2

Scope: non-promoting selection-gate correction for Board B `034002/downstream-combined-v1`.

This artifact does not edit the Board B Current Cursor, does not satisfy `user_selected_historical_data`, does not run factor-research or Auto-Quant, and does not call `update_goal`.

## Why v2 Exists

`user-selected-historical-data-gate-v1/user_selected_historical_data_gate_v1.md` contains a stale interval correction that says `MTF=1h` and `LTF=15m`. Later direct timestamp readback proves the actual candidate-file cadence is `HTF=1d`, `MTF=4h`, and `LTF=1h`.

This v2 artifact supersedes stale interval wording in v1. It does not change the candidate file paths or the blocking gate.

## Current Gate

The active Board B cursor remains:

- `last_loop_id`: `20260512T034002+0800-codex-board-b-nq-cost-crisis-repair-v3-downstream-combined-v1`
- `hard_gate_result`: `fail:downstream_closed_loop_not_promotable`
- `downstream_consumption`: `execution_tree:fail_closed`
- `blocker`: `user_selected_historical_data_missing`

`034002/downstream-combined-v1` mechanically ran Auto-Quant import/prior/real-trade ingest, Pre-Bayes readback, BBN-visible analysis, CatBoost/path-ranker training and registration, workflow readback, and execution-candidate readback. That is not enough for promotion because Pre-Bayes stayed `observe_only`, path-ranker validation stayed `0/30`, execution-candidate stayed blocked/not actionable, and workflow still requires explicit user-selected historical data.

## Correct Candidate Options

| Option | File | Actual cadence | Candles | First timestamp | Second timestamp | Last timestamp | SHA-256 |
|---|---|---:|---:|---|---|---|---|
| `HTF` | `state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_htf.json` | `1d` | 260 | `2025-03-03T00:00:00Z` | `2025-03-04T00:00:00Z` | `2025-12-31T00:00:00Z` | `9c737d7c9e198069ac2b91b8786d015912769e829167047901480d76043f6bb0` |
| `MTF` | `state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_mtf.json` | `4h` | 260 | `2025-10-31T16:00:00Z` | `2025-10-31T20:00:00Z` | `2025-12-31T20:00:00Z` | `807587969339bb879cd3bc6a72d57d53c84b75b501e1df9875e833c9b6d06752` |
| `LTF` | `state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_ltf.json` | `1h` | 260 | `2025-12-15T12:00:00Z` | `2025-12-15T13:00:00Z` | `2025-12-31T21:00:00Z` | `d38aea3d620ea56e12af08d11a22929daa076fcd8bdbe5e630f2b059acd244da` |

Full file prefix:

`docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/`

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T041042-codex-board-b-032157-historical-data-selection-options-v1/selection-options/historical_data_selection_interval_readback_v2.md`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041042-codex-board-b-032157-historical-data-selection-options-v1/selection-options/historical_data_selection_options_v1.md`
- `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/command-output/14_workflow_structural_bundle.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/command-output/16_workflow_full.out`

## Next Command Shape After Selection

After the user explicitly selects exactly one of `HTF`, `MTF`, or `LTF`, use the selected file in an isolated state. Do not treat the workflow's deferred `LTF` command as a user selection.

```bash
./target/debug/ict-engine factor-research \
  --symbol B2R_NQ_COST_CRISIS_REPAIR_032157 \
  --data docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_<selected>.json \
  --state-dir <isolated-state-dir> \
  --backend auto-quant \
  --auto-quant-profile synthetic_ohlcv \
  --output-format json
```

## Promotion Gate

Promotion remains blocked unless the selected run emits nonzero mature rooted branch observations and preserves the same branch identity through:

`main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`

Then the same branch path must pass:

`Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree`

## Gate Status

- `blocked:user_selected_historical_data_missing`
- `not_started:selected_data_factor_research`
- `not_started:selected_data_pre_bayes_bbn_catboost_execution_tree`
- `promotion_allowed=false`

