# R5 Recency Provenance Date Disambiguation v1

- Run id: `20260512T012104-codex-r5-recency-provenance-date-disambiguation-v1`.
- Gate result: `r5_recency_provenance_date_disambiguation_v1=composite_date_max_not_r5_stock_recency_rows_root_still_missing`.
- Composite source-label provenance `date_max`: `2026-03-20`.
- Raw stock-regime source date range: `2000-01-03` to `2026-01-30`.
- Raw stock-regime post-cutoff rows after `2026-01-30`: `0`.
- Source-label post-cutoff rows by owner: `ahaanverma00=34`.
- R5 verifier: status `blocked`, reason `missing_required_files`, exit `2`.
- Accepted rows added: `0`; new confidence gate: false; downstream chain rerun allowed: false.
- Strict full objective achieved: false. `update_goal=false`.

## Target Cells

- `XOM` / `Sideways`: raw stock latest `2025-12-19`, raw post-cutoff `0`, source-label latest `2025-12-19`, source-label post-cutoff `0`.
- `UNH` / `Bear`: raw stock latest `2025-12-31`, raw post-cutoff `0`, source-label latest `2025-12-31`, source-label post-cutoff `0`.
- `^DJI` / `Sideways`: raw stock latest `2025-12-01`, raw post-cutoff `0`, source-label latest `2025-12-01`, source-label post-cutoff `0`.
- `AMD` / `Bear`: raw stock latest `2025-12-11`, raw post-cutoff `0`, source-label latest `2025-12-11`, source-label post-cutoff `0`.

## Boundary

Do not use the composite `2026-03-20` date max to populate R5. It is not post-cutoff stock-regime source evidence for the required R5 cells. Keep `/tmp/ict-engine-source-panel-recency-extension` absent until source-owned extension rows and provenance are delivered.
