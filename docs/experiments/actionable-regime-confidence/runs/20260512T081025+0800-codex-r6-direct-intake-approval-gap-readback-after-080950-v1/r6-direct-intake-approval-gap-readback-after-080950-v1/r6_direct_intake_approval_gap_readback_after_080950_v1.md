# R6 Direct Intake Approval Gap Readback After 080950 v1

Run id: `20260512T081025+0800-codex-r6-direct-intake-approval-gap-readback-after-080950-v1`

Gate result: `r6_direct_intake_approval_gap_readback_after_080950_v1=direct_intake_present_but_no_r6_owner_export_or_approval_unlock`

## Scope

Read-only local readback after `080950` still reported no source/control unlock. This checks whether the already-present direct manipulation intake and the R6 Oystacher approval decision package can unlock Board B. It does not mutate target roots, approve controls, derive labels, run verifier/calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Direct intake root: `/tmp/ict-engine-direct-manipulation-row-intake`.
- Direct intake files present: `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.
- Current positive CSV physical lines: `74` including header, so `73` data rows.
- Current matched-negative CSV physical lines: `74` including header, so `73` data rows.
- Direct intake provenance run id: `20260511T235910-codex-r6-canonical-intake-v57-materialization-v1`.
- Direct intake provenance says `trade_usable=false`, `raw_data_committed=false`, `runtime_code_changed=false`, and `thresholds_relaxed=false`.
- Approval package: `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`.
- Approval package gate: `r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge`.
- Approval slots:
  - `public_recap_pacer_provenance`: `pending_explicit_user_or_board_approval`.
  - `same_exhibit_flip_as_matched_controls`: `rejected_under_current_contract`.
  - `source_owned_normal_controls_alternative`: `not_supplied`.
- Approval package row counts: `positive_spoof_rows=5182`, `flip_rows=1553`, `matched_groups=1313`, `parsed_order_rows=6735`, `isolated_verifier_status=schema_ready_unscored`.

## Decision

The local direct intake is real local evidence but remains non-unlocking for Board B promotion. It is not the approved R6 owner/export root, it is not trade usable, and the current approval package does not allow canonical merge or downstream rerun. Same-exhibit FLIP rows are explicitly rejected as matched controls under the current contract, and no source-owned normal controls alternative has been supplied.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `promotion_allowed=false`; `update_goal=false`.

## Next

Continue source/control acquisition only, or obtain exactly one explicit user-selected historical path (`HTF`, `MTF`, or `LTF`) for non-promotional factor research. Do not run selected-data AutoQuant or downstream promotion until both the source/control unlock gate and selected-history gate are satisfied.
