# R6 Split Species Gap Audit v1

- Run id: `20260512T000657-codex-r6-split-species-gap-audit-v1`.
- Live canonical verifier status: `schema_ready_unscored`.
- Live rows: positives `73`, matched controls `73`, matched groups `70`.
- Minimum all-success support needed for Wilson95 LCB >= 0.95: `73` rows per positive/control side.
- Chronological split gate: `false`; minimum pair deficits: train `35`, calibration `56`, test `55`.
- Heldout symbol gate: `false`; failing exact-symbol cells `36`.
- Heldout venue gate: `false`; failing exact-venue cells `11`.
- Direct species closed: `false`; missing species `quote_spoofing, quote_stuffing, pinging, bear_raid, painting_tape`.
- Latest full-chain readback reused: `docs/experiments/actionable-regime-confidence/runs/20260512T000048-codex-r6-isolated-reconstruction-verification-v57/r6-isolated-reconstruction-verification/r6_isolated_reconstruction_verification_v57.json`.
- Gate result: `r6_split_species_gap_audit_v1=pooled95_live_ready_split_species_targets_quantified_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000657-codex-r6-split-species-gap-audit-v1/r6-split-species-gap-audit/r6_split_species_gap_audit_v1.json`
- Split gaps CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000657-codex-r6-split-species-gap-audit-v1/r6-split-species-gap-audit/r6_split_species_gap_audit_v1_split_gaps.csv`
- Species gaps CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000657-codex-r6-split-species-gap-audit-v1/r6-split-species-gap-audit/r6_split_species_gap_audit_v1_species_gaps.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T000657-codex-r6-split-species-gap-audit-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`

## Next

Acquire source-owned direct rows that specifically fill chronological calibration/test, exact-symbol, exact-venue, and missing non-spoofing species cells; then rerun the unchanged direct verifier, split calibration, and provider/Auto-Quant/pre-Bayes/CatBoost/workflow readback.
