# Daily Main Root Source Inventory v1

Run ID: `20260511T162942+0800-codex-daily-main-root-source-inventory-v1`

## Decision

- This is a positive source-panel inventory for the actual `MainRegimeV2` price roots: `Bull`, `Bear`, `Sideways`, and `Crisis`.
- It does not promote child/sub-regime labels into root accounting.
- It does not use OHLCV proxies for direct `Manipulation`; `Manipulation` remains a separate direct overlay.
- New confidence gate claimed: `false`; full objective achieved: `false`; `update_goal=false`.

## Coverage

- Rows: `245021`
- Tickers: `39`
- Years: `27`
- Date range: `2000-01-03` to `2026-01-30`
- Daily ticker/root slots covered: `156/156`; Wilson95 LCB `0.975967`
- Year/root slots covered: `108/108`; Wilson95 LCB `0.965653`

## Root Counts

| Root | Rows |
|---|---:|
| Bull | 103766 |
| Bear | 54939 |
| Sideways | 56668 |
| Crisis | 29632 |

## Child Boundary

Accepted child/sub-regime packets may be useful context, but they attach under a separately emitted parent root. They cannot close a parent root by name, and `Manipulation` cannot be filled from OHLCV child tags.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1.json`
- Ticker/root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1_ticker_root.csv`
- Year/root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1_year_root.csv`
- Split/root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1_split_root.csv`
- Instrument/root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1_instrument_root.csv`
- Child attachment CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1_child_attachment.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/checks/daily_main_root_source_inventory_v1_assertions.out`
