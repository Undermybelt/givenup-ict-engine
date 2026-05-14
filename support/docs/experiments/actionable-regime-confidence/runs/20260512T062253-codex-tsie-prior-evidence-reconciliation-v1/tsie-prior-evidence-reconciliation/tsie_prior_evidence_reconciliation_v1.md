# TSIE Prior Evidence Reconciliation v1

Run id: `20260512T062253+0800-codex-tsie-prior-evidence-reconciliation-v1`

## Decision

`tsie_prior_evidence_reconciliation_v1=duplicate_candidate_prior_full_data_and_mapping_failures_no_intake`

- `061855` points to the same Hugging Face dataset and commit already audited by prior Board A artifacts.
- Prior mapping audit blocked TSIE as sidecar-only/rule-based IDX signal labels without direct `Crisis` or accepted `MainRegimeV2` source labels.
- Prior full-data parent-root calibration accepted `0` roots under unchanged 95% Wilson lower-bound and cross-context gates.
- Prior expanded-label calibration also accepted `0` new roots.
- No required target root exists or was mutated in this slice.

## Parent-Root Gate Readback

| Root | Cal support | Cal LCB | Test support | Test LCB | Test coverage | Accepted | Blockers |
|---|---:|---:|---:|---:|---:|---|---|
| Bull | 1439 | 0.374575 | 3501 | 0.563979 | 0.002434 | false | calibration_wilson95_below_0_95, test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, validation_market_contexts_below_2, validation_timeframes_below_2 |
| Bear | 1439 | 0.640954 | 1898 | 0.587442 | 0.001319 | false | calibration_wilson95_below_0_95, test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, validation_market_contexts_below_2, validation_timeframes_below_2 |
| Sideways | 1441 | 0.972876 | 177 | 0.864895 | 0.000123 | false | test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, validation_market_contexts_below_2, validation_timeframes_below_2 |

## Required Roots

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `false`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `false`
- `/tmp/ict-engine-source-panel-recency-extension`: `false`

## Accounting

- Accepted rows added: `0`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Do not materialize /tmp/ict-engine-native-subhour-source-label-intake from TSIE unless a new source-owner MainRegimeV2 crosswalk or materially different source revision arrives. Continue with explicit R6 source/control approval, source-owned R5 recency rows, or a different R3 native-subhour source-label panel.
