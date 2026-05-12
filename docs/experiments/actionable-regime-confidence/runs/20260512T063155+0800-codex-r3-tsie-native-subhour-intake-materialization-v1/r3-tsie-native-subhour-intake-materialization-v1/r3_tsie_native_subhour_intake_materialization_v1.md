# R3 TSIE Native Subhour Intake Materialization v1

Run id: `20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1`

Gate result: `r3_tsie_native_subhour_intake_materialization_v1=target_root_materialized_bull_bear_sideways_crisis_absent_no_downstream`

Scope:
- Downloaded TSIE parquet remained tmp-only and SHA-256 verified.
- Materialized verifier-shaped R3 native-subhour source-label rows under `/tmp/ict-engine-native-subhour-source-label-intake`.
- Did not mutate repo runtime code, commit raw parquet, run canonical merge, or rerun downstream promotion.

Readback:
- Raw rows: `7193996`.
- Mapped Bull/Bear/Sideways rows: `5032903`.
- Excluded trap/abstain rows: `2161093`.
- Date range: `1990-06-07 02:00:00` to `2026-04-07 02:00:00`.
- Symbols: `386`; groups: `1150`; timeframes: `3`.
- Rows file: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`.
- Rows SHA-256: `72406e48b000f91ed2b3c3e132651537339afb2a8ed2e3ce43b5007abf38f62f`.
- Provenance file: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`.

Split gate:
- Accepted mapping-confidence labels: `Bear, Bull, Sideways`.
- `Crisis` remains blocked because TSIE has no direct source taxonomy class.
- This is source-label mapping evidence only, not downstream profitability evidence.

Decision:
- R3 target root is now materialized with source-owned native sub-hour labels for Bull/Bear/Sideways.
- Strict full objective remains false because Crisis is absent, R6/R5 gates remain unresolved, canonical merge is false, and downstream promotion did not rerun.
- `update_goal=false`.

Next:
- Run a current-objective audit and only consider canonical/downstream rerun after all required root gates and per-regime coverage are satisfied.
