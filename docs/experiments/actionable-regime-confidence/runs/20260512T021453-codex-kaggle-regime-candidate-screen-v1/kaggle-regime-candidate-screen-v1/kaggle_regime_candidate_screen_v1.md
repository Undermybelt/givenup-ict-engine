# Kaggle Regime Candidate Screen v1

Run id: `20260512T021453-codex-kaggle-regime-candidate-screen-v1`

Purpose: bounded source-acquisition screen after the live Board A cursor stayed blocked on R6 owner/export controls and after public Hugging Face/TSIE branches were closed as non-promoting.

## Inputs Checked

- Board cursor before this packet: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`
- Board hash before writeback: `da876875127181fa6f7484b332ffc871c2c6cafe64ac22fa0ca0025298079340`
- R6 owner-export root: `/tmp/ict-engine-board-a-r6-owner-export-v1` absent
- R3 native sub-hour root: `/tmp/ict-engine-native-subhour-source-label-intake` absent
- R5 source-panel recency-extension root: `/tmp/ict-engine-source-panel-recency-extension` absent
- Source-label equivalence root: `/tmp/ict-engine-source-label-equivalence-intake` present with the known two confidence-blocked files
- Legacy direct rows: `/tmp/ict-engine-direct-manipulation-row-intake` present but not the active owner-export root

## Kaggle Screen

Kaggle query: `kaggle datasets list -s "market regime" --csv`.

Candidates screened:

| Candidate | Screen Result | Reason |
|---|---|---|
| `mafaqbhatti/stock-market-regimes-20002026` | known exhausted source panel | Already present in earlier board history; daily only; max date `2026-01-30`; no new R3/R5/R6 unlock. |
| `igormerlinicomposer/herding-based-market-regime-dataset` | reject for acceptance | Transformed herding/risk signals, not source-owned MainRegimeV2 labels or verifier-native rows. |
| `nickdatak/us-market-regimes-dataset-1995-2024` | proxy only | Weekly SP500 HMM/GMM latent states; explicitly unsupervised and not predefined source labels. |
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | sidecar only | Daily NIFTY 500 HMM labels to March 2026; useful as possible research context, but HMM-generated, India-only, no source-native Bull/Bear/Sideways/Crisis crosswalk, and no cross-timeframe rows. |
| `sergionefedov/synthetic-limit-order-book-market-microstructure` | reject for Board A acceptance | Synthetic 10-day simulated LOB data with normal/volatile/quiet regimes; not real source-owned market evidence. |

## Gate Result

`kaggle_regime_candidate_screen_v1=kaggle_candidates_screened_no_ready_source_owned_cross_timeframe_mainregime_export_no_promotion`

- New ready source-owned cross-timeframe `MainRegimeV2` exports found: `0`.
- Accepted rows added: `0`.
- New confidence gate: false.
- Canonical merge allowed: false.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false.
- Strict full objective achieved: false.
- `update_goal=false`.

## Non-Edits

- Runtime code changed: false.
- Shared intake mutated: false.
- R3/R5/R6 roots mutated: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- External vendor/contact request sent: false.
- Trade usable: false.

## Next

Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely new source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream rerun.
