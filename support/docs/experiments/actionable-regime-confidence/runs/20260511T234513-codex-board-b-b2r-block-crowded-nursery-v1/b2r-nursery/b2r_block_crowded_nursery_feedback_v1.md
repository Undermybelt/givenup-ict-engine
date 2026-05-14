# B2R Block-Crowded Nursery Feedback v1

Run id: `20260511T234513+0800-codex-board-b-b2r-block-crowded-nursery-v1`

## Decision

- Nursery status: `incubation_only`
- Promotion allowed: `false`
- Exact branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- RC-SPA score: `85.74074074074075`; gate `pass`; price roots `4/4`
- Pre-Bayes/filter: `pass_neutralized`
- BBN probe: `skipped`
- CatBoost/path-ranker: `enabled_candidate_set_ready`; validation `Ranker validation: calibration=true quality_ready=true raw_scored_mature=275/30 production_validation=274/30 observation_validation=48/30 ready=true`
- Execution tree: `block_crowded` / `blocked`
- Blocker: `market_state=RangeConsolidation/WideRange | execution=blocked/block_crowded/skip | ranker=history_path/unknown/ready`

## Provider Readback

| Provider | Fresh result | Artifact |
|---|---|---|
| `yfinance` | harness ok `1` exit `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/provider/harness_yfinance_qqq_1d.out` |
| `TradingViewRemix/tradingview_mcp` | harness ok `0` errors `1` exit `1` | `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/provider/harness_tradingview_qqq_1d.out` |
| `IBKR` | harness ok `0` errors `0` exit `1` | `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/provider/harness_ibkr_qqq_1d.out` |
| `Kraken CLI` | OHLC rows `721` exit `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/provider/kraken_cli_xbtusd_1h_ohlc.out` |

## Auto-Quant Readback

- Local visibility: `{'config_json': True, 'data_files': 43, 'python': '3.11.11', 'run_py': True, 'strategies_external_files': 1, 'strategies_files': 0}`
- Source Auto-Quant/RC-SPA artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json`
- `run.py --help` exit `2`; this is a default-strategy discovery issue, not a blocker for the existing `220646` sourced artifact.

## Nursery Row

- CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-nursery/b2r_block_crowded_nursery_feedback_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-nursery/b2r_block_crowded_nursery_feedback_v1.json`

## Next

Accumulate more non-crowded compatible execution-context observations before rerunning 220646 promotion readback.
