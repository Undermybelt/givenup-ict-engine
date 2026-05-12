# RootAwareRegimeSwitch B2R v1

Run id: `20260511T182138+0800-codex-board-b-rootaware-recipe-b2r-v1`.

## Decision

- Gate result: `reject_b2r_insufficient_root_coverage`
- Selected for B3: `false`
- Reason: RootAwareRegimeSwitch ran as a real Auto-Quant/Freqtrade strategy, but did not produce trades across Bull/Bear/Sideways/Crisis.

## Aggregate

- Trades: `0`
- Win rate: `0.0000`
- Total profit pct: `0.0000`
- Profit factor: `0.0000`
- Sharpe: `0.0000`

## Root Summary

| Root | Trades | Folds | Win Rate | Sum Profit Ratio | Path |
|---|---:|---:|---:|---:|---|
| Bull | 0 | 0 | 0.0000 | 0.000000 | `Bull->no_rows->no_rows->RootAwareRegimeSwitch` |
| Bear | 0 | 0 | 0.0000 | 0.000000 | `Bear->no_rows->no_rows->RootAwareRegimeSwitch` |
| Sideways | 0 | 0 | 0.0000 | 0.000000 | `Sideways->no_rows->no_rows->RootAwareRegimeSwitch` |
| Crisis | 0 | 0 | 0.0000 | 0.000000 | `Crisis->no_rows->no_rows->RootAwareRegimeSwitch` |
| Manipulation(scoped) | 0 | 0 | 0.0000 | 0.000000 | `Manipulation(scoped)->DirectEventOverlayMissing->no_direct_event_rows->suppress_or_abstain` |

## Artifacts

- Strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T182138-codex-board-b-rootaware-recipe-b2r-v1/strategies/RootAwareRegimeSwitch.py`
- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T182138-codex-board-b-rootaware-recipe-b2r-v1/rootaware-rc-spa/rootaware_regime_switch_b2r_report_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T182138-codex-board-b-rootaware-recipe-b2r-v1/rootaware-rc-spa/rootaware_regime_switch_trades_v1.csv`
- Root summary: `docs/experiments/actionable-regime-confidence/runs/20260511T182138-codex-board-b-rootaware-recipe-b2r-v1/rootaware-rc-spa/rootaware_regime_switch_root_summary_v1.csv`

## Next

- B2R: synthesize another root-aware recipe or loosen only the recipe logic, not the RC-SPA gates.
