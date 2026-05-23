# Release Notes

Version: `v0.1.5`
Draft date: 2026-05-23
Status: candidate notes refreshed for the selected `v0.1.5` export path;
mirror publication, tag creation, and GitHub release creation still require
fresh export gates plus explicit operator approval.

## Candidate scope

This candidate packages the current committed source tree after the release
version gate was advanced to `0.1.5`. The release-readiness audit now sees
`v0.1.5` as the selected unused tag while preserving the private mirror and
non-package-manager policy in Cargo metadata.

The release remains a consumer-facing source/mirror candidate. It is not a
crates.io, npm/npx, Homebrew, Docker, binary, or public package-manager release.

## Highlights

- Public Cargo metadata now selects `version = "0.1.5"`, avoiding reuse of
  release mirror tags already present through `v0.1.4`.
- `publish = false`, `license = "PolyForm-Noncommercial-1.0.0"`, and the
  release mirror repository URL remain in place.
- The active audit loop continues to preserve zero-config first-run and
  token-friendly workflow surfaces as release requirements, not assumptions.
- Factor claim/process hygiene is currently clear, but practical promotion and
  trade usability still have zero proven positives in the latest audit.

## Fresh evidence so far

- `cargo metadata --no-deps --format-version 1 > /tmp/ict_engine_metadata_version_015_precommit_20260523.json`
  - exit `0`.
- `cargo check --all-targets > /tmp/ict_engine_version_015_cargo_check_all_20260523.stdout 2> /tmp/ict_engine_version_015_cargo_check_all_20260523.stderr`
  - exit `0`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/factor_claim_terminalization_post_version_commit_20260523.json`
  - exit `0`; status `pass`.
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/done_definition_post_version_commit_20260523.json`
  - exit `0`; light status `pass`; heavy gates skipped.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/release_readiness_post_version_commit_20260523.json`
  - exit `1`; `release_version_tag_available=pass`; unresolved:
    `worktree_clean_for_release`, `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`.

## Required release gates

Before these notes can become release payload text, run the full gate set from a
fresh export of the selected committed `HEAD`:

```bash
RELEASE_EXPORT_DIR=$(mktemp -d /tmp/ict-engine-v015-release-export.XXXXXX)
git archive --format=tar HEAD | tar -x -C "$RELEASE_EXPORT_DIR"
cargo fmt --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --check
cargo clippy --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --all-targets -- -D warnings
cargo test --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml"
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- provider-status --compact
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-v015-first-run --human
cargo run --manifest-path "$RELEASE_EXPORT_DIR/Cargo.toml" --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-v015-first-run --refresh --agent
```

## Known limitations

- The development checkout is dirty with unrelated in-flight research and doc
  files; release payload selection must use a clean export, not the checkout.
- The selected source commit is ahead of `origin/main`; the release path must
  either push the selected source commit or publish from a clean export with
  explicit provenance.
- Practical factor promotion is not proven by the current audit snapshot:
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Heavy done-definition gates and clean-export zero-config smoke must still be
  rerun before release.
- Optional providers, external history, Auto-Quant material, TimesFM, and
  maintainer-local data remain hot-pluggable evidence only; none may become a
  default runtime dependency for consumers.

## Release label

`ict-engine v0.1.5`

Reason:
- current unused release tag selected;
- package-manager publication remains disabled;
- release docs now describe the selected candidate instead of an older tag;
- final publication remains gated by clean-export verification and operator
  approval.
