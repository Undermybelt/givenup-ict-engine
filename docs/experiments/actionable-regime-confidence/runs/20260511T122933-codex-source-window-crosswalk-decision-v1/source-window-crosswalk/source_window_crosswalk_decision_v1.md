# Source-Window Crosswalk Decision v1

Run ID: `20260511T122933+0800-codex-source-window-crosswalk-decision-v1`

This run converts the `122239` pending crosswalk candidates into a narrow board-local crosswalk decision. It does not claim a 95% confidence gate and does not make the regimes trade-usable.

## Approved

- `Yardeni S&P 500 -> ^GSPC` intraday/monthly `Bull/Bear`: `14` source-label slots.
- `NBER contraction months -> ^GSPC Crisis`: `7` source-label slots.
- `Yardeni S&P 500 -> SPY/ES=F` intraday/monthly `Bull/Bear`: `28` source-label slots.
- `NBER contraction months -> SPY/ES=F Crisis`: `14` source-label slots.

Total approved source-label slots: `63`.

Counts:
- `Bull`: `21`.
- `Bear`: `21`.
- `Crisis`: `21`.
- `Sideways`: `0`.
- `^GSPC`: `21`.
- `SPY`: `21`.
- `ES=F`: `21`.

## Still Blocked

- `Sideways`: no dated source window or approved adjudication protocol.
- `QQQ`, `^NDX`, `NQ=F`, `^DJI`, `DIA`, `YM=F`: broader index-family projection rejected by default.
- Commodities, volatility, crypto, Kraken cells: rejected by default because S&P 500/NBER windows are not direct labels for those instruments.

## Boundary

This is source-label attachment only. It is not a calibrated 95% regime-confidence pass and does not satisfy full-cycle/full-universe completion.

Safety:
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Proxy promoted beyond declared crosswalk: false.
- Trade usable: false.
