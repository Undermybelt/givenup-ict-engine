# Direct Control Pairing Feasibility Audit v1

Run ID: `20260511T184702+0800-codex-direct-control-pairing-feasibility-audit-v1`

This audit checks whether the positive-only Go3x3 pump/dump trade windows can be paired with Adam's control-only crypto L2/LOB data to create matched negative controls without generating proxy labels.

## Decision

`direct_control_pairing_feasibility_audit_v1=no_symbol_time_event_matched_controls`

- Go3x3 rows reported: `6946722` across `124` symbols.
- Go3x3 positive timestamp range: `1622474463035` to `1663777464790` epoch-ms.
- Adam control samples checked: `ADA_1m_ohlcv.csv, ADA_1m_depth30.csv, AVAX_1m_ohlcv.csv`.
- Adam control date ranges: `{'ADA_1m_ohlcv.csv': {'timestamp_min': '2025-03-12 00:00:00', 'timestamp_max': '2025-03-19 00:00:00'}, 'ADA_1m_depth30.csv': {'timestamp_min': '2025-03-12 00:00:00', 'timestamp_max': '2025-03-19 00:00:00'}, 'AVAX_1m_ohlcv.csv': {'timestamp_min': '2025-03-12 00:00:00', 'timestamp_max': '2025-03-19 00:00:00'}}`.
- Asset-name overlap in sampled controls: `['AVAX']`.
- Temporal overlap: `false`.
- Shared event id / matched-negative group id: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Full direct species coverage: `false`; full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Why It Blocks

AVAX overlaps as an asset name, but Adam control rows are 2025-03-12..2025-03-19 while Go3x3 positive windows are 2021-05..2022-09; both sources lack shared event ids and matched-negative group ids.

A separate control-only L2 panel cannot be used as a matched negative set unless it overlaps the positive source by symbol, time window, event policy, and provenance. This pairing currently fails time overlap and lacks shared event/control identifiers.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T184702-codex-direct-control-pairing-feasibility-audit-v1/direct-control-pairing/direct_control_pairing_feasibility_audit_v1.json`
- Pairing rows CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T184702-codex-direct-control-pairing-feasibility-audit-v1/direct-control-pairing/direct_control_pairing_feasibility_audit_v1_rows.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T184702-codex-direct-control-pairing-feasibility-audit-v1/checks/direct_control_pairing_feasibility_audit_v1_assertions.out`
