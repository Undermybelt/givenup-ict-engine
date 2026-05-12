# Tomac Local Schema Classifier After 083108 v1

Run id: `20260512T083450+0800-codex-tomac-local-schema-classifier-after-083108-v1`

Gate result: `tomac_local_schema_classifier_after_083108_v1=no_verifier_native_source_control_schema_no_unlock`

## Scope

Read-only schema classification of local Tomac CSV/JSON/archive candidates after the settled `083108` arrival poll. This artifact reads headers and archive member names only. It does not copy files into target roots, approve Tomac strategy/backtest/bar files as source/control evidence, run verifier/split calibration, run canonical merge, run Auto-Quant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.

## Summary

- Files scanned: `215`.
- Exact required source/control file names found: `0`.
- Exact required package present in R6 target roots: `false`.
- Verifier-native hint files: `0`.
- Strong order-lifecycle hint files: `5`.

## Target Roots

| Root | Exists | File Count | Exact Required Package |
|---|---:|---:|---:|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `0` | `False` |
| `/private/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `0` | `False` |

## Order-Lifecycle-Like Samples

| File | Class | Strong Hits | Archive Hits |
|---|---|---|---|
| `/Users/thrill3r/Downloads/Tomac/es future 2021-2025.zip` | `order_lifecycle_hint` | `none` | `symbology.json|symbology.csv` |
| `/Users/thrill3r/Downloads/Tomac/eur future 2015-2025.zip` | `order_lifecycle_hint` | `none` | `symbology.json|symbology.csv` |
| `/Users/thrill3r/Downloads/Tomac/nq future 2021-2025.zip` | `order_lifecycle_hint` | `none` | `symbology.json|symbology.csv` |
| `/Users/thrill3r/Downloads/Tomac/xau future 2021-2025.zip` | `order_lifecycle_hint` | `none` | `symbology.json|symbology.csv` |
| `/Users/thrill3r/Downloads/Tomac/ym future 2021-2025.zip` | `order_lifecycle_hint` | `none` | `symbology.json|symbology.csv` |

## Decision

- No exact required R6 owner-export positive/control/provenance package was present in target roots.
- Local Tomac files are classified as strategy/backtest/runtime context, OHLCV/bar context, or weak archive/member-name hints only; none is accepted as verifier-native source/control evidence.
- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval.
