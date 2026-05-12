# R5 Recency Source Acquisition Probe v1

- Decision: `r5_recency_source_acquisition_probe_v1=no_source_owned_post_cutoff_rows_found`.
- Required R5 extension cutoff: rows must be after `2026-01-30`.
- Local stock source rows: `245021`; date range `2000-01-03..2026-01-30`; post-cutoff rows `0`.
- Local NIFTY source rows: `3464`; date range `2012-02-02..2026-03-20`; post-cutoff rows `34`; R5 schema compatible `False`.
- Kaggle dataset ref checked: `mafaqbhatti/stock-market-regimes-20002026`; files command return code `0`.
- Source-panel recency verifier: `blocked` / `missing_required_files`.
- No `/tmp/ict-engine-source-panel-recency-extension` rows were written because no source-owned R5-compatible post-cutoff rows were found.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true` (Kaggle metadata only); trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/r5-recency-source-acquisition-probe/r5_recency_source_acquisition_probe_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/r5-recency-source-acquisition-probe/r5_recency_source_acquisition_probe_v1.md`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/r5-recency-source-acquisition-probe/r5_recency_source_acquisition_candidates_v1.csv`
- Kaggle files stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/command-output/kaggle_dataset_files_stock_market_regimes.stdout.txt`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/command-output/source_panel_recency_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-r5-recency-source-acquisition-probe-v1/checks/r5_recency_source_acquisition_probe_v1_assertions.out`
