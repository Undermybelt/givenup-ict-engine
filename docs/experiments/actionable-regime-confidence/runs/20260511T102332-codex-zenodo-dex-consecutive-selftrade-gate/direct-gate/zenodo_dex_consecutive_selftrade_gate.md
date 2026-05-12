# Zenodo DEX Consecutive Self-Trade Gate

Run ID: `20260511T102332+0800-codex-zenodo-dex-consecutive-selftrade-gate`

## Result

- Consecutive rows streamed: `200000`.
- Positive self-trade rows: `12671`.
- Negative controls: `187329`.
- Minimum calibration/test positive-or-negative Wilson95 LCB: `0.979218`.
- Minimum calibration/test positive support: `181`.
- Minimum calibration/test negative support: `32858`.
- Gate result: `accepted_direct_manipulation_self_trade_consecutive_95_context_only_full_goal_blocked`.
- Accepted parent-root slots added: `0`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Boundary

This is direct order-lifecycle evidence for a self-trade/wash-trade slice only.
It does not fill `Bull`, `Bear`, `Sideways`, or `Crisis`.

## Artifacts

- Audit JSON: `direct-gate/zenodo_dex_consecutive_selftrade_gate.json`
- Sample rows: `direct-gate/direct_manipulation_rows_zenodo_dex_consecutive_sample.csv`
- Assertions: `checks/zenodo_dex_consecutive_selftrade_gate_assertions.out`
