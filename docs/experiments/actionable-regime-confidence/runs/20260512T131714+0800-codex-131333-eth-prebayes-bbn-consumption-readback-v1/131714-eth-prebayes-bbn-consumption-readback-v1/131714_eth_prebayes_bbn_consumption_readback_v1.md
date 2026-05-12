# 131714 ETH Pre-Bayes/BBN Consumption Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T131714+0800-codex-131333-eth-prebayes-bbn-consumption-readback-v1`

Sources:
- `source_root_125715.txt`: six-provider ETH same-root Auto-Quant authority packet.
- `source_root_131333.txt`: prior Pre-Bayes/BBN consumption attempt.
- `source_root_131500.txt`: downstream ingest over the same six-provider ETH root.
- `source_root_130814.txt`: CatBoost/path-ranker runtime closure source.

## Command Status

All direct `131714` commands exited `0`:
- `01_validate_market_state_1h`
- `02_analyze_composite_apply_bbn`
- `03_pre_bayes_status_after_analyze`
- `04_policy_training_status_after_analyze`
- `05_workflow_structural_bundle_after_analyze`
- `06_workflow_execution_candidate_after_analyze`
- `07_workflow_full_after_analyze`
- `08_export_structural_path_ranking_target`

Follow-up post-export readback root `20260512T133943+0800-codex-131714-post-export-workflow-readback-v1` also exited `0` through policy-training status, structural bundle workflow, execution-candidate workflow, full workflow, and Pre-Bayes status.

## Pre-Bayes / BBN Readback

Pre-Bayes/BBN is no longer null in the isolated readback state, but it remains observe-only:
- `latest_gate_status=observe_only`
- `latest_uses_soft_evidence=true`
- active canonical structural regime: `range`
- canonical structural confidence: `0.367008438103555`
- canonical structural probabilities:
  - `range=0.34954935902525164`
  - `trend=0.2330329060168345`
  - `transition=0.2330329060168345`
  - `stress=0.18438482894107935`
- dominant soft-evidence probabilities are weak: market regime `range=0.34954935902525164`; factor alignment `mixed=0.6`; factor uncertainty `high=0.6`; liquidity context `neutral=0.6`; multi-timeframe resonance `mixed=0.6`.

The bridge is internally consistent but not decisive:
- multi-timeframe direction bias: `bullish`
- multi-timeframe alignment score: `0.999`
- multi-timeframe entry alignment score: `0.9026`
- long/short signal probability gap: `0.007918511296232222`
- selected entry quality: `medium` with probability `1.0`

## CatBoost / Path-Ranker Readback

After `131714` export and the `133943` post-export readback, historical validation remains mature but the current candidate set still has no matching runtime scores:
- runtime status: `enabled_no_matching_scores`
- runtime active matches: `0`
- current rows: `4`
- current mature rows: `1`
- current rows with raw path score: `0`
- current rows with calibrated path probability: `0`
- current rows with path probability lower bound: `0`
- current rows with execution gate status: `0`
- history rows: `329`
- history mature rows: `325`
- history rows with raw path score: `164`
- history rows with calibrated path probability: `162`
- history rows with path probability lower bound: `162`
- raw-scored mature validation: `163/30`
- production validation: `162/30`
- observation validation: `162/30`
- calibration status: `evaluated`
- trainer artifact status: `runtime_eligible`

This means the historical CatBoost/path-ranker floor is present, but current candidate rows do not receive raw, calibrated, lower-bound, or execution-gate fields.

## Execution Readback

Execution remains fail-closed:
- `candidate_status=execution_blocked`
- `ready=false`
- `actionable=false`
- `review_status=observe`
- `execution_gate_status=execution_blocked`
- `execution_readiness=0.3046756738194877`
- `selected_path_probability=0.33333333333333337`
- `path_probability_lower_bound=null`

Entry-model policy training remains blocked:
- `cisd_rb_long_v1`: `matched_rows=0`, not ready.
- `breaker_rb_long_v1`: `matched_rows=0`, not ready.

## Board A Decision

This run is support evidence only. It should be counted at most once as a Pre-Bayes/BBN soft-evidence consumption readback over the already-counted `125715 -> 131500 -> 130814` ETH chain.

No Board A acceptance is justified:
- calibrated regime/path confidence is far below `>=95%`
- Pre-Bayes gate remains `observe_only`
- current candidate rows have no matching CatBoost/path-ranker scores
- current calibrated path probability and lower bound are absent
- execution remains blocked and observe-only
- entry-model matched rows remain `0`
- trade usable remains false
- promotion allowed remains false
- `update_goal` must remain false

## Next Repair Target

Do not repeat provider/AQ authority, `125753` Kraken TOMAC no-data, or the earlier `131500/130814` numeric-floor CatBoost repair. The next useful slice is to make the current structural candidate set receive matching CatBoost/path-ranker scores while improving Pre-Bayes/BBN evidence quality enough to move beyond `observe_only` without relaxing the six-provider AQ provenance lock.
