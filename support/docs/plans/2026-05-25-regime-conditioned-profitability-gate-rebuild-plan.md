# Regime-Conditioned Profitability Gate Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use aegis:subagent-driven-development (recommended) or aegis:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current over-strict Board B promotion gates with a typed, regime-conditioned profitability lifecycle that can learn from factors when the market-state regime is correct, while keeping live-trade execution gates fail-closed.

**Architecture:** Keep the existing provider -> regime posterior -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree -> feedback/update chain. Destructively refactor the gate semantics inside that chain by splitting factor states into three planes: learning admission, paper/sim admission, and live trade usability. Hard cost, density, validation-row, PDA, transition, and execution-readiness thresholds move out of early factor death decisions and become later-plane blockers or telemetry.

**Tech Stack:** Rust application modules under `src/application/*`, existing structural path ranking artifacts, Python research/support scripts under `support/scripts/research/*`, current CLI surfaces (`factor-candidate-packs`, `factor-candidate-admission-targets`, `policy-training-status`, `workflow-status`), and existing unit/integration tests.

**Baseline / Authority Refs:** `AGENT.md`; `support/docs/plans/2026-05-24-board-b-current.md`; `support/docs/plans/2026-05-12-board-a-regime-state-current.md`; `support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md`; `support/docs/plans/2026-05-18-gate-rigidity-audit-todo.md`; `src/application/orchestration/factor_candidate.rs`; `src/application/orchestration/execution_tree.rs`; `src/domain/execution/gates.rs`; `support/scripts/research/regime_root_survivor_blocker_report.py`; `support/scripts/research/downstream_practical_admission_source_check.py`.

**Compatibility Boundary:** Public/default CLI remains zero-config and non-trading. Existing `promotion_allowed`, `trade_usable`, and `update_goal` fields must stay false unless the live-trade plane passes. Docs remain non-runtime. Regime-rooted branch grammar stays `main_regime -> sub_regime -> ... -> profit_factor`; market/product/provider/symbol/timeframe remain provenance labels only. Board A regime-confidence ownership is unchanged.

**Verification:** TDD for each changed Rust/Python owner, targeted Rust/Python tests, `cargo fmt --check`, `cargo check`, and a zero-config smoke using `/tmp`. Task 10 lists the exact commands one per line so cargo filters remain unambiguous.

---

## Design Decision

Current Board B gates answer too many questions with one verdict. A factor can be a valid regime-conditioned profit source and still fail a later live-execution guard because the current market is crowded, the sample is sparse, PDA disagrees, validation rows are immature, or a fixed 5bps stress is too punitive for the instrument. Those later facts are useful blockers, but they should not erase a factor from the learning loop.

This plan creates a lifecycle with separate truth surfaces:

- `learning_admission`: "Given a correctly identified regime, should this factor continue to train and accumulate evidence?"
- `paper_admission`: "Is it worth simulated/paper replay under realistic instrument friction and forward evidence?"
- `live_trade_usable`: "Can the execution tree act now?"

Only `live_trade_usable=true` may drive old practical fields. `learning_admission=true` is not a trading claim.

## 2026-05-25 Self-Review Fixes

This plan was reviewed against current Rust/Python consumers before implementation. The review found these implementation hazards and this version closes them explicitly:

- Do not infer `learning_admission=admitted` from Pre-Bayes alone. Execution-tree output may project live admission, but learning admission must come from a lifecycle artifact with regime confidence, declared-friction expectancy, leakage, and provider evidence; otherwise it is `not_evaluated`.
- Do not extend the global `structural_path_ranking_reward_label` for learning-only rows. That helper drives calibration/training behavior across the ranker. Learning-only rows must stay out of production mature-row accounting unless a later feedback artifact intentionally promotes them.
- Do not set `maturity_mask=true` for sparse learning-only rows. In current consumers, `maturity_mask` contributes to mature-row counts and validation readiness.
- Do not assume every artifact already has `net_after_declared_friction_pct`. Builders must normalize known cost keys and mark raw-profit fallbacks as blockers.
- Do not use invalid multi-filter cargo commands. Each cargo test command below has one test target/filter shape that cargo accepts.
- Do not let paper/live blockers mask learning blockers or vice versa. Classification hierarchy is explicit: learning validity first, then paper readiness, then live trade usability.
- Do not use broad variable-name heuristics for the practical-source guard. Only tainted learning values flowing into `promotion_allowed`, `trade_usable`, or `update_goal` are violations.
- Do not infer policy-training `live_ready_count`, `promotion_allowed`, or `trade_usable` from legacy ranker `execution_gate_status=pass|ready|execution_ready|admissible`. Those values predate the lifecycle split and may only prove ranker/execution-gate visibility. Policy training may count live trade usability only from explicit lifecycle live-plane statuses such as `live_trade_ready` or `live_trade_usable`.
- Do not let `workflow-status` synthesize live readiness from a structural candidate that is merely `ready && actionable`. Structural recommended-path visibility is not a live-plane artifact. Missing `live_trade_status=ready` plus explicit `promotion_allowed=true`, `trade_usable=true`, and `update_goal=true` must remain fail-closed.
- Do not let `execution-tree` become the live-plane bypass. Its closed-loop admission may set live practical flags only when Pre-Bayes is ready, execution gate is ready, execution tree branch is ready, execution readiness is at least `0.65`, transition hazard is below `0.60`, the path-ranker score is actually consumed by execution, and ranker validation is ready. PDA remains telemetry unless a later source contract reintroduces it as a hard gate.
- Do not let the canonical lifecycle owner become a second bypass. `decide_profitability_lifecycle` must not set live practical flags from a legacy `execution_gate_status=pass|ready|execution_ready|admissible` string alone. Missing same-root live-plane predicates produce `live_plane_artifact_missing`, and live readiness also requires Pre-Bayes ready, execution tree ready, `fill_viable`, path-ranker consumed by execution, and ranker validation ready.
- Do not let diagnostic-only support tools reuse live practical field names. Source diagnostics and candidate-pack intake must use diagnostic names such as `diagnostic_candidate_passed_gate` and `requires_downstream_live_gates`; they must not emit `promotion_allowed`, `trade_usable`, or `update_goal` unless they are explicitly writing a live-plane artifact.

## Non-Goals

- Do not relax Board A regime-confidence acceptance.
- Do not mark any existing Board B factor trade-usable from this refactor alone.
- Do not remove provider, Pre-Bayes, BBN, CatBoost, execution tree, or feedback/update surfaces.
- Do not make markdown a runtime input.
- Do not turn HMM state ids, provider names, symbols, or timeframes into branch roots.
- Do not delete old evidence packets or other agents' active work.

## New Typed Contract

Create this canonical schema in Rust and mirror it in Python artifact builders:

