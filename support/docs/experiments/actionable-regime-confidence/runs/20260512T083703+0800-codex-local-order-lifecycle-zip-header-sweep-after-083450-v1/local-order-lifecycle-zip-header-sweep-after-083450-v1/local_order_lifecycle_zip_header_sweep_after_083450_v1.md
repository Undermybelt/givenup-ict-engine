# Local Order-Lifecycle Zip/Header Sweep After 083450 v1

Run id: `20260512T083703+0800-codex-local-order-lifecycle-zip-header-sweep-after-083450-v1`

Gate result: `local_order_lifecycle_zip_header_sweep_after_083450_v1=no_verifier_native_order_lifecycle_package_no_unlock`

## Scope

Read-only local sweep of Tomac CSV/JSON/ZIP/RAR candidates after the `083450` schema classifier. The script reads file names, ZIP member names, and CSV headers only. It does not extract files into target roots, copy evidence, mutate state, run verifier/split calibration, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.

## Summary

- Candidate/header rows scanned: `243`.
- ZIP member rows scanned: `34`.
- Order-lifecycle candidate rows: `0`.
- Exact required R6 package present in target roots: `false`.

## Order-Lifecycle Candidates

- None.

## Target Roots

| Path | Exists | File Count | Required Files Present | Exact Package |
|---|---:|---:|---|---:|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `0` | `none` | `False` |
| `/private/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `0` | `none` | `False` |

## Decision

No verifier-native positive/control/provenance package was found. Local Tomac archives and extracted files remain market-data, symbology, strategy, or backtest context unless an owner-approved/source-owned order-lifecycle export with matched normal controls is placed in the required target root or same-exhibit `FLIP` is explicitly approved as control.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. Do not run selected-data AutoQuant or the ordered AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain until source/control unlock and selected-history gates are both satisfied.
