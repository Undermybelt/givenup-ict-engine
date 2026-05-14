# Kaggle R6 Owner Export Spoofing Search After 071316 v1

Run id: `20260512T071558+0800-codex-kaggle-r6-owner-export-spoofing-search-after-071316-v1`

Gate result: `kaggle_r6_owner_export_spoofing_search_after_071316_v1=no_oystacher_owner_export_no_normal_controls_no_unlock`

## Scope

This packet summarizes existing Kaggle command-output artifacts for R6 owner/export and spoofing-source acquisition after the `071316` local archive/schema readback. It does not mutate `/tmp/ict-engine-board-a-r6-owner-export-v1` or canonical intake; does not approve public same-exhibit controls; does not run direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion; does not make a trade claim; and does not call `update_goal`.

## Readback

- Kaggle searches for `3red trading`, `direct manipulation controls`, `direct manipulation matched controls`, `direct manipulation positive rows`, `futures order lifecycle`, `market depth mbo mbp`, and `oystacher` returned no datasets.
- Kaggle search for `spoofing futures` returned three crypto/order-book datasets:
  - `adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m`
  - `adamatractor/bitcoin-btc-level-2-orderbook-depth-data-5m`
  - `adamatractor/dex-orderbook-data-5m`
- These are crypto/DEX or Hyperliquid order-book context datasets, not CFTC/Oystacher owner-export packages, not futures owner/export rows, and not source-owned normal-control rows for Board A R6.

## Decision

The Kaggle R6 search found no verifier-native owner/export package for Oystacher-style direct manipulation and no source-owned normal/non-manipulation controls. The crypto order-book hits may be market-depth context for another lane, but they do not satisfy R6 source/control requirements and do not unlock canonical merge or downstream promotion.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Command output directory: `docs/experiments/actionable-regime-confidence/runs/20260512T071558+0800-codex-kaggle-r6-owner-export-spoofing-search-after-071316-v1/command-output/`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071558+0800-codex-kaggle-r6-owner-export-spoofing-search-after-071316-v1/kaggle-r6-owner-export-spoofing-search-after-071316-v1/kaggle_r6_owner_export_spoofing_search_after_071316_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T071558+0800-codex-kaggle-r6-owner-export-spoofing-search-after-071316-v1/checks/kaggle_r6_owner_export_spoofing_search_after_071316_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel `MainRegimeV2` schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