```json
{
  "schema_version": "factor-profitability-lifecycle/v1",
  "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> ibkr_avgo_mim_1m_mtf_v1",
  "regime_condition": {
    "board_a_regime_source": "workflow_snapshot|regime_confidence_asset|manual_frozen_context",
    "regime_confidence": 0.95,
    "regime_confidence_floor": 0.95,
    "regime_confidence_passed": true
  },
  "learning_admission": {
    "status": "not_evaluated|admitted|observe|blocked",
    "reason": "regime_conditioned_positive_expectancy",
    "long_run_expectancy_after_declared_friction": 0.012,
    "evidence_count": 12,
    "leakage_check": "pass",
    "provider_state": "ready|blocked|retained_real|local_research"
  },
  "paper_admission": {
    "status": "not_evaluated|ready|observe|blocked",
    "blockers": ["thin_forward_density"]
  },
  "live_trade": {
    "status": "not_evaluated|ready|observe|blocked",
    "promotion_allowed": false,
    "trade_usable": false,
    "update_goal": false,
    "blockers": ["execution_readiness_below_live_floor"]
  },
  "telemetry": {
    "fixed_bps_stress": {"0": 0.0, "1": 0.0, "2": 0.0, "5": 0.0},
    "instrument_cost_profile_id": "CME_NQ_default_v1",
    "trade_count": 12,
    "validation_rows": {"raw_scored_mature": 12, "production": 12, "observation": 12},
    "pre_bayes_gate_status": "pass_neutralized",
    "execution_gate_status": "execution_ready",
    "execution_tree_gate_status": "ready",
    "execution_tree_branch": "fill_viable",
    "execution_readiness": 0.52,
    "transition_hazard": 0.67,
    "pda_hybrid_alignment": false,
    "path_ranker_score_used_by_execution_tree": false,
    "ranker_validation_ready": false
  }
}
```

## File Ownership Map

- New Rust owner: `src/application/factor_lifecycle/profitability_admission.rs`
  - Owns typed lifecycle decision structs and pure decision functions.
- Modify: `src/application/factor_lifecycle/mod.rs`
  - Exports the new module.
- Modify: `src/application/orchestration/factor_candidate.rs`
  - Candidate-pack admission rows use learning lifecycle state instead of old hard density/profit-only maturity logic.
- Modify: `src/application/orchestration/execution_tree.rs`
  - Keeps live execution fail-closed, adds explicit learning/paper/live distinction in closed-loop branch admission.
- Modify: `src/application/orchestration/workflow_status.rs`
  - Exposes lifecycle fields in agent/human status without implying trade use.
- Modify: `src/application/entry_models/training_export.rs`
  - Reports lifecycle row counts and training readiness separately from live readiness.
- Modify: `support/scripts/research/factor_candidate_pack.py`
  - Emits `factor_profitability_lifecycle` and regime-conditioned payoff metadata in candidate packs.
- Modify: `support/scripts/research/factor_signal_diagnostics.py`
  - Keeps signal diagnostics diagnostic-only and avoids live practical field names.
- Modify: `support/scripts/research/regime_root_survivor_blocker_report.py`
  - Becomes a v2 lifecycle classifier: old blockers are moved to paper/live planes unless they invalidate learning.
- Modify: `support/scripts/research/downstream_practical_admission_source_check.py`
  - Allows learning-admission flags but keeps `promotion_allowed`, `trade_usable`, and `update_goal` guarded by live admission.
- Modify docs in this commit slice:
  - `support/docs/plans/2026-05-24-board-b-current.md`
  - `support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md`

## Task 0: Preflight Consumer Map And Baseline Guardrails

**Files:**
- Read only: `src/application/orchestration/factor_candidate.rs`
- Read only: `src/application/orchestration/execution_tree.rs`
- Read only: `src/belief_core/ranking_label.rs`
- Read only: `src/application/entry_models/training_export.rs`
- Read only: `src/application/orchestration/workflow_status.rs`
- Read only: `support/scripts/research/factor_candidate_pack.py`
- Read only: `support/scripts/research/regime_root_survivor_blocker_report.py`
- Read only: `support/scripts/research/downstream_practical_admission_source_check.py`

**Why this task exists:**
- The refactor changes vocabulary used by runtime, reports, and training export. A preflight map prevents an implementation from changing one owner while silently breaking another.
- Current ranker consumers treat `maturity_mask`, `calibrated_label`, and `training_weight` as training/validation signals. The learning plane must not pollute those signals accidentally.

**Impact / Compatibility:**
- No files are changed in this task.
- The output is a short implementation note inside the first code commit message or PR body, not a repo artifact, unless the implementing session explicitly needs a temporary scratch file under `/tmp`.

**Verification:**
- Commands below exit `0` when expected matches are present.

- [ ] **Step 1: Map practical flag consumers**

Run:

```bash
rg -n "promotion_allowed|trade_usable|update_goal" \
  src/application \
  support/scripts/research \
  tests \
  support/scripts/tests
```

Expected: output includes `factor_candidate.rs`, `execution_tree.rs`, `workflow_status.rs`, candidate-pack/report scripts, and practical-source guard tests where present. Any writer of these fields must be classified as either live-only owner or read-only status/report adapter before implementation starts.

- [ ] **Step 2: Map ranker training consumers**

Run:

```bash
rg -n "pending_reward_state|maturity_mask|calibrated_label|training_weight|structural_path_ranking_reward_label" \
  src/belief_core/ranking_label.rs \
  src/application/orchestration/factor_candidate.rs \
  src/application/entry_models/training_export.rs
```

Expected: output shows global reward-label and training-weight logic in `ranking_label.rs`, candidate row creation in `factor_candidate.rs`, and status/training export consumers in `training_export.rs`.

- [ ] **Step 3: Freeze compatibility decisions before edits**

Record these decisions in the implementation notes:

```text
promotion_allowed/trade_usable/update_goal: live-only fields.
structural_path_ranking_reward_label: unchanged unless a dedicated ranker-calibration task updates all consumers.
learning-only candidate rows: maturity_mask=false, calibrated_label=None, training_weight=None.
paper/live-ready feedback rows: existing matured_success/matured_failure states keep current semantics.
```

- [ ] **Step 4: Commit**

No commit for this task. Continue to Task 1 with the consumer map open.

## Task 1: Add Canonical Profitability Lifecycle Type

**Files:**
- Create: `src/application/factor_lifecycle/profitability_admission.rs`
- Modify: `src/application/factor_lifecycle/mod.rs`
- Test: unit tests inside `src/application/factor_lifecycle/profitability_admission.rs`

**Why this task exists:**
- The current system has no single owner for "learn this factor" versus "trade this factor."
- A typed owner prevents the old hard-gate semantics from reappearing in wrappers and markdown.

**Impact / Compatibility:**
- No CLI behavior changes yet.
- Existing live gates remain unchanged.

**Verification:**
- `cargo test --lib profitability_admission -- --nocapture`

- [ ] **Step 1: Write failing tests**

Add tests for these cases:

