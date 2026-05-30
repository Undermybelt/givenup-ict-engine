# Rachev Tail Reward-Risk Admission Source Prep

- Created: `2026-05-31T07:31:31+0800`
- Agent name: `codex-rachev-tail-reward-risk-admission-source-prep-20260531T073131+0800`
- Route: `sd/ict-engi-fact-rese-muta`
- Runtime skill: `/Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md`
- Run root: `/tmp/ict-engine-rachev-tail-reward-risk-admission-source-prep-20260531T073131+0800`
- Workdoc: `/tmp/ict-engine-rachev-tail-reward-risk-admission-source-prep-20260531T073131+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T073131+0800-codex-rachev-tail-reward-risk-admission-source-prep.claim`
- Compact root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T073131+0800-codex-rachev-tail-reward-risk-admission-source-prep-v1`
- Status: `terminalized_source_prep_no_launch_runtime_occupied`

## Blocker Snapshot

Same-turn compact audit at `2026-05-31T07:37:36+0800` reported
`status=needs_attention`, `valid_active_claims=1`, `live_factor_processes=1`,
`promotion_allowed_true=0`, `trade_usable_true=0`, and no same-tree practical
closure. The live owner was
`codex-vhf-chop-trend-reacceleration-exact-aq-launch-20260531T072254+0800`
writing under
`/tmp/ict-engine-vhf-chop-trend-reacceleration-exact-aqprep-20260531T063527+0800`;
focused `ps` showed PID `91749` running `run_tomac_one.py` for the VHF/CHOP
exact-AQ child. Therefore this packet did not launch provider, IBKR historical,
AutoQuant, Freqtrade/TOMAC backend, retained-cache local backtest, paper/sim/live,
or downstream lifecycle commands.

Post-write verification audit at `2026-05-31T07:43:46+0800` still reported
`status=needs_attention`: the live child had exited, but the same VHF/CHOP claim
remained a fresh active claim without live process. Fresh active claim state is
still a no-launch condition.

## Candidate

- Factor family: `rachev_tail_reward_risk_admission_filter`
- Factor id template: `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_<timeframe>_v1`
- Role: parent-signal admission filter, not standalone alpha.
- Branch path: `ValidationMaturity -> TailRewardRiskAsymmetry -> RachevExpectedTailGainLoss -> ParentSignalAdmissionFilter -> tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_<timeframe>_v1`
- Target timeframes: `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
- Session target: `ETH/full_retained_session`
- RTH filter applied: `false`
- Current evidence class: `source_prep_only`
- Promotion flags: `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

## Source Readback

- Crossref API for DOI `10.3905/jpm.2004.443328` returned HTTP 200 and verified
  the article metadata for Biglova, Ortobelli, Rachev, and Stoyanov,
  "Different Approaches to Risk Estimation in Portfolio Theory", Journal of
  Portfolio Management, 2004.
- RDocumentation for `PerformanceAnalytics::RachevRatio` returned HTTP 200 and
  verified the package-level function semantics: the Rachev ratio estimates
  upper-tail reward potential relative to lower-tail risk in non-Gaussian return
  settings.
- DOI landing page redirected to the PM Research host but returned HTTP 403, so
  the article landing page itself is not treated as fetched-content evidence;
  Crossref metadata and the RDocumentation function page are the captured
  readbacks for this no-launch packet.

These sources support the reward-risk metric and implementation shape only. They
are not profitability evidence.

## Formula Sketch

Use completed, shifted evidence only. For a later parent-rescore sidecar, define
an excess-return sample `x = return - hurdle` from either shifted rolling bar
returns or prior completed parent-trade outcomes available before the candidate
entry timestamp. Then compute:

- `upper_tail_gain = mean(x[x >= quantile(x, 1 - beta)])`
- `lower_tail_loss = mean(-x[x <= quantile(x, alpha)])`
- `rachev_ratio = upper_tail_gain / max(lower_tail_loss, eps)`

Admission rule: allow an already-owned parent trend/rejoin/breakout signal only
when the past-only Rachev state is above a predeclared hurdle and the admitted
subset improves parent-only instrument-cost economics, density retention,
split/year stability, drawdown/tail-loss shape, and downstream lifecycle
readiness. Reject if the filter merely cherry-picks the current candidate's
future payoff or collapses into a post-hoc trade-return sort.

## Duplicate Check

Focused same-turn searches for `rachev`, `tail reward`, `tail_reward`, `expected
tail`, `tail gain`, `tail loss`, and `reward risk` found no exact Rachev local
packet in current top-level experiment docs, runner scripts, repo-local skills,
or Board B claim files. Nearby lanes are intentionally distinct: L-moment
tail-shape, Omega payoff-asymmetry, CAViaR dynamic tail exceedance, realized
skew/tail asymmetry, downside-beta/coskew, copula tail dependence, time-under-
water/drawdown recovery, and Ulcer/drawdown risk surfaces.

## Terminal Decision

- `provider_fetch_started=false`
- `ibkr_historical_started=false`
- `autoquant_started=false`
- `freqtrade_tomac_started=false`
- `local_screen_started=false`
- `paper_sim_live_started=false`
- `downstream_lifecycle_started=false`
- `post_write_audit=needs_attention active_claims=1 live_factor_processes=0 fresh_active_claims_without_live_process=1`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- Decision: `terminalized_source_prep_no_launch_runtime_occupied`

## Next Steps

1. Rerun `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
2. Only if claims and live roots clear, create a TDD wrapper-prep or parent-rescore slice for this exact family.
3. Add a fixture test proving all tail samples are shifted and the candidate trade's own future payoff is not used for admission.
4. Start with parent-only versus parent-plus-Rachev comparison on one retained timeframe, then expand independently across `5m/15m/30m/1h/4h/1d`.
5. Keep futures costs as verified instrument-cost packets only; no fixed stress label is promotion authority.
6. Do not downstream unless an exact same-root retained/provider candidate has positive trade count, ETH/full-retained coverage proof, verified cost survival, density/stability gates, accepted execution feedback, and full lifecycle closure.
