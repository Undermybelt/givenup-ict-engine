# Contributing To ICT Engine

ICT Engine is a market-structure research workbench. Contributions should make
the clean-checkout experience clearer, more verifiable, or safer without baking
in maintainer-local paths, private data, provider credentials, or generated
workspace state.

## Start Here

```bash
git status --short
cargo run --quiet -- provider-status --compact
support/scripts/smoke_acceptance.sh
```

Use `/tmp/...` state directories for trials. Do not write generated state into
the repo unless a test fixture explicitly requires it.

## Read Before Editing

- `AGENT.md`: zero-config, privacy, and closed-loop operating contract.
- `support/docs/contributor-quickstart.md`: where code belongs and how to verify.
- `support/docs/main-rs-guardrails.md`: placement rules before adding
  entrypoint code.
- `support/docs/command-output-contract.md`: CLI output-mode expectations.
- `support/scripts/SCRIPTS.md`: script stability and usage classification.
- `support/docs/release-mirror-runbook.md`: release transport rules; do not
  publish from a dirty development checkout.
- Active handoff or plan documents named by the task.

## Change Discipline

- Keep changes small and coherent.
- Preserve unrelated dirty work. Do not revert, stage, move, or delete files you
  did not intentionally touch for the current slice.
- Do not use broad staging commands such as `git add .`.
- Keep runtime code independent of markdown plan files. Promote rules into typed
  config, flags, schemas, fixtures, or tests before code consumes them.
- Public surfaces must remain consumer-usable without private profiles.
- `src/main.rs` is for CLI arguments and thin dispatch. Put command behavior,
  output builders, workflow/report DTOs, and orchestration helpers in existing
  library modules unless `support/docs/main-rs-guardrails.md` explicitly allows
  the entrypoint change.

## Verification

For doc-only changes:

```bash
git diff --check
```

For shell scripts:

```bash
bash -n support/scripts/<script>.sh
```

For Rust code:

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test <focused_test_name> -- --nocapture
```

Before a broad readiness or release claim:

```bash
cargo test
support/scripts/smoke_acceptance.sh
git diff --check
```

## Output And Evidence

- Prefer structured output for agents and compact human output for operators.
- Do not make automation parse prose display strings.
- Record exact commands and evidence paths in the active plan or handoff.
- Treat demo runs, candidate packs, and ranker targets as inspection/admission
  surfaces until runtime gates explicitly promote them.

## Release Boundaries

Do not tag, push a release mirror, or claim release readiness without an explicit
operator instruction and fresh clean-export evidence. Release evidence must prove
zero-config first run, privacy scan, tests, lint, formatting, and smoke behavior
from the release slice.

The development checkout is the source of truth for active research work. The
release mirror is only a sanitized transport surface for an approved release
slice; do not send generated run trees, provider caches, private profiles, or
unreviewed local artifacts to that mirror.
