# Local Row Export Inventory v1

Run ID: `20260511T134054+0800-codex-local-row-export-inventory-v1`

## Result

- Usable local FINRA spoofing/layering positive row exports: `0`.
- Usable local FINRA spoofing/layering matched negative row exports: `0`.
- Usable local native intraday/full-species `MainRegimeV2` source-label panels: `0`.
- Gate result: `local_inventory_no_attachable_row_export_found`.
- Full objective achieved: `false`.

## What Was Checked

Local filename search was limited to `/Users/thrill3r/Downloads` and `docs/experiments/actionable-regime-confidence/runs`, with terms around FINRA, spoofing/layering, quote stuffing, manipulation, market regime labels, order book, market center, and PBBO.

## Relevant Existing Files

- `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`: already consumed daily/weekly/monthly US stock/index panel.
- `finra_manipulation_acquisition_schema_v1.csv`: schema only, no row export.
- `spoofing_appendix_direct_case_inventory.csv`: positive enforcement case inventory only, no matched negative order-lifecycle rows.
- Zenodo DEX self-trade sample files: already scoped self-trade slices, not spoofing/layering matched-negative coverage.

## Decision

This closes the "maybe the rows are already local" branch. The next valid move is acquisition, not another local filename or public metadata sweep:

- authenticated/user-provided FINRA-style spoofing/layering rows plus matched negatives, or
- exact native intraday/full-species `MainRegimeV2` source-label panel.

## Guardrails

- No runtime code changed.
- No thresholds relaxed.
- No raw data committed.
- No trade usability claimed.
- No full-objective completion claimed.
