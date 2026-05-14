# Auto-Quant Seed And Run After Threaded Prepare v1

Run id: `20260512T023312-codex-autoquant-seed-and-run-after-threaded-prepare-v1`

Gate result: `autoquant_seed_and_run_after_threaded_prepare_v1=autoquant_oracle_ran_seeded_strategies_no_board_a_acceptance`

## Inputs

- Prepared Auto-Quant state: `/tmp/ict-engine-board-a-autoquant-bootstrap-20260512T021808`
- Managed Auto-Quant commit: `34ba6b6ee6aa69813a50a72158d4c089d97afb96`
- Data readiness predecessor: `20260512T022850-codex-autoquant-threaded-dns-prepare-run-v1`
- Active strategies seeded from `versions/0.4.1/strategies`: `CrashRebound`, `PerPairMR`, `RegimeAdaptiveBNB`
- Active strategy count after seeding: `3`

## Command Results

- Strategy seeding exit: `0`
- Auto-Quant oracle command exit: `0`
- `auto-quant-status` after run exit: `0`
- Final `auto-quant-status`: `dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, `data_ready=true`

## Auto-Quant Results

| Strategy | Robust Sharpe | Binding Slice | Full Sharpe | Full Profit % | Full Trades | Win Rate % | Profit Floor |
|---|---:|---|---:|---:|---:|---:|---|
| `CrashRebound` | `0.0847` | `winter_2022` | `0.2903` | `55.69` | `207` | `68.5990` | `FAIL` |
| `PerPairMR` | `0.0520` | `winter_2022` | `0.3512` | `35.78` | `519` | `58.1888` | `FAIL` |
| `RegimeAdaptiveBNB` | `0.0967` | `recovery_23_25` | `0.1380` | `16.41` | `115` | `69.5652` | `FAIL` |

All three strategies passed the `min_position_size` gate and were non-dominated within the Auto-Quant oracle output, but all three failed the Auto-Quant `profit_floor` gate.

## Board A Impact

This run is real Auto-Quant execution evidence: data was prepared, three active strategies were seeded, and `run.py` completed. It does not satisfy Board A acceptance because it does not create source-owned `MainRegimeV2` regime labels, per-regime qualifying-condition packets, canonical source/control merge inputs, Pre-Bayes/BBN confidence >=95%, CatBoost/path-ranking promotion, or execution-tree actionable acceptance.

Accepted rows added: `0`.
New confidence gate: false.
Canonical merge allowed: false.
Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false.
Strict full objective achieved: false.
`update_goal=false`.

Runtime code changed: false.
Shared intake mutated: false.
R3/R5/R6 roots mutated: false.
Thresholds relaxed: false.
Raw data committed into repo: false.
Trade usable: false.

