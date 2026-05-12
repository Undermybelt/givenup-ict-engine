# R6 Split/Species Gap Impact v1

Run ID: `20260512T000714-codex-r6-split-species-gap-impact-v1`

## Result

- Base live snapshot: positives `73`, matched controls `73`.
- Live verifier status: `schema_ready_unscored`, return code `0`.
- All-success Wilson95 requires `73` rows per evaluated split bucket.
- Unaccepted unique sidecar positives: `20`; control-ready unaccepted positives: `4`; missing-control unaccepted positives: `16`.
- Non-spoofing sidecar species exist: `True`; non-spoofing sidecar species control-ready: `False`.
- Exact split gates remain false even in the all-sidecar what-if with missing controls represented as policy-required placeholders.
- Gate result: `r6_split_species_gap_impact_v1=remaining_sidecars_do_not_close_exact_split_gates_missing_controls_and_bulk_support_required`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; external requests sent: `false`; trade usable: `false`.

## Key Deficits

- Current chronological failing buckets: `3`; all-sidecar what-if failing buckets: `3`.
- Current exact-symbol failing buckets: `36`; all-sidecar what-if failing buckets: `47`.
- Current exact-venue failing buckets: `11`; all-sidecar what-if failing buckets: `11`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_v1.json`
- Candidate inventory: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_candidate_inventory_v1.csv`
- Source summary: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_source_summary_v1.csv`
- Current metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_current_metrics_v1.csv`
- Control-ready metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_control_ready_metrics_v1.csv`
- All-sidecar what-if metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/r6-split-species-gap-impact/r6_split_species_gap_impact_all_sidecar_what_if_metrics_v1.csv`
- Verifier stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`, `docs/experiments/actionable-regime-confidence/runs/20260512T000714-codex-r6-split-species-gap-impact-v1/command-output/direct_manipulation_row_intake_verifier.stderr.txt`

## Next

Do not mutate the 73x73 live intake with remaining sidecars alone. Either acquire a bulk owner-approved direct order-lifecycle export with split-balanced controls, or predeclare a less fragmented family-level validation protocol before rerunning R6 acceptance; continue R5 source-owner recency and R3 native-subhour acquisition separately.
