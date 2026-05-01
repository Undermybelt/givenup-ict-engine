# Structural Belief Learning Repo Map

Date: 2026-05-01
Status: patched_against_execution_plan
Scope: map literature mechanisms into concrete `ict-engine` belief surfaces, and mark what is already implemented vs still missing.

Aligned source docs:
- [2026-04-30-structural-belief-execution-plan.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/2026-04-30-structural-belief-execution-plan.md:1)
- [20260501repo.md](/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/20260501repo.md:1)

## Status Key

- `已实现`: versioned in repo and already used by production flows
- `部分实现`: repo has real code and tests, but the literature mechanism is only partially landed
- `未实现`: only planned / documented, not yet in the canonical runtime path

## Execution-Plan Alignment

| Execution phase | Repo status | Notes |
|---|---|---|
| `P0` Repo truth | `已实现` | execution plan, literature docs, and paper-code readmes are committed |
| `P1` Canonical structural anchor | `已实现` | downstream phases no longer redefine canonical structural lineage |
| `P2` Live feedback posterior update | `部分实现` | delayed resolution, fractional pseudo-count updates, compliance/off-policy exposure fields, clipped IPS counterfactual reward priors, and candidate-set policy logging exist; full DR/SNIPS correction remains |
| `P3` Offline evidence tempering | `部分实现` | source weighting, quality calibration, source panels, power-prior contribution objects, reusable source-reliability posteriors, and reliability-weighted panel aggregation exist |
| `P4` Structural prior state upgrade | `部分实现` | duration, transition, source panels, event ledger, separated prior-mass snapshots, and latest offline seed snapshot exist; richer dwell-time theory remains |
| `P5` BBN node/branch posterior update | `部分实现` | temporal priors adjust belief snapshots and branch surfaces, normalized outgoing branch-transition posterior state persists, and complete candidate-set branch adjustment consumes it directly |
| `P6` CatBoost path ranking target | `未实现` | structural candidate surfaces exist, but the formal target stack is not landed |

## Repo Targets

Allowed target surfaces:
- `structural_prior_state`
- `BBN node/branch posterior update`
- `CatBoost path ranking target`
- `artifact-validation prior source`
- `live feedback posterior update`

---

## 1. structural_prior_state

Status: `部分实现`

Primary papers
- `Sequential Bayesian Learning for Hidden Semi-Markov Models`
- `A sticky HDP-HMM with application to speaker diarization`
- `Using Bayesian Model Averaging to Calibrate Forecast Ensembles`

Already in repo
- persisted `LearningState.structural_prior_state`
- `source_panel_summaries`
- `last_offline_seed_source`
- `last_offline_seed_snapshot`
- `node_prior_mass`
- `branch_prior_mass`
- `scenario_prior_mass`
- `path_prior_mass`
- `event_ledger`
- `node_duration_priors`
- `branch_transition_priors`
- panel-derived prior reconstruction before structural display / ranking surfaces

Literature mechanisms still worth importing
- explicit HSMM-style duration distribution, not only streak-derived persistence
- sticky self-transition strength as a first-class parameter, not only blended persistence bias
- source-panel posterior aggregation written as explicit panel likelihood / prior math, not only weighted summary blending
- clearer node-level prior mass separation from branch/path-level prior mass

Suggested state fields
- `node_prior_mass`
- `node_duration_prior`
- `branch_transition_prior`
- `source_panel_summaries`
- `last_offline_seed_snapshot`

Current repo gap
- `node_duration_priors` and `branch_transition_priors` are real, and `node_prior_mass` / `branch_prior_mass` / `scenario_prior_mass` / `path_prior_mass` now keep entity-scaled prior mass auditable outside the generic stats maps
- `last_offline_seed_snapshot` is formalized as a persistent theory object for the latest offline seed, but deeper snapshot history / recalibration policy remains future work

Upgrade path
1. upgrade duration prior from streak summary to explicit dwell-time model
2. treat source panels as pre-merge posterior contributors, not only audit surfaces

---

## 2. BBN node/branch posterior update

Status: `部分实现`

Primary papers
- `Dynamic Bayesian Networks: Representation, Inference and Learning`
- `A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle`
- `Online Learning of Order Flow and Market Impact with Bayesian Change-Point Detection Methods`

