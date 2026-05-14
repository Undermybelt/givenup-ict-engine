# Live Source Label Extension Discovery After 041423 v1

- Run id: `20260512T041846-codex-live-source-label-extension-discovery-after-041423-v1`
- Decision: `live_source_label_extension_discovery_after_041423_v1=candidates_found_no_target_root_unlock_no_promotion`
- Current cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`
- Raw downloaded CSV roots stayed under `/tmp/ict-engine-live-source-label-extension-discovery-after-041423-v1`; raw data committed: `false`.
- Required roots present after scan: R3=`False`, R5=`False`, R6=`False`.

## Candidate Readback
- `mafaqbhatti/stock-market-regimes-20002026`: date_max=`2026-01-30`, rows=`245021`, label_like=`regime_label;regime_confidence`, gate=`prior_live_recheck_upstream_unchanged_no_r5_recency_tail_repair_no_promotion`.
- `igormerlinicomposer/herding-based-market-regime-dataset`: date_max=`2026-04-09`, rows=`630`, label_like=`Position;Position_Smart;Position_Smart_Lagged;Risk_State;Trend`, gate=`recency_label_like_single_panel_mapping_insufficient_no_promotion`.
- `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes`: date_max=`2026-02-25`, rows=`4150`, label_like=``, gate=`feature_panel_no_source_regime_labels_no_promotion`.
- `nickdatak/us-market-regimes-dataset-1995-2024`: date_max=`2023-12-29`, rows=`6256`, label_like=`Regime_GMM;Regime_HMM;Regime_label`, gate=`explicit_regime_source_stale_2024_no_r5_recency_no_promotion`.

## Result

No target root was unlocked. The herding dataset is the only new candidate with post-2026-01-30 label-like states, but it is a single-panel risk-state export without target-symbol source-panel rows, native sub-hour evidence, R6 owner controls, or a MainRegimeV2 cross-market contract. The macro/asset candidate is a useful feature panel but has no source-owned regime labels in the downloaded CSV. The older US-regime source is stale to 2024.

No canonical merge, downstream provider/AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion was run.
