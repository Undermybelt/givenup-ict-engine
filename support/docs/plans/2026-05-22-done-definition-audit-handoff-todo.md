# 2026-05-22 Done Definition Audit Handoff TODO

Owner: Codex (maintenance loop slice)
Scope: add repeatable, low-pollution Done Definition auditor for ongoing
audit/remediation loops.

## Objectives

- [x] Add zero-config, token-friendly, read-only default auditor.
- [x] Keep heavy verification opt-in and fail-closed.
- [x] Register script governance metadata.
- [x] Add focused unit tests for parser/summary logic.
- [x] Append evidence block to master remediation plan.
- [x] Run full heavy gates (`cargo check/clippy/test + smoke`) on current tree
      with fresh evidence packet.
- [x] Decide commit boundary for this slice after heavy-gate evidence review
      (narrow governance/script/doc slice only).

## Implemented Files

- `support/scripts/done_definition_audit.py`
- `support/scripts/tests/test_done_definition_audit.py`
- `support/scripts/SCRIPTS.md`
- `support/scripts/script_manifest.json`
- `support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`

## Verification Log (live updates)

- [x] `python3 -m py_compile support/scripts/done_definition_audit.py support/scripts/tests/test_done_definition_audit.py`
- [x] `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
- [x] `python3 -m unittest support.scripts.tests.test_help_audit -v`
- [x] `python3 support/scripts/check_script_manifest.py`
- [x] `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-light.json`
- [x] Optional heavy refresh:
      `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-heavy.json`
- [x] Optional partial heavy probe:
      `python3 support/scripts/done_definition_audit.py --run-smoke --output /tmp/ict-engine-done-definition-audit-smoke.json`
- [x] Heavy-skip flags verified:
      `--run-cargo-check`, `--run-cargo-clippy`, `--run-cargo-test`

## Evidence Snapshot

- Light report: `/tmp/ict-engine-done-definition-audit-light.json`
  - `summary.status=pass`, `pass_count=4`, `skip_count=4`, unresolved none.
- Smoke-enabled report: `/tmp/ict-engine-done-definition-audit-smoke.json`
  - `summary.status=pass`, `pass_count=5`, `skip_count=3`, `smoke_acceptance_tmp_state=pass`.
  - Remaining heavy skips point to explicit enable flags:
    - `cargo_check_all_targets -> --run-cargo-check`
    - `cargo_clippy_all_targets_deny_warnings -> --run-cargo-clippy`
    - `cargo_test -> --run-cargo-test`
- Heavy report: `/tmp/ict-engine-done-definition-audit-heavy.json`
  - `summary.status=pass`, `pass_count=8`, `fail_count=0`, `skip_count=0`, `unresolved=[]`.
  - Passed gates:
    - `main_rs_line_guardrail`
    - `quickstart_surface`
    - `script_governance_surface`
    - `help_audit_none_output_policy`
    - `cargo_check_all_targets`
    - `cargo_clippy_all_targets_deny_warnings`
    - `cargo_test`
    - `smoke_acceptance_tmp_state`

## 2026-05-22 Heavy-Gate Closure Update

The first full heavy run exposed two current-tree blockers:

- `cargo_clippy_all_targets_deny_warnings`
  - `src/status_command.rs::provider_status_shell` had too many arguments.
  - `src/status_command.rs::factor_mutation_status_shell` had too many arguments.
- `cargo_test`
  - explicit structural path-ranker trainer artifact errors lacked the required
    schema/recovery wording in one path;
  - registered-artifact runtime could pick a stale duplicate row sharing the
    same `path_id` instead of the current `candidate_set_id` row.

Fixes applied in the current maintenance slice:

- moved the two status shell adapters to local input structs, matching the
  existing `WorkflowStatusShellInput` / artifact shell adapter style;
- kept factor mutation status command input structured at the application
  boundary;
- tightened structural path-ranker explicit artifact validation wording;
- made registered-artifact row selection prefer exact current
  `candidate_set_id` matches over stale duplicate `path_id` rows.

Verification:

- `cargo clippy --all-targets -- -D warnings`
- `cargo test application::entry_models::training_export::tests::register_structural_path_ranking_trainer_artifact_requires_rule_or_tree_for_explicit_family -- --nocapture`
- `cargo test application::orchestration::structural_playbook::tests::path_ranker_runtime_prefers_current_candidate_row_over_stale_duplicate_artifact_row -- --nocapture`
- `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-heavy.json`

Current state before the 2026-05-22 18:59 rerun: all Done Definition auditor
gates passed on the current tree. This is maintenance-gate closure evidence
only; it is not a release claim.

## 2026-05-22 Fresh Rerun Timeout-Serialization Repair

A fresh full-heavy rerun was started for the latest completion audit:

- `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-current-heavy-rerun.json`

The rerun exposed a reporting bug before it could produce a reusable JSON
verdict: when the smoke subcommand timed out, `subprocess.TimeoutExpired`
returned `stdout` / `stderr` as bytes, and the auditor crashed during
`json.dumps(report)` with `TypeError: Object of type bytes is not JSON
serializable`.

Fix applied:

- normalize timeout `stdout` / `stderr` in `support/scripts/done_definition_audit.py::run_command`
  before writing the report.
- add regression coverage in
  `support/scripts/tests/test_done_definition_audit.py::test_run_command_timeout_details_are_json_serializable`.

Verification:

- RED before fix:
  `python3 -m unittest support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_run_command_timeout_details_are_json_serializable -v`
  failed because timeout `stdout` was `bytes`.
- GREEN after fix:
  the same targeted test passed.
- `python3 -m py_compile support/scripts/done_definition_audit.py support/scripts/tests/test_done_definition_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
  passed, `7` tests.
