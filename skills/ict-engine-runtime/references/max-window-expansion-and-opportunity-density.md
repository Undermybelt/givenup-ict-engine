# Max-window expansion and opportunity density

Session findings for IBKR/Auto-Quant expansion runs.

## Retrieval ceiling discovered
- `ibkr-historical` can often return the maximum available lookback per asset class, but the ceiling differs by asset and bar size.
- Examples from this session:
  - `SPY` 5m: 1Y available; 10Y 5m timed out / returned empty.
  - `SPY` 1d: 10Y available.
  - `AAPL` and `NVDA` 1d: 10Y available.
  - `ES` 5m: 60D available.
  - `NQ` 5m: 60D available.
  - `GC` 5m: 60D available.
- Rule: when the user asks for "10Y if possible", probe the largest usable duration per asset/bar size, not just a fixed target duration.

## Contract quirks
- Futures historical pulls need a resolved contract, usually with `--last-trade-date` and often `--multiplier`.
- Stock pulls can work with `--primary-exchange`; some stocks still return empty at 5m for long windows.
- If a pull is empty or times out, widen only after checking whether the duration is already near the provider ceiling for that asset/bar size.

## Signal-density lesson
- A very high win rate on a short window usually means the signal is too sparse, not necessarily better.
- In the ES strict gamma-pin test, the strict filter hit rate was only `19 / 2736 = 0.694%` on an 11.87-day window; after expanding to 60D and 1Y/10Y ceilings, strict gamma-pin density stayed extremely low:
  - ES 5m strict gamma bars: 14 / 5400 = 0.259%
  - NQ 5m strict gamma bars: 9 / 5400 = 0.167%
  - GC 5m strict gamma bars: 6 / 5400 = 0.111%
  - SPY 5m strict gamma bars: 47 / 19470 = 0.241%
- Rule: if win rate is high but trade count is tiny, treat it as sparse opportunity density first, not as a durable edge.

## Practical expansion heuristic
1. Pull the largest usable duration per asset/bar size.
2. Recompute opportunity density for the strict signal set.
3. Compare strict vs relaxed thresholds before changing the strategy logic.
4. Prefer more data plus stable thresholds over harvesting one-off short-window winners.
