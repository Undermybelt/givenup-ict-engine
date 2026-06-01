# Regime consumer bundle -> BBN soft evidence opt-in

Use when continuing `regime consumer bundle` mainline work or auditing whether regime sidecar data changes BBN/runtime behavior.

## Learned contract

- Default behavior must stay read-only diagnostics: loading a regime consumer bundle must not change BBN inference unless the user passes an explicit apply flag.
- Runtime apply path is opt-in with `--apply-regime-bundle-bbn-soft-evidence`.
- Bundle use remains hot-plugged by `--regime-consumer-bundle`; no repo/global config required.
- Consumer-facing fields should stay token-friendly: short stable machine fields plus one concise human reason, not verbose dumps.
- For this user, preserve personal/aux fields such as VRP/NQ context when available, but design them as optional extension data so other users can decline or omit them.

## Implementation shape that worked

Prefer a narrow adapter over duplicating logic in `analyze` and `analyze-live`:

- `append_read_only_bbn_diagnostics(...)`
  - emits diagnostics/evidence previews
  - does not mutate Pre-Bayes/BBN inputs
- `apply_bbn_soft_evidence_to_pre_bayes_filter(...)`
  - explicit opt-in path
  - maps bundle decisions into Pre-Bayes soft evidence
  - keeps provenance traceable

The useful mapping from this session:

- `accepted + RangeConsolidation/WideRange` -> moderate `range` soft evidence.

## Verification pattern

Use isolated state under `/tmp`, never repo `state/`, for smoke runs:

```bash
cargo test --test regime_consumer_bundle_adapter -- --nocapture
cargo check
cargo build --bin ict-engine
```

Then run two CLI smokes against the same fixture/state:

1. read-only path without `--apply-regime-bundle-bbn-soft-evidence`
2. applied path with `--apply-regime-bundle-bbn-soft-evidence`

Assert the decisive difference, not whole JSON snapshots. Example expected shape:

```text
readonly=moderate applied=range
```

## Commit / dirty worktree discipline

- Start with `git status --short`.
- Commit only the slice's touched files.
- Ignore unrelated dirty files from other agents/users.
- If a file touched by this slice also has unrelated edits, inspect carefully and stage only intended hunks/non-interactively.
- Update a fresh handoff TODO under `docs/plans/` during the slice; include commit hash, validation commands, smoke artifacts, and remaining unrelated dirty work.

## Pitfalls

- Do not make bundle presence implicitly alter BBN. This violates zero-config and hot-plug expectations.
- Do not duplicate analyze/analyze-live logic; factor into an adapter/helper and call from both.
- Do not snapshot huge CLI JSON in reports; surface the one or two decisive fields.
- Do not run broad repo formatting. Format only touched Rust files unless user explicitly approves full `cargo fmt`.
