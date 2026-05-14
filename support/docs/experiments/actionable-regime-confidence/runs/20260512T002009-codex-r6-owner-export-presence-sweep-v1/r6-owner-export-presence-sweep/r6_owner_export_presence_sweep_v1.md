# R6 Owner Export Presence Sweep v1

- Run id: `20260512T002009-codex-r6-owner-export-presence-sweep-v1`.
- Board cursor observed: `20260512T001636+0800-codex-r6-owner-export-request-package-v1`.
- Request package: `docs/experiments/actionable-regime-confidence/runs/20260512T001636-codex-r6-owner-export-request-package-v1`.
- Target intake root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Target intake root state: `missing`.
- Required files present: `0/3`.
- Gate result: `r6_owner_export_presence_sweep_v1=no_owner_export_files_present_request_package_still_blocked`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Required Files

- `direct_manipulation_positive_rows.csv`: missing.
- `direct_manipulation_matched_controls.csv`: missing.
- `direct_manipulation_provenance.json`: missing.

## Local Sweep

| Scope | Max Depth | Candidate Hits | Decision |
|---|---:|---:|---|
| `/tmp /private/tmp` | `5` | `0` | `no_required_owner_export_files_seen` |
| `/Users/thrill3r/Downloads` | `5` | `0` | `no_required_owner_export_files_seen` |
| `docs/experiments/actionable-regime-confidence/runs` | `all` | `7` | `only_request_package_files_seen_no_required_data_exports` |

The repo hits are the V62 request-package report, schema, matrix, JSON, assertions, and reproduction script. They are not row exports and do not satisfy the required positive/control/provenance file contract.

## Interpretation

The V62 request package is still the active handoff point, but no owner/user-approved export files are present in the target root or bounded local caches checked in this run. No verifier, split calibration, provider, Auto-Quant, BBN, CatBoost, or execution-tree promotion rerun is justified until real export files arrive or the owner explicitly approves a different split contract.

## Next

Place owner/user-approved R6 export files under `/tmp/ict-engine-board-a-r6-owner-export-v1` or record explicit approval for a different split contract; then rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.
