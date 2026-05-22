# 2026-05-23 Release Readiness Remote Readback Handoff TODO

Owner: Codex maintenance loop slice.
Scope: make release mirror readback failures actionable while preserving
fail-closed release semantics.

## Intent

The release audit must be useful to a downstream maintainer or agent without
requiring private context. If release mirror readback fails, the audit should
name the gate it blocks and the next operator action. It must not infer tag
availability from local state, and it must not publish, tag, push, or mutate the
mirror.

## Current Todo Board

### Done

- [x] Route through `sd/ict-engine-maintenance-loop` and repo `AGENT.md`.
- [x] Add RED regression for `remote_readback` failure actionability.
- [x] Add `evaluate_remote_readback(...)` with:
  - `origin_status`
  - `release_mirror_status`
  - `blocked_gate=release_version_tag_available`
  - `next_action` for restoring mirror git/network/auth readback and rerunning
    `--check-remotes`
  - fail-closed `status=fail`
- [x] Preserve tag authority: `release_version_tag_available` still depends on
  release mirror tags, not local tags.
- [x] Run targeted and full release-audit unit tests.
- [x] Run py_compile and script manifest verification.
- [x] Run a fresh real `--check-remotes` compact audit.

### Next

- [ ] If release mirror readback fails again, use the enriched
  `remote_readback.details.next_action` as the operator-facing remediation.
- [ ] For an actual release lane, select an explicit new version/tag, update
  release metadata, and rerun the release readiness audit from a clean sanitized
  export.
- [ ] Refresh `support/docs/audits/release-signoff.md` and
  `support/docs/release-notes-draft.md` for the selected tag/export.
- [ ] Re-run full done-definition heavy gates after any source change intended
  for release.

### Not Yet

- [ ] No clean release export has been built in this slice.
- [ ] No release tag/version has been selected or changed.
- [ ] No release mirror push, tag, or GitHub Release has been attempted.
- [ ] Factor-claim terminalization remains outside this slice.

## Evidence

- RED:
  `python3 -m unittest support.scripts.tests.test_release_readiness_audit.ReleaseReadinessAuditTest.test_remote_readback_failure_names_blocked_tag_gate -v`
  failed before implementation because `evaluate_remote_readback` was missing.
- GREEN targeted:
  the same test passed after adding the helper.
- Full release-audit tests:
  `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
  passed `13` tests.
- Compile:
  `python3 -m py_compile support/scripts/release_readiness_audit.py support/scripts/tests/test_release_readiness_audit.py`
  passed.
- Script manifest:
  `python3 support/scripts/check_script_manifest.py`
  passed with `entries=21`.
- Real compact remote audit:
  `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-release-readiness-remote-actionability-20260523.json`
  exited `1` as expected.

## Current Readback

The latest real remote audit read the release mirror successfully this time, so
the new `remote_readback` failure details are covered by unit regression rather
than the live environment. Current release readiness still reports
`summary.status=needs_fix`.

Unresolved gates from
`/tmp/ict-engine-release-readiness-remote-actionability-20260523.json`:

- `worktree_clean_for_release`
- `release_docs_fresh_for_selected_tag`
- `source_origin_matches_selected_source`
- `release_version_tag_available`

Important details:

- Current source `HEAD=fd24f3f67bb81fce46b27f1049e9cacf899b306b`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Source is `81` commits ahead of `origin/main`.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Current `Cargo.toml` version is `0.1.3`.
- Candidate tag `v0.1.3` already exists in the release mirror.
- Audit suggests unused next patch version `0.1.5`.

## Compatibility Boundary

- Public/compact output remains token-friendly.
- The audit remains read-only.
- No private paths or keys are needed for default operation.
- Richer remote readback is opt-in via `--check-remotes`.
- Mirror availability is treated as evidence, not assumed.

## Resume State

Resume from this file plus the JSON artifact above. Do not answer release-ready
until a clean export, fresh release docs, unused version/tag, source-origin
alignment, full verification, and explicit operator publish instruction all
exist.
