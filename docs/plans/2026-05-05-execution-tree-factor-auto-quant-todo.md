# Execution-Tree Factor Auto-Quant TODO

> **For agentic workers:** use this markdown as the execution contract for factor iteration work. Keep it in todo form. Update the same file in place after every lane or blocker change.

**Goal:** derive the factor iteration order from the execution tree itself, then use that ordering to drive an Auto-Quant loop until every unblocked factor lane is exhausted or externalized.

**Architecture:** the execution tree does not consume factor names directly. It consumes `execution_readiness`, `execution_score`, `evidence_quality`, `prediction_vote_score`, physics overlays (`OU`, `Ising`, `Pythagorean`, `spectral`), and `hmm_posterior`. Therefore this board works backward from those execution-tree inputs to the factor families that can actually move them, and separates: `can iterate now`, `needs paired data`, and `blocked by missing public input surface`.

**Tech Stack:** Rust CLI (`analyze`, `factor-research`, `factor-autoresearch`, `factor-autoresearch-status`, `workflow-status`, `artifact-status`, `auto-quant-status`), managed Auto-Quant backend, `/tmp` state dirs, repo docs under `docs/plans/`.

**Baseline / Authority Refs:** `src/application/orchestration/execution_tree.rs`, `src/application/execution/inputs.rs`, `src/application/execution/artifact.rs`, `src/factors/registry.rs`, `src/factor_lab/factor_definition.rs`, `src/factor_research_command.rs`, `docs/plans/factor-autoresearch-minimal-loop.md`, `docs/execution-paper-notes-and-plan-update.md`, `docs/plans/2026-05-03-repo-action-board.md`.

**Compatibility Boundary:** preserve zero-config defaults, consumer-usable CLI, token-friendly surfaces, explicit opt-in for personal/provider reuse, and no repo pollution outside chosen `/tmp` state dirs. Do not invent factor families that the current public CLI cannot feed unless they are explicitly marked blocked.

**Verification:** every factor lane must prove itself with real CLI artifacts, not only chat reasoning:
- `./target/debug/ict-engine analyze ... --human`
- `./target/debug/ict-engine factor-research ... --backend native --human`
- `./target/debug/ict-engine factor-autoresearch ... --backend auto-quant`
- `./target/debug/ict-engine factor-autoresearch-status ... --latest-only`
- `./target/debug/ict-engine workflow-status ... --human`

---

## Fact / Assumption / Unknown

### Fact

- The execution tree branches on four primary decision inputs from code:
  - `execution_readiness`
  - `prediction_vote_score`
  - `evidence_quality`
  - physics overlays: `ising_phase_transition_risk`, `pythagorean_overstretch`, plus spectral penalties
- `ExecutionFeatures` are built from:
  - `completion_pressure`
  - `liquidity_absorption_bias`
  - `evidence_quality`
  - `prediction_score`
  - OU / spectral / physics overlay fallbacks
- The current factor registry has exactly five public factor families:
  - `trend_momentum`
  - `volatility_mean_reversion`
  - `structure_ict`
  - `cross_market_smt`
  - `options_hedging`
- Public `factor-research` / `factor-autoresearch` CLI currently exposes:
  - primary historical data
  - optional `--paired-data`
  - `--backend native|auto-quant`
  - no public dedicated options / auxiliary evidence input
- `cross_market_smt` requires `paired_candles`.
- `options_hedging` requires `auxiliary` evidence for the real path; without it, it degrades to a volatility-only proxy.

### Assumption

- The best first pass is to exhaust all factor lanes that can move current execution-tree inputs without adding new code.
- Auto-Quant should iterate one factor lane at a time rather than mixing all factors in one undifferentiated loop.

### Unknown

- Whether the current five registered factor families are sufficient to fully explain `block_crowded` and `wait_for_reversion`, or whether new factor families are eventually required.
- Whether the current public surface for `options_hedging` is enough to count as a real lane, or should remain blocked until auxiliary/options input is exposed.

## Execution-Tree Reverse Map

### 1. `block_crowded`

**What the tree is reacting to**
- `execution_readiness < EXECUTION_GATE_OBSERVE`
- or `ising_phase_transition_risk >= 0.70`

**What factors can currently move it**
- `structure_ict`
  - raises or lowers `evidence_quality`
  - influences `gating_status`, therefore `liquidity_absorption_bias`
  - improves setup quality and completion pressure indirectly
- `trend_momentum`
  - strengthens `prediction_vote_score`
  - can stabilize evidence when direction is real
- `cross_market_smt`
  - confirms or downgrades cross-market agreement
  - strongest current tool for reducing false confidence when paired market disagrees
- `options_hedging`
  - only partial today
  - can help crowding / dealer-hedge interpretation, but public research CLI does not feed it real auxiliary data yet

### 2. `wait_for_reversion`

