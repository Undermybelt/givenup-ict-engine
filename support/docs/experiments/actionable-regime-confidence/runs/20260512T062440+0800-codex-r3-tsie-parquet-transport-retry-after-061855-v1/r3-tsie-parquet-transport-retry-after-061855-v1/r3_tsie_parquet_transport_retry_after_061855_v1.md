# R3 TSIE Parquet Transport Retry After 061855 v1

Run id: `20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1`

Gate result: `r3_tsie_parquet_transport_retry_after_061855_v1=partial_range_downloaded_not_intaked_no_promotion`

Scope:
- Retry the TSIE full Parquet transport after the 061855 metadata screen.
- Keep all tooling/cache/output in `/tmp` or this run artifact.
- Do not create `/tmp/ict-engine-native-subhour-source-label-intake` unless full raw data can be verified and mapped.

Readback:
- Local modules: `{'pandas': True, 'pyarrow': False, 'duckdb': False, 'polars': False, 'requests': True}`.
- `curl --head -L` return code: `0`.
- `curl` 1 MB range return code: `0`; bytes written `1048576`.
- Disposable `uvx --with hf_xet hf --help` return code: `0`.
- Dataset-server rows length cap confirmed: `True`.

Decision:
- Full Parquet transport remains blocked in this environment.
- The rows API cannot be scaled into a full 7.19M row verifier-native intake because `length > 100` is rejected.
- No R3 target root was created, no accepted rows were added, no canonical merge ran, and no downstream promotion rerun is allowed.

Next:
- Resolve the Hugging Face/Xet transport path, provide a local verified parquet, or use another source-owned native sub-hour label dataset before materializing `/tmp/ict-engine-native-subhour-source-label-intake`.

Artifacts:
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1/r3-tsie-parquet-transport-retry-after-061855-v1/r3_tsie_parquet_transport_retry_after_061855_v1.json`
- Command CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1/r3-tsie-parquet-transport-retry-after-061855-v1/r3_tsie_transport_commands_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1/checks/r3_tsie_parquet_transport_retry_after_061855_v1_assertions.out`
