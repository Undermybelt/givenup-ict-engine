# External Source Label Second Screen v1

Run ID: `20260511T191623+0800-codex-external-source-label-second-screen-v1`

Second-pass external screen for the remaining other-market/source-label equivalence blocker. This run is additive, does not edit Current Cursor, and does not write into other agents' 19:xx run roots.

## Decision

`external_source_label_second_screen_v1=no_promotable_source_label_equivalence`

- Kaggle searches: `3`.
- Kaggle datasets profiled to `/tmp` header-only: `1`.
- Hugging Face datasets screened: `7`.
- Candidate records: `8`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full other-market/source-label equivalence: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Candidate Disposition

| Source | Candidate | Decision | Reason |
|---|---|---|---|
| `kaggle` | [`kundanbedmutha/market-trend-and-external-factors-dataset`](https://www.kaggle.com/datasets/kundanbedmutha/market-trend-and-external-factors-dataset) | `blocked_raw_ohlcv_external_factor_panel_no_regime_label` | Header contains Date, OHLCV, VIX, news, sentiment, rates, geopolitical risk, and currency fields but no source-owned regime label or owner-approved MainRegimeV2 equivalence. |
| `huggingface` | [`akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`](https://huggingface.co/datasets/akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD) | `blocked_hmm_generated_crypto_labels_no_owner_mainregimev2` | BTCUSD rows include state/regime columns at 5m/15m, but the card says regimes are inferred using a 6-state HMM from OHLCV and technical indicators; this is generated/proxy labeling, not source-owned MainRegimeV2 equivalence. |
| `huggingface` | [`ClarusC64/market-regime-coherence-mapping-v0.1`](https://huggingface.co/datasets/ClarusC64/market-regime-coherence-mapping-v0.1) | `blocked_structural_score_table_no_mainregimev2_label` | Small cross-asset structure exercise exposes coherence scores and driver labels, not row-level Bull/Bear/Sideways/Crisis source labels. |
| `huggingface` | [`ClarusC64/market-regime-transition-breakpoint-mapping-v0.1`](https://huggingface.co/datasets/ClarusC64/market-regime-transition-breakpoint-mapping-v0.1) | `blocked_transition_taxonomy_no_owner_crosswalk` | Current regime basin and transition targets are structural taxonomy fields; no owner-approved mapping to MainRegimeV2 is supplied. |
| `huggingface` | [`ClarusC64/market-structural-fragility-spike-detection-v0.1`](https://huggingface.co/datasets/ClarusC64/market-structural-fragility-spike-detection-v0.1) | `blocked_fragility_binary_not_mainregimev2` | Fragility score/spike fields can inform risk sidecars, but they are not source-owned active-regime labels. |
| `huggingface` | [`ClarusC64/market-liquidity-cliff-and-basin-shift-v0.1`](https://huggingface.co/datasets/ClarusC64/market-liquidity-cliff-and-basin-shift-v0.1) | `blocked_liquidity_state_not_market_regime_label` | Basin/edge/cliff liquidity states are execution/liquidity risk labels, not Bull/Bear/Sideways/Crisis source labels. |
| `huggingface` | [`ClarusC64/market-systemic-stabilization-and-breakpoint-detection-v0.1`](https://huggingface.co/datasets/ClarusC64/market-systemic-stabilization-and-breakpoint-detection-v0.1) | `blocked_systemic_nodes_not_mainregimev2` | Stabilization and breakpoint nodes describe crisis mechanics, but do not provide row-level MainRegimeV2 labels across the active regimes. |
| `huggingface` | [`algoplexity/computational-phase-transitions-data`](https://huggingface.co/datasets/algoplexity/computational-phase-transitions-data) | `blocked_binary_structural_break_labels_not_mainregimev2` | Dataset labels identify structural break/no-break timestamps; they do not encode Bull/Bear/Sideways/Crisis/Manipulation labels or an approved crosswalk. |

## Search Readback

- `bull bear sideways market regime` returned only the already-known stock-market-regimes source panel in the top Kaggle result.
- `market regime label` still surfaces prior blocked candidates such as NIFTY 500 behavior regimes and raw macro/commodity panels.
- `crypto market regime` surfaces recent crypto OHLCV/microstructure panels and the prior macro-stress candidate, but no source-owned MainRegimeV2 rows.

## Why It Still Blocks

The second pass found no owner-approved `MainRegimeV2` crosswalk and no source-owned rows for non-US/non-equity or source-label equivalence. The most tempting new surface is BTCUSD 5m/15m HMM-6, but Board A already rejects HMM/generated labels as proxy evidence. The ClarusC64 and Algoplexity surfaces may be useful as structural sidecars, but they do not close the active regime-confidence acceptance gate.

## Next

Keep the source-label equivalence intake verifier fail-closed. The next useful external step is not another broad keyword sweep; it is either owner-approved crosswalk acquisition for a promising candidate, or a row/provenance drop that exactly matches the existing intake verifier schema.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1_candidates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/checks/external_source_label_second_screen_v1_assertions.out`
