# Mainline consumer reason field

Use when closing the final consumer-facing gap in `regime -> execution tree -> recommendation`.

## Goal

Expose one compact field that downstream consumers can read without parsing long trace text:

```text
market_state=<primary>/<secondary> | execution=<gate>/<branch>/<bias> | ranker=<source>/<model>/<ready|not_ready>
```

Example:

```text
market_state=TrendExpansion/BullTrendExhaustion | execution=ready/fill_viable/aggressive | ranker=registered_artifact/catboost/ready
```

## Proven implementation shape

Primary home:
- `src/application/orchestration/execution_tree.rs`

Add / maintain:
- `ExecutionTriage.consumer_reason: String`
- `ExecutionTreeOutput.consumer_reason: String` so `execution_tree_trace.json.output.consumer_reason` exists
- `refresh_consumer_reason(output)` and call it after any mutation of execution output, especially after `apply_regime_execution_guardrail(...)`
- Built by `build_execution_triage(&ExecutionTreeOutput)`; if `ExecutionTreeOutput.consumer_reason` is present, triage should reuse it rather than recompute a stale variant
- Derive market state from `split_reason_lineage` entries containing:
  - `market_state=primary_regime=... secondary_regime=...`
- Derive execution from direct output fields:
  - `gate_status`
  - `branch`
  - `execution_bias`
- Derive ranker from direct output fields:
  - `path_ranker_runtime_source`
  - `path_ranker_model_family`
  - `ranker_validation_ready`

Reporting homes:
- `src/application/reporting/analyze_output.rs`
- Ensure both normal `analyze` and `analyze-live` reporting paths copy `report.supporting.execution_triage` into:
  - `compact_report.execution_triage`
  - `agent_report.execution_triage`
  - `human_report` first line, preferably `consumer_reason` rather than verbose `one_line`

## TDD anchors

Add or preserve a test like:

```rust
triage_consumer_reason_merges_market_execution_and_ranker
```

Expected value:

```text
market_state=TrendExpansion/BullTrendExhaustion | execution=ready/fill_viable/aggressive | ranker=registered_artifact/catboost/ready
```

Run:

```bash
cargo test --lib triage_consumer_reason_merges_market_execution_and_ranker -- --nocapture
cargo test --lib path_ranker -- --nocapture
cargo test --lib triage_reason_summary -- --nocapture
cargo check
```

## Runtime proof checklist

After unit tests, prove the field is consumed by real outputs with an isolated audit state:

```bash
cargo build --bin ict-engine
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-root /tmp/ict-mainline-regime-audit \
  --state-dir /tmp/ict-mainline-regime-audit/state \
  --output-format json \
  --inline-ledger \
  > /tmp/ict-mainline-regime-audit/analyze-consumer-reason.json
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-root /tmp/ict-mainline-regime-audit \
  --state-dir /tmp/ict-mainline-regime-audit/state \
  --human \
  > /tmp/ict-mainline-regime-audit/analyze-consumer-reason-human.txt
```

Check all four consumers:

```text
report.supporting.execution_triage.consumer_reason
compact_report.execution_triage.consumer_reason
agent_report.execution_triage.consumer_reason
state/NQ/execution_tree_trace.json.output.consumer_reason
```

Expected live shape:

```text
market_state=RangeConsolidation/WideRange | execution=observe/transition_guardrail/guarded | ranker=candidate_set/catboost/not_ready
```

Human output should expose this as one readable line and remain short; a 10-line report is acceptable.

## Pitfalls

- `cargo test --bin ict-engine <lib-test-name>` may compile and report `0 tests`; use `cargo test --lib <filter>` for library module tests.
- Existing line parser using `strip_prefix("primary_regime=")` misses values embedded in `market_state=primary_regime=...`; use substring search for `key=` within whitespace-delimited parts.
- Normal `analyze` and `analyze-live` can have separate reporting bundle paths. Patch both; otherwise JSON live may pass while normal analyze misses compact/agent/human fields.
- If `ExecutionTreeOutput` is changed after scoring by guardrails, recompute `consumer_reason` after the guardrail; otherwise trace and triage can disagree.
- Keep this field short. Long trace remains in `reason_summary` / `split_reason_lineage`; `consumer_reason` is for consumers and token budgets.
- Stage only touched files; repo often has unrelated dirty files from parallel agents.
