# R2/R3/R5 Public Route And Root Readback v1

- Decision: `r2_r3_r5_public_route_and_root_readback_v1=rows_not_acquired_blocked`.
- Board cursor before run: `20260511T212004+0800-codex-r6-shak-duplicate-row-cleanup-v1`.
- Ready intake roots: `1/4`.
- Exact required R2/R3/R5 file hits under bounded `/tmp` and `Downloads` search: `0`.
- Source-label equivalence verifier: `blocked`.
- Recency verifier: `blocked`.
- VantMacro public route: `public_route_still_found_no_board_required_row_export`; source-owned rows acquired `false`; intake files created `false`.
- Direct R6 coordination readback: positives `32`, matched negatives `32`; still not accepted.
- Completed concurrent run dirs sampled by this readback: `4`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Boundary

This run does not create source-label intake files because no source-owned or owner-approved R2/R3/R5 rows were acquired. The VantMacro page remains a public route/contact surface, not row-level Board A evidence.

## Checklist

| ID | Status | Gap |
|---|---|---|
| `R2_R4_source_label_equivalence` | `fail_blocked` | source_label_equivalence_rows.csv and source_label_equivalence_provenance.json absent |
| `R3_native_subhour` | `fail_blocked` | native_subhour_source_label_rows.csv and native_subhour_source_label_provenance.json absent |
| `R5_recency_extension` | `fail_blocked` | stock_market_regimes_2026_extension.csv and source_panel_recency_provenance.json absent |
| `R6_coordination` | `still_blocked` | R6 still lacks support, Wilson95 >=0.95, broad normal sample, and direct species coverage |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_v1.json`
- Root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_roots_v1.csv`
- Exact-hit CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_exact_hits_v1.csv`
- Sampled-run CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_post_cursor_v1.csv`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/r2-r3-r5-public-route-and-root-readback/r2_r3_r5_public_route_and_root_readback_checklist_v1.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1/command-output`
- Public route raw HTML: `/tmp/ict-engine-r2-r3-r5-public-route-readback-v1/vantmacro_home.html` (not committed)