**What the tree is reacting to**
- `pythagorean_overstretch >= 0.70`
- OU / spectral layers later penalize execution readiness even if prediction is directionally correct

**What factors can currently move it**
- `volatility_mean_reversion`
  - current best public proxy for overstretch / reversion feasibility
- `structure_ict`
  - sweep return, displacement, and expansion logic can distinguish reversion after manipulation from blind countertrend fading
- `trend_momentum`
  - tells whether the current move is still persistent enough that fading is premature

### 3. `fill_viable`

**What the tree still needs even when branch is viable**
- stronger `prediction_vote_score`
- stronger `execution_readiness`
- lower posterior uncertainty
- cleaner explanation of why execution dominates

**What factors can currently move it**
- `structure_ict`
  - best current state-transition and setup-classification lane
- `trend_momentum`
  - best current directional evidence lane
- `cross_market_smt`
  - best current cross-market confirmation lane
- `volatility_mean_reversion`
  - only if fill viability depends on reversion structure, not pure continuation

## Factor Lanes

### Lane A: `structure_ict`

**Why this lane exists**
- It is the strongest current bridge between factor space and execution-tree needs.
- It owns `StateTransition`, `SetupClassifier`, and `OutcomeValidator` roles.
- It can move `evidence_quality`, `gating_status`, and therefore `liquidity_absorption_bias`.

**Execution-tree targets**
- reduce false `block_crowded`
- reduce false `wait_for_reversion`
- improve `fill_viable` confidence

**Primary mutation reasons from code**
- `balanced_accuracy_regressed`
- `bull_bear_separation_weak`
- `bridge_gap_too_small`
- `pre_bayes_gate_observe_only`
- `pre_bayes_gate_neutralized`

**Primary command loop**
```bash
./target/debug/ict-engine factor-research \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective expansion_manipulation \
  --state-dir /tmp/ict-engine-exec-tree-structure-ict \
  --backend native \
  --human

./target/debug/ict-engine factor-autoresearch \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective expansion_manipulation \
  --state-dir /tmp/ict-engine-exec-tree-structure-ict \
  --backend auto-quant \
  --iterations 5

./target/debug/ict-engine factor-autoresearch-status \
  --symbol <SYM> \
  --state-dir /tmp/ict-engine-exec-tree-structure-ict \
  --latest-only
```

**Stop condition**
- stop when three consecutive attempts produce no accepted mutation and the same failure cluster / same recommended focus repeats
- or when `workflow-status --human` still points to the same execution-tree weakness after the best accepted mutation is replayed

### Lane B: `trend_momentum`

**Why this lane exists**
- It is the clearest current driver of `prediction_vote_score`.
- It can turn `fill_viable + passive` into `fill_viable + aggressive` only if direction is truly strong.

**Execution-tree targets**
- raise `prediction_vote_score`
- raise `execution_readiness` only when direction and evidence agree

**Primary command loop**
```bash
./target/debug/ict-engine factor-research \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective generic \
  --state-dir /tmp/ict-engine-exec-tree-trend \
  --backend native \
  --human

./target/debug/ict-engine factor-autoresearch \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective generic \
  --state-dir /tmp/ict-engine-exec-tree-trend \
  --backend auto-quant \
  --iterations 5
```

**Stop condition**
- stop when prediction score increases but `execution_readiness` does not improve, meaning the lane is overfitting direction without helping execution

### Lane C: `cross_market_smt`

**Why this lane exists**
- It is the current public lane for paired-market confirmation.
- It is the most direct factor for reducing weak-confidence fills that should stay observe-only.

**Execution-tree targets**
- improve `evidence_quality`
- reduce false aggressive bias
- increase confidence only when paired-market quality is valid

**Required input**
- `--paired-data <paired.json>`

**Primary command loop**
```bash
./target/debug/ict-engine factor-research \
  --symbol <SYM> \
  --data <ltf.json> \
  --paired-data <paired.json> \
  --objective expansion_manipulation \
  --state-dir /tmp/ict-engine-exec-tree-smt \
  --backend native \
  --human

./target/debug/ict-engine factor-autoresearch \
  --symbol <SYM> \
  --data <ltf.json> \
  --paired-data <paired.json> \
  --objective expansion_manipulation \
  --state-dir /tmp/ict-engine-exec-tree-smt \
  --backend auto-quant \
  --iterations 5
```

**Stop condition**
- stop when repeated failures are caused by `paired_market_unavailable`, `invalid_due_to_pair_quality`, or flat paired data rather than the factor itself

### Lane D: `volatility_mean_reversion`

**Why this lane exists**
- It is the current public proxy for the execution tree’s stretch/reversion concerns.
- It is the first lane to use when the branch repeatedly lands on `wait_for_reversion`.

**Execution-tree targets**
- reduce false `wait_for_reversion`
- strengthen reversion quality when fading is actually feasible

