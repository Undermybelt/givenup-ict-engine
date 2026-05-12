# Full-Cycle Full-Universe Gap Audit

Run id: `20260511T070405+0800-codex-full-cycle-full-universe-gap-audit`

Goal achieved: `false`

## Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Named TODO board remains the active contract | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | PASS |
| Previously accepted sampled 95% root evidence still exists | `Accepted root artifacts` | PASS |
| Each bar root is validated on every observed accepted bar timeframe | `observed_timeframes=['15m', '1d', '1h', '1w']` | FAIL |
| Each bar root is validated on every observed accepted market context/instrument family | `observed_contexts=['CME_futures_local', 'IBKR_US_ETF', 'Kraken_crypto', 'crypto', 'equity_etf', 'index', 'single_stock', 'yfinance_ETF', 'yfinance_US_ETF', 'yfinance_crypto', 'yfinance_futures']` | FAIL |
| Direct-input-gated Manipulation is accepted across direct manipulation varieties, not only one crypto Telegram event feed | `Mehrnoom accepted; SystemsLab/Mendeley/Bayi/Kaggle NFT/raw-message/Twitter social diagnostics remain blocked or caveat-only` | FAIL |

## Observed Evidence Universe

- Bar timeframes: `15m, 1d, 1h, 1w`
- Bar market contexts: `CME_futures_local, IBKR_US_ETF, Kraken_crypto, crypto, equity_etf, index, single_stock, yfinance_ETF, yfinance_US_ETF, yfinance_crypto, yfinance_futures`
- Bar instruments: `52` observed accepted instruments.
- Direct manipulation accepted feed: `Mehrnoom/Mirtaheri Telegram pump-attempt events`.

## Root Gaps

| Root | Sampled 95 Preserved | Missing Observed Timeframes | Missing Observed Contexts | Missing Instrument Count |
|---|---:|---|---|---:|
| `Bull` | `true` | `15m, 1h` | `CME_futures_local, IBKR_US_ETF, Kraken_crypto, crypto, equity_etf, yfinance_ETF, yfinance_US_ETF, yfinance_crypto, yfinance_futures` | 16 |
| `Bear` | `true` | `15m, 1h` | `CME_futures_local, IBKR_US_ETF, Kraken_crypto, index, single_stock, yfinance_ETF, yfinance_US_ETF, yfinance_crypto, yfinance_futures` | 46 |
| `Sideways` | `true` | `15m, 1h` | `CME_futures_local, IBKR_US_ETF, Kraken_crypto, index, single_stock, yfinance_ETF, yfinance_US_ETF, yfinance_crypto, yfinance_futures` | 40 |
| `Crisis` | `true` | `1d, 1w` | `crypto, equity_etf, index, single_stock` | 45 |

## Direct Manipulation Gap

- Sampled accepted feed remains 95% accepted: `true`.
- Full-universe gap: accepted feed is only crypto Telegram event confirmation; other direct manipulation varieties remain blocked or diagnostic-only.

## Next Action

- Run a bounded full-matrix batch across available providers/instruments/timeframes, then keep Manipulation split by direct evidence variety; do not report full-cycle/full-universe completion until the matrix is accepted.