- Timeout regression probe:
  `python3 support/scripts/done_definition_audit.py --run-smoke --heavy-timeout-seconds 1 --output /tmp/ict-engine-done-definition-timeout-json-regression.json`
  exited `1` as expected, wrote valid JSON, and reported
  `smoke_acceptance_tmp_state=fail` / `error=timeout` with string
  `stdout` / `stderr`.
- Fresh light audit after the fix:
  `/tmp/ict-engine-done-definition-audit-current-light-after-timeout-fix.json`
  has `summary.status=pass`, `pass_count=4`, `fail_count=0`, `skip_count=4`.

Current post-repair status: the auditor can now report timeout failures
instead of crashing. A new full-heavy pass still needs to be rerun before making
any current-tree full-heavy completion claim. This repair is not a release claim
and not a factor-promotion claim.

## 2026-05-22 Three-Part Completion Audit Rerun

Prompt being audited:

- "实时检验 ict engine 最新审计结果"
- "逐步扩散可实战因子结果至全市场全品种"
- "发布到 mirror release"

Current deterministic answer: not complete. The latest local audit gate now has
fresh passing evidence, but the factor and release requirements are not proven.

Fresh audit evidence:

- Full-heavy auditor command:
  `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-20260522-current-heavy.json`
- Result:
  `summary.status=pass`, `pass_count=8`, `fail_count=0`, `skip_count=0`,
  `unresolved=[]`.
- Passed gates:
  `main_rs_line_guardrail`, `quickstart_surface`,
  `script_governance_surface`, `help_audit_none_output_policy`,
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`.
- This proves the current-tree Done Definition audit gate only. It is not a
  sanitized release-export proof and not factor-promotion proof.

Factor diffusion readback:

- Read-only sweep over
  `support/docs/experiments/actionable-regime-confidence/runs/20260522*`
  found `153` run roots and `149` terminal metrics files.
- Counts from terminal metrics: `trade_usable=true: 0`,
  `promotion_allowed=true: 0`, `downstream_allowed=true: 11`, and
  `gate1_5bps_survivor-like signals: 11`.
- Latest survivor blocker map:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T192643+0800-codex-regime-root-survivor-blocker-map-v1/summaries/terminal_decision_summary.md`.
- Blocker-map decision: no branch in the readback satisfies all hard gates; do
  not mark the goal complete.
- Concrete hole: several lanes can be observation or same-root repair material,
  but none proves practical all-market/all-product deployment readiness.

Release mirror readback:

