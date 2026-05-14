# Auto-Quant Seed Readback Root Poll v1

Run id: `20260512T023842-codex-autoquant-seed-readback-root-poll-v1`
Gate result: `autoquant_seed_readback_root_poll_v1=autoquant_seeded_strategy_runs_non_promoting_roots_still_blocked`
Board sha256 before artifact generation: `02b43150ce4aa684e18719c4f0c1a78ae43fe1f01a332c1f0f647402fe63005f`

## Inputs

- Threaded DNS/data-readiness readback: `docs/experiments/actionable-regime-confidence/runs/20260512T023236-codex-autoquant-threaded-dns-prepare-readback-v1`
- Seeded strategy run: `docs/experiments/actionable-regime-confidence/runs/20260512T023312-codex-autoquant-seed-and-run-after-threaded-prepare-v1`
- Local crypto-cache smoke run: `docs/experiments/actionable-regime-confidence/runs/20260512T023351-codex-autoquant-local-crypto-cache-backtest-smoke-v1`
- Active Board A cursor: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`

## Root Poll

| root | status | files | promotion use |
|---|---:|---:|---|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | absent | 0 | blocked |
| `/tmp/ict-engine-native-subhour-source-label-intake` | absent | 0 | blocked |
| `/tmp/ict-engine-source-panel-recency-extension` | absent | 0 | blocked |
| `/tmp/ict-engine-source-label-equivalence-intake` | present | 2 | non-promoting, already confidence-blocked |
| `/tmp/ict-engine-direct-manipulation-row-intake` | present | 3 | legacy non-promoting direct-intake root |

## Auto-Quant Readback

- `023236` closes the narrow data-readiness gap: Auto-Quant status became `dependency_ready_seed_required`, `healthy=true`, `dependency_healthy=true`, and `data_ready=true`, with `15` Binance feather files present.
- `023312` seeded `3` active strategies and `run.py` exited `0`.
- `023312` remains non-promoting:
  - `CrashRebound`: robust Sharpe `0.0847`; profit floor `FAIL`; full-period total profit `55.69%`; worst declared timerange profit `2.99%`.
  - `PerPairMR`: robust Sharpe `0.0520`; profit floor `FAIL`; full-period total profit `35.78%`; worst declared timerange profit `0.84%`.
  - `RegimeAdaptiveBNB`: robust Sharpe `0.0967`; profit floor `FAIL`; full-period total profit `16.41%`; worst declared timerange profit `3.71%`.
- `023351` bootstrapped and seeded an isolated local crypto-cache workspace, but `run.py` exited `1` because FreqTrade/ccxt still attempted Binance market loading and hit `Could not contact DNS servers`.

## Decision

These runs prove that the local Auto-Quant path can be data-ready and can execute seeded strategies in the already patched `021808` managed workspace. They do not provide Board A promotion evidence because they are strategy/profitability readbacks, not accepted `MainRegimeV2` confidence packets, and they are not connected to source-owned R6 normal controls, explicit `FLIP` approval, canonical intake merge, or downstream promotion.

Accepted rows added: `0`.
New confidence gate: `false`.
Canonical merge allowed: `false`.
Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.
Strict full objective achieved: `false`.
`update_goal=false`.

Runtime code changed: `false`.
Shared intake mutated: `false`.
R3/R5/R6 roots mutated: `false`.
Thresholds relaxed: `false`.
Raw data committed: `false`.
Trade usable: `false`.

## Next

Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream rerun. Do not use Auto-Quant data readiness, seeded strategy profitability, or Binance-cache smoke results as accepted regime-confidence evidence.
