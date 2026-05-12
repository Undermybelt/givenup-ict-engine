# Provider-Backed Regime Validation Smoke Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1`

## Scope

This is a provider-backed market-state validation smoke over the strongest immediately available long-window inputs from the `141554` provider capability matrix. It validates that current provider data can feed `ict-engine validate-market-state`, but it is not a full Board A acceptance packet because it does not run Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree admission.

## Data

| Provider / market | File | Rows including header | Current SHA-256 |
|---|---|---:|---|
| Binance `BTCUSDT` 1h full listing | `data/binance_btcusdt_1h_20170817_20260512.normalized.csv` | 76,430 | `6f9b9958bff8c85762acebd2f9891b30b336cbb59778f2c140e140e7b105e622` |
| IBKR `SPY` 1h 5Y | `data/ibkr_spy_1h_5y.normalized.csv` | 20,035 | `dc44b4db82d6a988d7b32ed45951edd43751336c1c113a72b0f625e32862a127` |
| Yahoo `ES=F` 1h 2Y | `data/yahoo_es_1h_20240513_20260512.normalized.csv` | 11,384 | `a508ec6b7615a47d20e6a3fc33e7baf6ad203bef6c5fdee35f5c0360dccfecb4` |

Note: `data_sha256.txt` contains an earlier IBKR hash from before the `ts` column was normalized to `timestamp`; the current on-disk IBKR hash is the value above.

## Command Results

| Check | Exit | Samples | Avg confidence | High confidence | Tradeable | Primary top | Secondary top |
|---|---:|---:|---:|---:|---:|---|---|
| `01_validate_binance_btc_1h` | 0 | 153 | 76.68% | 55.56% | 100.00% | `TrendExpansion:76` | `WideRange:41` |
| `02_validate_ibkr_spy_1h` | 0 | 80 | 75.19% | 50.00% | 100.00% | `RangeConsolidation:40` | `WideRange:27` |
| `03_validate_yahoo_es_1h` | 0 | 45 | 79.17% | 68.89% | 100.00% | `TrendExpansion:27` | `BullTrendAcceleration:16` |

Command evidence:
- `command-output/01_validate_binance_btc_1h.{cmd,out,err}`
- `command-output/02_validate_ibkr_spy_1h.{cmd,out,err}`
- `command-output/03_validate_yahoo_es_1h.{cmd,out,err}`
- `checks/01_validate_binance_btc_1h.exit`
- `checks/02_validate_ibkr_spy_1h.exit`
- `checks/03_validate_yahoo_es_1h.exit`

## Decision

- Provider-backed data paths are usable for `validate-market-state`: all three checks exited `0`.
- The observed confidence levels are materially below the Board A `>=95%` calibrated regime-confidence threshold.
- This smoke has no Auto-Quant strategy generation/backtest, no filter/Pre-Bayes admission, no BBN update, no CatBoost/path-ranker calibration, no path probability lower bound, and no execution-tree readiness result.
- The evidence is diagnostic only and must not be promoted as an accepted Board A regime context.

## Gate

- `support_once:143900_provider_backed_regime_validation_smoke_v1`.
- `evidence_class:provider_backed_market_state_validation_smoke`.
- `pass:binance_btcusdt_1h_validate_market_state_exit0`.
- `pass:ibkr_spy_1h_validate_market_state_exit0`.
- `pass:yahoo_es_1h_validate_market_state_exit0`.
- `fail_closed:binance_high_confidence_55_56_lt_95`.
- `fail_closed:ibkr_high_confidence_50_00_lt_95`.
- `fail_closed:yahoo_high_confidence_68_89_lt_95`.
- `fail_closed:no_auto_quant_strategy_generation_or_backtest`.
- `fail_closed:no_filter_pre_bayes_bbn_catboost_path_ranker_execution_tree_chain`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Use Binance `BTCUSDT` 1h full listing or IBKR `SPY` 1h 5Y as the next provider-backed input candidate only if it is carried through the full ordered chain: Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree. Do not run another heavy chain while unrelated `cargo`/`ict-engine` jobs are already active.
