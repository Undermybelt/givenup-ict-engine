# R6 Owner Export Schema Bridge v1

- Run id: `20260512T002941-codex-r6-owner-export-schema-bridge-v1`.
- V62 request fields: positive `14`, controls `4`, provenance `2`.
- Unchanged direct verifier required fields: `17`.
- Request/verifier filename mismatch: `true`.
- Schema bridge rows: `17`; gap rows: `12`; hard missing rows: `6`.
- Unchanged verifier adapter ready: `false`.
- Gate result: `r6_owner_export_schema_bridge_v1=adapter_not_ready_request_underspecified_for_unchanged_verifier`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Interpretation

The V62 request package is not yet sufficient for a safe copy/rename into the unchanged direct verifier. The filename mismatch is real, and the schema mismatch is also real: the unchanged verifier requires participant, side, order-count, quantity, source-section, and session-bucket fields that the V62 required export schema does not currently require.

No adapter should fabricate these fields. A future owner export must either provide verifier-native files and all verifier-native columns, or the V62 request package must be amended with explicit source-owned fields and an adapter policy before any verifier/calibration/downstream rerun.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T002941-codex-r6-owner-export-schema-bridge-v1/r6-owner-export-schema-bridge/r6_owner_export_schema_bridge_v1.json`
- Mapping CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002941-codex-r6-owner-export-schema-bridge-v1/r6-owner-export-schema-bridge/r6_owner_export_schema_bridge_mapping_v1.csv`
- Gap CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002941-codex-r6-owner-export-schema-bridge-v1/r6-owner-export-schema-bridge/r6_owner_export_schema_bridge_gaps_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002941-codex-r6-owner-export-schema-bridge-v1/checks/r6_owner_export_schema_bridge_v1_assertions.out`
