# HACK cybersecurity density downstream fail-closed

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session lesson from regime-rooted profitability-factor continuation.

## Branch

```text
TVR / ETF / HACK / 1m
TrendExpansion -> CybersecurityETFOpeningDrive -> one_minute_opening_drive_rvol_vwap_density_full_ladder -> tvr_hack_cybersecurity_opening_drive_rvol_vwap_density_1m_full_ladder_v1
```

## What passed

- TradingViewMCP provider ladder covered `1m/5m/15m/30m/1h/4h/1d` with `local_cache_replay=false`.
- Auto-Quant Gate 1 produced `7` ranked rows, `123` total trades, and positive `1m` origin plus `5m/15m/30m` siblings.
- Cost stress passed for the origin lane.
- AQ import, Pre-Bayes/status, BBN/workflow, structural target export, path-ranker trainer, direct-fallback scoring, score apply, runtime enable, analyze readback, workflow readback, Pre-Bayes readback, and policy readback all executed after corrective rerun.
- Exact branch survived downstream: `closed_loop_branch_admission.path_id` matched the tested rooted path.

## Corrective command pattern

When CatBoost training emits a direct fallback artifact but apply fails with:

```text
No trained model found ... pass --allow-direct-fallback to use weighted_feature_sum_v1
```

rerun apply with `--allow-direct-fallback`, register the artifact as `weighted_feature_sum_v1`, enable runtime, and rerun analyze/workflow/pre-bayes/policy before judging the branch.

## What failed

Despite Gate 1 and branch parity, execution remained observe-only:

```text
pre_bayes_gate_status=observe_only
execution_gate_status=execution_observe_only
execution_tree_gate_status=observe
execution_tree_branch=transition_guardrail
path_ranker_visible=true
path_ranker_used=false
ranker_validation_ready=false
hybrid_transition_hazard=0.889 threshold=0.600
pda_hybrid_alignment=false
execution_readiness=0.1732
promotion_allowed=false
trade_usable=false
update_goal=false
```

## Reusable rule

A dense/cost-surviving 1m-origin AQ branch is not enough. If downstream readback shows `hybrid_transition_hazard >= 0.60`, `pda_hybrid_alignment=false`, or `execution_readiness < 0.65`, preserve it only as scoped observation/incubation. The next same-root overlay should target transition stability and PDA/hybrid alignment; do not lower thresholds or call it live-ready.
