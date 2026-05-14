# R5 Source Panel Recency Extension Acquisition Screen v1

Decision: `r5_source_panel_recency_extension_acquisition_screen_v1=no_acceptable_post_cutoff_source_owned_rows`.

Result:
- Existing source panel max date remains `2026-01-30` with `0` rows after `2026-01-30`.
- Live Kaggle file listing for `mafaqbhatti/stock-market-regimes-20002026` was checked; the dataset files are still the February 2026 source package.
- Candidate screens checked `16` local/downloaded CSV profiles; accepted R5 extension candidates: `0`.
- Accepted extension rows written: `0`; intake rows written: `false`.
- R5 verifier status after screen: `blocked`.
- Rejected recent candidates had either no root regime labels, no exact source-panel schema, no existing 39-ticker panel match, or no rows after the cutoff.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

Candidate Summary:

| Candidate | Role | Post Rows | Exact Schema | Accepted | Reject Reason |
|---|---|---:|---:|---:|---|
| `mafaqbhatti/stock-market-regimes-20002026` | `current_source_panel` | `0` | `True` | `False` | no_post_2026_01_30_rows;non_root_or_missing_labels |
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | `other_market_post_cutoff_label_source_not_r5_panel` | `34` | `False` | `False` | schema_mismatch;non_root_or_missing_labels;not_existing_39_ticker_source_panel |
| `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes` | `macro_stress_recent_rows_no_root_labels` | `26` | `False` | `False` | schema_mismatch |
| `kanchana1990/tech-giants-and-global-macroeconomic-indicators` | `recent_macro_price_rows_no_root_labels` | `26` | `False` | `False` | schema_mismatch |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch;unknown_tickers_for_r5_verifier |
| `franekwodarczyk/trading-dataset-us-stocks-various-sectors-from-09` | `recent_stock_price_indicator_rows_no_root_labels` | `53` | `False` | `False` | schema_mismatch |

Next:
Expand R6 direct Manipulation intake toward >=50/50 support with broad normal controls and direct species coverage while keeping R5 blocked until a source owner publishes valid post-cutoff source-panel rows.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/r5-source-panel-recency-extension-acquisition-screen/r5_source_panel_recency_extension_acquisition_screen_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/r5-source-panel-recency-extension-acquisition-screen/r5_source_panel_recency_extension_acquisition_screen_v1.md`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/r5-source-panel-recency-extension-acquisition-screen/r5_source_panel_recency_extension_candidates_v1.csv`
- Command CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/r5-source-panel-recency-extension-acquisition-screen/r5_source_panel_recency_extension_commands_v1.csv`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/checks/r5_source_panel_recency_extension_acquisition_screen_v1_assertions.out`
