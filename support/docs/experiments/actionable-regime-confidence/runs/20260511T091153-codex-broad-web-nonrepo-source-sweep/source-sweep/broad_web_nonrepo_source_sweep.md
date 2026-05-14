# Broad Web Non-Repo Source Sweep

Run id: `20260511T091153+0800-codex-broad-web-nonrepo-source-sweep`

## Result

- Active taxonomy: `MainRegimeV2`.
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct class / overlay: `Manipulation`.
- Candidates classified: `7`.
- Accepted new MainRegimeV2 root-label slots: `0`.
- Accepted new direct `Manipulation` label sources: `0`.
- Accepted gate remains `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_broad_web_nonrepo_sources_proxy_partial_or_methodology_only`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Candidate Dispositions

| Source | Decision | Reason |
|---|---|---|
| [Kaggle stock-market-regimes-2000-2026](https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026) | `partial_existing_only_no_new_missing_slots` | Already consumed where exact-underlying attachment is allowed; does not cover intraday/monthly, Kraken, missing exact instruments, or rejected near-underlying slots. |
| [HF TSIE market-regime dataset](https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset) | `rejected_proxy_or_narrow_panel` | Narrow IDX/240m/1d source; previous gates found it not attachable to the full MainRegimeV2 provider/instrument/timeframe matrix. |
| [TradingView Turbo Market Regime Detector](https://www.tradingview.com/script/2pH4ZOw5-Turbo-Market-Regime-Detector-QuantAlgo/) | `rejected_indicator_proxy_only` | Generates states from price/volume math and technical indicators; no independent source labels or positive/negative event windows. |
| [TradingView Regime Compass](https://www.tradingview.com/script/jV0JbXq2-Regime-Compass-The-Fearless-Trader/) | `rejected_indicator_proxy_only` | Uses ADX, Bollinger position, ATR volatility, Hurst exponent, and volume profile; feature/proxy logic only. |
| [QuantHQ market-regime HMM API](https://docs-api.quanthq.io/client-api/examples/market-regime) | `rejected_authenticated_model_signal_not_source_labels` | Authenticated model-generated signal API; not accessible here and not an independent full-matrix label panel. |
| [arXiv hierarchical HMM market-regime paper](https://arxiv.org/abs/2310.03761) | `rejected_methodology_only_hmm_labels` | Methodology/provenance only; no downloadable exact-underlying source-label panel. |
| [ScienceDirect Ethereum market-regime paper](https://www.sciencedirect.com/science/article/pii/S0378437125008580) | `rejected_methodology_or_model_inferred_labels` | Research/modeling source result; no attachable MainRegimeV2 source-label panel for required instruments/timeframes. |

## Accounting

- New accepted source-label slots: `0`.
- Missing/rejected parent-root source-label slots remain `564`.
- Existing partial public sources and indicator/model/methodology sources cannot satisfy the full-cycle/full-species parent-root gate.

## Next Action

The next useful path is acquisition or authenticated export of exact-underlying parent-root label panels, or authenticated direct `Manipulation` rows. Do not spend more cycles on public indicator/model/methodology pages as completion evidence.
