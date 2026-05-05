# Execution-Tree Auto-Quant Factor TODO

> Authoritative todo board for execution-tree-driven factor iteration.  
> This file is docs-only and should be updated in place after every real loop slice.

**Goal:** drive Auto-Quant factor iteration from the execution tree’s actual decision needs rather than from the current in-repo factor registry, and keep iterating until every factor family is either exhausted, blocked by missing data/surface, or externalized as a future implementation need.

**Architecture:** treat `ict-engine` as the execution-tree judge and Auto-Quant as the factor author / mutator. The execution tree defines what capabilities are missing or weak; Auto-Quant supplies or mutates factor families to improve those capabilities. Current in-repo factors may be used as temporary bootstrap seeds, but they are not the design boundary, and the agent must retain freedom to hardcode or synthesize factor families inside the Auto-Quant research workspace without requiring repo code changes first.

**Tech Stack:** `./target/debug/ict-engine analyze`, `factor-research --backend auto-quant`, `factor-autoresearch --backend auto-quant`, `factor-autoresearch-status`, `workflow-status --human`, `artifact-status`, `auto-quant-status`, isolated `/tmp/...` state dirs.

**Baseline / Authority Refs:** `src/application/orchestration/execution_tree.rs`, `src/application/execution/inputs.rs`, `src/application/execution/artifact.rs`, `src/application/reflection/execution_tree_bundle.rs`, `src/factor_research_command.rs`, `docs/execution-paper-notes-and-plan-update.md`, `docs/plans/factor-autoresearch-minimal-loop.md`, `docs/plans/2026-05-03-repo-action-board.md`.

**Compatibility Boundary:** preserve zero-config default behavior, consumer-usable CLI surfaces, token-friendly human/compact outputs, and low-pollution execution through explicit `/tmp/...` state dirs. Do not let the current Rust factor registry cap the factor family design space. Do not require repo code changes just to continue the Auto-Quant research loop.

**Coverage Rule:** beyond broad market / high-liquidity instrument coverage, every factor family should also be evaluated against a multi-timeframe candle ladder whenever the public surface can support it:
- `1m` minute
- `5m`
- `15m`
- `1h`
- `4h`
- `1d`
- `1w`
- `1M` monthly

Do not reject higher-timeframe factors just because they are less directly tradable intraday. They may still matter as regime / resonance / confirmation context for lower-timeframe execution.

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

## Current Execution Slice

### 2026-05-05 Slice 1: baseline + Family A public surface

**Coverage rule**
- Each factor family should strive for broad multi-market coverage.
- Do not treat a single-symbol lift as closure unless it later generalizes across a wider market set.
- Each factor family should also strive for multi-timeframe coverage across `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`, and `1M` wherever the public surface or additive profile can support it.
- Treat higher-timeframe factors as potentially important resonance / confirmation context even when the eventual execution target is intraday.

**Execution context**
- target baseline symbol: `NQ`
- baseline state dir: `/tmp/ict-engine-exec-tree-aq-20260505-baseline-trimmed`
- family state dir: `/tmp/ict-engine-exec-tree-aq-20260505-family-a`
- trimmed multi-timeframe inputs derived into `/tmp/ict-engine-exec-tree-aq-20260505-data/` from:
  - `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/nq.continuous-15m.json`
  - `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-1h/nq.continuous-1h.json`
  - `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-1d/nq.continuous-1d.json`

**Baseline evidence**
- commands:
  - `./target/debug/ict-engine analyze --symbol NQ --data-htf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1d.2023plus.json --data-mtf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1h.2023plus.json --data-ltf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --state-dir /tmp/ict-engine-exec-tree-aq-20260505-baseline-trimmed --human`
  - `./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-exec-tree-aq-20260505-baseline-trimmed --human`
- result:
  - analyze returned: `Bull bias`, `entry=medium`, `gate=pass_neutralized`, `quality=0.424`, `Action: TUNE structure_ict`
  - persisted execution-tree trace resolved to `branch=transition_guardrail`, `execution_bias=guarded`, `gate_status=observe`
  - lineage still passed through weak `execution_readiness` / `block_crowded` and transition-hazard stress
  - strongest trace features were `cycle_phase_alignment`, `spectral_entropy`, `pythagorean_overstretch`, and `ising_phase_transition_risk`
  - baseline `workflow-status` blocked on `user_selected_historical_data_missing` because analyze recorded multiple timeframe paths in one shared state dir; later family slices should therefore keep separate research state dirs

**Family A evidence**
- commands:
  - `./target/debug/ict-engine auto-quant-status --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --human`
  - `./target/debug/ict-engine auto-quant-bootstrap --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --repo-url /Users/thrill3r/Auto-Quant --tracked-branch autoresearch/apr26`
  - `./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a`
  - `./target/debug/ict-engine factor-research --symbol NQ --data /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --data-15m /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --data-1h /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1h.2023plus.json --data-1d /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1d.2023plus.json --objective expansion_manipulation --strategy-material-root /Users/thrill3r/Downloads/Tomac --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --backend auto-quant --human`
  - `./target/debug/ict-engine factor-autoresearch --symbol NQ --data /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --data-15m /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --data-1h /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1h.2023plus.json --data-1d /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1d.2023plus.json --objective expansion_manipulation --strategy-material-root /Users/thrill3r/Downloads/Tomac --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --backend auto-quant --iterations 5`
  - `./target/debug/ict-engine factor-autoresearch-status --symbol NQ --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --latest-only`
  - `./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-exec-tree-aq-20260505-family-a --human`
- result:
  - managed readiness advanced `missing_dependency -> dependency_ready_data_missing -> dependency_ready_data_ready`
  - prepare populated only the standard managed crypto universe:
    - `BTC/USDT`
    - `ETH/USDT`
    - `SOL/USDT`
    - `BNB/USDT`
    - `AVAX/USDT`
  - `factor-research --backend auto-quant` still emitted a handoff only
  - `factor-autoresearch --backend auto-quant` still emitted only `auto-quant-handoff:factor_autoresearch:*`
  - `factor-autoresearch-status` remained `no_autoresearch_state`
  - `workflow-status` remained `no_workflow_state`
  - managed `program.md` still defines Auto-Quant v0.3.0 as a fixed 5-pair crypto portfolio contract, so the recommended `uv run --with ta-lib .../run.py` path is not yet aligned to the `NQ` execution-tree baseline or to the broader market-coverage target
  - repo-owned additive external tooling exists for wider market routing:
    - `scripts/auto_quant_external/config.tomac.json` targets `NQ/USD`
    - local `/Users/thrill3r/Auto-Quant/user_data/data/` already contains wider-market evidence files such as `NQ_USD-*`, `ES_USD-*`, `AAPL_USD-*`, `SPY_USD-*`, `EUR_USD-*`
  - however, the local wider-market data surface is still uneven:
    - `NQ/USD` already has `1h`, `4h`, `1d`
    - `ES/USD`, `AAPL/USD`, `SPY/USD`, `EUR/USD` currently only have `1d`
  - so even the additive path is not yet ready to claim true broad multi-market coverage for this family without more data preparation

**Stop reason**
- `surface_blocked`
  - the public managed Auto-Quant loop reaches readiness, but its actual execution contract still points at the fixed crypto portfolio rather than the target execution-tree market slice or a broader full-market coverage lane
  - therefore this slice does not yet produce a valid after-run workflow/export artifact for Family A

### 2026-05-06 Slice 2: Family G public auxiliary/options input surface

**Implementation**
- public `factor-research` and `factor-autoresearch` now expose:
  - `--auxiliary-evidence <path>`
- accepted input shapes:
  - direct `AuxiliaryMarketEvidence` JSON
  - full analyze-report JSON containing `supporting.auxiliary`
