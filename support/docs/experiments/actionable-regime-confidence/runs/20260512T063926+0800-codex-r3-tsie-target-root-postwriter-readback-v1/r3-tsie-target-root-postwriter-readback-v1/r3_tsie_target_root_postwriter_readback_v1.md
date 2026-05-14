# R3 TSIE Target-Root Postwriter Readback v1

Run id: `20260512T063926+0800-codex-r3-tsie-target-root-postwriter-readback-v1`

Gate result: `r3_tsie_target_root_postwriter_readback_v1=target_root_finished_bull_bear_sideways_only_policy_blocked_no_promotion`

Scope:
- Read back `/tmp/ict-engine-native-subhour-source-label-intake` after the earlier quarantine noted that the writer was still active.
- Did not delete, rewrite, or consume the target root as an accepted unlock.
- Did not run direct verifier, canonical merge, provider/AutoQuant, Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, or `update_goal`.

Readback:
- Target root exists and contains `native_subhour_source_label_rows.csv` plus `native_subhour_source_label_provenance.json`.
- Rows file size observed by `stat`: `2786719721` bytes.
- Provenance file size observed by `stat`: `2400` bytes.
- Rows line count observed by `wc -l`: `5032904`, which is one header plus `5032903` data rows.
- Provenance-declared rows SHA-256: `72406e48b000f91ed2b3c3e132651537339afb2a8ed2e3ce43b5007abf38f62f`.
- Provenance SHA-256 observed by `shasum`: `60f2422260c404302dbb98dc641f13e50cdae8f09527a848e614a690b87fcc0f`.
- Raw parquet SHA-256 from provenance: `8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158`.

063155 artifact readback:
- `schema_ready=true`.
- `raw_parquet_sha256_verified=true`.
- `target_root_mutated=true`.
- `mapped_rows=5032903`.
- `accepted_mapping_confidence_95_labels=Bear,Bull,Sideways`.
- `canonical_merge=false`.
- `downstream_promotion_rerun=false`.
- `strict_full_objective=false`.
- `trade_usable=false`.
- `update_goal=false`.

Decision:
- The file-writing side of `063155` is now readable, but it remains a policy-blocked TSIE target-root materialization, not an accepted R3 unlock.
- Board A accepted rows added remain `0` for strict objective accounting. The `5032903` rows are materialized/mapped TSIE rows only.
- `Crisis` remains absent, TSIE remains disputed/proxy under the prior ledger, R6 owner-export/control evidence is still absent, R5 recency is still absent, canonical merge did not run, and downstream promotion did not rerun.

Next:
- Keep `/tmp/ict-engine-native-subhour-source-label-intake` quarantined unless the user/board explicitly changes the TSIE source/control policy.
- Continue from real R6 owner-export rows with controls, source-owned R5 recency rows, verifier-native R3 labels, a genuinely new accepted cross-timeframe `MainRegimeV2` source export, or explicit source/control approval before rerunning the full chain.
