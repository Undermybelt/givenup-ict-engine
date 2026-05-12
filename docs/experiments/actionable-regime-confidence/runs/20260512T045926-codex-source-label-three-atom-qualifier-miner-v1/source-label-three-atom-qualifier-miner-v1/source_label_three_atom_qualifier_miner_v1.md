# Source Label Three-Atom Qualifier Miner v1

Run id: `20260512T045926-codex-source-label-three-atom-qualifier-miner-v1`

Gate result: `source_label_three_atom_qualifier_miner_v1=three_atom_scored_no_full_acceptance`

## Result

- Rows scored: `248440`.
- Rule search: bounded single/two/three-atom conjunctions selected by calibration Wilson95 ranking.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted three-atom confidence labels: `[]`.
- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Min Support | Min Wilson95 | Kind | Rule | Blockers |
|---|---|---:|---:|---|---|---|
| `Bear` | `false` | `26` | `0.6435280915` | `3_atom_conjunction` | `volatility >= 0.9564397693 AND regime_confidence <= 0.385 AND vix >= 19.45000076` | calibration_wilson95_below_0.95;heldout_market_support_below_50;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_support_below_50;test_wilson95_below_0.95 |
| `Bull` | `false` | `181` | `0.7986296577` | `3_atom_conjunction` | `regime_confidence >= 0.833 AND cpi >= 246.626 AND vix <= 12.89000034` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Crisis` | `false` | `520` | `0.4324193032` | `1_atom_conjunction` | `volatility >= 0.5480683811` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Sideways` | `false` | `3421` | `0.3659108855` | `2_atom_conjunction` | `regime_confidence >= 0.75 AND volatility <= 0.2067864525` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |

## Boundary

This is a diagnostic qualifying-condition miner over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
