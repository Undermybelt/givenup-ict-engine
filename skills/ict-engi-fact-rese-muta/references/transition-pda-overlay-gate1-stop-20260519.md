# Transition/PDA overlay Gate 1 stop pattern (2026-05-19)

Use when continuing a regime-rooted profitability branch where the base factor has Gate 1 evidence but downstream fails on transition hazard, PDA/hybrid disagreement, or execution readiness.

## Branch shape

Observed exact root:

`US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1`

The overlay was correctly attached after the first profit factor. The failure was not branch grammar; it was Gate 1 viability.

## Durable lesson

A transition/PDA overlay can be directionally appropriate but too restrictive for the 1m origin. If the overlay improves or stays positive on 5m/1h but the exact 1m-origin rows fail 1-2 bps/side cost stress, stop before Pre-Bayes/BBN/CatBoost/execution-tree.

Do not let higher-timeframe positives rescue the failed 1m root. Restart those positives under their own exact timeframe roots if they matter.

## Gate interpretation

For this class, downstream is allowed only when all hold:

- exact branch fields preserved in Auto-Quant `ranking[]`
- 1m-origin survivor exists after realistic cost stress, normally at least 2 bps/side
- trade density remains practical for the target cadence
- fresh provider rows are available, or cache replay is explicitly marked non-live-ready

If `origin_survivors_2bps=[]`, set:

- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`

## Completed-run precedence

If a fresh long run is interrupted or exits without `checks/terminal_metrics.json`, do not infer a verdict from partial Auto-Quant workspaces. Use the latest completed packet with terminal metrics for the current verdict, and label the interrupted run as incomplete.

## Concrete session evidence

Completed packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260519T130042+0800-hermes-ibkr-qqq-transition-stability-pda-alignment-overlay-v1/checks/terminal_metrics.json`

Key fields:

- `branch_fields_preserved=true`
- covered `1m/5m/15m/30m/1h/4h/1d`
- `cache_replay_used=true`, so `fresh_ibkr_live_ready=false`
- `origin_survivors_2bps=[]`
- `decision=drop_gate1_no_ibkr_cost_density`

Decisive 1m rows:

- `stable_balanced/QQQ/1m`: trades=9, raw=+0.18%, 2bps=-0.18%
- `stable_dense/QQQ/1m`: trades=13, raw=-0.01%, 2bps=-0.53%
- `pda_quality/QQQ/1m`: trades=4, raw=-0.41%, 2bps=-0.57%

Higher-timeframe positives were subclass evidence only:

- `stable_balanced/QQQ/1h`: trades=6, 2bps=+0.67%, 5bps=+0.31%
- `stable_balanced/QQQ/5m`: trades=18, 2bps=+0.53%, 5bps=-0.55%

## Next candidate direction

Keep the base `intraday_micro_trend_reclaim_density` as observation evidence. Replace the too-restrictive overlay with a lighter same-root overlay aimed at:

- preserving 1m 2bps edge first
- reducing transition hazard second
- improving the current active transition/readiness/alignment predicate without killing density
- only then pushing `execution_readiness >= 0.65`
