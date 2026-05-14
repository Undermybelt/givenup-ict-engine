# Board A Six-Provider Local-Stdio AQ Packet Preflight v1

Run id: `20260512T162440+0800-codex-board-a-six-provider-localstdio-aq-packet-v1`

## Provider Rows

- IBKR: exit `0`, rows `17`, symbol `SPY STK SMART/ARCA`, same-symbol `False`.
- TradingViewRemix/TVR: exit `0`, rows `720`, symbol `BTC-USD`, same-symbol `True`.
- yfinance/YF: exit `0`, rows `263`, symbol `BTC-USD`, same-symbol `True`.
- Kraken: exit `0`, rows `265`, symbol `PF_XBTUSD`, same-symbol `False`.
- Binance: exit `0`, rows `265`, symbol `BTCUSDT`, same-symbol `True`.
- Bybit: exit `0`, rows `265`, symbol `BTCUSDT linear`, same-symbol `False`.

## Decision

- six_provider_current_rows: `True`
- same_root_current_aq_authority: `False`
- auto_quant_should_start: `False`
- blockers: `['provider_rows_not_same_symbol_or_same_market_context:IBKR,Kraken,Bybit']`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
