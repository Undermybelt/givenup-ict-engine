# Current Goal Completion Audit

Run id: `20260511T084755+0800-codex-current-goal-completion-audit`

## Objective

Every regime must reach 95%-99% calibrated confidence and validate across other markets/timeframes/full universe/full cycle.

## Result

- Goal achieved: `false`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Single blocker: `564 missing/rejected source-label slots plus incomplete direct Manipulation label coverage`.
- Missing/rejected slots: `564`.
- Missing by root: `{'Bull': 141, 'Bear': 141, 'Sideways': 141, 'Crisis': 141}`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| Use the named TODO as the authoritative artifact | `pass` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md | Current cursor, run sections, and Evidence Ledger are present in the named TODO. |
| Every active regime reaches 95%-99% calibrated confidence | `fail` | accepted_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal | Current accepted gate is not a completed all-regime gate; expanded full-universe/full-cycle goal remains blocked. |
| Validate across other markets and other timeframes | `fail` | missing/rejected slots=564; by_timeframe={'1m': 68, '5m': 68, '15m': 68, '30m': 68, '1h': 68, '1d': 44, '1w': 44, '1mo': 68, '4h': 68} | Only 48/612 source-label slots are attached from prior evidence; 564 slots remain missing/rejected across intraday, monthly, non-yfinance/Kraken, and missing exact instruments. |
| Full-cycle/full-species coverage | `fail` | by_provider={'yfinance': 456, 'kraken_public_lowpollution_http': 108}; by_root={'Bull': 141, 'Bear': 141, 'Sideways': 141, 'Crisis': 141} | Missing slots are balanced at 141 for each MainRegimeV2 price root, so no root is complete under expanded matrix accounting. |
| Manipulation has direct labeled evidence, not OHLCV proxy | `fail` | Dune gate=blocked_dune_export_missing_api_key; acquisition_new_manipulation=0 | Dune is schema-promising but blocked by missing API/export rows; acquisition probe added 0 direct manipulation sources. |
| No proxy labels promoted as completion | `pass` | HMM/GMM/HF/future-return/near-proxy candidates rejected or sidecar-only | Latest probe preserved fail-closed handling and did not count HMM/GMM/HF/off-universe/near-proxy labels. |

## Next Action

Acquire exact-underlying non-Kaggle root-label panels or authenticated direct Manipulation rows; otherwise the goal remains blocked.
