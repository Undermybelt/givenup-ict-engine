# 104703 BTC EMA/RSI Full-Chain Registration v1

Run id: `20260512T105445+0800-codex-104703-btc-ema-rsi-fullchain-registration-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1`

Gate: `104703_btc_ema_rsi_fullchain_registration_v1=provider_owned_noncanary_profitable_single_provider_window_downstream_fail_closed_no_promotion`

## Readback

The source root exercised the ordered chain through provider-owned Auto-Quant output, real-trade ingest, Pre-Bayes status, policy/CatBoost status, structural path-ranking export, structural bundle, execution candidate, and full workflow. All source exit files inspected were `0`.

Auto-Quant branch:

| Branch | Provider scope | Trades | Total Profit % | Sharpe | Win Rate % | Profit Factor | Max DD % |
|---|---|---:|---:|---:|---:|---:|---:|
| `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12` | Binance BTCUSDT 1h only | 42 | 22.60 | 9.2978 | 69.0476 | 2.9309 | -2.9274 |

This is a better non-canary datapoint than the forced-entry/canary runs, but it is still only one provider, one instrument, one timeframe, and one short provider window.

## Downstream Gate

- `auto-quant-results-import`, `auto-quant-prior-init`, `auto-quant-ingest-real-trades`, `pre-bayes-status`, `policy-training-status`, structural target export, structural bundle, execution candidate, and full workflow all exited `0`.
- Policy training stayed not ready: entry model matched rows `0`.
- CatBoost/path-ranking stayed unavailable: runtime selection disabled, trainer artifact missing/not ready, raw scored mature rows `0`.
- Execution tree stayed observe/fail-closed: execution candidate `ready=false`, `actionable=false`, and full workflow `closed_loop_branch_admission.status=fail_closed`.
- The six-provider matrix is incomplete: this slice did not invoke IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, or Bybit.

## Non-Promotion

- Accepted rows added: `0`
- Mature rooted branch observations added: `0`
- Source/control evidence acquired: `false`
- Explicit selected-history: `false`
- Canonical merge: `false`
- Six-provider matrix satisfied: `false`
- Cross-market/timeframe/period validation: `false`
- Selected-data AutoQuant promotion: `false`
- Downstream promotion: `false`
- Strict full objective: `false`
- Trade usable: `false`
- Promotion allowed: `false`
- `update_goal=false`

## Next

Do not promote the single-provider/single-window `104703` branch. Continue from cross-provider/cross-window validation plus source/control unlock, or a rooted branch with enough mature observations that survives Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree.
