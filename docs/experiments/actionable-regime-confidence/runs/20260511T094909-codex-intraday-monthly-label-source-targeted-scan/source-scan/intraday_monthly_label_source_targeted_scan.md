# Intraday/Monthly Label Source Targeted Scan

Run ID: `20260511T094909+0800-codex-intraday-monthly-label-source-targeted-scan`

## Purpose

Search specifically for exact-underlying intraday/monthly parent-root labels after the daily Kaggle panel failed to fill the current missing slots.

## Queries

- `"stock_market_regimes" "1m" kaggle "regime_label"`
- `site:kaggle.com/datasets "market regimes" "1m" "Bull" "Bear" "Sideways"`
- `"market regime" "intraday" "Kaggle"`
- `"regime_label" "Bull" "Bear" "Sideways" "1m"`

## Candidate Classification

| Source | Decision | Reason |
|---|---|---|
| `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset` | rejected | IDX-only, rule-based OHLCV/technical labels; prior Board A audits added zero accepted MainRegimeV2 slots. |
| `https://www.kaggle.com/datasets/vivek468/sip-dataset-nifty-banknifty-gold-and-silver` | rejected | Monthly OHLCV/calculated metrics for Indian ETF proxies; no explicit parent-root source labels for current slots. |
| `https://huggingface.co/JonusNattapong/xauusd-trading-ai-smc-v2` | rejected | Model artifacts and validation claims, not independent downloadable parent-root label rows. |
| `https://www.technical-analysis-pro.com/strategies-xgboost-trading-gradient-boosting-python/` | rejected | Methodology article; no exact-underlying source-label panel. |

## Result

- Accepted parent-root label sources: `0`
- Accepted parent-root slots added: `0`
- Accepted direct `Manipulation` rows added: `0`
- Gate result: `blocked_targeted_intraday_monthly_scan_no_exact_parent_root_label_panel`
- Runtime code changed: false
- Thresholds relaxed: false
- Raw data committed: false
- Trade usable: false

## Next Action

A new source must be a real row-level export for current missing instruments/timeframes or direct `Manipulation` rows; proxy, model, methodology, or off-contract data must stay rejected.
