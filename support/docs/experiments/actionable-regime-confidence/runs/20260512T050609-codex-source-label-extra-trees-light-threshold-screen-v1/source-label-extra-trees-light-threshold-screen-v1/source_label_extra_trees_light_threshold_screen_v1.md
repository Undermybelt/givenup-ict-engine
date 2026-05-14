# Source Label ExtraTrees Light Threshold Screen v1

Run id: `20260512T050609-codex-source-label-extra-trees-light-threshold-screen-v1`

Gate result: `source_label_extra_trees_light_threshold_screen_v1=extra_trees_light_scored_no_full_acceptance`

## Result

- Rows scored: `248440`.
- Model: light `ExtraTreesClassifier` trained only on the `calibration` split.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted ExtraTrees-light confidence labels: `[]`.
- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Threshold | Min Support | Min Wilson95 | Blockers |
|---|---|---:|---:|---:|---|
| `Bear` | `false` | `0.5` | `0` | `0.0` | calibration_support_below_50;calibration_wilson95_below_0.95;heldout_market_support_below_50;heldout_market_wilson95_below_0.95;heldout_time_support_below_50;heldout_time_wilson95_below_0.95;test_support_below_50;test_wilson95_below_0.95 |
| `Bull` | `false` | `0.55` | `0` | `0.0` | heldout_market_support_below_50;heldout_market_wilson95_below_0.95;heldout_time_wilson95_below_0.95;test_support_below_50;test_wilson95_below_0.95 |
| `Crisis` | `false` | `0.87` | `0` | `0.0` | heldout_market_support_below_50;heldout_market_wilson95_below_0.95;heldout_time_support_below_50;heldout_time_wilson95_below_0.95;test_support_below_50;test_wilson95_below_0.95 |
| `Sideways` | `false` | `0.77` | `0` | `0.0` | heldout_market_support_below_50;heldout_market_wilson95_below_0.95;heldout_time_support_below_50;heldout_time_wilson95_below_0.95;test_support_below_50;test_wilson95_below_0.95 |

## Boundary

This is a diagnostic threshold screen over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
