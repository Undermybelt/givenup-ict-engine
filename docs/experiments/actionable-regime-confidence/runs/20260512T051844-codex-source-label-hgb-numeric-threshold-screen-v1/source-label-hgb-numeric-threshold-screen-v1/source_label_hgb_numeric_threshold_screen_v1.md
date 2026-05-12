# Source Label HGB Numeric Threshold Screen v1

Run id: `20260512T051844-codex-source-label-hgb-numeric-threshold-screen-v1`

Gate result: `source_label_hgb_numeric_threshold_screen_v1=all_root_labels_hgb_numeric_accepted`

## Result

- Rows scored: `248440`.
- Model: `HistGradientBoostingClassifier` trained only on the `calibration` split.
- Feature policy: numeric source features only; no source-owner, market-family, or symbol one-hot columns.
- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.
- Accepted HGB numeric confidence labels: `['Bear', 'Bull', 'Crisis', 'Sideways']`.
- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.

## Best Gates

| Label | Accepted 95 | Threshold | Min Support | Min Wilson95 | Blockers |
|---|---|---:|---:|---:|---|
| `Bear` | `true` | `0.98` | `177` | `0.9787578642` |  |
| `Bull` | `true` | `0.97` | `618` | `0.9908918883` |  |
| `Crisis` | `true` | `0.985` | `547` | `0.9930261988` |  |
| `Sideways` | `true` | `0.97` | `534` | `0.990666799` |  |

## Boundary

This is a diagnostic numeric model screen over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