- native research now injects that auxiliary evidence into the `options_hedging` / dealer-positioning runtime context
- auto-quant handoff now preserves the same auxiliary evidence path inside:
  - payload JSON
  - suggested commands
  - agent prompt
  - notes

**Verification**
- help surface:
  - `./target/debug/ict-engine factor-research --help`
  - `./target/debug/ict-engine factor-autoresearch --help`
- native smoke:
  - `./target/debug/ict-engine factor-research --symbol DEMO --data examples/demo/demo-15m.json --backend native --auxiliary-evidence /tmp/ict-engine-family-g-aux-direct.json --state-dir /tmp/ict-engine-family-g-native --output-format json`
  - output contained:
    - `auxiliary_evidence_path=...`
    - `auxiliary_spot_symbol=SPY`
    - `auxiliary_options_symbol=SPY`
- auto-quant research handoff smoke:
  - `./target/debug/ict-engine factor-research --symbol NQ --data /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --backend auto-quant --auxiliary-evidence /tmp/ict-engine-family-g-aux-wrapper.json --state-dir /tmp/ict-engine-family-g-aq --human`
  - `/tmp/ict-engine-family-g-aq/NQ/auto_quant_handoff.factor_research.json` preserved:
    - `auxiliary_evidence_path`
    - `auto_quant_auxiliary_evidence_path=...`
- auto-quant autoresearch handoff smoke:
  - `./target/debug/ict-engine factor-autoresearch --symbol NQ --data /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --backend auto-quant --auxiliary-evidence /tmp/ict-engine-family-g-aux-wrapper.json --state-dir /tmp/ict-engine-family-g-ar --iterations 2`
  - output payload preserved the same auxiliary path
- build / targeted verification:
  - `cargo check --bin ict-engine`
  - `cargo test --lib handoff_payload_carries_auxiliary_evidence_path_into_commands_and_prompt -- --nocapture`
  - `cargo test --lib review_marks_prepare_required_when_data_is_missing -- --nocapture`

**Outcome**
- Family G is no longer blocked by the absence of a dedicated public auxiliary/options research input surface.
- The remaining work for this family is now actual factor iteration quality and coverage, not CLI/input-surface absence.

### 2026-05-06 Slice 3: Family A opt-in synthetic OHLCV profile

**Implementation**
- public `factor-research` and `factor-autoresearch` now expose:
  - `--auto-quant-profile <managed|synthetic_ohlcv>`
- `synthetic_ohlcv` behavior:
  - opt-in and state-dir scoped
  - persists `auto_quant_workspace_profile.json`
  - switches Auto-Quant workspace contract from:
    - `prepare.py`
    - `run.py`
    - `config.json`
    - `user_data/strategies`
  - to:
    - `prepare_external.py`
    - `run_tomac.py`
    - `config.tomac.json`
    - `user_data/strategies_external`
  - derives `SYMBOL/USD` `1h/4h/1d` feather files from the caller-supplied cleaned candle JSON instead of assuming the fixed crypto universe
  - keeps default managed behavior untouched unless the caller explicitly opts in
- profile seeding is export-aware:
  - active strategies are copied into `strategies_external`
  - if they lack `AUTO_QUANT_META`, a minimal valid block is synthesized automatically during materialization
  - if no active strategies exist, the repo fallback external strategy is seeded automatically

**Verification**
- handoff / state-profile persistence:
  - `ICT_ENGINE_AUTO_QUANT_REPO_URL=/Users/thrill3r/Auto-Quant ICT_ENGINE_AUTO_QUANT_BRANCH=autoresearch/apr26 ./target/debug/ict-engine factor-research --symbol NQ --data /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-family-a-profile --human`
  - persisted:
    - `/tmp/ict-engine-family-a-profile/auto_quant_workspace_profile.json`
    - `/tmp/ict-engine-family-a-profile/NQ/auto_quant_handoff.factor_research.json`
  - handoff JSON now points at:
    - `prepare_external.py`
    - `run_tomac.py`
    - `config.tomac.json`
    - `user_data/strategies_external`
    - `profile_name=synthetic_ohlcv`
- prepare / readiness:
  - `./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-family-a-profile`
  - prepared files:
    - `NQ_USD-1h.feather`
    - `NQ_USD-4h.feather`
    - `NQ_USD-1d.feather`
  - `./target/debug/ict-engine auto-quant-status --state-dir /tmp/ict-engine-family-a-profile`
  - readiness now reports:
    - `status=dependency_ready_data_ready`
    - `recommended_next_command=uv run --with ta-lib .../run_tomac.py`
    - `auto_quant_profile=synthetic_ohlcv`
- real run:
  - `cd /tmp/ict-engine-family-a-profile/.deps/auto-quant && uv run --with ta-lib run_tomac.py`
  - real backtest output landed for:
    - `TomacAggressiveBE`
    - `TomacKillzoneBreakout`
    - `TomacRRWinRate`
- export / import closure:
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac.log --config config.tomac.json --output strategy_library.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --library /tmp/ict-engine-family-a-profile/.deps/auto-quant/strategy_library.json --log /tmp/ict-engine-family-a-profile/.deps/auto-quant/run_tomac.log`
  - current imported result:
    - `n_ok=2`
    - `n_meta_invalid=1`
    - `matched=2`
    - `library_state_path=/tmp/ict-engine-family-a-profile/NQ/auto_quant_strategy_library.json`

**Outcome**
- Family A is no longer blocked by the fixed crypto-only managed contract.
- Family A is no longer blocked by the absence of a caller-choosable additive external path for user-specific non-crypto candle data.
- The remaining work for this family is now iterative quality / coverage improvement on top of the new public surface, not surface absence.

### 2026-05-06 Slice 4: Family A imported-run re-check

**Execution**
- imported the synthetic-profile strategy library into `ict-engine`:
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --library /tmp/ict-engine-family-a-profile/.deps/auto-quant/strategy_library.json --log /tmp/ict-engine-family-a-profile/.deps/auto-quant/run_tomac.log`
- applied the imported library as a BBN prior-init:
  - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-a-profile`
- re-checked the same trimmed NQ multi-timeframe baseline:
  - `./target/debug/ict-engine analyze --symbol NQ --data-htf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1d.2023plus.json --data-mtf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1h.2023plus.json --data-ltf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --state-dir /tmp/ict-engine-family-a-profile --human`
  - `./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --human`

**Result**
- prior-init apply succeeded with:
  - `n_ok=3`
  - `n_meta_invalid=0`
  - `matched=3`
  - `prior_init_artifact_id=auto_quant_prior_init_NQ_20260505T173430.030500000Z`
- analyze outcome after import/prior-init remained:
  - `Bull bias`
  - `entry=medium`
  - `gate=pass_neutralized`
  - `quality=0.424`
  - `Action: TUNE structure_ict`
- `workflow-status --human` now correctly reflects the latest analyze state rather than the old handoff:
  - `analyze | action_blocked`
  - blocker: `user_selected_historical_data_missing`
  - next research candidate remains the trimmed 15m path

**Outcome**
- Family A surface is resolved and end-to-end importable.
- The first post-import re-check did not materially improve execution-tree quality yet.
- Therefore Family A should remain the active quality-iteration lane rather than being treated as “finished”.

### 2026-05-06 Slice 5: Family A round 2 strategy selection

**Execution**
- injected an NQ-specific structure candidate into the synthetic-profile managed seed source:
  - `TomacNQ_KillzoneBreakout`
- reran the same public synthetic-profile loop:
  - `./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-family-a-profile`
  - `cd /tmp/ict-engine-family-a-profile/.deps/auto-quant && uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac.log --config config.tomac.json --output strategy_library.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --library /tmp/ict-engine-family-a-profile/.deps/auto-quant/strategy_library.json --log /tmp/ict-engine-family-a-profile/.deps/auto-quant/run_tomac.log`

**Round 2 strategy results**
- `TomacAggressiveBE`
  - `sharpe=-0.274`
  - `profit=-4.37%`
  - `trade_count=18`
- `TomacKillzoneBreakout`
  - `sharpe=-0.0382`
  - `profit=-1.51%`
  - `trade_count=2`
- `TomacNQ_KillzoneBreakout`
  - `sharpe=0.668`
  - `profit=11.29%`
  - `trade_count=19`
  - `win_rate=89.47%`
  - `profit_factor=4.3778`
- `TomacRRWinRate`
  - `sharpe=-1.9872`
  - `profit=-3.89%`
  - `trade_count=2`

**Import result**
- latest library import improved to:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T174324.219225000Z`

