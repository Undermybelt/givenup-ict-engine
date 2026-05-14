# MainRegimeV2 Lock After V7 Drift

Run ID: `20260511T103015+0800-codex-mainregimev2-lock-after-v7-drift`

## Decision

- Active Board A taxonomy is restored to `MainRegimeV2`.
- Main price roots are exactly `Bull`, `Bear`, `Sideways`, and `Crisis`; `UnknownOrMixed` remains residual only.
- `Manipulation` remains a separate direct-event/order-flow/order-lifecycle class or overlay.
- `ActionableRegimeRootV7` is superseded drift/provenance only because no visible user instruction supersedes the MainRegimeV2 correction in this thread.

## Direct Manipulation Update

- Zenodo DEX direct gate: `20260511T101019+0800-codex-zenodo-dex-selftrade-direct-gate`.
- Gate result: `accepted_95_direct_order_lifecycle_self_trade_bounded`.
- Accepted direct `Manipulation` rows added: `12671`.
- Scope: bounded direct order-lifecycle self-trade evidence only; it does not close `Bull`/`Bear`/`Sideways`/`Crisis` parent-root slots or all manipulation varieties.

## Accounting

- Accepted parent-root slots added: `0`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
