# TOMAC Cross-Asset Risk Rotation Negative Screen, 2026-05-29

## Context

The active objective remained regime-rooted factor training with 1m origin,
full-MTF context, hard gates, and IBKR historical or paper evidence when safe.
Same-turn audit showed a fresh IBKR M2K row-truth claim, so this slice stayed
local-only and did not launch IBKR, paper trading, provider fetches, AutoQuant,
or freqtrade.

## Branch Tested

- Factor id: `tomac_idxfut_crossasset_risk_rotation_mtf_reentry_1m_v1`
- Branch path: `CrossAssetRegime -> RiskOnOffDivergence -> IndexSafeHavenRotation -> MtfMomentumReentry -> tomac_idxfut_crossasset_risk_rotation_mtf_reentry_1m_v1`
- Data: retained TOMAC `NQ/YM/XAU` `1m` parquet with available `5m/15m/30m/1h/4h/1d` context.
- Gate: `5bps/side`, `10bps` round trip, cadence `0.333` to `3` trades/day, PF `>=1.10`, all available years positive, minimum `200` trades.
- Evidence root: `/tmp/ict-engine-tomac-crossasset-risk-rotation-mtf-reentry-20260529T171807+0800`
- Durable packet: `support/docs/experiments/actionable-regime-confidence/runs/20260529T171807+0800-codex-tomac-crossasset-risk-rotation-mtf-reentry-v1`

## Result

Local screen command exited `0`; stderr was empty.

- `rows_tested=1728`
- `screen_gate_pass_count=0`
- `cadence_and_positive_5bps_count=0`
- `near_positive_count=0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

The best row with actual trades was still strongly negative after honest cost:

- YM long, `472` trades, `0.333805` trades/day, `net_5bps_side_total_return_pct=-63.014016`, `avg_net_bps_per_trade=-13.350427`, `profit_factor_5bps_side=0.014672`, `yearly_positive_count=0/5`.

## Lesson

This simple cross-asset NQ/YM/XAU risk-on/risk-off rotation with MTF reentry is
not a near-practical TOMAC branch on retained `1m` OHLCV. When the signal reaches
the cadence floor, the realized fixed-RRR screen is deeply negative after
`5bps/side` cost.

Do not rerun this exact branch unchanged. Future cross-asset work needs a
different source of edge, such as a better event/regime definition, lower-cost
instrument, or IBKR historical bid/ask and paper-fill evidence before any AQ,
Pre-Bayes, BBN, CatBoost, execution-tree, promotion, or trade-use handoff.