**Focused prior-init re-check**
- instead of applying all four strategies equally, ran a focused prior-init on the two stronger candidates:
  - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --dry-run --strategies TomacNQ_KillzoneBreakout,TomacAggressiveBE`
  - then applied with rollback + force:
    - backup: `bbn_network.before_family_a_round2.json`
    - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --strategies TomacAggressiveBE,TomacNQ_KillzoneBreakout --force`
- focused prior-init moved the CPT row to:
  - `final_probs=[0.8575458461538461, 0.0000020056980056980055, 0.14245214814814813]`
- post-apply re-check:
  - `./target/debug/ict-engine analyze --symbol NQ --data-htf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1d.2023plus.json --data-mtf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-1h.2023plus.json --data-ltf /tmp/ict-engine-exec-tree-aq-20260505-data/nq.continuous-15m.2023plus.json --state-dir /tmp/ict-engine-family-a-profile --human`
  - `./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-engine-family-a-profile --human`

**Result**
- analyze improved only in comparability semantics:
  - `Decision: Comparable run, but factor backlog remains`
- but the core execution-tree output still remained:
  - `Bull bias`
  - `entry=medium`
  - `gate=pass_neutralized`
  - `quality=0.424`
  - `Action: TUNE structure_ict`
- workflow still points to the trimmed 15m path as the next research candidate

**Outcome**
- Family A now has one clearly positive structure/setup candidate on the new public surface: `TomacNQ_KillzoneBreakout`.
- Even after selecting the stronger subset for prior-init, execution-tree quality did not move yet.
- So the next Family A work should bias toward:
  - structure-specific follow-up variants around the NQ killzone / breakout thesis
  - broader market/timeframe expansion of that family
  - not more retries of the clearly weak `TomacRRWinRate` branch

### 2026-05-06 Slice 6: Family A NQ daily-bias fork and export-surface hardening

**Execution**
- forked a tighter structure-confirmation variant from the strongest current candidate:
  - `TomacNQ_KillzoneBreakoutDailyBias`
- reran the same synthetic-profile public loop after seeding the new candidate

**Result**
- round output after the fork:
  - `TomacNQ_KillzoneBreakoutDailyBias`
    - `sharpe=0.0`
    - `profit=0.0%`
    - `trade_count=0`
  - interpretation:
    - the extra daily-bias / ATR gate over-tightened the setup and produced no trades on this NQ slice
- while running this slice, a real consumer-surface defect appeared:
  - the synthetic profile’s generated `strategies_external/*.py` files initially placed `AUTO_QUANT_META` into a second top-level docstring, which caused:
    - FreqTrade import warnings around `from __future__`
    - then, after the first fix, manifest parse failures because `# END_AUTO_QUANT_META` was not on its own line
- fixed the generation path so profile-materialized strategies now:
  - preserve a single module docstring
  - keep `from __future__` in a valid position
  - emit a parseable `AUTO_QUANT_META` block

**Verification**
- reran:
  - `./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-family-a-profile`
  - `cd /tmp/ict-engine-family-a-profile/.deps/auto-quant && uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac.log --config config.tomac.json --output strategy_library.json`
- final export state after the hardening fix:
  - `n_ok=5`
  - `n_validation_errors=0`
  - no remaining `from __future__ imports must occur` warnings in `run_tomac.log`

**Outcome**
- the daily-bias fork is currently weaker than the base NQ killzone candidate because it produced no trades.
- the current best Family A candidate remains `TomacNQ_KillzoneBreakout`.
- the profile surface itself is now materially more consumer-safe and export-stable.

### 2026-05-06 Slice 7: Family A market-expansion proof on ES

**Execution**
- ran the same opt-in synthetic profile on a second major index future:
  - `ICT_ENGINE_AUTO_QUANT_REPO_URL=/Users/thrill3r/Auto-Quant ICT_ENGINE_AUTO_QUANT_BRANCH=autoresearch/apr26 ./target/debug/ict-engine factor-research --symbol ES --data /Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/es.continuous-15m.json --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-family-a-es-profile --human`
- then completed the same closure steps:
  - `./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-family-a-es-profile`
  - `cd /tmp/ict-engine-family-a-es-profile/.deps/auto-quant && uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac.log --config config.tomac.json --output strategy_library.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol ES --state-dir /tmp/ict-engine-family-a-es-profile --library /tmp/ict-engine-family-a-es-profile/.deps/auto-quant/strategy_library.json --log /tmp/ict-engine-family-a-es-profile/.deps/auto-quant/run_tomac.log`

**Result**
- the same public synthetic profile successfully materialized:
  - `ES/USD-1h.feather`
  - `ES/USD-4h.feather`
  - `ES/USD-1d.feather`
- import closure succeeded:
  - `n_ok=3`
  - `n_meta_invalid=0`
  - `matched=3`
  - `library_artifact_id=auto_quant_strategy_library_ES_20260505T175426.389082000Z`

**Outcome**
- the synthetic-profile Family A surface is no longer an NQ-only special case.
- it is now proven on at least two futures-index markets:
  - `NQ`
  - `ES`
- broader market coverage is still incomplete, but the product surface is now demonstrably reusable across major futures-index instruments.

### 2026-05-06 Slice 8: Family A ES round 2 candidate selection

**Execution**
- injected the current strongest NQ candidate into the `ES` managed seed source:
  - `TomacNQ_KillzoneBreakout`
- reran the same `synthetic_ohlcv` profile closure for `ES`

**Result**
- `ES` round 2 strategy results:
  - `TomacAggressiveBE`
    - `sharpe=-0.0972`
    - `profit=-3.05%`
    - `trade_count=59`
  - `TomacKillzoneBreakout`
    - `sharpe=0.2889`
    - `profit=16.98%`
    - `trade_count=40`
    - `win_rate=60.0%`
    - `profit_factor=2.1103`
  - `TomacNQ_KillzoneBreakout`
    - `sharpe=-0.0126`
    - `profit=-0.59%`
    - `trade_count=43`
    - `win_rate=55.814%`
    - `profit_factor=0.9707`
  - `TomacRRWinRate`
    - `sharpe=0.1593`
    - `profit=9.21%`
    - `trade_count=26`
    - `win_rate=69.2308%`
    - `profit_factor=1.9605`

**Outcome**
- the NQ-specific positive candidate does **not** currently generalize to `ES`.
- `ES` still prefers its original generic breakout lane:
  - best current `ES` structure/setup candidate remains `TomacKillzoneBreakout`
- therefore Family A should now treat:
  - `TomacNQ_KillzoneBreakout` as an `NQ`-leaning candidate
  - `TomacKillzoneBreakout` as the stronger current `ES` structure/setup candidate

### 2026-05-06 Slice 9: Family A YM expansion attempt

**Execution**
- attempted the same `synthetic_ohlcv` public profile on `YM`
- profile materialized and prepared successfully
- `run_tomac.py` then executed against the `YM/USD` synthetic workspace

**Result**
- profile surface itself succeeded:
  - `YM/USD-1h.feather`
  - `YM/USD-4h.feather`
  - `YM/USD-1d.feather`
