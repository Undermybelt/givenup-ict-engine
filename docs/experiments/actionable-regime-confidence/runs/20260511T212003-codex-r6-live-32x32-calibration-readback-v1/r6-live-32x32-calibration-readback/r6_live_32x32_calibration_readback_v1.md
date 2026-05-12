# R6 Live 32x32 Calibration Readback v1

Decision: `r6_live_32x32_calibration_readback_v1=live_rows_schema_ready_wilson_broad_control_blocked`.

Result:
- Live direct intake rows: positives `32`, matched negatives `32`, matched groups `31`.
- Unique positive dates/symbols/venues: `17` / `10` / `5`.
- Wilson95 LCB positive/negative/min: `0.892821` / `0.892821` / `0.892821`.
- Required all-success support for Wilson95 `>=0.95`: `73`.
- Verifier status: `schema_ready_unscored`; stable file hashes during readback: `true`.
- Broad normal sample: `false`; direct species coverage still only `spoofing_layering`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `stable_file_hashes` | `True` | `True` | `true` |
| `verifier_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `positive_support` | `32` | `73` | `false` |
| `negative_support` | `32` | `73` | `false` |
| `orphan_groups` | `0` | `0` | `true` |
| `chronological_train_calibration_test` | `17` | `3` | `true` |
| `heldout_symbol_or_venue` | `symbols=10;venues=5` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.892821` | `>=0.95` | `false` |
| `broad_normal_sample` | `same-source public CFTC genuine-order counterparts` | `source-owned broad normal activity sample` | `false` |
| `direct_species_coverage` | `spoofing_layering` | `spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape` | `false` |

Interpretation:
The live R6 intake now has enough public CFTC row breadth to lift Wilson95 from the earlier 0.77 range to 0.892821, while preserving chronological and heldout-symbol/venue gates. It still fails the unchanged strict objective because Wilson95 remains below 0.95, broad source-owned normal controls are absent, and non-spoofing direct species are not covered.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212003-codex-r6-live-32x32-calibration-readback-v1/r6-live-32x32-calibration-readback/r6_live_32x32_calibration_readback_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212003-codex-r6-live-32x32-calibration-readback-v1/r6-live-32x32-calibration-readback/r6_live_32x32_calibration_readback_v1_gates.csv`
- Source report CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212003-codex-r6-live-32x32-calibration-readback-v1/r6-live-32x32-calibration-readback/r6_live_32x32_calibration_readback_v1_sources.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T212003-codex-r6-live-32x32-calibration-readback-v1/r6-live-32x32-calibration-readback/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212003-codex-r6-live-32x32-calibration-readback-v1/checks/r6_live_32x32_calibration_readback_v1_assertions.out`
