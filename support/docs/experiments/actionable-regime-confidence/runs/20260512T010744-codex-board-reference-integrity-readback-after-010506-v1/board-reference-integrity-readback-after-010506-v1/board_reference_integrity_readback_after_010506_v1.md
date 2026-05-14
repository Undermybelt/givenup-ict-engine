# Board Reference Integrity Readback After 010506 v1

- Run id: `20260512T010744-codex-board-reference-integrity-readback-after-010506-v1`.
- Board cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Board hash observed: `6ac85f7af44e170b6f7216340716d1c42a573295a62bbf6b6fb7070056f77349`.
- Gate result: `board_reference_integrity_readback_after_010506_v1=missing_010212_reference_no_promotion`.
- Missing tail-referenced run root: `docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1`.
- Present verified run roots: `005913`, `010127`, `010201`, `010401`, `010506`, and `010612`.
- Present but non-promoting completion-audit root: `010503`.

## Result

- Treat the board section that references `010212` as non-durable until the files are restored or regenerated.
- Do not use `010212` as promotion evidence in its current filesystem state.
- `010401`, `010503`, and `010612` are present after concurrent completion, but they remain non-promoting: no rows or controls were acquired, and downstream rerun remains disallowed.
- Required R6 owner-export files are still absent under `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Non-R6 required intake files are still absent under their target `/tmp` roots.
- Valid source-owned normal controls acquired: `0`.
- Same-exhibit `FLIP` approval acquired: false.
- Canonical merge allowed: false.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.
- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.

## Next

Preserve the `010127` cursor. Use the verified `005913` request drafts and `010506` contact routes to satisfy the R6 owner-export request or obtain explicit `FLIP`-control approval. Only after verifier-native controls plus provenance arrive should `/tmp/ict-engine-board-a-r6-owner-export-v1` be populated under shared lock and the direct verifier plus downstream chain be rerun.