- but strategy runtime quality was mixed:
  - `TomacAggressiveBE`
    - runtime failure: `UnboundLocalError: cannot access local variable 'price' where it is not associated with a value`
  - `TomacKillzoneBreakout`
    - same runtime failure
  - `TomacRRWinRate`
    - `trade_count=0`
    - no usable edge evidence
- because the run exited with mixed failures, no imported `YM` strategy library closure was kept as a valid Family A proof point

**Outcome**
- `YM` is now a concrete runtime blocker for the current profile + current strategy set.
- this is not a surface-availability blocker anymore; it is a strategy/runtime compatibility blocker that needs a narrower follow-up slice.

### 2026-05-06 Slice 11: Family A YM partial salvage

**Execution**
- injected `TomacNQ_KillzoneBreakout` into the `YM` managed seed source
- reran the same synthetic-profile loop, but allowed `run_tomac.py` to continue into export/import even if some strategies failed

**Result**
- imported `YM` library state improved from “no valid closure” to:
  - `n_ok=1`
  - `n_error=3`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_YM_20260505T181911.021030000Z`
- per-strategy state:
  - `TomacAggressiveBE`
    - `status=error`
    - `UnboundLocalError: cannot access local variable 'price' where it is not associated with a value`
  - `TomacKillzoneBreakout`
    - same runtime failure
  - `TomacNQ_KillzoneBreakout`
    - same runtime failure
  - `TomacRRWinRate`
    - `status=ok`
    - `trade_count=0`
    - no usable edge evidence
- `auto-quant-prior-init --dry-run` for `YM` therefore applied nothing:
  - every error strategy was skipped as `status=error`
  - `TomacRRWinRate` was skipped as `trade_count=0`

**Outcome**
- `YM` is no longer “surface completely unproven”, because import closure now exists.
- but it is still not a valid Family A market proof point because no positive / nonzero strategy candidate survived the runtime + trade-count filters.

### 2026-05-06 Slice 12: Family A XAU synthetic-profile probe

**Execution**
- ran the same opt-in `synthetic_ohlcv` profile on the existing `XAU` cleaned 15m/1h/1d data:
  - `./target/debug/ict-engine factor-research --symbol XAU --data /Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/xau.continuous-15m.json --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-family-a-xau-profile --human`
- then completed prepare / run / export / import closure

**Result**
- import closure succeeded:
  - `n_ok=3`
  - `n_meta_invalid=0`
  - `matched=3`
  - `library_artifact_id=auto_quant_strategy_library_XAU_20260505T182423.822631000Z`
- but all three strategies were flat:
  - `TomacAggressiveBE`
    - `trade_count=0`
  - `TomacKillzoneBreakout`
    - `trade_count=0`
  - `TomacRRWinRate`
    - `trade_count=0`
- `auto-quant-prior-init --dry-run` therefore applied nothing for `XAU`

**Outcome**
- `XAU` proves the profile surface can materialize/import on a third market family.
- but it is not yet a useful Family A quality proof point because the current strategy set generates no trades there.

### 2026-05-06 Slice 13: Family A broader market shape after additional probes

**Result summary**
- currently positive / usable Family A evidence:
  - `NQ`
    - strongest candidate: `TomacNQ_KillzoneBreakout`
  - `ES`
    - strongest candidate: `TomacKillzoneBreakout`
- currently unresolved or weak:
  - `YM`
    - runtime failures on the structure candidates
    - remaining `ok` strategy has `trade_count=0`
  - `XAU`
    - no runtime failure, but all current strategies `trade_count=0`

**Outcome**
- Family A is now proven as a reusable synthetic-profile surface across:
  - index futures (`NQ`, `ES`)
  - a precious-metals proxy market (`XAU`)
- but only `NQ` and `ES` currently produce positive structure/setup candidates worth continuing immediately.

### 2026-05-06 Slice 14: Family A EUR synthetic-profile probe

**Execution**
- ran the same `synthetic_ohlcv` public profile on the existing `EUR` cleaned 15m/1h/1d data
- then completed prepare / run / export / import closure
- applied a focused prior-init using the strongest current `EUR` candidate:
  - `TomacRRWinRate`
- re-checked the imported run with:
  - `analyze`
  - `workflow-status --human`

**Result**
- import closure succeeded:
  - `n_ok=3`
  - `n_meta_invalid=0`
  - `matched=3`
  - `library_artifact_id=auto_quant_strategy_library_EUR_20260505T182957.067645000Z`
- strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-0.3422`
    - `profit=-1.69%`
    - `trade_count=13`
  - `TomacKillzoneBreakout`
    - `sharpe=-0.0459`
    - `profit=-0.37%`
    - `trade_count=6`
  - `TomacRRWinRate`
    - `sharpe=0.2273`
    - `profit=0.94%`
    - `trade_count=20`
    - `win_rate=55.0%`
    - `profit_factor=2.2007`
- focused prior-init on `TomacRRWinRate` moved the CPT row to:
  - `final_probs=[0.6785588571428571, 0.000006285714285714286, 0.32143485714285713]`
- post-apply re-check:
  - `Bear bias`
  - `entry=medium`
  - `gate=pass_neutralized`
  - `quality=0.553`
  - `Action: TUNE structure_ict`
  - `workflow-status` points to the trimmed `eur.continuous-15m.2023plus.json` path

**Outcome**
- `EUR` is another real importable synthetic-profile proof point.
- but its strongest current candidate is `TomacRRWinRate`, not the structure/setup lane.
- this suggests the current Family A structure backlog does not obviously dominate `EUR`; another factor family may be more natural there.

### 2026-05-06 Slice 15: Local multi-timeframe availability audit

**Result**
- the local cleaned corpus already covers these intervals for at least:
  - `ES`
  - `EUR`
  - `NQ`
  - `XAU`
  - `YM`
- confirmed available now under `~/Downloads/Tomac/ict-cleaned-mtf/`:
  - `1m`
  - `5m`
  - `15m`
  - `1h`
  - `4h`
  - `1d`

**Outcome**
- the current multi-timeframe blocker is no longer “minute through daily candles do not exist locally”.
- the remaining gap is narrower:
  - exercising those intervals through the public Family A surface
  - preparing or proving `1w`
  - preparing or proving `1M`

### 2026-05-06 Slice 16: Family A NQ 5m synthetic-profile probe

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-a-nq-5m-profile`
- used the public synthetic profile with the existing cleaned `5m` NQ source:
  - `./target/debug/ict-engine factor-research --symbol NQ --data /Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-5m/nq.continuous-5m.json --backend auto-quant --auto-quant-profile synthetic_ohlcv --state-dir /tmp/ict-engine-family-a-nq-5m-profile --human`
- then manually expanded the profile workspace to a real `5m` base:
  - generated:
    - `NQ_USD-5m.feather`
    - `NQ_USD-1h.feather`
    - `NQ_USD-4h.feather`
    - `NQ_USD-1d.feather`
  - set `config.tomac.json` timeframe to `5m`
  - added a dedicated `TomacNQKillzoneBreakout5m` strategy using:
    - `5m` base
    - `1h` informative context
    - `4h` informative context
- completed closure:
  - `uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac_5m.log --config config.tomac.json --output strategy_library_5m.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-nq-5m-profile --library /tmp/ict-engine-family-a-nq-5m-profile/.deps/auto-quant/strategy_library_5m.json --log /tmp/ict-engine-family-a-nq-5m-profile/.deps/auto-quant/run_tomac_5m.log`

**Result**
- 5m-base strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-0.49`
    - `profit=-4.95%`
    - `trade_count=216`
  - `TomacKillzoneBreakout`
    - `sharpe=0.4291`
    - `profit=11.5%`
    - `trade_count=37`
    - `win_rate=64.8649%`
    - `profit_factor=1.5278`
  - `TomacNQKillzoneBreakout5m`
    - `sharpe=0.4568`
    - `profit=7.17%`
    - `trade_count=30`
    - `win_rate=76.6667%`
    - `profit_factor=1.7932`
  - `TomacRRWinRate`
    - `sharpe=-0.0344`
    - `profit=-1.16%`
    - `trade_count=3`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T184132.711258000Z`
- focused prior-init dry-run on the new 5m candidate:
  - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-a-nq-5m-profile --dry-run --strategies TomacNQKillzoneBreakout5m`
  - result:
    - `final_probs=[0.8157802105263158, 0.000004631578947368421, 0.18421515789473683]`

