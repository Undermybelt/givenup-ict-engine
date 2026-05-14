# TSIE Public Source Intake Dry Run v1

Run id: `20260512T020216-codex-tsie-public-source-intake-dry-run-v1`
Gate result: `tsie_public_source_intake_dry_run_v1=sample_mapping_ready_no_acceptance_no_canonical_merge`

Scope:
- Candidate: `sujinwo/tsie-market-regime-dataset`.
- Dataset URL: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset`.
- API-only dry run; full parquet download is explicitly `false`.
- Canonical intake roots were not mutated.

Source facts:
- License verified: `True`.
- Total rows from dataset-server size API: `7193996`.
- Parquet size from dataset-server parquet API: `591890794` bytes.
- Local parquet engines available for full read: `false` for pyarrow/duckdb/polars in this environment.

Sample dry run:
- Offsets sampled: `[0, 500000, 2000000, 4000000, 6000000]` with page length `100`.
- Sampled rows: `500`.
- Unique symbols in sample: `5`.
- Timeframe hints in sample: `1D, 240, 60`.
- Source label counts: `{'FLAT / NOISE': 151, 'BEAR TRAP': 96, 'WEAK SELL': 123, 'BULL TRAP': 35, 'WEAK BUY': 61, 'STRONG BUY': 10, 'STRONG SELL': 24}`.
- MainRegimeV2 dry-run counts: `{'Sideways': 151, 'Abstain': 131, 'Bear': 147, 'Bull': 71}`.
- Decision counts: `{'map': 369, 'abstain_trap': 131}`.
- Year counts: `{'2013': 100, '2012': 100, '2017': 100, '2024': 100, '2020': 43, '2021': 57}`.
- Row API errors: `[]`.

Mapping posture:
- Bear: `STRONG SELL`, `WEAK SELL`.
- Sideways: `FLAT / NOISE`.
- Bull: `WEAK BUY`, `STRONG BUY`.
- Abstain: `BEAR TRAP`, `BULL TRAP`.
- Crisis: not represented by TSIE labels.

Decision:
- This is useful as a public non-US equity source-label dry run for Bull/Bear/Sideways mapping research.
- It is not Board A acceptance evidence because it is sample-only, not full calibrated split/market/time evidence, and R6/canonical merge remains blocked.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

Next:
- If continuing this branch, acquire a parquet-capable reader in disposable `/tmp` tooling or use a bounded remote parquet scanner, then compute full split/year/symbol label support before any canonical intake proposal. Keep R6 and full objective blocked until owner-export/FLIP evidence and canonical merge exist.
