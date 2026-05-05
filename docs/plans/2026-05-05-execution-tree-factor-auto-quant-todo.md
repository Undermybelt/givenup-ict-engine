# Execution-Tree Auto-Quant Factor TODO

> Authoritative todo board for execution-tree-driven factor iteration.  
> This file is docs-only and should be updated in place after every real loop slice.

**Goal:** drive Auto-Quant factor iteration from the execution tree’s actual decision needs rather than from the current in-repo factor registry, and keep iterating until every factor family is either exhausted, blocked by missing data/surface, or externalized as a future implementation need.

**Architecture:** treat `ict-engine` as the execution-tree judge and Auto-Quant as the factor author / mutator. The execution tree defines what capabilities are missing or weak; Auto-Quant supplies or mutates factor families to improve those capabilities. Current in-repo factors may be used as temporary bootstrap seeds, but they are not the design boundary, and the agent must retain freedom to hardcode or synthesize factor families inside the Auto-Quant research workspace without requiring repo code changes first.

**Tech Stack:** `./target/debug/ict-engine analyze`, `factor-research --backend auto-quant`, `factor-autoresearch --backend auto-quant`, `factor-autoresearch-status`, `workflow-status --human`, `artifact-status`, `auto-quant-status`, isolated `/tmp/...` state dirs.

**Baseline / Authority Refs:** `src/application/orchestration/execution_tree.rs`, `src/application/execution/inputs.rs`, `src/application/execution/artifact.rs`, `src/application/reflection/execution_tree_bundle.rs`, `src/factor_research_command.rs`, `docs/execution-paper-notes-and-plan-update.md`, `docs/plans/factor-autoresearch-minimal-loop.md`, `docs/plans/2026-05-03-repo-action-board.md`.

**Compatibility Boundary:** preserve zero-config default behavior, consumer-usable CLI surfaces, token-friendly human/compact outputs, and low-pollution execution through explicit `/tmp/...` state dirs. Do not let the current Rust factor registry cap the factor family design space. Do not require repo code changes just to continue the Auto-Quant research loop.

**Verification:** every lane must be proven by real command artifacts:
- `./target/debug/ict-engine analyze ... --human`
- `./target/debug/ict-engine factor-research ... --backend auto-quant --human`
- `./target/debug/ict-engine factor-autoresearch ... --backend auto-quant`
- `./target/debug/ict-engine factor-autoresearch-status ... --latest-only`
- `./target/debug/ict-engine workflow-status ... --human`

---

## Fact / Assumption / Unknown

### Fact

- This todo is guidance-only. It should constrain loop shape and verification, but it should not overconstrain the agent’s factor design space once the execution-tree need is clear.
- The reverse chain is not `execution tree -> factor` directly. The actual chain is:
  - execution tree branch / gate / bias
  - execution artifact + execution features
  - CatBoost / XGBoost policy surfaces and prediction vote score
  - Bayesian belief / BBN nodes and evidence-quality path
  - temporal / HMM / regime filter layer
  - factor families and Auto-Quant iteration
- The execution tree branches on:
  - `execution_readiness`
  - `prediction_vote_score`
  - `evidence_quality`
  - `ising_phase_transition_risk`
  - `pythagorean_overstretch`
  - spectral penalty inputs (`spectral_entropy`, `dominant_cycle_energy`, `cycle_phase_alignment`)
- `execution_readiness` is not a pure price-direction score. It is execution-first and can block even when prediction is directionally strong.
- The current public Auto-Quant loop can already run from repo CLI:
  - `factor-research --backend auto-quant`
  - `factor-autoresearch --backend auto-quant`
  - `factor-autoresearch-status`
- The current public research CLI exposes:
  - main historical data
  - optional paired data
  - no dedicated public auxiliary / options surface

### Assumption

- The correct factor backlog is defined by the execution tree’s missing capabilities, not by whichever factors the current Rust registry already happens to expose.
- Auto-Quant should iterate factor families lane-by-lane, not treat the whole factor universe as one giant undifferentiated search.
- Once a capability gap is identified, the agent may express it as a temporary hardcoded factor family or strategy hypothesis inside Auto-Quant, even if no equivalent factor exists yet in the Rust registry.

### Unknown

- Which required factor families can be satisfied by mutating current bootstrap seeds versus needing genuinely new external factor ideas.
- Which lanes will plateau because the missing ingredient is data/surface, not factor logic.

## Execution-Tree Reverse Map

Before mapping to factor families, preserve this reasoning order:

1. identify the execution-tree failure mode
2. identify which execution feature or physics overlay is weak
3. identify whether the weakness actually comes from:
   - prediction vote layer
   - belief / BBN evidence layer
   - HMM / regime filter layer
   - factor family itself
4. only then decide which factor family Auto-Quant should mutate or invent

Do not jump from branch name straight to factor family if an upstream layer is the real bottleneck.

### Branch 1: `block_crowded`

**Tree trigger**
- `execution_readiness < EXECUTION_GATE_OBSERVE`
- or `ising_phase_transition_risk >= 0.70`

