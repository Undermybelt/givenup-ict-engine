# Board B Six-Provider BTC Matrix Probe v1

Run id: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

## Scope

Provider-layer BTC matrix probe for the active Board A six-provider authority gap. This packet records provider-status readbacks plus raw/ad hoc fetches for TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, Bybit, and IBKR PAXOS BTC. It does not run Auto-Quant, select history, mutate source/control roots, or run Pre-Bayes, BBN, CatBoost/path-ranker, or the execution tree.

## Results

- `provider-status` commands exited `0` for all inspected providers, but readiness was mixed: yfinance ready; TradingViewRemix/TVR unhealthy in the default credential path; IBKR and IBKR bridge unhealthy in repo provider-status because the runtime still lacks dependencies; Kraken, Binance, and Bybit provider-status paths unhealthy under system python dependency checks.
- yfinance ad hoc BTC-USD 1h fetch exited `0` and wrote `983` rows from `2026-04-01T00:00:00+00:00` through `2026-05-11T23:00:00+00:00`.
- Kraken ad hoc XBTUSD 1h fetch exited `0` and wrote `721` rows from `2026-04-12T03:00:00+00:00` through `2026-05-12T03:00:00+00:00`.
- Binance ad hoc BTCUSDT 1h fetch exited `0` and wrote `985` rows from `2026-04-01T00:00:00+00:00` through `2026-05-12T00:00:00+00:00`.
- Bybit ad hoc BTCUSDT linear 1h fetch exited `0` and wrote `985` rows from `2026-04-01T00:00:00+00:00` through `2026-05-12T00:00:00+00:00`.
- IBKR PAXOS BTC daily `TRADES` fetch exited `0` but returned `0` rows because IBKR required `AGGTRADES`; the follow-up `AGGTRADES` fetch exited `0` and wrote `30` rows from `2026-04-01` through `2026-05-12`.
- TVR default `BINANCE:BTCUSDT` 1d fetch and local-stdio exchange-prefixed aliases failed. The local-stdio plain `BTC-USD` alias exited `0` and returned `29` daily rows from `2026-04-13T00:00:00Z` through `2026-05-12T00:00:00Z`.

## Decision

- Gate: `112315_board_b_six_provider_btc_matrix_probe_v1=six_provider_raw_rows_present_via_mixed_ad_hoc_paths_but_default_provider_status_mixed_no_aq_no_promotion`.
- This is useful provider-layer coverage: all six required provider lanes now have at least one raw BTC row source inside the same run root if TVR is counted through the working `BTC-USD` stdio alias and IBKR through PAXOS `AGGTRADES`.
- It is not a six-provider AQ authority pass. The evidence is mixed between repo provider-status, market-data-harness, and ad hoc `uv` fetches; default provider readiness is not uniformly healthy; no Auto-Quant run consumed the six-provider data in this root; no selected-history/source-control unlock exists; no canonical merge occurred; and no ordered downstream chain ran.
- Accepted rows added: `0`.
- Mature rooted branch observations added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.

