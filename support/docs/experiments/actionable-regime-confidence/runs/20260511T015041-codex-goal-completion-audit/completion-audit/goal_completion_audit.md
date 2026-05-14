# Goal Completion Audit

Run id: `20260511T015041+0800-codex-goal-completion-audit`

## Objective

`docs/plans/2026-05-10-actionable-regime-confidence-todo.md` must not report success until every active MainRegimeV2 regime has calibrated confidence at or above 95%.

Concrete success criteria:
- Active release axis is MainRegimeV2: `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`; `UnknownOrMixed` is residual and cannot be promoted as release confidence.
- Each active root has its own accepted 95 packet with chronological calibration/test evidence.
- Subtype/signature packets do not count as root completion unless reissued through the active root gate.
- `Manipulation` must use direct L2/L3/MBO/order-lifecycle or event/social/on-chain evidence; OHLCV, liquidity, sweep-like, session, or volume-ratio proxies are not enough.
- Thresholds are not relaxed and runtime code is not changed for the evidence claim.

## Prompt-To-Artifact Checklist

| Requirement | Evidence Inspected | Result |
|---|---|---|
| Board file is the authoritative artifact | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | present |
| Active root axis is MainRegimeV2 | board Current Cursor and active-axis sections | present |
| `Bull` >= 95 | `20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_probe_summary.csv` | missing; test Wilson95 LCB 0.336235 |
| `Bear` >= 95 | same summary CSV | missing; test Wilson95 LCB 0.263968 |
| `Sideways` >= 95 | same summary CSV | missing; test Wilson95 LCB 0.457435 |
| `Crisis` >= 95 | same summary CSV | accepted_95; test Wilson95 LCB 0.995981 |
| `Manipulation` >= 95 with direct/event evidence | `20260511T014742-codex-pump-dump-manipulation-event-gate` and `20260511T014630-codex-provider-export-readiness-contract` | missing; event/social gate accepted_95 false and provider export not ready |
| No threshold relaxation | provider/export, Tomac, and pump/dump assertion files | confirmed false |
| No runtime code change | provider/export, Tomac, and pump/dump assertion files | confirmed false |
| Trade usable | latest evidence packets | false |

## Root Audit

| MainRegimeV2 Root | State | Current Strongest Direct Evidence | Release Status |
|---|---|---|---|
| `Bull` | missing_95_root_packet | Best active-root summary row inspected: test Wilson95 LCB `0.3362347730812829`; blockers include calibration/test Wilson below 0.95 and ECE above 0.05. | blocked |
| `Bear` | missing_95_root_packet | Best active-root summary row inspected: test Wilson95 LCB `0.26396770345110193`; blockers include calibration/test Wilson below 0.95, ECE above 0.05, and validation timeframes below 2. | blocked |
| `Sideways` | missing_95_root_packet | Best active-root summary row inspected: test Wilson95 LCB `0.4574348340085442`; blockers include calibration/test Wilson below 0.95, ECE above 0.05, and coverage below 0.03. | blocked |
| `Crisis` | accepted_95 | Rule `range_ratio32_128 >= 1.43116959912`, calibration support 1020, test support 952, test Wilson95 LCB `0.9959810711439178`. | accepted_95 |
| `Manipulation` | missing_95_root_packet | Pump/dump event/social dataset accepted_95 false; best test LCBs `0.036087`, `0.052392`, `0.058929`; provider export readiness false. | blocked |

## Decision

Goal achieved: false.

Accepted 95 roots: `Crisis` only.

Missing 95 roots: `Bull`, `Bear`, `Sideways`, and direct-input-gated `Manipulation`.

The next executable action is to acquire broader calibration-grade direct manipulation data plus materially new non-OHLCV signed-direction/sideways evidence, then rerun unchanged MainRegimeV2 gates.

