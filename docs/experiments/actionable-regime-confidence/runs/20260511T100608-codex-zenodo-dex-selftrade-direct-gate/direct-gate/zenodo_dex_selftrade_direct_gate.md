# Zenodo DEX Self-Trade Direct Gate

Run ID: `20260511T100608+0800-codex-zenodo-dex-selftrade-direct-gate`

## Result

- Rows exported: `2000`.
- Positive self-trade rows: `1000`.
- Same-venue non-self negative controls: `1000`.
- Minimum calibration/test per-venue/class Wilson95 LCB: `0.675592`.
- Accepted direct self-trade slice at 95: `false`.
- Accepted direct `Manipulation` rows added: `0`.
- Accepted parent-root slots added: `0`.
- Full Board A goal achieved: `false`.
- Gate result: `blocked_zenodo_dex_selftrade_slice_below_95`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Scope

This is real DEX order-lifecycle evidence for a bounded self-trade/wash-trade slice. It does not close `Bull`, `Bear`, `Sideways`, `Crisis`, or full manipulation-variety coverage.
