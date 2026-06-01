# Beauty transition-stable overlay v5 downstream/provider-parity lesson

## Context
Session branch:
`RangeReversion -> BeautyPersonalCareOversoldReclaim -> rsi_vwap_reclaim_dense -> transition_stable_vwap_reclaim_overlay -> yf_beauty_personal_care_rsi_vwap_transition_stable_overlay_1m_v5`

Source Gate 1 run:
`support/docs/experiments/actionable-regime-confidence/runs/20260518T193741+0800-hermes-yf-beauty-rsi-vwap-transition-stable-overlay-1m-v5`

Downstream run:
`.../downstream-20260518T195834+0800-hermes`

Provider parity probes:
- IBKR: `20260518T194902+0800-hermes-ibkr-beauty-transition-stable-v5-provider-parity-probe`
- TradingViewMCP: `20260518T195006+0800-hermes-tvr-beauty-transition-stable-v5-provider-parity-probe`

## Decisive observations
- Gate 1 looked promising: `rank_rows=18`, `rank_total_trades=346`, `origin_trades_1m=77`, `origin_positive_rows_trade_ge_5=2`.
- Downstream mechanics all executed successfully: AQ import, prior init, analyze, workflow, pre-bayes/filter, structural target export, CatBoost train/apply, ICT score apply, runtime registration/enablement, analyze/workflow/pre-bayes/policy readback.
- Downstream final state was still fail-closed:
  - `all_command_exits_zero=true`
  - `exact_branch_survived=true`
  - `execution_candidate.actionable=false`
  - `execution_candidate.status=no_trade`
  - `execution_tree.gate_status=observe`
  - `execution_tree.branch=transition_guardrail`
  - `path_ranker_score_visible_to_execution_tree=true`
  - `path_ranker_score_used_by_execution_tree=false`
  - `ranker_validation_ready=false`
- Fresh provider parity failed:
  - IBKR `ELF/ULTA/COTY 1m 7D`: all `rows=0`, exits nonzero.
  - TradingViewMCP `NYSE:ELF/NASDAQ:ULTA/NYSE:COTY 1m`: exits zero but all `rows=0`.
  - Remaining evidence was YF source material only.

## Durable rule
If a same-root overlay passes Gate 1 but downstream returns `observe/transition_guardrail`, `actionable=false`, or `ranker_validation_ready=false`, do not keep adding near-identical overlays and do not call it live-ready. Treat it as scoped candidate evidence only.

Before any promotion claim, require both:
1. native/provider parity for the exact market/product/symbol/timeframe lane, and
2. downstream admission where the exact rooted branch is actionable and ranker validation is ready/used, not merely visible.

## Recommended next move
Stop spending budget on small parameter/overlay tweaks for this exact v5 branch. Pivot to one of:
- provider parity restoration for the exact single-stock 1m lane;
- same-root mature/validation row generation;
- execution-readiness diagnostics for `transition_guardrail`;
- a materially different denser same-root candidate family.

## Reporting contract
For future summaries, separate these classes explicitly:
- `gate1_candidate`: AQ rank rows and raw profitability evidence.
- `downstream_mechanics`: filter/BBN/CatBoost/tree commands ran and branch survived.
- `execution_admission`: actionable/readiness/live suitability.
- `provider_parity`: IBKR/TVR/YF/other provider proof.

Path-ranker visibility alone is not readiness. Fresh provider-status readiness is not fresh fetch proof.
