# Mainline execution trace consumer fields

Session: 2026-05-09 regime -> execution mainline implementation.

## Problem

`path_ranker` / CatBoost evidence was previously visible mostly as text lineage in `execution_tree_trace.json`. That is weak for consumers: downstream tools need stable machine fields, while human/agent/compact surfaces need a short reason summary.

## Implementation shape

Execution tree output should expose explicit additive fields:

- `path_ranker_score_used_by_execution_tree: bool`
- `path_ranker_model_family: Option<String>`
- `path_ranker_runtime_source: Option<String>`
- `ranker_validation_ready: bool`

Execution triage should expose:

- `reason_summary: Vec<String>` containing only compact selected lineage:
  - `market_state=...`
  - `path_ranker=...`
  - branch line
  - hybrid transition hazard line

Analyze runtime should inject a compact machine lineage line into `path_ranker_lineage` before calling the execution scorer:

```text
ranker_machine=source=<source> model_family=<family> validation_ready=<bool> active_match_count=<n>
```

The scorer can parse this line plus existing `Ranker runtime:` / `Ranker validation:` text to fill the machine fields. Keep default behavior safe when the line is missing: all booleans false and options `None`.

## TDD anchors

Use targeted lib tests first:

```bash
cargo test --lib path_ranker -- --nocapture
cargo test --lib triage_reason_summary -- --nocapture
```

Useful test names from the slice:

- `execution_tree_surfaces_path_ranker_machine_fields`
- `triage_reason_summary_includes_regime_and_ranker_context`

RED failures to expect before implementation:

- missing `ExecutionTreeOutput.path_ranker_*` fields
- missing `ExecutionTriage.reason_summary`

## Validation anchors

```bash
cargo check
cargo test --bin ict-engine test_market_state_summary_threads_primary_secondary_regime -- --nocapture
```

Runtime smoke in `/tmp/...` state:

```bash
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-root /tmp/ict-mainline-regime-audit \
  --state-dir /tmp/ict-mainline-regime-audit/state \
  --output-format json \
  --inline-ledger
```

Check:

- `supporting.execution_triage.reason_summary`
- `supporting.execution_artifact.output.path_ranker_score_used_by_execution_tree`
- `supporting.execution_artifact.output.path_ranker_runtime_source`
- `supporting.execution_artifact.output.path_ranker_model_family`
- `supporting.execution_artifact.output.ranker_validation_ready`

## Commit hygiene pitfall

A narrow `git add <files>` does not protect against files already staged before the current slice. Before any commit in dirty multi-agent repos, run:

```bash
git diff --cached --name-only
git status --short
```

If the commit accidentally includes unrelated pre-staged files, recover without losing work:

```bash
git reset --soft HEAD~1
git reset
git add <only-this-slice-files>
git commit -m "<message>"
```

Do not use `git reset --hard`; preserve unrelated worktree changes.