**Outcome**
- this is the first real proof that the public synthetic profile can be exercised at `5m` base, not only `1h`.
- the 5m candidate is positive, but it is still weaker than the current best `1h` NQ candidate:
  - `TomacNQ_KillzoneBreakout`
    - `sharpe=0.668`
    - `profit=11.29%`
  - `TomacNQKillzoneBreakout5m`
    - `sharpe=0.4568`
    - `profit=7.17%`
- therefore `5m` is now a proven execution lane, but not yet the dominant `NQ` Family A candidate.

### 2026-05-06 Slice 17: Family A NQ 15m synthetic-profile probe

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-a-nq-15m-profile`
- used the public synthetic profile with the existing cleaned `15m` NQ source
- then manually expanded the profile workspace to a real `15m` base:
  - generated:
    - `NQ_USD-15m.feather`
    - `NQ_USD-1h.feather`
    - `NQ_USD-4h.feather`
    - `NQ_USD-1d.feather`
  - set `config.tomac.json` timeframe to `15m`
  - added a dedicated `TomacNQKillzoneBreakout15m` strategy using:
    - `15m` base
    - `1h` informative context
    - `4h` informative context
- completed closure:
  - `uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac_15m.log --config config.tomac.json --output strategy_library_15m.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-nq-15m-profile --library /tmp/ict-engine-family-a-nq-15m-profile/.deps/auto-quant/strategy_library_15m.json --log /tmp/ict-engine-family-a-nq-15m-profile/.deps/auto-quant/run_tomac_15m.log`

**Result**
- 15m-base strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=0.0863`
    - `profit=1.1%`
    - `trade_count=74`
  - `TomacKillzoneBreakout`
    - `sharpe=0.1686`
    - `profit=5.63%`
    - `trade_count=32`
    - `win_rate=68.75%`
    - `profit_factor=1.2187`
  - `TomacNQKillzoneBreakout15m`
    - `sharpe=0.0746`
    - `profit=1.18%`
    - `trade_count=22`
    - `win_rate=72.7273%`
    - `profit_factor=1.1272`
  - `TomacRRWinRate`
    - `sharpe=-0.0433`
    - `profit=-1.62%`
    - `trade_count=3`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T185037.218597000Z`
- focused prior-init dry-run on `TomacNQKillzoneBreakout15m` moved the CPT row to:
  - `final_probs=[0.7999882666666667, 0.000005866666666666667, 0.20000586666666667]`

**Outcome**
- `15m` is now another real proven execution lane through the public profile.
- but the dedicated `15m` fork is weaker than both:
  - the best `1h` NQ candidate
  - and the best `5m` NQ candidate
- so `15m` is currently evidence of coverage, not evidence of a stronger replacement.

### 2026-05-06 Slice 18: Family A NQ 1m synthetic-profile probe

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-a-nq-1m-profile`
- used the public synthetic profile with the existing cleaned `1m` NQ source
- then manually expanded the profile workspace to a real `1m` base:
  - generated:
    - `NQ_USD-1m.feather`
    - `NQ_USD-15m.feather`
    - `NQ_USD-1h.feather`
    - `NQ_USD-4h.feather`
    - `NQ_USD-1d.feather`
  - set `config.tomac.json` timeframe to `1m`
  - added a dedicated `TomacNQKillzoneBreakout1m` strategy using:
    - `1m` base
    - `15m` informative context
    - `1h` informative context
    - `4h` informative context
- completed closure:
  - `uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac_1m.log --config config.tomac.json --output strategy_library_1m.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-a-nq-1m-profile --library /tmp/ict-engine-family-a-nq-1m-profile/.deps/auto-quant/strategy_library_1m.json --log /tmp/ict-engine-family-a-nq-1m-profile/.deps/auto-quant/run_tomac_1m.log`

**Result**
- 1m-base strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-4.5402`
    - `profit=-25.69%`
    - `trade_count=1050`
  - `TomacKillzoneBreakout`
    - `sharpe=0.4081`
    - `profit=7.83%`
    - `trade_count=100`
    - `win_rate=43.0%`
    - `profit_factor=1.1795`
  - `TomacNQKillzoneBreakout1m`
    - `sharpe=-0.3518`
    - `profit=-8.2%`
    - `trade_count=56`
    - `win_rate=69.6429%`
    - `profit_factor=0.6742`
  - `TomacRRWinRate`
    - `sharpe=-0.6171`
    - `profit=-12.79%`
    - `trade_count=2`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T185516.551633000Z`

**Outcome**
- `1m` is now also a real proven execution lane through the public profile.
- however, the dedicated `1m` fork is clearly weaker than the best `1h`, `5m`, and even the generic `1m` breakout line.
- current interpretation:
  - `1m` coverage is proven
  - but `1m` is not currently the preferred Family A quality lane for `NQ`

### 2026-05-06 Slice 19: Family A focused re-checks on new NQ forks

**Execution**
- created isolated copies of the current `NQ` Family A state:
  - `/tmp/ict-engine-family-a-profile-1dregime-check`
  - `/tmp/ict-engine-family-a-profile-5m-check`
- applied focused prior-init on each candidate and reran `analyze` with the same trimmed `NQ` multi-timeframe baseline:
  - `TomacNQ_KillzoneBreakout1dRegime`
  - `TomacNQKillzoneBreakout5m`

**Result**
- `TomacNQ_KillzoneBreakout1dRegime`
  - prior-init moved the CPT row to:
    - `final_probs=[0.8860366769230769, 0.0000016045584045584045, 0.11396171851851851]`
  - post-apply analyze still returned:
    - `quality=0.424`
    - `gate=pass_neutralized`
    - `Action: TUNE structure_ict`
- `TomacNQKillzoneBreakout5m`
  - prior-init moved the CPT row to:
    - `final_probs=[0.7857991255060729, 0.0000004222522117258959, 0.2142004522417154]`
  - post-apply analyze still returned:
    - `quality=0.424`
    - `gate=pass_neutralized`
    - `Action: TUNE structure_ict`

**Outcome**
- both focused forks can move the BBN prior, but neither one moves the execution-tree decision surface yet.
- this strengthens the current conclusion:
  - the Family A blocker is no longer surface, profile, or timeframe availability
  - it is strategy quality relative to what `structure_ict` still needs

### 2026-05-06 Slice 20: Family A NQ displacement-quality fork

**Execution**
- forked another `NQ` 1h structure variant from the strongest current candidate:
  - `TomacNQ_KillzoneBreakoutDisplacement`
- this fork kept the same broad thesis but tightened:
  - reclaim quality at the prior 24h high
  - breakout candle body strength
  - close location strength inside the breakout candle
- reran the same `NQ` 1h synthetic-profile closure:
  - `auto-quant-prepare`
  - `run_tomac.py`
  - `export_strategy_library.py`
  - `auto-quant-results-import`

**Result**
- round 4 import closure succeeded:
  - `n_ok=7`
  - `n_meta_invalid=0`
  - `matched=7`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T191042.368235000Z`
- new strategy metrics:
  - `TomacNQ_KillzoneBreakoutDisplacement`
    - `sharpe=0.8634`
    - `profit=8.73%`
    - `trade_count=18`
    - `win_rate=83.3333%`
    - `profit_factor=8.1291`
- comparison with prior best:
  - `TomacNQ_KillzoneBreakout`
    - `sharpe=0.668`
    - `profit=11.29%`
    - `trade_count=19`
    - `win_rate=89.4737%`
    - `profit_factor=4.3778`
- focused prior-init on the new displacement fork:
  - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-a-profile-displacement-check --force --strategies TomacNQ_KillzoneBreakoutDisplacement`
  - result:
    - `final_probs=[0.8407833372781065, 0.0000006171378479070786, 0.15921604558404556]`
