# R6 Board Artifact Integrity Repair v1

- Run id: `20260512T004552-codex-r6-board-artifact-integrity-repair-v1`.
- Board hash observed before writeback: `fdb757d9e819602ddd747f77123f228bef27467d6da0c4dc424ade7a3c01eee3`.
- Gate result: `r6_board_artifact_integrity_repair_v1=current_cursor_and_supporting_artifacts_present_no_merge`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Findings

- The Current Cursor points to `20260512T004322-codex-r6-oystacher-external-control-source-scan-v1`, and the cursor run root plus its JSON, report, source CSV, fetch readback CSV, assertions, and reproduction script are present.
- The supporting public normal-control probe `20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1` is also present.
- The board also references `20260512T004022-codex-r6-oystacher-source-owner-control-route-v1`; that run root is present in this checkout after the final recheck and can be used as source-route context.
- Additional present route evidence is `20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1`; the present route/date-fit evidence is `20260512T004410-codex-r6-official-route-date-fit-check-v1`.
- `/tmp/ict-engine-board-a-r6-owner-export-v1` is absent, so no verifier-native owner package exists for canonical merge.

## Result

No source-owned normal controls were acquired, no same-exhibit `FLIP` rows were approved as controls, no shared intake was mutated, and no provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun is allowed.

## Next

Keep `004322` as the active R6 source/control cursor. Use the present `004116`, `004022`, `003924`, and `004410` artifacts for public-source and source-route/date-fit context, then acquire source-owned normal controls through the mapped CME/Cboe routes or explicitly approve the same-exhibit `FLIP`-as-control exception before any canonical merge or downstream rerun.
