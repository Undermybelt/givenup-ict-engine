# Mehrnoom Yfinance PnL Bridge v1

Run ID: `20260511T191648+0800-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1`

## Decision

- Gate result: `diagnostic_only:yfinance_daily_pnl_bridge_not_promotion_grade`
- Provider rows: `27016`
- Positive event rows: `13784`
- Control rows: `13232`
- Positive mean next-day return: `0.003797`
- Control mean next-day return: `0.010500`
- Monthly folds: `14`
- Promotion allowed: `False`

## Why It Stays Diagnostic

- This uses yfinance daily close-to-next-close bars, not the source-owned Telegram price sidecar and not intraday execution prices.
- It repairs provider-reconstructability for a subset of accepted direct events, but does not make the direct event source itself trade-usable.
- Scoped Manipulation should still route to suppression/abstain until an executable entry/exit bridge is accepted.

## Coin Coverage

| Coin | Ticker | Events | Controls | Download Rows | Reconstructed Rows |
|---|---|---:|---:|---:|---:|
| `BTC` | `BTC-USD` | 8957 | 8936 | 471 | 17893 |
| `ADA` | `ADA-USD` | 504 | 504 | 279 | 817 |
| `XRP` | `XRP-USD` | 480 | 480 | 279 | 707 |
| `ETC` | `ETC-USD` | 427 | 427 | 279 | 710 |
| `SC` | `SC-USD` | 425 | 425 | 279 | 745 |
| `NEO` | `NEO-USD` | 415 | 415 | 279 | 554 |
| `DGB` | `DGB-USD` | 378 | 378 | 279 | 542 |
| `LSK` | `LSK-USD` | 372 | 372 | 279 | 631 |
| `TRX` | `TRX-USD` | 369 | 369 | 279 | 721 |
| `WAVES` | `WAVES-USD` | 340 | 340 | 279 | 554 |
| `OMG` | `OMG-USD` | 338 | 338 | 279 | 501 |
| `STORJ` | `STORJ-USD` | 329 | 329 | 279 | 590 |
| `ETH` | `ETH-USD` | 320 | 320 | 279 | 521 |
| `XLM` | `XLM-USD` | 301 | 301 | 279 | 511 |
| `BAT` | `BAT-USD` | 298 | 298 | 279 | 509 |
| `XEM` | `XEM-USD` | 283 | 283 | 279 | 510 |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T191648-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1/mehrnoom-yfinance-pnl-bridge/mehrnoom_yfinance_pnl_bridge_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T191648-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1/mehrnoom-yfinance-pnl-bridge/mehrnoom_yfinance_pnl_rows_v1.csv`
- Coin coverage CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T191648-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1/mehrnoom-yfinance-pnl-bridge/mehrnoom_yfinance_coin_coverage_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T191648-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1/checks/mehrnoom_yfinance_pnl_bridge_v1_assertions.out`

## Next

- If this branch is reused, rebuild with intraday provider bars or source-owned entry/exit prices and then run branch RC-SPA with matched controls.
