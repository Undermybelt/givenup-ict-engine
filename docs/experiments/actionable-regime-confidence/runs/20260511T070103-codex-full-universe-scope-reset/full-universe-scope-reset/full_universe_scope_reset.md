# Full-Universe Scope Reset

Run id: `20260511T070103+0800-codex-full-universe-scope-reset`

## Decision

- New expanded requirement: `full species / full cycles` coverage before final completion.
- Current Board A cross-context gate remains useful baseline evidence.
- Later taxonomy correction `20260511T070241+0800` narrows main price-regime roots to `Bull`, `Bear`, `Sideways`, and `Crisis`; `Manipulation` is a separate direct-event overlay gate.
- Goal achieved under the expanded requirement: `false`.
- Gate result: `blocked_full_universe_full_cycle_not_yet_attempted`.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Named TODO board remains the active contract | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | `pass` |
| Every active main price root has prior >=95 cross-context evidence | `20260511T065805-codex-cross-market-timeframe-completion-audit` | `pass_but_prior_scope_only` |
| All available species/instruments were tried | no provider-universe coverage matrix yet | `blocked` |
| All available cycles/timeframes were tried | current packets cover only selected cycles per root | `blocked` |
| Unsupported provider/timeframe/instrument cells are explained | no full coverage matrix with unsupported reasons yet | `blocked` |
| No thresholds relaxed / no trade usability claimed | prior packet flags | `pass` |

## Current Coverage Versus Expanded Scope

| Root | Prior 95 Status | Covered Contexts | Covered Cycles | Expanded-Scope Status |
|---|---|---|---|---|
| `Bull` | accepted_95 | index, single_stock | `1d`, `1w` | not full-universe |
| `Bear` | accepted_95 | crypto, equity_etf | `1d`, `1w` | not full-universe |
| `Sideways` | accepted_95 | crypto, equity_etf | `1d`, `1w` | not full-universe |
| `Crisis` | accepted_95 | CME/local, IBKR ETF, Kraken crypto, yfinance ETF/crypto/futures | `15m`, `1h` | not full-cycle |
| `Manipulation` overlay | accepted_95 | Telegram event, cross-coin, cross-channel | chronological event train/cal/test | not a main price root; direct-event universe needs explicit overlay coverage accounting |

## Next

1. Build a provider-universe manifest across yfinance, IBKR/local cache, Kraken, TradingViewRemix if reachable, and Auto-Quant cache.
2. Define the timeframe/cycle ladder per provider, including unsupported cells.
3. Run the first active-main-root coverage matrix without relaxing thresholds, and keep `Manipulation` in a separate overlay coverage lane.

Do not mark Board A complete for the expanded objective until that matrix exists and passes.
