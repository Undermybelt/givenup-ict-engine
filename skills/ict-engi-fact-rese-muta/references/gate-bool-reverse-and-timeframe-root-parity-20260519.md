# Gate-bool reverse diagnosis and timeframe-root parity

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Trigger
Use when a factor-training artifact reports all downstream gates false, such as:

- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`

Do not stop at "Gate1 failed". Reverse the boolean surface into the missing factor properties before choosing the next candidate.

## Reverse map

### `pre_bayes_allowed=false`
Likely blockers:
- exact rooted branch has no positive cost-stressed AQ row
- real-cost trade density is too sparse
- branch metadata lost market/product/symbol/timeframe/regime identity
- low-timeframe root is being rescued by a higher-timeframe sibling

### `bbn_allowed=false`
Likely blockers:
- no same-root Pre-Bayes survivor
- regime evidence conflicts with factor direction
- downstream label set flattened to factor name instead of rooted path

### `catboost_allowed=false`
Likely blockers:
- insufficient mature/validation rows
- one-class or constant-feature target
- current exact branch absent from structural target
- fallback/pseudo-label model only proves plumbing

### `execution_tree_allowed=false`
Likely blockers:
- `transition_hazard >= 0.60`
- `pda_hybrid_alignment=false`
- `execution_readiness < 0.65`
- `closed_loop_branch_admission.path_id` pivots to sibling path
- SHAP dominated by overextension/spectral/reversion penalties

### `promotion_allowed=false` or `trade_usable=false`
Likely blockers:
- AQ -> Pre-Bayes -> BBN -> CatBoost -> execution-tree direction mismatch
- provider parity missing
- validation rows immature
- execution admission observe/fail-closed

## Timeframe-root parity rule
When restarting a failed 1m root as a 5m (or any other timeframe) candidate, the run is invalid unless artifacts prove the new root everywhere.

Hard checks before using the result:

```text
branch_path contains "<market> -> <product> -> <symbol> -> <base_timeframe> ->"
base_timeframe == intended root timeframe
training_timeframe == intended root timeframe
origin/provider rows come from the intended timeframe file
AQ material ids and package namespace use the intended timeframe
terminal_metrics.branch_path does not retain the old timeframe root
```

If any check fails, mark `ROLLBACK_REQUIRED: timeframe root not preserved` and rerun with a hard-failing runner. Do not use the artifact as evidence for the new timeframe.

## Practical implication
A failed QQQ 1m VWAP/reclaim root can justify a new exact 5m-root candidate, but only after the runner proves:

`US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> cost_stable_vwap_reclaim -> <profit_factor>`

1m rows may be microstructure/context for that lane, not proof for or against the 5m root.
