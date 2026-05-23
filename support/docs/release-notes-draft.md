# Release Notes

Version: `v0.1.6`
Draft date: 2026-05-23
Status: correction candidate for the private `ict-engine-release` mirror.

## Scope

`v0.1.6` corrects the CI failure exposed by the published `v0.1.5` mirror
release. The fix is intentionally narrow: the release privacy audit test fixture
no longer embeds a `support/docs/plans/*.md` literal that violates the mirror CI
docs-runtime-isolation rule.

The release remains a private source mirror release. It is not a crates.io,
npm/npx, Homebrew, Docker, binary, or public package-manager release.

## Changes since `v0.1.5`

- Moved the secret-like archived-doc fixture in
  `support/scripts/tests/test_release_privacy_audit.py` from
  `support/docs/plans/old.md` to `support/docs/audits/old.md`.
- Preserved the release privacy audit behavior: secret-like tokens still block
  release even when found in archived docs.
- Advanced Cargo metadata to `version = "0.1.6"` so the correction release uses
  a new mirror tag instead of rewriting `v0.1.5`.

## Verification already run for the fix slice

- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`.
- `python3 -m unittest support.scripts.tests.test_release_privacy_audit -v`
  - exit `0`; `8` tests passed.
- Clean export `/tmp/ict-engine-v015-ci-fix-export-20260523T120926+0800`:
  - docs runtime isolation: exit `0`.
  - privacy audit unit tests: exit `0`; `8` tests passed.
  - release privacy audit: exit `0`; `release_blocking_hits=0`.
  - cargo fmt: exit `0`.
  - cargo clippy: exit `0`.
  - cargo test: exit `0`.

## Release requirements

Publish `v0.1.6` only after a fresh clean export from the selected committed
`HEAD` passes the final gate set and readback confirms:

- mirror `main` advances on `Undermybelt/ict-engine-release`;
- tag `v0.1.6` exists and resolves to the published mirror commit;
- GitHub release `v0.1.6` exists;
- no package-manager publication is enabled.

## Release label

`ict-engine v0.1.6`
