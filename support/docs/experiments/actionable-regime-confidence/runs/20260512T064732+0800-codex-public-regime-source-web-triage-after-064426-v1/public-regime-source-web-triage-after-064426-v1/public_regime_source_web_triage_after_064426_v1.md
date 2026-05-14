# Public Regime Source Web Triage After 064426 v1

Run id: `20260512T064732+0800-codex-public-regime-source-web-triage-after-064426-v1`

Gate result: `public_regime_source_web_triage_after_064426_v1=no_public_crisis_or_recency_unlock_no_downstream`

Board sha256 before artifact: `367a295e6e70dcb55b1619d7bf53afe056aeb87a6a3b5855cbc0ab1fa0b32670`

## Scope

Targeted web/source triage after the local CFE sample applicability audit `064426`. The goal was to look for a public source-label path that could satisfy one of the still-open unlocks:

- verifier-native R3 native-subhour `MainRegimeV2` labels including `Crisis`
- source-owned R5 post-cutoff recency extension
- genuinely new cross-timeframe `MainRegimeV2` source export

This triage did not download or mutate target roots, approve TSIE, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Candidate Decisions

| Candidate | Source | Decision | Reason |
|---|---|---|---|
| `thesven/fintime-decoder-dataset` | `https://huggingface.co/datasets/thesven/fintime-decoder-dataset` | `rejected_forecasting_dataset_no_source_regime_labels` | The dataset is useful market forecasting coverage, but it is not source-owned Bull/Bear/Sideways/Crisis regime evidence and does not provide accepted native-subhour `MainRegimeV2` labels. |
| `Sashank-810/crisisnet-dataset` | `https://huggingface.co/datasets/Sashank-810/crisisnet-dataset` | `rejected_corporate_distress_not_mainregimev2_market_regime` | CrisisNet is corporate distress/crisis event data. It does not provide market-wide `MainRegimeV2` Bull/Bear/Sideways/Crisis labels, R3 native-subhour rows, or R5 source-panel recency rows. |
| `FinMultiTime` | `https://arxiv.org/abs/2506.05019` | `rejected_multimodal_forecasting_not_source_label_packet` | The paper describes multimodal financial time-series forecasting data, not source-owned `MainRegimeV2` labels with accepted per-regime confidence and cross-axis validation. |
| `FinRL-Meta` | `https://papers.nips.cc/paper_files/paper/2022/file/0bf54b80686d2c4dc0808c2e98d430f7-Paper-Datasets_and_Benchmarks.pdf` | `rejected_platform_data_source_not_regime_label_unlock` | Useful as a data-source platform reference, but not a Board A source/control packet and not a verifier-native R3/R5/R6 unlock. |
| `mafaqbhatti/stock-market-regimes-20002026` | `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026` | `rejected_prior_known_daily_panel_no_new_unlock_in_this_slice` | Already covered by prior local/public-source sweeps as a daily panel that does not satisfy the current R5/R3/R6 unlock contract in this slice. |

## Decision

No public web candidate was selected. The search did not find a source-owned `Crisis`-capable R3 native-subhour `MainRegimeV2` label packet, a source-owned R5 post-cutoff recency extension, or a new accepted cross-timeframe `MainRegimeV2` source export.

Promotion remains blocked: accepted rows added `0`, valid required root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.
