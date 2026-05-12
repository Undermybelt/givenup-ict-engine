# Direct Manipulation Variety Matrix v1

Run ID: `20260511T131311+0800-codex-direct-manipulation-variety-matrix-v1`

Board cursor read before write: `20260511T130916+0800-codex-mainregimev2-relock-after-taxonomy-drift-v10`.

This artifact keeps the active price-root axis unchanged: `Bull`, `Bear`, `Sideways`, and `Crisis` remain `MainRegimeV2` price roots. `Manipulation` remains a separate direct-event/order-flow/order-lifecycle/social/on-chain class or overlay.

## Coverage Matrix

| Variety | State | Evidence | Gate | Remaining Gap |
|---|---|---|---|---|
| `pump_dump_telegram_event` | accepted 95 scoped | `20260511T045102` Mehrnoom Telegram gate | accepted; calibration/test LCB >= 0.95; per-regime map records `0.999735` / `0.999701` | Event-confirmed suppression/cooldown only; not order-book behavior. |
| `pump_dump_social_text_or_twitter` | blocked | `20260511T045215`, `20260511T050029` | Twitter best cal/test LCB `0.937652` / `0.815594`; raw social text `0.901875` / `0.881516` | Needs stronger direct controls or feature construction. |
| `dex_self_trade_order_lifecycle` | accepted 95 scoped | `20260511T101019` Zenodo DEX self-trade | `12671` positives, `10000` negatives, cal/test LCB `0.998671` / `0.998675` | Bounded DEX self-trade/wash slice only. |
| `dex_consecutive_self_trade_order_lifecycle` | accepted 95 scoped context | `20260511T102332` consecutive self-trade readback | streamed `200000` rows, min class/split LCB `0.979218` | Confirms self-trade context, not full variety coverage. |
| `midsummer_bsc_wash_maker` | accepted 95 scoped | `20260511T111122` Midsummer BSC wash-maker | `1870` positives, `2994` negatives, min LCB `0.995736` | BSC wash-maker only. |
| `midsummer_multichain_wash_maker` | accepted 95 scoped | `20260511T112642` base/ethereum/solana expansion | new accepted rows `5693`; min LCBs base `0.98008`, ethereum `0.967945`, solana `0.998285` | On-chain wash-maker only. |
| `spoofing_layering_enforcement_cases` | positive-only no 95 gate | `20260511T130457` spoofing appendix inventory | `204` positive cases; accepted 95 gate added `0` | Needs matched negative order-lifecycle/order-book rows. |
| `local_spoofing_repos` | rejected | `20260511T110827` local spoofing audit | accepted rows `0` | Repos had framework/synthetic logic, not replayable real positive/negative rows. |
| `quote_stuffing` | missing | none accepted | none | Need order-message burst rows plus controls. |
| `pinging` | missing | none accepted | none | Need order-lifecycle probe rows plus controls. |
| `bear_raid_or_painting_tape` | missing | none accepted | none | Need direct event/order-flow rows plus non-event controls. |

## Decision

- Accepted scoped direct varieties exist: pump/dump Telegram event, DEX self-trade/order-lifecycle, and Midsummer on-chain wash-maker.
- Full direct `Manipulation` variety coverage is still incomplete.
- Accepted parent-root slots added: `0`.
- Full objective achieved: `false`.
- `update_goal` allowed: `false`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next

Acquire matched negative order-lifecycle/order-book rows for spoofing/layering/quote-stuffing, then run one direct `Manipulation` calibration gate. Do not run another OHLCV proxy scan.
