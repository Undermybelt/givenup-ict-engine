# R6 Shak Complaint Row Uplift Gate v1

- Decision: `r6_shak_complaint_row_uplift_gate_v1=schema_ready_but_calibration_blocked`.
- Positive rows now: `21`; added this run: `8`.
- Matched negative/control rows now: `21`; added this run: `8`.
- Unique dates: `17`; symbols: `10`; venues: `4`.
- Wilson95 LCB positive/negative/min: `0.845361` / `0.845361` / `0.845361`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This slice materializes source-owned CFTC Shak complaint example rows for Gold/Silver spoofing events. The matched controls are same-complaint genuine-order legs only, so they remain schema/control seeds and do not satisfy the broad normal-market calibration requirement.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `21` | `50` | `false` |
| `negative_support` | `21` | `50` | `false` |
| `chronological_split` | `17` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=10;venues=4` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.845361` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC complaint facts describing genuine order legs in the same examples; schema-ready/unscored seed, not a broad normal-market calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1/r6-shak-complaint-row-uplift-gate/r6_shak_complaint_row_uplift_gate_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1/r6-shak-complaint-row-uplift-gate/r6_shak_complaint_row_uplift_gate_v1_gates.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1/checks/r6_shak_complaint_row_uplift_gate_v1_assertions.out`
