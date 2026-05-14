# Current Goal Completion Audit v6

Run ID: `20260511T104815+0800-current-goal-completion-audit-v6-mainregimev2-relock`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Objective

Every active Board A regime must reach at least 95% calibrated confidence, and those regimes must be validated across other markets, other timeframes, full cycles, and the broad available universe before reporting success.

## Active Taxonomy

- Active taxonomy: `MainRegimeV2`.
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct-event class or overlay: `Manipulation`.
- Residual: `UnknownOrMixed`.
- Controlling relock: `20260511T103333+0800-codex-mainregimev2-board-a-top-relock`.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Use the named Board A markdown as authoritative status | Current Cursor and Evidence Ledger inspected after the MainRegimeV2 relock and the `104752` public-source delta audit | pass |
| Active taxonomy is MainRegimeV2 with `Bull`/`Bear`/`Sideways`/`Crisis`; `Manipulation` separate | `20260511T103333-codex-mainregimev2-board-a-top-relock` taxonomy JSON | pass |
| Six accepted subtype/signature packets do not complete parent roots | Board and relock mark the six packets as `sub_regime_evidence_only` | pass |
| Every active main price root has 95%-99% calibrated evidence | Board baseline ledger preserves scope-limited 95% packets for `Bull`, `Bear`, `Sideways`, and `Crisis` | partial_scope_limited |
| Every active main price root is validated across other markets/timeframes/full cycles/full observed universe | `20260511T070405` full-cycle/full-universe gap audit reports FAIL | fail |
| Fresh public source delta adds attachable labels or rows | `20260511T104752` adds `0` parent-root slots and `0` direct `Manipulation` rows | fail_no_new_slots |
| `Manipulation` uses direct evidence, not OHLCV subfactors | Mehrnoom direct event and Zenodo bounded self-trade slices are direct evidence; OHLCV proxy acceptance false | pass_scope_limited |
| `Manipulation` covers broader direct manipulation varieties | Current direct evidence is scoped; full direct variety coverage is false | fail |
| No threshold/runtime/raw-data/trade-usable shortcut | Latest inspected artifacts keep thresholds relaxed false, runtime code changed false, raw data committed false, trade usable false | pass |

## Scope-Limited 95 Evidence Preserved

| Regime | Evidence | Calibration/Test Wilson95 | Status |
|---|---|---|---|
| `Bull` | Kaggle bull coverage-buffer gate | `0.952516` / `0.961931` | scope_limited_full_matrix_blocked |
| `Bear` | Yahoo source-backed parent-root gate | `0.993968` / `0.992722` | scope_limited_full_matrix_blocked |
| `Sideways` | Yahoo source-backed parent-root gate | `0.988647` / `0.995568` | scope_limited_full_matrix_blocked |
| `Crisis` | broader MainRegimeV2 root probe | `0.996248` / `0.995981` | scope_limited_full_matrix_blocked |
| `Manipulation` | Mehrnoom Telegram direct-event gate | `0.999735` / `0.999701` | direct_event_scope_limited_full_variety_blocked |

## Full-Cycle Full-Universe Blockers

From `20260511T070405-codex-full-cycle-full-universe-gap-audit`:

| Regime | Missing Observed Timeframes | Missing Observed Contexts | Missing Instrument Count |
|---|---|---|---:|
| `Bull` | `15m`, `1h` | `CME_futures_local`, `IBKR_US_ETF`, `Kraken_crypto`, `crypto`, `equity_etf`, `yfinance_ETF`, `yfinance_US_ETF`, `yfinance_crypto`, `yfinance_futures` | 16 |
| `Bear` | `15m`, `1h` | `CME_futures_local`, `IBKR_US_ETF`, `Kraken_crypto`, `index`, `single_stock`, `yfinance_ETF`, `yfinance_US_ETF`, `yfinance_crypto`, `yfinance_futures` | 46 |
| `Sideways` | `15m`, `1h` | `CME_futures_local`, `IBKR_US_ETF`, `Kraken_crypto`, `index`, `single_stock`, `yfinance_ETF`, `yfinance_US_ETF`, `yfinance_crypto`, `yfinance_futures` | 40 |
| `Crisis` | `1d`, `1w` | `crypto`, `equity_etf`, `index`, `single_stock` | 45 |
| `Manipulation` | event-window evidence only | accepted slices are Mehrnoom Telegram direct event and Zenodo DEX bounded self-trade | full direct-variety coverage false |

## Latest Source Delta

`20260511T104752-codex-current-public-source-delta-audit` audited fresh public Kaggle/Hugging Face candidates and added:

- Accepted parent-root slots: `0`.
- Accepted direct `Manipulation` rows: `0`.
- Gate result: `blocked_current_public_source_delta_no_attachable_mainregimev2_labels`.

## Decision

- Goal achieved: `false`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_completion_audit_v6_scope_limited_95_not_full_cycle_full_universe`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Run or acquire a true full-matrix MainRegimeV2 parent-root label/evidence batch across available providers, instruments, and timeframes; keep `Manipulation` split by direct evidence variety and do not accept OHLCV proxies.
