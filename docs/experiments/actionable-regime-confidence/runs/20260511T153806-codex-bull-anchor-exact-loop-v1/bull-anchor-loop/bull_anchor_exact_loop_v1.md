# Bull Anchor Exact Loop v1

Run ID: `20260511T153806+0800-codex-bull-anchor-exact-loop-v1`

This loop follows the positive next step left by the PFE/TSLA rare-root loop. It does not perform another source sweep.
It consumes the existing accepted strict exact-source `1h` rows from `141910`.

## Result

- Selected pair: `GE+GS`.
- Purpose: close abundant `Bull` exact-source supply after `PFE+TSLA` already closed `Bear`, `Sideways`, and `Crisis`.
- Selected pair rows: `8`.
- Accepted strict Bull rows: `2`.
- Non-target blocked rows retained: `6`.
- Accepted roots this loop: `Bull`.
- Combined with `PFE+TSLA` rare-root loop, covered active `MainRegimeV2` price roots: `Bear, Bull, Crisis, Sideways`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `bull_anchor_exact_loop_v1=accepted2_bull_anchor_no_new_download`.

## Accepted Bull Rows

| Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |
|---|---|---:|---:|---:|---:|
| `GE` | `Bull` | 184 | 0.9795494624 | 196 | 0.9807774681 |
| `GS` | `Bull` | 206 | 0.9816935183 | 179 | 0.97899022 |

## Combined Price-Root Supply

| Source Loop | Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |
|---|---|---|---:|---:|---:|---:|
| `bull_anchor_exact_loop_v1` | `GE` | `Bull` | 184 | 0.9795494624 | 196 | 0.9807774681 |
| `bull_anchor_exact_loop_v1` | `GS` | `Bull` | 206 | 0.9816935183 | 179 | 0.97899022 |
| `pfe_tsla_rare_root_exact_loop_v1` | `PFE` | `Bear` | 109 | 0.9659570262 | 74 | 0.9506502206 |
| `pfe_tsla_rare_root_exact_loop_v1` | `PFE` | `Sideways` | 74 | 0.9506502206 | 92 | 0.9599186107 |
| `pfe_tsla_rare_root_exact_loop_v1` | `TSLA` | `Crisis` | 146 | 0.9743631779 | 146 | 0.9743631779 |

## Boundary

- This is positive `MainRegimeV2` price-root supply, not a direct `Manipulation` label.
- Direct `Manipulation` remains a separate row-intake lane waiting for external row-level positive and matched-negative exports.
- Do not spend the next active Board A loop on broad negative source sweeps; run a completion audit that separates price-root evidence from the direct row-intake blocker.
