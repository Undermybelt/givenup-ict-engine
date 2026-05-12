# R6 Gandhi Expanded Calibration Gate v1

- Decision: `r6_gandhi_expanded_calibration_gate_v1=expanded_rows_schema_ready_calibration_blocked`.
- Positive rows: `4`; matched negative rows: `4`; matched groups: `3`.
- Unique dates: `3`; symbols/contracts: `3`; venues: `1`.
- Wilson95 LCB positive/negative/min: `0.510109` / `0.510109` / `0.510109`.
- Chronological train/calibration/test split ok: `true`.
- Heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Missing direct species: `quote_spoofing,quote_stuffing,pinging,bear_raid,painting_tape`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `4` | `73` | `false` |
| `negative_support` | `4` | `73` | `false` |
| `chronological_train_calibration_test` | `3` | `3` | `true` |
| `heldout_symbol_or_venue` | `symbols=3;venues=1` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.510109` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample.` | `source-owned broad normal activity sample` | `false` |
| `direct_species_coverage` | `spoofing_layering` | `spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape` | `false` |

## Interpretation

The Gandhi uplift materially improves the R6 schema-ready seed from 2/2 rows to 4/4 rows and adds chronological plus symbol/contract breadth. It still cannot satisfy the unchanged Board A confidence objective because support is far below the Wilson95 threshold, controls are same-report seeds rather than a broad normal sample, and direct species coverage is still incomplete.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1/r6-gandhi-expanded-calibration-gate/r6_gandhi_expanded_calibration_gate_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1/r6-gandhi-expanded-calibration-gate/r6_gandhi_expanded_calibration_gate_v1_gates.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1/r6-gandhi-expanded-calibration-gate/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1/checks/r6_gandhi_expanded_calibration_gate_v1_assertions.out`
