# Kaggle R5/R3 Source Route Probe After 071316 v1

Run id: `20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1`

Gate result: `kaggle_r5_r3_source_route_probe_after_071316_v1=candidates_found_nifty500_profiled_no_mainregimev2_no_unlock`

## Scope

This packet materializes the report and assertion files referenced by the Board A `071538` registration. It is a readback of already-created Kaggle command outputs and profile artifacts. It does not copy Kaggle rows into R3/R5/R6 target roots, approve behavior or macro labels, run direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter/Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree readback, make a trade claim, or call `update_goal`.

## Readback

- Kaggle `MainRegimeV2` search exited `0` and returned no datasets.
- `mafaqbhatti/stock-market-regimes-20002026` remains a historical stock-regime candidate with `245,021` rows and label counts `Bull=103,766`, `Bear=54,939`, `Sideways=56,668`, `Crisis=29,632`, and `High-volatility=16`.
- The `mafaqbhatti` candidate max date is `2026-01-30`, so rows after `2026-01-30` are `0`; it does not unlock R5 recency.
- `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` downloaded and profiled successfully. Its files include post-`2026-01-30` rows through `2026-03-20`, but labels are behavior or macro states, not source-panel `MainRegimeV2` labels.
- NIFTY profile label families include `Mean-Reverting`, `Noisy`, `Trending`, `Durable`, `Fragile`, `Calm`, `Choppy`, and `Stress`; no `Crisis` label and no R3 native-subhour provenance is present.

## Decision

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle_r5_r3_source_route_probe_after_071316_v1.json`
- Historical candidate profile JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle_stock_market_regimes_2000_2026_profile_v1.json`
- Historical label counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle-r5-r3-source-route-probe-after-071316-v1/kaggle_stock_market_regimes_2000_2026_label_counts_v1.csv`
- NIFTY behavior profile JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1/command-output/kaggle_nifty500_behavior_profile.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T071538+0800-codex-kaggle-r5-r3-source-route-probe-after-071316-v1/checks/kaggle_r5_r3_source_route_probe_after_071316_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
