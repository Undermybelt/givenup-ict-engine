# R6 Post-V68 Artifact Readback v1

- Run id: `20260512T004406-codex-r6-post-v68-artifact-readback-v1`.
- Gate result: `r6_post_v68_artifact_readback_v1=registered_artifacts_present_no_controls_no_merge`.
- Existing post-V68 artifact runs registered: `4`.
- Absent/unstable artifact paths excluded: `0`.
- Required Oystacher control cells: `17`.
- Cells with official owner route identified: `17`.
- Local candidate roots checked by the applicability audit: `13`.
- Required cells passing from any single local non-FLIP root: `0/17`.
- Best single-root valid non-FLIP control count for any required cell: `29`.
- Public sources checked by the latest probe: `5`; downloaded OK: `5`.
- Parsed Exhibit A rows: `6735`; `SPOOF=5182`; `FLIP=1553`.
- Valid source-owned normal controls found: `0`.
- Required-cell shortfall: `1241`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`.

## Used Evidence
- `20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1`: `r6_oystacher_owner_control_source_route_screen_v1=official_source_routes_identified_controls_not_acquired`; controls found `0`; assertions ok `true`.
- `20260512T004014-codex-r6-local-control-applicability-audit-v1`: `r6_local_control_applicability_audit_v1=local_candidate_controls_insufficient_no_approval_no_merge`; controls found `0`; assertions ok `true`.
- `20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1`: `r6_oystacher_public_normal_control_source_probe_v1=no_public_source_owned_normal_controls_found`; controls found `0`; assertions ok `true`.
- `20260512T004022-codex-r6-oystacher-source-owner-control-route-v1`: `r6_oystacher_source_owner_control_route_v1=routes_identified_controls_not_acquired_no_merge_or_chain_rerun`; controls found `0`; assertions ok `true`.

## Next
Acquire source-owned normal controls for all 17 Oystacher cells from the mapped CME/Cboe owner routes, or explicitly approve RECAP/PACER provenance plus the same-exhibit FLIP-as-control exception; only then merge under a shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004406-codex-r6-post-v68-artifact-readback-v1/r6-post-v68-artifact-readback/r6_post_v68_artifact_readback_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004406-codex-r6-post-v68-artifact-readback-v1/r6-post-v68-artifact-readback/r6_post_v68_artifact_readback_sources_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004406-codex-r6-post-v68-artifact-readback-v1/checks/r6_post_v68_artifact_readback_v1_assertions.out`
