# R6 Owner Control Local Inbox Scan v1

Run id: `20260512T013716-codex-r6-owner-control-local-inbox-scan-v1`
Gate result: `r6_owner_control_local_inbox_scan_v1=old_candidates_found_no_source_owned_controls_no_approval`

Scan scope:
- `/Users/thrill3r/Downloads`
- `/Users/thrill3r/Desktop`
- `/tmp`
- max depth `4`

Result:
- Matching local inbox candidate files found: `34`.
- Ready source-owned normal-control or explicit-approval candidates found: `0`.
- Hits are prior readbacks, source trace files, isolated/same-exhibit artifacts, live direct-intake rows, or pending approval templates; none satisfy the active owner-export branch.
- This scan does not treat historical repo experiment artifacts as source-owned control inputs.

Target root readback:
- `r6_owner_export`: present `false`, files `0` at `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- `r3_native_subhour`: present `false`, files `0` at `/tmp/ict-engine-native-subhour-source-label-intake`.
- `r5_recency_extension`: present `false`, files `0` at `/tmp/ict-engine-source-panel-recency-extension`.
- `source_label_equivalence`: present `true`, files `2` at `/tmp/ict-engine-source-label-equivalence-intake`.

Promotion status:
- Accepted rows added: `0`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

