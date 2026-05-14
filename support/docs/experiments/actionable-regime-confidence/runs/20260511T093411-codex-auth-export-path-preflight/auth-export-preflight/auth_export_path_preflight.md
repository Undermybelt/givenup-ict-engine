# Auth Export Path Preflight

Run ID: `20260511T093411+0800-codex-auth-export-path-preflight`

## Result

- Secret values recorded: false.
- Dune ready: `false`.
- Kaggle ready: `false`.
- HuggingFace ready: `false`.
- FINRA ready: `false`.
- SEC API ready: `false`.
- FRED ready sidecar only: `false`.
- TradingView config present: `true`.
- Accepted new parent-root label sources: `0`.
- Accepted new direct `Manipulation` rows: `0`.
- Gate result: `blocked_auth_export_paths_no_accepted_label_export_available`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Next Action

Use an available authenticated export path only if it yields exact-underlying parent-root labels or timestamped direct Manipulation positive/negative rows; otherwise user-provided structured panels are required.
