# TSIE Local Download Rejection Readback v1

Run id: `20260512T062519+0800-codex-tsie-local-download-rejection-readback-v1`

Gate result: `tsie_local_download_rejection_readback_v1=download_present_same_hash_provenance_rejected_no_intake_no_promotion`

## Scope

This readback reconciles the completed local Hugging Face CLI download with the Board A TSIE provenance decision. It does not copy rows into `/tmp/ict-engine-native-subhour-source-label-intake`, does not mutate any required target root, does not run canonical merge or downstream promotion, does not make a trade claim, and does not call `update_goal`.

## Download Readback

- Local HF parquet present: `True`
- Local HF parquet bytes: `591890794`
- Local HF parquet sha256: `8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158`
- Matches prior private-tmp dry-run parquet: `True`
- Prior dry-run rows: `7193996`
- Prior dry-run groups: `1150`
- Prior dry-run window: `1990-06-07T02:00:00` to `2026-04-07T02:00:00`

## Provenance Decision

- 062201 provenance rejected TSIE as rule-based proxy labels: `True`
- 062253 prior-evidence reconciliation blocked the same dataset/commit: `True`
- TSIE remains useful research metadata, but not source-owned `MainRegimeV2` R3 intake evidence.

## Required Roots

| Root | Present | File count |
|---|---:|---:|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `0` |
| `/tmp/ict-engine-native-subhour-source-label-intake` | `False` | `0` |
| `/tmp/ict-engine-source-panel-recency-extension` | `False` | `0` |

## Decision

- Accepted rows added: `0`.
- Source/control evidence acquired: `false`.
- Target root mutated: `false`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Do not materialize TSIE into the R3 target root. Continue with owner/source-native R3 labels, R5 recency rows, or R6 owner/export controls before any direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree readback.