**Capability need**
- distinguish “prediction is interesting” from “execution is too crowded / too fragile to act”

**Required factor family**
- crowding / herding execution-risk factors

**Typical factor ideas**
- participation concentration
- same-side crowding pressure
- crowding relief after sweep / liquidity event
- dealer positioning and hedge-flow pressure
- execution fragility under regime phase transition

### Branch 2: `wait_for_reversion`

**Tree trigger**
- `pythagorean_overstretch >= 0.70`
- OU / spectral layers later penalize readiness

**Capability need**
- determine whether current stretch is tradeable continuation, exhausted continuation, or feasible reversion

**Required factor family**
- stretch / reversion feasibility factors

**Typical factor ideas**
- geometric overstretch distance
- OU reversion half-life / expected pullback speed
- continuation-vs-reversion asymmetry after displacement
- exhaustion after multi-leg extension

### Branch 3: `fill_viable`

**Tree requirement**
- stronger `prediction_vote_score`
- stronger `execution_readiness`
- lower posterior uncertainty
- explanation of why execution dominates

**Capability need**
- separate “good setup but bad timing” from “good setup and good execution window”

**Required factor families**
- structure and setup-quality factors
- directionality / momentum factors
- evidence-integrity / confirmation factors

### Cross-cutting gate: weak evidence

**Tree symptom**
- execution readiness never rises enough because `evidence_quality` remains soft or mixed

**Capability need**
- quality scoring and confirmation, not just raw alpha

**Required factor family**
- evidence-integrity / confirmation factors

### Cross-cutting gate: noisy / chaotic execution environment

**Tree symptom**
- readiness penalty from spectral layer

**Capability need**
- know when the market is too rhythmically unstable to trust the entry

**Required factor family**
- spectral rhythm / chaos execution filters

## Required Factor Families

These are the factor families the execution tree actually needs. They are the design backlog. They are not capped by the current Rust registry.

### Family A: Structure / Setup Quality

**Purpose**
- improve `evidence_quality`
- improve `liquidity_absorption_bias`
- improve setup classification before execution

**Typical subfactors**
- sweep-return quality
- displacement quality
- FVG / OB / CISD confluence quality
- setup recency and completion quality
- post-manipulation continuation clarity

**Execution-tree role**
- primary input to `fill_viable`
- partial relief for false `block_crowded`
- partial relief for false `wait_for_reversion`

### Family B: Directionality / Persistence

**Purpose**
- improve `prediction_vote_score`
- raise confidence only when directional continuation is real

**Typical subfactors**
- momentum persistence
- slope persistence
- trend continuation strength
- continuation failure / exhaustion signs

**Execution-tree role**
- turn viable-but-passive execution into higher-confidence actionable execution
- prevent weak-direction fills from being overpromoted

### Family C: Cross-Market Confirmation

**Purpose**
- improve `evidence_quality`
- reduce false positives when the primary market disagrees with its paired confirmation market

**Typical subfactors**
- SMT divergence / agreement
- leader-laggard confirmation
- correlation-consistency regime fit
- paired-market quality gating

**Execution-tree role**
- strongest current public lane for reducing false aggressive bias
- useful for suppressing weak `fill_viable`

### Family D: Stretch / Reversion Feasibility

**Purpose**
- decide whether an overstretched move should still be executed, observed, or faded

**Typical subfactors**
- normalized overstretch
- pullback feasibility
- OU reversion speed
- exhaustion after leg extension
- bounce probability after displacement

**Execution-tree role**
- primary antidote for false `wait_for_reversion`

### Family E: Crowding / Herding Execution Risk

**Purpose**
- explain and predict execution crowding degradation

**Typical subfactors**
- same-direction herd intensity
- crowding persistence
- crowding collapse / release setup
- crowding + options / dealer positioning interaction

**Execution-tree role**
- primary antidote for false `block_crowded`
- also a blocker family that should override pure prediction strength

### Family F: Spectral Rhythm / Chaos

**Purpose**
- identify when price action is too chaotic or too rhythmically unstable for execution confidence

**Typical subfactors**
- spectral entropy
- dominant cycle energy
- cycle-phase alignment
- rhythm stability / instability transitions

**Execution-tree role**
- execution-readiness filter
- secondary blocker even when setup and direction look good

### Family G: Options / Dealer Positioning

**Purpose**
- inject options-derived execution pressure where available

**Typical subfactors**
- gamma skew
- hedge pressure
- put/call OI imbalance
- IV / convexity concentration around execution zone

**Execution-tree role**
- partial proxy for crowding
- partial proxy for reversion pressure

**Current public status**
- blocked as a real lane until a stable public auxiliary/options research input exists

### Family H: Session / Liquidity Window Quality

**Purpose**
- differentiate execution quality by session condition rather than by setup alone

**Typical subfactors**
- session participation quality
- kill-zone alignment
- session transition risk
- liquidity window quality

**Execution-tree role**
- execution-readiness multiplier across all branches

## Auto-Quant Loop Order

This is the closed-loop order, independent of current Rust factor names.

### Loop 0: Baseline Snapshot

Before any family iteration:

