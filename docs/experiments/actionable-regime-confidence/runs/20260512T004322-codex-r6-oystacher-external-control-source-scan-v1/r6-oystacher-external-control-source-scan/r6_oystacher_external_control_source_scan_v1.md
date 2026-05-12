# R6 Oystacher External Control Source Scan v1

- Run id: `20260512T004322-codex-r6-oystacher-external-control-source-scan-v1`.
- Gate result: `r6_oystacher_external_control_source_scan_v1=external_routes_identified_no_verifier_ready_source_owned_normal_controls`.
- External sources checked: `4`.
- Raw market-data acquisition routes identified: `3`.
- Verifier-ready source-owned normal controls found: `0`.
- Required Oystacher normal-control cells still short: `17`.
- CME/Databento routes remain acquisition or licensing paths for raw order-book/depth data, not source-owned normal/non-manipulation labels under the current contract.
- Canonical merge allowed: `false`; downstream verifier/provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_control_source_scan_v1.json`
- Sources CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_control_sources_v1.csv`
- Fetch readback CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/r6-oystacher-external-control-source-scan/r6_oystacher_external_fetch_readback_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/checks/r6_oystacher_external_control_source_scan_v1_assertions.out`

Next:
- Keep the Oystacher rows isolated. Either obtain explicit approval for RECAP/PACER provenance plus FLIP-as-control, or acquire verifier-ready source-owned normal controls. Raw CME/Databento data needs explicit policy approval before it can be treated as normal controls.