```rust
#[test]
fn learning_admits_regime_conditioned_positive_expectancy_even_when_live_blocked() {
    let input = ProfitabilityAdmissionInput {
        regime_confidence: Some(0.96),
        regime_confidence_floor: 0.95,
        long_run_expectancy_after_declared_friction: Some(0.004),
        evidence_count: 8,
        leakage_passed: true,
        provider_state: ProviderEvidenceState::Ready,
        execution_readiness: Some(0.41),
        transition_hazard: Some(0.72),
        pda_hybrid_alignment: Some(false),
        pre_bayes_gate_status: Some("pass_neutralized".to_string()),
        execution_gate_status: Some("blocked".to_string()),
        execution_tree_gate_status: Some("blocked".to_string()),
        execution_tree_branch: Some("block_crowded".to_string()),
        path_ranker_score_used_by_execution_tree: false,
        ranker_validation_ready: false,
        validation_rows: ValidationRows {
            raw_scored_mature: 8,
            production: 8,
            observation: 8,
        },
    };

    let decision = decide_profitability_lifecycle(&input);

    assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
    assert_eq!(decision.paper.status, AdmissionStatus::Observe);
    assert_eq!(decision.live.status, AdmissionStatus::Blocked);
    assert!(!decision.live.promotion_allowed);
    assert!(!decision.live.trade_usable);
}

#[test]
fn learning_blocks_when_regime_confidence_is_missing_or_wrong() {
    let input = ProfitabilityAdmissionInput {
        regime_confidence: Some(0.62),
        regime_confidence_floor: 0.95,
        long_run_expectancy_after_declared_friction: Some(0.02),
        evidence_count: 40,
        leakage_passed: true,
        provider_state: ProviderEvidenceState::Ready,
        execution_readiness: Some(0.80),
        transition_hazard: Some(0.20),
        pda_hybrid_alignment: Some(true),
        pre_bayes_gate_status: Some("pass_hard".to_string()),
        execution_gate_status: Some("ready".to_string()),
        execution_tree_gate_status: Some("ready".to_string()),
        execution_tree_branch: Some("fill_viable".to_string()),
        path_ranker_score_used_by_execution_tree: true,
        ranker_validation_ready: true,
        validation_rows: ValidationRows {
            raw_scored_mature: 40,
            production: 40,
            observation: 40,
        },
    };

    let decision = decide_profitability_lifecycle(&input);

    assert_eq!(decision.learning.status, AdmissionStatus::Blocked);
    assert!(decision.learning.blockers.contains(&"regime_confidence_below_floor".to_string()));
    assert!(!decision.live.trade_usable);
}
```

- [ ] **Step 2: Run the tests to confirm failure**

Run:

```bash
cargo test --lib profitability_admission -- --nocapture
```

Expected: FAIL because the module and types do not exist.

- [ ] **Step 3: Implement the minimal module**

Implement the public structs/enums and `decide_profitability_lifecycle`. Keep thresholds named and local to this module first:

```rust
pub const DEFAULT_REGIME_CONFIDENCE_FLOOR: f64 = 0.95;
pub const LIVE_EXECUTION_READINESS_FLOOR: f64 = 0.65;
pub const LIVE_TRANSITION_HAZARD_CAP: f64 = 0.60;
pub const PAPER_VALIDATION_MIN_ROWS: usize = 30;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdmissionStatus {
    NotEvaluated,
    Admitted,
    Ready,
    Observe,
    Blocked,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProviderEvidenceState {
    Ready,
    RetainedReal,
    LocalResearch,
    Blocked,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidationRows {
    pub raw_scored_mature: usize,
    pub production: usize,
    pub observation: usize,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProfitabilityAdmissionInput {
    pub regime_confidence: Option<f64>,
    pub regime_confidence_floor: f64,
    pub long_run_expectancy_after_declared_friction: Option<f64>,
    pub evidence_count: usize,
    pub leakage_passed: bool,
    pub provider_state: ProviderEvidenceState,
    pub execution_readiness: Option<f64>,
    pub transition_hazard: Option<f64>,
    pub pda_hybrid_alignment: Option<bool>,
    pub pre_bayes_gate_status: Option<String>,
    pub execution_gate_status: Option<String>,
    pub execution_tree_gate_status: Option<String>,
    pub execution_tree_branch: Option<String>,
    pub path_ranker_score_used_by_execution_tree: bool,
    pub ranker_validation_ready: bool,
    pub validation_rows: ValidationRows,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdmissionPlaneDecision {
    pub status: AdmissionStatus,
    pub blockers: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LiveTradeDecision {
    pub status: AdmissionStatus,
    pub blockers: Vec<String>,
    pub promotion_allowed: bool,
    pub trade_usable: bool,
    pub update_goal: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProfitabilityLifecycleDecision {
    pub learning: AdmissionPlaneDecision,
    pub paper: AdmissionPlaneDecision,
    pub live: LiveTradeDecision,
}
```

Decision rules:

- Learning admits when:
  - regime confidence is present and `>= regime_confidence_floor`;
  - expectancy after declared friction is present and `> 0`;
  - `evidence_count > 0`;
  - leakage passed;
  - provider state is not `Blocked`.
- Paper is `Ready` only when learning admitted and all validation rows meet `30`; otherwise `Observe`.
- Live is `Ready` only when paper ready, Pre-Bayes is `pass_hard` or `pass_neutralized`, execution gate is one of `ready`, `execution_ready`, `pass`, or `admissible`, execution tree gate is `ready`, execution tree branch is `fill_viable`, readiness is `>= 0.65`, transition hazard is `< 0.60`, path-ranker score was consumed by execution, and ranker validation is ready. PDA is telemetry, not a hard gate in this module.
- A legacy execution-gate-ready string without same-root live-plane predicates must stay `Blocked` with `live_plane_artifact_missing`.
- `promotion_allowed`, `trade_usable`, `update_goal` are true only in the live-ready branch.
- All public structs/enums in this module derive `Serialize` and `Deserialize` with explicit snake_case JSON names where the artifact contract needs stable strings. Example:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdmissionStatus {
    NotEvaluated,
    Admitted,
    Ready,
    Observe,
    Blocked,
}
```

- [ ] **Step 4: Export the module**

Add this to `src/application/factor_lifecycle/mod.rs`:

```rust
pub mod profitability_admission;
```

- [ ] **Step 5: Run tests**

Run:

```bash
cargo test --lib profitability_admission -- --nocapture
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/application/factor_lifecycle/profitability_admission.rs src/application/factor_lifecycle/mod.rs
git commit -m "feat: add profitability lifecycle admission policy"
```

## Task 2: Preserve Live Execution Hard Gates But Add Lifecycle Output

**Files:**
- Modify: `src/application/orchestration/execution_tree.rs`
- Test: `tests/hard_gate_execution_first.rs` and unit tests in `src/application/orchestration/execution_tree.rs`

**Why this task exists:**
- Execution must remain fail-closed for live trading, but execution blockers must not delete learning candidates.

**Impact / Compatibility:**
- Existing `hard_gate_execution_first` behavior stays unchanged.
- Closed-loop admission JSON gains `learning_admission_status`, `paper_admission_status`, and `live_trade_status`.

**Verification:**
- `cargo test --test hard_gate_execution_first`
- `cargo test --lib execution_tree_closed_loop_branch_admission`

- [ ] **Step 1: Add failing unit test**

Add a unit test near existing closed-loop admission tests. The important assertion is that execution-tree code does not fabricate learning admission from Pre-Bayes readiness:

```rust
#[test]
fn closed_loop_admission_keeps_learning_not_evaluated_without_lifecycle_artifact() {
    let output = ExecutionTreeOutput {
        gate_status: "blocked".to_string(),
        branch: "block_crowded".to_string(),
        execution_bias: "skip".to_string(),
        execution_readiness: Some(0.42),
        hybrid_transition_hazard: Some(0.71),
        pda_hybrid_alignment: Some(false),
        path_ranker_score_visible_to_execution_tree: true,
        path_ranker_score_used_by_execution_tree: false,
        ranker_validation_ready: false,
        ..ExecutionTreeOutput::default()
    };

    let value = build_execution_tree_closed_loop_branch_admission_value(
        "TrendExpansion -> PublicSourceMomentum -> long_run_edge -> ibkr_public_momentum_v1",
        "pass_neutralized",
        "execution_blocked",
        &output,
    );

    assert_eq!(value["status"], "fail_closed");
    assert_eq!(value["learning_admission_status"], "not_evaluated");
    assert_eq!(value["paper_admission_status"], "not_evaluated");
    assert_eq!(value["live_trade_status"], "blocked");
    assert_eq!(value["promotion_allowed"], false);
    assert_eq!(value["trade_usable"], false);
}
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cargo test --lib closed_loop_admission_keeps_learning_not_evaluated_without_lifecycle_artifact -- --nocapture
```

Expected: FAIL because the fields are missing.

- [ ] **Step 3: Add fields without weakening existing status**

Inside `build_execution_tree_closed_loop_branch_admission_value`, keep closed-loop admission fail-closed and add live-only lifecycle projection. `ready && actionable` is not enough by itself; the live plane must also satisfy readiness, transition, and validated-ranker consumption predicates:

```rust
let learning_admission_status = "not_evaluated";
let paper_admission_status = "not_evaluated";
let execution_readiness_ready = output
    .execution_readiness
    .is_some_and(|readiness| readiness >= EXECUTION_GATE_READY);
