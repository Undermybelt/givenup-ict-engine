# Source-Window Attachability v1

Run ID: `20260511T122239+0800-codex-source-window-attachability-v1`

This run consumes the `120900` source-window seed and the current v3 missing-slot request. It does not run another broad search and it does not promote proxies.

## Result

- Current missing/rejected slots: `564`.
- Missing by root: `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141`.
- Strict native no-projection slots added: `0`.
- Approved crosswalk slots added: `0`.
- Candidate slots pending explicit crosswalk decision: `63`.
- Still blocked without crosswalk or a Sideways source: `501`.

No 95% gate is claimed here. This is an attachability preflight.

## Crosswalk Layers

Useful pending decisions:

- `Yardeni S&P 500 -> ^GSPC` calendar-window projection for intraday/monthly `Bull` and `Bear`: `14` candidate slots.
- `NBER contraction months -> ^GSPC Crisis`: `7` candidate slots.
- `Yardeni S&P 500 -> SPY/ES=F` tradable proxy projection for `Bull` and `Bear`: `28` candidate slots.
- `NBER contraction months -> SPY/ES=F Crisis`: `14` candidate slots.

Fail-closed until explicit decision:

- `Sideways`: no dated source window in the seed. It needs a dated range-bound source or owner-approved adjudication protocol.
- `QQQ/^NDX/NQ=F`, `^DJI/DIA/YM=F`, commodities, volatility, and crypto: not exact same-underlying. They need separate source labels or an explicit broader cross-market projection decision.

## Why This Matters

The useful bottleneck is no longer "search more random datasets." It is now explicit crosswalk governance:

1. Which source-window families may project across timeframe?
2. Which instruments count as the same underlying or tradable proxy?
3. Is NBER macro contraction an acceptable `Crisis` label for market bars?
4. What source/protocol defines `Sideways` without turning it into an OHLCV proxy?

Until those decisions are made, the source-window seeds remain positive acquisition material but cannot close the full-matrix objective.

## Safety

- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
- Proxy promoted: false.
