# TSIE Public Source Intake Dry Run v1

Run id: `20260512T020450-codex-tsie-public-source-intake-dry-run-v1`
Gate result: `tsie_public_source_intake_dry_run_v1=metadata_mapping_transport_blocked_no_acceptance_no_merge`
Board hash before artifact: `968acaf8c749ed01a0fb14330562408afe12757b173452862ffdf0f9b7af39a8`

Purpose:
- Continue the non-R6 public source-label branch from the latest board next action.
- Rehearse a conservative MainRegimeV2 mapping for `sujinwo/tsie-market-regime-dataset`.
- Record the current transport blocker without mutating shared intake roots or accepting rows.

Source readback:
- Dataset: `sujinwo/tsie-market-regime-dataset`.
- Source URL: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset`.
- API URL: `https://huggingface.co/api/datasets/sujinwo/tsie-market-regime-dataset`.
- License tags: `license:mit`.
- Hugging Face metadata says private=`False`, gated=`False`, disabled=`False`.
- Size API rows: `7193996`.
- Size API parquet bytes: `591890794`.
- First-rows API feature count: `32`.
- Tmp-only first-row sample path: `/tmp/ict-engine-tsie-market-regime-dry-run-v1/first_rows_sample.json`.

Mapping rehearsal:
- `0 STRONG SELL` and `1 WEAK SELL` -> `Bear`.
- `3 FLAT / NOISE` -> `Sideways`.
- `5 WEAK BUY` and `6 STRONG BUY` -> `Bull`.
- `2 BEAR TRAP` and `4 BULL TRAP` -> `Abstain`.
- `Crisis` has no source candidate in this dataset.

Transport blocker:
- Full Parquet aggregate support was not produced in this artifact.
- DuckDB/httpfs and curl attempts in this environment hit SSL connect errors against the Hugging Face/Xet Parquet transport.
- This artifact therefore uses only Hugging Face metadata, size, and first-row APIs.

Decision:
- This remains a candidate-only mapping rehearsal, not acceptance evidence.
- It does not unlock R3/R5/R6, canonical merge, or any downstream chain rerun.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- External vendor/contact request sent: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6.
- If TSIE continues, first fix the Parquet transport/read path into `/tmp`; only then emit verifier-shaped candidate rows for Bull/Bear/Sideways, still blocked from acceptance until R6/canonical merge gates are satisfied.
