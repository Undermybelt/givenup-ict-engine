# Required Intake Disk Sweep v1

- Decision: `required_intake_disk_sweep_v1=no_required_intake_files_found_verifiers_blocked`
- Required filename hits: `0`
- Source-label verifier returncode: `2`
- Recency-extension verifier returncode: `2`
- Direct-manipulation verifier returncode: `2`
- Native sub-hour package ready: `false`
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Scope

Searched bounded local roots for the exact intake filenames required by the Board A fail-closed gates. This does not promote proxy data or create intake rows.

## Intake Roots

| Package | Ready | Missing Files |
|---|---:|---|
| `source_label_equivalence` | `false` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `native_subhour_source_label` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `source_panel_recency_extension` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `direct_manipulation_row_intake` | `false` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |

## Decision

No required source-owned or owner-approved intake files were found in the bounded local search, and all existing fail-closed verifiers remain blocked. The strict objective remains incomplete.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T203437-codex-required-intake-disk-sweep-v1/required-intake-disk-sweep/required_intake_disk_sweep_v1.json`
- Hits CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T203437-codex-required-intake-disk-sweep-v1/required-intake-disk-sweep/required_intake_disk_sweep_v1_hits.csv`
- Intake roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T203437-codex-required-intake-disk-sweep-v1/required-intake-disk-sweep/required_intake_disk_sweep_v1_intake_roots.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T203437-codex-required-intake-disk-sweep-v1/checks/required_intake_disk_sweep_v1_assertions.out`
