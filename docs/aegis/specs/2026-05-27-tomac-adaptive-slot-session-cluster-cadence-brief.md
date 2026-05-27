# TOMAC Adaptive Slot Session-Cluster Cadence Brief

## TaskIntentDraft

- Requested outcome: approve a new profitability-factor training document target
  that can be taken over and iterated with Auto-Quant once the current live
  owner becomes stale under the one-hour rule.
- Chosen branch:
  `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`
- Goal: preserve the exact regime-rooted branch grammar, keep the parent
  profitability edge intact, and raise cadence into the target operating band
  without lowering economics or downstream gates.
- Success evidence:
  - the canonical root path and factor lineage are explicit;
  - takeover preconditions are explicit;
  - the future workdoc and claim requirements are explicit;
  - the later Auto-Quant iteration is constrained by current evidence rather
    than by convenience or gate relaxation.
- Stop condition for this brief: approved written design ready for planning; no
  direct lane takeover, no direct Auto-Quant launch, no runtime edits.
- Non-goals:
  - no duplicate write into the currently active cadence lane;
  - no gate relaxation;
  - no new root-family invention in this brief;
  - no `promotion_allowed=true` or `trade_usable=true` claim.

## BaselineReadSetHint

- `docs/aegis/BASELINE-GOVERNANCE.md`
- `support/docs/plans/2026-05-25-board-b-current.md`
- `/tmp/ict-engine-agent-claims/board-b-factor-refinement/`
- `/private/tmp/ict-engine-tomac-adaptive-slot-contrarian-exact-aq-race-repair-20260526T193259+0800/workdoc.md`
- `/private/tmp/ict-engine-tomac-adaptive-slot-contrarian-exact-aq-race-repair-20260526T193259+0800/aq/checks/terminal_metrics.json`
- `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-prep-20260527T125200+0800/workdoc.md`
- `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-relaunch-20260527T170335+0800/workdoc.md`
- `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_tod_contrarian_density_repair_prep_v1.py`
- `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_tod_contrarian_session_cluster_cadence_repair_prep_v1.py`

## ImpactStatementDraft

- Affected layers:
  - Board B factor-document design;
  - later `/tmp` workdoc and claim packet shape;
  - later same-root Auto-Quant launch packet and readback interpretation.
- Invariants:
  - preserve regime-rooted grammar;
  - `1m` origin remains canonical;
  - context frames remain `5m/15m/30m/1h/4h/1d`;
  - target cadence remains between one trade every three days and three trades
    per day;
  - historical or retained-real evidence stays ahead of paper/sim evidence;
  - no lowering of cost, cadence, validation, readiness, transition, ranker, or
    execution gates.
- Compatibility boundary:
  - this brief does not modify runtime code or wrappers;
  - this brief does not authorize colliding with a fresh active claim;
  - this brief does not redefine product/provider/symbol/timeframe provenance as
    branch roots.

## Current Situation

- This branch is already approved as the preferred next TOMAC continuation
  target.
- The lane is not yet available for takeover in this brief's current snapshot
  because the active claim is still fresh.
- Compact audit later cleared `live_factor_processes=0`, but the active claim on
  this exact family remained too recent for a lawful takeover.
- Therefore the right current artifact is a design brief that fixes the future
  takeover target and prevents scope drift.

## Canonical Branch

### Root path

`SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`

### Meaning of each node

- `SessionRhythm` is the main regime root.
- `TimeOfDaySeasonality` is the sub-regime root.
- `AdaptiveSlotContrarian` is the first profitability-factor branch already
  proven to have positive hard-friction expectancy at the parent level.
- `SessionClusterCadenceRepair` is a child profitability factor whose job is to
  repair cadence while staying inside the same profitability lineage.
- `tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1` is the exact
  candidate factor id for later lawful takeover and AQ iteration.

### Grammar rule preserved

- main regime may attach sub-regimes;
- sub-regimes may attach more sub-regimes or the first profitability factor;
- once the path reaches a profitability factor, descendants may only be
  profitability-factor descendants;
- provenance labels such as market, product, symbol, provider, timeframe,
  AQ workspace, or retained-local file path stay outside the rooted branch.

## Why This Branch

- The parent exact branch already proved positive expectancy after hard friction.
- The blocker is not sign; the blocker is sparse cadence.
- That makes this branch a stronger next continuation than paths that still
  fail because of comparability, zero-trade economics, or unrelated branch-root
  drift.
- It is also cleaner than inventing a new TOMAC family while stronger same-root
  evidence already exists.

## Current Evidence Snapshot

### Parent exact AQ evidence

- Parent root:
  `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> tomac_nq_tod_contrarian_slot120_h240_lb80_e75_wr56_rv1_exact_v1`
- Parent exact AQ fail-closed on cadence, not economics:
  - `trade_count=151`
  - `raw_total_profit_pct=21.26`
  - `5bps_per_side_total_profit_pct=6.16`
  - `profit_factor=1.8951`
  - `trades_per_session=0.097044`
- Interpretation:
  the branch has positive hard-friction expectancy but is too sparse for the
  requested practical cadence band.

