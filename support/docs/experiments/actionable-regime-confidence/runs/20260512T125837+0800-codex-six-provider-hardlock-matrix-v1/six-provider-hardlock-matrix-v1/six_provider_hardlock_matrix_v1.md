# 20260512T125837 Six-Provider Hardlock Matrix v1

## Scope

This root records a provider/harness hard-lock diagnostic for the six provider rows required by Board A: IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.

It is not an Auto-Quant authority packet. No Auto-Quant provider-owned run, filter/Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree promotion command was run from this root.

## Evidence

- Command list: `command-output/*.cmd`
- Exit codes: `checks/*.exit`
- Provider status: `command-output/00_provider_status_agent.out`
- Successful yfinance fetch: `command-output/10_fetch_yfinance_qqq.out`
- Failed TVR fetch: `command-output/11_fetch_tradingview_qqq.err`
- Failed IBKR fetch: `command-output/12_fetch_ibkr_qqq.err`
- Failed crypto harness mappings: `command-output/13_fetch_kraken_btc.err`, `command-output/14_fetch_binance_btc.err`, `command-output/15_fetch_bybit_btc.err`
- Six-row matrix: `six-provider-hardlock-matrix-v1/six_provider_hardlock_matrix_v1.csv`
- Prompt-to-artifact checklist: `six-provider-hardlock-matrix-v1/prompt_to_artifact_checklist_six_provider_hardlock_matrix_v1.csv`

## Readback

Provider-status commands exited `0` for all six direct probes:

- `provider-status --agent`
- `provider-status --provider yfinance --agent`
- `provider-status --provider ibkr --agent`
- `provider-status --provider tradingview_mcp --agent`
- `provider-status --provider kraken_public --agent`
- `provider-status --provider binance_public --agent`
- `provider-status --provider bybit_public --agent`

Fetch acquisition did not pass the hard-lock matrix:

- yfinance/YF: `QQQ` `1d` fetch exited `0` and returned `21` daily candles.
- TradingViewRemix/TVR: `NASDAQ:QQQ` `1d` fetch exited `1` because `get_ohlcv` returned an error.
- IBKR: `QQQ` `1d` fetch exited `1` because the runtime could not import `redis`; the same evidence says the IBKR gateway is reachable on port `4002`.
- Kraken: `BTC/USD` `1d` fetch exited `1` because `kraken_public` is unsupported by the current `market-data-harness` role mapping.
- Binance: `BTC/USDT` `1d` fetch exited `1` because `binance_public` is unsupported by the current `market-data-harness` role mapping.
- Bybit: `BTC/USDT` `1d` fetch exited `1` because `bybit_public` is unsupported by the current `market-data-harness` role mapping.

## Decision

This root is fail-closed for Board A acceptance.

- Six provider rows requested: `6/6`
- Provider data acquired: `1/6`
- AQ provider invoked: `0/6`
- Local cache replay: `0/6`
- Same-root six-provider AQ authority: `false`
- Calibrated `>=95%` regime packet: `false`
- Mature rooted observations added: `0`
- CatBoost/path-ranker promotion: `false`
- Execution-tree readiness: `false`
- Trade usable: `false`
- `update_goal`: `false`

## Next

Use this root only to narrow provider/harness wiring gaps. It should not be counted as a provider-provenanced AQ pass, a same-root six-provider acceptance packet, a local-cache replay substitute, or downstream promotion evidence.