Already in repo
- canonical belief snapshot consumes structural priors
- node duration prior adjusts regime confidence in belief snapshot
- branch transition prior adjusts canonical regime probabilities
- branch temporal posterior state stores `transition_prior`, `posterior_multiplier`, and normalized outgoing `normalized_transition_posterior`
- `regime_posterior`, `belief_posteriors["market_regime"]`, `gate_decision`, `strategy_recommendation`, and selected market subgraph are synchronized after adjustment
- workflow snapshot and ensemble surfaces reuse canonical structural regime posteriors across phases
- `workflow-status` temporal summary exposes the maintained normalized transition posterior for consumer agents
- complete candidate-set branch posterior adjustment reads maintained normalized transition posterior state before falling back to multiplier reconstruction

Literature mechanisms still worth importing
- discounted transition-count updates:
  - `N_ij(t) = lambda * N_ij(t-1) + P(z_(t-1)=i, z_t=j | x_1:t)`
- Hamilton/DBN-style recursive branch posterior maintenance
- BOCPD-style hazard handling for branch birth / node break
- moving branch posterior maintenance out of display-layer blending and into core belief-state updates

Suggested formulas
- discounted transition counts:
  - `N_ij(t) = lambda * N_ij(t-1) + P(z_(t-1)=i, z_t=j | x_1:t)`
- normalized branch posterior:
  - `pi_ij(t) = N_ij(t) / sum_j N_ij(t)`

Suggested implementation hooks
- `src/domain/belief/*`
- `src/application/belief/*`
- `src/state/*`

Current repo gap
- branch transition priors already affect branch prior/posterior surfaces and belief snapshots, and maintained branch temporal posterior state now carries normalized outgoing posterior mass
- complete candidate sets now consume the maintained transition posterior directly; partial candidate fallback and richer node transition handling still need consolidation

---

## 3. artifact-validation prior source

Status: `部分实现`

Primary papers
- `Power Prior Distributions for Regression Models`
- `Using Bayesian Model Averaging to Calibrate Forecast Ensembles`

Already in repo
- artifact validation feeds `structural_prior_state`
- source-specific weighting exists
- quality calibration exists
- validation regression can reduce effective contribution
- source panels preserve inspectable pre-merge evidence instead of only final aggregate prior
- source panels store the latest `StructuralPowerPriorContribution` with source rank, tempering coefficient, entity scale, effective tau, and weighted contribution masses
- `structural_prior_state.source_reliability_posteriors` stores reusable source-level reliability posteriors from offline seeds and live feedback
- panel-derived aggregate priors consume source-reliability posteriors so low-reliability high-mass panels shrink toward neutral instead of dominating by raw mass

Literature mechanisms still worth importing
- richer aggregate power-prior / tempered likelihood composition across source-panel contributions:
  - `posterior(theta) propto prior(theta) * product_s L_s(theta)^(tau_s)`
- consuming learned source-specific reliability posteriors during cross-source aggregation
- clearer split between source rank, evidence quality, recency, and drift penalty

Suggested formula
- `posterior(theta) propto prior(theta) * product_s L_s(theta)^(tau_s)`

Suggested `tau_s` ingredients
- base source rank
- execution readiness
- aggregate return quality
- score delta stability
- mutation acceptance rate
- conformal coverage quality
- break penalty

Current repo gap
- source reliability is persisted and consumed by panel aggregation, but reliability learning is still simple Beta-style mass accounting rather than a richer confusion-matrix model

---

## 4. live feedback posterior update

Status: `部分实现`

Primary papers
- `The Beta-Binomial Bayesian Model`
- `Counterfactual Risk Minimization: Learning from Logged Bandit Feedback`
- `Modeling Delayed Feedback in Display Advertising`

Already in repo
- `structural-feedback-v1` round-trips through `update --feedback-file`
- structural lineage survives in `FeedbackRecord`, `UpdateRunRecord`, `WorkflowSnapshot.latest_update`
- feedback updates persisted `structural_prior_state`
- explicit success/failure mass exists
- invalidated / abandoned / breakeven outcomes no longer look like pure wins
- not-followed feedback updates weighted exposure mass, weighted not-followed mass, execution propensity, and an off-policy-adjusted prior without adding reward pseudo-counts
- structural history surfaces expose execution propensity and off-policy exposure rate for consumer agents
- persisted structural stats and `structural-experience-priors` expose clipped IPS weight and counterfactual reward prior
- recommended path bundles log candidate-set id, candidate-set size, and selected path behavior-policy probability for later DR/SNIPS correction

