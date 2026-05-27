# Factor Candidate Buildable Closed-Loop Audit

Updated: `2026-05-27`

## Scope

This audit tracks one verified loophole in the Python factor-candidate resolver
surface. It does not claim that the full `ict-engine` training-to-live closed
loop is complete.

## Verified Problem

Authoritative repo contract in `AGENT.md` says candidate packs are
inspection/admission surfaces until runtime gates explicitly promote them.

Before this fix, `python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format human`
reported only `buildable_count` and then listed repo-native candidate packs
without any explicit fail-closed closed-loop status.

Current repo-native packs demonstrate why that is unsafe:

- `family_f_vrp_compression_15m_v1` was listed as buildable while
  `learning_admission_status=blocked`.
- `order_block_mitigation_block_1h_v1` was listed as buildable while
  `learning_admission_status=blocked`.
- The pre-fix human output exposed expectancy and transfer labels, but not
  `promotion_allowed=false` or `trade_usable=false`.

That made `buildable` too easy to misread as downstream-consumable.

## Fix

`support/scripts/research/factor_candidate_resolver.py` now keeps `buildable`
strictly as an artifact-reuse signal, while also emitting explicit fail-closed
closed-loop fields for each listed candidate:

- `closed_loop_consumption_status`
- `learning_blockers`
- `promotion_allowed`
- `trade_usable`

The buildable summary now also reports:

- `promotion_ready_count`
- `trade_usable_count`
- `inspection_only_count`

The human output now prints the closed-loop consumption status per candidate.

## Verification

Commands run in this slice:

```bash
python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver.FactorCandidateResolverTests.test_list_buildable_candidates_surfaces_curated_pack_metrics -v
python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v
python3 support/scripts/research/factor_candidate_resolver.py --list-buildable --output-format human
```

Observed post-fix resolver surface:

```text
buildable_count=8 candidate_count=14 promotion_ready_count=0 trade_usable_count=0 inspection_only_count=8
family_f_vrp_compression_15m_v1 ... blocked inspection_only_learning_blocked ...
order_block_mitigation_block_1h_v1 ... blocked inspection_only_learning_blocked ...
```

This proves the resolver no longer presents current repo-native buildable packs
as implicitly promotable.

## Additional Verified Loophole

The resolver fix did not cover every downstream consumer. In the same repo
state, `support/scripts/research/regime_conformal_calibration_report.py`
still treated missing `trade_usable` contract fields as `True` inside
`_conformal_set(...)`.

That was a fail-open conformal consumer contract:

- a legacy or malformed label contract missing `trade_usable` could still enter
  the conformal set;
- if no explicit labels passed threshold, the fallback `best` path could still
  return the highest-score label from the same malformed contract;
- this weakened the closed-loop rule that downstream practical/trade admission
  must be explicit, not inferred from missing fields.

Current fix changes both conformal selection paths to default
`trade_usable=False` when the field is absent.

Verification for this slice:

```bash
python3 -m unittest support/scripts/research/tests/test_regime_conformal_calibration_report.py
python3 -m unittest support/scripts/research/tests/test_downstream_practical_admission_source_check.py
```

Observed regression proof:

- new test `test_conformal_set_fails_closed_when_trade_usable_flag_missing`
  failed before the patch by returning `['primary::TrendExpansion']`;
- the same test passes after the patch and now returns `[]`.

## Additional Verified Loophole - Regime Sidecar Was Advertising Practical Admission

The resolver and conformal fixes still left one fail-open consumer path:
`support/scripts/research/regime_high_confidence_decision.py`.

Before this fix, a sidecar-only regime decision could emit `trade_usable=true`
as soon as the regime stack reached `single_label_99` or `single_label_95`.
That violated the repo contract in `AGENT.md`, which requires downstream
Pre-Bayes, BBN, path-ranker, execution-tree, and live-admission proof before
practical/promotion fields can turn true.

Unsafe pre-fix behavior:

- `decision_state=single_label_99` implied `trade_usable=true` with no explicit
  downstream live-admission artifact.
- `regime_consumer_bundle.py` propagated that value into `latest_decision`,
  making the token-friendly consumer surface easy to misread as runtime-ready.
- `regime_sidecar_pipeline.py` therefore returned a final decision that looked
  practically consumable even though the entire pipeline was still a regime-only
  sidecar.

