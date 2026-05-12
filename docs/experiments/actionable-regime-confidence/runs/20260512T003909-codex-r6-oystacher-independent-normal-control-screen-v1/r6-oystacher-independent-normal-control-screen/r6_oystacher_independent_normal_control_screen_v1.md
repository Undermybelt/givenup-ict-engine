# R6 Oystacher Independent Normal-Control Screen v1

- Run id: `20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1`.
- Source materialization root: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization`.
- Parsed order rows: `6735`; side counts: `{'SPOOF': 5182, 'FLIP': 1553}`.
- Positive SPOOF candidates: `5182`.
- Same-exhibit FLIP candidate controls: `1553`.
- Independent normal rows found in materialized Exhibit A: `0`.
- Public source probes sent: `4`.
- Gate result: `r6_oystacher_independent_normal_control_screen_v1=no_independent_owner_approved_normal_controls_found`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Result

The materialized Exhibit A rows contain only `SPOOF` and `FLIP` side labels. No independent source-owned normal/non-manipulation rows were found in the materialized row set. The existing `matched_negative_normal_activity_rows.csv` remains a same-exhibit `FLIP` candidate set and is still blocked without explicit control-policy approval.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1/r6-oystacher-independent-normal-control-screen/r6_oystacher_independent_normal_control_screen_v1.json`
- Public source probe CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1/r6-oystacher-independent-normal-control-screen/r6_oystacher_public_source_probe_v1.csv`
- Normal-control evidence CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1/r6-oystacher-independent-normal-control-screen/r6_oystacher_normal_control_evidence_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1/checks/r6_oystacher_independent_normal_control_screen_v1_assertions.out`

## Next

Source independent owner-approved normal controls for the Oystacher SPOOF positives, or get explicit board/user approval for same-exhibit FLIP rows as controls and public RECAP/PACER provenance; only after that merge through the shared lock and rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree chain.
