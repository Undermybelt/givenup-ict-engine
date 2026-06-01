# M2K 1m liquidity sweep reject-short RVOL/PDA guard

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session: 2026-05-20

## Exact branch

`FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_7d_gate1_v1`

## Gate 1 evidence

Source packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260520T024014+0800-codex-ibkr-m2k1m-liquidity-sweep-reject-short-rvol-pda-guard-7d-gate1-v1`

Provider/provenance:

- retained real IBKR `M2K 202606` `1m` `7 D`
- `rows=9392`
- `local_cache_replay=retained_real_ibkr_same_contract_replay`
- source provider root: `20260520T005518+0800-codex-ibkr-m2k1m-liquidity-sweep-reject-short-7d-gate1-v1`

Cost survivors:

- `M2K/rvol100_ema55/1m_short`: 19 trades, raw `+2.60%`, `2bps=+1.84%`, `5bps=+0.70%`
- `M2K/rvol075_ema55/1m_short`: 28 trades, raw `+3.14%`, `2bps=+2.02%`, `5bps=+0.34%`
- `M2K/rvol075_slope/1m_short`: 20 trades, raw `+2.33%`, `2bps=+1.53%`, `5bps=+0.33%`
- `M2K/rvol075_ema200/1m_short`: 31 trades, raw `+3.37%`, `2bps=+2.13%`, `5bps=+0.27%`

Verdict: Gate 1 earned downstream repair because density and `5bps/side` cost survival were real on the exact rooted branch.

## Simulated feedback admission

Packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260520T024014+0800-codex-ibkr-m2k1m-liquidity-sweep-reject-short-rvol-pda-guard-7d-gate1-v1/simulated-trade-admission-m2k-1m-liquidity-sweep-reject-short-rvol-pda-guard-20260520T024616+0800`

Result:

- simulated trades: 19 rows, 12 wins, 7 losses
- all wrapper commands `01` through `19` exited `0`
- `exact_branch_survived=true`
- `ranker_validation_ready=true`
- `path_ranker_score_visible_to_execution_tree=true`
- `mature_rows=2`
- `history_mature_rows=20`
- `execution_candidate_status=no_trade`
- `execution_readiness=0.3180972047048167`
- `transition_hazard=0.9184975817511946`
- `pda_hybrid_alignment=false`
- `path_ranker_score_used_by_execution_tree=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Verdict: clean same-root mechanics plus 5bps Gate 1 survival still did not create a trade-usable factor. The blocker is execution admission and regime/PDA alignment, not AQ cost survival.

## Full-ladder simulated admission rerun

Packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260520T024014+0800-codex-ibkr-m2k1m-liquidity-sweep-reject-short-rvol-pda-guard-7d-gate1-v1/simulated-trade-admission-m2k-1m-liquidity-sweep-reject-short-rvol-pda-guard-20260520T032305+0800`

Change from prior packet:

- generated explicit cleaned MTF ladder from retained real `1m` source: `1m/5m/15m/30m/1h/4h/1d`
- replayed the same AQ workspace and the same 19 simulated trades
- CatBoost train/apply/register/runtime-enable and workflow/pre-bayes/policy readbacks ran after trade ingestion

Result:

- `03_analyze_seed.exit=-15`
- `16_analyze_after_ranker.exit=-15`
- all other commands `01..19` exited `0`
- `exact_branch_survived=false`
- `ranker_validation_ready=false`
- `mature_rows=2`
- `history_mature_rows=20`
- `execution_candidate_status=null`
- `execution_readiness=0.0`
- `transition_hazard=1.0`
- `pda_hybrid_alignment=false`
- `path_ranker_score_visible_to_execution_tree=null`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Verdict: adding the full timeframe ladder did not repair this same-root blocker. It made the analyze/execution materialization path fail before an exact execution candidate or tree trace existed. Do not repeat the same full-ladder simulated-admission relaunch.

## Rule

If an exact-root `1m` futures branch survives `5bps/side` and same-workspace simulated feedback runs cleanly, still fail closed unless the current execution predicates pass together: actionable exact execution candidate, active transition/readiness thresholds, mature validation, and path-ranker score actually used by the execution tree. Treat short simulated feedback as a repair probe and maturity visibility tool, not promotion evidence. The next same-root attempt should directly isolate and repair analyze/execution-candidate materialization or the live transition/readiness blocker. Do not relaunch the same simulated full-ladder admission shape, lower gates, or count clean CatBoost mechanics as live readiness.
