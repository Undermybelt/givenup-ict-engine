# Independent Market Timeframe Downstream Smoke v1

- Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T175651+0800-codex-high-density-rsi-bb-ema-six-provider-aq-v1`
- Providers tested: `6`
- Independent market classes: `2`
- Commands exit zero: `30/30`
- Accepted 95 contexts added: `0`
- Promotion allowed: `false`
- Trade usable: `false`

## Gate Matrix

| Symbol | Provider | Market | Confidence | Mature Rows | Ready | Actionable | Accepted 95 |
|---|---|---|---:|---:|---|---|---|
| `BOARD_A_SPY_YF_191941` | `yfinance/YF` | `equity` | 0.977742 | 0 | False | False | False |
| `BOARD_A_SPY_IBKR_191941` | `IBKR` | `equity` | 0.977742 | 0 | False | False | False |
| `BOARD_A_BTC_BINANCE_191941` | `Binance` | `crypto` | 0.730130 | 0 | False | False | False |
| `BOARD_A_BTC_BYBIT_191941` | `Bybit` | `crypto` | 0.726859 | 0 | False | False | False |
| `BOARD_A_BTC_KRAKEN_191941` | `Kraken` | `crypto` | 0.544541 | 0 | False | False | False |
| `BOARD_A_BTC_TVR_191941` | `TradingViewRemix/TVR` | `crypto` | 0.453331 | 0 | False | False | False |

## Fail-Closed Reasons

- 4h/1d files are deterministic resamples from 1h provider candles, not independent provider-native timeframe fetches.
- This smoke uses the existing 175651 provider materialization and does not rerun Auto-Quant.
- No per-regime calibrated `>=95%` artifact was produced.
- No independent symbol reached execution-ready/actionable acceptance.
