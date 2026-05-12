# Hugging Face R5/R3 Source Route Probe After 071630 v1

Run id: `20260512T072015+0800-codex-huggingface-r5-r3-source-route-probe-after-071630-v1`

Gate result: `huggingface_r5_r3_source_route_probe_after_071630_v1=no_mainregimev2_source_export_no_r5_r3_unlock`

## Scope

Read-only Hugging Face source-route probe after the `071630` source/control unlock refresh stayed blocked. This packet searches for R5/R3 candidates that could supply source-owned post-`2026-01-30` `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 roots, copy rows into canonical inputs, approve model-derived labels, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree readback, make a trade claim, or call `update_goal`.

## Search Readback

Hugging Face API searches all exited `0`.

Exact/phrase searches returned `0` datasets:
- `MainRegimeV2`
- `market regime Crisis`
- `stock market regime`
- `financial market regime`
- `regime_label`
- `stock-market-regimes`

Hyphenated/source-route searches:
- `market-regime`: `5` datasets.
- `tsie-market-regime`: `1` dataset, the already-known TSIE source.
- broad `regime`: `20` mixed-language/legal/text results; not finance source-control candidates.

## Candidate Classification

| Dataset | Useful context | Rejection reason |
|---|---|---|
| `sujinwo/tsie-market-regime-dataset` | Large finance/parquet TSIE regime source already materialized locally | Already quarantined; labels are `Bear/Bull/Sideways`; `Crisis=0`; no accepted R3 unlock |
| `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | Multi-timeframe `5m/15m` BTC regime context with HMM state/regime columns | Single crypto asset; HMM/model-derived states; no `MainRegimeV2`; no Crisis source label; not R5 post-cutoff source-panel evidence |
| `AAdevloper/nifty50-market-regime` | MIT Nifty50 binary `RISK_ON/RISK_OFF` labels | Daily technical-indicator data; max sample date `2024-11-14`; no `MainRegimeV2`; no `Crisis`; no post-`2026-01-30` rows |
| `ClarusC64/market-regime-coherence-mapping-v0.1` | Tiny cross-asset/macro regime-coherence examples | `6` train rows; relationship examples only; no source-panel row export, no `MainRegimeV2`, no Crisis-native R3 labels |
| `ClarusC64/market-regime-transition-breakpoint-mapping-v0.1` | Tiny macro transition/breakpoint examples | `6` train rows; relationship examples only; no source-panel row export, no `MainRegimeV2`, no Crisis-native R3 labels |

## Decision

No Hugging Face source/control unlock was acquired. The search improved source-route coverage but found no exact `MainRegimeV2` source export, no post-`2026-01-30` R5 source-panel rows, and no verifier-native Crisis-capable R3 `MainRegimeV2` labels. The only native-subhour-scale candidate remains TSIE, which is already quarantined and Crisis-absent.

Accepted rows added `0`; R5 recency unlock false; R3 native-subhour unlock false; R6 owner-export unlock false; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Search output root: `docs/experiments/actionable-regime-confidence/runs/20260512T072015+0800-codex-huggingface-r5-r3-source-route-probe-after-071630-v1/command-output/`
- Candidate summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072015+0800-codex-huggingface-r5-r3-source-route-probe-after-071630-v1/huggingface-r5-r3-source-route-probe-after-071630-v1/huggingface_r5_r3_source_route_probe_after_071630_v1.csv`
- JSON summary: `docs/experiments/actionable-regime-confidence/runs/20260512T072015+0800-codex-huggingface-r5-r3-source-route-probe-after-071630-v1/huggingface-r5-r3-source-route-probe-after-071630-v1/huggingface_r5_r3_source_route_probe_after_071630_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072015+0800-codex-huggingface-r5-r3-source-route-probe-after-071630-v1/checks/huggingface_r5_r3_source_route_probe_after_071630_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, or downstream promotion until explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel `MainRegimeV2` schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