let transition_hazard_ready = output
    .hybrid_transition_hazard
    .is_some_and(|hazard| hazard < 0.60);
let ranker_live_ready =
    output.path_ranker_score_used_by_execution_tree && output.ranker_validation_ready;
let live_plane_ready = pre_bayes_ready
    && execution_ready
    && execution_tree_ready
    && execution_readiness_ready
    && transition_hazard_ready
    && ranker_live_ready;
let live_trade_status = if live_plane_ready { "ready" } else { "blocked" };
```

Add JSON fields:

```rust
"learning_admission_status": learning_admission_status,
"paper_admission_status": paper_admission_status,
"live_trade_status": live_trade_status,
"promotion_allowed": live_trade_status == "ready",
"trade_usable": live_trade_status == "ready",
"update_goal": live_trade_status == "ready",
```

Do not make `learning_admission_status` depend on `pre_bayes_ready`. If a future caller passes a serialized `ProfitabilityLifecycleDecision`, preserve that lifecycle value verbatim in a separate task with tests proving missing lifecycle remains `not_evaluated`.

`workflow-status` must consume these explicit fields, not reconstruct live readiness from legacy structural candidate fields. A structural candidate with `ready=true` and `actionable=true` but no live-plane/practical flags must remain `fail_closed` and must not unblock `pass_neutralized` workflow state.

- [ ] **Step 4: Run live-gate regression**

Run:

```bash
cargo test --test hard_gate_execution_first
```

Expected: PASS; strong prediction with weak execution still blocks.

- [ ] **Step 5: Commit**

```bash
git add src/application/orchestration/execution_tree.rs tests/hard_gate_execution_first.rs
git commit -m "feat: expose factor lifecycle states in execution admission"
```

## Task 3: Rework Candidate Admission Rows Around Long-Run Regime Payoff

**Files:**
- Modify: `src/application/orchestration/factor_candidate.rs`
- Test: unit tests in `src/application/orchestration/factor_candidate.rs`

**Why this task exists:**
- `factor-candidate-admission-targets` currently turns candidates into path-ranker rows using trade count and aggregate profit observations. It needs to preserve learning candidates even when density is thin or live gates are not ready.

**Impact / Compatibility:**
- Structural path target schema remains `structural-path-ranking-target-v1`.
- New lifecycle fields must be encoded through existing optional fields and lineage/score metadata, not by breaking row deserialization.

**Verification:**
- `cargo test --lib factor_candidate -- --nocapture`
- `cargo run --quiet -- factor-candidate-packs --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-lifecycle-plan-check --agent`

- [ ] **Step 1: Add failing test for sparse positive regime-conditioned candidate**

Create a candidate pack fixture in the unit test where:

- `branch_path_contract.regime_profit_branch_path` is present.
- `factor_eval_grid_summary.factor_profitability_lifecycle.learning_admission.status` is `admitted`.
- aggregate trade count is below `30`.
- total profit after declared friction is positive.

Expected row. This row is visible to candidate inventory and path-ranking readback, but it is not a supervised mature training row until later feedback produces a normal `matured_success`/`matured_failure` state:

```rust
assert_eq!(row.pending_reward_state, "regime_conditioned_learning_success");
assert_eq!(row.maturity_mask, false);
assert_eq!(row.calibrated_label, None);
assert_eq!(row.training_weight, None);
assert_eq!(row.direction, "Observe");
assert_eq!(row.execution_gate_status.as_deref(), Some("learning_admitted_live_blocked"));
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cargo test --lib factor_candidate_sparse_regime_conditioned_positive_admits_learning -- --nocapture
```

Expected: FAIL because the old code returns `candidate_pack_admission_pending`.

- [ ] **Step 3: Add lifecycle read helper**

In `build_factor_candidate_admission_target_artifact`, read:

```rust
let lifecycle = eval_summary
    .get("factor_profitability_lifecycle")
    .and_then(Value::as_object);
let learning_status = lifecycle
    .and_then(|value| value.pointer("/learning_admission/status"))
    .and_then(Value::as_str);
let learning_expectancy = lifecycle
    .and_then(|value| value.pointer("/learning_admission/long_run_expectancy_after_declared_friction"))
    .and_then(Value::as_f64);
```

Then set:

```rust
let regime_learning_success =
    learning_status == Some("admitted") && learning_expectancy.is_some_and(|value| value > 0.0);
let pending_reward_state = if regime_learning_success {
    "regime_conditioned_learning_success"
} else {
    existing_pending_reward_state
};
```

Keep `structural_path_ranking_reward_label` unchanged. `regime_conditioned_learning_success` is a lifecycle/readback state, not a global calibrated reward label.

Set learning-only row training fields explicitly:

```rust
let learning_only = pending_reward_state == "regime_conditioned_learning_success";
let calibrated_label = if learning_only {
    None
} else {
    structural_path_ranking_reward_label(pending_reward_state)
};
let maturity_mask = if learning_only {
    false
} else {
    calibrated_label.is_some()
};
let maturity_weight = if learning_only {
    0.0
} else if full_profit_observation {
    1.0
} else if external_score_observation {
    0.5
} else {
    0.0
};
let propensity_estimate = maturity_mask.then_some(behavior_policy_probability);
let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
let training_weight =
    structural_path_ranking_training_weight(calibrated_label, maturity_weight, ips_weight);
