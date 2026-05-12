# Board B Read-Only Regime Root Chain Refresh v1

Run id: `20260512T053410+0800-codex-board-b-readonly-regime-root-chain-refresh-v1`

Gate result: `readonly_regime_root_chain_refresh_v1=ran_fail_closed_no_promotion`

## Scope

This run re-exercised the current Board B `032157` downstream chain on a copied state under `/tmp/20260512T053410+0800-ict-engine-board-b-state-copy`. It did not mutate the existing `032157` state, did not select historical data for the user, did not start a new heavy Auto-Quant training job, did not promote any candidate, and did not call `update_goal`.

## Provider Readback

- yfinance status exit `0`; provider ready. Direct `QQQ` 1h helper fetch exit `0`, CSV rows including header `198`.
- IBKR status exit `0` but provider-status remains unhealthy because runtime dependencies are missing while the gateway is reachable. Ad-hoc `uv --with redis --with ib_async --with pandas` `SPY` 1d fetch exit `0`, CSV rows including header `22`.
- TradingViewRemix / `tradingview_mcp` status exit `0` but unhealthy. Direct harness fetch for `NASDAQ:QQQ` 1d exit `1` with `get_ohlcv` failure and retry/credential guidance.
- Kraken public status exit `0` but provider-status remains unhealthy for system-python dependency reasons. Direct helper `XBTUSD` 1h fetch exit `0`, CSV rows including header `722`.
- Kraken CLI status exit `0`; CLI OHLC command exit `0`, stdout bytes `59211`.

## Chain Readback

- Auto-Quant result import on the copied state exit `0`.
- Auto-Quant prior init exit `1` because the copied BBN already carries an Auto-Quant prior init and the command correctly refused duplicate pseudo-count stacking.
- Auto-Quant real-trade ingest exit `1` because the same JSONL content hash had already been ingested and the command correctly refused duplicate ingest without rollback/force.
- `ict-engine analyze` on the copied state exit `0`.
- Pre-Bayes status exit `0`: gate `observe_only`, active structural regime `range`, confidence `0.4038250313856651`.
- The Pre-Bayes filtered assignments did not expose `regime_profit_branch_path` in this runtime readback, so branch-path preservation is not proven by this chain run.
- Policy/CatBoost-facing status exit `0`: entry models pending, ranker runtime disabled, target rows `3`, mature rows `0`, production validation `0/30`, observation validation `0/30`.
- Structural path bundle exit `0`: path `range_mean_reversion`, recommended next step remains `ask_user_choose_historical_data`.
- Execution candidate exit `0`: candidate status `execution_blocked`, ready `false`, actionable `false`, Pre-Bayes gate `observe_only`, trade direction `Observe`.

## Decision

This is useful runtime evidence, not promotion evidence. The requested provider paths were exercised where available, and the chain was run in order on a copied state, but the candidate remains fail-closed because there is still no explicit user-selected historical dataset, no nonzero mature rooted selected observations, no validated CatBoost/path-ranker production rows, and no execution-tree admission.

## Artifacts

- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T053410+0800-codex-board-b-readonly-regime-root-chain-refresh-v1/command-output/`
- Assertion file: `docs/experiments/actionable-regime-confidence/runs/20260512T053410+0800-codex-board-b-readonly-regime-root-chain-refresh-v1/checks/readonly_regime_root_chain_refresh_v1_assertions.out`
- JSON summary: `docs/experiments/actionable-regime-confidence/runs/20260512T053410+0800-codex-board-b-readonly-regime-root-chain-refresh-v1/readonly-regime-root-chain-refresh-v1/readonly_regime_root_chain_refresh_v1.json`

## Next

Keep `034002` as the fail-closed cursor. The next qualifying Board B action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`; then run selected-data Auto-Quant/factor-research and continue downstream only if nonzero mature rooted observations exist.
