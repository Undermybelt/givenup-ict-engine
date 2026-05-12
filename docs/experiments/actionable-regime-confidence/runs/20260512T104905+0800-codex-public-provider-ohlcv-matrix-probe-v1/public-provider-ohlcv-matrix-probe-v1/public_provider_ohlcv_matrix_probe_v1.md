# Public Provider OHLCV Matrix Probe v1

Run id: `20260512T104905+0800-codex-public-provider-ohlcv-matrix-probe-v1`

Purpose: separate default `provider-status` readiness from ad hoc public-provider fetch evidence for the Board A provider matrix. This is data-path evidence only; it is not source/control approval, selected-history approval, Auto-Quant promotion, downstream promotion, or trade evidence.

## Probe Result

The first command `00_fetch_public_provider_ohlcv_matrix` failed because the embedded Python received `$RUN_ROOT` literally from a quoted heredoc and could not write artifacts. The corrected command `01_fetch_public_provider_ohlcv_matrix_env` passed the run root through environment variables and exited `0`.

| Provider path | Symbol | Timeframe | Rows | Result |
|---|---:|---:|---:|---|
| yfinance | `BTC-USD` | `1h` | 146 | ok |
| Kraken public via ccxt | `BTC/USD` | `1h` | 120 | ok |
| Binance public via ccxt | `BTC/USDT` | `1h` | 120 | ok |
| Bybit public via ccxt | `BTC/USDT` | `1h` | 120 | ok |

## Evidence

- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T104905+0800-codex-public-provider-ohlcv-matrix-probe-v1/public-provider-ohlcv-matrix-probe-v1/public_provider_ohlcv_matrix_probe_v1.json`
- Corrected fetch stdout/stderr/exit: `command-output/01_fetch_public_provider_ohlcv_matrix_env.out`, `command-output/01_fetch_public_provider_ohlcv_matrix_env.err`, `checks/01_fetch_public_provider_ohlcv_matrix_env.exit`
- Failed first attempt stdout/stderr/exit: `command-output/00_fetch_public_provider_ohlcv_matrix.out`, `command-output/00_fetch_public_provider_ohlcv_matrix.err`, `checks/00_fetch_public_provider_ohlcv_matrix.exit`
- CSV outputs: `provider-csv/yfinance_btc_usd_1h_7d.csv`, `provider-csv/kraken_public_ccxt_btc_1h_120.csv`, `provider-csv/binance_public_ccxt_btc_1h_120.csv`, `provider-csv/bybit_public_ccxt_btc_1h_120.csv`

## Gate

- `public_provider_ohlcv_matrix_probe_v1=ad_hoc_yfinance_kraken_binance_bybit_ohlcv_rows_no_promotion`
- `pass:yfinance_btc_usd_1h_rows_146`
- `pass:kraken_public_ccxt_btc_usd_1h_rows_120`
- `pass:binance_public_ccxt_btc_usdt_1h_rows_120`
- `pass:bybit_public_ccxt_btc_usdt_1h_rows_120`
- `fail_closed:first_probe_bad_run_root_literal`
- `fail_closed:not_default_provider_status_repair`
- `fail_closed:no_tradingviewremix_data`
- `fail_closed:no_ibkr_data_in_this_probe`
- `fail_closed:no_auto_quant_run`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_rerun`
- `fail_closed:no_source_control_unlock`
- `fail_closed:no_selected_history`
- `promotion_allowed=false`
- `update_goal=false`

## Decision

This proves ad hoc public OHLCV rows are reachable for yfinance, Kraken, Binance, and Bybit under an isolated `uv` runtime. It does not make the repo default provider-status gates ready, does not satisfy the six-provider hard gate, and does not advance any regime to a 95% accepted packet.

Next useful work remains explicit selected-history approval, real R6/R5/R3 source/control unlock, or a provider-owned branch-specific recipe with enough mature rooted observations followed by the ordered Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain.
