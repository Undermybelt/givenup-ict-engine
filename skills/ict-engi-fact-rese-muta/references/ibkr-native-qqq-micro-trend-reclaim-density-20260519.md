# IBKR-native QQQ micro trend reclaim density (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Context
User corrected the workflow: for practical profit-factor training, use IBKR rather than fallback/YF when possible.

Exact branch root used:

```text
US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1
```

## Gate 1 provider ladder
Use IBKR-native fetches and keep each timeframe explicit:

- `1m`: `1 min`, `7 D`, training origin
- `5m`: `5 mins`, `1 M`, small-cycle context
- `15m`: `15 mins`, `1 M`, sibling/context
- `30m`: `30 mins`, `1 M`, neutralization context
- `1h`: `1 hour`, `1 M`, HTF veto/context
- `4h`: `4 hours`, `1 M`, context when IBKR supports it
- `1d`: `1 day`, `1 Y`, daily context

In the observed run all seven IBKR lanes returned rows with `local_cache_replay=false`.

## Useful factor shape
After YF QQQ opening-drive/pullback variants were too sparse, a denser IBKR-native family worked better:

- Session VWAP soft reclaim
- EMA9/EMA21/EMA55 micro-trend alignment
- EMA21 slope guard
- RVOL/volume participation guard
- RSI window
- ATR-normalized VWAP extension guard
- short-hold/trailing execution controls

Best Gate 1 row:

```text
balanced/QQQ/1m
trades=25
raw_total_profit_pct=+1.47
1bps_per_side_total_profit_pct=+0.97
2bps_per_side_total_profit_pct=+0.47
5bps_per_side_total_profit_pct=-1.03
survives_2bps_per_side=true
```

This is enough for downstream readback, not enough for promotion.

## Downstream result
Downstream chain ran through:

```text
auto-quant-results-import
auto-quant-prior-init
analyze
workflow-status
pre-bayes-status
export-structural-path-ranking-target
ranker train/apply
apply-structural-path-ranking-external-scores
register-structural-path-ranking-trainer-artifact
enable-structural-path-ranking-runtime
analyze/workflow/pre-bayes/policy readback
```

Exact branch survived, but execution failed closed:

```text
pre_bayes_gate_status=pass_neutralized
execution_gate_status=execution_blocked
closed_loop.status=fail_closed
exact_branch_survived=true
actionable=false
execution_readiness=0.0
transition_hazard=1.0
pda_hybrid_alignment=false
trade_usable=false
```

## Reusable lesson
When IBKR Gate 1 passes cost/density but downstream fails on transition/PDA/readiness, do not keep widening the base density factor and do not lower gates. Preserve the base as observation and add only a same-root overlay:

```text
... -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1
```

The overlay objective is not more trades. It must reduce `transition_hazard`, align PDA/hybrid, and push `execution_readiness >= 0.65` while preserving the exact rooted path.