### Fix

The sidecar decision now stays fail-closed on practical admission:

- `decision_state` still reports confidence shape such as `single_label_99` or
  `single_label_95`.
- `promotion_allowed=false` and `trade_usable=false` remain hardcoded unless a
  separate downstream live-admission contract exists.
- a new explicit
  `closed_loop_consumption_status=inspection_only_regime_sidecar_requires_downstream_live_admission`
  is emitted.
- abstain reasons now include
  `regime_sidecar_requires_downstream_live_admission`.
- `regime_consumer_bundle.py` now preserves `promotion_allowed` and
  `closed_loop_consumption_status` in `latest_decision` so bundle consumers do
  not silently drop the fail-closed state.

### Verification

Commands run in this slice:

```bash
python3 -m unittest support.scripts.research.tests.test_regime_high_confidence_decision -v
python3 -m unittest support.scripts.research.tests.test_regime_consumer_bundle -v
python3 -m unittest support.scripts.research.tests.test_regime_sidecar_pipeline -v
```

Observed regression proof:

- `test_single_label_99_remains_inspection_only_without_downstream_live_admission`
  failed before the patch because `trade_usable` was `True`;
- `test_single_label_95_when_99_gate_fails_but_95_accepts` failed before the
  patch for the same reason;
- both tests now pass and assert:
  `promotion_allowed=false`,
  `trade_usable=false`,
  `closed_loop_consumption_status=inspection_only_regime_sidecar_requires_downstream_live_admission`;
- `test_pipeline_runs_r2_to_r10_with_ohlcv` now proves the token-friendly
  pipeline result also stays inspection-only.

## Additional Verified Loophole - Conformal Label Contracts Reused A Practical Field Name

Even after the sidecar admission fix, one adjacent regime-only surface still
reused a practical-admission field name:
`support/scripts/research/regime_conformal_calibration_report.py`.

The issue was not that the conformal set was passing live-trade readiness. The
issue was semantic leakage:

- `_label_contracts(...)` emitted `trade_usable` to mean "this regime label is
  eligible to appear in a conformal label set";
- `_conformal_set(...)` consumed the same key;
- any downstream reader inspecting `label_contracts` could plausibly mistake
  that field for practical/live admission instead of regime-sidecar label
  eligibility.

That naming collided with the repo-wide meaning of `trade_usable`, which is
reserved for explicit practical/live-trade admission after downstream gates.

### Fix

The conformal report now uses regime-specific terminology:

- `label_contracts` emits `conformal_eligible` instead of `trade_usable`;
- `_conformal_set(...)` fails closed on missing `conformal_eligible`;
- the old misleading field name is no longer emitted by this report.

### Verification

Commands run in this slice:

```bash
python3 -m unittest support.scripts.research.tests.test_regime_conformal_calibration_report -v
python3 -m unittest support.scripts.research.tests.test_regime_sidecar_pipeline -v
python3 -m unittest support.scripts.research.tests.test_regime_high_confidence_decision -v
```

Observed regression proof:

- `test_unknown_labels_remain_non_conformal_eligible` now asserts the report
  emits `conformal_eligible=false` for unknown labels and no longer emits
  `trade_usable`;
- `test_label_contracts_use_conformal_eligibility_name_not_practical_admission_name`
  proves the renamed field is present and the misleading field is absent;
- `test_conformal_set_fails_closed_when_conformal_eligible_flag_missing`
  proves the selection path still fails closed;
- adjacent sidecar pipeline and high-confidence decision tests still pass,
  proving the terminology repair did not break the current fail-closed
  inspection-only pipeline.

## Still Unproven

This slice does not prove any of the following:

- that any current candidate is promotion-ready;
- that any current candidate is trade-usable;
- that the Pre-Bayes, BBN, path-ranker, execution-tree, and feedback/update
  links are all green for a real factor lane;
- that Board B current active claims are terminalized enough for a fresh
  end-to-end training lane.

As of the same-turn `factor_claim_terminalization_audit.py --compact` readback
on `2026-05-27 13:51 +0800`, Board B still reports `active_claims=1`,
`promotion_allowed_true=0`, and `trade_usable_true=0`. The remaining active
claim is still the prep-only same-root TOMAC child:
`codex-tomac-tod-balanced-early2021-hour13-gapfill-prep-20260527T133948+0800`.
