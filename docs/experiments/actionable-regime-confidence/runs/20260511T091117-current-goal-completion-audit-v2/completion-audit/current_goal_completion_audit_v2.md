# Current Goal Completion Audit v2

Run ID: `20260511T091117+0800-current-goal-completion-audit-v2`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Objective

Every active regime must reach 95%-99% calibrated confidence, and the result must validate across other markets and other timeframes before reporting the outcome.

Concrete deliverables:
- Use the named Board A TODO as the authoritative artifact.
- Prove each active MainRegimeV2 parent root (`Bull`, `Bear`, `Sideways`, `Crisis`) at 95%-99% calibrated confidence.
- Validate across other markets and other timeframes/full-cycle/full-universe slots.
- Prove separate direct `Manipulation` with timestamped positive/negative labels, not OHLCV proxy labels.
- Preserve fail-closed handling for proxy/model-generated/subtype labels.
- Report the result from real artifacts.

## Result

- Goal achieved: `false`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Missing/rejected parent-root source-label slots: `564`.
- Missing by root: `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141`.
- Missing by provider: `yfinance=456`, `kraken_public_lowpollution_http=108`.
- Missing by timeframe: `1m=68`, `5m=68`, `15m=68`, `30m=68`, `1h=68`, `4h=68`, `1d=44`, `1w=44`, `1mo=68`.
- Latest public/source probes since the prior audit added `0` accepted parent-root label slots and `0` accepted direct `Manipulation` label sources.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| Use the named TODO as authoritative artifact | `pass` | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | Current Cursor, run sections, and Evidence Ledger are present in the named board. |
| Every active regime reaches 95%-99% calibrated confidence | `fail` | `accepted_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal` | No all-regime 95%-99% gate is accepted. |
| Validate across other markets and other timeframes | `fail` | `564` missing/rejected parent-root slots across yfinance and Kraken, including intraday/monthly cells | Full cross-market/timeframe source-label coverage remains absent. |
| Full-cycle/full-universe accounting | `fail` | `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141` missing/rejected slots | The missing shape is balanced across all four parent roots. |
| Direct `Manipulation` evidence | `fail` | latest source probes add `0` accepted direct rows/windows; Dune remains blocked without authenticated export | Direct timestamped positive/negative rows are still missing. |
| No proxy labels promoted | `pass` | HMM/GMM/HF/OHLCV/Pine/model-service candidates remain rejected or sidecar-only | Thresholds were not relaxed and child/subtype/proxy packets were not promoted. |
| Report the result | `pass` | this audit report and Board A Current Cursor | The result is reported as blocked, not achieved. |

## Single Blocker

`564` missing/rejected parent-root source-label slots plus incomplete direct `Manipulation` label coverage.

## Next Action

Obtain a downloadable or authenticated exact-underlying parent-root label panel for `Bull`/`Bear`/`Sideways`/`Crisis`, or authenticated timestamped direct `Manipulation` positive/negative rows.
