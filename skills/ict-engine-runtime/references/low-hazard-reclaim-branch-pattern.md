# Low-hazard reclaim branch pattern

Use this reference when a dense K-line reclaim branch has positive Auto-Quant/provider profitability but execution stays `observe/transition_guardrail/guarded`, and the user wants a new profitability factor rather than rerunning the same branch.

## Pattern

Split a stricter factor under the same frozen root, e.g.:

```text
TrendExpansion -> SessionLiquidity -> dense_kline_low_hazard_reclaim -> low_hazard_reclaim_long_v1
```

The new factor should be different by real ownership axis (`sub_sub_regime_or_profit_factor` and `profit_factor`), not a same-factor replay.

## Strategy shape

For Freqtrade-style material, reduce transition-hazard exposure with simple, auditable filters:

- `close > open`
- `close > EMA20`
- candle `body_ratio > 0.20`
- `45 < RSI14 < 69`
- `ATR14/close < rolling_mean20(ATR14/close) * 1.25`
- `0 < volume < SMA20(volume) * 2.2`
- tighter stop/ROI than dense upbar reclaim, e.g. `stoploss=-0.010`, `minimal_roi={"0":0.0035,"10":0}`

This is a seed-discovery gate, not an execution permission.

## Runtime chain checklist

1. Create an ephemeral claim in `/tmp/ict-engine-agent-claims/board-b/` before touching artifacts.
2. Reuse existing provider K-line material only when provenance is known; do not retouch Board A labels.
3. Build material JSON with full branch fields:
   - `branch_path`
   - `regime_profit_branch_path`
   - `main_regime`
   - `sub_regime`
   - `sub_sub_regime_or_profit_factor`
   - `profit_factor`
   - provider/timeframe/source rows
4. Run `auto-quant-agent-material-batch`, `dispatch`, and `rank`.
5. Build a strategy library from completed rank rows only.
6. Run `auto-quant-results-import` and `auto-quant-prior-init`.
7. Run `analyze`, `workflow-status`, `pre-bayes-status`, and `export-structural-path-ranking-target`.
8. Train/apply CatBoost:
   ```bash
   python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py --target-csv <target.csv> --output-dir <model-dir> --model-family catboost
   python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py --apply --model-dir <model-dir> --target-csv <target.csv> --output-scores <scores.csv>
   ```
9. Apply/register/enable ranker scores.
10. Rerun `analyze` after enabling the ranker. Without this second analyze, `execution_tree_trace.json` may still show `ranker=unknown` even though scores were applied.
11. Verify nested `execution_tree_trace.json.output.*`:
    - `path_ranker_score_visible_to_execution_tree=true`
    - `path_ranker_score_used_by_execution_tree=true`
    - `path_ranker_model_family=catboost`
    - final `gate_status`, `branch`, `execution_bias`, and `decision_hint`

## Local Auto-Quant source workaround

If `--repo-url <existing aq_workspace>` fails because the workspace has no `.git`, copy it into the run root and initialize a local git repo before passing it to `--repo-url`:

```bash
rsync -a --exclude user_data/backtest_results --exclude user_data/data <aq_workspace>/ <run>/local_auto_quant_source/
git init -b master <run>/local_auto_quant_source
git -C <run>/local_auto_quant_source add .
git -C <run>/local_auto_quant_source -c user.email=hermes@example.invalid -c user.name=hermes commit -m 'local auto-quant source for replay'
```

This captures the reusable retry pattern; do not record the original clone failure as a durable tool limitation.

## Decision rule

`visible=true` and `used=true` prove consumption, not promotion.

Keep decision as `incubate` or `blocked` when any of these remain:

- CatBoost trained from pseudo-label or tiny structural target rows.
- `mature_rows=0`.
- `raw_scored_mature=0/30`.
- `production_validation=0/30`.
- `observation_validation=0/30`.
- execution stays `observe/transition_guardrail/guarded`.

Next unclaimed work should export/replay real per-trade rows for the exact new branch, then re-check validation and transition hazard.
