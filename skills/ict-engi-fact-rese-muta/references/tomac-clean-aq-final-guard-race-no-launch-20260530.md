# TOMAC Clean-AQ Final Guard Race No-Launch Lesson - 2026-05-30

## Context

Lane: `tomac_idxfut_clean_aroon_cci_cadence_lift_volume_persistence_retest_1m_v1`

Rooted branch:
`TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation -> CadenceLiftSymbolGuard -> VolumePersistenceRetest -> tomac_idxfut_clean_aroon_cci_cadence_lift_volume_persistence_retest_1m_v1`

The slice created a new repo tracking doc, `/tmp` workdoc, and claim, then added
tested family support to `run_tomac_index_futures_clean_aq_v1.py` under TDD. A
same-turn compact audit passed with `active_claims=0` and
`live_factor_processes=0`, so the wrapper was launched under the same run root.

## Evidence

- Tracking doc: `support/docs/experiments/actionable-regime-confidence/20260530T064801+0800-codex-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep.md`
- Workdoc: `/tmp/ict-engine-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep-20260530T064801+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T064801+0800-codex-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep.claim`
- Wrapper summary: `/tmp/ict-engine-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep-20260530T064801+0800/aq/summary.json`
- No-launch summary: `/tmp/ict-engine-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep-20260530T064801+0800/aq/summaries/terminal_no_launch_summary.json`
- Foreign runtime root: `/tmp/ict-engine-ym-minprice-smoke-20260530T0656`

Focused verification passed:

```bash
python3 -m unittest \
  support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_candidate_specs_include_crabel_nr7_intraday_expansion_continuation \
  support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_public_family_strategy_source_is_materially_distinct \
  support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_candidate_specs_can_select_only_next_family_rotation \
  support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_score_rows_uses_actual_backtest_span_for_density -v
python3 -m py_compile \
  support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_index_futures_clean_aq.py
git diff --check
```

## Lesson

A compact audit pass is necessary but not sufficient for TOMAC clean-AQ launch
safety. A foreign runtime can appear between the operator's audit and the
wrapper's final in-process guard. The wrapper must keep the final guard as the
authority and fail closed before cleaning/staging/AQ when any foreign runtime is
visible, even when the immediately previous compact audit passed.

When this race occurs, terminalize the lane as no-launch evidence:

- `decision=launch_blocked_by_foreign_claim_or_runtime`
- `clean_bundles=[]`
- `aq_staging=[]`
- `aq_commands=[]`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Do not convert a no-launch packet into a factor-negative result. No data was
cleaned, no Auto-Quant command ran, and no Gate 1 evidence exists. The next
attempt must rerun compact audit and focused process guard before launch.
