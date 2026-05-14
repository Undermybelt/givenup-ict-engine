# R6 Owner Export Arrival Poll After 070315 v1

Run id: `20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1`

Gate result: `r6_owner_export_arrival_poll_after_070315_v1=no_r6_r5_arrival_r3_tsie_only_no_downstream`

## Scope

Read-only arrival poll after the `070315` public exact source-route probe. This packet checks whether any required target root changed and whether local candidate files or dispatch drafts provide a new R6 owner/export unlock. It does not mutate R3/R5/R6 roots, approve TSIE, approve public same-exhibit controls, run direct verifier, run canonical merge, run downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Board SHA-256 before poll: `a43899d6603d94f6ff224f2bc84c04886084d0566036d2c099895a55cc78d4bf`.
- `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent, `0` files.
- `/tmp/ict-engine-source-panel-recency-extension`: absent, `0` files.
- `/tmp/ict-engine-native-subhour-source-label-intake`: present with `2` files.
- R3 TSIE row file line count: `5,032,904` including header, so `5,032,903` data rows.
- Local candidate scan found Tomac Databento/symbology files for ES, EUR, GC, NQ, and YM context, but no R6 owner/export normal-control packet and no R5 source-panel recency extension.
- Dispatch `.eml` readback still shows request drafts and delivery instructions only; no ticket/export/license/order/support response artifact arrived.

## Decision

No required source/control root unlocked. R6 owner/export remains absent; R5 recency remains absent; R3 remains present only as TSIE-derived/quarantined evidence. Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Target roots status: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/target_roots_status.tsv`
- R6 files readback: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/r6_target_root_files.txt`
- R5 files readback: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/r5_target_root_files.txt`
- R3 files/readback: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/r3_target_root_files.txt`, `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/r3_rows_wc_l.txt`
- Dispatch drafts readback: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/dispatch_draft_headers_readback.txt`
- Local candidate files: `docs/experiments/actionable-regime-confidence/runs/20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1/command-output/local_candidate_files.txt`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
