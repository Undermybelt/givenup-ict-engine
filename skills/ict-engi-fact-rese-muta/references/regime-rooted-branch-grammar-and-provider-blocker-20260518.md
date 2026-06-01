# Regime-rooted branch grammar + provider-blocker handling (2026-05-18)

## Trigger
Use this note when training ict-engine profitability factors after the operator asks for regime-rooted factor branches, 1m-origin ladders, and downstream gate-aware continuation.

## Branch grammar
A profitability branch must preserve this identity through Auto-Quant, filtering, BBN, CatBoost/path-ranker, execution tree, and feedback:

```text
market/provider -> product/species -> symbol -> base_timeframe -> main_regime -> sub_regime -> ... -> sub_regime_or_first_profit_factor -> profit_factor -> profit_factor_overlay...
```

Rules:
- Regime nodes may branch to more regime nodes or to the first profit factor.
- Profit-factor nodes may only branch to later profit-factor overlays.
- Start with one specific profit factor under one specific rooted branch.
- Add composite strategy only as an explicit overlay after the base factor earns evidence.
- Do not let downstream artifacts flatten the branch to just a factor name or pivot to a sibling path.

## Ladder contract
Default practical-profit ladder:
- Start from 1m when feasible.
- Cover 5m, 15m, 30m, 1h, 4h, and 1d where real provider data exists.
- Use the maximum feasible window per lane.
- Seek enough density for roughly 1-3 trades/day unless the strategy class justifies otherwise.
- HTF positives are context/confirmation/suppression evidence; they do not rescue a failed 1m-origin branch.

## Session evidence
MARA/RIOT YF 1m-origin branch:
- Script: `support/docs/experiments/actionable-regime-confidence/scripts/run_yf_mara_riot_vwap_rvol_opening_drive_1m_mtf_v1.py`
- Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260518T204540+0800-codex-yf-mara-riot-vwap-rvol-opening-drive-1m-mtf-v1/`
- Result: `rank_rows=10`, `rank_total_trade_count=58`, `one_minute_trades=6`, `positive_origin_1m_count=0`.
- Decision: `drop_or_block_gate1_practical`; no Pre-Bayes/BBN/CatBoost/execution-tree handoff.

Kraken full-ladder retry:
- Script: `support/docs/experiments/actionable-regime-confidence/scripts/run_kraken_btc_eth_sol_vwapdev_obvrsi_cost_tight_1m_full_ladder_v1.py`
- Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260518T205044+0800-codex-kraken-btc-eth-sol-vwapdev-obvrsi-cost-tight-1m-full-ladder-v1/`
- Result: `BTCUSD 1m` fetched, but `BTCUSD 5m/15m` failed after Kraken OHLC SSL retries and the outer run timed out before a complete ladder/AQ verdict.
- Decision: provider reachability/window blocker, not factor failure. Retry with smaller windows or alternate public runtime while preserving the exact branch grammar.

## Pitfalls
- Do not advance downstream when 1m origin is sparse/negative, even if 5m/30m/1h siblings are positive.
- Do not classify partial provider fetches as factor failures.
- Do not use cache/fallback data as live-ready parity; mark `local_cache_replay` or fallback provenance explicitly.
- Board B terminal evidence should be appended to the compact current-state doc, not old large logs.