- post-apply re-check:
  - `quality=0.424`
  - `gate=pass_neutralized`
  - `Action: TUNE structure_ict`

**Outcome**
- `TomacNQ_KillzoneBreakoutDisplacement` is now the strongest **backtest** candidate on the `NQ` 1h Family A lane.
- but even this stronger structure-quality fork still does not move the execution-tree decision surface.
- so the current leading interpretation is:
  - Auto-Quant has produced better trade candidates
  - yet the missing execution-tree ingredient is still upstream of raw backtest quality, or depends on evidence dimensions not yet covered by these forks

### 2026-05-06 Slice 21: Family C NQ+ES cross-market confirmation at 1h

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-c-nq-es-profile`
- used the public synthetic profile on `NQ`
- manually added into the same external workspace:
  - `ES/USD` `1h/4h/1d` feather files
  - a new cross-market strategy `TomacNQEsSmtBreakout`
  - config whitelist updated to include:
    - `NQ/USD`
    - `ES/USD`
- completed closure:
  - `uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac_family_c.log --config config.tomac.json --output strategy_library_family_c.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-c-nq-es-profile --library /tmp/ict-engine-family-c-nq-es-profile/.deps/auto-quant/strategy_library_family_c.json --log /tmp/ict-engine-family-c-nq-es-profile/.deps/auto-quant/run_tomac_family_c.log`

**Result**
- Family C `1h` strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-0.1948`
    - `profit=-7.64%`
    - `trade_count=78`
  - `TomacKillzoneBreakout`
    - `sharpe=0.1956`
    - `profit=18.38%`
    - `trade_count=61`
    - `win_rate=63.9344%`
    - `profit_factor=1.4912`
  - `TomacNQEsSmtBreakout`
    - `sharpe=0.0665`
    - `profit=3.77%`
    - `trade_count=46`
    - `win_rate=58.6957%`
    - `profit_factor=1.1772`
  - `TomacRRWinRate`
    - `sharpe=0.134`
    - `profit=8.81%`
    - `trade_count=28`
    - `win_rate=67.8571%`
    - `profit_factor=1.773`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T192601.556001000Z`
- focused prior-init dry-run on `TomacNQEsSmtBreakout`:
  - `final_probs=[0.6481416296296296, 0.000003259259259259259, 0.3518551111111111]`

**Outcome**
- this is the first real `Family C` auto-quant slice using paired-market confirmation.
- the cross-market confirmation candidate is positive, but weaker than the better existing `NQ` candidates on the same horizon.

### 2026-05-06 Slice 22: Family C NQ+ES cross-market confirmation at 5m

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-c-nq-es-5m-profile`
- used the public synthetic profile on `NQ 5m`
- then manually added into the same external workspace:
  - `NQ/USD` `5m/1h/4h/1d`
  - `ES/USD` `5m/1h/4h/1d`
  - a new cross-market strategy `TomacNQEsSmtBreakout5m`
  - config whitelist updated to include:
    - `NQ/USD`
    - `ES/USD`
- completed closure:
  - `uv run --with ta-lib run_tomac.py`
  - `uv run export_strategy_library.py --strategies-dir user_data/strategies_external --log run_tomac_family_c_5m.log --config config.tomac.json --output strategy_library_family_c_5m.json`
  - `./target/debug/ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-family-c-nq-es-5m-profile --library /tmp/ict-engine-family-c-nq-es-5m-profile/.deps/auto-quant/strategy_library_family_c_5m.json --log /tmp/ict-engine-family-c-nq-es-5m-profile/.deps/auto-quant/run_tomac_family_c_5m.log`

**Result**
- Family C `5m` strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-0.1538`
    - `profit=-4.95%`
    - `trade_count=216`
  - `TomacKillzoneBreakout`
    - `sharpe=0.4211`
    - `profit=42.18%`
    - `trade_count=67`
    - `win_rate=70.1493%`
    - `profit_factor=2.0301`
  - `TomacNQEsSmtBreakout5m`
    - `sharpe=0.0315`
    - `profit=1.57%`
    - `trade_count=26`
    - `win_rate=61.5385%`
    - `profit_factor=1.1621`
  - `TomacRRWinRate`
    - `sharpe=-0.3842`
    - `profit=-10.83%`
    - `trade_count=163`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T193100.726656000Z`
- focused prior-init dry-run on `TomacNQEsSmtBreakout5m`:
  - `final_probs=[0.705872, 0.000005176470588235294, 0.29412282352941177]`

**Outcome**
- `Family C` now has both `1h` and `5m` real slices.
- but the cross-market candidates remain clearly weaker than the stronger existing `NQ` baseline candidates.

### 2026-05-06 Slice 25: Family F NQ stability/chaos proxy

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-f-nq-profile`
- added a dedicated stability/chaos-aware candidate:
  - `TomacNQStabilityBreakout`
- completed the same synthetic-profile closure:
  - `auto-quant-prepare`
  - `run_tomac.py`
  - `export_strategy_library.py`
  - `auto-quant-results-import`
- then reran after the candidate was correctly materialized into `strategies_external`

**Result**
- Family F strategy metrics after the corrected rerun:
  - `TomacAggressiveBE`
    - `sharpe=-0.2597`
    - `profit=-4.19%`
    - `trade_count=19`
  - `TomacKillzoneBreakout`
    - `sharpe=0.0315`
    - `profit=1.31%`
    - `trade_count=21`
  - `TomacNQStabilityBreakout`
    - `sharpe=-100.0`
    - `profit=0.71%`
    - `trade_count=1`
    - `win_rate=100.0%`
    - `profit_factor=0.0`
  - `TomacRRWinRate`
    - `sharpe=-0.0158`
    - `profit=-0.4%`
    - `trade_count=2`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T195642.037962000Z`
- focused prior-init dry-run on `TomacNQStabilityBreakout`:
  - `final_probs=[0.9999608888888889, 0.000019555555555555554, 0.000019555555555555554]`

**Outcome**
- `Family F` is now no longer untested.
- its first real `NQ` slice is materially weaker than the stronger `Family A` candidates and barely moves prior-init at all.
- current interpretation:
  - `Family F` does not deserve priority under the present no-code constraints
  - if revisited later, it should be because real upstream spectral/chaos evidence becomes available, not because this proxy filter is promising

### 2026-05-06 Slice 24: No-code plateau diagnostic

**Execution**
- compared the latest `workflow_snapshot.json` and `execution_tree_trace.json` across several isolated `NQ` states:
  - baseline `Family A` imported run
  - `TomacNQ_KillzoneBreakoutDisplacement`
  - `TomacNQKillzoneBreakout5m`
  - `TomacNQTrendPersistence`
- also tested the same stronger displacement candidate against the active analyze label row by applying it to:
  - `--parent-config 1,1,1`
  - corresponding to the current live labels:
    - `entry_quality=medium`
    - `factor_alignment=mixed`
    - `factor_uncertainty=high`

**Result**
- across baseline, displacement, `5m`, and `Family B` re-check states, these runtime fields remained unchanged:
  - `pre_bayes_gate_status = pass_neutralized`
  - `pre_bayes_evidence_quality_score = 0.4243112653658687`
  - `execution_readiness = 0.31868931152176383`
  - `execution_gate_status = execution_blocked`
  - `execution_edge_share = 0.33870883441752014`
  - `prediction_edge_share = 0.6612911655824798`
  - `family_score_map.structure_ict = 0.4670000000000001`
  - `family_score_map.options_hedging = 0.1540695195141977`
  - `family_score_map.cross_market_smt = 0.1225`
  - `execution_tree_trace.output.branch = transition_guardrail`
  - `execution_tree_trace.output.execution_bias = guarded`
  - `execution_tree_trace.output.gate_status = observe`
  - `execution_tree_trace.output.execution_score = 0.5121931942326463`
