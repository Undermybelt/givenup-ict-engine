# 124408 Signal Export Diagnostic v1

Generated: 2026-05-12T13:00:55+0800

Source run root: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T125232+0800-codex-124408-signal-export-diagnostic-v1`

## Scope

Diagnose why the settled `124408` TOMAC trade-density iteration produced zero trades even though the selected-history BTC/USD data and strategy files loaded successfully.

This root does not mutate repo runtime code, BBN CPDs, CatBoost models, execution-tree gates, or the `124408` source state. The precision-fix probe is in-memory only and is not a promotion claim.

## Readback

- Plain `freqtrade backtesting --export signals` exited `2` for all three strategies because the CLI path loaded remote Binance market metadata and hit DNS. The existing `run_tomac.py` synthetic-exchange path is required for this isolated workspace.
- The synthetic-exchange path confirms the strategies do generate entry signals after Freqtrade startup trimming:
  - `TomacAggressiveBE`: `150` trade-direction rows.
  - `TomacKillzoneBreakout`: `65` trade-direction rows.
  - `TomacRRWinRate`: `1` non-colliding trade-direction row.
- The zero-trade blocker is not missing signals. It is order amount precision.
- The synthetic market uses `precision.amount = 8`, while the resolved exchange precision mode is tick-size mode (`4`). Under tick-size semantics, `8` means an 8 BTC amount step, not 8 decimal places.
- First-entry stake sizing produced valid stake and raw amount, then rounded the order amount to zero:
  - `TomacAggressiveBE`: raw `1.4748598202305097` BTC -> rounded `0.0`.
  - `TomacKillzoneBreakout`: raw `1.4285424402913902` BTC -> rounded `0.0`.
  - `TomacRRWinRate`: raw `1.3814685887598475` BTC -> rounded `0.0`.

## Precision-Fix Probe

An in-memory probe changed only the synthetic market precision to amount tick size `1e-8` under the same Freqtrade path. It produced nonzero trades:

| Strategy | Trades | Total profit % | Win rate % | Sharpe | Profit factor |
|---|---:|---:|---:|---:|---:|
| `TomacAggressiveBE` | 94 | 2.72 | 24.4681 | 3.1752 | 1.4726 |
| `TomacKillzoneBreakout` | 49 | -2.25 | 20.4082 | -2.4522 | 0.6450 |
| `TomacRRWinRate` | 1 | 0.00 | 0.0000 | -100.0000 | 0.0000 |

Total diagnostic trades after the precision fix: `144`.

## Decision

- Gate: `124408_signal_export_diagnostic_precision_amount_root_cause`.
- Root cause: `run_tomac.py` synthetic market precision used decimal-place style values under tick-size mode, causing every intended BTC order amount to round to `0.0`.
- Candidate package availability changed from false to diagnostic-only true after the in-memory precision fix, but this still needs a settled rerun and ordered downstream consumption before any Board A promotion.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Create a settled isolated rerun that patches only the copied Auto-Quant TOMAC runner or monkey-patches the synthetic market precision in an auditable wrapper. If the nonzero trades persist, export the measured candidate package and pass it through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree before any promotion claim.

