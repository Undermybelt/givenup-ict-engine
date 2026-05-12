# Source Label Single-Atom Qualifier Scan v1

Run id: `20260512T044701-codex-source-label-single-atom-qualifier-scan-v1`

Gate result: `source_label_single_atom_qualifier_scan_v1=single_atom_scored_no_full_acceptance`

## Result

- Rows scored: `248440`.
- Rule search: single-feature threshold atoms using sorted cumulative counts.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted single-atom confidence labels: `[]`.
- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Min Support | Min Wilson95 | Rule | Blockers |
|---|---|---:|---:|---|---|
| `Bear` | `false` | `455` | `0.4249084736` | `vix >= 29.98999977` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Bull` | `false` | `12677` | `0.5353234712` | `regime_confidence >= 0.6` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Crisis` | `false` | `520` | `0.4324193032` | `volatility >= 0.5480683811` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Sideways` | `false` | `5770` | `0.3488806669` | `regime_confidence >= 0.75` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |

## Boundary

This is a diagnostic qualifying-condition scan over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
