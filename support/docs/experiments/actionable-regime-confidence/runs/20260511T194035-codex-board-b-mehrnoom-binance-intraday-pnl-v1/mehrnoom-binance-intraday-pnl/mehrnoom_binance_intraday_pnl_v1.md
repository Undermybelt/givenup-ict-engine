# Mehrnoom Binance Intraday PnL Bridge v1

Run ID: `20260511T194035+0800-codex-board-b-mehrnoom-binance-intraday-pnl-v1`

## Decision

- Gate result: `fail:direct_manipulation_intraday_pnl_bridge_not_accepted`
- Direct rows ready for future RC-SPA: `False`
- Full Board B promotion allowed: `False`
- Provider rows: `20684`
- Positive event rows: `13535`
- Control rows: `7149`
- Positive mean 6h return: `0.000946`
- Control mean 6h return: `0.001818`
- Positive-control 6h mean diff: `-0.000872`
- Positive-control 6h bootstrap LCB 5%: `-0.001630`
- Monthly folds: `12`
- Fold positive rate vs control: `0.4167`
- Blockers: `reject_positive_underperforms_control;reject_bootstrap_diff_lcb_nonpositive;reject_fold_positive_rate_lt60pct`
- Downstream consumption: `not_started:full_board_b_still_blocked_by_required_root_branch_rc_spa`

## Protocol

- Positive rows come from accepted Mehrnoom Telegram pump events.
- Controls are same-coin non-event timestamps at least 24h away from a classified pump event.
- Entry is the next 1h bar open after the event timestamp; primary exit is the 6h close; 24h return is recorded as secondary context.
- This is provider-reconstructed intraday PnL, not source-owned sell/exit rows.
- Even if the direct branch is repairable, full Board B remains blocked until every required root branch passes RC-SPA.

## Coin Coverage

| Coin | Symbol | Events | Controls | Bars | Positive Rows | Control Rows | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `BTC` | `BTC/USDT` | 8957 | 8865 | 8650 | 8898 | 2804 | `ready` |
| `ETH` | `ETH/USDT` | 320 | 320 | 8650 | 313 | 309 | `ready` |
| `XRP` | `XRP/BTC` | 480 | 480 | 6805 | 410 | 328 | `ready` |
| `ADA` | `ADA/BTC` | 504 | 504 | 6128 | 471 | 303 | `ready` |
| `ETC` | `ETC/BTC` | 427 | 427 | 7307 | 406 | 373 | `ready` |
| `TRX` | `TRX/BTC` | 369 | 369 | 6856 | 367 | 355 | `ready` |
| `OMG` | `OMG/BTC` | 338 | 338 | 8032 | 317 | 296 | `ready` |
| `LSK` | `LSK/BTC` | 372 | 372 | 6323 | 295 | 299 | `ready` |
| `XLM` | `XLM/BTC` | 301 | 301 | 5942 | 210 | 215 | `ready` |
| `BAT` | `BAT/BTC` | 298 | 298 | 6537 | 253 | 250 | `ready` |
| `ZRX` | `ZRX/BTC` | 117 | 117 | 8008 | 116 | 117 | `ready` |
| `LTC` | `LTC/BTC` | 236 | 236 | 9466 | 236 | 233 | `ready` |
| `DASH` | `DASH/BTC` | 167 | 167 | 7120 | 159 | 161 | `ready` |
| `NEO` | `NEO/BTC` | 415 | 415 | 9466 | 412 | 407 | `ready` |
| `XEM` | `XEM/BTC` | 283 | 283 | 3523 | 135 | 123 | `ready` |
| `SC` | `SC/BTC` | 425 | 425 | 1459 | 32 | 46 | `ready` |
| `DGB` | `DGB/BTC` | 378 | 378 | 0 | 0 | 0 | `no_provider_bars` |
| `STORJ` | `STORJ/BTC` | 329 | 329 | 6779 | 304 | 298 | `ready` |
| `WAVES` | `WAVES/BTC` | 340 | 340 | 5768 | 201 | 232 | `ready` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_rows_v1.csv`
- Coin coverage CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_coin_coverage_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/checks/mehrnoom_binance_intraday_pnl_v1_assertions.out`

## Next

- B2R-repeat: direct Manipulation still needs stronger intraday/source-owned PnL rows; do not promote downstream.
