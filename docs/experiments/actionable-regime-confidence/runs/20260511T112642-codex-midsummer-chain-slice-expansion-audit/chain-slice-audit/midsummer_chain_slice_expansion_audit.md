# Midsummer Chain Slice Expansion Audit

Run ID: `20260511T112642+0800-codex-midsummer-chain-slice-expansion-audit`

## Scope

This audit reuses the already downloaded Zenodo Midsummer ZIP under `/tmp` and checks whether the direct wash-maker Dune export contains additional per-chain accepted 95% slices beyond the BSC slice already written to the Board A cursor.

## Method

- Unit: `maker-token-day`.
- Positive: same `platform/address/day` paired controls and `is_both_buyer_seller == True`.
- Negative: same `platform/address/day` paired controls and `is_both_buyer_seller == False`.
- Split: per-platform chronological 60/40 by paired token-day.
- Gate: minimum calibration/test positive/negative Wilson95 LCB >= `0.95`.
- Raw data committed: false.

## Platform Summary

| Platform | Accepted 95 | Already Ledgered | Paired Token-Days | Rows | Positives | Negatives | Min Split/Class LCB | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `base` | `true` | `false` | 84 | 8618 | 556 | 8062 | `0.98008` | accepted |
| `bsc` | `true` | `true` | 298 | 4864 | 1870 | 2994 | `0.995736` | accepted |
| `ethereum` | `true` | `false` | 95 | 977 | 265 | 712 | `0.967945` | accepted |
| `solana` | `true` | `false` | 639 | 44669 | 4872 | 39797 | `0.998285` | accepted |

## Decision

- Accepted parent-root slots added: `0`.
- New accepted direct `Manipulation` rows added: `5693`.
- New accepted platforms: `base, ethereum, solana`.
- Gate result: `accepted_95_additional_midsummer_chain_wash_slices`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

This remains direct `Manipulation` wash-trading evidence only. It does not close any `Bull`/`Bear`/`Sideways`/`Crisis` parent-root slot and does not complete broader direct-manipulation variety coverage.
