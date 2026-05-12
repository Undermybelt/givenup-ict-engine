# Current Public Source Delta Audit

Run ID: `20260511T104752+0800-codex-current-public-source-delta-audit`

Board cursor readback: `20260511T103333+0800-codex-mainregimev2-board-a-top-relock`

## Scope

This slice audited fresh public Kaggle and Hugging Face search results for sources that could fill the current `MainRegimeV2` missing-slot contract without touching the shared board cursor.

The active missing-slot contract is still:

- Missing slots: `564`
- Providers: `yfinance=456`, `kraken_public_lowpollution_http=108`
- Roots: `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141`
- Required provenance: exact provider or exact underlying, exact timeframe, source-backed/manual/official root-label windows
- Rejected provenance: HMM/GMM states, OHLCV/technical labels, future-return labels, synthetic rows, methodology-only pages, provider/venue proxies without explicit approval

## Candidate Decisions

| Source | Shape | Decision |
|---|---|---|
| `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | BTCUSD/BTCUSDT `5m`/`15m` rows with OHLCV, indicators, HMM states, and post-hoc labels such as `Squeeze`, `Range`, `Strong Trend` | Rejected: HMM-derived and not `Bull`/`Bear`/`Sideways`/`Crisis`; exchange unspecified |
| `sergionefedov/crypto-microstructure` | Synthetic crypto cycle/microstructure set with BTC/ETH/SOL, bear/crab/bull periods, funding/liquidations/spreads | Rejected: synthetic, not real Kraken labels or real direct `Manipulation` rows |
| `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes` | Daily yfinance/FRED feature panel for SPY/QQQ/GLD/USO/BTC and macro stress fields | Rejected: feature sidecar only, no source-backed parent-root labels |
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | NIFTY 500 daily HMM labels and technical features | Rejected: off-contract instruments and HMM-derived labels |
| `nudratabbas/tech-titans-volatility-and-trend-analysis-data` | Daily tech-stock trend labels from moving-average crossovers | Rejected: wrong instruments, no `Crisis`, technical-label provenance |
| `thisathdamiru/bybit-multi-crypto-historical-data-2020-2026` | Bybit multi-timeframe OHLCV with optional future-return labels | Rejected: venue mismatch, raw OHLCV/future-return labels |
| `nickdatak/us-market-regimes-dataset-1995-2024` | Weekly S&P/VIX/yield-spread feature table for GMM/HMM comparison | Rejected: unsupervised discovery features, not independent root labels |
| `ClarusC64/market-regime-transition-breakpoint-mapping-v0.1` | Benchmark-style macro transition rows with regime basins and probabilities | Rejected: no exact instrument/provider/timeframe rows; labels are task basins |

## Result

- Accepted parent-root slots added: `0`
- Accepted direct `Manipulation` rows added: `0`
- Gate result: `blocked_current_public_source_delta_no_attachable_mainregimev2_labels`
- Runtime code changed: false
- Thresholds relaxed: false
- Raw data committed: false
- Trade usable: false

## Next Action

Public generic regime-search surfaces are now low-yield for the current missing denominator. The next useful acquisition path is one of:

- exact provider/instrument/timeframe label-window export from an authenticated/private source;
- explicit owner-approved provider/venue crosswalk for crypto labels before using non-Kraken BTC/ETH/SOL regime datasets;
- a new real direct `Manipulation` source with timestamped positives and same-asset/venue negative controls if parent-root acquisition remains blocked.
