# Source Label Predictive Confidence Screen v1

Run id: `20260512T041656-codex-source-label-predictive-confidence-screen-v1`

Gate result: `source_label_predictive_confidence_screen_v1=predictive_confidence_scored_no_full_acceptance`

## Result

- Verifier status: `schema_ready_unscored`; return code `0`; rows `248440`.
- Model: Gaussian Naive Bayes implemented in this script, calibration split training only, 70 features, high-confidence threshold `0.95`.
- Accepted predictive-confidence labels: `[]`.
- Accepted rows added `0`; new confidence gate `false`; strict full objective `false`; `update_goal=false`.

## Gates

| Label | Accepted 95 | Blockers |
|---|---|---|
| `Bear` | `false` | calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_precision_wilson95_below_0.95 |
| `Bull` | `false` | calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_precision_wilson95_below_0.95 |
| `Crisis` | `false` | calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_support_below_50;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_precision_wilson95_below_0.95 |
| `Sideways` | `false` | calibration_high_confidence_precision_wilson95_below_0.95;heldout_market_high_confidence_precision_wilson95_below_0.95;heldout_time_high_confidence_precision_wilson95_below_0.95;test_high_confidence_precision_wilson95_below_0.95 |

## Boundary

This is a diagnostic predictive-confidence screen over source-owned labels. It does not promote schema readiness or model confidence unless every required split passes with enough high-confidence support and Wilson95 lower bound >=0.95.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_screen_v1.json`
- Metrics CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_metrics_v1.csv`
- Gates CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_gates_v1.csv`
- Feature importance CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/source-label-predictive-confidence-screen-v1/source_label_predictive_confidence_feature_importance_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T041656-codex-source-label-predictive-confidence-screen-v1/checks/source_label_predictive_confidence_screen_v1_assertions.out`
