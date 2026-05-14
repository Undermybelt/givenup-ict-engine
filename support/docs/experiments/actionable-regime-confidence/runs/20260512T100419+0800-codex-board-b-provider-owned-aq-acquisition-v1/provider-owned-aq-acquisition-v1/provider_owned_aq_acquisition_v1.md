# Board B Provider-Owned AQ Acquisition v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`

Mode: `provider_acquisition_readback_only`

## Commands

- `01_provider_status_agent`: exit `0`
- `02_market_data_harness_plan`: exit `0`
- `03_market_data_harness_fetch`: exit `1`
- `04_yahoo_nq_f_1h`: exit `0`
- `05_kraken_xbtusd_1h`: exit `0`
- `06_binance_btcusdt_1h`: exit `0`
- `07_bybit_btcusdt_linear_1h`: exit `0`
- `08_ibkr_nq_202606_1h`: exit `1`

## Provider Readback

- Market-data harness request covered NQ provider-owned acquisition over `2026-04-01T00:00:00Z` to `2026-05-12T00:00:00Z` with roles `nq_yfinance`, `nq_tradingview`, and `nq_ibkr`.
- Harness yfinance fetch succeeded for `NQ=F` with `642` hourly bars.
- Harness TradingViewRemix fetch failed for `CME_MINI:NQ1!` with `tradingview MCP call 'get_ohlcv' returned error`.
- Harness IBKR fetch failed for `NQ`; stderr reported missing `redis` in the harness runtime.
- Direct Yahoo fetch succeeded for `NQ=F` with `642` hourly bars after one HTTP `429` retry.
- Direct Kraken fetch succeeded for `XBTUSD` spot with `721` hourly bars.
- Direct Binance fetch succeeded for `BTCUSDT` spot with `985` hourly bars.
- Direct Bybit fetch succeeded for `BTCUSDT` linear with `985` hourly bars.
- Direct IBKR fetch reached the `uv` dependency path but failed before writing bars: `AttributeError: 'NoneType' object has no attribute 'includeExpired'`.

## Artifacts

- Harness request: `provider-owned-aq-acquisition-v1/market_data_harness_request.json`
- Provider CSVs: `provider-csv/yahoo_nq_f_1h.csv`, `provider-csv/kraken_xbtusd_1h.csv`, `provider-csv/binance_btcusdt_1h.csv`, `provider-csv/bybit_btcusdt_linear_1h.csv`
- Command output directory: `command-output/`

## Decision

- This packet satisfies the provider-acquisition probe for yfinance/YF, Kraken, Binance, and Bybit.
- TradingViewRemix and IBKR remain provider-authority blockers in this runtime.
- No Auto-Quant factor-research/backtest was run from these newly acquired provider CSVs in this packet.
- No mature rooted branch observations, BBN posterior evidence, CatBoost/path-ranker training evidence, execution-tree promotion evidence, or closed-loop confidence were produced here.
- Promotion allowed: `false`
- `update_goal`: `false`

## Next

- Pre-seed an isolated Auto-Quant workspace from the successful provider CSVs, preferably starting with `yahoo_nq_f_1h.csv` for the `032157` NQ follow-up and using the crypto CSVs as cross-provider sidecars.
- Only after provider-provenanced Auto-Quant produces nonzero mature rooted branch observations should the chain advance through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
