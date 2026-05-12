# R3/R5 Public Source Durable Rerun v1

Run id: `20260512T055912-codex-r3-r5-public-source-durable-rerun-v1`

Gate result: `r3_r5_public_source_durable_rerun_v1=metadata_search_no_required_root_unlock_no_promotion`

Board hash before artifact: `9db69bf1c935ca73b6b7e81c3cac85d3a25fcd662f9182e189423e2f8d375adc`

## Scope

Durable rerun of the missing `055212` Kaggle/Hugging Face R3/R5 public metadata search. This run stores command outputs and summaries under this run root. It does not download row data, create labels, mutate R3/R5/R6 target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Search Readback

- Kaggle queries: `8`, rows scanned: `1`
- Hugging Face queries: `5`, rows scanned: `0`
- Exact R3 metadata hits: `0`
- Exact R5 metadata hits: `0`
- Kaggle file listings inspected: `1`

Summary CSV:
- `docs/experiments/actionable-regime-confidence/runs/20260512T055912-codex-r3-r5-public-source-durable-rerun-v1/r3-r5-public-source-durable-rerun-v1/r3_r5_public_source_durable_rerun_v1_search_summary.csv`

## Decision

Durable public metadata search did not unlock R3/R5 source-control evidence. No required target root exists, and no exact source-owned native sub-hour R3 rows or post-cutoff MainRegimeV2 R5 rows were acquired.

Required root status:
- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `False`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `False`
- `/tmp/ict-engine-source-panel-recency-extension`: `False`

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root.