- Source remote `origin/main` readback: `79d9579e...`.
- Current source `HEAD`: `c3924f45...`; local branch is still `51` commits
  ahead of source remote.
- Release mirror `main` readback:
  `ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- GitHub Releases readback: latest is `v0.1.4` at
  `2026-05-18T13:02:21Z`; `v0.1.3`, `v0.1.2`, `v0.1.1`, `v0.1.0`, and
  `v0.0.1` also exist.
- Current release docs are stale for a fresh publish claim:
  `support/docs/audits/release-signoff.md` still describes `v0.1.3`, and the
  runbook warns that the version field must not be treated as release readiness.
- Current worktree is broad and dirty: `91` tracked modified paths and `781`
  untracked paths were observed in this audit turn. Do not publish or mirror-sync
  from this worktree directly.

Required next fixes before any completion claim:

1. Current audit lane:
   keep `/tmp/ict-engine-done-definition-audit-20260522-current-heavy.json` as
   current-tree evidence, then rerun it after any additional source change.
2. Practical factor lane:
   start from the latest blocker map and repair a same-root candidate, preferably
   M2K `1m` RVOL/PDA or SI `5m` tight-range, through real/current mature
   validation, PDA/transition repair, execution-candidate materialization, and
   trade-admission gates. Fresh Gate 1 exploration is only justified for a truly
   new unclaimed public-family cell.
3. Release mirror lane:
   choose an explicit next tag/version, rebuild a clean sanitized export from
   the intended committed source, rerun fmt/Clippy/tests/smoke/privacy from the
   export, refresh `release-signoff.md` and release notes to the new tag, compare
   against mirror `main`, and only then push mirror main/tag and create a GitHub
   Release after explicit operator confirmation.

Completion remains unproven until all three lanes have fresh, matching
authoritative evidence.

## Notes

- Default path is read-only and no-network except local `help_audit` probe,
  aligned with "no pollution / no debt".
- Heavy checks remain operator-controlled to avoid accidental long-running
  compile/test load in crowded worktrees.

## 2026-05-22 Path-Ranker Smoke Acceptance Continuation

Current inherited slice:

- `support/scripts/smoke_acceptance.sh` now asserts the zero-config DEMO
  structural path-ranker boundary:
  - target export is inspectable;
  - trainer manifest is inspectable;
  - runtime selection remains disabled by default;
  - missing trainer artifact and validation shortfall are visible.
- `support/scripts/tests/test_smoke_acceptance.py` now has a weak
  `policy-training-status` fixture and verifies the smoke script fails when the
  fail-closed path-ranker fields are absent.

Verification in this continuation:

- `python3 -m unittest support.scripts.tests.test_smoke_acceptance`
  passed, `4` tests in `3.752s`.
- Fresh full-heavy auditor:
  `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-20260522-current-heavy.json`
  completed with `summary.status=pass`, `pass_count=8`, `fail_count=0`,
  `skip_count=0`, `unresolved=[]`.
- The real smoke output at
  `/tmp/ict-engine-done-definition-audit-smoke-out/policy_training_agent.out`
  contains the expected fail-closed path-ranker evidence:
  `export_ready=true`, `trainer_manifest_ready=true`,
  `runtime_selection_enabled=false`, `trainer_artifact=missing`,
  `runtime_selection=disabled`, and `production_validation=0/30`.
- Re-run after heavy completion:
  `python3 -m unittest support.scripts.tests.test_smoke_acceptance`
  passed, `4` tests in `1.161s`.

Closed for this slice:

- The smoke-acceptance extension is now verified by focused unit coverage and
  by the real full-heavy smoke gate.
- This is done-definition / smoke-boundary evidence only. It is not a release
  claim and not a strategy or factor-promotion claim.

Next exact commands for future re-verification:

```bash
STATE_DIR=/tmp/ict-engine-smoke-acceptance-path-ranker-state \
OUT_DIR=/tmp/ict-engine-smoke-acceptance-path-ranker-out \
support/scripts/smoke_acceptance.sh

rg -n 'export_ready|trainer_manifest_ready|runtime_selection|trainer_artifact|production_validation' \
  /tmp/ict-engine-smoke-acceptance-path-ranker-out/policy_training_agent.out
```