### Prior child prep evidence

- Previous child packet existed as prep-only under:
  `/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-prep-20260527T125200+0800/workdoc.md`
- Relaunch packet later verified exact-wrapper prep completeness under:
  `/private/tmp/ict-engine-tomac-adaptive-slot-session-cluster-cadence-relaunch-20260527T170335+0800/workdoc.md`
- Latest durable decision on the relaunch packet:
  `exact_wrapper_verified_prep_complete_pending_clear_launch_window`

### Current occupancy constraint

- This family must not be duplicated while another active claim on the exact
  same branch remains fresh.
- The takeover trigger is:
  factor-local workdoc or claim older than one hour and no matching live lane
  process writing under the claimed run root.

## Problem Statement

Raise the parent branch from positive-but-too-sparse toward the target cadence
band without:

- reducing the `5bps` cost standard;
- broadening branch identity;
- weakening downstream, transition, ranker, or execution thresholds;
- or mixing unrelated products/roots into the path.

## Approaches Considered

### Approach A: Adjacent slot/session-cluster merge inside the same root

- Merge or re-bucket nearby session-cluster windows so the contrarian slot
  family fires more often while still respecting session-seasonality structure.
- Pros:
  - directly targets cadence;
  - preserves exact root lineage;
  - best fit for the verified wrapper and current evidence.
- Cons:
  - can damage expectancy if slot broadening becomes indiscriminate;
  - needs exact AQ readback to prove cadence gain did not destroy economics.

### Approach B: Reuse the parent exact logic and add hold-cluster persistence

- Keep current slot definitions but alter hold/exit clustering to reduce wasted
  churn and raise usable trade materialization.
- Pros:
  - lower structural drift;
  - may preserve expectancy better than slot broadening.
- Cons:
  - less direct attack on cadence;
  - risks solving execution shape more than entry frequency.

### Approach C: Start a brand-new TOD child under another family

- Invent a fresh same-root child rather than continuing the current cadence
  child.
- Pros:
  - allows a clean sheet if the current child is fundamentally wrong.
- Cons:
  - weaker evidence basis;
  - higher collision risk and higher chance of scope drift;
  - not justified while the current child still has a verified prep surface.

### Recommendation

- Recommend `Approach A`.
- Reason:
  it is the most direct response to the proven blocker, matches the existing
  wrapper/readback surface, and preserves the strongest same-root profitability
  evidence already present in the branch.

## Future Training Document Requirements

The future authoritative factor workdoc for this branch must contain:

- creation time and owner;
- exact rooted branch path;
- factor id;
- parent factor id;
- provenance labels:
  - retained-local or provider source;
  - `1m` origin;
  - `5m/15m/30m/1h/4h/1d` context frames;
  - target symbol scope;
- explicit non-goals;
- carried parent evidence roots;
- exact launch command;
- compact root and `/tmp` run root;
- blocker statement and next gate;
- terminal decision fields:
  `promotion_allowed`, `trade_usable`, `update_goal`.

## Takeover Rule

- If the factor document or active claim has not been modified for more than one
  hour, and no matching live lane process is writing under the exact run root,
  the next agent may take it over.
- The takeover packet must append:
  - takeover timestamp;
  - takeover agent name;
  - takeover reason;
  - takeover run root;
  - refreshed progress report;
  - explicit false values for `promotion_allowed`, `trade_usable`, and
    `update_goal` unless current-turn artifacts prove otherwise.

## AQ Handoff Rules

- Historical/retained-real evidence comes first.
- IBKR history or simulated evidence is secondary and only useful after same-root
  historical gates stay intact.
- Any later AQ rerun must preserve:
  - exact root identity;
  - exact factor lineage;
  - explicit cost model;
  - cadence readback;
  - downstream/evidence packet paths.
- The later packet must classify itself explicitly as one of:
  - prep-only wrapper verification;
  - exact AQ cadence repair;
  - downstream materialization readback;
  - paper/sim execution-readiness evidence.

## Testing And Verification Expectations

- Before any takeover launch:
  - rerun the compact claim audit;
  - confirm no live lane writer exists;
  - confirm the exact wrapper help/prep surface remains safe.
- During execution:
  - preserve same-root artifact truth in `/tmp` and compact-root packets;
  - use current-turn command evidence only.
- After execution:
  - read back Gate 1 economics, cadence, validation, readiness, transition, and
    execution-tree classification;
  - fail closed if cadence rises but economics or downstream gates regress.

## Explicit Non-Claims

- This brief does not claim the child is already promotable.
- This brief does not claim the child is already trade-usable.
- This brief does not claim the active owner is stale yet.
- This brief does not authorize bypassing Board B occupancy discipline.

## Recommended Decision

- Approved next takeover target:
  `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian -> SessionClusterCadenceRepair -> tomac_nq_tod_contrarian_session_cluster_cadence_repair_1m_v1`
- Recommended action after this brief:
  write the implementation plan for stale-safe takeover and exact AQ cadence
  iteration, then wait for or verify lawful takeover conditions before touching
  the lane.
