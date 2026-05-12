# Mehrnoom Telegram Direct Manipulation Gate

Run id: `20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate`

Purpose: test whether public Telegram pump-attempt labels can close the direct-input-gated `Manipulation` root without using OHLCV proxy features.

## Rule

`classified_telegram_coin_pump_event_present == 1`

This is a direct social/event confirmation rule. It is not a price/volume proxy and it is not a learned market-feature rule.

## Source

- Repo: `https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump`
- Paper: `https://arxiv.org/abs/1902.03110`
- Raw data root: `/private/tmp/ict-regime-mehrnoom-pump-dump`
- Raw data committed: false

## Calibration

| Split | Rows | Support | Successes | False Positives | Negative Controls | Precision | Wilson95 LCB | Coverage | Coins | Channels |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 73776 | 34165 | 34165 | 0 | 39611 | 1.000000 | 0.999888 | 0.463091 | 466 | 139 |
| calibration | 24592 | 14516 | 14516 | 0 | 10076 | 1.000000 | 0.999735 | 0.590273 | 364 | 147 |
| test | 24592 | 12834 | 12834 | 0 | 11758 | 1.000000 | 0.999701 | 0.521877 | 365 | 167 |

## Result

- Accepted 95: `true`
- Gate result: `accepted_manipulation_95_direct_event_sourcebacked`
- Positive events after de-duplication: `61515`
- Same-coin non-event controls: `61445`
- Unique positive coins/channels: `542` / `209`
- Runtime code changed: false
- Thresholds relaxed: false
- Fresh calibration rerun: true
- Trade usable: false

## Caveats

- This closes only an event-confirmed direct `Manipulation` gate. It does not predict pump events before the Telegram source emits a classified event.
- It should route downstream to suppression/abstain/cooldown behavior, not to automatic trade entry.
- Kamps/OSF remains fail-closed for this root because its notebook derives labels from OHLCV thresholds rather than independent direct event labels.
