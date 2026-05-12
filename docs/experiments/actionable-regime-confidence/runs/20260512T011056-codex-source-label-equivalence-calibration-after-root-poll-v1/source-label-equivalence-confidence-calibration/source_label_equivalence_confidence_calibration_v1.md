# Source Label Equivalence Confidence Calibration v1

- Decision: `source_label_equivalence_confidence_calibration_v1=source_confidence_scored_no_acceptance`.
- Verifier status: `schema_ready_unscored`; return code `0`; rows `248440`.
- Labels present: `{'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`; missing roots `[]`.
- Confidence rule: source-owned confidence field `>= 0.95`; Wilson95 lower bound `>= 0.95`; minimum support `50` per required split.
- Accepted source-confidence labels: `[]`.
- Missing confidence rows: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Label Split Scores

| Label | Split | Support | Rows >=0.95 | Share >=0.95 | Wilson95 LCB | Mean | Median | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Bear` | `calibration` | `32975` | `49` | `0.001486` | `0.001124` | `0.446792` | `0.444000` | `1.000000` |
| `Bear` | `heldout_market` | `4635` | `3` | `0.000647` | `0.000220` | `0.487871` | `0.500000` | `1.000000` |
| `Bear` | `heldout_time` | `11012` | `0` | `0.000000` | `0.000000` | `0.466332` | `0.462000` | `0.857000` |
| `Bear` | `test` | `6317` | `0` | `0.000000` | `0.000000` | `0.469449` | `0.500000` | `0.857000` |
| `Bull` | `calibration` | `60213` | `5460` | `0.090678` | `0.088411` | `0.583859` | `0.600000` | `1.000000` |
| `Bull` | `heldout_market` | `12786` | `795` | `0.062177` | `0.058122` | `0.609447` | `0.600000` | `1.000000` |
| `Bull` | `heldout_time` | `19497` | `2417` | `0.123968` | `0.119416` | `0.620857` | `0.600000` | `1.000000` |
| `Bull` | `test` | `12483` | `1521` | `0.121846` | `0.116224` | `0.627731` | `0.600000` | `1.000000` |
| `Crisis` | `calibration` | `21523` | `130` | `0.006040` | `0.005089` | `0.411362` | `0.417000` | `0.989973` |
| `Crisis` | `heldout_market` | `1029` | `0` | `0.000000` | `0.000000` | `0.391580` | `0.417000` | `0.500000` |
| `Crisis` | `heldout_time` | `5076` | `80` | `0.015760` | `0.012682` | `0.428110` | `0.417000` | `0.997706` |
| `Crisis` | `test` | `2995` | `66` | `0.022037` | `0.017359` | `0.437621` | `0.417000` | `0.990888` |
| `Sideways` | `calibration` | `34265` | `4929` | `0.143849` | `0.140174` | `0.612122` | `0.600000` | `1.000000` |
| `Sideways` | `heldout_market` | `7786` | `1671` | `0.214616` | `0.205639` | `0.676047` | `0.600000` | `1.000000` |
| `Sideways` | `heldout_time` | `9799` | `1388` | `0.141647` | `0.134884` | `0.662797` | `0.600000` | `1.000000` |
| `Sideways` | `test` | `6049` | `698` | `0.115391` | `0.107583` | `0.632328` | `0.600000` | `1.000000` |

## Gates

| Label | Accepted 95 | Blockers |
|---|---|---|
| `Bear` | `false` | calibration_source_confidence_wilson95_below_0.95; heldout_market_source_confidence_wilson95_below_0.95; heldout_time_source_confidence_wilson95_below_0.95; test_source_confidence_wilson95_below_0.95 |
| `Bull` | `false` | calibration_source_confidence_wilson95_below_0.95; heldout_market_source_confidence_wilson95_below_0.95; heldout_time_source_confidence_wilson95_below_0.95; test_source_confidence_wilson95_below_0.95 |
| `Crisis` | `false` | calibration_source_confidence_wilson95_below_0.95; heldout_market_source_confidence_wilson95_below_0.95; heldout_time_source_confidence_wilson95_below_0.95; test_source_confidence_wilson95_below_0.95 |
| `Sideways` | `false` | calibration_source_confidence_wilson95_below_0.95; heldout_market_source_confidence_wilson95_below_0.95; heldout_time_source_confidence_wilson95_below_0.95; test_source_confidence_wilson95_below_0.95 |

## Boundary

This is a source-confidence calibration screen over the live cleaned source-label equivalence root. It does not promote schema readiness into accepted Board A confidence, does not create native sub-hour or R5 recency-extension rows, and does not alter R6 direct Manipulation evidence.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.md`
- Label split CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_label_split_v1.csv`
- Source owner CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_owner_v1.csv`
- Market family CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_market_v1.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_gates_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/checks/source_label_equivalence_confidence_calibration_v1_assertions.out`
