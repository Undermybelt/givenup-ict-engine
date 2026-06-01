# QQQ transition overlay Gate1 and exact-timeframe pivot (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when continuing a QQQ/IBKR regime-rooted profit-factor run where a 1m-origin base factor survives Gate 1 but downstream is blocked by transition/PDA/execution-readiness gates.

## Exact branches observed

Base 1m root:

`US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1`

Same-root overlay tested:

`US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1`

Independent 15m root tested after HTF survivor appeared:

`US -> equity_etf -> QQQ -> 15m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_15m_v1`

## Durable workflow lesson

1. If a 1m same-root transition/PDA overlay kills the 1m cost edge, stop at Gate 1 even if 5m/1h siblings look good.
2. Positive 5m/1h siblings are not proof for the 1m root. Restart them as their own exact timeframe roots, with the original 1m lane only as microstructure/context.
3. If a partial Auto-Quant packet has completed dispatch artifacts but no terminal metrics, run `auto-quant-agent-material-rank` directly on the packet state before judging it. Use the actual `ranking[]` rows, not stale helper counters.
4. When CatBoost/path-ranker trainer registration fails with family mismatch such as `cli='catboost' source='weighted_feature_sum_v1'`, re-register with the artifact's true `model_family`; then re-run enable/analyze/workflow/pre-bayes/policy before making the verdict.
5. A successful `weighted_feature_sum_v1` re-registration is plumbing parity only when mature/validation rows are insufficient. Do not treat it as real CatBoost maturity or live readiness.

## Observed verdicts

1m transition/PDA overlay Gate 1 retry:
- full ladder ranked: `1m/5m/15m/30m/1h/4h/1d`
- branch fields preserved
- `origin_survivors_2bps=[]`
- best 1m rows after cost:
  - `stable_balanced/QQQ/1m`: trades=9, raw=+0.18%, 2bps=-0.18%
  - `stable_dense/QQQ/1m`: trades=13, raw=-0.01%, 2bps=-0.53%
  - `pda_quality/QQQ/1m`: trades=4, raw=-0.41%, 2bps=-0.57%
- decision: `drop_gate1_no_ibkr_cost_density`
- downstream gates remain false; no Pre-Bayes/BBN/CatBoost/execution-tree handoff.

15m exact-root downstream after register fix:
- Gate1 15m survivor: `dense/QQQ/15m`, trades=42, raw=+2.43%, 2bps=+0.75%
- trainer artifact family: `weighted_feature_sum_v1`
- exact branch survived downstream
- `pre_bayes_gate_status=pass_neutralized`
- `closed_loop.status=fail_closed`
- `execution_readiness=0.3418474258427023`
- `transition_hazard=0.9589006593813092`
- `pda_hybrid_alignment=false`
- `promotion_allowed=false`, `trade_usable=false`

## Next candidate shape

For the 1m branch: do not add stricter transition/PDA overlays to rescue it. Treat the tested overlay as negative/suppression evidence.

For HTF survivors: open a new exact root such as:

`US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> transition_stability_pda_alignment_overlay -> <new_profit_factor>`

or continue the 15m exact root with a new overlay that specifically targets:
- `transition_hazard < 0.60`
- `pda_hybrid_alignment=true`
- `execution_readiness >= 0.65`

Do not lower the gates. Do not call `path_ranker_score_visible` or direct fallback readiness a promotion signal.
