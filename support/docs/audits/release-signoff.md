# Release signoff

Date: 2026-05-24
Selected candidate: `v0.1.7`
Selected source commit: `518b05579cb3d851accae1da43f8a9cf6d637389`
Status: selected clean candidate for the private `ict-engine-release` mirror.

## Correction scope

`v0.1.5` was published to the private `ict-engine-release` mirror and exposed a
CI failure in the mirror workflow's docs runtime isolation gate. `v0.1.6`
corrected that immediate failure without rewriting the failed tag.

`v0.1.7` is the next selected source snapshot. It preserves the privacy/docs
runtime isolation correction, includes subsequent Board A/B source-side gate
repairs, and hardens release/done-definition helper timeout propagation.

## Verified gates

Clean worktree:
`/tmp/ict-engine-release-clean-current-20260524T185534+0800`
at `518b05579cb3d851accae1da43f8a9cf6d637389`.

Evidence root:
`/tmp/ict-engine-v017-current-gates-20260524T185534+0800`.

- `python3 support/scripts/release_readiness_audit.py --check-remotes --compact`
  - exit `0` after source `origin/main` was aligned to the selected source.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`; `docs runtime isolation ok`.
- `python3 support/scripts/release_privacy_audit.py . --compact`
  - exit `0`; `release_blocking_hits=0`.
- `python3 -m unittest support.scripts.tests.test_help_audit support.scripts.tests.test_done_definition_audit -v`
  - exit `0`; `20` tests passed.
- `cargo fmt --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --check`
  - exit `0`.
- `cargo clippy --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --locked --all-targets -- -D warnings`
  - exit `0`.
- `cargo test --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --locked`
  - exit `0`.
- Zero-config smoke:
  - `provider-status --compact`: exit `0`.
  - `analyze --symbol DEMO --demo --human`: exit `0`.
  - `workflow-status --symbol DEMO --refresh --agent`: exit `0`.

## Required final readback

Before publishing, confirm:

```bash
git ls-remote https://github.com/Undermybelt/givenup-ict-engine.git refs/heads/main
git ls-remote https://github.com/Undermybelt/ict-engine-release.git refs/heads/main refs/tags/v0.1.7
```

After publishing, confirm mirror `main`, tag `v0.1.7`, the GitHub Release page,
and the GitHub Actions run conclusion.

## Release boundary

Package-manager publication remains disabled:

```text
publish = false
license = "PolyForm-Noncommercial-1.0.0"
repository = "https://github.com/Undermybelt/ict-engine-release"
```

The private mirror `Undermybelt/ict-engine-release` remains the release target.
The development repo is source/provenance only.
