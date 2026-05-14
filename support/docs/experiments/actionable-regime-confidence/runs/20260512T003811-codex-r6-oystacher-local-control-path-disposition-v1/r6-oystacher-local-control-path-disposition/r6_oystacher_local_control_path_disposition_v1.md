# R6 Oystacher Local Control Path Disposition v1

- Run id: `20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1`.
- Gate result: `r6_oystacher_local_control_path_disposition_v1=no_local_path_satisfies_source_owned_normal_control_contract`.
- Local paths checked: `6`; existing paths checked: `6`.
- Fincept CME path is aggregate public market data only: settlements, volume, open interest, delayed quotes, product/calendar metadata.
- Nautilus/Databento paths are sample/test data or bars/trades from modern ES/other contracts, not Oystacher 2011-2014 multi-symbol source-owned normal controls.
- Valid source-owned normal controls found: `0`.
- Required Oystacher normal-control cells still short: `17`.
- Canonical merge allowed: `false`; downstream verifier/provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1/r6-oystacher-local-control-path-disposition/r6_oystacher_local_control_path_disposition_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1/r6-oystacher-local-control-path-disposition/r6_oystacher_local_control_path_candidates_v1.csv`
- Required cells CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1/r6-oystacher-local-control-path-disposition/r6_oystacher_local_control_required_cells_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1/checks/r6_oystacher_local_control_path_disposition_v1_assertions.out`

Next:
- Keep the Oystacher rows isolated. Either obtain explicit approval for RECAP/PACER provenance plus FLIP-as-control, or supply independent source-owned normal controls for all required cells before canonical merge and full-chain rerun.
