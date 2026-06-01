# Beauty RSI/VWAP reclaim execution-readiness readback

Session date: 2026-05-18

## Branch
`RangeReversion -> BeautyPersonalCareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_beauty_personal_care_rsi_vwap_reclaim_1m_dense_v3`

## Gate 1 result
- Source run: `support/docs/experiments/actionable-regime-confidence/runs/20260518T184353+0800-hermes-yf-beauty-personal-care-rsi-vwap-reclaim-1m-dense-v3/`
- Provider coverage: `ELF`, `ULTA`, `COTY` with `1m/5m/15m/30m/1h/1d`; `4h` unsupported and recorded as missing
- Gate 1 density: `rank_rows=17`, `rank_total_trades=923`, `origin_trades_1m=43`, `positive_rows_trade_ge_5=6`
- Decision: `promote_gate1_candidate_to_downstream`

## Downstream readback
- Commands all exited `0`
- `execution_candidate_actionable=false`
- `execution_candidate_status=no_trade`
- `execution_tree_gate_status=observe`
- `execution_tree_branch=transition_guardrail`
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=false`
- `ranker_validation_ready=false`
- `mature_rows=1`, `history_mature_rows=12`

## Execution readiness audit
- Readback run: `support/docs/experiments/actionable-regime-confidence/runs/20260518T190002+0800-hermes-beauty-dense-v3-execution-readiness-readback-v1`
- `execution_readiness=0.22849963186858985`
- ready threshold: `0.65`
- shortfall: `0.4215003681314102`
- blocker shape: exact branch survives, but execution remains fail-closed / observe-only

## Durable lesson
- Once 1m-origin Gate 1 density is healthy, stop spending more sweeps on density for the same rooted branch.
- If the tree is still observe-only, switch to a same-root composite overlay that targets `session_liquidity` and `transition_stability`, then rerun Gate 1.
- Do not treat execution-tree visibility alone as readiness.
