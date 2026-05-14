# Reproduce TSIE dry run

Raw parquet was downloaded to `/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/0000.parquet` using the Hugging Face converted parquet URL recorded in `tsie_source_label_intake_dryrun_v1.json`.

The stats pass used:

```bash
uv run --with pyarrow python <pyarrow-only selected-column aggregation script>
```

Only selected columns were read: `group_id`, `time`, `regime_label`. Raw parquet data was not copied into the repo.
