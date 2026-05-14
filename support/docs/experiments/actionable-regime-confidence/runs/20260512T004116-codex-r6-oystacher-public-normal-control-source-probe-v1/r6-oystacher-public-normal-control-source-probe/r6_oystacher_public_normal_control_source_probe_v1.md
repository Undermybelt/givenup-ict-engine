# R6 Oystacher Public Normal-Control Source Probe v1

Run id: `20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1`.

## Result

- Sources checked: `5`; downloaded OK: `5`.
- Raw downloads kept in `/tmp`: `/tmp/ict-engine-r6-oystacher-public-normal-control-source-probe-v1`.
- Parsed Exhibit A rows: `6735`.
- Exhibit A side labels: `{'SPOOF': 5182, 'FLIP': 1553}`.
- Valid public source-owned normal-control rows found: `0`.
- Required control cells: `17`; cells with valid controls: `0`; total shortfall: `1241`.
- Gate result: `r6_oystacher_public_normal_control_source_probe_v1=no_public_source_owned_normal_controls_found`.

## Interpretation

The public row-level source still contains only `SPOOF` positives and same-exhibit `FLIP` rows. `FLIP` rows remain useful as candidate context, but this probe found no independent public source-owned normal/non-manipulation control rows for the required cells.

No canonical intake was mutated and no provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun was allowed.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_source_probe_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_sources_checked_v1.csv`
- Required cells CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_required_cells_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/checks/r6_oystacher_public_normal_control_source_probe_v1_assertions.out`

## Next

Supply source-owned normal controls for the 17 Oystacher cells or explicitly approve the same-exhibit FLIP-as-control exception before canonical merge and downstream rerun.
