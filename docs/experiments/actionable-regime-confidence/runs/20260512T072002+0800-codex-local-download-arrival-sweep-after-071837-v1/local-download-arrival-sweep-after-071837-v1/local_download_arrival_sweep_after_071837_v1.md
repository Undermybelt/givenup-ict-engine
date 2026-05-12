# Local Download Arrival Sweep After 071837 v1

Run id: `20260512T072002+0800-codex-local-download-arrival-sweep-after-071837-v1`

Gate result: `local_download_arrival_sweep_after_071837_v1=known_stock_regime_download_only_no_vendor_export_no_unlock`

## Scope

Bounded read-only sweep of recent files under `Downloads`, `Desktop`, and `Documents` after the `071837` Kaggle source-probe registration. This packet does not mutate target roots, copy rows into canonical inputs, approve proxy labels, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Recent candidate files matched: `4`.
- Candidate unlock-like files matched: `0`.
- Known stock-market-regimes max date: `2026-01-30`.
- Known stock-market-regimes post-`2026-01-30` rows: `0`.

## Decision

The bounded recent local sweep found only the known stock-market-regimes-20002026 CSV/parquet context files as name-matched arrivals. No vendor ticket/export/license response, DBN/MBO/MBP/depth/order-lifecycle file, required R6 filename, MainRegimeV2 source export, or native-subhour file arrived outside the target roots.

Accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T072002+0800-codex-local-download-arrival-sweep-after-071837-v1/local-download-arrival-sweep-after-071837-v1/local_download_arrival_sweep_after_071837_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072002+0800-codex-local-download-arrival-sweep-after-071837-v1/local-download-arrival-sweep-after-071837-v1/local_download_arrival_sweep_after_071837_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072002+0800-codex-local-download-arrival-sweep-after-071837-v1/checks/local_download_arrival_sweep_after_071837_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export.
