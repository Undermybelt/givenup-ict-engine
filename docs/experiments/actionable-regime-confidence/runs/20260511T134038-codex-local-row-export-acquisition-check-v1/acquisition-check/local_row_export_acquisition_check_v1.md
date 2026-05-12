# Local Row Export Acquisition Check v1

Run ID: `20260511T134038+0800-codex-local-row-export-acquisition-check-v1`

## Result

- FINRA-like spoofing/layering positive rows found locally: `0`.
- FINRA-like matched negative rows found locally: `0`.
- Native intraday/full-species `MainRegimeV2` source-label panels found locally: `0`.
- Accepted direct `Manipulation` windows added: `0`.
- Gate result: `blocked_local_row_export_acquisition_check_no_accepted_exports_found`.
- Full objective achieved: `false`.

## Scope

Bounded local search only:

- `/Users/thrill3r/Downloads`
- `/Users/thrill3r/Documents`
- `/Users/thrill3r/Desktop`
- `/private/tmp`
- `/tmp`
- `docs/experiments/actionable-regime-confidence/runs`

Search patterns were limited to FINRA, potential manipulation, spoofing, layering, quote stuffing, order book, market regime labels, and regime labels.

## Findings

- Found local order-book/CLOB scripts under `Downloads`, but they are scripts, not labeled positive/negative rows.
- Found Polymarket order-book/event parquet sidecars under `/private/tmp/ict-regime-direct-manipulation-schema-20260511T081556`, but existing schema audit already records these as unlabeled and accepted direct windows as `0`.
- Found HMM/model-inferred NQ 15m label files under `/private/tmp`; these remain rejected proxy labels for completion.
- Found the repo-local FINRA acquisition schema package from `133337`, but no matching row exports.

## Decision

The next action remains external acquisition: provide or authenticate row exports matching the FINRA spoofing/layering schema, or provide an exact native intraday/full-species `MainRegimeV2` source-label panel.

Guardrails:

- No runtime code changed.
- No thresholds relaxed.
- No raw data committed.
- No trade usability claimed.
- Proxy/model/synthetic/unlabeled order-book files remain fail-closed.
