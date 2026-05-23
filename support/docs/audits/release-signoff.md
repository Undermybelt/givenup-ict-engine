# Release signoff

Date: 2026-05-23
Selected candidate: `v0.1.7`
Selected source commit: pending commit after the CI fixture fix and version bump.
Status: correction candidate after `v0.1.6` was found already present in the
release mirror. Publish only from a clean export after the gates below pass.

## Correction scope

`v0.1.5` was published to the private `ict-engine-release` mirror and exposed a
CI failure in the mirror workflow's docs runtime isolation gate. The failing
surface was a test fixture literal in
`support/scripts/tests/test_release_privacy_audit.py`:
`support/docs/plans/old.md`.

The fix keeps the privacy-audit test semantics while moving the fixture path to
`support/docs/audits/old.md`, so runtime/code surfaces no longer reference
`support/docs/plans/*.md`.

## Verified gates before this signoff refresh

- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`; `docs runtime isolation ok`.
- `python3 -m unittest support.scripts.tests.test_release_privacy_audit -v`
  - exit `0`; `8` tests passed.
- Fresh clean export: `/tmp/ict-engine-v015-ci-fix-export-20260523T120926+0800`.
- From that export:
  - `python3 support/scripts/ci/check_docs_runtime_isolation.py`
    - exit `0`.
  - `python3 -m unittest support.scripts.tests.test_release_privacy_audit -v`
    - exit `0`; `8` tests passed.
  - `python3 support/scripts/release_privacy_audit.py . --compact --output /tmp/release_privacy_audit_ci_fix_export_20260523.json`
    - exit `0`; `release_blocking_hits=0`.
  - `cargo fmt --manifest-path /tmp/ict-engine-v015-ci-fix-export-20260523T120926+0800/Cargo.toml --check`
    - exit `0`.
  - `cargo clippy --manifest-path /tmp/ict-engine-v015-ci-fix-export-20260523T120926+0800/Cargo.toml --all-targets -- -D warnings`
    - exit `0`.
  - `cargo test --manifest-path /tmp/ict-engine-v015-ci-fix-export-20260523T120926+0800/Cargo.toml`
    - exit `0`.

## Required final gates for `v0.1.7`

After this document and `Cargo.toml` are committed, create a fresh export of the
selected committed `HEAD` and run:

```bash
python3 support/scripts/ci/check_docs_runtime_isolation.py
python3 support/scripts/release_privacy_audit.py . --compact --output /tmp/release_privacy_audit_v017_export_20260523.json
python3 -m unittest support.scripts.tests.test_release_privacy_audit -v
cargo fmt --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --check
cargo clippy --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --all-targets -- -D warnings
cargo test --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml"
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- provider-status --compact
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-v017-first-run --human
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-v017-first-run --refresh --agent
```

## Release boundary

Package-manager publication remains disabled:

```text
publish = false
license = "PolyForm-Noncommercial-1.0.0"
repository = "https://github.com/Undermybelt/ict-engine-release"
```

The private mirror `Undermybelt/ict-engine-release` remains the release target.
The development repo is source/provenance only.
