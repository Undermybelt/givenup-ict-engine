# M2K RangeReversion PDA-floor admission refresh (2026-05-20)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Correct factor-tree semantics

Do not use `M2K -> 1m` as tree root. Those are labels.

Factor path:

```text
RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1
```

Labels:

```text
market=FUTURES
product=equity_index
symbol=M2K
timeframe=1m
provider=IBKR
window=7D
```

## Fresh run evidence

Reverse-gate diagnostic:

```text
<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T182116+0800-codex-m2k-execution-admission-reverse-gate-diagnostic-v1
```

Simulated trade admission refresh:

```text
<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260520T093302+0800-codex-ibkr-m2k1m-rvol-pda-consistency-floor-7d-gate1-v1/simulated-trade-admission-m2k-1m-rvol-pda-consistency-floor-20260520T182204+0800
```

## Current gate state

- simulated_trade_rows=17
- wins=11
- losses=6
- exact_branch_survived=true
- mature_rows=2
- history_mature_rows=18
- ranker_validation_ready=false
- execution_candidate_actionable=false
- execution_candidate_status=no_trade
- execution_gate_status=observe
- execution_readiness=0.3211044072278747
- transition_hazard=0.9184975817511946
- pda_hybrid_alignment=false
- path_ranker_score_visible_to_execution_tree=true
- path_ranker_score_used_by_execution_tree=false
- covered intervals: 1m, 5m, 15m, 30m, 1h, 4h
- 1d insufficient: 9 bars < 29 required

## Decision

Observe only. Do not promote.

The path has real-cost survivor evidence and downstream visibility, but fails the user's hard gates under that historical readback:

- transition_hazard must be <0.60, current 0.9185
- historical pda_hybrid_alignment was false; current work must ignore this retired field unless live source reintroduces it
- execution_readiness must be >=0.65, current 0.3211
- execution candidate must be actionable, current no_trade/false
- ranker validation still below 30-row thresholds

Next useful work: adjust the same regime-root factor path toward the live transition/readiness/materialization blockers, or seek cross-label evidence for a more stable RangeReversion short family. Do not treat symbol/timeframe labels as tree parents.
