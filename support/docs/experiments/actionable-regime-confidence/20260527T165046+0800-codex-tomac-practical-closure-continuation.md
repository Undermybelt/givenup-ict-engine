# TOMAC Practical Closure Continuation

- timestamp: `20260527T165046+0800`
- owner: `codex`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- objective: continue TOMAC work until a branch reaches practical, same-root trading closure or a concrete blocker is proven with artifacts
- scope: Board B TOMAC continuation only
- non_goals: do not reuse shared current-state docs as live scratchpads; do not relaunch duplicate active lanes; do not declare trade-readiness from Gate 1 alone

## Baseline Read Set

1. `AGENT.md`
2. `support/scripts/factor_claim_terminalization_audit.py --compact` output
3. current `/tmp` TOMAC workdoc and claim truth
4. latest same-root TOMAC artifacts that survived Gate 1 or failed practical/runtime gates

## Todo Checkpoint

- [x] Create slice-local repo doc
- [x] Create `/tmp` workdoc
- [x] Create `/tmp` claim
- [x] Audit Board B claims and live factor processes
- [x] Identify the freshest non-duplicated TOMAC blocker root
- [x] Pick the next smallest safe TOMAC slice
- [x] Verify the slice with same-turn artifacts

## Evidence Log

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  currently reports `active_claims=10`, `invalid_active_claims=0`,
  `live_factor_processes=0`, `attention_groups.by_owner={"codex":10}`,
  `next_action=terminalize or externalize active claims`.
- strongest same-root TOMAC branch still comes from
  `/tmp/ict-engine-tomac-tod-balanced-practical-repair-20260526T214903+0800/top1965_comp40_floor50_exact_suppressed`
  with `trade_count=1633`, `signal_count_parity=true`, `gate1_survivor=true`.
- `python3 -m unittest support/scripts/research/tests/test_purged_cv_backtest_guard.py support/scripts/research/tests/test_tomac_tod_balanced_trade_label_sidecar.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_balanced_practical_admission_prep_v1.py -v`
  passed `10` tests.
- `python3 -m unittest support/scripts/research/tests/test_simulated_feedback_admission_guard.py -v`
  passed `9` tests.
- real same-root rerun:
  `python3 support/scripts/research/tomac_tod_balanced_trade_label_sidecar.py --exact-root /tmp/ict-engine-tomac-tod-balanced-practical-repair-20260526T214903+0800/top1965_comp40_floor50_exact_suppressed --output-dir /tmp/ict-engine-tomac-practical-closure-20260527T165046+0800/sidecar-rerun`
  preserved `label_count=1633`, `trade_count_parity=true`,
  `purged_cv_gate=reject`, and downstream fail-closed blockers on frequency,
  unresolved provider parity, validation rows, and execution readiness.
- owner fix:
  `support/scripts/research/tomac_tod_balanced_trade_label_sidecar.py` no
  longer hard-codes `provider_parity=false` and zero validation/readiness rows;
  it now hydrates those fields from sibling downstream exact artifacts when
  present and stays fail-closed only as fallback.
- second owner fix:
  `support/scripts/research/simulated_feedback_admission_guard.py` no longer
  treats multi-pair basket cadence as one aggregate stream for daily trade-count
  caps; when `pair` is present it evaluates daily frequency per pair while
  keeping long-gap checks fail-closed.
- hydrated same-root readback:
  the sidecar now preserves actual downstream metrics for this root instead of
  synthetic zero placeholders:
  `raw_scored_mature_rows=1`, `production_validation_rows=1`,
  `observation_validation_rows=0`, `execution_readiness=0.4606046164602364`,
  `transition_hazard=0.6248959443126174`,
  `execution_candidate_actionable=false`.
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-live.json`
  returned `completion_ready=false`, `evidence_level=partial_skipped_gates`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
  currently fails `worktree_clean_for_release`,
  `source_origin_matches_selected_source`,
  `release_version_tag_available`.
- bounded provider parity proof:
  `cargo run --quiet -- provider-status --provider ibkr --agent` returned
  `market_data:1/1 ready`;
  rerunning
  `tomac_tod_balanced_provider_parity_probe.py --duration '1 D' --request-timeout 20`
  succeeded for all three basket proxies and wrote
  `checks/provider_parity_probe.json` with
  `decision=bounded_provider_parity_recent_rows_present`.
- post-proof same-root readback:
  rerunning the real sidecar cleared `provider_parity_false` and the aggregate
  daily-count artifact. The remaining downstream blockers are now:
  `frequency.max_gap_days_gt_allowed:350.00>3.00`,
  `raw_scored_mature_rows_lt_30`,
  `production_validation_rows_lt_30`,
  `observation_validation_rows_lt_30`,
  `execution_readiness_lt_0.65`,
  `transition_hazard_gte_0.60`,
  `actionable_false`.

## Drift Check

- status: `continue`
- note:
  current-turn evidence strengthened the blocker diagnosis. The strongest TOMAC
  root still fails practical closure after a real rerun, and objective-level
  completion remains false because Board B closure and release closure are both
  still red.
