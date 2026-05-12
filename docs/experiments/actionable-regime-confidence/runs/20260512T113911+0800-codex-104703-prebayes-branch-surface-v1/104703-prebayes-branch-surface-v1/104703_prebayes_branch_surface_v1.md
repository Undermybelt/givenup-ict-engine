# 104703 Pre-Bayes Branch Surface v1

Run id: `20260512T113911+0800-codex-104703-prebayes-branch-surface-v1`

## Scope

This isolated probe copied the already CatBoost-ready `113152` exact-branch state and consumed one exact structural feedback submission for `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`.

## Readback

- `00_analyze_live_btc_yfinance.exit=130`: stopped after no stdout/stderr while CPU-bound; no durable analyze-live policy was created by that step.
- `01` through `06` exited `0` for update, Pre-Bayes status, policy-training status, structural bundle, execution-candidate, and full workflow readbacks.
- Pre-Bayes gate surface is now present: `latest_gate_status=pass_neutralized`.
- Pre-Bayes exact branch assignment is present: `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`.
- Durable latest Pre-Bayes policy remains absent: `latest_policy_present=False`.
- CatBoost/path-ranker validation remains ready: `Ranker validation: calibration=true quality_ready=true raw_scored_mature=86/30 production_validation=85/30 observation_validation=43/30 ready=true`.
- Closed-loop branch admission remains `fail_closed` with `execution_gate_status=execution_observe_only` and `review_status=observe`.

## Decision

This repairs the narrow `pre_bayes_gate_and_branch_assignments_missing` surface for the exact 104703 branch, but it is not promotion evidence. The run remains fail-closed because the gate is `pass_neutralized`, the durable Pre-Bayes policy/bridge is absent after the stopped analyze-live attempt, execution is observe-only, and the same-root six-provider AQ authority gate is still unsatisfied.
