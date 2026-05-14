# R6 Oystacher Control Contract Request v1

- Run id: `20260512T003627-codex-r6-oystacher-control-contract-request-v1`.
- Policy review run: `20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1`.
- Purpose: make the V65 control blocker executable without accepting FLIP rows by default.
- Required validation cells: `17`.
- Gate result: `r6_oystacher_control_contract_request_v1=control_request_ready_no_controls_or_approval`.
- Accepted rows added: `0`; controls acquired: `false`; FLIP-as-control approved: `false`; `update_goal=false`.

## Options

1. Preferred: supply source-owned normal/non-manipulation controls matched to the Exhibit A SPOOF rows.
2. Exception: explicitly approve the same-exhibit FLIP-as-control contract using the template; this still requires the full verifier/split/provider/Auto-Quant/BBN/CatBoost/execution-tree rerun.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/r6_oystacher_control_contract_request_v1.json`
- Required normal-control cells: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/r6_oystacher_required_normal_control_cells_v1.csv`
- Control contract options: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/r6_oystacher_control_contract_options_v1.csv`
- Target control files: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/r6_oystacher_target_control_files_v1.csv`
- FLIP-control approval template: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/r6-oystacher-control-contract-request/flip_control_approval_template_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003627-codex-r6-oystacher-control-contract-request-v1/checks/r6_oystacher_control_contract_request_v1_assertions.out`
