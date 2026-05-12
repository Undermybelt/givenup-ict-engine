# Release signoff

Date: 2026-05-12
Status: `v0.1.2` release mirror candidate prepared; publish is waiting on
explicit operator confirmation for tag/push/`gh release create`.

## Final verdict

Ready to publish to the `Undermybelt/ict-engine-release` mirror as `v0.1.2`
after explicit confirmation.

The committed clean export passes Rust fmt, Clippy, and full tests. The current
source checkout still has unrelated dirty docs/runtime artifacts, so the release
candidate must be exported from committed `HEAD`, not from broad worktree state.

## Important release routing decision

This checkout currently tracks:

```text
origin git@github.com:Undermybelt/givenup-ict-engine.git
```

Release metadata points at:

```text
Undermybelt/ict-engine-release
```

Use the release mirror flow. Do not reuse `v0.1.1`; the mirror already has that
tag. The next prepared tag is `v0.1.2`.

## Signoff checklist

### Build and test
- [x] clean export `cargo fmt --check`
- [x] clean export `cargo clippy --all-targets -- -D warnings`
- [x] clean export `cargo test`
- [ ] Python pytest suite: not rerun during this release-prep pass
- [x] release export uses committed `HEAD`
- [x] unrelated source worktree dirt excluded from release export

### CLI and consumer quality
- [x] `workflow-status` exposes opt-in profile choices without auto-adoption
- [x] agent output keeps selected profile state explicit
- [x] zero-config tests do not depend on maintainer-local `state/` files
- [x] BBN fixture files are tracked, small, and path-redacted
- [x] runtime BBN overlays remain hot-pluggable via user state

### Portability and state hygiene
- [x] `Cargo.toml` version prepared as `0.1.2`
- [x] `Cargo.lock` package version prepared as `0.1.2`
- [x] no tracked `state*` files are required by the clean export fixture fix
- [x] generated Auto-Quant dependency workspaces are not staged for release

## Commands executed for signoff

```bash
cargo fmt --check
cargo test bbn::trading -- --nocapture
cargo clippy --all-targets -- -D warnings
```

```bash
git archive HEAD | tar -x -C /tmp/ict-engine-release-export.ueDk6B
cargo fmt --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --check
cargo clippy --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml
```

## Decisive outcomes

### Source targeted gates
- `cargo fmt --check`: passed
- `cargo test bbn::trading -- --nocapture`: passed, 19 matching tests
- `cargo clippy --all-targets -- -D warnings`: passed

### Clean export gates
- `cargo fmt --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --check`: passed
- `cargo clippy --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml --all-targets -- -D warnings`: passed
- `cargo test --manifest-path /tmp/ict-engine-release-export.ueDk6B/Cargo.toml`: passed
  - lib tests: 927 passed
  - bin tests: 236 passed
  - integration tests: all listed suites passed
  - doc tests: 0 passed, 0 failed

## Release caveats

1. Branch is still far ahead of the source remote; this release uses the mirror
   flow to publish clean tree state without rewriting source history.
2. The current source checkout has unrelated dirty docs/runtime artifacts that
   were not staged into this release candidate.
3. Python pytest is outside the current Rust release gate.
4. The mirror already has `v0.1.1`; publish this candidate as `v0.1.2` only
   after explicit confirmation.

## Release recommendation

Proceed with `v0.1.2` on `Undermybelt/ict-engine-release` using the mirror
release flow after explicit operator confirmation.
