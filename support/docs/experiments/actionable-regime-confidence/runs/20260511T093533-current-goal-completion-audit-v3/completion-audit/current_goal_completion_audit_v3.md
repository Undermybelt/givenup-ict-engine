# Current Goal Completion Audit v3

Run ID: `20260511T093533+0800-current-goal-completion-audit-v3`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Objective

Every active regime must reach 95%-99% calibrated confidence, and the result must validate across other markets and other timeframes before reporting the outcome.

Concrete deliverables:

- Use the named Board A TODO as the authoritative artifact.
- Prove each active MainRegimeV2 parent root at 95%-99% calibrated confidence: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Validate each accepted root across other markets and other timeframes/full-cycle/full-universe slots.
- Keep `Manipulation` separate and require direct timestamped positive/negative event, order-flow, order-lifecycle, L2/L3/MBO, wash-trade, spoofing/layering, or comparable labels.
- Do not promote subtype, OHLCV proxy, HMM/GMM/cluster ID, future target, model-generated, Pine indicator, service API, or methodology-only evidence.
- Report the result from concrete repo artifacts.

## Current Taxonomy Readback

- Latest taxonomy lock: `docs/experiments/actionable-regime-confidence/runs/20260511T093157-codex-mainregimev2-current-user-lock/taxonomy/mainregimev2_current_user_lock.json`
- Active taxonomy: `MainRegimeV2`
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`
- Residual: `UnknownOrMixed`
- Separate overlay/class: `Manipulation`

## Result

- Goal achieved: `false`
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`
- Missing/rejected parent-root source-label slots: `564`
- Missing by root: `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141`
- Missing by provider: `yfinance=456`, `kraken_public_lowpollution_http=108`
- Missing by timeframe: `1m=68`, `5m=68`, `15m=68`, `30m=68`, `1h=68`, `4h=68`, `1d=44`, `1w=44`, `1mo=68`
- Accepted direct `Manipulation` rows/windows added: `0`
- Runtime code changed: false
- Thresholds relaxed: false
- Raw data committed: false
- Trade usable: false

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| Use named Board A TODO as authoritative artifact | `pass` | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | Current Cursor and run sections are in the named file. |
| Every active parent-root regime reaches 95%-99% calibrated confidence | `fail` | `accepted_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal` | No all-root 95%-99% gate is accepted after the current lock. |
| Validate across other markets and other timeframes | `fail` | `564` missing/rejected parent-root source-label slots | The missing shape spans yfinance and Kraken cells. |
| Full-cycle/full-universe coverage | `fail` | `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141` missing/rejected slots | Missing coverage is balanced across all four parent roots. |
| Direct `Manipulation` evidence | `fail` | `0` accepted timestamped direct rows/windows | OHLCV/session/liquidity proxies remain fail-closed. |
| No proxy/subtype promotion | `pass` | `20260511T093157` lock | Six subtype packets are demoted to `sub_regime_evidence_only`. |
| Report result from concrete artifacts | `pass` | this v3 audit and Board A Current Cursor | The reported result is blocked, not achieved. |

## Single Blocker

`564` missing/rejected parent-root source-label slots plus incomplete direct `Manipulation` label coverage.

## Next Action

Obtain a downloadable/authenticated exact-underlying parent-root label panel for `Bull`, `Bear`, `Sideways`, and `Crisis`, or authenticated timestamped direct `Manipulation` positive/negative rows. Do not repeat proxy or metadata-only searches.
