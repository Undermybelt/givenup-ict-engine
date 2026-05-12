# HF Pump/Dump Schema Audit v1

Run ID: `20260511T183018+0800-codex-hf-pumpdump-schema-audit-v1`

This audit inspects `/tmp` downloads from `Go3x3/pump_and_dump_dataset` without committing raw rows into the repo.

## Decision

`hf_pumpdump_schema_audit_v1=blocked_no_labels_or_matched_negatives`

- ZIP files inspected: `2`.
- CSV files in data1/data2: `351` / `351`.
- Headers seen: `amount, btc_volume, datetime, price, side, symbol, timestamp`.
- Timestamp fields present: `true`.
- Trade fields present: `true`.
- Explicit label fields present: `false`.
- Matched-negative/control fields present: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full direct species coverage: `false`.
- `update_goal`: `false`.

## Why It Blocks

The rows look like trade/event-window data: `symbol`, `timestamp`, `datetime`, `side`, `price`, `amount`, and `btc_volume`. The schema does not expose explicit manipulation labels, event IDs, matched negative groups, or control windows. File names encode candidate event windows, but file names are not enough to run a chronological 95% direct `Manipulation` gate.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T183018-codex-hf-pumpdump-schema-audit-v1/hf-pumpdump-schema/hf_pumpdump_schema_audit_v1.json`
- Sample/header CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T183018-codex-hf-pumpdump-schema-audit-v1/hf-pumpdump-schema/hf_pumpdump_schema_audit_v1_samples.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T183018-codex-hf-pumpdump-schema-audit-v1/checks/hf_pumpdump_schema_audit_v1_assertions.out`

## Next

Keep this source as positive-window provenance only unless a separate manifest supplies labels and matched negative/control windows.
