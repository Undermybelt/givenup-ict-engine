# Fintech lending dense RSI/VWAP downstream fail-closed pattern

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session class: regime-rooted profitability-factor training after Gate 1 passes and downstream partially runs.

Observed branch:
`RangeReversion -> FintechLendingOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_fintech_lending_rsi_vwap_reclaim_1m_dense_v1`

Gate 1 shape:
- Fresh yfinance/YF SOFI/AFRM/LC data, `local_cache_replay=false`.
- `1m/5m/15m/30m/1h/1d` fetched; `4h` unsupported and not fabricated.
- Auto-Quant batch/dispatch/rank exited `0`.
- `rank_rows=18`, `total_trades=802`, `origin_trades_1m=44`, branch fields preserved.
- 1m cost stress was mixed: AFRM survived 2 bps/side but failed 5 bps; SOFI flipped negative at 2 bps; LC was negative.

Downstream pattern:
- `auto-quant-results-import`, `auto-quant-prior-init`, first `analyze`, `workflow-status`, `pre-bayes-status`, `export-structural-path-ranking-target`, `policy-training-status`, CatBoost train/apply, score apply, register, and enable runtime all exited `0`.
- Rerunning `analyze_after_ranker` on the full dense packet can be very slow or stall. If the pre-ranker analyze has already produced `execution_tree_trace.json`, `execution_candidate.json`, and workflow state, inspect those before spending more time.
- In this case exact branch survived, but execution was fail-closed:
  - `closed_loop_branch_admission.status=fail_closed`
  - `candidate_status=execution_observe_only`
  - `execution_tree_branch=transition_guardrail`
  - `execution_readiness=0.4614462727928709`
  - `hybrid_transition_hazard=0.6293519858490934`
  - `pda_hybrid_alignment=true`
  - path-ranker score not visible/used by execution tree in the inspected trace
  - `mature_rows=1`, `rows_with_training_weight=1`

Decision rule:
- Do not promote when exact branch survives but `transition_hazard >= 0.60` or `execution_readiness < 0.65`, even if Gate 1 and CatBoost plumbing succeeded.
- If only one 1m sibling survives 2 bps and the downstream trace is observe-only, keep as observation/incubation; do not call it trade usable.
- Next candidate should target transition-hazard compression and execution-readiness uplift, not more raw RSI/VWAP density: add same-root overlays for PDA sequence consistency, lower overextension/spectral entropy, and session-liquidity stability.

Closure labels:
- `decision=gate1_pass_downstream_fail_closed`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
