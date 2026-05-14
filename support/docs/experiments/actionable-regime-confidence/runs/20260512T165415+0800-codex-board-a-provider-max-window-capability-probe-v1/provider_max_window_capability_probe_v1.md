# Board A Provider Max-Window Capability Probe v1

Run id: `20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1`

This probe requests the broadest feasible BTC 1h history from provider interfaces and does not run Auto-Quant or downstream ict-engine gates.

## Matrix
- yfinance/YF: requested `2021-01-01_to_2026-05-12`, rows `0`, first `None`, last `None`, exit `1`, status `fail_closed`.
- Kraken: requested `2021-01-01_to_2026-05-12`, rows `2000`, first `2022-03-23 10:00:00+00:00`, last `2022-06-14 17:00:00+00:00`, exit `0`, status `current_row_ready`.
- Binance: requested `2021-01-01_to_2026-05-12`, rows `46955`, first `2021-01-01 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, exit `0`, status `current_row_ready`.
- Bybit: requested `2021-01-01_to_2026-05-12`, rows `1000`, first `2026-03-31 09:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, exit `0`, status `current_row_ready`.
- TradingViewRemix/TVR: requested `provider_default_local_stdio_no_explicit_range`, rows `720`, first `2026-04-12T09:00:00Z`, last `2026-05-12T08:59:51Z`, exit `0`, status `current_row_ready`.
- IBKR: requested `1Y_duration_via_ibkr_bulk`, rows `0`, first `None`, last `None`, exit `1`, status `fail_closed`.

## Gate
- provider_rows_ready=4/6.
- sample_adequacy=capability_probe_only.
- auto_quant_started=false.
- downstream_started=false.
- promotion_allowed=false.
- trade_usable=false.
- update_goal=false.
