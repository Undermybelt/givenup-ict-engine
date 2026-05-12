# R6 Official Row-Level Support Extension v1

Run ID: `20260511T220755+0800-codex-r6-official-rowlevel-support-extension-v1`

## Result

- Official CFTC source PDFs fetched to `/tmp`: `2`.
- Source text checks passed: `true`.
- Rows added: positives `9`, matched controls `9`.
- Direct intake after run: positives `62`, matched negatives `62`, matched groups `61`.
- Unique positive dates/symbols/venues: `49` / `26` / `11`.
- Wilson95 LCB positive/negative/min: `0.941656` / `0.941656` / `0.941656`.
- `50/50` support gate: `true`.
- Broad normal sample: `false`; controls remain same-complaint genuine-order schema seeds.
- Direct species coverage closed: `false`.
- Gate result: `r6_official_rowlevel_support_extension_v1=support_50x50_reached_confidence_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run changes only the shared `/tmp/ict-engine-direct-manipulation-row-intake` files and writes repo-local evidence artifacts. It does not commit raw PDFs/text, change runtime code, relax thresholds, or promote same-event genuine-order controls into broad normal-market controls.
