# R5/R3 Target Contract Readback After 065449 v1

Run id: `20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1`

Gate result: `r5_r3_target_contract_readback_after_065449_v1=post_cutoff_candidates_found_but_no_required_root_unlock_no_downstream`

Board sha256 before artifact: `0b05a246460cac6efb760a42833ac08fa2fdaefaca156cb8605ae18c6dd7adb2`

## Scope

This readback checks the newer public source-search outputs from `065449`, `065547`, and `065605` against the existing R5/R3 target contracts. It does not download new raw data, mutate `/tmp/ict-engine-source-panel-recency-extension`, approve TSIE, approve any public dashboard, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Contract Readback

The R5 verifier requires:

- `/tmp/ict-engine-source-panel-recency-extension/stock_market_regimes_2026_extension.csv`
- `/tmp/ict-engine-source-panel-recency-extension/source_panel_recency_provenance.json`
- rows after `2026-01-30`
- expected existing source-panel tickers
- `regime_label` in `Bear`, `Bull`, `Crisis`, or `Sideways`

The R3 target remains verifier-native, Crisis-capable `MainRegimeV2` labels. TSIE-derived proxy rows do not satisfy that policy gate.

## Candidate Decisions

| Candidate | Readback | Decision |
|---|---|---|
| NIFTY 500 behavior regime | Has `35` post-`2026-01-30` rows, but labels are `Trending`, `Mean-Reverting`, `Noisy`, `Durable`, `Fragile`, `Calm`, `Choppy`, and `Stress`. | Reject as R5/R3 unlock. It is not the expected 39-ticker source panel, not `Bull/Bear/Sideways/Crisis`, and not native subhour. |
| Global Market Stress and Liquidity Regimes | Has `26` post-`2026-01-30` rows, but the observed source field is numeric `Financial_Stress_Index`. | Reject as R5/R3 unlock. It is a stress index, not source-owned `MainRegimeV2` labels. |
| Stock Market Regimes 2000-2026 | Has historical `Bull/Bear/Sideways/Crisis` rows but still ends at `2026-01-30`. | Reject as R5 recency unlock because post-cutoff rows are `0`. |
| Public dashboard/article candidates from `065605` | No acquired verifier-native row packet. | Reject as source/control unlock. |

## Accounting

- Accepted rows added: `0`
- R5 recency unlock: `false`
- R3 native-subhour unlock: `false`
- R6 owner-export unlock: `false`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Provider/AutoQuant promotion: `false`
- Filter / Pre-Bayes / BBN / CatBoost / path-ranking / execution-tree rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- Decision CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1/r5-r3-target-contract-readback-after-065449-v1/r5_r3_target_contract_readback_after_065449_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1/r5-r3-target-contract-readback-after-065449-v1/r5_r3_target_contract_readback_after_065449_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1/checks/r5_r3_target_contract_readback_after_065449_v1_assertions.out`

## Next

Do not materialize the NIFTY or macro-stress candidates into R5/R3 target roots. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 post-`2026-01-30` rows matching the existing source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
