# Release Notes

Version: `v0.1.7`
Draft date: 2026-05-24
Status: selected clean candidate for the private `ict-engine-release` mirror.

## Scope

`v0.1.7` carries the release-mirror continuation after `v0.1.5` exposed a
mirror CI docs-runtime-isolation failure and `v0.1.6` delivered the immediate
correction without rewriting the failed tag.

This tag is the next selected source snapshot after follow-up Board A/B
gate/source repairs and release-audit timeout hardening were committed and
verified from a clean worktree. It remains a private source mirror release, not
a crates.io, npm/npx, Homebrew, Docker, binary, or public package-manager
release.

## Changes since `v0.1.6`

- Preserves the `v0.1.6` privacy/docs-runtime isolation correction.
- Includes Board A/B source-side readback and gate repairs through
  `0ae337610e4d3e37078915bcee484f693ebb81f7`.
- Hardens release/done-definition helper timeout propagation in
  `518b05579cb3d851accae1da43f8a9cf6d637389`.
- Keeps the public zero-config consumer path and mirror-only release policy.

## Final clean verification

Clean worktree:
`/tmp/ict-engine-release-clean-current-20260524T185534+0800`
at `518b05579cb3d851accae1da43f8a9cf6d637389`.

Gate log:
`/tmp/ict-engine-v017-current-gates-20260524T185534+0800/gates.log`.

Passed gates:

- release readiness after source push: pass.
- docs runtime isolation: exit `0`.
- release privacy audit: exit `0`, `release_blocking_hits=0`.
- release/done-definition helper tests: exit `0`.
- cargo fmt: exit `0`.
- cargo clippy `--locked --all-targets -- -D warnings`: exit `0`.
- cargo test `--locked`: exit `0`.
- zero-config smoke: `provider-status --compact`, demo `analyze --human`, and
  `workflow-status --agent`: all exit `0`.

## Release requirements

Publish `v0.1.7` from the selected committed `HEAD` only after readback confirms:

- mirror `main` advances on `Undermybelt/ict-engine-release`;
- tag `v0.1.7` exists and resolves to the published mirror commit;
- GitHub release `v0.1.7` exists;
- no package-manager publication is enabled.

## Release label

`ict-engine v0.1.7`
