# Positive Target Selector v1

Run ID: `20260511T142858+0800-codex-positive-target-selector-v1`

This is a selector, not another source sweep. It consumes the already accepted strict exact-source `1h` rows from `141910` and ranks only positive next targets.

## Result

- Accepted strict rows consumed: `41`.
- Accepted roots present: `Bull, Bear, Sideways, Crisis`.
- Top two-market pair: `PFE+TSLA`.
- Top pair roots: `Bear, Sideways, Crisis`.
- Top pair rare roots: `Bear, Crisis`.
- Two-market pair can cover all four roots under strict rows: `false`.
- Gate result: `positive_target_selector_v1_rare_root_anchors_selected_no_new_confidence_gate`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Top Pairs

| Rank | Pair | Roots | Rare Roots | Support Floor Min | Score |
|---:|---|---|---|---:|---:|
| 1 | `PFE+TSLA` | `Bear,Sideways,Crisis` | `Bear,Crisis` | 74 | 11429.400 |
| 2 | `INTC+PFE` | `Bear,Sideways,Crisis` | `Bear,Crisis` | 74 | 11427.500 |
| 3 | `AMD+PFE` | `Bear,Sideways,Crisis` | `Bear,Crisis` | 74 | 11424.200 |
| 4 | `NKE+TSLA` | `Bear,Crisis` | `Bear,Crisis` | 117 | 9326.300 |
| 5 | `COP+TSLA` | `Bear,Crisis` | `Bear,Crisis` | 112 | 9325.800 |
| 6 | `INTC+NKE` | `Bear,Crisis` | `Bear,Crisis` | 117 | 9324.400 |
| 7 | `COP+INTC` | `Bear,Crisis` | `Bear,Crisis` | 112 | 9323.900 |
| 8 | `SBUX+TSLA` | `Bear,Crisis` | `Bear,Crisis` | 93 | 9323.900 |

## Root Anchors

| Root | Best Anchors |
|---|---|
| `Bull` | `GE`(184), `GS`(179), `JPM`(170), `MS`(169), `WFC`(163) |
| `Bear` | `NKE`(117), `COP`(112), `SBUX`(93), `PFE`(74) |
| `Sideways` | `MCD`(102), `CVX`(98), `DIS`(80), `MSFT`(77), `VZ`(76) |
| `Crisis` | `TSLA`(146), `INTC`(127), `AMD`(94) |

## Next

- Use `PFE+TSLA` as the next rare-root exact-source loop: `PFE` supplies strict `Bear` and `Sideways`; `TSLA` supplies strict `Crisis`.
- Keep `Bull` separate because it is already abundant; forcing all four roots into a two-market strict loop creates a false bottleneck.
- Do not return to NQ/QQQ proxy work unless a Nasdaq-100-grade source-label panel or explicit owner-approved `^IXIC` policy appears.
