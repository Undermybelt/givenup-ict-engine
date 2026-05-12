# Release Notes Draft

Version: `v0.1.2` candidate
Status: release mirror candidate, refreshed 2026-05-12

## Highlights

- `workflow-status` now surfaces matching opt-in provider/profile choices for
  the requested symbol without selecting or loading maintainer-local material.
- Agent and human workflow surfaces stay token-friendly: optional profile
  references are compact, and selected profile state remains explicit.
- Branch-admission routing no longer overrides first-run, Auto-Quant handoff,
  evidence-review, selected-profile, or generic execution-contract guidance
  unless the latest feedback is for the exact same structural path.
- Structural path-plan artifacts carry candidate set ids and candidate paths,
  and path-ranking target rows expose branch segment categorical fields for
  external ranker training.
- BBN CPT and logic-family tests now use tracked, path-redacted fixtures under
  `tests/fixtures/policy_training/`; runtime overlays remain hot-pluggable via
  user state and are not adopted as zero-config defaults.
- Clean release export gates are green from committed `HEAD`:
  - `cargo fmt --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --check`
  - `cargo clippy --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --all-targets -- -D warnings`
  - `cargo test --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml`

## Smoke results from 2026-05-12

```bash
cargo fmt --check
cargo test bbn::trading -- --nocapture
cargo clippy --all-targets -- -D warnings
```

All passed in the source checkout after the fixture repair.

```bash
git archive HEAD | tar -x -C /tmp/ict-engine-release-export.ueDk6B
cargo fmt --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --check
cargo clippy --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml
```

All passed from the committed `v0.1.2` clean export. The full clean-export Rust suite
reported:
- lib tests: 927 passed
- bin tests: 236 passed
- integration tests: passed
- doc tests: 0 passed, 0 failed

## Known limitations

- This remains an agent-first / researcher-preview release, not a fully
  generalized packaged distribution.
- Python pytest was not rerun during the `v0.1.2` release-prep pass.
- Auto-Quant remains optional and should keep dependency workspaces under the
  selected state directory or explicit Auto-Quant output directory.
- Local long-history data can be used for maintainer training and hardening,
  but consumer-facing promotion still requires a portable provider recipe,
  built-in factor path, or explicit hot-plug material bundle.
- The source checkout has unrelated dirty docs/runtime artifacts; this release
  candidate is based on the committed clean export, not a broad worktree sync.
- `v0.1.1` already exists in the release mirror; publish this candidate as
  `v0.1.2` only after explicit operator confirmation.

## Release label

`ict-engine v0.1.2`

Reason:
- consumer-safe hot-plug profile-choice UX is committed
- local personal-data assumptions remain opt-in, not zero-config defaults
- clean export no longer depends on ignored `state/policy_training` fixtures
- clean export Rust fmt, Clippy, and full test gates are green
