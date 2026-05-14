# Zenodo DEX Self-Trade Direct Gate

Run ID: `20260511T101019+0800-codex-zenodo-dex-selftrade-direct-gate`

## Result

- Candidate rows: `22671`.
- Positive self-trade rows: `12671`.
- Negative control rows: `10000`.
- Calibration Wilson95 LCB/support: `0.998671` / `2887`.
- Test Wilson95 LCB/support: `0.998675` / `2896`.
- Accepted direct `Manipulation` 95: `true`.
- Accepted direct `Manipulation` rows added: `12671`.
- Accepted parent-root slots added: `0`.
- Gate result: `accepted_95_direct_order_lifecycle_self_trade_bounded`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Scope

This is direct order-lifecycle wash-trade/self-trade evidence from Zenodo DEX rows.
It does not fill `Bull`, `Bear`, `Sideways`, or `Crisis` parent-root slots and it
does not close all manipulation varieties.