Literature mechanisms still worth importing
- DR/SNIPS-style off-policy value correction using logged candidate-set policy probabilities
- maturity / censoring logic for delayed reward
- richer maturity / censoring logic for delayed reward beyond simple delayed -> resolved replacement
- compliance / propensity correction before updating execution value

Suggested formulas
- path success posterior:
  - `p_k ~ Beta(alpha_k, beta_k)`
  - `alpha_k += w * q * c * reward_credit`
  - `beta_k += w * q * c * loss_credit`
- optional OPE correction:
  - `V_DR = q(x, pi_e) + [pi_e(a|x)/pi_b(a|x)] * (r - q(x,a))`

Suggested outcome decomposition
- realized return component
- execution readiness realized component
- user compliance component
- invalidation cleanliness component

Current repo gap
- feedback learning is real and no longer heuristic-only; delayed outcomes now resolve into one posterior event and abandoned/invalidated outcomes use explicit pseudo-count weights
- not-followed recommendations now carry separate propensity/off-policy exposure fields and clipped IPS counterfactual reward priors, and recommended path bundles log behavior-policy probability; DR/SNIPS correction remains the next value-estimation step

---

## 5. CatBoost path ranking target

Status: `未实现`

Primary papers
- `Adaptive Conformal Inference Under Distribution Shift`
- `Modeling Delayed Feedback in Display Advertising`
- `Counterfactual Risk Minimization: Learning from Logged Bandit Feedback`

Already in repo
- structural candidate contract exists for `node / branch / scenario / path`
- path / branch / scenario / node history surfaces exist
- recommended path bundle and top-path candidate surfaces already exist for consumption

Not yet in repo
- training target surface for delayed / partial-compliance ranking
- explicit probability calibration layer for path acceptance
- lower-bound gating fields for execution
- propensity-aware evaluation / learning target

Suggested target stack
1. train raw ranking score on realized / corrected outcomes
2. debias eval under partial execution
3. apply probability calibration
4. maintain regime-conditional conformal coverage

Suggested fields
- `raw_path_score`
- `calibrated_path_prob`
- `path_prob_lower_bound`
- `pending_reward_state`
- `propensity_estimate`
- `regime_calibration_bucket`

Current repo gap
- CatBoost is still downstream work; current path ranking surfaces are structural-orchestration outputs, not a learned calibrated ranker target

---

## Recommended implementation order

### Phase 1
- `artifact-validation prior source`
- `live feedback posterior update`

Reason
- the repo already has working source weighting and feedback learning; the next gain is to make the math explicit and versionable

### Phase 2
- `structural_prior_state`
- `BBN node/branch posterior update`

Reason
- duration / transition state now exists; the next step is to move from persistence + surface adjustment into proper transition-count-driven posterior maintenance

### Phase 3
- `CatBoost path ranking target`

Reason
- ranking calibration should consume trustworthy structural candidates and posterior state, not race ahead of them

---

## Minimal Viable Theory Bundle

If only 5 mechanisms are implemented next, use these:
1. HSMM node duration prior
2. discounted DBN branch transition update
3. tempered offline pseudo-likelihood by source
4. Beta-Binomial fractional pseudo-count path outcome update
5. calibrated path probability + lower bound for execution gating

---

## Practical Reading Of Current Repo State

Use this summary when deciding the next coding slice:

- `canonical structural anchor`: `已实现`
- `canonical structural posterior propagation across phases`: `已实现`
- `offline source weighting + quality calibration`: `部分实现`
- `live structural feedback learning`: `部分实现`
- `source-panel inspectability`: `已实现`
- `duration / transition persistence`: `已实现`
- `duration / transition as core BBN transition engine`: `部分实现`
- `CatBoost calibrated path target`: `未实现`

The repo is no longer blocked on surface drift. The highest-value remaining work is now:
1. explicit tempered source contribution math
2. explicit fractional pseudo-count outcome math
3. discounted transition-count maintenance inside belief updates
4. only then CatBoost target design
