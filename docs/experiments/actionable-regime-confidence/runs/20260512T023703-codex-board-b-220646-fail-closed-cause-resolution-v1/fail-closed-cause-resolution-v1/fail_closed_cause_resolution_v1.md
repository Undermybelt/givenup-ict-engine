# Board B 220646 Fail-Closed Cause Resolution v1

## Conclusion

Current exact Sideways branch replay is rejected for this context, not promoted. The source recipe and RC-SPA score remain unchanged; this audit only resolves the downstream fail-closed cause after trace parity was repaired.

## Exact Branch

`Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

## Evidence

- Auto-Quant status: `dependency_ready_data_ready`; source score unchanged at `85.7407`.
- Provider surface kept in view: yfinance, Kraken, IBKR, and TradingViewRemix strings are present in provider-status output.
- Pre-Bayes: `latest_gate_status=pass_neutralized`, policy `318900600c5e8cf2`, active structural regime `trend` with primary market state `TrendExpansion` / `BullTrendAcceleration`.
- Entry bridge: selected quality `medium`, long-short probability gap `0.007747167221267781`.
- CatBoost/path-ranker: runtime ready `True`, production validation `869/30`, observation validation `82/30`.
- Workflow: candidate status `execution_blocked`, execution gate `execution_blocked`, readiness `0.4420748337394927`, ready `False`, actionable `False`.
- Execution tree: `closed_loop_branch_admission.status=fail_closed`, gate `observe`, branch `transition_guardrail`, bias `guarded`.
- Ledger: `promote_candidate=False`, `actionable=False`.

## Decision

Treat this exact branch as fail-closed for the current replay context because the branch root is Sideways/RangeCarry while the filtered runtime context is TrendExpansion/BullTrendAcceleration and Pre-Bayes is neutralized. Next work should replay only with a user-selected/provider-sourced Sideways or range-compatible context, or encode an explicit abstain/sibling branch for non-Sideways contexts.

## Assertions

```json
{
  "catboost_runtime_ready": true,
  "exact_branch_preserved": true,
  "execution_candidate_not_actionable": true,
  "execution_tree_fail_closed": true,
  "ledger_not_promotional": true,
  "path_ranker_validation_ready": true,
  "pre_bayes_neutralized": true,
  "pre_bayes_not_sideways_root": true,
  "pre_bayes_trend_context": true,
  "provider_names_present": true
}
```
