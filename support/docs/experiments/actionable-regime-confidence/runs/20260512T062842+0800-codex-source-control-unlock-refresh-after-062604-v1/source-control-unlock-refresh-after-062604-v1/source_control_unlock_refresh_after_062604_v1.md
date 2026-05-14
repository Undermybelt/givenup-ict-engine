# Source/Control Unlock Refresh After 062604 v1

Run id: `20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1`

Gate result: `source_control_unlock_refresh_after_062604_v1=no_required_root_no_approval_no_downstream`

## Scope

Read-only refresh after the `062604` prompt-to-artifact audit. This checks whether any required R6/R3/R5 source-control root or explicit dispatch evidence has arrived. It does not send mail, approve controls, copy files into target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Required Roots

| Root ID | Root | Exists | All Required Present | Missing Files |
|---|---|---:|---:|---|
| `r6_owner_export` | `/tmp/ict-engine-board-a-r6-owner-export-v1` | `false` | `false` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |
| `r3_native_subhour` | `/tmp/ict-engine-native-subhour-source-label-intake` | `false` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `r5_recency_extension` | `/tmp/ict-engine-source-panel-recency-extension` | `false` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |

## Dispatch Drafts

| Owner | Draft Present | Status | SHA256 |
|---|---:|---|---|
| `CME Group` | `true` | `draft_not_sent` | `56319c5826e17480a1130fdd6accc0378a2e5e099f4d4d771532ab2ced6cbd0b` |
| `Cboe/CFE` | `true` | `draft_not_sent` | `411e6733aaaf0ade2097f49601086177f2c89f47089d5eb9b37b34a5fae1249d` |

## Decision

- Source-label equivalence root remains present with `248440` rows, but it is still non-target/non-promoting.
- Required root unlocked: `false`.
- Required root exists at all: `false`.
- Local candidate scan hits: `110`, with `0` inside required roots.
- External requests sent `false`; approval present `false`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only from explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or verifier-native R3 native-subhour `MainRegimeV2` rows before rerunning direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1/source-control-unlock-refresh-after-062604-v1/source_control_unlock_refresh_after_062604_v1.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1/source-control-unlock-refresh-after-062604-v1/source_control_unlock_required_roots_v1.csv`
- Dispatch drafts CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1/source-control-unlock-refresh-after-062604-v1/source_control_unlock_dispatch_drafts_v1.csv`
- Local candidates CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1/source-control-unlock-refresh-after-062604-v1/source_control_unlock_local_candidates_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1/checks/source_control_unlock_refresh_after_062604_v1_assertions.out`