```

If the team later wants learning rows to train a separate exploration model, add a separate field/owner such as `learning_signal_weight` instead of reusing `maturity_mask`.

To keep the factor visible to the learning loop without polluting supervised production labels, carry the positive lifecycle signal through existing non-label fields:

```rust
let normalized_expectancy_prior = learning_expectancy
    .map(|value| (0.5 + value.tanh() / 2.0).clamp(0.0, 1.0));

if learning_only {
    target_policy_reward_prior = normalized_expectancy_prior;
    target_policy_reward_lower_bound =
        normalized_expectancy_prior.map(|value| (value - 0.10).max(0.0));
    experience_prior = Some("regime_conditioned_learning_positive_expectancy".to_string());
    current_posterior = normalized_expectancy_prior;
}
```

This is an exploration/readback signal. Production supervised ranker loss still waits for normal mature feedback rows.

- [ ] **Step 4: Keep old practical fields false**

For lifecycle-admitted learning rows, set:

```rust
direction: "Observe".to_string(),
execution_gate_status: Some("learning_admitted_live_blocked".to_string()),
execution_gate_reason: Some("learning admission is not live trade usability".to_string()),
```

- [ ] **Step 5: Run targeted tests**

Run:

```bash
cargo test --lib factor_candidate -- --nocapture
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/application/orchestration/factor_candidate.rs
git commit -m "feat: admit regime-conditioned learning candidates to ranker"
```

## Task 4: Update Candidate Pack Builder To Emit Lifecycle Evidence

**Files:**
- Modify: `support/scripts/research/factor_candidate_pack.py`
- Test: `support/scripts/research/tests/test_factor_candidate_pack.py`

**Why this task exists:**
- Python candidate pack generation is the ingress for many public repo/paper factors. It must emit regime-conditioned lifecycle evidence without claiming live trade use.

**Impact / Compatibility:**
- Three-file candidate pack contract remains unchanged.
- New fields are additive.

**Verification:**
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack`

- [ ] **Step 1: Add failing test**

Add a test named `test_candidate_pack_emits_factor_profitability_lifecycle_for_regime_conditioned_edge`:

```python
self.assertEqual(
    bundle["factor_eval_grid_summary"]["factor_profitability_lifecycle"]["schema_version"],
    "factor-profitability-lifecycle/v1",
)
self.assertEqual(
    bundle["factor_eval_grid_summary"]["factor_profitability_lifecycle"]["learning_admission"]["status"],
    "admitted",
)
self.assertFalse(
    bundle["transfer_score"]["timeframe_ladder_transfer"]["promotion_allowed"],
)
self.assertFalse(
    bundle["transfer_score"]["timeframe_ladder_transfer"]["trade_usable"],
)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack.FactorCandidatePackTests.test_candidate_pack_emits_factor_profitability_lifecycle_for_regime_conditioned_edge
```

Expected: FAIL because lifecycle evidence is missing.

- [ ] **Step 3: Implement lifecycle builder**

Add helper:

```python
def _declared_friction_expectancy(metrics: dict[str, Any]) -> tuple[float | None, list[str]]:
    blockers: list[str] = []
    for key in (
        "net_after_declared_friction_pct",
        "instrument_cost_total_profit_pct",
        "net_after_5bps_side_pct",
        "net_after_5bps_per_side_pct",
        "5bps_per_side_total_profit_pct",
    ):
        value = metrics.get(key)
        if value is not None:
            return float(value), blockers
    raw_profit = metrics.get("total_profit_pct")
    if raw_profit is not None:
        blockers.append("declared_friction_missing_raw_profit_only")
        return float(raw_profit), blockers
    blockers.append("declared_friction_expectancy_missing")
    return None, blockers


def _factor_profitability_lifecycle(candidate_spec: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    regime_confidence = candidate_spec.get("regime_confidence")
    expectancy, expectancy_blockers = _declared_friction_expectancy(metrics)
    leakage_passed = candidate_spec.get("leakage_check", "pass") == "pass"
    provider_state = candidate_spec.get("provider_state", "ready")
    learning_ok = (
        regime_confidence is not None
        and float(regime_confidence) >= float(candidate_spec.get("regime_confidence_floor", 0.95))
        and expectancy is not None
        and float(expectancy) > 0.0
        and leakage_passed
        and provider_state != "blocked"
    )
    return {
        "schema_version": "factor-profitability-lifecycle/v1",
        "learning_admission": {
            "status": "admitted" if learning_ok else "blocked",
            "long_run_expectancy_after_declared_friction": expectancy,
            "evidence_count": int(metrics.get("trade_count") or 0),
            "leakage_check": "pass" if leakage_passed else "fail",
            "provider_state": provider_state,
            "blockers": ([] if learning_ok else expectancy_blockers),
        },
        "paper_admission": {
            "status": "observe",
            "blockers": ["forward_validation_required", *expectancy_blockers],
        },
        "live_trade": {
            "status": "blocked",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "blockers": ["live_execution_gate_not_evaluated"],
        },
    }
```

