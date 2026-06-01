# QQQ rooted VWAP reclaim cost/density lesson (2026-05-19)

Use when continuing regime-rooted profitability-factor training from a QQQ 1m origin and the 1m lane repeatedly fails cost stress while nearby higher timeframes survive.

## Session result

Strict root tested:

`US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> cost_stable_vwap_reclaim -> yf_qqq_cost_stable_vwap_reclaim_v2`

Provider/AQ coverage:
- YF real fetch, no cache replay.
- `1m`, `5m`, `15m`, `30m`, `1h`, `1d` succeeded.
- `4h` missing/unsupported; recorded as missing, not synthesized.
- Auto-Quant material batch/dispatch/rank completed.
- Branch fields were preserved.

Key rows:
- `edge_guard/QQQ/1m`: 28 trades, raw `+0.74%`, 1bps `+0.18%`, 2bps `-0.38%`.
- `edge_relaxed/QQQ/1m`: 40 trades, raw `+1.09%`, 1bps `+0.29%`, 2bps `-0.51%`.
- `edge_mid/QQQ/1m`: 35 trades, raw `+0.76%`, 1bps `+0.06%`, 2bps `-0.64%`.
- `edge_guard/QQQ/5m`: 27 trades, raw `+1.38%`, 2bps `+0.30%`.
- `edge_mid/QQQ/30m`: 9 trades, raw `+0.63%`, 2bps `+0.27%`.

Decision: `drop_gate1_no_cost_density` for the 1m root. Do not run Pre-Bayes, BBN, CatBoost, or execution tree for that 1m branch.

## Durable rule

If the declared root is `... -> QQQ -> 1m -> ...` and every 1m variant flips negative at 2bps/side, positive `5m` or `30m` siblings do not rescue the 1m root. Treat them as evidence for a new specific timeframe root, not promotion evidence for the failed 1m root.

Correct next move:

`US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> cost_stable_vwap_reclaim -> yf_qqq_5m_cost_stable_vwap_reclaim_v1`

Preserve `1m` only as microstructure/context for the 5m branch. Do not claim 1m-origin readiness.

## Gate policy

- Keep the 2bps/side minimum for intraday promotion.
- If 1m is raw-positive but 2bps-negative, stop at Gate 1.
- If 5m or 30m is 2bps-positive, restart as its own market/product/symbol/timeframe/regime root.
- Downstream is allowed only after the exact new root survives cost/density and branch-preservation checks.
