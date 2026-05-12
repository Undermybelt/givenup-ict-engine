# PFE/TSLA Rare-Root Exact Loop v1

Run ID: `20260511T144604+0800-codex-pfe-tsla-rare-root-exact-loop-v1`

This loop executes the positive selector's next target without another provider download.
It consumes accepted strict exact-source `1h` rows from `141910`.

## Result

- Selected pair: `PFE+TSLA`.
- Purpose: close rare-root exact-source supply for `Bear`, `Sideways`, and `Crisis` in a two-market loop.
- Selected pair rows: `8`.
- Accepted strict rows: `3`.
- Blocked non-target rows retained: `5`.
- Accepted roots: `Bear, Sideways, Crisis`.
- Rare roots closed: `Bear, Sideways, Crisis`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `pfe_tsla_rare_root_exact_loop_v1=accepted3_rare_roots_bear_sideways_crisis_no_new_download`.

## Accepted Rows

| Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |
|---|---|---:|---:|---:|---:|
| `PFE` | `Bear` | 109 | 0.965957 | 74 | 0.950650 |
| `PFE` | `Sideways` | 74 | 0.950650 | 92 | 0.959919 |
| `TSLA` | `Crisis` | 146 | 0.974363 | 146 | 0.974363 |

## Non-Target Blocked Rows

- `PFE:Bull`, `PFE:Crisis`, `TSLA:Bull`, `TSLA:Bear`, and `TSLA:Sideways` remain blocked in this pair.
- That is expected: this loop is the rare-root pair selected by `142858`, not a forced all-root pair.

## Next

- Use a separate abundant-root exact-source pair for `Bull` if a two-market loop artifact is still needed.
- Then run a completion audit against full objective coverage instead of rerunning proxy/no-source scans.
