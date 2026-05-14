# Source Label HistGB Confidence Screen v1

Run id: `20260512T042448-codex-source-label-histgb-confidence-screen-v1`

Gate result: `source_label_histgb_confidence_screen_v1=histgb_confidence_scored_no_full_acceptance`

## Result

- Verifier status: `schema_ready_unscored`; return code `0`; rows `248440`.
- Model: fixed `HistGradientBoostingClassifier`, trained on `calibration` split only.
- Accepted HistGB confidence labels: `[]`.
- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.

## Gates

| Label | Accepted 95 | Blockers |
|---|---|---|
| `Bear` | `false` | calibration_high_confidence_support_below_50;calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_support_below_50;test_high_confidence_precision_wilson95_below_0.95 |
| `Bull` | `false` | calibration_high_confidence_support_below_50;calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_support_below_50;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_support_below_50;test_high_confidence_precision_wilson95_below_0.95 |
| `Crisis` | `false` | heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95 |
| `Sideways` | `false` | heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95;test_high_confidence_precision_wilson95_below_0.95 |

## Boundary

This is a diagnostic model screen over source-owned labels. It does not promote unless every required split clears support and Wilson95 lower bound >=0.95.
