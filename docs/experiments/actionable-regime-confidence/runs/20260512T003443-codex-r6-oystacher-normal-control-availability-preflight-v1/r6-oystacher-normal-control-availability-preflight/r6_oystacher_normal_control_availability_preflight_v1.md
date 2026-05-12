# R6 Oystacher Normal-Control Availability Preflight v1

- Run id: `20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1`.
- Gate result: `r6_oystacher_normal_control_availability_preflight_v1=no_source_owned_normal_controls_found_no_merge_or_chain_rerun`.
- Positive SPOOF rows preserved in isolated evidence: `5182`.
- Same-exhibit FLIP rows remain control candidates only: `1553`.
- Source-policy approval present in target root: `false`.
- Target owner-export root exists: `false`.
- Independent local normal-control candidates found: `0`.
- Provider readback: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant readback status in isolated state: `missing_dependency`.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`, because source-policy approval or independent normal controls are still absent.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

- Keep Oystacher Exhibit A rows isolated.
- The public RECAP/PACER source can stay as positive-candidate evidence, but canonical merge remains blocked.
- Same-exhibit `FLIP` rows were not promoted to `matched_negative_normal_activity`; no independent source-owned normal controls were found locally.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/r6-oystacher-normal-control-availability-preflight/r6_oystacher_normal_control_availability_preflight_v1.json`
- Local candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/r6-oystacher-normal-control-availability-preflight/r6_oystacher_normal_control_local_candidates_v1.csv`
- Root presence CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/r6-oystacher-normal-control-availability-preflight/r6_oystacher_normal_control_roots_v1.csv`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1/checks/r6_oystacher_normal_control_availability_preflight_v1_assertions.out`

## Next

Keep Oystacher rows isolated. Obtain explicit approval for the RECAP/PACER source policy and same-exhibit FLIP control contract, or supply independent source-owned normal controls; only then merge under a shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
