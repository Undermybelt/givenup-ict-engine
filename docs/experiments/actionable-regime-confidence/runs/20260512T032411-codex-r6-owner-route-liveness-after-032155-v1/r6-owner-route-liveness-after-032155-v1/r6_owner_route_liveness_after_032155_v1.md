# R6 Owner Route Liveness After 032155 v1

Run id: `20260512T032411-codex-r6-owner-route-liveness-after-032155-v1`

Gate result: `r6_owner_route_liveness_after_032155_v1=official_routes_observed_rows_not_acquired_no_promotion`.

## Scope

This packet checks whether the official CME and Cboe/CFE request routes remain reachable after the `032155` source-unlock readback. It is route evidence only. It does not acquire rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, approve `FLIP` controls, run canonical merge, rerun provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, or call `update_goal`.

## Result

- Routes checked: `4`.
- Routes observed via web readback or curl: `4`.
- Cboe/CFE routes returned CLI curl HTTP `200`.
- CME routes were observable through web readback, but CLI curl was blocked or transport-failed: default curl exited `92`, HTTP/1.1 retry exited `28`, and browser-UA curl returned HTTP `403`.
- Rows acquired: `false`.
- Accepted rows added: `0`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Artifacts

- Summary CSV: `r6_owner_route_liveness_summary_after_032155_v1.csv`
- Attempt CSV: `r6_owner_route_liveness_attempts_after_032155_v1.csv`
- Web-readback CSV: `r6_owner_route_liveness_web_readback_after_032155_v1.csv`
- JSON: `r6_owner_route_liveness_after_032155_v1.json`
- Assertions: `checks/r6_owner_route_liveness_after_032155_v1_assertions.out`

## Next

Use these routes only to send or satisfy owner/export requests. Continue the Board A promotion path only after source-owned rows or explicit `FLIP`-control approval arrive, then rerun direct verifier, split calibration, and provider/Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree.
