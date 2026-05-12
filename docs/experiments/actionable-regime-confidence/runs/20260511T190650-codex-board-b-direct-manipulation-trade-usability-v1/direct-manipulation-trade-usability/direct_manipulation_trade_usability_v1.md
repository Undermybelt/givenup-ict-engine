# Direct Manipulation Trade-Usability v1

Run ID: `20260511T190650+0800-codex-board-b-direct-manipulation-trade-usability-v1`

## Decision

- Gate result: `blocked:accepted_direct_manipulation_sources_not_board_b_trade_pnl_usable`
- Accepted direct rows seen: `94420`
- Sources checked: `5`
- Trade-usable sources: `0`
- Board B profitability rows added: `0`
- Downstream consumption: `not_started:no_trade_usable_manipulation_profit_rows`

## Why This Does Not Repair RC-SPA

- Board A has accepted direct `Manipulation` context rows.
- The accepted source artifacts mark them as `trade_usable=false` or provide labels without executable entry/exit PnL.
- The Mehrnoom price sidecar has buy levels but no sell/exit rows, so source-owned realized PnL cannot be computed from it.
- Local Auto-Quant crypto OHLCV coverage starts in 2021, while the Telegram/Zenodo direct rows are 2017-2018; Midsummer rows are maker-token-day wash evidence without local pair mapping.

## Source Checks

| Source | Accepted Rows | Controls | Trade Usable | Sample Has PnL Columns | Status |
|---|---:|---:|---|---|---|
| `mehrnoom_telegram_pump_events` | 61515 | 61445 | `False` | `False` | `blocked:not_trade_pnl_usable` |
| `zenodo_dex_self_trade` | 12671 | 10000 | `False` | `False` | `blocked:not_trade_pnl_usable` |
| `zenodo_dex_consecutive_self_trade` | 12671 | 187329 | `False` | `False` | `blocked:not_trade_pnl_usable` |
| `midsummer_bsc_wash_maker` | 1870 | 0 | `False` | `False` | `blocked:not_trade_pnl_usable` |
| `midsummer_multichain_wash_maker` | 5693 | 0 | `False` | `False` | `blocked:not_trade_pnl_usable` |

## Mehrnoom Price Sidecar

- Rows: `55751`
- Buy rows: `46744`
- Sell rows: `0`
- Both buy/sell rows: `0`

## Next

- For scoped Manipulation, require a source-owned or provider-reconstructed entry/exit PnL bridge before adding Board B RC-SPA rows; otherwise keep accepted direct rows as suppression/abstain overlay only.
