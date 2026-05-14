# GitHub Source Label Candidate Screen v1

Run ID: `20260511T193958+0800-codex-github-source-label-candidate-screen-v1`

## Decision

`github_source_label_candidate_screen_v1=no_promotable_source_label_equivalence`

- GitHub search queries: `4`.
- Candidate records dispositioned: `6`.
- Ready source-owned or owner-approved active-regime label sources found: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Candidate Disposition

| Repo | Decision | Reason |
|---|---|---|
| [`akash-kumar5/CryptoMarket_Regime_Classifier`](https://github.com/akash-kumar5/CryptoMarket_Regime_Classifier) | `blocked_hmm_generated_labels_not_source_owned` | Regimes are discovered from OHLCV/technical features and HMM state mapping, not source-owned or owner-approved MainRegimeV2 labels. |
| [`uday-31/detecting-market-regime-changes`](https://github.com/uday-31/detecting-market-regime-changes) | `blocked_hmm_pseudo_labels_not_source_owned` | Labels are retrospective HMM outputs and then classifier targets; they are proxy/generated labels rather than source-owned labels. |
| [`iamd26/Predicting-Market-Regimes-Based-on-Stock-Bond-Return-ratio`](https://github.com/iamd26/Predicting-Market-Regimes-Based-on-Stock-Bond-Return-ratio) | `blocked_method_generated_binary_turning_points` | The repository provides methodology-generated bull/bear turning points from price series, not row-level source-owned regime labels or a four-root MainRegimeV2 crosswalk. |
| [`hetu412patel/volatility-regime-classification`](https://github.com/hetu412patel/volatility-regime-classification) | `blocked_model_generated_binary_crisis_noncrisis` | Binary model output is not source-owned Bull/Bear/Sideways/Crisis labels and does not cover the required active-regime taxonomy. |
| [`AndrewFSee/regime-rl-trading`](https://github.com/AndrewFSee/regime-rl-trading) | `blocked_feature_or_hmm_detector_outputs_not_source_labels` | The framework generates detector outputs for strategy routing; no source-owned row-level label panel or owner-approved crosswalk is exposed. |
| [`Hishamhajaz/market-regime-detection`](https://github.com/Hishamhajaz/market-regime-detection) | `blocked_kmeans_generated_spy_labels` | Labels are KMeans-generated from SPY OHLCV features and a plot output, not source-owned validation labels. |

## Search Readback

- Public GitHub hits were mostly HMM, KMeans, feature-threshold, Lunde/Timmermann, or binary volatility-classifier projects.
- None exposed source-owned row-level Bull/Bear/Sideways/Crisis labels, owner-approved MainRegimeV2 equivalence rows, or usable direct `Manipulation` positive/control rows.
- `akash-kumar5/CryptoMarket_Regime_Classifier` overlaps the prior Hugging Face HMM-6 BTCUSD surface and remains proxy/generated evidence.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193958-codex-github-source-label-candidate-screen-v1/github-source-label-screen/github_source_label_candidate_screen_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193958-codex-github-source-label-candidate-screen-v1/github-source-label-screen/github_source_label_candidate_screen_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193958-codex-github-source-label-candidate-screen-v1/checks/github_source_label_candidate_screen_v1_assertions.out`
