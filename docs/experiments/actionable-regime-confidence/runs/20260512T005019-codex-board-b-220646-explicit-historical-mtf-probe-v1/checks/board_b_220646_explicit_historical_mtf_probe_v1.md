# Board B 220646 Explicit Historical MTF Probe v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T005019-codex-board-b-220646-explicit-historical-mtf-probe-v1`

Scope: supplemental exact-branch readback for `SourceRootStopCarryLongHorizonV1` / `SRC_ROOT_CARRY_LONG_220646`. This run does not own the current Board B cursor and does not promote the candidate.

## Ordered Readback

1. `auto-quant-status` started at `missing_dependency` with `auto_quant_bootstrap_required`.
2. `auto-quant-bootstrap --repo-url /Users/thrill3r/Auto-Quant` exited `0`; managed Auto-Quant became dependency-healthy at commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`.
3. `factor-research` on the recorded `163704` MTF paths exited `0` and emitted an Auto-Quant handoff, but readiness was `dependency_ready_data_missing` and `data_ready=false`.
4. `auto-quant-prepare` did not complete:
   - CLI prepare attempts exited `1` through a relative-script spawn failure.
   - direct `prepare.py` failed with `ModuleNotFoundError: No module named 'freqtrade'`.
   - managed-cwd `uv run --with ta-lib prepare.py` was terminated after idle/no output for more than 150s.
5. `factor-backtest` on the same recorded MTF paths was terminated after long-running/no output for more than 300s.
6. Downstream readbacks were callable and branch identity stayed visible:
   - providers: yfinance ready, Kraken CLI ready, IBKR bridge/market-data dependency-unhealthy with gateway reachable, TradingView MCP unhealthy, Kraken public dependency-unhealthy.
   - Pre-Bayes: `pass_neutralized`, policy `318900600c5e8cf2`, `regime_bundle_branch_path_count=4`, `regime_bundle_stable_profit_score=0.857407`.
   - branch paths preserved: Bull, Bear, Sideways, and Crisis paths all still point to `SourceRootStopCarryLongHorizonV1`.
   - structural feedback latest path: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`.
   - path-ranker runtime: ready, candidate-set source, `active_match_count=4`, `raw_scored_mature=866/30`, `production_validation=866/30`, `observation_validation=82/30`.
   - structural export: `rows=4`, `history_rows=877`, `history_mature_rows=866`.
7. Workflow refresh included the `005019` Auto-Quant handoff as `prepare_required`. Existing ready/promote labels still point at earlier analyze-live artifacts and are not exact branch promotion evidence.

## Gate

`pass:bootstrap_and_downstream_readbacks_callable`

`fail_closed:auto_quant_data_missing_prepare_backtest_timeout_no_exact_execution_tree_promotion`

Promotion allowed: `false`.

## Next

Do not promote from this run. Continue from the active Board B cursor or a prepared explicit-historical Auto-Quant workspace; require the same rooted branch path to pass Auto-Quant/replay, Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree admission before any promotion claim.