Call it from `build_factor_candidate_pack` and store under `factor_eval_grid_summary`.

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add support/scripts/research/factor_candidate_pack.py support/scripts/research/tests/test_factor_candidate_pack.py
git commit -m "feat: emit factor profitability lifecycle in candidate packs"
```

## Task 5: Convert Survivor Blocker Report To Lifecycle Report

**Files:**
- Modify: `support/scripts/research/regime_root_survivor_blocker_report.py`
- Test: `support/scripts/research/tests/test_regime_root_survivor_blocker_report.py`

**Why this task exists:**
- The current report drops or blocks candidates when they fail 5bps, readiness, transition, PDA, or validation rows. The new contract must classify these as learning, paper, or live blockers.

**Impact / Compatibility:**
- Keep output fields `promotion_allowed=false` and `trade_usable=false` unless live ready.
- `decision` values change; consumers must use explicit lifecycle fields.

**Verification:**
- `python3 -m unittest support.scripts.research.tests.test_regime_root_survivor_blocker_report`

- [ ] **Step 1: Add failing test**

Add test:

```python
def test_regime_positive_sparse_candidate_is_learning_admitted_not_dropped(self) -> None:
    import json
    import tempfile
    from pathlib import Path

    metrics = {
        "branch_fields_preserved": True,
        "branch_path": "TrendExpansion -> PublicSourceMomentum -> cost_window -> public_mim",
        "selected_gate1_row": {
            "label": "PUBLIC/MIM/1m",
            "trade_count": 4,
            "net_after_declared_friction_pct": 0.42,
            "survives_5bps_per_side": False,
        },
        "regime_confidence": 0.96,
        "leakage_check": "pass",
        "provider_state": "retained_real",
    }
    candidate = {
        "candidate_status": "no_trade",
        "actionable": False,
        "pre_bayes_evidence_filter": {
            "gating_status": "pass_neutralized",
            "conflict_flags": [],
            "evidence_assignments": {
                "regime_profit_branch_path": metrics["branch_path"],
            },
        },
    }
    tree = {
        "output": {
            "execution_readiness": 0.41,
            "hybrid_transition_hazard": 0.72,
            "pda_hybrid_alignment": False,
            "ranker_validation_ready": False,
            "path_ranker_score_visible_to_execution_tree": True,
            "path_ranker_score_used_by_execution_tree": False,
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        gate1_path = root / "gate1.json"
        candidate_path = root / "candidate.json"
        tree_path = root / "tree.json"
        gate1_path.write_text(json.dumps(metrics), encoding="utf-8")
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        tree_path.write_text(json.dumps(tree), encoding="utf-8")

        built = report.build_report(gate1_path, candidate_path, tree_path)

    self.assertEqual(built["decision"], "learning_admitted_paper_observe")
    self.assertEqual(built["factor_profitability_lifecycle"]["learning_admission"]["status"], "admitted")
    self.assertEqual(built["factor_profitability_lifecycle"]["paper_admission"]["status"], "observe")
    self.assertEqual(built["factor_profitability_lifecycle"]["live_trade"]["status"], "blocked")
    self.assertFalse(built["promotion_allowed"])
    self.assertFalse(built["trade_usable"])
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_regime_root_survivor_blocker_report.RegimeRootSurvivorBlockerReportTests.test_regime_positive_sparse_candidate_is_learning_admitted_not_dropped
```

Expected: FAIL because no 5bps survivor currently drops the branch.

- [ ] **Step 3: Refactor classifier**

Replace early `no_real_cost_5bps_survivor` drop logic with:

- learning blockers:
  - branch path invalid;
  - regime confidence missing/below floor;
  - expectancy after declared friction missing or non-positive;
  - leakage failed;
  - provider truly blocked with no retained evidence.
- paper blockers:
  - no exact 5bps survivor;
  - validation rows below floor;
  - thin forward density.
- live blockers:
  - execution candidate not ready;
  - readiness below floor;
  - transition hazard high;
  - ranker validation not ready;
  - path ranker visible but not used.

Classification:

```python
live_ready = learning_admitted and not paper_blockers and not live_blockers
if learning_blockers:
    decision = "learning_blocked"
elif live_ready:
    decision = "live_trade_ready"
elif paper_blockers:
    decision = "learning_admitted_paper_observe"
elif live_blockers:
    decision = "learning_admitted_live_blocked"
else:
    decision = "learning_admitted_paper_observe"
```

This order is intentional. Paper blockers come before live blockers because a candidate that has not reached paper/sim readiness cannot honestly be described as only live-blocked.

- [ ] **Step 4: Preserve old flags**

Set:

```python
report["promotion_allowed"] = decision == "live_trade_ready"
report["trade_usable"] = decision == "live_trade_ready"
```

- [ ] **Step 5: Run tests**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_regime_root_survivor_blocker_report
```

Expected: PASS after updating old expected decisions intentionally.

- [ ] **Step 6: Commit**

```bash
git add support/scripts/research/regime_root_survivor_blocker_report.py support/scripts/research/tests/test_regime_root_survivor_blocker_report.py
git commit -m "feat: split survivor report into learning paper and live gates"
```

## Task 6: Update Practical-Admission Source Guard

**Files:**
- Modify: `support/scripts/research/downstream_practical_admission_source_check.py`
- Test: `support/scripts/research/tests/test_downstream_practical_admission_source_check.py`

**Why this task exists:**
- Existing AST guard correctly blocks unsafe `promotion_allowed` and `trade_usable`, but it does not know about learning-plane fields.
- Diagnostic-only tools can also leak risk by reusing live practical field names for "interesting signal" telemetry.

**Impact / Compatibility:**
- Unsafe practical assignments remain violations.
- New `learning_admission` or `learning_allowed` fields are allowed only when they do not feed `promotion_allowed`, `trade_usable`, or `update_goal`.
- Diagnostic-only wrappers should use non-practical names such as `diagnostic_candidate_passed_gate` and `requires_downstream_live_gates`.

**Verification:**
- `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check`

- [ ] **Step 1: Add tests**

Add:

```python
def test_allows_learning_admission_without_practical_flags(self) -> None:
    path = self.write_source("""
def build_metrics(branch_ok):
    return {
        "learning_admission_status": "admitted" if branch_ok else "blocked",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
""")
    report = checker.check_source_file(path)
    self.assertTrue(report["ok"])
```

And:

```python
def test_flags_learning_admission_reused_as_trade_usable(self) -> None:
    path = self.write_source("""
def build_metrics(branch_ok):
    lifecycle = {"learning_allowed": branch_ok}
    learning_allowed = lifecycle["learning_allowed"]
    return {
        "learning_allowed": learning_allowed,
        "trade_usable": learning_allowed,
    }
""")
    report = checker.check_source_file(path)
    self.assertFalse(report["ok"])
```

- [ ] **Step 2: Run guard tests to verify failure/pass split**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check
```

Expected: new first test may pass already; second must fail until explicit taint detection is added.

- [ ] **Step 3: Add learning-to-practical taint detection**

Add precise taint tracking to `PracticalAssignmentVisitor`:

```python
LEARNING_KEYS = frozenset((
    "learning_admission",
    "learning_admission_status",
    "learning_allowed",
))


def contains_learning_source(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Subscript) and string_key(child.slice) in LEARNING_KEYS:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if child.value in LEARNING_KEYS:
                return True
    return False
```

Then inside the visitor:

```python
self.learning_tainted_names: set[str] = set()
```

On assignment, mark only names whose value is a learning source or already-tainted name:

```python
def is_learning_tainted_value(self, node: ast.AST) -> bool:
    if contains_learning_source(node):
        return True
    return any(isinstance(child, ast.Name) and child.id in self.learning_tainted_names for child in ast.walk(node))
```

For `Assign` and `AnnAssign`, add target names to `learning_tainted_names` when `is_learning_tainted_value(value)` is true. In `visit_Dict`, if `key in PRACTICAL_KEYS` and `is_learning_tainted_value(value_node)` is true, append:

```python
{
    "line": getattr(value_node, "lineno", getattr(node, "lineno", 0)),
    "column": getattr(value_node, "col_offset", getattr(node, "col_offset", 0)),
    "key": key,
    "value": expression_text(self.source, value_node),
    "violation": "learning_admission_reused_as_practical_flag",
}
```

Do not flag harmless variable names that merely contain the substring `learning` unless their value comes from one of the explicit learning keys or an already-tainted variable.

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add support/scripts/research/downstream_practical_admission_source_check.py support/scripts/research/tests/test_downstream_practical_admission_source_check.py
git commit -m "test: guard learning admission from practical flag reuse"
```

## Task 7: Expose Lifecycle In Policy Training And Workflow Status

**Files:**
- Modify: `src/application/entry_models/training_export.rs`
- Modify: `src/application/orchestration/workflow_status.rs`
- Test: existing unit tests in both files plus CLI tests in `tests/provider_neutral_cli.rs` if needed.

**Why this task exists:**
- Agents need to see why a factor is still useful even when live execution blocks it.

**Impact / Compatibility:**
- Additive JSON/human/agent fields.
- Existing summary lines should remain compact.

**Verification:**
- `cargo test --lib policy_training_status`
- `cargo test --lib workflow_status`
- `cargo test --test provider_neutral_cli`

- [ ] **Step 1: Add failing status tests**

Policy training expected line:

```text
factor_lifecycle: learning_admitted=1 paper_ready=0 live_ready=0 trade_usable=false
```

Workflow expected JSON:

```json
{
  "factor_profitability_lifecycle": {
    "learning_admission_status": "admitted",
    "paper_admission_status": "observe",
    "live_trade_status": "blocked",
    "trade_usable": false
  }
}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cargo test --lib policy_training_status -- --nocapture
cargo test --lib workflow_status -- --nocapture
```

Expected: FAIL because fields do not exist.

- [ ] **Step 3: Add read/summary fields**

In status builders, parse lifecycle data from target rows or execution admission artifacts and count:

- `learning_admitted_count`
  - count `pending_reward_state == "regime_conditioned_learning_success"` and explicit lifecycle artifacts with `learning_admission_status == "admitted"`;
  - do not require `maturity_mask=true`, `calibrated_label`, or `training_weight`;
- `paper_ready_count`
- `live_ready_count`
- `live_trade_usable_count`

Use `promotion_allowed=false` if live count is zero. Do not treat legacy
`execution_gate_status=pass`, `ready`, `execution_ready`, or `admissible` as live
trade usability; those values are ranker/execution-gate states unless a
lifecycle live-plane value explicitly says `live_trade_ready` or
`live_trade_usable`.

- [ ] **Step 4: Run tests**

Run:

```bash
cargo test --lib policy_training_status -- --nocapture
cargo test --lib workflow_status -- --nocapture
cargo test --test provider_neutral_cli
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/application/entry_models/training_export.rs src/application/orchestration/workflow_status.rs tests/provider_neutral_cli.rs
git commit -m "feat: surface profitability lifecycle in status commands"
```

## Task 8: Update Board B Runtime Contract Docs

**Files:**
- Modify: `support/docs/plans/2026-05-24-board-b-current.md`
- Modify: `support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md`

**Why this task exists:**
- Current docs still tell agents that no 5bps/density survivor means drop and no downstream. That policy conflicts with the new lifecycle.

**Impact / Compatibility:**
- Docs remain instruction/authority, not runtime input.
- Historical terminal rows are not rewritten; the active May 24 board and
  ingestion guide carry the supersession rule for this slice.

**Verification:**
- `rg -n "5bps|density|promotion_allowed|trade_usable|learning_admission|live_trade" support/docs/plans/2026-05-24-board-b-current.md support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md support/docs/plans/2026-05-25-regime-conditioned-profitability-gate-rebuild-plan.md`

- [ ] **Step 1: Edit Gate Model in Board B current**

Replace current one-lane gate wording with:

```text
Gate 1, learning viability: a factor may be learning-admitted when a frozen or current Board A regime context is correct, leakage checks pass, provider/local evidence is real or explicitly retained, and long-run expectancy after declared friction is positive. Gate 1 no longer requires fixed 5bps survival, 30 validation rows, PDA alignment, transition hazard below 0.60, or execution readiness above 0.65.

Gate 2, paper/sim admission: requires enough forward or retained-real density, instrument-aware friction, and replayable candidate packs.

Gate 3, portability: reproduces learning/paper evidence across chosen markets or documents the branch as local/scope-limited.

Gate 4, live trade usability: requires Pre-Bayes/BBN/CatBoost/execution tree and keeps `promotion_allowed`, `trade_usable`, and `update_goal` false unless live-ready.
```

- [ ] **Step 2: Update candidate ingestion**

Change the minimum path to:

```text
candidate evidence
-> candidate pack three-file contract with factor_profitability_lifecycle
-> factor-candidate-packs inventory
-> factor-candidate-admission-targets export
-> policy-training-status readback
-> learning/paper/live lifecycle gates
```

- [ ] **Step 3: Record diversity matrix supersession boundary**

Do not stage the large shared May 20 matrix in this slice. Instead, keep this
plan and the May 24 active board explicit that older rows using the old hard
promotion model are superseded:

```text
Rows before 2026-05-25 used the old hard 5bps/density/downstream promotion model. Treat their negative economics as paper/live blockers unless the packet also invalidates learning by regime mismatch, leakage, non-positive declared-friction expectancy, or provider truth failure.
```

- [ ] **Step 4: Verify docs**

Run:

```bash
rg -n "learning_admission|live_trade|5bps|execution_readiness >= 0.65|transition_hazard < 0.60|pda_hybrid_alignment=true|PDA alignment" support/docs/plans/2026-05-24-board-b-current.md support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md support/docs/plans/2026-05-25-regime-conditioned-profitability-gate-rebuild-plan.md
```

Expected: new lifecycle language present; any remaining hard thresholds, including fixed 5bps, validation density, transition hazard, PDA alignment, and execution readiness, are explicitly scoped to paper/live and are not learning-admission blockers.

- [ ] **Step 5: Commit**

```bash
git add support/docs/plans/2026-05-24-board-b-current.md support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md support/docs/plans/2026-05-25-regime-conditioned-profitability-gate-rebuild-plan.md
git commit -m "docs: redefine Board B gates around profitability lifecycle"
```

## Task 9: Add Migration Readback For Existing Evidence

**Files:**
- Create: `support/scripts/research/factor_lifecycle_migration_readback.py`
- Create: `support/scripts/research/tests/test_factor_lifecycle_migration_readback.py`

**Why this task exists:**
- Many prior packets were classified under old gates. We need a read-only migration surface that reclassifies existing JSON/CSV summaries without modifying old artifacts.

**Impact / Compatibility:**
- Read-only script.
- No deletion, no provider launch, no Auto-Quant launch.

**Verification:**
- `python3 -m unittest support.scripts.research.tests.test_factor_lifecycle_migration_readback`

- [ ] **Step 1: Write failing tests**

Use a temp run root containing:

- a terminal summary with `decision=drop_gate1_no_exact_1m_5bps_density_survivor`;
- a cost row with positive declared-friction expectancy using one of: `net_after_declared_friction_pct`, `instrument_cost_total_profit_pct`, `net_after_5bps_side_pct`, `net_after_5bps_per_side_pct`, or `5bps_per_side_total_profit_pct`;
- `regime_confidence=0.96`;
- `leakage_check=pass`.

Expected migration:

```python
self.assertEqual(result["migration_decision"], "old_drop_reclassified_learning_admitted_paper_observe")
self.assertFalse(result["writes_old_artifacts"])
self.assertFalse(result["promotion_allowed"])
self.assertFalse(result["trade_usable"])
```

- [ ] **Step 2: Implement parser**

Read only these files when present:

- `summaries/terminal_decision_summary.md`
- `summaries/gate1_cost_stress.csv`
- `summaries/rank_rows_cost_stress.csv`
- `summaries/*.csv` when the filename contains `cost`, `gate`, `rank`, `terminal`, or `summary`
- `checks/terminal_metrics.json`
- `checks/*.json`
- `materials/*.json`

Never scan historical May 10 logs from this script.

Use the same declared-friction normalization order as Task 4:

```python
DECLARED_FRICTION_KEYS = (
    "net_after_declared_friction_pct",
    "instrument_cost_total_profit_pct",
    "net_after_5bps_side_pct",
    "net_after_5bps_per_side_pct",
    "5bps_per_side_total_profit_pct",
)
```

Only fall back to `total_profit_pct` when no declared-friction key exists, and include blocker `declared_friction_missing_raw_profit_only`.

- [ ] **Step 3: Emit JSONL and compact markdown**

Fields:

- `run_root`
- `old_decision`
- `migration_decision`
- `learning_admission_status`
- `paper_admission_status`
- `live_trade_status`
- `promotion_allowed=false`
- `trade_usable=false`
- `evidence_paths`

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest support.scripts.research.tests.test_factor_lifecycle_migration_readback
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add support/scripts/research/factor_lifecycle_migration_readback.py support/scripts/research/tests/test_factor_lifecycle_migration_readback.py
git commit -m "feat: add read-only factor lifecycle migration readback"
```

## Task 10: Full Verification And Zero-Config Smoke

**Files:**
- No new code unless verification exposes a blocker.

**Why this task exists:**
- This is a destructive semantic refactor. It must prove old live safety remains intact and new learning admission is visible.

**Impact / Compatibility:**
- Confirms no source generated private path leaks in public smoke.

**Verification:**
- Commands below.

- [ ] **Step 1: Format**

Run:

```bash
cargo fmt --check
```

Expected: PASS.

- [ ] **Step 2: Rust checks**

Run:

```bash
cargo check
cargo test --test hard_gate_execution_first
cargo test --test provider_neutral_cli
cargo test --lib profitability_admission -- --nocapture
cargo test --lib lifecycle_blocks_live_when_only_legacy_execution_gate_is_ready -- --nocapture
cargo test --lib factor_candidate -- --nocapture
cargo test --lib execution_tree_closed_loop_branch_admission -- --nocapture
cargo test --lib policy_training_status -- --nocapture
cargo test --lib policy_training_status_does_not_treat_legacy_execution_gate_pass_as_live_trade_usable -- --nocapture
cargo test --lib workflow_status -- --nocapture
```

Expected: PASS.

- [ ] **Step 3: Python tests**

Run:

```bash
python3 -m unittest \
  support.scripts.research.tests.test_factor_candidate_pack \
  support.scripts.research.tests.test_factor_signal_diagnostics \
  support.scripts.research.tests.test_regime_root_survivor_blocker_report \
  support.scripts.research.tests.test_downstream_practical_admission_source_check \
  support.scripts.research.tests.test_factor_lifecycle_migration_readback
python3 support/scripts/research/downstream_practical_admission_source_check.py \
  support/scripts/research/factor_candidate_pack.py \
  support/scripts/research/factor_signal_diagnostics.py \
  support/scripts/research/regime_root_survivor_blocker_report.py \
  support/scripts/research/factor_lifecycle_migration_readback.py
```

Expected: PASS.

- [ ] **Step 4: Zero-config smoke**

Run:

```bash
rm -rf /tmp/ict-engine-profitability-lifecycle-smoke
cargo run --quiet -- provider-status --compact
cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-profitability-lifecycle-smoke --human
cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-profitability-lifecycle-smoke --refresh --agent
cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-profitability-lifecycle-smoke --output-format agent
```

Expected:

- Commands exit `0`.
- Output shows no private absolute home paths.
- Demo is not described as trade-ready.
- `promotion_allowed` and `trade_usable` remain false unless a real live-ready packet exists.
- Lifecycle fields are visible where relevant.

- [ ] **Step 5: Commit final verified slice**

```bash
git status --short
git add <only files touched by this plan>
git commit -m "feat: rebuild factor gates around regime-conditioned profitability"
```

## Repair Track

Root cause being addressed:

- Board B conflates early learning viability with late live-execution safety.
- Fixed 5bps/density/validation/PDA/readiness thresholds kill public source-backed factors before the engine can learn whether they work under the correct Board A regime.
- The old `promotion_allowed` vocabulary is too coarse: it suggests one binary outcome when at least three separate decisions exist.

Canonical owner being changed:

- New owner: `src/application/factor_lifecycle/profitability_admission.rs`.
- Existing consumers become adapters to that owner.

Smallest necessary change:

- Add typed lifecycle states.
- Route candidate admission, blocker reports, and status outputs through those states.
- Keep live execution hard gates unchanged.

Compatibility boundary:

- `promotion_allowed`, `trade_usable`, and `update_goal` remain live-only.
- Existing CLI commands keep names and basic output contract.
- Existing structural-path-ranking target schema is not broken.

Task-level verification:

- Unit tests prove learning can admit while live blocks.
- Regression tests prove weak execution still blocks live trading.

## Retirement Track

Old owner / fallback / duplicate branch:

- Hard-coded Board B prose model: `no exact 1m 5bps density survivor -> drop/no downstream`.
- Script-local practical flag patterns in downstream wrappers.
- Candidate admission maturity based only on full profit observation or external Sharpe.

Still active:

- Yes, until Tasks 1-8 land.

Only reason to keep it:

- Historical packets and old docs need readback compatibility.

Trigger for deletion or convergence:

- After migration readback proves old packets are reclassified without losing evidence and all tests pass, old hard-drop language can be archived or narrowed to paper/live gate language.

Verification before removal:

- `factor_lifecycle_migration_readback.py` produces a no-write report for representative old `drop_gate1_no_exact_1m_5bps_density_survivor`, downstream fail-closed, provider-blocked, and live-ready packets.

## Rollback Plan

If the refactor creates unsafe practical flags:

1. Revert only the source commits that changed runtime lifecycle wiring.
2. Keep the read-only migration script and docs plan if they remain accurate.
3. Run `downstream_practical_admission_source_check.py` over modified wrappers.
4. Confirm `workflow-status` and `policy-training-status` no longer expose lifecycle fields before retrying.

If the refactor breaks zero-config consumer smoke:

1. Disable lifecycle fields in public/human output first.
2. Keep JSON artifact generation available behind existing internal status surfaces.
3. Re-run the zero-config smoke before restoring public fields.

## Success Criteria

- A public/paper factor with correct regime context and positive long-run expectancy can enter the learning/ranker loop even if it fails fixed 5bps, 30-row validation, PDA, transition, or live execution readiness.
- The same factor remains non-trade-usable until live execution gates pass.
- Existing CLI and docs make the distinction visible to agents and humans.
- Old Board B terminal evidence is not deleted or misreported; it is reclassified by read-only migration.
- No new runtime dependency on markdown is introduced.
