# Public Case Attachment Route Refresh After 085131 v1

Run id: `20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1`

Gate result: `public_case_attachment_route_refresh_after_085131_v1=public_case_narrative_only_no_row_level_source_control_no_unlock`

## Scope

This source/control acquisition readback records a fresh public case-route probe after `085131`.
It uses official/public CFTC and court-route references to check whether public case attachments
can unlock the R6/R5/R3 source/control gate. It does not mutate target roots, send external
requests, approve same-exhibit `FLIP` controls, select historical data, run selected-data AutoQuant,
run verifier/split calibration, run filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree
promotion, make a trade claim, mark the objective complete, or call `update_goal`.

## Readback

- Board A SHA-256 before artifact: `9afc53556f3088d68f14f4cf128208a11ae6651f2dca914e83db5e78c477d9ef`.
- Board B SHA-256 before artifact: `3d58c1fe7432f36f6a34d5a32127335bf2f1eff0d33d63c6d69f1040f0c3d6e4`.
- Public official/court routes checked: `5`.
- Row-level positive rows acquired: `false`.
- Matched normal controls acquired: `false`.
- Ticket/export/license provenance present: `false`.
- R6 owner/export unlock: `false`.
- R5 recency unlock: `false`.
- R3 native-subhour present: `true`; unlock remains `false`.
- `085042` run root present at this filesystem readback: `true`.

## Route Disposition

The public CFTC and court materials confirm the relevant Oystacher spoofing/layering context,
product coverage, flip/cancel behavior, order-imbalance summaries, and the existence of expert
or complaint data categories. They still do not expose verifier-native row-level positives,
matched normal controls, or source-owned provenance manifests that can satisfy the R6/R5/R3
source/control gate.

## Decision

No public case attachment or official route acquired row-level source/control evidence.
Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false;
explicit user-selected history false; canonical merge false; selected-data AutoQuant promotion false;
downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed
false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/public-case-attachment-route-refresh-after-085131-v1/public_case_attachment_route_refresh_after_085131_v1.json`
- Route CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/public-case-attachment-route-refresh-after-085131-v1/public_case_attachment_routes_after_085131_v1.csv`
- Target-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/public-case-attachment-route-refresh-after-085131-v1/source_control_target_roots_after_085131_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/checks/public_case_attachment_route_refresh_after_085131_v1_assertions.out`

## Next

Continue source/control acquisition only. The live unblocker remains an owner-approved/authenticated
FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched
normal controls, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable
R3 native-subhour labels, or explicit same-exhibit `FLIP`-as-control approval before verifier,
split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking,
execution-tree promotion, trade claims, or `update_goal`.
