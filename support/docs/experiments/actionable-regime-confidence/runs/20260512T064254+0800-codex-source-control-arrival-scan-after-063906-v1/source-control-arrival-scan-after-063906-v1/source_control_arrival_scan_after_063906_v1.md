# Source Control Arrival Scan After 063906 v1

Run id: `20260512T064254+0800-codex-source-control-arrival-scan-after-063906-v1`

Gate result: `source_control_arrival_scan_after_063906_v1=no_new_accepted_source_control_unlock_no_downstream`

## Scope

Bounded read-only scan after `063906` for real source/control arrivals. This checked required `/tmp` roots, recent local filename candidates in Downloads/tmp/private tmp/repo experiment roots, and board text for approval/ticket/export/license/support evidence. It did not mutate target roots, approve TSIE, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Required Roots

| Root | Exists | Required files present | Missing files |
|---|---:|---:|---|
| `r6_owner_export` | `False` | `False` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |
| `r5_recency_extension` | `False` | `False` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `r3_native_subhour` | `True` | `True` | `` |

## TSIE Readback

- TSIE root present: `True`.
- TSIE mapped rows from provenance: `5032903`.
- TSIE labels from provenance: `Bear,Bull,Sideways`.
- Crisis present in TSIE labels: `False`.
- Accepted for promotion now: `False`.

## Candidate Scan

- Filename candidate count: `240`.
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064254+0800-codex-source-control-arrival-scan-after-063906-v1/source-control-arrival-scan-after-063906-v1/source_control_arrival_candidates_v1.csv`.
- Board approval hit tail CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064254+0800-codex-source-control-arrival-scan-after-063906-v1/source-control-arrival-scan-after-063906-v1/source_control_arrival_board_approval_hits_v1.csv`.

## Decision

No new accepted source/control unlock was found. R6 owner/export remains absent, R5 recency remains absent, and R3 remains present only as TSIE-quarantined/non-promoting evidence. Canonical merge and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion remain blocked.

## Next

Continue only after explicit source/control-policy approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