- even when the stronger displacement fork was written to the currently active CPT parent row (`1,1,1`), post-apply analyze still returned:
  - `quality=0.424`
  - `gate=pass_neutralized`
  - `Action: TUNE structure_ict`

**Outcome**
- current no-code Auto-Quant loops are definitely changing imported `trade_outcome` priors.
- but in this environment they are **not** changing the upstream evidence surfaces that currently dominate the execution tree:
  - `factor_alignment`
  - `factor_uncertainty`
  - `liquidity_context`
  - `execution_readiness`
- therefore the present no-code plateau is real, not just “more loops needed on the same lane”.

### 2026-05-06 Slice 23: Family B NQ trend-persistence probe

**Execution**
- created a fresh isolated state dir:
  - `/tmp/ict-engine-family-b-nq-profile`
- added a dedicated directionality / persistence candidate:
  - `TomacNQTrendPersistence`
- completed the same synthetic-profile closure:
  - `auto-quant-prepare`
  - `run_tomac.py`
  - `export_strategy_library.py`
  - `auto-quant-results-import`
- then ran a focused prior-init/apply check on an isolated copy:
  - `/tmp/ict-engine-family-b-nq-check`
  - `./target/debug/ict-engine auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-engine-family-b-nq-check --force --strategies TomacNQTrendPersistence`
  - `./target/debug/ict-engine analyze --symbol NQ ... --state-dir /tmp/ict-engine-family-b-nq-check --human`

**Result**
- Family B strategy metrics:
  - `TomacAggressiveBE`
    - `sharpe=-0.2597`
    - `profit=-4.19%`
    - `trade_count=19`
  - `TomacKillzoneBreakout`
    - `sharpe=0.0315`
    - `profit=1.31%`
    - `trade_count=21`
  - `TomacNQTrendPersistence`
    - `sharpe=0.0189`
    - `profit=0.66%`
    - `trade_count=3`
    - `win_rate=66.6667%`
    - `profit_factor=1.2346`
  - `TomacRRWinRate`
    - `sharpe=-0.0158`
    - `profit=-0.4%`
    - `trade_count=2`
- import closure succeeded:
  - `n_ok=4`
  - `n_meta_invalid=0`
  - `matched=4`
  - `library_artifact_id=auto_quant_strategy_library_NQ_20260505T194200.732533000Z`
- focused prior-init on `TomacNQTrendPersistence` moved the CPT row to:
  - `final_probs=[0.8054878881118881, 0.0000014586894586894585, 0.19451065319865316]`
- post-apply analyze still returned:
  - `quality=0.424`
  - `gate=pass_neutralized`
  - `Action: TUNE structure_ict`

**Outcome**
- `Family B` is now no longer untested.
- its first real `NQ` slice is materially weaker than the stronger `Family A` candidates.
- current interpretation:
  - `Family B` does not deserve priority over the stronger `Family A` line in the current `NQ` environment
  - if revisited later, it should be because a new directionality-specific hypothesis appears, not because the current persistence fork looks promising

### 2026-05-06 Slice 10: Family G real-data acquisition attempts

**Execution**
- attempted to obtain a first real Family G options/dealer-positioning slice through existing public tooling:
  - `./target/debug/ict-engine analyze-live --symbol NQ --state-dir /tmp/ict-engine-family-g-live --human`
  - `./target/debug/ict-engine market-data-harness --action fetch --request-json /tmp/ict-engine-family-g-harness-request.json`
  - `python scripts/auto_quant_external/fetch_external.py binance-kline ...`
  - `python scripts/auto_quant_external/fetch_external.py binance-options ...`
  - `python scripts/auto_quant_external/fetch_external.py bybit-kline ...`
  - `python scripts/auto_quant_external/fetch_external.py bybit-options ...`

**Result**
- `analyze-live` default path failed on upstream data source access:
  - `HTTP status client error (403 Forbidden)` for `NQ=F`
- `market-data-harness` with `yfinance` for `QQQ` / `^VXN` failed:
  - `yahoo chart returned error for 'QQQ'`
  - `yahoo chart returned error for '^VXN'`
- direct exchange fetchers also failed in this environment:
  - Binance spot/options: retries exhausted after repeated `SSLError`
  - Bybit spot/options: retries exhausted after repeated `SSLError`

**Outcome**
- Family G is no longer blocked by CLI surface absence.
- Family G is currently blocked in this environment by **provider/network acquisition failure**, not by missing repo surface.
- the next real Family G slice should reuse:
  - a working local live backend, or
  - an already captured options snapshot / auxiliary evidence file, or
  - a network path that can actually reach the required options providers

### 2026-05-06 Slice 26: Family G historical-state salvage audit

**Execution**
- audited the existing repo-local historical live states under:
  - `state/GC`
  - `state/CL`
  - `state/YM`
- inspected:
  - `workflow_snapshot.json`
  - `analyze_runs.json`
  - `artifact_ledger.json`
  - persisted `analyze_live_*` candle snapshots

**Result**
- historical live states do show materially higher `options_hedging` family scores than the current `NQ` no-code loop:
  - `GC`
    - `family_score_map.options_hedging = 0.5084220010906515`
  - `CL`
    - `family_score_map.options_hedging = 0.522982694279153`
  - `YM`
    - `family_score_map.options_hedging = 0.2575`
- however, those historical states do **not** expose a reusable raw `AuxiliaryMarketEvidence` object in a simple persisted JSON surface:
  - no recoverable `supporting.auxiliary` payload was found in `analyze_runs.json`
  - no standalone auxiliary artifact was found in `artifact_ledger.json`
  - the persisted `analyze_live_*` files are candle snapshots (`spot`, `ltf`, `m5`, `m1`, `h4`, `htf`), not the options/auxiliary object needed by the new `--auxiliary-evidence` surface

**Outcome**
- the repo already contains evidence that `Family G` can matter on markets like `GC` and `CL`.
- but that evidence is not yet persisted in a format the new public `--auxiliary-evidence` input can directly replay.
- therefore the current practical blocker is narrower and more precise:
  - not “no data ever existed”
  - but “no reusable persisted auxiliary/options artifact is currently available to feed back into factor-research without either a new live fetch or code work”

### 2026-05-06 Slice 27: Family G current-environment live retry check

**Execution**
- retried `analyze-live` directly on two markets that already had historical repo-local live state from earlier successful runs:
  - `./target/debug/ict-engine analyze-live --symbol GC --state-dir /tmp/ict-engine-family-g-gc-live`
  - `./target/debug/ict-engine analyze-live --symbol CL --state-dir /tmp/ict-engine-family-g-cl-live`

**Result**
- both retries now fail on the same upstream Yahoo path used by the current zero-config live runtime:
  - `GC=F`
    - `HTTP status client error (403 Forbidden)`
  - `CL=F`
    - `HTTP status client error (403 Forbidden)`

**Outcome**
- this confirms the current `Family G` blocker is not just `NQ`-specific.
- in the present environment, even historically successful `GC` / `CL` zero-config live paths are now unavailable.
- therefore the remaining no-code path for `Family G` genuinely requires one of:
  - a caller-supplied reusable auxiliary/options artifact
  - a working local live backend other than the current zero-config path
  - restored provider reachability

## Current Todo Board

### Done

