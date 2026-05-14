# Native Sub-hour Intake Request Package v1

Run ID: `20260511T203100-codex-native-subhour-intake-request-package-v1`

- Gate result: `native_subhour_intake_request_package_v1=request_ready_rows_not_acquired`.
- Purpose: convert the R3 native sub-hour blocker into exact source-owned intake requirements without accepting proxy labels.
- Active native intraday source-label request rows: `336`.
- Focus blocker cells carried forward: `4`.
- Required intake root: `/tmp/ict-engine-native-subhour-source-label-intake`.
- Required files: `native_subhour_source_label_rows.csv` and `native_subhour_source_label_provenance.json`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Focus Cells

| Instrument | Timeframe | Root | Intake row file |
|---|---|---|---|
| `AAPL` | `15m` | `all four roots required` | `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` |
| `AAPL` | `30m` | `all four roots required` | `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` |
| `^IXIC` | `15m` | `all four roots required` | `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` |
| `^IXIC` | `30m` | `all four roots required` | `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` |

## Request Boundary

- This package does not create source labels, does not download raw rows, and does not run calibration.
- OHLCV/provider candles, HMM states, KMeans labels, future-return labels, classifier outputs, generated labels, and daily/monthly labels projected into sub-hour windows remain fail-closed.
- After files appear under the intake root, rerun the fail-closed native sub-hour verifier before any completion audit.

## Artifacts

- JSON: `native_subhour_intake_request_package_v1.json`
- Target rows: `native_subhour_intake_request_targets_v1.csv`
- Focus cells: `native_subhour_intake_focus_cells_v1.csv`
- Required fields: `native_subhour_intake_required_fields_v1.csv`
- Request template: `native_subhour_intake_request_template_v1.md`
- Assertions: `../checks/native_subhour_intake_request_package_v1_assertions.out`