```bash
./target/debug/ict-engine analyze \
  --symbol <SYM> \
  --data-htf <htf.json> \
  --data-mtf <mtf.json> \
  --data-ltf <ltf.json> \
  --state-dir /tmp/ict-engine-exec-tree-baseline \
  --human

./target/debug/ict-engine workflow-status \
  --symbol <SYM> \
  --state-dir /tmp/ict-engine-exec-tree-baseline \
  --human
```

Record:
- current execution-tree branch
- current execution bias
- current next action
- current blocker family

### Loop 1: Family A Structure / Setup Quality

Run this first because it is the highest-leverage family for `evidence_quality` and execution viability.

### Loop 2: Family B Directionality / Persistence

Run second, but only after Structure / Setup Quality has a stable baseline. Otherwise you risk optimizing prediction without improving execution.

### Loop 3: Family C Cross-Market Confirmation

Run once paired data is available for the same symbol/window.

### Loop 4: Family D Stretch / Reversion Feasibility

Run when the baseline tree repeatedly lands on `wait_for_reversion`.

### Loop 5: Family E Crowding / Herding Execution Risk

Run when the baseline tree repeatedly lands on `block_crowded`.

### Loop 6: Family F Spectral Rhythm / Chaos

Run when readiness remains weak despite decent setup and direction, and the spectral layer is likely the hidden blocker.

### Loop 7: Family G Options / Dealer Positioning

Keep blocked until auxiliary/options data becomes a first-class public research input.

### Loop 8: Family H Session / Liquidity Window Quality

Run when a family appears promising but only in certain sessions / liquidity windows.

## Loop Contract Per Family

For each family:

1. Start with one `factor-research --backend auto-quant --human` pass.
2. Use that run to define or refine the family’s mutation direction.
3. Switch into `factor-autoresearch --backend auto-quant`.
4. After each Auto-Quant batch, read:
   - `factor-autoresearch-status --latest-only`
   - `workflow-status --human`
5. Continue the family only if the targeted execution-tree weakness is actually moving.
6. Stop and mark exhausted if:
   - accepted mutations stop changing the tree branch / gate / execution bias
   - the same failure cluster repeats 3 times
   - gains are only in return metric, not in execution-tree development

## Exact Command Skeleton

Use one isolated state dir per family:

```bash
./target/debug/ict-engine factor-research \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective <generic|expansion_manipulation> \
  --state-dir /tmp/ict-engine-family-<family-slug> \
  --backend auto-quant \
  --human

./target/debug/ict-engine factor-autoresearch \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective <generic|expansion_manipulation> \
  --state-dir /tmp/ict-engine-family-<family-slug> \
  --backend auto-quant \
  --iterations 5

./target/debug/ict-engine factor-autoresearch-status \
  --symbol <SYM> \
  --state-dir /tmp/ict-engine-family-<family-slug> \
  --latest-only

./target/debug/ict-engine workflow-status \
  --symbol <SYM> \
  --state-dir /tmp/ict-engine-family-<family-slug> \
  --human
```

For cross-market families, add:

```bash
--paired-data <paired.json>
```

## Current Todo Board

### Done

- [x] Read execution-tree owner code.
- [x] Read execution feature / artifact owner code.
- [x] Read current factor CLI loop surfaces.
- [x] Separate “execution-tree needs” from “current in-repo registry names”.
- [x] Identify which family is blocked by missing public input surface rather than by missing factor logic.

### Next

- [ ] Establish the baseline execution-tree snapshot for the target symbol.
- [ ] Run Family A: Structure / Setup Quality.
- [ ] Re-check execution tree. If the blocker is still setup quality, keep iterating Family A; otherwise move on.
- [ ] Run Family B: Directionality / Persistence only after Family A is stable.
- [ ] Run Family C: Cross-Market Confirmation once paired data exists.
- [ ] Run Family D whenever `wait_for_reversion` is the persistent blocker.
- [ ] Run Family E whenever `block_crowded` is the persistent blocker.
- [ ] Run Family F whenever readiness is suppressed by noise/chaos rather than by setup.
- [ ] Keep Family G blocked until options/auxiliary public input exists.
- [ ] Run Family H when execution viability is clearly session-dependent.

### Not Yet

- [ ] Treat current Rust factor registry as the final factor universe.
- [ ] Implement new factor families in repo code before Auto-Quant iteration proves they are needed.
- [ ] Pretend `options_hedging` is a complete public lane before auxiliary/options input exists.

## Blocked

- [ ] Family G Options / Dealer Positioning
  - blocker: public `factor-research` / `factor-autoresearch` does not yet expose a dedicated auxiliary/options input
  - acceptable temporary state: leave blocked and continue the rest of the execution-tree family backlog

## Verification Checklist

- [ ] Every family uses its own isolated `/tmp/...` state dir.
- [ ] Every family logs one before/after `workflow-status --human` snapshot.
- [ ] Every family has an explicit stop reason: `improved`, `plateaued`, `data_blocked`, or `surface_blocked`.
- [ ] No family is declared “done” from return improvement alone; it must help execution-tree development.
