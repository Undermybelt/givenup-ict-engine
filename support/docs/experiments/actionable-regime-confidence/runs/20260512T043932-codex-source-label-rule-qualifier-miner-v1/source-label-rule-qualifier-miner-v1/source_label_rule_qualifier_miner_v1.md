# Source Label Rule Qualifier Miner v1

Run id: `20260512T043932-codex-source-label-rule-qualifier-miner-v1`

Gate result: `source_label_rule_qualifier_miner_v1=rules_scored_no_full_acceptance`

## Result

- Rows scored: `248440`.
- Rule search: single-feature threshold atoms plus bounded two-atom conjunctions.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted rule-confidence labels: `[]`.
- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Min Support | Min Wilson95 | Rule | Blockers |
|---|---|---:|---:|---|---|
| `Bear` | `false` | `134` | `0.566325058` | `vix >= 29.98999977 AND regime_confidence <= 0.385` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Bull` | `false` | `338` | `0.7054974201` | `regime_confidence >= 0.833 AND vix <= 12.89000034` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Crisis` | `false` | `1074` | `0.4729340579` | `volatility >= 0.411418579 AND regime_confidence <= 0.455` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |
| `Sideways` | `false` | `3421` | `0.3659108855` | `regime_confidence >= 0.75 AND volatility <= 0.2067864525` | calibration_wilson95_below_0.95;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_wilson95_below_0.95 |

## Boundary

This is a diagnostic qualifying-condition miner over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
