# BTC Provider Matrix + Path-Ranker Readback v1

Run id: `20260512T113017+0800-codex-btc-provider-matrix-path-ranker-readback-v1`

## Sources

- Six-provider BTC matrix probe: `docs/experiments/actionable-regime-confidence/runs/20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`
- Provider-data / Pre-Bayes / path-ranker readback: `docs/experiments/actionable-regime-confidence/runs/20260512T112740+0800-codex-104703-provider-data-prebayes-pathranker-readback-v1`
- Symbol-normalized BTC pullback path-ranker bridge: `docs/experiments/actionable-regime-confidence/runs/20260512T112954+0800-codex-111403-symbol-normalized-path-ranker-bridge-v1`

## Provider Matrix Readback

The `112315` BTC provider matrix acquired BTC rows through yfinance, Kraken, Binance, Bybit, and an IBKR PAXOS AGGTRADES retry, but it is still provider-layer evidence only.

- yfinance BTC-USD 1h: `983` data rows, command exit `0`.
- Kraken XBTUSD 1h: `721` data rows, command exit `0`.
- Binance BTCUSDT 1h: `985` data rows, command exit `0`.
- Bybit linear BTCUSDT 1h: `985` data rows, command exit `0`.
- IBKR PAXOS BTC TRADES request: connected and qualified, but `0` rows; IBKR returned error `10299` requesting `AGGTRADES`.
- IBKR PAXOS BTC AGGTRADES retry: `30` daily rows, command exit `0`.
- TradingViewRemix / tradingview_mcp BTC fetch remained blocked in this root: default credential fetch exited `1`, and local-stdio fetch exited `1` with HTTP 404 for `BINANCE:BTCUSDT`.

This does not satisfy the strengthened Board A six-provider AQ authority gate because it is not same-root AQ/provider provenance and the repo provider-status rows for TVR, IBKR, Kraken, Binance, and Bybit remained unhealthy in the probe.

## Downstream Readback

`112740` proved the provider-data chain can create a non-empty Pre-Bayes bridge and history-backed CatBoost/path-ranker context for `B2R_PROVIDER_BTC_EMA_RSI_104703`, but execution stayed fail-closed.

- Provider-data conversion rows: `42` daily, `247` 4h, `985` 1h.
- Pre-Bayes gate: `pass_neutralized`; canonical structural regime: `range`; confidence: `0.5345590139527494`.
- Corrected structural export command `04b` exited `0` after the original export command failed on unsupported `--output-format`.
- Policy/path-ranker validation: raw scored mature `86/30`, production validation `85/30`, observation validation `43/30`, CatBoost trainer artifact ready, runtime status `enabled_candidate_set_ready`.
- Execution candidate: ready `false`, actionable `false`, review status `observe`, gate `execution_blocked`.
- Full workflow closed-loop branch admission: `fail_closed`; next command remains blocked on `user_selected_historical_data_missing`.

`112954` repaired the `111403` BTC pullback path-ranker cardinality issue by normalizing the trade symbol before ingest. It proves the path-ranker bridge can reach validation floors on that copied branch, but it still does not promote Board A.

- Normalized real trades ingested: `146`.
- Final path-ranker validation: raw scored mature `147/30`, production validation `146/30`, observation validation `146/30`.
- Trainer artifact: CatBoost, ready, runtime status `enabled_candidate_set_ready`, runtime matches `2`.
- Pre-Bayes policy fields remained absent.
- Execution candidate remained ready `false`, actionable `false`, review status `observe`.
- Full workflow closed-loop branch admission remained `fail_closed`.

## Decision

Gate: `btc_provider_matrix_path_ranker_readback_v1=provider_rows_and_path_ranker_validation_repaired_but_same_root_aq_authority_pre_bayes_execution_fail_closed_no_promotion`.

Accepted rows added: `0`. Mature rooted branch observations promoted: `0`. Source/control evidence acquired: `false`. Explicit selected-history approval: `false`. Canonical merge: `false`. Same-root six-provider AQ matrix: `false`. Selected-data AutoQuant promotion: `false`. Downstream promotion: `false`. Strict full objective: `false`. Trade usable: `false`. Promotion allowed: `false`. `update_goal=false`.

Next: use the `112954` symbol-normalized bridge as the next path-ranker repair baseline only after Pre-Bayes/filter produces policy fields on the same rooted branch, and rebuild same-root AQ/provider provenance across IBKR, TVR, YF, Kraken, Binance, and Bybit before any promotion claim.
