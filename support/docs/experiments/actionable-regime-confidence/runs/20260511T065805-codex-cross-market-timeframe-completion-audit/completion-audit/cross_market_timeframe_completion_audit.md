# Cross-Market/Timeframe Completion Audit

Run id: `20260511T065805+0800-codex-cross-market-timeframe-completion-audit`

Goal achieved: `true`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Named TODO board is the active contract | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | PASS |
| Every active root regime is audited | `Active MainRegimeV2 Root Ledger plus per-root artifacts` | PASS |
| Every active regime reaches at least 95% calibrated confidence | `calibration/test Wilson 95 lower confidence bound in root artifacts` | PASS |
| Each accepted root has other-market or other-instrument validation | `market contexts and instruments for bar roots; coins/channels for direct Manipulation` | PASS |
| Each accepted root has other-timeframe or separated chronological-period validation | `1d/1w or 15m/1h for bar roots; chronological train/calibration/test event windows for Manipulation` | PASS |
| Sub-regime labels and preflight concepts are not counted as completed roots | `Board guidance and Active MainRegimeV2 Root Ledger` | PASS |
| No trade usability or Auto-Quant profitability is claimed | `per-root artifact flags and board scope` | PASS |

## Root Results

| Root | Evidence Kind | Test Wilson95 | Test Breadth | Status |
|---|---|---:|---|---|
| `Bull` | `bar_cross_market_cross_timeframe` | `0.961930612117` | 2 contexts / 2 timeframes / 36 instruments | PASS |
| `Bear` | `bar_cross_market_cross_timeframe` | `0.992722324561` | 2 contexts / 2 timeframes / 6 instruments | PASS |
| `Sideways` | `bar_cross_market_cross_timeframe` | `0.995568441286` | 2 contexts / 2 timeframes / 12 instruments | PASS |
| `Crisis` | `bar_cross_market_cross_timeframe` | `0.995981071144` | 7 contexts / 2 timeframes / 7 instruments | PASS |
| `Manipulation` | `direct_event_cross_coin_channel_chronological` | `0.999700770660` | 365 coins / 167 channels | PASS |

Notes:
- This audit treats bar-based regimes and direct-event manipulation differently because a Telegram pump event is not a fixed OHLCV bar timeframe.
- Manipulation is accepted only as an event-confirmed suppress/abstain/cooldown gate, not as a pre-event prediction or trade-entry signal.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
