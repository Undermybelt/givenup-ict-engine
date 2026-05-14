# R6 Local Control Applicability Audit v1

- Run id: `20260512T004014-codex-r6-local-control-applicability-audit-v1`.
- Required-cell source: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv`.
- Candidate verifier-native roots checked: `13`.
- Unique control CSV sets observed: `7`.
- Required cells passing from any single local non-FLIP control root: `0/17`.
- Best single-root valid non-FLIP control count for any required cell: `29`.
- Owner approval present under `/tmp/ict-engine-board-a-r6-owner-export-v1`: `False`.
- Verifier-native owner package present under `/tmp/ict-engine-board-a-r6-owner-export-v1`: `False`.
- Gate result: `r6_local_control_applicability_audit_v1=local_candidate_controls_insufficient_no_approval_no_merge`.
- Accepted rows added: `0`; canonical merge allowed: `false`; downstream rerun allowed: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

The local verifier-native snapshots are not a valid substitute for the missing Oystacher normal controls. Existing non-Oystacher control rows are either duplicated historical seed/control snapshots or fail the required Oystacher exact-cell support threshold. The Oystacher Exhibit A `FLIP` rows are present in the isolated materialization, but remain rejected as normal controls unless the explicit exception is approved.

## Next

Preserve the active V66 next action: choose one approval option from the `003653` decision package, or supply source-owned normal controls for the `17` required cells from `003627`; only then copy verifier-native files under the shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004014-codex-r6-local-control-applicability-audit-v1/r6-local-control-applicability-audit/r6_local_control_applicability_audit_v1.json`
- Candidate roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004014-codex-r6-local-control-applicability-audit-v1/r6-local-control-applicability-audit/r6_local_candidate_control_roots_v1.csv`
- Cell applicability CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004014-codex-r6-local-control-applicability-audit-v1/r6-local-control-applicability-audit/r6_oystacher_local_control_cell_applicability_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004014-codex-r6-local-control-applicability-audit-v1/checks/r6_local_control_applicability_audit_v1_assertions.out`
