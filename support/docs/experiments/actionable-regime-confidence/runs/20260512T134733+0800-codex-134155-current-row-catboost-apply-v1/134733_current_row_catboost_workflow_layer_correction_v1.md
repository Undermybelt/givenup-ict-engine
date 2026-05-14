# 134733 Current-Row CatBoost Workflow-Layer Correction v1

## Scope

Support-only readback for the short-window ETH six-provider branch:

- Parent chain: `125715 -> 131500 -> 130814 -> 131333/134155`.
- Sibling current-candidate repair roots: `134321`, `134558`, and this `134733`.
- This does not add provider/AQ authority, production BBN mutation, execution-tree promotion, or trade usability.

## What Was Confirmed

- All `134733` commands exited `0`.
- `apply-structural-path-ranking-external-scores` wrote `4` rows.
- Policy-training status saw CatBoost current-row score continuity:
  - `runtime_selection=enabled_candidate_set_ready`
  - `runtime_matches=3`
  - `score_model_family=catboost`
  - `score_source_kind=external_model`
  - `raw_scored_mature=325/30`
  - `production_validation=324/30`
  - `observation_validation=162/30`

## What Still Failed Closed

The workflow and execution-candidate layer did not consume those scores as executable path-ranking evidence:

- `workflow-status --phase structural-recommended-path-bundle` still reported `path_ranker_runtime.status=enabled_no_matching_scores`.
- `workflow-status --phase execution-candidate` still reported:
  - `actionable=false`
  - `ready=false`
  - `candidate_status=execution_blocked`
  - `execution_gate_status=execution_blocked`
  - `execution_readiness=0.3046756738194877`
  - `pre_bayes_gate_status=observe_only`
  - `path_ranker_calibrated_path_prob=null`
  - `path_ranker_path_prob_lower_bound=null`
  - `path_ranker_raw_score=null`

## Field-Level Cause

The current candidate rows received raw CatBoost scores, but they still lacked admission fields:

- Current candidate rows had `raw_path_score=0.293439`.
- Current candidate rows had blank `calibrated_path_prob`.
- Current candidate rows had blank `path_prob_lower_bound`.
- Current candidate rows had blank `execution_gate_status`.
- The only populated calibrated/gated row in the target CSV was a historical feedback row, not the current candidate path.

So the short-window repair improved policy-training status, but it did not satisfy workflow-layer path-ranker admission or execution readiness.

## Decision

Board A remains fail-closed:

- accepted `>=95%` contexts: `0`
- strict full objective: false
- trade usable: false
- promotion allowed: false
- `update_goal=false`

This correction does not supersede the long-history direction correction. Future work should not repeat short-window ETH rescore loops unless they directly support the long-history validation contract.
