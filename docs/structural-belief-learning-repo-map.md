# Structural Belief Learning Repo Map

Date: 2026-04-30
Status: drafted
Scope: map literature mechanisms into concrete `ict-engine` belief surfaces

## Repo targets

Allowed target surfaces:
- `structural_prior_state`
- `BBN node/branch posterior update`
- `CatBoost path ranking target`
- `artifact-validation prior source`
- `live feedback posterior update`

---

## 1. structural_prior_state

Primary papers
- Bayesian Nonparametric Hidden Semi-Markov Models
- Posterior Belief Assessment
- Optimal execution with regime-switching market resilience

Mechanisms to import
- explicit duration prior for node persistence
- transition matrix between structural nodes / branches
- source-panel posterior aggregation before canonical commit

Suggested state fields
- `node_prior_mass`
- `node_duration_prior`
- `branch_transition_prior`
- `source_panel_summaries`
- `last_offline_seed_snapshot`

Upgrade path
1. add duration-aware node persistence
2. split node prior from branch prior
3. store source-specific seed summaries before aggregation

---

## 2. BBN node/branch posterior update

Primary papers
- Detecting bearish and bullish markets in financial time series using hierarchical hidden Markov models
- Online Estimation of Dynamic Bayesian Network Parameter
- Optimal execution in high-frequency trading with Bayesian learning

Mechanisms to import
- hierarchical latent state decomposition
- discounted transition-count updates
- posterior-to-policy coupling

Suggested formulas
- discounted transition counts:
  - `N_ij(t) = lambda * N_ij(t-1) + P(z_(t-1)=i, z_t=j | x_1:t)`
- normalized branch posterior:
  - `pi_ij(t) = N_ij(t) / sum_j N_ij(t)`

Suggested implementation hooks
- `src/domain/belief/*`
- `src/application/belief/*`
- `src/state/*`

---

## 3. artifact-validation prior source

Primary papers
- Likelihood Tempering in Dynamic Model Averaging
- Posterior Belief Assessment

Mechanisms to import
- source-specific tempering coefficient `tau_source`
- pseudo-likelihood powers for offline evidence
- multi-judgement prior synthesis before commit to canonical prior

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

---

## 4. live feedback posterior update

Primary papers
- The Beta-Binomial Bayesian Model
- Debiased Off-Policy Evaluation for Recommendation Systems
- Off-Policy Evaluation for Human Feedback

Mechanisms to import
- fractional pseudo-count updating for path outcomes
- separate executed vs non-executed path handling
- policy-mismatch correction before updating value estimates

Suggested formulas
- path success posterior:
  - `p_k ~ Beta(alpha_k, beta_k)`
  - `alpha_k += w * q * c * reward_credit`
  - `beta_k  += w * q * c * loss_credit`
- OPE correction:
  - `V_DR = q(x, pi_e) + [pi_e(a|x)/pi_b(a|x)] * (r - q(x,a))`

Suggested outcome decomposition
- realized return component
- execution readiness realized component
- user compliance component
- invalidation cleanliness component

---

## 5. CatBoost path ranking target

Primary papers
- Counterfactual contextual bandit for recommendation under delayed feedback
- Conformal Predictive Systems Under Covariate Shift
- Self-Calibrating Conformal Prediction

Mechanisms to import
- delayed reward handling with pending ledger
- weighted calibration under covariate shift
- probability calibration before thresholding

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

---

## Recommended implementation order

### Phase 1
- `artifact-validation prior source`
- `live feedback posterior update`

Reason
- easiest uplift from heuristic weighting to principled pseudo-counts and tempered evidence

### Phase 2
- `structural_prior_state`
- `BBN node/branch posterior update`

Reason
- once evidence math is cleaner, latent structural state can stabilize around duration and transition logic

### Phase 3
- `CatBoost path ranking target`

Reason
- ranker calibration should sit on top of cleaner structural and posterior surfaces, not precede them

---

## Minimal viable theory bundle

If only 5 mechanisms are implemented, use these:
1. HSMM node duration prior
2. discounted DBN branch transition update
3. tempered offline pseudo-likelihood by source
4. Beta-Binomial fractional pseudo-count path outcome update
5. calibrated path probability + lower bound for execution gating