- [x] Read execution-tree owner code.
- [x] Read execution feature / artifact owner code.
- [x] Read current factor CLI loop surfaces.
- [x] Separate “execution-tree needs” from “current in-repo registry names”.
- [x] Identify which family is blocked by missing public input surface rather than by missing factor logic.
- [x] Establish the baseline execution-tree snapshot for the target symbol.
- [x] Run Family A through the current public Auto-Quant surface and record its stop reason.
- [x] Expose a dedicated public auxiliary/options research input for Family G.
- [x] Expose an opt-in additive external runner profile for Family A and obtain the first real importable after-run artifact.
- [x] Re-check execution tree after the first real Family A imported run.
- [x] Run a second Family A iteration round and isolate the strongest current structure/setup candidate.
- [x] Prove the synthetic Family A profile on a second major futures-index market (`ES`).
- [x] Verify that the strongest current `NQ` candidate does not automatically generalize to `ES`.
- [x] Probe the same synthetic Family A profile on additional non-`NQ` markets and record which ones are positive, flat, or runtime-blocked.
- [x] Confirm that local cleaned data already exists for `1m/5m/15m/1h/4h/1d` on multiple markets.
- [x] Prove at least one real `5m` synthetic-profile execution slice end-to-end on `NQ`.
- [x] Prove real `15m` and `1m` synthetic-profile execution slices end-to-end on `NQ`.
- [x] Verify on isolated re-check states that the current `1dRegime` and `5m` NQ forks still do not move execution-tree `quality` or `gate_status`.
- [x] Produce a stronger `NQ` 1h structure-quality fork (`TomacNQ_KillzoneBreakoutDisplacement`) and verify that it still does not move execution-tree `quality` or `gate_status`.
- [x] Run the first real `Family C` paired-market auto-quant slices (`1h` and `5m`) using `NQ + ES`.
- [x] Run the first real `Family B` no-code `NQ` directionality/persistence slice and verify that it still does not move execution-tree `quality` or `gate_status`.
- [x] Confirm with runtime evidence that current no-code Auto-Quant loops are plateaued at the execution-tree layer even when trade_outcome priors move.
- [x] Run the first real `Family F` no-code `NQ` stability/chaos proxy slice and verify that it is still weaker than the stronger `Family A` candidates.

### Next

- [ ] Because the first imported Family A re-check still says `TUNE structure_ict`, keep iterating Family A quality on the new public surface until execution-tree development actually moves.
- [ ] Fork from `TomacNQ_KillzoneBreakout` rather than from the weaker generic branches, and test whether structure-specific variants can move `quality` or `gate_status`.
- [ ] Expand the set of **positive** synthetic-profile markets beyond `NQ` and `ES`; `YM` and `XAU` are now surface-proven but still not quality-proven.
- [x] Decide that `EUR` should not stay on the Family A structure lane for now; its strongest current candidate is the `TomacRRWinRate` branch.
- [x] Decide that `5m` is proven but secondary, and the main `NQ` focus should return to the stronger `1h` structure lane.
- [x] Decide that `15m` and `1m` should be deprioritized behind the stronger `1h` and `5m` `NQ` lanes unless a new hypothesis appears.
- [x] Decide to stop spending cycles on `1dRegime`, `15m`, or `1m` `NQ` forks unless a new hypothesis explains why they should move `quality` rather than just produce a positive backtest.
- [ ] Decide whether `TomacNQ_KillzoneBreakoutDisplacement` should replace `TomacNQ_KillzoneBreakout` as the default `NQ` Family A candidate for future no-code loops, or whether the extra displacement filter is only a backtest improvement without execution-tree value.
- [x] Decide that `Family C` should be deprioritized for now, since both `1h` and `5m` paired-market candidates are positive but clearly weaker than the stronger baseline candidates.
- [x] Decide that `Family B` should be actively deprioritized in the todo board now that its first real slice is weaker than `Family A` and still leaves execution-tree unchanged.
- [ ] Decide whether the objective should stay in “no-code iteration” mode at all, now that runtime evidence shows prior-init-only loops are not moving the execution-tree inputs.
- [ ] Use a reachable provider path, or a caller-supplied reusable `AuxiliaryMarketEvidence` / `supporting.auxiliary` file, to run the first real Family G `options_hedging` / dealer-positioning research slice rather than only proving the input contract.
- [ ] Run Family B: Directionality / Persistence only after Family A is stable.
- [ ] Run Family C: Cross-Market Confirmation once paired data exists.
- [ ] Run Family D whenever `wait_for_reversion` is the persistent blocker.
- [ ] Run Family E whenever `block_crowded` is the persistent blocker.
- [ ] Run Family F whenever readiness is suppressed by noise/chaos rather than by setup.
- [ ] Run Family G once options/dealer-positioning data is available for the chosen market/timeframe slice.
- [ ] Run Family H when execution viability is clearly session-dependent.

### Not Yet

- [ ] Treat current Rust factor registry as the final factor universe.
- [ ] Implement new factor families in repo code before Auto-Quant iteration proves they are needed.
- [ ] Pretend `options_hedging` is fully validated across market/timeframe coverage just because the public auxiliary/options input surface now exists.

## Blocked

- [ ] Family G Options / Dealer Positioning data quality for the chosen market slice
  - blocker: the new public input surface exists, but this environment currently cannot reach the needed live/options providers (`Yahoo 403`, `Binance SSLError`, `Bybit SSLError`) and has no running local live backend
  - blocker: historical repo-local live states show strong `options_hedging` scores, but they do not persist a reusable raw `AuxiliaryMarketEvidence` artifact that can be replayed into `factor-research --auxiliary-evidence`
  - acceptable temporary state: keep the new surface active, then treat provider reachability / reusable auxiliary artifact availability as the next gating issue rather than CLI absence
- [ ] No-code execution-tree plateau
  - blocker: current no-code Auto-Quant loops can change imported `trade_outcome` priors, but the active `analyze` / execution-tree path is still dominated by unchanged upstream evidence surfaces (`factor_alignment`, `factor_uncertainty`, `liquidity_context`, `execution_readiness`)
  - acceptable temporary state: stop assuming “more of the same no-code loops” will move the tree, and only continue no-code work when it brings new upstream evidence or new market/timeframe proof
- [ ] Multi-timeframe coverage beyond the currently proven slices
  - blocker: `1m/5m/15m/1h/4h/1d` data is locally available, and `1m/5m/15m/1h/4h/1d` are now all exercised on at least one `NQ` synthetic-profile lane, but `1w` and `1M` are still not prepared or proven
  - acceptable temporary state: keep logging separately:
    - intervals with local cleaned data available
    - intervals proven through the public profile
    - intervals still missing (`1w`, `1M`)
- [ ] YM synthetic-profile runtime stability
  - blocker: the current Family A strategy set hits `UnboundLocalError: cannot access local variable 'price' where it is not associated with a value` on `YM` for at least `TomacAggressiveBE` and `TomacKillzoneBreakout`
  - acceptable temporary state: do not count `YM` as a proven market until a narrower follow-up slice identifies whether the failure is strategy-specific or a broader synthetic futures runtime issue
- [ ] XAU Family A candidate quality
  - blocker: the profile surface imports cleanly on `XAU`, but the current strategy set produces `trade_count=0` across the board, so there is no actionable edge evidence yet
  - acceptable temporary state: count `XAU` as surface-proven but not as a positive quality/profit proof point

## Verification Checklist

- [ ] Every family uses its own isolated `/tmp/...` state dir.
- [ ] Every family logs one before/after `workflow-status --human` snapshot.
- [ ] Every family has an explicit stop reason: `improved`, `plateaued`, `data_blocked`, or `surface_blocked`.
- [ ] No family is declared “done” from return improvement alone; it must help execution-tree development.
- [ ] No family is declared “done” from a single-symbol improvement alone; each factor family should strive for broad market coverage and log any remaining coverage gap explicitly.
- [ ] No family is declared “done” from a single-timeframe improvement alone; each factor family should log which of `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`, and `1M` are covered, unsupported, or still pending.
