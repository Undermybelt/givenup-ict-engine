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
- [ ] Run full heavy gates (`cargo check/clippy/test + smoke`) on current tree
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
- [ ] Optional heavy refresh:
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

## Notes

- Default path is read-only and no-network except local `help_audit` probe,
  aligned with "no pollution / no debt".
- Heavy checks remain operator-controlled to avoid accidental long-running
  compile/test load in crowded worktrees.
