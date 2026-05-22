# ICT Engine Contributor Quickstart

Use this path for small, reviewable changes. Preserve unrelated dirty work and
write generated state under `/tmp`.

## Before Editing

```bash
git status --short
cargo run --quiet -- provider-status --compact
```

Read the relevant entry contracts before changing behavior:

- `AGENT.md` for zero-config, privacy, and closed-loop rules.
- `support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` for the
  active full-audit remediation ledger.
- `support/docs/command-output-contract.md` before adding or changing CLI output.

## Where Code Belongs

- CLI argument declarations and thin dispatch: `src/main.rs`.
- Command behavior and report construction: `src/*_command.rs` or
  `src/application/**`.
- Workflow state, artifact, and training DTOs: existing typed modules under
  `src/application/**` and `src/state/**`.
- Python bridge code: `support/scripts/auto_quant_external/**` when it is part
  of the active external trainer contract.

Do not make runtime code parse `support/docs/plans/*.md`. Promote rules into
typed config, flags, schemas, fixtures, or tests.

## Smoke Gate

Run the zero-config consumer smoke before claiming a user-visible loop still
works:

```bash
support/scripts/smoke_acceptance.sh
```

The script writes output under `/tmp` by default and scans for private local
paths or secret-like strings.

## Focused Verification

For Rust behavior changes:

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test <focused_test_name> -- --nocapture
```

Before broad completion claims:

```bash
cargo test
git diff --check
```

For Python bridge changes, prefer stdlib `unittest` when `pytest` is not
installed:

```bash
python3 -m unittest support.scripts.auto_quant_external.tests.test_path_ranker_hotplug -v
```

## Output Rules

- Read-only status/export commands should support `--output-format` where
  practical, plus aliases for documented modes.
- Human output can be compact English field labels; explain those labels in the
  user's language outside the CLI.
- JSON and agent surfaces are contracts. Do not make automation parse prose.
- Demo and candidate surfaces are inspection/admission surfaces, not
  trade-readiness proof.

## Completion Bar

A change is not complete until the relevant command or test passed in the
current tree and the evidence is recorded in the active plan or handoff. Do not
stage broad dirty work, generated run trees, private profiles, provider caches,
or unrelated Board A/B artifacts.
