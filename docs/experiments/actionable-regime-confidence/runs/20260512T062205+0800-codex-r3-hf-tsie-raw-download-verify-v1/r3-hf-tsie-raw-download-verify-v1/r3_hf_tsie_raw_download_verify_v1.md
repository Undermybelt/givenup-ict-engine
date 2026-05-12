# R3 HF TSIE Raw Download Verify v1

Run id: `20260512T062205+0800-codex-r3-hf-tsie-raw-download-verify-v1`

Candidate source: `sujinwo/tsie-market-regime-dataset`

Purpose: perform the next non-promoting R3 candidate check from the Board B TODO by attempting to download the raw parquet into `/tmp`, compute file evidence, and verify whether the source can become a native-subhour intake candidate. This run does not mutate `/tmp/ict-engine-native-subhour-source-label-intake` or any other required target root.

## Result

Decision: `r3_hf_tsie_raw_download_verify_v1=raw_download_blocked_xethub_tls_schema_api_readable_no_acceptance`

Raw parquet download did not succeed. The Hugging Face dataset-server metadata and first-rows APIs were readable, but every attempted raw parquet download path failed while connecting to `cas-bridge.xethub.hf.co`.

## Attempts

- `01_hf_headers`: `curl -I -L` against the converted parquet URL exited `35`.
- `02_hf_raw_download`: `curl -L` full download exited `35`.
- `07_hf_range_curl_http1`: `curl --http1.1 --range 0-1048575` exited `35`.
- `08_hf_range_python_requests`: Python `requests` range fetch exited `1`.
- `09_hf_cli_download_no_xet`: `hf download ... tft_dataset_labeled.parquet` with `HF_HUB_DISABLE_XET=1` exited `1`.
- `10_hf_cli_download_convert_no_xet`: `hf download ... default/train/0000.parquet --revision refs/convert/parquet` with `HF_HUB_DISABLE_XET=1` exited `1`.
- `11_wget_raw_download`: `wget` full download exited `4`.

Common blocker:
- `curl` and `wget` reached `huggingface.co`, received a `302` to `cas-bridge.xethub.hf.co`, then failed TLS with EOF / SSL_ERROR_SYSCALL.
- Python `requests` and `hf download` failed with `UNEXPECTED_EOF_WHILE_READING` against the same CAS bridge.

## Readable Metadata

- `04_hf_first_rows` exited `0`.
- `05_hf_size` exited `0`.
- Dataset-server size reports `7193996` rows, `32` columns, and `591890794` parquet bytes for split `train`.
- First-rows/schema API confirms:
  - native timestamp field: `time` as `timestamp[ns]`
  - OHLCV fields: `open`, `high`, `low`, `close`, `volume`
  - session/hour fields: `is_opening`, `is_closing`, `is_session_1`, `is_session_2`, `hour`
  - source label field: `regime_label` as `int8`
  - subhour sample timestamps such as `2013-01-07T02:00:00`, `2013-01-07T03:00:00`, and `2013-01-07T04:00:00`

## Gate

- `candidate_metadata_readable=true`.
- `raw_parquet_downloaded=false`.
- `raw_parquet_sha256_present=false`.
- `raw_parquet_local_metadata_verified=false`.
- `target_root_mutated=false`.
- `accepted_rows_added=0`.
- `canonical_merge=false`.
- `downstream_promotion_rerun=false`.
- `strict_full_objective=false`.
- `trade_usable=false`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

The candidate remains useful but not accepted. A future attempt needs either a working CAS/XetHub download path, an alternate mirror, or a smaller verifier-native sample sourced from the owner route before `/tmp/ict-engine-native-subhour-source-label-intake` can be populated. Do not run canonical merge or downstream provider/AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost / path-ranking -> execution-tree promotion from this packet.
