# Source Label Numeric Tree Threshold Screen v1

Run id: `20260512T052522-codex-source-label-numeric-tree-threshold-screen-v1`

Gate result: `source_label_numeric_tree_threshold_screen_v1=numeric_tree_scored_no_full_acceptance`

## Result

- Rows scored: `248440`.
- Model: `DecisionTreeClassifier` trained only on the `calibration` split.
- Feature policy: numeric source features only; no source-owner, market-family, or symbol one-hot columns.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted numeric-tree confidence labels: `['Bull', 'Crisis', 'Sideways']`.
- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Threshold | Min Support | Min Wilson95 | Blockers |
|---|---|---:|---:|---:|---|
| `Bear` | `false` | `0.965` | `68` | `0.9465286635` | heldout_market_wilson95_below_0.95 |
| `Bull` | `true` | `0.995` | `539` | `0.9810757714` |  |
| `Crisis` | `true` | `0.995` | `547` | `0.9930261988` |  |
| `Sideways` | `true` | `0.995` | `955` | `0.9959936455` |  |

## Boundary

This is a diagnostic numeric tree screen over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
