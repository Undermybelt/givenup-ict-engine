# Board B KAMA Efficiency Pullback Brief

## Status

- approved_direction: `B`
- approved_at: `2026-05-26`
- design_state: `approved_family_written_for_review`
- implementation_state: `not_started`

## TaskIntentDraft

- Create one new Board B profitability-factor training document for a regime-rooted branch.
- Keep the branch grammar strict: main regime and sub-regime remain root structure; the first profitability factor is a single child branch, not a mixed basket.
- Start from `1m`, keep `5m/15m/30m/1h/4h/1d` as context/resonance evidence, and feed real backtest or IBKR-sim evidence forward into later stages.
- Do not lower gates to force passage.
- Do not duplicate another live agent lane.

## BaselineReadSetHint

- [AGENT.md](/Users/thrill3r/projects-ict-engine/ict-engine/AGENT.md:1)
  Repo authority for Board B claim/workdoc discipline and evidence-first execution.
- [SKILL.md](/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md:1)
  Board B factor-research constraints, stale takeover rules, and prep-only staging policy.
- [brainstorming SKILL.md](/Users/thrill3r/.codex/aegis/skills/brainstorming/SKILL.md:1)
  Hard gate requiring design approval before implementation.
- [20260526T132732+0800-codex-ibkr-mes-kama-efficiency-pullback-training.md](/Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence/20260526T132732+0800-codex-ibkr-mes-kama-efficiency-pullback-training.md:1)
  Prior exact MES KAMA branch that must be preserved as a negative sample, not reopened as the new exact cell.
- [run_ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1.py](/Users/thrill3r/projects-ict-engine/ict-engine/support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1.py:1)
  Reusable script pattern for a KAMA efficiency pullback family runner.

## ImpactStatementDraft

- Affected surfaces: new Board B design/spec doc first; later plan will own the repo packet, `/tmp` workdoc, `/tmp` claim, and exact runner or prep wrapper.
- Compatibility boundary: no change to existing terminalized negative packets, no reuse of a live owner lane, and no relaxation of `5bps`, density, or downstream gates.
- Non-goals:
  - Do not reopen the old `MES 1m KAMA efficiency pullback` exact root.
  - Do not mix multiple first-profit-factor children under one fresh branch.
  - Do not treat higher-timeframe context as a substitute for exact `1m` economics.

## Problem

The user approved the `KAMA efficiency pullback` family as the next direction, but the most recent same-family exact branch already exists as a terminalized negative sample on `MES 1m`. The next slice therefore needs a new exact cell that keeps the approved family while avoiding duplicate live work and avoiding the already-cooled exact `MES` cell.

## Current Evidence

- Fresh Board B compact audit in this turn dropped to `active_claims=2` and does not show an active KAMA family lane.
- The old exact KAMA lane is preserved as:
  `TrendEfficiency -> KaufmanAdaptivePullback -> KaufmanAdaptivePullback -> ibkr_mes1m_kama_efficiency_pullback_7d_gate1_v1`
- That exact `MES` branch failed practical cost economics:
  `64` trades, raw `+0.56%`, `1bps=-0.72%`, `2bps=-2.00%`, `5bps=-5.84%`.
- Therefore the approved family may continue, but the exact `MES/1m/KAMA` cell must cool down and remain a negative sample.

## Approved Branch Design

### Canonical grammar

The new branch must use this rooted path shape:

`TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> <exact_factor_id>`

Interpretation:

- `TrendExpansion` is the main regime root.
- `MtfTrendAlignment` is the sub-regime that gates whether higher frames are aligned strongly enough to justify continuing work.
- `KAMAEfficiencyPullbackContinuation` is the first profitability-factor child.
- `<exact_factor_id>` is the exact implementation leaf for the chosen market/product/symbol/timeframe cell.

This replaces the older `TrendEfficiency -> KaufmanAdaptivePullback -> KaufmanAdaptivePullback` grammar for the new slice. The old grammar stays archived as historical evidence only.

### Exact cell selection rule

Choose exactly one fresh IBKR futures cell using this deterministic order:

1. `M2K 1m`
2. `MYM 1m`
3. Stop and re-audit if both are occupied or already terminalized for the same family

Rationale:

- The current compact audit does not show active KAMA family ownership on `M2K` or `MYM`.
- `MES 1m` already received a fair same-family Gate 1 attempt and must cool down.
- The rule is deterministic, so implementation will not drift into ad hoc symbol picking.

### Exact factor id format

For the preferred cell:

`ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1`

If `M2K` is blocked at implementation time and `MYM` is free:

`ibkr_mym1m_kama_efficiency_pullback_7d_gate1_v1`

## Economic and regime rules

- Exact origin is always `1m`.
- `5m/15m/30m/1h/4h/1d` are context frames only.
- A higher frame counts as aligned only when its direction is consistent and its slope is large enough to plausibly cover the hard `10bps` round-trip floor.
- The branch should target a trading cadence between `one trade every three days` and `three trades per day`.
- If cadence is lower or higher, the branch fails design intent unless a later approved descendant explicitly changes the density objective.

## Entry hypothesis

The new exact leaf should express this logic:

- Detect a trend-expansion state on `1m` with higher-frame confirmation.
- Use KAMA or closely related efficiency-ratio measures to confirm adaptive trend quality rather than simple momentum chase.
- Wait for a pullback or reclaim into the adaptive trend envelope.
- Enter only when the pullback resumes in the direction of the rooted trend and the higher-frame alignment remains intact.

## Evidence chain contract

The branch is not complete at Gate 1. The intended chain is:

1. IBKR historical or IBKR sim-admission preflight
2. AutoQuant Gate 1 exact-root run
3. Import/prior surfaces
4. Pre-Bayes / filter
5. BBN
6. CatBoost / path-ranker
7. Execution tree
8. Feedback/update evidence

Every downstream surface must keep the rooted path intact and use the regime-rooted branch path as the parent identity.

## Required artifacts for implementation

The later implementation plan must create:

- one repo-local Board B training packet for this exact branch
- one factor-local `/tmp` workdoc
- one valid `/tmp` claim pointing at that workdoc
- one exact runner or prep-only runner for the chosen `M2K` or `MYM` cell
- one identity test that asserts the new branch path and factor id

## Compatibility boundary

- Do not modify or overwrite any existing terminalized `MES KAMA` packet.
- Do not touch active `MNQ KST/Coppock` or active `TOMAC WPR` lanes.
- Do not lower `5bps`, density, yearly stability, or downstream release gates.
- Do not let context frames replace the exact `1m` root.

## Risks and unknowns

- The existing reusable KAMA runner pattern is tied to the older `TrendEfficiency` grammar, so implementation may need a new exact runner rather than a direct rename.
- IBKR row availability for `M2K` or `MYM` still needs same-turn verification at implementation time.
- If both `M2K` and `MYM` become occupied before implementation starts, the plan must stop and re-audit instead of silently switching markets.

## Decision

Approved family direction is locked as:

`TrendExpansion -> MtfTrendAlignment -> KAMAEfficiencyPullbackContinuation -> <exact_factor_id>`

The preferred first exact cell is:

`ibkr_m2k1m_kama_efficiency_pullback_7d_gate1_v1`

with a deterministic fallback to:

`ibkr_mym1m_kama_efficiency_pullback_7d_gate1_v1`

only if `M2K` is no longer collision-safe at implementation time.
