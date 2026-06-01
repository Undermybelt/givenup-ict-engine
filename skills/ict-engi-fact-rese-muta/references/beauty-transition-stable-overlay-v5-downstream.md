# Beauty transition-stable overlay v5 downstream fail-closed

Session date: 2026-05-18

## Branch
`RangeReversion -> BeautyPersonalCareOversoldReclaim -> rsi_vwap_reclaim_dense -> transition_stable_vwap_reclaim_overlay -> yf_beauty_personal_care_rsi_vwap_transition_stable_overlay_1m_v5`

## Gate 1 result
- Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260518T193741+0800-hermes-yf-beauty-rsi-vwap-transition-stable-overlay-1m-v5`
- Provider coverage: `1m/5m/15m/30m/1h/1d`; Yahoo `4h` unsupported and should be recorded as missing, not synthesized.
- `rank_rows=18`
- `rank_total_trades=346`
- `origin_trades_1m=77`
- `positive_rows_trade_ge_5=4`
- `origin_positive_rows_trade_ge_5=2`
- Gate 1 decision: `promote_same_root_overlay_to_downstream`
- Top row: `ULTA 1m`, 33 trades, +2.05%, win 72.7273%.

## Downstream readback
- Downstream root: `support/docs/experiments/actionable-regime-confidence/runs/20260518T193741+0800-hermes-yf-beauty-rsi-vwap-transition-stable-overlay-1m-v5/downstream-20260518T194415+0800`
- Commands exited `0`: import, prior init, analyze, workflow/pre-bayes/policy status, target export, CatBoost train/apply, ICT score apply, trainer registration, runtime enable, and post-ranker analyze/workflow/policy.
- `execution_candidate_actionable=false`
- `execution_tree_gate_status=observe`
- `execution_tree_branch=transition_guardrail`
- `ranker_validation_ready=false`
- `promotion_allowed=false`
- `trade_usable=false`

## Durable lesson
- A same-root overlay can improve Gate 1 density and still fail the execution tree. Do not rerun near-identical overlays after `transition_guardrail` persists.
- After a dense same-root overlay reaches downstream and remains observe-only, pivot to the missing gate: same-branch mature/validation rows, provider parity (IBKR/TradingViewRemix before YF-only claims), or execution-readiness feature diagnostics.
- Keep the branch path exact through all artifacts. If downstream selects `transition_guardrail` and `ranker_validation_ready=false`, the result is `gate1_pass_downstream_fail_closed`, not live readiness.
- In multi-agent sessions, write claim files outside the repo (for example `/tmp/ict-engine-agent-claims/...`) and avoid editing shared planning docs unless explicitly assigned.
