# Board Reference Integrity After 012425 Restoration v1

Run id: `20260512T013119-codex-board-reference-integrity-after-012425-restoration-v1`
Gate result: `board_reference_integrity_after_012425_restoration_v1=artifacts_restored_new_roots_reviewed_r6_r3_r5_roots_missing_no_promotion`

Reference readback:
- `20260512T012425-codex-source-label-qualifying-condition-failclosed-v1`: board refs `23`, files `8/8`, status `complete`.
- `20260512T012616-codex-current-objective-completion-audit-after-012318-v1`: board refs `17`, files `7/7`, status `complete`.
- `20260512T012658-codex-current-objective-completion-audit-after-012425-v1`: board refs `13`, files `5/5`, status `complete`.
- `20260512T012926-codex-board-reference-integrity-after-012616-v1`: board refs `0`, files `0/6`, status `missing_files`.
- `20260512T013042-codex-source-label-cross-timeframe-public-source-screen-v1`: board refs `7`, files `6/6`, status `complete`.
- `20260512T013106-codex-012425-artifact-restoration-readback-v1`: board refs `0`, files `8/8`, status `complete`.
- `20260512T013127-codex-012425-restoration-readback-v1`: board refs `0`, files `7/7`, status `complete`.

Stale-reference readback:
- `012616` artifact-presence CSV still records the `012425` JSON as present `False`.
- Prior `012926` gate result remains `missing_json` and is superseded by this refresh.

Tmp root readback:
- `r6_owner_export`: present `false` at `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- `r3_native_subhour`: present `false` at `/tmp/ict-engine-native-subhour-source-label-intake`.
- `r5_recency_extension`: present `false` at `/tmp/ict-engine-source-panel-recency-extension`.
- `source_label_equivalence`: present `true` at `/tmp/ict-engine-source-label-equivalence-intake`.

Result:
- The restored `012425` packet is now complete as fail-closed evidence, not acceptance evidence.
- The newer `013042`, `013106`, and `013127` roots are present and complete; they add fail-closed screening/restoration evidence only.
- The stale missing-artifact statements in earlier `012616` / `012658` / `012926` readbacks are superseded by this refresh.
- R6 owner controls, R3 native sub-hour rows, and R5 recency extension rows are still absent.
- No confidence gate, canonical merge, downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun, or goal completion is authorized.

