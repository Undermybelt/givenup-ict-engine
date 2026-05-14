# 111403 Path-Ranker Direct Bridge v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112215+0800-codex-111403-path-ranker-direct-bridge-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T111403+0800-codex-105014-ingest-bridge-fix-v1`

Symbol: `B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610`

## Result

Gate: `111403_path_ranker_direct_bridge_v1=direct_scores_applied_runtime_enabled_but_validation_floor_and_execution_fail_closed_no_promotion`

This run copied the settled `111403` ingest-bridge state, generated deterministic weighted fallback scores, applied them to the structural target, registered the fallback artifact, enabled runtime reuse, and reran policy/workflow readbacks. It is not promotion evidence.

## Evidence

- All commands exited `0`: `True`.
- Score rows emitted: `2`; score family: `weighted_feature_sum_v1`; source kind: `direct_fallback`.
- Runtime selection status: `enabled_registered_model_invalid`; active matches: `2`.
- Structural target rows: `2`; mature rows: `1`; history mature rows: `1`.
- Ranker validation: raw scored mature `1/30`, production validation `0/30`, observation validation `146/30`.
- Execution candidate: ready `False`, actionable `False`, review `observe`.
- Closed-loop branch admission: `fail_closed` / `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

The bridge proves the 111403 branch can accept external/direct fallback scores and enable the runtime contract in isolated copied state. It still cannot promote: only one mature structural target row is available, production validation remains below floor, Pre-Bayes remains empty, and execution stays observe/fail-closed.

Accepted rows added `0`. Mature rooted branch observations promoted `0`. Source/control evidence acquired `false`. Explicit selected-history `false`. Canonical merge `false`. Selected-data AutoQuant promotion `false`. Downstream promotion `false`. Strict full objective `false`. Trade usable `false`. Promotion allowed `false`. `update_goal=false`.

## Next

Do not promote from direct fallback scoring alone. The next useful slice is to create enough scored mature target rows under the same rooted branch, then rerun Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree with validation floors met.
