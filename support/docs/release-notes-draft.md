# Release Notes

Version: `v0.1.9`
Draft date: 2026-06-01
Status: retargeted candidate for the private `ict-engine-release` mirror; full
release readiness remains blocked until the current source is exported from a
clean tree and private release mirror readback passes.

## Scope

`v0.1.9` carries the release-mirror continuation after `v0.1.8` was already
present in the private release mirror. It preserves the prior mirror-only
release boundary and avoids rewriting or reusing the published `v0.1.8` tag.

This tag is the next selected source snapshot after follow-up objective-closure
and release-readiness audit hardening. It remains a private source mirror
release, not a crates.io, npm/npx, Homebrew, Docker, binary, or public
package-manager release.

## Changes since `v0.1.7`

- Preserves the prior privacy/docs-runtime isolation correction and mirror-only
  release policy.
- Adds objective-closure fail-closed handling for release remote/tag checks.
- Adds release signoff/notes/Cargo tag-consistency checks.
- Adds a release-clone Auto-Quant startup guard: default bootstrap source is
  `https://github.com/undermybelt/Auto-Quant`, and missing-dependency readiness
  output prints the full `auto-quant-bootstrap --repo-url ...` command.
- Adds repo-local Auto-Quant handoff skill files to the release mirror so
  release-clone agents can read the installed workflow contract.
- Keeps the public zero-config consumer path as the release smoke baseline.

## Required clean verification

The current retarget only clears the reused-tag blocker. Before publishing,
create a clean selected-source export and rerun the full release gate suite from
that export.

Minimum gates:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
- `python3 support/scripts/release_privacy_audit.py . --compact`
- focused helper tests for changed release/objective scripts
- `cargo fmt --check`
- `cargo clippy --locked --all-targets -- -D warnings`
- `cargo test --locked`
- zero-config smoke: `provider-status --compact`, demo `analyze --human`, and
  `workflow-status --agent`

## Release requirements

Publish `v0.1.9` from the selected committed `HEAD` only after readback confirms:

- mirror `main` advances on `Undermybelt/ict-engine-release`;
- tag `v0.1.9` exists and resolves to the published mirror commit;
- GitHub release `v0.1.9` exists;
- no package-manager publication is enabled.

## Release label

`ict-engine v0.1.9`
