# Release signoff

Date: 2026-06-01
Selected candidate: `v0.1.9`
Selected source commit: pending clean selected-source export
Status: retargeted candidate for the private `ict-engine-release` mirror;
publishing remains blocked until a clean selected source/export and remote
readback pass.

## Correction scope

`v0.1.5` was published to the private `ict-engine-release` mirror and exposed a
CI failure in the mirror workflow's docs runtime isolation gate. `v0.1.6`
corrected that immediate failure without rewriting the failed tag.

`v0.1.9` is the next selected candidate because `v0.1.8` is already present in
the private release mirror and must not be rewritten or reused. It preserves the
privacy/docs runtime isolation correction, includes subsequent audit hardening,
adds the release-clone Auto-Quant bootstrap guard, and keeps package-manager
publication disabled.

## Required gates before publication

- Create a clean selected-source export from the chosen source commit.
- `python3 support/scripts/release_readiness_audit.py --check-remotes --compact`
  - must exit `0` after the selected source/export is clean and the private
    release mirror readback is aligned for the selected release slice.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - must exit `0`; `docs runtime isolation ok`.
- `python3 support/scripts/release_privacy_audit.py . --compact`
  - must exit `0`; `release_blocking_hits=0`.
- `python3 -m unittest support.scripts.tests.test_help_audit support.scripts.tests.test_done_definition_audit -v`
  - must exit `0`.
- `cargo fmt --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --check`
  - must exit `0`.
- `cargo clippy --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --locked --all-targets -- -D warnings`
  - must exit `0`.
- `cargo test --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --locked`
  - must exit `0`.
- Zero-config smoke:
  - `provider-status --compact`: must exit `0`.
  - `analyze --symbol DEMO --demo --human`: must exit `0`.
  - `workflow-status --symbol DEMO --refresh --agent`: must exit `0`.

## Required final readback

Before publishing, confirm:

```bash
git ls-remote https://github.com/Undermybelt/ict-engine-release.git refs/heads/main refs/tags/v0.1.9
```

After publishing, confirm mirror `main`, tag `v0.1.9`, the GitHub Release page,
and the GitHub Actions run conclusion.

## Release boundary

Package-manager publication remains disabled:

```text
publish = false
license = "PolyForm-Noncommercial-1.0.0"
repository = "https://github.com/Undermybelt/ict-engine-release"
```

The private mirror `Undermybelt/ict-engine-release` remains the release target.
The development repo is source/provenance only; do not use the configured
`givenup-ict-engine` origin as the push target for this release-clone guard.
