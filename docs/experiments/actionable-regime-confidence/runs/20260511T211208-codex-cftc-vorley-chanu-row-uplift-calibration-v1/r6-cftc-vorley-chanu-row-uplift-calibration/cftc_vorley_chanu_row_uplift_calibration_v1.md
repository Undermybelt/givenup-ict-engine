# CFTC Vorley/Chanu Row Uplift Calibration v1

- Decision: `r6_cftc_vorley_chanu_calibration_gate_v3=schema_ready_but_calibration_blocked`.
- Source: `https://www.cftc.gov/idc/groups/public/@lrenforcementactions/documents/legalpleading/enfvorleychanucomplaint012618.pdf`.
- Source PDF SHA256: `2a109b1b86b529737396f57461dded471bbae4f4ddfcedc124cd7961f2b91493`.
- Added positives / matched negatives this run: `4` / `4`.
- Total positives / matched negatives: `13` / `13`.
- Unique dates: `10`; symbols: `6`; venues: `3`.
- Wilson95 LCB positive/negative/min: `0.771905` / `0.771905` / `0.771905`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Added Rows

| Type | Source Row ID | Group | Date | Symbol |
|---|---|---|---|---|
| `positive_spoofing_layering` | `cftc_vorley_chanu_20120106_gold_buy_spoof_orders` | `cftc_vorley_chanu_20120106_gold_example` | `2012-01-06` | `COMEX Gold Futures` |
| `positive_spoofing_layering` | `cftc_vorley_chanu_20120606_gold_buy_spoof_orders` | `cftc_vorley_chanu_20120606_gold_example` | `2012-06-06` | `COMEX Gold Futures` |
| `positive_spoofing_layering` | `cftc_vorley_chanu_20130128_gold_sell_spoof_order` | `cftc_vorley_chanu_20130128_gold_example` | `2013-01-28` | `COMEX Gold Futures` |
| `positive_spoofing_layering` | `cftc_vorley_chanu_20130523_gold_sell_spoof_order` | `cftc_vorley_chanu_20130523_gold_example` | `2013-05-23` | `COMEX Gold Futures June delivery` |
| `matched_negative_normal_activity` | `cftc_vorley_chanu_20120106_gold_sell_genuine_iceberg_control` | `cftc_vorley_chanu_20120106_gold_example` | `2012-01-06` | `COMEX Gold Futures` |
| `matched_negative_normal_activity` | `cftc_vorley_chanu_20120606_gold_sell_genuine_iceberg_control` | `cftc_vorley_chanu_20120606_gold_example` | `2012-06-06` | `COMEX Gold Futures` |
| `matched_negative_normal_activity` | `cftc_vorley_chanu_20130128_gold_buy_genuine_iceberg_control` | `cftc_vorley_chanu_20130128_gold_example` | `2013-01-28` | `COMEX Gold Futures` |
| `matched_negative_normal_activity` | `cftc_vorley_chanu_20130523_gold_buy_genuine_iceberg_control` | `cftc_vorley_chanu_20130523_gold_example` | `2013-05-23` | `COMEX Gold Futures June delivery` |

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `13` | `50` | `false` |
| `negative_support` | `13` | `50` | `false` |
| `chronological_split` | `10` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=6;venues=3` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.771905` | `>=0.95` | `false` |
| `broad_normal_sample` | `same-report or same-complaint genuine-order control seeds only; not a broad source-owned normal-market sample` | `source-owned broad normal activity sample` | `false` |

## Interpretation

The direct R6 intake has more official CFTC timestamped spoofing/genuine-order examples, but it is still schema-ready only. Support remains far below the unchanged 50/50 floor and the matched controls are same-complaint genuine-order seeds, not a broad normal-market sample.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/r6-cftc-vorley-chanu-row-uplift-calibration/cftc_vorley_chanu_row_uplift_calibration_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/r6-cftc-vorley-chanu-row-uplift-calibration/cftc_vorley_chanu_row_uplift_calibration_v1_gates.csv`
- Intake summary CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/r6-cftc-vorley-chanu-row-uplift-calibration/cftc_vorley_chanu_row_uplift_calibration_v1_intake_summary.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/r6-cftc-vorley-chanu-row-uplift-calibration/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/checks/cftc_vorley_chanu_row_uplift_calibration_v1_assertions.out`
