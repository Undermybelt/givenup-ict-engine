# Release signoff

Date: 2026-05-23
Selected candidate: `v0.1.5`
Selected source commit: the committed `HEAD` chosen for the clean export at
release-gate time.
Status: candidate documentation refreshed; release publication still requires a
clean sanitized export, source/export parity readback, full export gates, and
explicit operator approval.

## Current gate readback

Fresh release-readiness evidence after the local version slice:

- `cargo metadata --no-deps --format-version 1 > /tmp/ict_engine_metadata_version_015_precommit_20260523.json`
  - exit `0`.
- `cargo check --all-targets > /tmp/ict_engine_version_015_cargo_check_all_20260523.stdout 2> /tmp/ict_engine_version_015_cargo_check_all_20260523.stderr`
  - exit `0`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/release_readiness_post_version_commit_20260523.json`
  - exit `1`.
  - passing gates: `cargo_release_policy`, `release_version_tag_available`.
  - remaining gates: `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`.
  - version `0.1.5`; candidate tag `v0.1.5`; release mirror tags observed
    through `v0.1.4`, so the selected tag is unused in that readback.

## Release boundary

The selected candidate must be published only from an explicit sanitized export
of the selected committed tree. The broad development checkout contains other
lanes' modified and untracked files and is not itself the release payload.

Package-manager publication remains disabled by Cargo metadata:

```text
publish = false
license = "PolyForm-Noncommercial-1.0.0"
repository = "https://github.com/Undermybelt/ict-engine-release"
```

## Required export gates

Run these from a fresh `git archive` export of the selected committed `HEAD`
before any mirror/tag/GitHub release action:

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

After those pass, scan captured smoke output and the export tree for private
paths, API keys, tokens, maintainer-only datasets, generated dependency
workspaces, and repo-local experiment state.

## Current checklist

- [x] Candidate version advanced to `0.1.5`.
- [x] Candidate tag `v0.1.5` was unused in the release mirror readback.
- [x] Cargo policy still blocks package-manager publication.
- [x] Working-tree cargo check passed for the version metadata slice.
- [ ] A clean sanitized export has been created from the selected commit.
- [ ] Full fmt, Clippy, test, zero-config smoke, and privacy gates passed from
  that export.
- [ ] Source origin or selected export provenance is aligned with the release
  publication path.
- [ ] Operator has explicitly approved mirror push, tag push, and GitHub release
  creation for `v0.1.5`.

## Verdict

This document is a current `v0.1.5` candidate signoff surface, not publish
authorization. It clears the stale-documentation blocker only after the release
readiness audit confirms the paired release notes are also current. Publication
remains blocked until the checklist above is completed with fresh evidence.
