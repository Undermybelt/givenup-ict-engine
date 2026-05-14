# Native Subhour Local/Live Intake Sweep v1

- Decision: `native_subhour_local_live_intake_sweep_v1=no_native_subhour_source_owned_intake_package`
- Intake roots checked: `4`
- Candidate files classified: `18086`
- Candidate CSV rows written: `500`
- Exact required intake files present: `0`
- Complete native sub-hour package present: `false`
- Ready native sub-hour source-owned label sources: `0`
- Accepted rows added: `0`
- New confidence gate: `false`
- Native sub-hour source overlap closed: `false`
- Strict full objective achieved: `false`; `update_goal=false`

## Disposition Summary

| Disposition | Files |
|---|---:|
| `blocked_daily_source_panel_not_native_subhour` | `11` |
| `blocked_direct_manipulation_not_price_root_native_subhour` | `12148` |
| `blocked_generated_or_model_derived_regime_labels` | `296` |
| `blocked_no_r3_native_subhour_source_label_schema` | `4392` |
| `blocked_price_or_feature_panel_not_source_owned_labels` | `1239` |

## Gate Readback

No source-owned native sub-hour R3 intake package was found. The visible sub-hour yfinance files are raw OHLCV/provider panels and remain rejected as proxy/price data, not native source labels.

This run is additive after `194400` and does not reopen R6 spoofing/layering, R5 recency-tail, or the owner-request package. It preserves the strict blocker: R3 remains blocked until `native_subhour_source_label_rows.csv` and `native_subhour_source_label_provenance.json` are acquired under an intake root and verified.

## Artifacts

- JSON: `native_subhour_local_live_intake_sweep_v1.json`
- Candidate CSV: `native_subhour_local_live_intake_sweep_v1_candidates.csv`
- Intake roots CSV: `native_subhour_local_live_intake_sweep_v1_intake_roots.csv`
- Assertions: `../checks/native_subhour_local_live_intake_sweep_v1_assertions.out`