**Primary command loop**
```bash
./target/debug/ict-engine factor-research \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective generic \
  --state-dir /tmp/ict-engine-exec-tree-reversion \
  --backend native \
  --human

./target/debug/ict-engine factor-autoresearch \
  --symbol <SYM> \
  --data <ltf.json> \
  --objective generic \
  --state-dir /tmp/ict-engine-exec-tree-reversion \
  --backend auto-quant \
  --iterations 5
```

**Stop condition**
- stop when `wait_for_reversion` remains unchanged and the best accepted mutations only improve return without shifting execution branch behavior

### Lane E: `options_hedging`

**Current status**
- registered in the factor registry
- not yet a clean public Auto-Quant lane

**Why blocked**
- real evaluation depends on `context.auxiliary`
- current public `factor-research` / `factor-autoresearch` CLI does not expose a dedicated auxiliary/options evidence input
- without auxiliary data, this factor falls back to a volatility proxy and cannot honestly count as a fully iterated options lane

**Unblock condition**
- either expose public auxiliary/options input to factor-research
- or export a stable auxiliary artifact from `analyze-live` that factor-research can consume

## Missing Factor Families

These are execution-tree needs visible in code, but not yet first-class factor families in the public registry.

### Missing Family 1: crowding / herding execution risk

**Execution-tree symptom**
- `block_crowded` triggered by `ising_phase_transition_risk`

**Why current factors are insufficient**
- `options_hedging` is only a partial proxy
- no current public factor explicitly models crowding / herd pressure as a factor lane

### Missing Family 2: geometry / stretch-reversion feasibility

**Execution-tree symptom**
- `wait_for_reversion` triggered by `pythagorean_overstretch`
- OU reversion speed affects readiness directly

**Why current factors are insufficient**
- `volatility_mean_reversion` is a proxy, not a geometry-aware factor
- no current factor directly optimizes `overextension_distance` / `reversion_speed`

### Missing Family 3: spectral rhythm / chaos execution filter

**Execution-tree symptom**
- readiness penalty from `spectral_entropy`, `dominant_cycle_energy`, `cycle_phase_alignment`

**Why current factors are insufficient**
- none of the five registered factors explicitly target the spectral execution layer

## Auto-Quant Loop Contract

For every lane that is not blocked:

1. Run one `native` `factor-research --human` pass first.
2. Record:
   - `best_factor`
   - `iteration_action`
   - `recommended_next_command`
   - current `workflow-status --human`
3. If the lane is still relevant to the current execution-tree blocker, switch to:
   - `factor-autoresearch --backend auto-quant`
4. After each Auto-Quant batch, check:
   - `factor-autoresearch-status --latest-only`
   - `workflow-status --human`
   - current branch expectation: `block_crowded`, `wait_for_reversion`, or `fill_viable`
5. Only keep iterating the same lane when the execution-tree weakness it targets is actually moving.
6. If the execution-tree blocker does not move, close the lane and move to the next factor family.

## Current Todo Board

### Done

- [x] Read execution-tree owner code.
- [x] Read execution feature / artifact owner code.
- [x] Read factor registry and factor role definitions.
- [x] Read public factor CLI loop surfaces (`factor-research`, `factor-autoresearch`).
- [x] Identify which registered factors can be iterated now and which are blocked by missing public input surface.

### Next

- [ ] Run Lane A (`structure_ict`) first. This is the highest-leverage lane for execution-tree development.
- [ ] Run Lane B (`trend_momentum`) second, but only after Lane A baseline is recorded.
- [ ] Run Lane C (`cross_market_smt`) once paired data is available for the same symbol/window.
- [ ] Run Lane D (`volatility_mean_reversion`) specifically when execution tree repeatedly lands on `wait_for_reversion`.
- [ ] Keep Lane E (`options_hedging`) blocked until a real auxiliary/options input surface exists.
- [ ] After the four runnable lanes plateau, decide whether Missing Families 1-3 need to become real factor families or can stay implicit in physics overlays.

### Not Yet

- [ ] New factor family implementation.
- [ ] Public auxiliary/options factor input surface for `options_hedging`.
- [ ] Public spectral-execution factor lane.
- [ ] Public crowding/herding execution-risk factor lane.
- [ ] Public geometry/reversion feasibility factor lane.

## Verification Checklist

- [ ] For each runnable lane, preserve one isolated `/tmp/...` state dir.
- [ ] For each runnable lane, capture `factor-research --human` before Auto-Quant.
- [ ] For each runnable lane, capture `factor-autoresearch-status --latest-only` after Auto-Quant.
- [ ] For each runnable lane, compare `workflow-status --human` before/after the lane.
- [ ] Do not claim a lane is “done” from aggregate return alone; it must move an execution-tree-relevant weakness or be formally exhausted.
