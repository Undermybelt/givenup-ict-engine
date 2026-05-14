# Auto-Quant Provider Data Bridge Probe v1
Gate: `autoquant_provider_data_bridge_probe_v1=partial_provider_data_no_autoquant_prepare_coverage_no_promotion`
Purpose: test whether named provider paths can supply Auto-Quant fixed data coverage without editing the read-only Auto-Quant prepare contract.

## Required Auto-Quant Contract
- Pairs: BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, AVAX/USDT
- Timeframes: 1h, 4h, 1d
- Timerange: 20210101-20251231

## Probe Results
- `00_kraken_pf_xbtusd_1d`: exit `0`, provider `kraken_futures`, symbol `PF_XBTUSD`, interval `1d`, rows `1380`, range `2022-03-23 00:00:00+00:00 -> 2025-12-31 00:00:00+00:00`, blocker `starts_after_autoquant_required_20210101`.
- `01_kraken_pf_xbtusd_1h`: exit `0`, provider `kraken_futures`, symbol `PF_XBTUSD`, interval `1h`, rows `2000`, range `2022-03-23 10:00:00+00:00 -> 2022-06-14 17:00:00+00:00`, blocker `starts_after_autoquant_required_20210101`.
- `02_kraken_pf_xbtusd_4h`: exit `0`, provider `kraken_futures`, symbol `PF_XBTUSD`, interval `4h`, rows `2000`, range `2022-03-23 08:00:00+00:00 -> 2023-02-19 12:00:00+00:00`, blocker `starts_after_autoquant_required_20210101`.
- `03_yahoo_btcusd_1d`: exit `0`, provider `yahoo`, symbol `BTC-USD`, interval `1d`, rows `1826`, range `2021-01-01 00:00:00+00:00 -> 2025-12-31 00:00:00+00:00`, blocker `daily_only_not_enough_for_autoquant_1h_4h_1d_contract`.
- `04_yahoo_btcusd_1h`: exit `1`, provider `yahoo`, symbol `BTC-USD`, interval `1h`, rows ``, range ` -> `, blocker `yahoo_1h_730_day_limit_for_20210101_20251231`.

## Decision
This is non-promoting. yfinance daily coverage is useful, but Auto-Quant requires 1h/4h/1d coverage over the fixed 2021-2025 window. yfinance 1h is blocked by the 730-day limit, and Kraken futures intraday/daily probes start after the required 2021-01-01 start or are window-capped. No compliant Auto-Quant data bridge was materialized.

Accepted rows added: `0`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.
