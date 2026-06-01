---
name: ict-engi-fact-rese-muta
description: >
  Class-level umbrella for ict-engine factor-research, mutation scoring, parameter sweeps,
  autoresearch scripting, and structural interpretation of optimization bottlenecks.
  Use when working on factor-research experiments, mutation evaluation, scoring anatomy,
  cluster jumps, state isolation, experiment scripting, or turning reusable factor-training
  lessons into durable Hermes skills in ict-engine. Also use for profitability-factor
  transaction-cost, commission, fee-model, and cost-survival verification across stocks,
  ETFs, futures, options, crypto, perps, markets, currencies, and fee-effective dates.
  Also use when enforcing profitability-factor session scope, especially ETH/full retained
  tradable session evidence versus RTH-only comparisons.
tags:
  - ict-engine
  - factor-research
  - mutation
  - optimization
  - autoresearch
  - scripting
version: 3
---

# ict-engine factor research and mutation

## Goal
- Provide one discoverable umbrella for the factor-research / mutation-optimization class in ict-engine.
- Cover scoring anatomy, experiment design, scripting patterns, and the point where parameter tuning stops and structural work begins.
- Keep run-specific formulas, parsing bugs, and specialized notes in support references instead of splitting into many narrow skills.
- Enforce the training-loop rule: every completed factor-training run, gate-schema change, or runtime-field behavior change that produces reusable experience must update the relevant skill/reference before the lesson disappears into chat or throwaway artifacts.
- Enforce the user's profitability target as ETH/full retained tradable session
  factors. RTH-only profitability is not the requested objective and must stay a
  labeled comparison slice unless the user explicitly asks for RTH.

## Operator hard rule: ETH, not RTH
- In this skill, `ETH` means extended trading hours / full retained tradable
  session for the product, not Ethereum. `RTH` means regular trading hours.
- When the user asks for `盈利因子`, `实战因子`, `trade_usable=true`, or
  factor training without explicitly requesting RTH in the current turn, treat
  the objective as ETH/full retained session profitability. Do not reinterpret
  that request as an RTH survivor search.
- Treat this as a durable default for ict-engine profitability work, not a
  one-turn preference. RTH-only profitability cannot be reported as
  `trade_usable`, `实战`, or even `接近实战` for this target; near-practical
  status requires ETH/full-retained evidence or a clearly recorded ETH data
  blocker after an ETH-capable provider attempt.
- If the user corrects the session target with wording such as `eth而非rth`,
  `ETH盈利因子`, `full retained session factor`, or `extended trading hours
  factor`, treat it as a stop-and-repair instruction for the current and future
  ict-engine factor-training work: do not continue an RTH-only lane as if it
  were the requested profitability objective, and do not report it as practical
  progress except as a labeled comparison or blocker.
- RTH-only rows, Yahoo regular-session stock/ETF rows, or artifacts without
  retained-session coverage proof are comparison or blocker evidence only. They
  must not satisfy `promotion_allowed`, `trade_usable`, `update_goal`, live-ready
  counts, or same-tree practical closure for this user's default objective.
- A positive gate flag is invalid for this user's default objective unless the
  same terminal packet also proves `session_scope=ETH/full_retained_session` or
  an equivalent normalized value, `rth_filter_applied=false`, and retained rows
  outside the product's exchange-local RTH window. If those session fields are
  missing, contradictory, or only request-shape evidence, classify the lane as
  `session_scope_unverified` or `data_scope_blocked_for_eth_target` and keep
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
- Before answering factor counts, selecting a lane, or launching a run, require
  the workdoc, claim, terminal metrics/summary, or handoff to state
  `session_scope`, `rth_filter_applied`, and ETH/full-retained coverage evidence
  or the exact blocker.
- When both ETH and RTH evidence exist, rank and answer from the ETH verdict
  first. Show RTH only as secondary comparison, never as a substitute count for
  `trade_usable=true` or `实战因子`.

## Use when
- The user is tuning factor parameters or running `factor-research` / `factor-autoresearch`.
- You need to understand mutation scores, scoring bottlenecks, cluster-jump paths, or experiment scripting.
- You are deciding whether to keep sweeping parameters or switch to structural evidence/gate/bridge work.
- The user says `训练因子经验`, `因子训练经验`, `训练完沉淀skill`, or asks to preserve lessons from ict-engine training runs.
- The user asks to do useful interruptible work while waiting for claims,
  provider, IBKR, Auto-Quant, paper, or lifecycle runtime to clear: papers,
  strategies, indicators, source intake, or factor knowledge reserves.
- The user corrects an agent for passively waiting on fresh claims, stale-safe
  timers, or runtime ownership instead of creating useful interruptible factor
  knowledge work.
- You need to model profitability-factor friction for any traded instrument:
  futures, stocks, ETFs, options, perps, crypto, different markets, currencies,
  broker schedules, product classes, or historical fee-date assumptions.
- The user asks for `trade_usable=true`, `实战因子`, `盈利因子`, or factor
  training without naming a session: default the target to ETH/full retained
  session. Do not silently run or count RTH-only variants as success.
- The user mentions `数据清洗`, `清洗工序`, `每笔 edge`, `交易密度`,
  `成本墙`, `ETH时间数据`, `数据可证`, `网上找新因子`, or asks why a
  factor candidate was not screened before implementation.

## Class-level workflow
1. Confirm the objective, scoring surface, and session scope before any lane
   work. For this user's profitability-factor target, default to ETH/full
   retained tradable session. If the artifact is RTH-only, label it as
   comparison evidence and keep `promotion_allowed=false`,
   `trade_usable=false`, and `update_goal=false` unless the user explicitly
   requests RTH in the current task.
2. Run the mandatory data-cleaning/provenance gate before interpreting any
   signal metric: source identity, timestamp order, duplicate/null/gap checks,
   timezone/session classification, ETH/full-retained coverage evidence,
   return sanity, no-lookahead feature/target alignment, and MTF resample
   integrity. Missing proof is `data_cleaning_unverified`, not a weak pass.
3. For web-sourced or paper/repo/social candidates, prefilter before coding by
   per-trade edge, trade density, verified cost wall, and ETH time-data
   provability. Reject weak candidates into source reserve instead of spending
   provider/AQ/downstream budget on them.
4. Verify that the mutation-evaluation path is scoring the actual mutated parameters.
5. Isolate experiment state before comparing parameter candidates.
6. Inspect whether dead/null metrics are suppressing large chunks of the score.
7. Only then run broader or finer sweeps.
8. Stop parameter brute force once isolated runs re-confirm defaults or expose structural bottlenecks.

## Core principles
- Shared state can fake improvement; isolated state is the default for comparison studies.
- Dead scoring weight can dominate outcomes more than parameter choice.
- A scoring preview path that ignores mutated params invalidates the search surface.
- Once defaults remain best after fair isolated evaluation, switch to structural work instead of more sweeps.
- Reusable post-training experience is not done until it lands in a skill/reference plus router/index trigger if future automatic loading matters. If code removes, renames, or downgrades a gate/readback field, update this skill in the same work slice before reusing old gate language.

## Mandatory data cleaning and candidate prefilter
- Treat data cleaning as a hard gate before factor scoring, not as a cosmetic
  cleanup step after a result appears. Every workdoc, runner output, terminal
  metrics/summary, or handoff that claims factor evidence must record the input
  provider/path, fetch command or source archive, timestamp timezone, row count,
  duplicate/out-of-order/null checks, return-sanity checks, session coverage,
  and whether the target uses ETH/full-retained rows or an RTH comparison.
- Multi-timeframe context must use completed bars only. After resampling a
  lower timeframe into `5m/15m/30m/1h/4h/1d`, drop empty or incomplete buckets
  such as market-closed `1h` bars before HTF rolling calculations and before
  reindexing back to the low-timeframe frame. Do not forward-fill synthetic HTF
  context across missing market-closed buckets and call it clean evidence.
- Feature/target alignment must be closed-bar and no-lookahead: signals use only
  information available at or before the decision bar, and entry/label rows must
  be shifted to the next executable bar or later. If availability time is not
  proven, classify the packet as `lookahead_unverified`.
- When searching the web for new factor ideas, discard weak candidates before
  implementation unless all four prefilters are plausible and recordable:
  `per_trade_edge` above realistic all-in cost/slippage, `trade_density` inside
  the lane's cadence target without becoming churn, `cost_wall` verified from
  official broker/exchange/regulatory sources or a complete verified cache row,
  and `eth_time_data_provable` for the product/timeframe/session needed by the
  user's default ETH/full-retained objective.
- Source text, a paper abstract, a GitHub strategy, a social post, or a blog
  backtest is idea evidence only. If per-trade edge, density, cost, or ETH data
  proof is missing, mark the idea `idea_only`, `paper_only`,
  `repo_source_only`, `data_scope_blocked_for_eth_target`,
  `cost_model_unverified`, or `data_cleaning_unverified`; keep
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
- See `references/data-cleaning-and-candidate-prefilter-20260601.md`.

## Repo training scratch rule
- Factor-training scratch belongs in `/tmp/ict-engine-...`, not in the repo.
- Repo paths are allowed only after the artifact is intentionally tracked or
  force-added as a durable evidence packet, product surface, test fixture, or
  reviewed reference.
- If a lane has not reached `trade_usable=true` and has not become an explicit
  evidence packet, move/delete/externalize its scratch residue instead of
  leaving ignored or untracked files under `support/docs/`, run trees, state
  dirs, model-output dirs, or local build/cache roots.
- `done_definition_audit.py` enforces this as `repo_training_scratch_surface`;
  a failing gate is cleanup work, not something to hide behind `.gitignore`.

## Problem classes

### 1. Mutation score anatomy
Use this class when you need to understand:
- composite vs mechanical mutation score
- objective-specific weighting
- shrink/credibility bottlenecks
- null/dead metrics

### 2. Experiment scripting
Use this class when you need:
- batch runs
- parsing of factor-research JSON output
- result aggregation
- parallel cluster/autoresearch orchestration
- state isolation discipline

### 3. Plateau diagnosis
Use this class when you need to answer:
- are parameters exhausted?
- is the baseline truly best?
- should we move to evidence/gate/bridge changes?
- is a factor-family bug distorting results?

### 4. Regime-aware factor runtime
Use this class when you need to:
- extend regime states from 3 → 8 for finer granularity
- integrate HMM regime labels into FactorContext
- implement per-bar regime lookup for backtest
- enable regime-conditional factor parameter switching
- distinguish trend strength / range volatility / transition states

## Global rules
- Never trust shared-state sweep results until revalidated in isolated state dirs.
- For TrendExpansion-only profitability work, do not require the current
  materialized LTF regime label to already be `TrendExpansion` before entry.
  The prediction target is the next segment transitioning into
  `TrendExpansion`. Current closed-bar market-structure evidence must be
  modeled as first-class belief-network evidence: MSS/CISD, displacement,
  range-edge rejection or breakout acceptance, direction quality, and HTF
  range-edge context. HTF `range` is not an automatic veto; a higher-timeframe
  range top/bottom can be a prior for when lower-timeframe TrendExpansion starts.
  Other regimes remain reference/veto surfaces for execution, but their
  structure evidence can update the posterior. All entries still need
  no-lookahead proof: closed-bar evidence only, next-bar-or-later execution,
  and no promotion from local/backtest evidence alone.
- Balance throughput and quality by keeping learning/flywheel admission
  separate from final practical promotion. A lower learning regime-confidence
  floor may admit a positive-expectancy, non-leaking, evidence-backed candidate
  to collect feedback, but it must not lower `promotion_allowed`,
  `trade_usable`, or `update_goal`. Final practical/live promotion still
  requires the strict live regime floor plus same-root closure, accepted
  paper/live/broker execution feedback, verified cost, retained ETH/full-session
  coverage, and Pre-Bayes/BBN/path-ranker/execution-tree proof. A
  moderate-confidence learning candidate is `safe_to_train`, not
  `safe_to_trade`. As of the current lifecycle split,
  `paper_feedback_collection_ready` may use the explicit 12/12/12 mature row
  floor for raw-scored, production, and observation validation rows when the
  quality plane is otherwise clean. On workflow-status structural readbacks,
  this feedback-collection stage may open even before the branch is
  `ready/actionable`; those fields remain execution/live-plane evidence, not
  the feedback-flywheel gate. The full paper/live promotion floor remains
  30/30/30; below that floor, live blockers must include
  `paper_not_ready_for_live` and practical flags stay false.
- Session scope is a hard profitability gate for this user: the requested target
  is ETH / extended trading hours / full retained tradable session, not RTH.
  RTH-only runs are comparison evidence only unless the user explicitly asks for
  RTH in the current task. Do not count RTH-only survivors as `trade_usable`,
  do not use them for `promotion_allowed`, `update_goal`, or
  `same_tree_practical_closure`, and do not answer "实战因子" counts from
  RTH-only packets. Every new factor workdoc, claim, runner output, terminal
  metrics, terminal summary, and handoff must state `session_scope`,
  `rth_filter_applied`, and ETH/full-retained coverage evidence or blocker.
  Coverage evidence must prove retained tradable-session rows outside the RTH
  window, not merely omit an explicit RTH filter flag. If an artifact cannot
  prove ETH/full retained coverage, classify the lane as `session_scope_unverified`
  and keep `promotion_allowed=false`, `trade_usable=false`, and
  `update_goal=false`. For stock/ETF refetches through
  `fetch_external.py ibkr-historical`, omitting `--rth` is the intended request
  shape for all-session data, but it is only a request contract until the
  returned rows prove retained tradable-session coverage outside RTH. The
  workdoc/terminal packet should record both the omitted `--rth` argv and the
  later row-coverage evidence. For US stocks and ETFs, row coverage must use
  the exchange-local regular session window, for example NYSE/Nasdaq
  `09:30-16:00 America/New_York`; a row at `13:30Z` during daylight saving is
  the RTH open, not ETH proof.
- `transition_hazard`, `hybrid_transition_hazard`, and `pda_hybrid_alignment`
  are retired as profitability, promotion, and live-trade hard gates. Do not
  require them for `branch_local_admitted`, `extension_complete`,
  `promotion_allowed`, `trade_usable`, `update_goal`, practical admission, or
  candidate selection. If historical artifacts or execution-tree traces still
  contain them, treat them as telemetry/legacy readback only and prefer
  duration/readiness/path-ranker/lifecycle fields for current gates. If a
  wrapper, policy template, report, or workflow-status surface uses these
  fields as admission criteria, fix the source before continuing factor
  training.
- Transaction costs are a hard evidence gate, not a parameter default. For every
  cost-sensitive factor run, identify the instrument class, exact product/root,
  listed market or exchange, venue/routing assumption, currency, broker, pricing
  plan, account region, unit convention, and fee-effective date before judging
  cost survival. Do not guess fees for stocks, ETFs, futures, options, perps,
  crypto, FX, or sibling products. If any fee or economic field is unknown, the
  agent must actively search official broker/exchange/regulatory sources in the
  same turn and record the source URL/timestamp in the workdoc and terminal
  packet. If it still cannot be verified, write `cost_model_unverified`, keep
  `promotion_allowed=false` / `trade_usable=false` / `update_goal=false`, and
  stop before promotion or downstream practical admission. A cost-stressed Gate
  1 survivor is still blocked if the exact instrument cost model is unverified:
  downstream, Pre-Bayes, BBN, CatBoost, execution-tree, paper/sim, live, and
  same-tree practical closure must remain false until `promotion_cost_verified`
  is true for the product, venue/routing, account/pricing plan, currency, unit,
  and fee-effective date. Similar-looking products are not interchangeable:
  stocks may share a market schedule but differ by market/currency/year/
  minimums/taxes; ETFs can differ by product, domicile, venue, borrow/financing,
  and routing; futures vary by contract family, multiplier, tick value,
  exchange, regulatory, and clearing charges; options require option-specific
  per-contract, exchange/OCC/regulatory, exercise, and assignment schedules.
  Official-source verification is mandatory: use live web/provider/API lookup
  in the same work slice, or a local verified cache row that includes source
  URL(s), fetch timestamp, fee-effective date, broker/pricing-plan/account
  assumptions, instrument root, multiplier/tick geometry, currency, venue, and
  per-unit components. A cache row without those fields is not verification.
  Never infer, estimate, copy from a sibling script, or reuse a historical bps
  stress label as a fee. If official lookup fails or the cache is incomplete,
  fail closed and document the blocker instead of inventing a cost.
  Fixed-bps cost or stress models are forbidden as current authority. This
  applies to every value, not only `5bps`: do not use `1bps`, `2bps`, `5bps`,
  `10bps`, `cost_bps`, `fee_bps`, `bps_per_side`, `net5bps`, fixed bps
  ladders, or percent-space formulas such as `gross - trades * bps * 0.02`
  for candidate screening, Gate 1, downstream/practical admission, feedback
  labels, promotion, `trade_usable`, `update_goal`, or telemetry that can be
  confused as gate evidence. Legacy bps field names may appear only as
  readback constants for already-created artifacts and must not be emitted as
  new authority. Bps/notional is valid only when it is the verified actual
  commission model for that exact instrument/venue/date. See
  `references/instrument-cost-model-verification.md` and
  `references/futures-contract-cost-models-ibkr.md`.
  In `ict-engine` code, futures scripts must reuse the canonical shared helper
  `support/scripts/research/instrument_cost_model.py` for root normalization,
  verified IBKR futures cost profiles, per-contract USD-to-return conversion,
  and cost-model packets. Do not introduce or preserve a wrapper-local
  `FUTURES_COST_PROFILES` table, wrapper-local `FuturesCostProfile`, hardcoded
  `cost_bps`, `fee_bps`, `bps_per_side`, or `fee=0.0005` as commission,
  slippage, stress, telemetry, or gate authority. The cost authority for futures
  is the verified `survives_instrument_cost` / instrument-cost packet, with
  sample, density, session, validation, and lifecycle gates kept separate.
  When terminal metrics accept a per-run `cost_model` packet, do not treat the
  global wrapper default as promotion evidence and do not accept
  `promotion_cost_verified=true` by itself. The packet must also populate the
  exact instrument class, broker, pricing plan, venue/routing, currency, unit
  convention, fee-effective date, and required official source refs; each
  required source must have a same-turn readback proving official HTTP 200 plus
  rate verification, with no `unknown`, `unverified`, `not_rate_verified`,
  HTTP 403, or HTTP 404 residue. Only then may a Gate 1 exact-root survivor feed
  downstream Pre-Bayes/BBN/path-ranker/execution-tree evidence; even then,
  `promotion_allowed` and `trade_usable` remain false until the rest of the
  practical lifecycle evidence passes.
- Cost-survival fields must describe cost economics only. New current artifacts
  must use real instrument-cost fields such as `survives_instrument_cost`, not
  fixed-bps names such as `survives_5bps_per_side`,
  `survives_2bps_per_side`, `survives_1bps_per_side`, `net5bps`, or
  `*_bps_per_side_total_profit_pct`. Do not fold sample size, trade density,
  cadence, or validation readiness into cost-survival fields. Use separate fields
  such as `minimum_trade_sample_floor_met`, `density_target_1_to_3_per_day`,
  cadence, and validation-readiness gates, and require those fields explicitly
  in `gate1_survivor` or downstream admission. Otherwise a sparse but
  cost-positive packet becomes indistinguishable from a cost-negative packet,
  and objective closure cannot explain why a near-practical factor remains
  non-trade-usable.
- Separate flywheel learning admission from final practical/live promotion.
  Candidate-pack and lifecycle surfaces may use a lower explicit flywheel
  learning floor, for example `flywheel_regime_confidence_floor`, to admit
  positive, leakage-clean, provider-unblocked candidates into learning or
  calibration. Paper-feedback collection may also admit candidates with explicit
  real-cost/session verification debt when the quality plane is otherwise clean:
  positive expectancy after declared friction, no leakage, the explicit
  12/12/12 feedback-collection validation row floor, verified market-data
  provenance, and ready Pre-Bayes /
  execution-tree / path-ranker evidence. That does not lower the live/practical
  gate. `promotion_allowed`, `trade_usable`, `update_goal`, deploy-ready, and
  same-tree practical closure must still require the strict live regime floor
  plus accepted paper/live/broker execution feedback, verified cost,
  ETH/full-retained session, full 30/30/30 paper/live validation rows, and the
  full downstream lifecycle evidence. If code
  changes one side of this split, update both producer tests and
  candidate-pack/readback tests so feedback-collection admission cannot be
  reused as practical promotion. Consumer/readback code must not infer feedback
  collection readiness from legacy `ready=true` / `actionable=true` fields and
  must not trust a naked `paper_feedback_collection_ready=true` flag. The flag is
  valid only when the same admission object also proves
  `learning_admission_status=admitted` and `paper_admission_status=ready`;
  otherwise the consumer must report feedback collection as blocked. Structural
  branch admission may emit `paper_feedback_collection_ready=true` only after
  raw-scored mature, production validation, and observation validation rows each
  meet the explicit 12/12/12 feedback-collection floor; ranker runtime status,
  matured confirmation text, or `ready/actionable` alone is not enough.
- In futures fee-amnesty or real-cost rescue audits, legacy fixed-cost wall
  evidence may appear under `stress_5bps_total_pct` as well as
  `5bps_per_side_total_profit_pct` or `legacy_fixed_cost_total_pct`. Treat
  `stress_5bps_total_pct <= 0` as old fixed-5bps failure evidence when deciding
  whether a row was potentially fee-model-killed; otherwise rescued rows can be
  falsely downgraded to `not_rescued_no_cost_wall_evidence`.
- Product/timeframe-specific AQ wrapper files must prove their own identity
  before launch. Do not leave an XAU/NQ/GC wrapper as a thin proxy to a sibling
  product wrapper unless tests prove the exported `factor_id`, class name,
  `symbol`, `pair`, schema version, source universe, strategy source, and
  terminal packet all match the advertised product and timeframe. A wrapper file
  name, workdoc title, or old terminal packet is not enough: rerun the focused
  identity tests or add them before launching. If a wrapper identity is repaired,
  rerun the sibling tests too so the fix does not break the original product.
- Auto-Quant/Freqtrade OHLCV data files must remain strict six-column market
  data (`date/open/high/low/close/volume`). Cross-market, macro, lead-lag,
  rotation, or other sidecar features must not be written into the OHLCV
  feather/parquet consumed by Freqtrade's data handler; otherwise the loader can
  fail with a column-count mismatch before any factor verdict exists. Materialize
  such features as separate strategy-sidecar files and merge them by completed
  timestamp inside the generated strategy, with focused tests proving the market
  data file shape stays clean and the strategy still shifts entries by one
  closed bar.
- For exact-AQ futures strategies that use Freqtrade `@informative(...)`
  timeframes, verify futures OHLCV aliases for every informative timeframe
  before a `--no-fill-missing` launch. The current single-strategy wrapper
  stages futures aliases for the primary requested timeframe, but an informative
  `30m` or `1h` can still fail with `Informative dataframe ... is empty` unless
  `user_data/data/futures/<BASE>_<QUOTE>-<tf>-futures.feather` exists or is
  explicitly staged from a verified legacy source. Treat missing informative
  aliases as a data-plane blocker, not a factor economics failure; record the
  alias source path in the workdoc/terminal packet if staged.
- For `ict-engine` profitability-factor or regime work, every Board / Board A /
  Board B / Board AB / current-board / coverage-matrix / ledger style doc is
  archive/reference material only. Boards are not active state, not enabled
  workflow surfaces, not live entrypoints, not lock tables, not task queues, not
  candidate-selection sources, and not execution authority. The only valid active
  entry chain is:
  1. create or identify the repo-local handoff/plan/workdoc for the slice;
  2. create the factor-local `/tmp` workdoc under the lane run root;
  3. create or refresh the `/tmp` claim;
  4. drive the lane from same-turn command truth and run-root artifacts.
  Repo-local write surfaces are for durable, reviewed material only. Factor
  training scratch docs, temporary plans, ad-hoc runners, local screen outputs,
  Auto-Quant/Freqtrade workspaces, caches, model output, and non-promoted run
  trees belong under `/tmp`, not in the repository. A repo path is allowed only
  after it is intentionally tracked or force-added as a durable evidence packet,
  product code/test, or reviewed reference. If a lane has not reached
  `trade_usable=true` and has not become an explicit evidence packet, delete or
  externalize the residue instead of leaving ignored or untracked files in the
  repo. `done_definition_audit.py` enforces this as
  `repo_training_scratch_surface`.
  Shared docs such as `support/docs/plans/2026-05-25-board-b-current.md`,
  `2026-05-24-board-b-current.md`,
  `2026-05-23-board-b-current.md`,
  `2026-05-17-board-b-factor-refinement-small-cycle-current.md`, and
  `2026-05-20-board-b-factor-diversity-coverage-matrix.md` are 资料留档 only.
  Read them only after the new repo-local doc and factor-local `/tmp` workdoc
  exist, and only for targeted evidence lookup.
- Hard board-archive rule: never open, scan, grep, summarize, or use any Board
  doc for entry, candidate lookup, broad duplicate search, lane selection,
  active status, or execution decisions. This includes
  `support/docs/plans/2026-05-17-board-b-factor-refinement-small-cycle-current.md`
  and every other Board/current/coverage ledger. If you enter a Board file before
  creating the local repo doc and factor-local `/tmp` workdoc, stop and redirect
  to the canonical entry chain. Return to a Board ledger only when a local doc,
  `/tmp` workdoc, or exact artifact names a specific heading, factor id, run
  root, or evidence path; read only that targeted section as archived资料.
- Every Board B agent must use a stable board-local `agent_name` before doing
  Board B work and must put it in the active `/tmp` claim plus any durable
  Board B terminal/readback artifact it writes. A valid claim must state
  `agent_name`, `owner`, `claimed_at`, `last_progress_at`, `scope`,
  `active_task`, `non_goals`, `write_surface`, `run_root` or `tmp_root`,
  `status`, and `progress_report` or `latest_report`. Vague work such as
  "continue", "audit", "help", "repair", or "readback" is not valid unless it
  names the exact factor/root/artifact/gate/write surface. If a lane is already
  claimed, active, done, or blocked, do not continue, repair, rerun, summarize,
  or help that lane while the owning work is still live; choose a genuinely
  different ownership axis or stop with a compact duplicate/blocker note. A
  stale active claim may be taken over when no matching live process is visible
  for the lane (`run_ibkr_*`, `fetch_external.py`, Auto-Quant/freqtrade, TOMAC
  scan/postscan, IBKR `provider-status`, or another command writing under the
  claimed root) and `last_progress_at` is more than one hour old, or no
  timestamp/report exists and no lane process is running. The takeover must
  append a timestamped report to the original claim with `takeover_agent_name`,
  `takeover_reason`, `takeover_run_root`, `last_progress_at`, `latest_report`,
  `decision`, and false `promotion_allowed`/`trade_usable`/`update_goal` unless
  the full live-usability gate actually passes.
- For Board B factor work, create one factor-local work document under the
  factor's `/tmp` run root before substantive work, for example
  `/tmp/ict-engine-.../workdoc.md`. The claim should stay a small ownership and
  state pointer, and its `write_surface` must name the workdoc path. The workdoc
  should carry creation time, owner, factor id, exact rooted branch, non-goals,
  data/provider provenance, session scope (`ETH/full_retained_session` vs a
  clearly labeled `RTH_comparison`), run root, launch command, evidence paths,
  terminal metrics, terminal decision, and next gate. Do not use the compact board as a
  scratchpad, and do not keep appending unrelated factor detail into one swollen
  factor file. One factor gets one workdoc so creation time and ownership are
  visible, board fake-work is avoided, and later agents can decide whether a
  lane is active, stale, terminalized, or safe to take over from that packet.
- `live_factor_processes` is a process-collision signal, not a documentation
  model. Board B agents should still be forced to create separate factor docs,
  `/tmp` workdocs, and claims for their own exact branches. Runtime occupancy
  only means provider/Auto-Quant children are already writing under some other
  run root, so a new launch on a different branch would collide on shared
  backend/runtime resources. Never "solve" occupancy by reusing one board doc;
  solve it by keeping per-factor docs separate and deferring launch until the
  foreign live process roots clear.
- When the user wants a new profitability factor document plus skill sync and
  the shared provider / Auto-Quant backend is still occupied by other live
  owners, stage the exact branch instead of colliding. Create the authoritative
  `/tmp` factor workdoc first, add a repo reference packet under
  `support/docs/experiments/actionable-regime-confidence/runs/...` when the
  user asked for durable lookup, create the valid `/tmp` claim pointing at that
  workdoc, and prepare the exact runner / launch command for the same rooted
  branch. Mark the lane prep-only until live provider/AQ owners clear, and sync
  only the reusable workflow lesson into this skill or its reference. If the
  factor workdoc has not been updated for more than one hour and no matching
  live lane process is writing under that run root, takeover is allowed with a
  timestamped claim update and the same rooted branch path.
- Use `support/scripts/factor_claim_terminalization_audit.py --compact` before
  choosing a profitability-factor lane. The audit's `/tmp` claims and live
  process roots are the collision source of truth; Board docs are not. It treats
  live factor processes, active claims, and invalid active claims as
  `needs_attention`. An active claim is invalid when it lacks `agent_name`,
  `owner`, `scope`, `active_task`, `non_goals`, `write_surface`, `status`, or
  either `run_root` or `tmp_root`; repair, externalize, or avoid those lanes
  instead of treating vague claims as free.
  The audit also attributes live provider child processes to repo experiment
  run roots when their `--output` path is under
  `support/docs/experiments/actionable-regime-confidence/runs/<run-id>/...`;
  use that run-root signal to avoid active artifact roots even when a parent
  wrapper command has no static run root.
- Board B claim-audit hygiene is part of the collision guard. Generated
  sidecars such as `*.summary.json`, `*.summary.json.check`,
  `*.claim.pretty`, `*.json.pretty`, and `*.exit` are not standalone claims and
  should not inflate active-claim counts. The compact audit summary separates
  `valid_active_claims` from `invalid_active_claims`; use that split to
  distinguish real occupied lanes from stale/under-specified claim debt. When a
  live provider or Auto-Quant child writes under `/tmp/ict-engine-*` subdirs
  such as `scripts`, `state`, `checks`, or `summaries`, attribute the live root
  to the parent artifact directory so backend occupancy is grouped by the lane
  root instead of by wrapper/state subdirectory.
- JSON claim payloads must be parsed by content, not by suffix. A terminal
  readback stored as a JSON object in a `.claim` file is still JSON and should
  normalize keys such as `agent-name`/`agent_name`, boolean
  `promotion_allowed`, and `trade_usable` before deciding whether it is active
  or terminalized. If compact audit active/invalid counts suddenly inflate,
  first check for JSON payloads in `.claim` files before treating them as real
  ownership collisions.
- Claim-audit terminal artifact discovery must inspect wrapper-nested terminal
  outputs as well as top-level run-root summaries. A guarded wrapper can write
  `summaries/terminal_no_launch_summary.json`,
  `aq/summaries/terminal_no_launch_summary.json`,
  `aq/summaries/terminal_summary.json`, `aq/checks/terminal_metrics.json`,
  `run/summaries/terminal_summary.json`, or `run/checks/terminal_metrics.json`
  under the claimed root; if that nested summary reports a terminal no-verdict
  decision such as `launch_blocked_by_foreign_claim_or_runtime`, a terminal
  no-verdict status such as `launch_blocked_by_collision_guard`, or a
  fail-closed practical lifecycle status such as
  `practical_lifecycle_fail_closed`, classify the active claim as
  terminalized/no-promotion evidence, preserve the summary path and decision in
  compact readback, and keep `promotion_allowed=false` / `trade_usable=false`.
  Do not let such stale active claims keep blocking closure or become promotion
- IBKR provider readiness is not accepted execution feedback. The repo-local
  `support/scripts/ibkr_bridge` is a read-only market-data / Redis bridge; it
  connects with `readonly=True` and is not an order/fill producer. A same-turn
  read-only `reqExecutions(ExecutionFilter())` query against a reachable paper
  gateway can audit whether broker/paper fills already exist, but `fills=0` or
  rows without `broker_realized=true`, `broker_fill_evidence=true`, and an
  accepted source marker such as `paper_execution_feedback` remain
  `accepted_execution_feedback_missing`. Do not relabel exact-AQ/Freqtrade
  backtest rows, retained-label simulations, IBKR historical rows, or Redis
  market-data bars as paper/live/broker execution feedback.
  evidence.
- Claim-audit terminal artifact discovery must also resolve wrapper-stamped repo
  run roots for claims whose `repo_run_root` is still a pending sentinel such as
  `pending_wrapper_launch_stamp`. If a later repo run root under
  `support/docs/experiments/actionable-regime-confidence/runs/<run-id>/...`
  has terminal metrics with the same `factor_id` or normalized `branch_path`,
  classify the claim from that terminal packet and preserve the repo-relative
  evidence path. This is terminalization/occupancy hygiene only: a sparse Gate 1
  survivor that still has `promotion_allowed=false` and `trade_usable=false`
  remains non-practical until same-tree practical lifecycle evidence passes.
- Claim-audit terminal artifact discovery must also inspect the claim's own
  `write_surface` workdoc when that file is the run-root `workdoc.md` or lives
  under the claimed run root. A workdoc terminal readback with a terminal
  decision/status and explicit `promotion_allowed=false` / `trade_usable=false`
  is terminal evidence and should not keep a stale `.claim` status active in
  compact closure readbacks. Do not read arbitrary external workdoc paths as
  terminal authority; keep discovery scoped to the claimed run root.
- Workdoc terminal parsing must not treat every markdown `Decision:` key as a
  terminal decision. Planning sections such as `TDD Route`, route choice,
  diagnostics, or next-gate notes can legitimately contain `Decision: skipped`,
  `Decision: strict`, or similar non-terminal words while the lane is still
  active. Only `terminal_*` fields, a terminal/final readback section, or an
  explicitly terminal decision/status such as `terminalized_*`, `drop_*`,
  `reject_*`, `fail_closed`, `launch_blocked_*`, or `readback_complete` may
  terminalize the claim from the workdoc.
- The objective-closure `same_tree_practical_closure` packet is a structured
  proof packet, not raw claim metadata. `factor_claim_terminalization_audit.py`
  may surface it only when exactly one terminalized claim run root contains a
  valid `same_tree_practical_closure.json` under `summaries/`, `checks/`, or the
  run-root top level. The packet must have `status=pass`, explicit
  `promotion_allowed=true`, `trade_usable=true`, `deploy_ready=true`,
  `funded_live_fill_required=false`,
  `readiness_contract=deploy_ready_from_backtest_autoquant_provider_or_paper_sim_execution_chain_not_funded_fill`,
  `provider_execution_feedback_chain=pass`, and an `evidence_packet` file that
  exists inside the same run root and whose JSON content proves the practical
  chain: true practical flags, distinct command result rows with explicit
  `stage` values `provider_data`, `pre_bayes`, `bbn_workflow`, `path_ranker`,
  `execution_tree`, `feedback_update`, and `policy_training`; each row must
  have `exit == 0` and explicit `timed_out=false`. Command names are readback
  labels only and must not be used to infer stage coverage. The packet must
  also prove branch survival, actionable candidate, branch-local
  admission, validation readiness, path-ranker use by the execution tree,
  non-observe candidate status, policy-training summary, and
  raw/production/observation validation counters meeting their required ratios.
  After this content check passes, the factor audit must surface
  `evidence_packet_validated=true`; objective snapshots and completion summaries
  must require that flag instead of re-accepting marker-only packet fields.
  The legacy alias `evidence_validated=true` is not a valid substitute for
  `evidence_packet_validated=true`; Rust workflow/analyze validators must fail
  closed when only the legacy alias is present.
  The evidence packet must also prove the full profitability lifecycle tuple:
  `learning_admission_status=admitted`, `paper_admission_status=ready`,
  `deploy_ready=true`, `live_trade_status=ready`,
  `funded_live_fill_required=false`, and the same readiness contract. Here
  `deploy_ready` means readiness from backtest/Auto-Quant/provider or paper/sim
  execution-chain evidence; it does not require funded real-money fills.
  Execution-tree readiness or a loose nonempty `policy_training_summary` is not
  enough for practical closure when learning or paper admission is absent/not
  evaluated. The `policy_training_summary` itself must prove the same lifecycle,
  either directly or under `factor_profitability_lifecycle`, with positive
  `learning_admitted_count`, `paper_ready_count`, `deploy_ready_count`,
  `live_ready_count`, `live_trade_usable_count`, true practical flags,
  `funded_live_fill_required=false`, and the same readiness contract. When
  the policy lifecycle itself exposes status fields such as
  `learning_admission_status`, `paper_admission_status`, `deploy_ready`, or
  `live_trade_status`, those fields must agree with the required top-level
  lifecycle tuple; positive counts cannot mask an explicit `not_evaluated`,
  false deploy-ready, or non-ready lifecycle status. Market data provenance is
  also part of the closure
  evidence: require `market_data_provenance.status=pass`, an allowed source
  class such as roll-adjusted clean feather, verified provider historical data,
  or paper/live broker feedback, and clean `return_sanity`; raw contract/CSV
  stitching or extreme-return sanity failures are not practical closure proof.
  The same canonical metrics packet must also prove ETH/full retained session
  scope and verified promotion costs: `session_scope` must normalize to
  ETH/full retained session, `rth_filter_applied=false`,
  `retained_session_coverage.status=pass` with `has_non_rth_rows=true`,
  a positive non-RTH/outside-RTH row count, the exchange-local RTH window,
  the window timezone, and a structured evidence reference or object. A
  prose-only string such as "verified retained tradable-session rows outside
  RTH" is not evidence. The packet also needs `promotion_cost_verified=true`
  with a complete `cost_model`. Cost source refs must be structured readbacks
  proving official-source HTTP 200 plus `rate_verified`; a bare URL string or a
  source marked unknown, unverified, not rate verified, HTTP 403, or HTTP 404 is
  not same-tree practical closure evidence.
- Same-tree practical closure must also prove a positive accepted execution
  feedback source. Accepted source markers are `paper_execution_feedback`,
  `live_execution_feedback`, `paper_trade_feedback`, `live_trade_feedback`, or
  `broker_execution_feedback`, and they must appear in the metrics evidence
  chain such as `feedback_source`, `trade_feedback_source`, `trade_summary`, or
  `runtime_trade_feedback_summary`. These markers must be exact delimiter-bound
  tokens, not naive substrings: values such as
  `not_paper_execution_feedback` or `paper_execution_feedback_missing` are
  fail-closed. Negated machine-label forms must also fail closed when a nearby
  prefix token such as `not`, `no`, `non`, `without`, `missing`, `absent`,
  `fake`, or `spoofed` appears before the accepted marker; examples include
  `not-paper_execution_feedback` and
  `without-broker-paper_execution_feedback`. The absence of simulated markers is not enough. Sources
  containing `simulated_backtest`,
  `retained_real_event_label_simulation`, `paper_trade_simulation`,
  `simulation_child_gate`, `child_gate_filtered`, or `simulated_feedback` are
  fail-closed for practical closure even if all downstream commands exit zero,
  CatBoost/path-ranker rows mature, or policy rows otherwise read `pass`.
  Structural feedback aggregates may count as `live_trade_usable` only when all
  aggregate records come from an accepted paper/live/broker execution-feedback
  source, have mature successful labels and positive training weight, and the
  aggregate PnL is positive. Do not relabel retained-label materialization or
  simulated backtest rows into paper/live/broker feedback to satisfy this gate.
- Same-tree practical closure packet production has one canonical owner:
  `support/scripts/research/same_tree_practical_closure.py`. Experiment wrappers
  must call `build_same_tree_practical_closure_packet(...)` or
  `write_same_tree_practical_closure_packet(...)`; they must not hand-write
  `schema_version="same-tree-practical-closure/v1"`, call `write_text` on a
  `same_tree_practical_closure` path, or spoof a local builder with the same
  name. The factor audit validator and packet producer must share the helper's
  `metrics_prove_same_tree_practical_closure(...)` semantics so producer and
  consumer gates cannot drift. Local branch readiness can be true while
  `promotion_allowed=false` / `trade_usable=false` until that canonical helper
  emits a pass packet from full lifecycle evidence.
- Practical-lifecycle continuation wrappers must not synthesize a one-row
  command result such as `practical_lifecycle_readback` and then report
  `all_command_exits_zero=true`. If the wrapper summarizes an upstream Gate 1 /
  downstream / policy chain, it must inherit or produce the explicit staged
  `command_results` rows required by the canonical helper. If those staged rows
  are absent, pass an empty command list or otherwise fail closed so the metrics
  show `all_command_exits_zero=false`, no same-tree closure packet is written,
  and the CLI exits nonzero even if local lifecycle flags happen to say
  `promotion_allowed=true` or `trade_usable=true`.
- Practical admission wrappers must not manufacture `extension_complete` from
  local wrapper state. In downstream source, `practical_admission_flags(...)`
  may omit `extension_complete` or pass explicit `False`; positive or locally
  computed arguments such as `extension_complete=True` or
  `extension_complete=bool(metrics.get("extension_complete"))` must fail the
  static gate until they are replaced by a validated same-tree practical-closure
  source. Treat `extension_complete` as lifecycle proof, not a convenience flag.
  Retired PDA/transition fields such as `pda_hybrid_alignment`,
  `pda_hybrid_alignment_true`, `transition_hazard_lt`, and
  `*_transition_hazard_lt` must also fail when used as practical gate templates;
  only explicit false telemetry markers such as `pda_required=False` and
  `transition_hazard_required=False` are observation-only and allowed.
  explicit true `promotion_allowed` / `trade_usable`; otherwise a packet that
  says live-ready at top level can still mask `live_ready_count=0` and must fail
  closed.
  The evidence packet must also prove market-data provenance and return sanity:
  `market_data_provenance.status=pass`, an explicitly allowed source class such
  as verified provider historical data, roll-adjusted clean feather, or
  paper/live broker execution feedback, and `return_sanity.status=pass` with no
  parse-bad rows, no `extreme_abs_gross_gt_10pct_count`, and no
  `max_abs_gross_return_pct > 10.0`. Raw contract stitching, raw local CSV
  stitching, raw Databento contract stitching, and raw TOMAC CSV evidence are
  not practical-closure proof even when other closure booleans are true.
  Multiple packets, external evidence paths, missing evidence files,
  marker-only evidence JSON, or non-pass fields must fail closed as no validated
  practical closure. Keep raw `promotion_allowed_true` / `trade_usable_true`
  claim counters as hygiene blockers, not objective-completion proof.
- Claim-audit boolean parsing must prefer explicit claim fields over prose.
  Negated `non_goals` text such as `no promotion_allowed=true` or
  `no trade_usable=true` is not positive gate evidence when later explicit
  fields say `promotion_allowed=false` / `trade_usable=false`.
- Prep/launch wrappers that emit packet metadata must resolve the active claim
  from the current `run_root` / `tmp_root`, not from a stale historical claim
  constant. If a fresh prep packet under a new `/tmp/ict-engine-*` root still
  points its `claim` field at an older lane, treat that as a packet-integrity
  bug, add a regression test on the prep surface, and regenerate the packet
  before relying on it for takeover or launch decisions.
- Custom local TOMAC scanners/postscans named like `tomac_*_scan.py` or
  `tomac_*_postscan.py` count as live factor processes even when they are
  launched from `/tmp` rather than a repo wrapper. Attribute their `--out` path
  to the enclosing `/tmp/ict-engine-*` lane root, and block fresh provider/AQ
  work until the scanner exits or its owning claim terminalizes. Do not dismiss
  those commands as readback probes merely because they are not named
  `run_tomac.py`.
- TOMAC launch wrappers named like `run_tomac_*_autoquant_loop_v*.py` or other
  launch-capable `run_tomac_*.py` scripts count as live factor processes even
  before a child `run_tomac.py` appears and even when their root is supplied by
  environment variables rather than `--root`. The compact claim audit must fail
  closed during that staging window; otherwise a second agent can see
  `live_factor_processes=0` and create duplicate NR7/Donchian/Chandelier
  launch claims while the first wrapper is already staging data or AQ work.
- Generic Python scripts running from a Board B `/tmp/ict-engine-*` lane root
  also count as live factor processes. This includes Python-only prescreens such
  as `/tmp/ict-engine-.../scripts/run_*_pybacktest.py`, even when the script is
  not named `run_tomac`, `run_ibkr_*`, or `fetch_external.py`. The live-process
  classifier should still ignore help/unittest/search/readback commands and
  TOMAC diagnostic probes, but once a generic `.py` command exposes a Board B
  run root, treat it as live runtime occupancy and block sibling launches until
  the owning claim terminalizes.
- Board B launch acquisition is not safe when it is only `audit pass -> create
  claim -> launch` in separate shell turns. Two agents can both observe
  `active_claims=0` / `live_factor_processes=0` and then start the same clean-AQ
  branch under different run roots. Launch-capable TOMAC prep wrappers should
  run a final in-process full claim audit immediately before spawning the AQ
  child, allow only their own exact run-root/parent-root claim, and block with a
  no-verdict terminal summary when any foreign active claim or live runtime root
  exists. Use full audit JSON for this guard because compact attention claims do
  not carry enough run-root detail to distinguish own-root from foreign claims.
- For retained-data clean-AQ wrappers, the same claim-collision guard must also
  run before expensive cleaning or strategy staging when an AQ launch is enabled.
  A fresh foreign active claim, invalid non-coordination claim, or foreign live
  runtime is a no-clean/no-stage/no-launch condition: return a fail-closed
  summary with `clean_bundles=[]`, `aq_staging=[]`, `aq_commands=[]`,
  `promotion_allowed=false`, and `trade_usable=false`. Keeping the guard only
  immediately before `run_tomac.py` is too late because long cleaning/staging can
  consume shared disk/runtime while another lane owns the board.
- For TOMAC futures ZIP source archives, "cleaned" requires
  `source_archive_validation.status=pass_zip_pristine_source` before any clean
  bundle, exact-AQ prep, regime-feedback packet, or downstream handoff can be
  trusted. The extracted source directory must match the ZIP payload exactly:
  no symlinked OHLCV file, no older same-symbol CSV, no shifted fallback CSV,
  no generated higher-timeframe CSV mixed into the raw source directory, no
  missing ZIP member, and no source-size mismatch. If any of those appear, the
  correct action is to delete/re-extract the polluted source directory from ZIP,
  regenerate the cleaned MTF root, invalidate affected prior "cleaned" evidence,
  and keep `promotion_allowed=false`, `trade_usable=false`, and
  `update_goal=false` until the factor is rerun on the ZIP-pristine clean root.
- Full-audit launch guards must keep their raw `claims` fallback semantically
  aligned with compact audit attention rules. Raw full JSON includes
  coordination-only active claims that compact output intentionally excludes
  from launch blockers; do not re-inflate those into `active_claims` merely
  because `status=active` or `missing_identity_fields` is present on a
  `coordination_only` claim. A wrapper may ignore only its own current wrapper
  PID or its own exact run-root claim. If removing those self entries leaves no
  foreign active claims, invalid claims, live factor processes, promotion/trade
  usable flags, or blocking reasons, audit exit `1` from the self-only raw
  blocker is non-blocking. Missing/malformed audit output, unexplained nonzero
  audit exits, foreign claims, invalid non-coordination claims, and foreign live
  processes still block fail-closed.
- Launch wrappers that run a final full-audit collision guard from inside the
  wrapper must explicitly pass and exclude the current wrapper PID when raw live
  process rows have no `run_root`. Otherwise the wrapper can classify its own
  parent process as an unrooted `foreign_live_root` and no-launch itself before
  AQ starts. This self-PID exclusion must be exact-PID only; never broaden it to
  script-name or family-level ignores, and still block every foreign claim,
  foreign run root, invalid non-coordination claim, or separate live process.
  Add a focused regression test for this path before relying on the wrapper in
  a crowded Board B window.
- For exact IBKR/AQ wrappers that shell out to `fetch_external.py`, timeout
  cleanup must kill the whole process group, not only return `124` to the
  parent helper. If a timed-out wrapper leaves child `ibkr-historical` fetches
  alive, those lingering children will pollute compact-audit occupancy, force
  manual cleanup, and can make the same rooted branch look falsely active or
  duplicate-blocked in later Board B turns.
- For TOMAC prep/launch wrappers that spawn a clean-AQ child in the same Python
  dependency domain, do not hardcode child commands to plain `python3` when the
  parent interpreter was deliberately chosen for optional dependencies such as
  `pyarrow`. Use the current interpreter for child helper commands, or expose an
  explicit interpreter override, and cover this with a focused unit test. A
  parent Python with `pyarrow` can otherwise launch a child `python3` that
  resolves to another installation and fails at `DataFrame.to_feather()` before
  any factor economics are measured.
- Generated exact-AQ strategy sources that call `pd.merge_asof` must normalize
  both join keys to the same dtype before runtime launch. Local Mansfield
  exact-AQ evidence showed Freqtrade data can arrive as `datetime64[us, UTC]`
  while CSV sidecars parse as `datetime64[ns, UTC]`, causing a runtime
  `MergeError` even when both columns are timezone-aware UTC. Prefer a small
  generated helper such as `_utc_ns(...)` that casts to
  `datetime64[ns, UTC]` and merges on integer nanosecond keys, and cover the
  generated source contract with a focused test before launching.
- `support/scripts/auto_quant_external/run_tomac_one.py` owns the single-strategy
  Freqtrade/AQ trade-export contract. Do not rely on Freqtrade's Python API
  honoring `exportfilename`; current local evidence showed Freqtrade still wrote
  default `user_data/backtest_results/backtest-result-*.zip` files while the
  requested `/tmp/.../checks/aq_trades_*.json` paths stayed missing. After
  `Backtesting.start()`, `run_tomac_one.py` must explicitly serialize
  `bt.results` to the caller-provided export path, and focused tests must assert
  that the file exists and contains `strategy -> <StrategyName> -> trades`.
  Backfilled AQ trade exports remain simulated backtest evidence only; they do
  not satisfy accepted paper/live/broker execution feedback.
- `run_tomac_one.py --no-fill-missing` must cover both the main Freqtrade
  `history.load_data` path and informative timeframe loads through
  `freqtrade.data.dataprovider.load_pair_history`. Freqtrade imports
  `load_pair_history` by value inside the DataProvider module, so patching only
  `freqtrade.data.history.load_data` can leave `@informative("30m")` /
  `@informative("1h")` calendar fillup warnings unresolved. Add or keep focused
  tests for the informative DataProvider path before trusting no-fill exact-AQ
  parity. A cleared fillup blocker is still exact-AQ backtest candidate evidence
  only; it does not satisfy paper/live/broker execution feedback or practical
  promotion.
- Exact Board B wrapper scripts that can launch provider/AQ work must expose a
  lightweight CLI help guard before `main()` runs. A direct `python ... --help`
  must print usage and exit `0` without creating a run root, invoking
  `provider-status`, or spawning `fetch_external.py` / Auto-Quant children.
  If a wrapper lacks argparse but is commonly inspected with `--help`, add a
  small `run_cli(argv=None)` gate and cover it with a focused unit test so
  operators can inspect the wrapper safely during crowded Board B windows.
- Bounded IBKR backend probes such as
  `cargo run --quiet -- provider-status --provider ibkr --agent` count as live
  Board B backend occupancy for lane selection. The compact claim audit should
  report them as live factor/backend processes unless they only appear inside a
  readback/search command such as `ps | rg`; do not launch fresh IBKR,
  provider, or Auto-Quant lanes while those probes are active.
- Direct `ict-engine` feedback-ingest commands such as
  `auto-quant-ingest-real-trades --state-dir /tmp/ict-engine-.../state` count
  as live Board B runtime occupancy when they write under a factor run root.
- Practical-admission source checks must treat transition-hazard hard gates as
  branch-local-only blockers, not promotion proof, even when the hazard test is
  hidden behind an intermediate boolean. Patterns such as
  `hazard_ok = transition_hazard < 0.60` followed by
  `pass_exec = branch_ok and hazard_ok` must taint `branch_local_admitted` /
  `pass_exec`; do not let that branch-local signal set `promotion_allowed`,
  `trade_usable`, or `update_goal`. A wrapper may omit `extension_complete` or
  pass explicit `False` into `practical_admission_flags(...)`; it must not
  hardcode or locally read back positive `extension_complete` as a shortcut for
  same-tree practical closure.
- Blocker reports that build a `factor_profitability_lifecycle` must not copy
  nested `live_trade.promotion_allowed` / `live_trade.trade_usable` back into
  top-level practical flags. Recompute top-level `promotion_allowed`,
  `trade_usable`, and `update_goal` through the local
  `practical_admission_flags(...)` contract, or keep them explicit false, so the
  source checker can prove `extension_complete` still gates practical use.
  Human/markdown report output must show lifecycle status,
  `extension_complete`, `promotion_allowed`, and `trade_usable` whenever the
  JSON report can classify a candidate as meeting current gate shape; otherwise
  branch-local readiness can hide an extension-incomplete, non-trade-usable
  state.
  The compact claim audit must include them as live processes; otherwise a
  terminalized claim can mask a still-running state writer and allow a
  colliding sibling launch.
- Practical-admission source checking should distinguish practical writers from
  passive/readback surfaces. Claim/report/lifecycle payload readbacks,
  serialized claim bool extraction, explicit local `False` aliases, and
  diagnostic `allowed_targets` maps may be safe source shapes when they do not
  write practical-use authority; reassigned aliases and practical dictionaries
  still require the local `practical_admission_flags(...)` contract. The
  done-definition practical source scan must include tracked helper/report files
  that can emit lifecycle or blocker readbacks, not only `run_*.py` wrappers,
  but it should not scan test fixtures as runtime source. Recovered regime
  assets and other scope-limited evidence must remain `promotion_allowed=false`
  and `trade_usable=false` until a downstream live-admission surface proves the
  full practical tuple.
- A fresh claim, unexpired stale-safe timer, or foreign live runtime is a
  no-launch condition, not a wait condition. Never idle, sleep, or poll for a
  one-hour takeover window or for another agent's claim to clear. Immediately
  create or continue a separate, interruptible, low-collision source-intake or
  knowledge-reserve packet: papers, strategies, indicators, exchange/broker
  docs, public repo ideas, and local duplicate/negative evidence. Convert only
  codeable findings into regime-rooted candidate packets, and keep every packet
  `promotion_allowed=false` / `trade_usable=false`. Never launch
  provider/AQ/Freqtrade/IBKR/paper/lifecycle commands, clone/install external
  repos, or write practical closure while blocked by someone else's runtime or
  claim. See `references/waiting-window-factor-research.md` and
  `references/2026-05-30-paper-strategy-reserve.md`; for lower-turnover
  cross-asset/carry/VRP filters, see
  `references/2026-05-30-crossasset-carry-risk-reserve.md`.
- Low-collision source/cost reserve, source/cost prep no-launch, and
  knowledge-reserve claims are coordination work, not runtime ownership, only
  when they explicitly keep `promotion_allowed=false`, `trade_usable=false`,
  and say no provider, IBKR historical, AutoQuant, Freqtrade/TOMAC,
  paper/sim/live, downstream lifecycle, or local backtest launch.
  `factor_claim_terminalization_audit.py` should classify those as
  coordination-only so the waiting-window workflow does not create loops such as
  `runtime blocked -> reserve/prep packet -> reserve/prep packet blocks
  runtime`. Any source/cost packet missing the false practical flags or
  no-launch language remains a real active claim and must be repaired or
  terminalized before launch.
- Wrapper/training prep no-launch claims follow the same coordination-only
  principle when they explicitly set `promotion_allowed=false` and
  `trade_usable=false`, say no provider fetch, no IBKR historical, no
  AutoQuant/Freqtrade/TOMAC launch, no paper/sim/live, no downstream lifecycle
  launch, and no local backtest launch. Use one of the audit-recognized status
  prefixes such as `active_training_prep_no_launch`,
  `active_wrapper_prep_no_launch`, `active_source_prep_no_launch`, or
  `active_source_cost_prep_no_launch`, and include purpose text such as
  `training prep`, `wrapper prep`, `source prep`, or `prep packet`. A bare JSON
  field such as `coordination_only=true` is not enough; the compact audit derives
  coordination-only status from the claim `status` and no-launch purpose text.
  or Pre-Bayes/BBN/CatBoost/execution-tree, and no local backtest launch. These
  claims may preserve a tested wrapper, factor-local workdoc, repo tracking doc,
  and launch-ready command while another lane owns runtime, but they must not
  block the next collision-free runtime window. Any wrapper/training prep claim
  missing the false practical flags or no-launch language remains a real active
  claim.
- Retired transition/PDA telemetry must not re-enter practical admission through
  templates, intake profiles, execution-candidate readbacks, or blocker reports.
  As of 2026-05-29, `transition_hazard`, `hybrid_transition_hazard`, and
  `pda_hybrid_alignment` may remain observation/debug telemetry in specialized
  diagnostics, but source templates such as `transition_hazard_lt`,
  `*_transition_hazard_lt`, `transition_hazard_required=true`,
  `pda_hybrid_alignment=true`, or `pda_required=true` are practical-gate debt.
  The same rule applies when these fields are copied into execution-candidate or
  lifecycle readbacks in a way that suggests they are blockers or promotion
  evidence. Keep them out of practical surfaces unless current source explicitly
  reintroduces them as active typed gates with tests and skill/router updates.
- Context hygiene: do not copy retired field names into new factor workdocs,
  claims, handoffs, or lane plans just to say they are not gates. Use generic
  wording such as "retired regime-transition telemetry is excluded from the
  gate policy". Keep the explicit retired field names only in source-check,
  scanner, or migration-governance text that must catch stale templates.
- For TOMAC `SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian`
  same-root continuations, preserve wrapper lineage explicitly. Child factors
  such as density repair or cadence/session-cluster repair should derive from
  the TOD-contrarian prep-wrapper family
  (`run_tomac_tod_contrarian_*_prep_v1.py`) rather than from
  `PortfolioAdaptiveSlotContrarian` wrappers. If no existing wrapper targets
  the exact child factor id, stage the packet as prep-only, record the nearest
  reusable wrapper/readback in the workdoc, and wait for foreign live
  factor/AQ owners to clear before creating the exact child wrapper or launch.
- IBKR simulated-trade admission is not a free promotion path. A same-root run
  may ingest simulated trades, train/apply/register the ranker, enable runtime,
  and still fail closed. When a simulated-admission packet reports
  `all_command_exits_zero=true` but `exact_branch_survived=false`,
  `execution_candidate_actionable=false`, or
  `practical_admission=branch_local_only_extension_incomplete`, classify it as
  terminal evidence only. Preserve the simulated-trade rows, ranker artifacts,
  and execution-blocked readback for downstream evidence, but keep
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
- TOMAC sidecar label JSONL is not automatically the
  `auto-quant-ingest-real-trades` wire schema. If a same-root validation repair
  converts sidecar/backtest labels into real-trade wire rows, label the source as
  simulated/backtest feedback, run a dry-run first, and keep the output in the
  lane run root. A successful converted-feedback ingest can make observation
  validation ready, but it does not by itself satisfy production target
  validation or practical readiness. If policy readback still shows
  `raw_scored_mature < 30`, `production_validation < 30`,
  `closed_loop_branch_admission.status=fail_closed`, `review_status=discard`,
  or `execution_gate_status=observe`, terminalize fail-closed with
  `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` even
  when `feedback_rows_with_structural_feedback` is large and ranker runtime is
  enabled.
- TOMAC TOD Balanced policy-label repairs must preserve the simulated-vs-real
  feedback boundary. A validation materialization packet can apply all converted
  sidecar rows and still not create production policy rows: if `update_runs` are
  large but `consumed_analyze_run_id=null`, standard entry-model training should
  report `matched_rows=0` / `updates_missing_consumed_analyze_run_id`, and if
  `learning_state.feedback_history.source` is
  `auto_quant_simulated_feedback:*`, `auto_quant_real_trade_feedback` policy
  rows must remain `0` because current source only consumes
  `auto_quant_real_trades*` or `structural_feedback_submission`. Do not patch
  around this by reclassifying simulated sidecar labels as real production
  evidence or backfilling analyze ids unless the source provenance is genuinely
  production/real feedback. Observation validation such as `1633/30` can support
  learning evidence, but live/paper usability still requires production/raw
  ranker validation, consumed ranker rows, and non-observe execution.
- Split training/paper admission from live-trade usability. A real-feedback
  candidate with mature labels, positive training weight, ranker runtime ready,
  production/observation validation ready, and `execution_gate_status=pass` can
  be counted as `learning_admitted` and `paper_ready` so the training loop can
  optimize from real feedback. That does not make it live practical:
  `promotion_allowed`, `trade_usable`, and `update_goal` must remain false until
  the current workflow readback also shows the live plane ready, including
  Pre-Bayes pass, execution-tree live readiness, and the complete live tuple.
  `execution_gate_status=observe` may count as learning evidence with mature
  training rows, but it must not count as paper-ready.
- Do not interpret `live_trade_status=ready` as requiring funded real-money
  losses or live capital deployment before a factor can be judged practical.
  `paper_admission_status=ready` means the no-capital paper/sim execution loop
  is evidenced and ready; `live_trade_status=ready` means the same rooted branch
  is ready to be switched to live execution based on backtest/Auto-Quant
  reproduction, verified costs, provider or paper/sim execution semantics,
  risk controls, non-observe execution-tree admission, and policy lifecycle
  evidence. Funded live fills can strengthen evidence, but they are not a
  prerequisite for `trade_usable=true`. Conversely, Python-only or backtest-only
  profitability is still insufficient for live readiness.
- Execution-tree readiness is not practical/live usability. A branch can have
  Pre-Bayes pass, execution readiness above floor, ranker validation ready, and
  `ready/actionable=true`; that is execution-plane evidence only. Do not emit or
  trust `promotion_allowed=true`, `trade_usable=true`, or `update_goal=true`
  from execution-tree traces or `workflow-status` unless the complete lifecycle
  tuple is present in the same readback: `learning_admission_status=admitted`,
  `paper_admission_status=ready`, `deploy_ready=true`,
  `live_trade_status=ready`, `funded_live_fill_required=false`, the deploy-ready
  readiness contract, and all practical booleans true. If stale trace/bundle artifacts show live flags while learning
  or paper status is `not_evaluated`, sanitize to `status=fail_closed`,
  `live_trade_status=blocked`, and practical flags false. The 2026-05-29 Greedy
  stateful packet exposed this leak: workflow surfaces promoted while
  `policy-training-status` had `live_ready_count=0` and
  `live_trade_usable_count=0`.
- When cloning a state for a fresh factor run, clear stale BBN / Auto-Quant ledgers in both the symbol root and the `auto-quant/` subtree before replaying `auto_quant_results_import` + `auto_quant_prior_init`; copied snapshots can otherwise keep the old single-apply guard alive.
- Never infer missing sources from a snapshot. If historical OI / Greeks / gamma / expiry-magnet series are not available, mark them `unknown` and keep them out of the scored backtest.
- Never parse nested JSON tool output with naive `rfind('{')` style logic.
- Treat evaluate-preview flags and scorer parameter binding as prerequisite checks, not optional details.
- For Auto-Quant timeframe ladders, enumerate retained timeframe files first; if `1m`/`3m` or other requested frames are absent, report them as missing and run only real retained frames instead of fabricating data.
- Treat gate-field names as live schema, not permanent doctrine. As of 2026-05-24, `pda_hybrid_alignment` is retired/non-blocking unless current ict-engine source or readback artifacts explicitly reintroduce it as active. As of 2026-05-28, `transition_hazard` / `hybrid_transition_hazard` is regime telemetry only and must not be used as a promotion, live, or execution hard gate. As of 2026-05-29, Python blocker reports must mirror Rust Pre-Bayes semantics: when the Pre-Bayes gate status is accepted, every `pre_bayes` conflict flag whose name starts with `pda_` is telemetry, not a learning blocker. Do not create new blockers, promotion gates, plans, claims, or skill notes that require `pda_hybrid_alignment=true`, `transition_hazard < 0.60`, or `pre_bayes_conflict:pda_*`; older references may quote historical readbacks, but current classification must ignore those fields as hard gates unless live source explicitly reintroduces them as blocking. Before using `execution_readiness`, any active alignment field, or any successor field as a blocker, inspect the current source/readback contract and the latest artifact semantics. If a field is absent, retired, renamed, or explicitly marked non-blocking, do not report it as a hard gate; classify from current actionable/readiness/status/ranker/mature-row fields and update this skill/reference with the schema drift.
- For blocker reports, execution-tree `output.split_reason_lineage` can carry
  authoritative ranker validation rows such as
  `raw_scored_mature=961/30 production_validation=961/30 observation_validation=30/30`.
  Parse those lineage counters before classifying validation shortfalls. Do not
  infer `0/30` merely because the rows are absent from top-level JSON fields,
  and do not remove active readiness/execution-observe-only blockers when
  validation rows are ready. Do not treat transition hazard telemetry as one of
  those active blockers unless current source reintroduces it as blocking.
- For exact-timeframe downstream wrappers that use the path-ranker trainer
  fallback, keep the fallback family consistent end to end. If
  `pandas_path_ranker_trainer.py --allow-direct-fallback` writes a
  `weighted_feature_sum_v1` artifact, then the apply step must also pass
  `--allow-direct-fallback`, and
  `register-structural-path-ranking-trainer-artifact` must use
  `--model-family weighted_feature_sum_v1` instead of `catboost`. When checking
  exact branch survival, inspect execution-candidate branch fields,
  `execution_tree_trace.output.path_id` / `path_label`, and
  `split_reason_lineage`, not only top-level workflow fields; some current
  snapshots preserve the branch in candidate/trace surfaces while workflow
  branch keys remain null.
- Direct-model path-ranker artifacts must emit the current Rust execution gate
  floor, not stale trainer-local thresholds. As of 2026-05-29, repo runtime
  `STRUCTURAL_PATH_RANKING_EXECUTION_GATE_MIN_PATH_PROB` is `0.30`; a
  `path_ranker_direct_model.json` with `execution_gate_min_path_prob=0.50` can
  falsely leave a valid lower-bound score such as `0.437503` visible but unused
  by the execution tree. When rehearing a `path_ranker_visible_but_not_used`
  blocker, inspect the registered trainer artifact URI, direct-model JSON, and
  `execution_tree_trace.output.split_reason_lineage`; if the registered direct
  model carries the stale floor, regenerate/register the direct model on copied
  same-root state, enable runtime, and rerun local `analyze`/`workflow-status`
  before declaring the branch terminal. Clearing this blocker only proves ranker
  consumption; it does not override `execution_observe_only`, regime/friction,
  cost-survivor, validation, or promotion gates.
- When regenerating `regime_root_survivor_blocker_report.py` after a same-root
  downstream/materialization replay, use the original Gate 1 owner metrics for
  `--gate1-metrics`, not a downstream replay `checks/terminal_metrics.json` that
  only summarizes command exits and validation state. A downstream replay packet
  can correctly show `exact_branch_survived=true` while omitting the original
  5bps cost-survivor rows; feeding that replay summary as Gate 1 input creates a
  false `no_real_cost_5bps_survivor` and can hide already-cleared friction
  expectancy. Pair source Gate 1 owner metrics with the current copied-state
  execution candidate/tree when classifying whether remaining blockers are true
  live-plane issues such as regime confidence below floor or
  `execution_observe_only`.
- When the shared AQ/IBKR backend is occupied by a foreign live owner, a pure
  pandas pybacktest reading the persistent feathers in
  `<managed-auto-quant-checkout>/user_data/data/NQ_USD-*.feather` is a valid
  non-colliding prescreen route (it spawns no `fetch_external.py`,
  `provider-status`, IBKR gateway, or Rust clean-AQ child). Only NQ has a dense
  full-ladder 1m series there (1,770,523 rows, 2021-2025, retained ETH/full-session
  coverage; inspect actual timestamp coverage before computing density);
  ES/MNQ/M2K user_data feathers are decimated (ES 1m ~61 bars/day, ES 1d ~104
  days/yr) and must be rejected as dishonest evidence rather than used for
  superficial symbol diversity. Use merge_asof backward + shift(1) for all HTF
  context to avoid look-ahead, and compute cadence against the FULL session
  universe (unique NY calendar dates / retained ETH sessions), not trade-bearing
  sessions. For this user's profitability-factor work, default to ETH/extended
  trading hours or full retained session evidence. Do not silently RTH-filter
  futures factors, and do not treat an RTH-only survivor as the requested target
  unless the user explicitly asks for RTH; RTH may be reported only as a named
  comparison slice beside the ETH result.
- Interrupted or fixture-only Python prescreens are no-verdict artifacts, not
  Gate 1 evidence. If a prescreen writes `*.interrupted.exit` or exits via a
  signal/timeout such as `143`, record `prescreen_status=interrupted_no_verdict`,
  keep `promotion_allowed=false` / `trade_usable=false` / `update_goal=false`,
  and do not downstream it even if helper fixtures pass. A fixture-only
  prescreen that proves parser/readback shape on a tiny synthetic or bounded
  window may be useful test coverage, but it cannot prove full-window ETH/full
  retained session coverage, ES/YM/NQ breadth, cost survival, provider parity,
  paper/sim readiness, or lifecycle admission. Write that distinction into the
  workdoc, claim, and terminal summary before leaving the lane.
- The 2026-05-29 Claude NQ lane used a historical fixed `5bps/side` stress, not
  the correct futures commission model. Do not repeat its conclusion as a hard
  `10bps` futures cost wall or as a requirement for `>0.10%` gross edge per
  trade. Rehear old futures packets with the canonical per-contract helper
  (`support/scripts/research/instrument_cost_model.py`) or the dedicated
  `futures_bps_false_negative_revival.py` audit. The old NQ examples remain
  useful as stress evidence and payoff-shape evidence: the ~0.03% and ~0.056%
  gross-edge/trade rows failed the old stress, but their current disposition
  must be one of three buckets: `bps_stress_false_negative_recheck` if verified
  all-in instrument cost is positive while stress is negative;
  `zero_edge_churn_not_rescued_by_realistic_cost` if gross edge is still below
  commission/spread/slippage; or `cost_model_unverified` if the exact product
  cost was not verified. Do not manufacture a pass by ignoring cost or session
  gates, but do not discard a futures candidate solely because an old fixed-bps
  stress was negative. Promotion/trade-usable/update_goal remain false until
  same-root provider/AQ/downstream/lifecycle gates pass under verified
  instrument cost. Evidence packet retained as historical stress evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260529T123039+0800-claude-nq-htf-resonance-atrtrail-swing-pullback-v1`.
- When the user asks to find genuinely higher-quality factors, stop local parameter grinding and run a paper/repo/blog/social intake first. Keep only source-backed, codeable candidates, then feed them through small Auto-Quant Gate 1 slices with the same cost model before tree handoff. Treat social/blog material as idea source, not proof. Be active: choose the strongest codeable candidate yourself and run at least one real Auto-Quant Gate 1 slice instead of ending at a research list. See `references/paper-repo-alpha-intake-to-auto-quant.md`.
- Waiting time during Board B crowding is work time, never passive wait time.
  When fresh active claims, stale-safe timers, or live AQ/provider owners block
  a launch, do not wait for the one-hour mark and do not wait for ownership to
  clear. Immediately create or continue useful, interruptible source-backed
  intake: search papers,
  public repositories, strategy writeups, and indicator families; extract only
  codeable hypotheses, regime roots, data requirements, cost model needs,
  known failure modes, and exact non-duplicate branch candidates. Keep this
  intake read-only and low collision: no provider fetches, no IBKR probes, no
  Auto-Quant/Freqtrade/TOMAC launch, no external installer/clone execution, and
  no mutation of shared runtime state while blockers remain. Store findings in
  the lane workdoc or a compact repo-local intake packet, and mark every idea as
  `idea_only`, `paper_only`, `repo_source_only`, `python_prescreen_ready`, or
  `blocked_by_runtime`. A paper, blog, social post, or GitHub strategy is never
  trade evidence; it only earns a later Gate 1 attempt after duplicate checks,
  data/provenance checks, and honest cost gates. If a waiting-period insight is
  reusable, update this runtime skill and the repo-local agent skill surface in
  the same slice so future agents do the intake instead of passively waiting.
- 2026-05-29 paper-intake evidence on NQ 2021-2025 (5bps): Market Intraday Momentum
  (Gao-Han-Li-Zhou JFE 2018; futures-confirmed Baltussen et al JFE 2021) is DECAYED
  on recent NQ — verified timing, corr(r_first_30m, r_last_30m)=0.0048, OLS R²=0.0000,
  sign-agreement 47.6%; all trade variants raw≈0, net5bps≈-cost. Do not re-test plain
  first-half-hour intraday momentum on recent NQ expecting edge. The robust academic
  family is time-series momentum / trend (Moskowitz-Ooi-Pedersen JFE 2012; repos
  github.com/rkohli3/TSMOM, github.com/anthonyng2/Time-Series-Momentum); the only
  positive-5bps result of the session was a multi-day trend-hold (TSMOM family):
  net5bps +5.14%, 4/5 years positive, win 50%, PF 1.027, but sparse cadence
  0.078/session — edge is real, breadth-limited (single dense symbol). Lift cadence via
  a multi-instrument trend portfolio, NOT by shortening holds (which killed the edge:
  shortening max_hold flipped net5bps back negative) and NOT by overlapping concurrent
  same-direction entries (correlated over-betting flipped raw negative).
- BBN feedback maturation requires structural linkage, not loose `update --outcome`.
  Feeding regime-rooted backtest outcomes via `ict-engine update --symbol --outcome
  win/loss --pnl --regime` ingests feedback history, but `policy-training-status` stays
  matched_rows=0 / learning_admitted=0 / trade_usable=false unless the feedback links to
  analyze entry-model packets (structural-feedback-v1 with matching path_id/branch from
  `export-structural-path-ranking-target`). Simulated/backtest feedback is
  observation/learning evidence only; the gate correctly refuses promotion — do not read
  loose-update ingestion as paper/live readiness.
- CRITICAL: the local Auto-Quant freqtrade backend (`<managed-auto-quant-checkout>`,
  `run_tomac.py`, `config.tomac.json`) defaults to `fee=0.0` (ZERO cost), and
  `factor-autoresearch --auto-quant-profile synthetic_ohlcv` writes a short smoke config
  (timeframe 5m, ~7-day timerange, pairs ES/USD). Zero-fee results are a gate-lowering
  trap: on 2026-05-29 the 8 trend strategies showed +5-8% / PF 1.05-1.56 at fee=0.0, then
  flipped to -4% .. -63% / PF 0.31-0.54 at the honest `fee=0.0005` (5bps/side) on NQ/USD
  full window. For equities/ETFs/crypto/perps where a bps/notional fee model is the intended
  commission model, first verify the exact market, currency, broker plan, minimums/caps,
  exchange/regulatory fees, and fee-effective date; then set the real nonzero `fee`,
  `pair_whitelist`, and full `timerange` before trusting any run_tomac/freqtrade number.
  For futures, do not blindly set `fee=0.0005`: verify the product-specific per-contract
  cost, multiplier, tick value, and side convention, then either model it in a
  post-processor or document the exact notional conversion. For options, do not reuse stock
  or ETF fees; verify per-contract commission plus exchange/OCC/regulatory, exercise, and
  assignment fees before any cost-survival claim. Re-run and read the honest result. The
  lowest-turnover strategy (NqPullbackReclaimEma5m, 69 trades) was least negative —
  reconfirming low turnover is the only viable direction and that 1m/5m intraday trend
  churn failed that notional stress across BOTH the pandas and freqtrade engines (consistent
  with the 757 prior terminalizations). factor-autoresearch needs network to git-clone the AQ
  backend into `<state-dir>/.deps/auto-quant`; in a no-network sandbox, symlink the
  existing `<managed-auto-quant-checkout>` there and use `--auto-quant-profile synthetic_ohlcv`.
  Restore any edited shared `config.tomac.json` from backup after the run.
- ★ NQ compound trend recipe that achieved a strong stress-positive Gate-1 result on
  NQ 2021-2025 under historical `5bps/side` stress (2026-05-29, factor
  `nq_compound_trend_rrr_chopfilter_v1`): net5bps **+144%**, cadence
  **0.3625/session** (floor 0.333), **5/5 years all positive**, PF 1.34, win 57%.
  Since futures costs now use per-contract instrument cost, treat this as a strong
  stress-robust candidate, not as proof that `5bps/side` is the live commission model.
  Three independent walls, three independent fixes — apply them together:
  1. PAYOFF wall -> hard-code a fixed RRR bracket: SL = k*ATR (LARGE k on a
     higher-frame ATR, e.g. 8*ATR1h), TP = RRR*SL (RRR 1.5-3). Trailing/tight-SL
     exits keep per-trade gross edge tiny; a large-SL bracket makes payoff large
     enough to clear realistic futures all-in cost and even historical stress.
     Keep stress and real cost as separate readbacks.
  2. YEAR-STABILITY wall -> ChopFilter sub-regime gate: Kaufman Efficiency Ratio
     (|delta close_n| / sum|delta close|) on 1h, require ER>=0.35 over ~40 bars. Only trend
     entries in trending regimes; turned chop/bear years (2021/2022) from large losses to
     positive. CRITICAL: do NOT loosen ER to chase cadence — ER n40->n30/25 flips net5bps
     negative (-22%/-60%, 3/5 yrs). Loosening the regime filter IS gate-lowering.
  3. CADENCE wall -> compound portfolio of MULTIPLE DISTINCT entry mechanisms under one regime
     root (thrust/ROC + Donchian breakout don 60/120/240 + pullback-reclaim), each its own RRR
     bracket + ER filter, combined and DEDUPED by (entry-minute, dir). Single-mechanism
     multi-day holds cap at ~0.07-0.13/session; summing distinct cost-positive+year-stable
     streams reaches >=0.333 without shortening holds (kills edge) or overlapping same-signal
     entries (correlated over-betting, flips raw negative). This is the user's compound-strategy
     grammar (盈利因子叠加成为复合策略).
  Gate-1 economics PASS != trade-usable: keep promotion/trade_usable/update_goal FALSE until
  cross-engine reproduction with verified futures instrument cost, IBKR paper/sim forward
  validation, execution-tree materialization, and a multi-instrument breadth check. Evidence:
  repo packet `.../runs/20260529T123039+0800-claude-...-v1/`.
- The RRR-bracket trick beats cost ONLY for families with a large favorable excursion
  (trend/continuation): the large TP=RRR*SL makes friction a small fraction of
  payoff. Mean-reversion often still fails because its TP is small (revert to
  mid-band ~1-2 ATR), but the decisive futures test is verified instrument cost,
  not `10bps`. A 2026-05-29 RangeReversion factor (low-ER range regime +
  Bollinger/RSI extreme + MeanReclaim + RRR bracket) was negative across its old
  stress grid (net5bps -64%..-150%, PF 0.74-0.88, win <50%, despite cadence
  0.45-0.59). Reclassify such rows with per-contract cost before final
  dismissal; if gross edge stays below realistic all-in cost, label as churn.
- The full closed loop runs and is regime-rooted at every stage (verified 2026-05-29): analyze
  -> regime posterior; pre-bayes-status -> filter evidence; BBN belief_regime_node entities;
  export-structural-path-ranking-target -> trainer_manifest whose FEATURE COLUMNS are exactly
  regime_profit_branch_path / parent_regime_root / main_regime / sub_regime /
  sub_sub_regime_or_profit_factor / profit_factor (CatBoost/ranker is branched on the regime
  root by design); execution tree -> execution candidate + gate. It correctly stays
  observe/blocked when the analyzed window's regime != the factor's regime root (a trend factor
  is blocked in a range window) and the ranker stays mature_rows=0 until realized regime-matched
  feedback accumulates. That honest gating is correct closed-loop behavior, not a failure.
- A KST/Coppock NQ-local density frontier that is 5bps-positive but too sparse
  does not become practical merely by portfolio-aggregating ES/NQ/YM. The
  2026-05-29 bounded portfolio-density lift for
  `TrendExpansion -> KstCoppockMomentum -> MtfTrendResonancePullback -> PortfolioDensityLift`
  used retained ES/NQ/YM clean `1m` data with `5m/15m/30m/1h/4h/1d` context and
  a 12-row seed set from prior NQ-positive rows. It repaired cadence
  (`best_trades_per_day=0.692159`) but had `positive_5bps_count=0` and
  `survivor_count=0`; the best portfolio row was `5bps=-16.679702%` because the
  symbol split was ES `-22.487992`, NQ `+32.693822`, YM `-26.885532`. Treat
  cross-index aggregation as a symbol-quality gate, not a density shortcut: at
  least two symbols should be positive and no traded symbol negative before a
  portfolio screen can justify clean-AQ. This packet is fail-closed Python-only
  evidence; no downstream, paper/sim, promotion, or trade-use. Evidence: repo
  packet
  `support/docs/experiments/actionable-regime-confidence/runs/20260529T140630+0800-codex-tomac-kst-coppock-portfolio-density-lift-pybacktest-v1/summaries/terminal_packet.md`.
- When starting the next fresh Board B factor lane and no stricter user
  instruction overrides it, bias candidate selection toward TrendExpansion /
  trend-following families first. This is a search prior, not proof: do not
  claim trend-following is guaranteed profitable. Apply the profitability
  lifecycle split: learning admission needs a correct regime root, declared
  friction positive expectancy, evidence rows, leakage pass, and non-blocked
  provider evidence; verified friction/cost model, density, validation,
  execution readiness, and execution materialization are paper/live blockers
  unless current source says they invalidate learning. Transition hazard is
  currently telemetry only.
- When the user flags poor factor diversity, enforce a rotation queue before launching the next profitability run. Give time-tested public families a fair Gate 1 attempt before revisiting local favorites: opening-range breakout/fade/reclaim, Donchian/Turtle, Darvas/box breakout, ADX/ATR, Keltner/squeeze, Connors RSI2, SuperTrend, Elder/MACD impulse, time-of-day/seasonality, market-profile/initial-balance, pair/relative-value z-score, gap fade/go, stop-run/liquidity sweep, volatility/noise-band breakout, NR7/Crabel, Heikin-Ashi/ATR trend, KST/Coppock, Choppiness, Mass Index, Alligator/Fractal, CMF/OBV, Klinger, pivot/CPR/Camarilla, Vortex/VI, Aroon/CCI, and PSAR. Do not let VWAP/RSI/RVOL/microtrend variants occupy most consecutive slots unless they are explicit overlays on an already cost-surviving exact root. Before launching, search recent run roots and `/tmp/ict-engine-agent-claims/board-b-factor-refinement/` for the exact symbol/timeframe/family/factor id; do not use an active board because boards are archive-only; if it is already claimed or terminalized, skip it and choose a fresh symbol-family cell instead of duplicating evidence. Preserve negative rows as useful evidence, but move to a materially different family after a clean Gate 1 cost failure.
- Diversity is an execution gate, not a courtesy note. When the user says the search is too narrow, the next fresh Gate 1 slot must come from a public/time-tested family that has not already been terminalized for the same market/product/symbol/timeframe/root. Build and consult a compact coverage matrix with columns `family`, `market`, `product`, `symbol`, `timeframe`, `status`, `best_cost_bps`, `run_root`, and `next_action`. A negative Gate 1 is still a fair chance and should be preserved as evidence, but it must cool down that exact cell; the next attempt should rotate family or market cell, not mutate one familiar indicator. VWAP/RSI/RVOL/opening-drive/liquidity micro-variants are allowed only as downstream overlays on an existing exact-root survivor or when the hypothesis directly repairs currently active execution blockers such as readiness, mature feedback, ranker consumption, or execution-candidate materialization.
- If the user narrows Board B to "only trend-following" / "只做顺势交易", treat that as the active family-selection policy for new lanes until superseded. Choose fresh candidates under trend-continuation roots such as `TrendExpansion`, breakout/continuation, Donchian/Turtle, SuperTrend/ADX, Keltner/ATR breakout, Heikin-Ashi/ATR trend, Vortex/VI, Aroon/CCI continuation, PSAR trend flip, momentum-window continuation, and volatility-expansion trend. Require multi-timeframe resonance as the preferred candidate shape: low-timeframe entries, usually `1m`, should align with higher-frame trend evidence from real retained frames such as `5m/15m/30m/1h/4h/1d` where available, using slope/structure/breakout/volatility-expansion confirmation and rejecting countertrend entries unless they are only protective filters on an already cost-surviving trend root. Avoid new mean-reversion, fade, range-reversion, pair z-score, gap-fade, snapback, or sideways/chop families unless they are only protective filters on an already cost-surviving trend root. Do not claim trend-following or multi-timeframe resonance guarantees profit: still require real provider or retained-real rows, exact rooted positive verified cost model, positive trade count, same-root downstream, provider parity, validation, and execution materialization. For futures, that verified model must be product-specific per-contract cost; `5bps/side` is only an explicitly labeled stress scenario.
- If the user narrows entry to predicted expansion/trend only, enforce the stricter policy as `TrendExpansion`-only entry until superseded. A factor may enter only when closed-bar evidence predicts the next tradable state is `TrendExpansion`; every other regime or unclear state is reference/veto only and must not open its own range, fade, mean-reversion, stress, chop, or transition trade. Realized future regime labels are not entry features. Market, stop, or limit order variants are allowed only after the closed signal bar is available, with the earliest fill modeled at the next bar or later and with separate slippage/fill evidence. Workdocs, claims, terminal metrics, and source intake packets should record `entry_allowed_regimes=TrendExpansion`, `other_regimes_policy=reference_veto_only_no_entry`, and a no-lookahead guard.
- Multi-timeframe trend resonance is an economics preflight, not just a sign
  check. For new trend-only Board B prep, require a real trade side and a
  higher-timeframe directional slope large enough to clear the verified
  round-turn friction floor before counting a timeframe as aligned. For futures,
  use product-specific per-contract commission/exchange/regulatory costs plus an
  explicit slippage model; do not assume a universal `10bps` round trip. Tiny
  positive slopes that cannot plausibly pay the declared friction floor should be
  rejected as `slope_bps_lt_min` or the lane's equivalent, and `side=0` rows must remain
  `no_trade_side` instead of accidentally becoming short-trend resonance.
- In local Auto-Quant loops, repeated `0 trades` across finished rounds are a
  structural classification signal, not a cost-survivor near miss. If
  `terminal_metrics.json` shows `best_raw_total_profit_pct=0.0`,
  `best_5bps_total_profit_pct=0.0`, `survivors_5bps=[]`, and finished rounds
  write only zero-trade rows, classify the branch as structural no-entry /
  no-survivor and stop treating it like a candidate that merely missed friction.
  If a later round exits abnormally after earlier finished zero-trade rounds,
  preserve the runtime failure in the terminal decision, but keep the primary
  economic classification anchored on structural zero-entry rather than
  rebranding it as a cost or downstream blocker.
- IBKR paper/sim trading is a forward execution-validation surface, not a
  shortcut around Gate 1. Use it after a same-root trend-continuation factor has
  real or retained-real historical rows, exact rooted positive verified
  instrument-cost survival, positive trade count, and MTF resonance evidence.
  Historical `5bps/side` survival may be retained as stress telemetry but is not
  the futures commission authority. Before any fresh
  IBKR paper/sim lane, run a bounded IBKR preflight such as
  `provider-status --provider ibkr --agent` plus a tiny known-good historical
  probe (`AAPL`/`SPY` or the exact target) that writes nonzero rows; if the
  gateway is unreachable, returns zero rows, or times out, classify the lane as
  provider-blocked and do not launch paper/sim execution. Record paper/sim fills
  as execution-readiness and latency/slippage evidence with redacted account
  provenance; do not treat simulated fills as promotion or trade usability until
  historical cost gates, provider parity, validation rows, execution readiness,
  and execution materialization all pass under the same rooted branch. Treat
  transition hazard as regime telemetry, not a live gate.
- `provider-status --provider ibkr --agent` is a readiness hint, not row truth.
  For Board B, do not treat IBKR as usable until a same-turn historical probe
  writes nonzero rows. Do not hardcode `127.0.0.1:7497` as the probe target:
  discover the reachable local API port first (`7497`, `7496`, `4002`, `4001`)
  or let `fetch_external.py ibkr-historical` auto-probe it; on 2026-05-25 the
  live IB Gateway listener was `4002`, so the earlier `7497` connection-refused
  readback was a bad probe shape, not row truth. If Bybit/Binance public crypto
  endpoints are region-blocked (`403` CloudFront country block or `451`
  restricted location), reroute to a provider that actually returns rows, such
  as Kraken public OHLC, and record the provider triage in the run packet.
- For strict `TrendExpansion` OTE overlays under
  `RootEvidencePullbackMssCisd`, do not stop at recording the bearish Fibonacci
  draw contract. If a script declares both bullish and bearish OTE setups, the
  generated strategy must implement both executable directions: `can_short=True`,
  bullish and bearish MSS/CISD evidence fields, bullish and bearish
  `0/0.5/0.62/0.705/0.79/1.0` OTE levels, `enter_long`, `enter_short`,
  `exit_long`, and `exit_short`. Keep the canonical branch rooted as
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ...`,
  store `direction=long_short` as material metadata, and keep downstream gates
  locked behind exact same-root positive `5bps/side` survivors plus current
  validation/readiness/execution requirements. Add identity tests that compile
  the generated strategy source; source-contract parity is not a factor verdict
  and must not imply promotion or trade usability.
- A source-backed NQ Dual Thrust smoke is currently negative and should not be
  promoted or rerun unchanged. The 2026-05-29 local retained-feather lane
  `nq_dual_thrust_mtf_breakout_v1` used `1m` origin plus
  `5m/15m/30m/1h/4h/1d` context, previous-session Dual Thrust breakout lines,
  1h ER/trend confirmation, and fixed RRR exits. The bounded source-formula
  smoke row `lb2_k0.35_er0.35_risk0.75_rrr2.5_hold3120` produced full
  2021-2025 raw `+8.431172%` but net `5bps/side=-3.268828%`, PF `0.974391`,
  cadence `0.090768/session`, and only `2/5` positive years; 2024-2025 was
  positive but 2021-2023 was negative. Treat it as
  `terminalized_python_gate1_smoke_negative`, with `promotion_allowed=false`,
  `trade_usable=false`, and `update_goal=false`. Because the smoke permitted
  overlapping multi-day positions, successor work must be a new child branch
  with explicit single-slot/non-overlap modeling or a 2024+ regime split; do
  not lower costs/cadence or promote this smoke result. Evidence root:
  `/tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800`.
- A strict `TrendExpansion` OTE/MSS/CISD tail-exhaustion guard can repair
  economics while still failing practical cadence. The local TOMAC NQ
  `trend_tail_exhaustion_guard_v1` overlay preserved the rooted branch
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> trend_tail_exhaustion_guard_v1`
  and changed the full 2021-2025 best row from negative `5bps/side` parent
  behavior to a sparse positive short-balanced row (`38` trades, `1290`
  sessions, `5bps=+1.9536%`, `PF=1.2083`), but it failed the user's cadence
  floor (`0.02946` trades/session, below one trade per three sessions).
  Treat this as incubate/repair evidence only: do not downstream, promote, or
  call it trade-usable; the next same-root repair should increase density
  without lowering hard `5bps/side`, rooted identity, or cadence gates.
- The same TOMAC NQ strict OTE root showed that a bounded OTE touch followed by
  later MSS/CISD confirmation can improve density but still fail practical
  cadence. The `ote_reaction_confirmation_v1` overlay preserved the rooted
  branch
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> ote_reaction_confirmation_v1`
  and moved the full 2021-2025 best row to `74` trades over `1290` sessions
  (`0.05736` trades/session) with positive `5bps=+1.6272%` and `PF=1.1111`,
  but still failed the one-trade-per-three-sessions floor. Treat this as
  density-improved sparse-positive repair evidence only: no downstream,
  promotion, or trade usability. The next same-root attempt must either add a
  materially denser entry trigger without destroying 5bps economics or pivot to
  a denser trend-continuation subfamily under the same regime root.
- Treating OTE as a trend-root pullback opportunity while making MSS/CISD
  supplemental evidence is directionally useful but still not enough on local
  TOMAC NQ full-window data. The
  `trend_root_ote_pullback_opportunity_v1` overlay preserved the rooted branch
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> trend_root_ote_pullback_opportunity_v1`
  with `trend_root_role=hard_entry_gate`, `ote_role=hard_entry_gate`,
  `mss_cisd_role=supplemental_score_and_evidence`, and
  `tail_role=risk_metadata_and_score_penalty`. Full 2021-2025 TOMAC NQ results
  split into sparse-positive quality and dense-negative rows: best quality
  short row had `48` trades over `1290` sessions (`0.03721`
  trades/session), positive `5bps=+5.9196%`, `PF=1.7492`, but failed the
  one-trade-per-three-sessions floor; dense rows reached acceptable cadence
  (`849`/`1149` trades) but failed hard `5bps` economics. Treat this as
  incubate/negative boundary evidence only: no downstream, promotion, or trade
  usability. The next same-root attempt should pivot to a denser non-OTE 1m
  entry family, or use OTE only as supplemental context on an already
  cost-surviving dense trend-continuation root.
- TOMAC NQ ETH/full-session OTE reacceleration improved materially only after
  disabling the early `exit_signal` and using fixed-hold exits. The 2026-05-31
  exact-AQ fixed-hold repair
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
  produced 1721 trades, fee-only instrument-cost total `+66.160966%`, PF
  `1.218802`, `1.106752` trades/session, positive chronological thirds, and
  `5/5` positive fee-only years. Treat this as the current strongest OTE repair
  lead, not practical evidence: Freqtrade still reported `48.30%` missing-data
  fillup, the trade rows are simulated exact-AQ backtest feedback, accepted
  paper/live/broker feedback is absent, and no canonical same-tree practical
  closure exists. Next work should verify market-data provenance, accepted
  execution feedback, and downstream lifecycle on the fixed-hold root after
  compact audit/process guard clearance; do not relabel the exact-AQ survivor as
  `trade_usable=true`.
- The same strict trend-root OTE/MSS/CISD contract can fail on a different
  index-futures lane even when both long and short OTE directions are correctly
  implemented. The local TOMAC YM full-window scan preserved
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> tomac_ym_strict_trend_ote_mss_cisd_gate1_v1`,
  implemented bullish and bearish Fibonacci levels
  `0/0.5/0.62/0.705/0.79/1.0`, and treated MSS/CISD as supplemental evidence,
  but the best full 2021-2025 row had only `19` trades over `1289` sessions
  (`0.01474` trades/session), `5bps=-0.0235%`, and PF `0.5710`. Treat this as
  a negative-boundary sample: trend-root pullbacks remain the correct branch
  shape, but do not infer trade usability from "trend confirmed means every
  pullback is an entry"; require same-root cost/density survival before
  downstream, paper/sim, promotion, or trade-use.
- The local TOMAC ES strict TrendExpansion OTE/MSS/CISD full-window scan
  produced the same negative boundary on a larger retained index-futures
  history. The scan preserved
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> tomac_es_strict_trend_ote_mss_cisd_gate1_v1`,
  used ES retained-local `1m` rows plus `5m/15m/30m/1h/4h/1d` context,
  implemented bullish and bearish OTE levels `0/0.5/0.62/0.705/0.79/1.0`,
  and kept MSS/CISD as local swing-break plus displacement evidence. The
  2010-06-06 to 2026-04-03 full-window result had `5,528,518` local `1m`
  rows.
- The TOMAC TOD cap65 branch remains the strongest known TOMAC Gate 1 lead, but
  same-root execution-admission repairs must preserve hard cost and cadence
  instead of promoting low-hazard snapshots. The
  `SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio ->
  session_sweep_grid_v1` repair attempt on the case04 NQ low-hazard snapshot
  tested deeper sweep/reclaim and wider target/stop variants at explicit
  `5bps/side`. Freqtrade/AQ variants all failed 5bps (`DeepWide` best:
  `41` trades, `5bps=-1.69%`, PF `0.8087`). A wider local grid found sparse
  positive rows (`17` trades, `5bps=+1.4391%`, PF `1.4734`) but no candidate
  satisfying the one-trade-per-three-sessions density floor; the best density
  floor row was still negative (`34` trades, `5bps=-1.2586%`, PF `0.8230`).
  Treat this as a negative boundary for session-sweep/wider-target repair:
  no downstream, no IBKR paper/sim, no promotion, no trade usability. The next
  same-root TOD repair should change the entry family or portfolio component
  mix rather than continuing to tune the same sweep/reclaim shape.
- The TOMAC `AdaptiveSlotContrarian` density-repair source scan can report a
  `gate1_survivor_needs_downstream` row while still failing the user's practical
  cadence once density is recalculated against the full retained session
  universe. The retained-local NQ scan at
  `/tmp/ict-engine-tomac-tod-contrarian-density-repair-launch-20260526T194000+0800`
  completed with `build_coverage.exit=0` and `tomac_scan.exit=0`; the top row
  `TOD_contrarian_slot120_h240_lb80_e7.5_wr56_rv1_all_days` had `151` short
  trades, exact `5bps=+4.6725%`, PF `1.1517`, and scanner decision
  `gate1_survivor_needs_downstream`. But
  `tomac_session_seasonality_scan.py` measures `trades_per_session` over
  trade-bearing sessions, not all eligible retained sessions. Recomputed against
  `1292` full regular NQ sessions, density is only `0.116873` trades/session,
  below the one-trade-per-three-sessions floor, and 2021 is negative
  (`5bps=-7.4171%`, PF `0.4558`). Treat this as
  `incubate_sparse_positive_not_trade_usable`: no downstream, paper/sim,
  promotion, or trade usability. Before accepting any future TOD/session scan
  survivor, recompute density against the full retained session universe and
  year splits, not the scanner-local trade-session denominator.
- TOMAC `PortfolioAdaptiveSlotContrarian` is an incubate-only lead after the
  2026-05-26 retained-local NQ/YM/XAU portfolio scan, not a practical factor.
  The takeover root
  `/tmp/ict-engine-tomac-portfolio-adaptive-slot-contrarian-takeover-20260526T184900+0800`
  found a 12-component contrarian portfolio with `558` trades over `1556`
  sessions, aggregate exact `5bps=+33.2138%`, PF `1.3118`, and
  `0.3586` trades/session, but the artifact decision was
  `reject_low_density` because 2021/2023 were negative and yearly cadence was
  below the one-trade-per-three-session practical floor in 2023, 2024, and
  2025. Keep `downstream_allowed=false`, `promotion_allowed=false`, and
  `trade_usable=false`; future work must materially improve year stability and
  yearly cadence before exact AQ/downstream. The same slice fixed
  `tomac_tod_portfolio_aq.py` and
  `run_tomac_portfolio_adaptive_slot_contrarian_prep_v1.py` so exact-AQ launch
  plans can pass explicit `--branch-path`, `--factor-id`, and
  `--strategy-class`; do not run the old hardcoded
  `BalancedAdaptiveSlotPortfolio` AQ identity for this contrarian branch.
- Local TOMAC high-excursion families across NQ/YM/XAU are a completed Gate 1
  negative boundary unless a future hypothesis materially changes the entry
  economics or density. The retained-local scan at
  `/tmp/ict-engine-tomac-high-excursion-gate1-20260526T182946+0800` preserved
  rooted branches under `TrendExpansion -> InitialBalanceExtension`,
  `TrendExpansion -> PriorDayExtremeContinuation`,
  `RangeTransition -> OvernightInventoryFade`, and
  `TrendExpansion -> ImpulseFollowThrough`, evaluated `1620` candidates, and
  found `0` survivors. Sparse overnight-inventory rows were the only positive
  looking top rows; the best was a YM fade with `10` trades and positive
  `5bps_net_ret=0.010436159693631968`, but it failed density. Treat this as
  `drop_gate1_no_survivor_high_excursion_sparse_or_negative`: no downstream,
  paper/sim, promotion, or trade usability, and do not repeat these
  high-excursion families as fresh lanes without a materially different
  density/economics mechanism.
  rows, `4,065` sessions, `0` hard `5bps/side` survivors, and best row
  `short_quality` with `161` trades (`0.039606` trades/session),
  `5bps=-11.3565%`, PF `0.7907`. Treat this as
  `drop_gate1_no_positive_5bps_after_retained_local_scan`: no downstream,
  paper/sim, promotion, or trade usability, and do not repeat ES strict
  OTE/MSS/CISD unless the next hypothesis materially changes the cost/churn
  structure while preserving the same regime-root contract.
- The local TOMAC 6E strict TrendExpansion OTE/MSS/CISD full-window scan also
  failed after preserving the same rooted OTE contract on retained FX-futures
  data. The scan preserved
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> tomac_6e_strict_trend_ote_mss_cisd_gate1_v1`,
  used 6E retained-local `1m` rows plus `5m/15m/30m/1h/4h/1d` context,
  implemented bullish and bearish OTE levels `0/0.5/0.62/0.705/0.79/1.0`,
  and kept MSS/CISD as local swing-break plus displacement evidence. The
  2015-01-01 to 2025-12-31 result had `3,818,325` local `1m` rows, `2,841`
  trade sessions, `6` variants, `0` hard `5bps` survivors, and best row
  `short_quality` with `57` trades (`0.020063` trades/session),
  exact `5bps=-4.7194%`, PF `0.2669`. Treat this as
  `drop_gate1_no_positive_5bps_after_retained_local_scan`: no downstream,
  paper/sim, promotion, or trade usability. Do not repeat 6E strict OTE/MSS/CISD
  as a fresh lane unless the next hypothesis materially changes the cost/churn
  structure while preserving the same regime-root contract.
- The local TOMAC XAU/GC strict TrendExpansion OTE opportunity scan extended the
  same rooted contract into retained precious-metals futures and still only
  produced sparse incubate evidence. The full-window source scan preserved
  `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> ote_pullback_continuation_v1 -> xau_gc_strict_ote_opportunity_mss_supplemental_v1`,
  used `1,769,524` retained-local GC `1m` rows from 2021-01-06 to 2026-01-05
  plus `5m/15m/30m/1h/4h/1d` context, kept market/product/provider/symbol/timeframe
  as labels, implemented bullish and bearish OTE levels `0/0.5/0.62/0.705/0.79/1.0`,
  and treated MSS/CISD as supplemental evidence. It produced `0` hard
  `5bps/side` plus cadence survivors; the best row was one sparse positive
  `short_quality` trade over `1,556` sessions (`5bps=+0.1913%`,
  `0.00064` trades/session), so it failed the one-trade-per-three-sessions
  floor. A neighboring same-symbol smoke packet found `11` trades over `78`
  sessions with positive `5bps`, but also failed cadence and did not launch a
  full replay because the NQ strict OTE owner was live. Treat XAU/GC strict OTE
  as `incubate_sparse_positive_no_downstream`: no provider fetch, Auto-Quant,
  downstream, paper/sim, promotion, or trade usability; do not repeat it as a
  fresh lane unless the next hypothesis changes the density/economic entry
  mechanism while preserving the same regime-root contract.
- A denser non-OTE `TrendExpansion` momentum-window pivot can repair cadence
  while failing the hard cost gate. The local TOMAC NQ
  `body_momentum_volatility_expansion_v1` scan preserved the rooted branch
  `TrendExpansion -> MomentumWindowContinuation -> body_momentum_volatility_expansion_v1`,
  kept market/product/provider/symbol/timeframe as provenance labels, used
  `1m` origin plus synthetic `5m/15m/30m/1h/4h/1d` context, and made MSS/CISD
  supplemental rather than a hard entry blocker. Full 2021-2025 results had
  practical cadence in the best long-quality row (`528` trades, `1290`
  sessions, `0.4093` trades/session), but exact `5bps/side` economics were
  deeply negative (`-37.6501%`, PF `0.4926`), and dense rows were worse. Treat
  this as negative boundary evidence only: no downstream, promotion, or trade
  usability. The next trend-root TOMAC attempt should add a cost-aware
  continuation filter that attacks churn/slippage directly, or return to the
  stronger sparse OTE branch only as context on a different dense survivor.
- A cost-aware continuation filter on that same TOMAC NQ body-momentum branch
  can recover exact `5bps/side` economics only by becoming too sparse. The
  completed-trade postscan preserved the rooted branch
  `TrendExpansion -> MomentumWindowContinuation -> body_momentum_volatility_expansion_v1 -> cost_aware_continuation_filter_v1`
  and kept market/product/provider/symbol/timeframe as provenance labels. The
  best full 2021-2025 row was the short-quality parent with a volume/tail/late
  session filter (`22` trades over `1290` sessions, `0.01705`
  trades/session, `5bps=+2.6481%`, PF `1.9461`), so it failed the practical
  one-trade-per-three-sessions cadence floor and produced `0` Gate 1
  candidates. Treat this as incubate/negative-boundary evidence only: no
  downstream, promotion, or trade usability. Do not keep tightening this same
  body-momentum cost overlay; the next same-root TOMAC attempt should build a
  materially denser entry trigger that preserves positive exact `5bps/side`, or
  return to raw OHLCV for a different trend-continuation subfamily under
  `TrendExpansion`.
- A local TOMAC 6E/EUR Vortex/VI trend-continuation full-window scan can
  preserve the correct regime root and MTF ladder while still failing the hard
  cost floor. The 2015-2025 retained-local scan preserved
  `TrendExpansion -> VortexViTrendContinuation -> vortex_vi_mtf_continuation -> tomac_6e_vortex_vi_trend_gate1_v1`,
  used outright 6E contracts only, wrote `1m` plus
  `5m/15m/30m/1h/4h/1d`, and kept provider fetch, Auto-Quant, downstream,
  paper/live, promotion, and trade-use false. Full-window results used
  `3,818,325` rows over `3,423` sessions; the best row was `short_quality`
  with `392` trades (`0.1145` trades/session) and exact
  `5bps/side=-52.3106%`, with `0` hard 5bps survivors. Treat this exact
  6E/Vortex cell as terminal negative boundary evidence; do not rerun it as a
  fresh active claim unless the hypothesis materially changes the entry
  economics or cost model while preserving the same rooted identity.
- A local TOMAC 6E/EUR Aroon/CCI trend-continuation full-window scan produced
  another negative boundary under the same TrendExpansion policy. The
  retained-local 2015-2025 run preserved
  `TrendExpansion -> EuroFxAroonCciTrendContinuation -> aroon_cci_mtf_continuation -> tomac_6e_aroon_cci_trend_gate1_v1`,
  used outright 6E contracts only, wrote `1m` plus
  `5m/15m/30m/1h/4h/1d`, and kept provider fetch, IBKR historical,
  Auto-Quant, downstream, paper/live, promotion, and trade-use false. The run
  used `3,818,325` retained-local `1m` rows over `3,423` sessions with `6`
  variants and `0` hard `5bps` frequency survivors. The best visible row was
  `short_quality` with `209` trades (`0.061058` trades/session),
  exact `5bps=-20.7149%`, PF `0.2009`; dense rows had acceptable cadence but
  deeply negative cost economics. Treat this exact 6E/Aroon/CCI cell as
  terminal negative-boundary evidence; do not repeat it as a fresh lane unless
  the hypothesis materially changes the cost/churn structure while preserving
  the same regime-root contract.
- A local TOMAC 6E/EUR DMI/ADX trend-continuation full-window scan added the
  same negative-boundary evidence for another public trend family. The
  retained-local 2015-2025 run preserved
  `TrendExpansion -> EuroFxDmiAdxTrendContinuation -> dmi_adx_mtf_continuation -> tomac_6e_dmi_adx_trend_gate1_v1`,
  used `3,818,325` cleaned outright 6E `1m` rows over `3,423` sessions plus
  `5m/15m/30m/1h/4h/1d` context, and kept provider fetch, IBKR historical,
  IBKR paper/sim, Auto-Quant, downstream, paper/live, promotion, and trade-use
  false. The scan produced `0` hard `5bps` plus frequency candidates. The best
  row was `tomac_6e_dmi_adx_trend_short_quality_dmi28_a4` with `318` trades
  (`0.092901` trades/session), exact `5bps=-30.4790%`, PF `0.0972`, and
  decision `reject_less_than_one_trade_per_3_sessions`; dense rows had cadence
  but failed hard `5bps` economics. Treat this exact 6E/DMI/ADX cell as
  terminal negative-boundary evidence: no downstream, paper/sim, promotion, or
  trade usability, and do not repeat it as a fresh lane unless the hypothesis
  materially changes the cost/churn structure while preserving the same
  regime-root contract.
- A local TOMAC YM Chande-Kroll/ADX trend-continuation smoke can produce plenty
  of `1m` cadence while still failing the hard cost floor. The bounded
  2025-01-01 to 2025-03-31 smoke preserved the rooted branch
  `TrendExpansion -> EquityIndexChandeKrollAdxTrend -> chande_kroll_stop_adx_trend_continuation -> tomac_ym_chande_kroll_adx_trend_gate1_v1`,
  used local retained YM rows (`85013` normalized `1m` rows) plus
  `5m/15m/30m/1h/4h/1d` derived context, and kept provider fetch,
  Auto-Quant, downstream, promotion, and trade-use false. All three variants
  failed exact `5bps/side`: dense `311` trades had `5bps=-32.1597%`, balanced
  `242` trades had `5bps=-25.5273%`, and quality `181` trades had
  `5bps=-16.6967%`. Treat this as a clean Gate 1 negative boundary sample:
  do not downstream, paper/sim, promote, or keep repeating Chande-Kroll/ADX on
  YM without a materially different cost hypothesis.
- A local TOMAC ES SuperTrend/ADX trend-continuation full-window scan can also
  produce real `1m` trades while failing the user's hard friction floor. The
  retained-local 2010-06-06 to 2026-04-03 scan preserved
  `TrendExpansion -> SupertrendAdxTrendContinuation -> supertrend_adx_mtf_continuation -> tomac_es_supertrend_adx_trend_gate1_v1`,
  built `1m` plus `5m/15m/30m/1h/4h/1d` context from `5524335` local rows, and
  kept provider fetch, Auto-Quant, downstream, paper/live, promotion, and
  trade-use false. All variants failed exact `5bps/side`: dense `559` trades
  had `5bps=-54.8510%`, balanced `483` trades had `5bps=-48.3857%`, and
  quality `263` trades had `5bps=-30.5719%`. Treat this as
  `drop_gate1_no_positive_5bps_after_retained_local_scan`: no downstream,
  paper/sim, promotion, or trade usability, and do not repeat ES SuperTrend/ADX
  without a materially different cost/churn hypothesis.
- A local TOMAC NQ KST/Coppock trend-continuation full-window scan can preserve
  the current trend-only branch grammar and full MTF ladder while still failing
  both practical cadence and hard friction. The retained-local 2011-01-01 to
  2025-12-31 scan preserved
  `TrendExpansion -> NasdaqKstCoppockTrendContinuation -> kst_coppock_mtf_continuation -> tomac_nq_kst_coppock_trend_gate1_v1`,
  built `1m` plus `5m/15m/30m/1h/4h/1d` context from `5,302,713` local NQ rows
  over `4,652` sessions, and kept provider fetch, IBKR historical, IBKR
  paper/sim, Auto-Quant, downstream, paper/live, promotion, and trade-use false.
  It produced `0` hard `5bps` frequency survivors and no sparse-positive
  `5bps` rows; the best row was
  `tomac_nq_kst_coppock_trend_long_quality_ctx4_slope16` with `1,426` trades
  (`0.306535` trades/session), exact `5bps=-121.4577%`, PF `0.2973`, and
  decision `reject_less_than_one_trade_per_3_sessions`. Treat this exact local
  NQ KST/Coppock cell as terminal negative-boundary evidence: no downstream,
  paper/sim, promotion, or trade usability, and do not repeat it as a fresh
  lane unless the hypothesis materially changes the cost/churn structure while
  preserving the same regime-root contract.
- A local retained-data NQ Mass Index + Keltner trend-carry screen is also a
  terminal negative/no-candidate cell for the rooted branch
  `TrendExpansion -> VolatilityBulgeResolution -> MassIndexKeltnerTrendCarry -> nq_mass_index_keltner_trend_carry_local_screen_v1`.
  The 2026-05-30 screen used `1,770,523` retained NQ `1m` rows from 2021-01-03
  to 2025-12-31 with shifted `5m/15m/30m/1h/4h/1d` context and ETH/full
  retained coverage (`1,275,583` non-RTH rows). It produced `0` Python Gate 1
  candidates. The best sparse long-swing row had `239` trades,
  `0.153599` trades/session, `net5bps=+1.413575%`, PF `1.010671`, and `3/5`
  positive years; the denser long row reached `563` trades and `0.361825`
  trades/session but fell to `net5bps=-32.241050%`. Treat this as
  `drop_python_screen_no_gate1_candidate`: no downstream, Auto-Quant, provider,
  paper/sim, promotion, or trade usability, and do not rerun unchanged. Evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260530T105902+0800-codex-nq-mass-index-keltner-trend-carry-local-screen-v1/checks/terminal_metrics.json`.
- A retained TOMAC Market Meanness Index trend-cleanliness screen is a
  terminal local negative/no-candidate cell as of 2026-05-31. The branch
  `RegimeRoot -> TrendExpansion -> NoiseRegimeFilter -> MarketMeannessTrendCleanliness -> PullbackRejoin -> <factor_id>`
  screened NQ/YM/XAU independent `5m/15m/30m/1h/4h/1d` ETH/full-retained
  factors from local TOMAC cache, with verified retained-session coverage and
  instrument-cost packets, and produced `108` local rows, `0` instrument-cost
  candidates, `0` Gate 1 survivors, and `promotion_allowed=false` /
  `trade_usable=false`. The best NQ `15m` row was cost-positive and dense but
  failed chronological split stability; the best NQ/YM `4h` rows were
  cost-positive but below the density floor. Do not rerun the same MMI
  trend-cleanliness shape unchanged. A successor must be a structurally distinct
  child such as split-stability repair for NQ `15m` or density repair for
  NQ/YM `4h`, and still needs exact AQ/provider/downstream practical lifecycle
  evidence before any promotion or trade-use claim. Evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T032939+0800-codex-mmi-trend-cleanliness-filter-local-screen-v1/checks/terminal_metrics.json`.
- For local TOMAC NQ Chande-Kroll/ADX trend-continuation, distinguish runner
  materialization failures from factor verdicts. The first full-window owner
  preserved
  `TrendExpansion -> NasdaqChandeKrollAdxTrendContinuation -> chande_kroll_adx_mtf_continuation -> tomac_nq_chande_kroll_adx_trend_gate1_v1`
  and materialized retained-local `1m/5m/15m/30m/1h/4h/1d` ladder files
  (`1m=1,770,523`, `5m=355,397`, `15m=119,327`, `30m=60,316`,
  `1h=30,810`, `4h=8,001`, `1d=1,556`) but exited without
  `checks/terminal_metrics.json`, `summaries/terminal_decision_summary.md`, or
  `summaries/screen_rows.csv`. Treat that as
  `blocked_runtime_exit_without_terminal_metrics_after_ladder_materialization`,
  not a Gate 1 factor verdict. The vectorized same-root debug runner using
  `merge_asof` context joins and vectorized resonance counts completed a
  bounded `50,000` row smoke with `0` hard `5bps` survivors (`short_dense`
  had `7` trades and `5bps=-1.459703`). The subsequent vectorized full-window
  rerun did produce one same-root hard `5bps` survivor over `1,770,523`
  retained NQ `1m` rows: `long_balanced`, `25` trades, `1,556` sessions,
  `0.01606684` trades/session, and `5bps=+2.164741%`. Treat that as
  sparse-positive incubate/repair evidence only because it misses the user's
  one-trade-per-three-sessions cadence floor by a wide margin. Do not
  downstream, paper/sim, promote, or call it trade-usable. The next same-root
  attempt should densify entries while preserving the vectorized MTF resonance,
  rooted identity, and positive hard `5bps` economics, or rotate away from NQ
  Chande-Kroll/ADX if the densification hypothesis would only loosen gates.
- The first same-root TOMAC NQ Chande-Kroll/ADX density-repair overlay did not
  fix the practical blocker. The retained-local full-window scan preserved
  `TrendExpansion -> NasdaqChandeKrollAdxTrendContinuation -> chande_kroll_adx_mtf_continuation -> tomac_nq_chande_kroll_adx_trend_gate1_v1 -> tomac_nq_chande_kroll_adx_density_repair_v1`,
  reused the vectorized `1m/5m/15m/30m/1h/4h/1d` resonance ladder over
  `1,770,523` NQ `1m` rows and `1,556` sessions, and produced the same sparse
  hard-`5bps` survivor (`long_parent_balanced`, `25` trades,
  `0.01606684` trades/session, `5bps=+2.164741%`). Denser variants increased
  cadence but all failed hard `5bps` economics; the densest row had `761`
  trades (`0.48907455` trades/session) but `5bps=-74.821439%`. Treat this
  as `incubate_same_root_5bps_positive_but_sparse_no_downstream_launched`:
  no downstream, IBKR paper/sim, promotion, trade usability, or repeated
  Chande-Kroll/ADX density overlays unless the next hypothesis changes the
  entry economics rather than merely loosening the same resonance filters.
- A later retained-local TOMAC NQ Chande-Kroll/ADX density-repair postscan
  confirmed the same child path is a negative boundary, not a viable downstream
  candidate. The same-root branch
  `TrendExpansion -> NasdaqChandeKrollAdxTrendContinuation -> chande_kroll_adx_mtf_continuation -> tomac_nq_chande_kroll_adx_trend_gate1_v1 -> tomac_nq_chande_kroll_adx_density_repair_v1`
  kept the full `1m/5m/15m/30m/1h/4h/1d` TOMAC NQ ladder, but exact same-bar
  pullback plus breakout/reentry constraints produced `0` trades across all six
  scripted variants. A sequential pullback/reclaim diagnostic repaired cadence
  while destroying friction survival: best short row `1865` trades,
  `1.198586` trades/session, `5bps=-184.077501%`; best long row `2452` trades,
  `1.575835` trades/session, `5bps=-243.082978%`. Treat this as
  `drop_child_density_repair_zero_trade_and_dense_cost_negative_no_downstream`:
  no downstream, IBKR paper/sim, promotion, trade usability, or further
  Chande-Kroll/ADX density tightening unless the next attempt changes the
  economic entry family rather than adding another loosened pullback overlay.
- A retained-local TOMAC YM Donchian/Turtle breakout trend-continuation scan
  can be dense and still economically dead after hard friction. The full-window
  scan preserved
  `TrendExpansion -> DonchianTurtleBreakoutContinuation -> donchian_turtle_mtf_continuation -> tomac_ym_donchian_turtle_trend_gate1_v1`,
  used `1m` origin plus `5m/15m/30m/1h/4h/1d` context over `5,063,395` YM
  rows and `4,656` sessions, and kept provider fetch, IBKR historical,
  Auto-Quant, downstream, paper/live, promotion, and trade-use false. It
  produced `0` hard `5bps` survivors: the least-bad visible row was
  `long_lb240_swing` with `2,714` trades (`0.58290378` trades/session) and
  exact `5bps=-265.371027%`; denser rows were worse. Treat this exact YM
  Donchian/Turtle cell as terminal negative-boundary evidence: do not
  downstream, paper/sim, promote, or repeat it as a fresh lane unless the
  hypothesis materially changes the cost/churn structure while preserving the
  same regime-root contract.
- A later retained-local TOMAC dense-family Donchian scan extended the same
  negative boundary across NQ/YM/XAU. The exact child branch
  `TrendExpansion -> DonchianChannel -> TrendBreakoutContinuation -> tomac_dense_donchian_trend_breakout_1m_v1`
  used local corrected-cleaner futures rows with `1m` origin and
  `5m/15m/30m/1h/4h/1d` context labels. The scan completed with
  `build_coverage.exit=0`, `tomac_scan.exit=0`, `216` raw rows, and `48`
  exact Donchian rows; every exact row was `reject_5bps_economics`. The best
  exact row was XAU `donchian240_trend_break_rv1.2_h120` with `974` trades,
  `1.0` trades/session, `5bps_net=-85.1428%`, and PF `0.5227`. Treat this
  as terminal dense-cost-failure evidence only: no AQ, downstream, paper/sim,
  promotion, trade usability, or repeated Donchian breakout scans without a
  materially different cost/churn mechanism.
- TOMAC prior-day `VolumeConfirmation` source-parity repair is also terminal
  negative after exact clean-AQ. The branch
  `RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> VolumeConfirmation -> tomac_idxfut_clean_prior_day_multifactor_confluence_volume_reclaim_1m_v1`
  repaired the generator from long-only hard-AND to bidirectional `score >= 4`
  source parity across WPR extreme, RSI extreme, PDH/PDL sweep/reclaim,
  `volume_ratio > 1.2`, low-volatility environment, and EMA20/EMA50 trend,
  and ran clean ES `1m` AQ with `run_tomac_1m.exit=0`. It produced `1887`
  trades and passed density, but raw return was `-21.76%`,
  `5bps/side=-210.46%`, instrument-cost return `-43.416954%`, and PF
  `0.912`. Treat as dense negative cost evidence only: no downstream,
  promotion, or trade usability.
- TOMAC NQ `VWAPMeanReclaim -> VwapReclaimPersistence -> RvolTrendQualityFilter`
  daily-first-signal parity repair improved raw behavior but still failed
  friction. The exact clean-AQ branch
  `RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> RvolTrendQualityFilter -> tomac_idxfut_clean_vwap_reclaim_rvol_trend_quality_filter_1m_v1`
  completed with `659` trades, raw `+2.71%`, PF `1.1829`, and balanced
  long/short evidence, but flipped negative at `1bps=-10.47%`,
  `2bps=-23.65%`, and `5bps=-63.19%`; `gate1_survivor=false`. Treat daily
  de-dupe as a useful parity repair but not a practical factor, and do not
  downstream or promote VWAP/RVOL quality unless a future exact-root variant
  survives hard cost and density.
- A retained-local TOMAC NQ two-leg OpeningDrive Gate 1 survivor can now
  materialize the same rooted branch through the local downstream chain while
  still remaining observation-only. The bounded replay preserved
  `TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1`,
  used retained NQ `1m/15m/1h` samples and exact branch metadata, and ran
  `auto_quant_results_import`, `auto_quant_prior_init`, `analyze`,
  `workflow-status`, `pre-bayes-status`, `policy-training-status`, and
  `export-structural-path-ranking-target` with exit `0` on both `2k` and `10k`
  bounded samples. That repairs small-sample materialization enough to inspect
  execution artifacts, but final readback stayed fail-closed:
  `execution_candidate.actionable=false`, execution tree `gate_status=blocked`,
  `branch=block_crowded`, `execution_readiness=0.3898991331301483`,
  `hybrid_transition_hazard=0.36857907253269917`,
  `path_ranker_score_visible_to_execution_tree=false`,
  `path_ranker_score_used_by_execution_tree=false`,
  `ranker_validation_ready=false`, and
  `raw_scored_mature=0/30 production_validation=0/30 observation_validation=0/30`.
  Treat this as an execution-materialization/readiness/ranker-validation repair
  lead only: no provider fetch, IBKR, external Auto-Quant dispatch, paper/sim,
  promotion, or trade usability. The next same-root work should add legitimate
  mature feedback / ranker validation and directly improve execution readiness
  or ranker consumption, not relaunch Gate 1 or lower gates.
- A raw TOMAC source script can report a spectacular parent result while the
  corrected front-outright clean replay fails. The local ES
  `no_be_strategy.py` WPR/fractal no-break-even parent first showed
  `21738` trades, `81.35%` win rate, `PF=6.58`, and `total_net_pnl=7110629.56`
  on the raw overlapping-contract CSV. A later full-window clean-AQ replay
  preserved the canonical branch
  `RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget`,
  used the same underlying symlinked TOMAC ES CSV, selected current highest
  volume outrights, boundary back-adjusted rolls, and wrote quality-ok
  `1m/5m/15m/30m/1h/4h/1d` feathers from `8433933` raw rows into
  `1768151` clean ES `1m` rows. Clean-AQ `1m` exited `0` but failed hard:
  `2753` trades, `total_profit_pct=-25.3`, `5bps_per_side_total_profit_pct=-300.6`,
  `instrument_cost_total_profit_pct=-56.895969`, and `PF=0.94`. A direct replay
  of the source no-BE logic on that same corrected clean bundle also failed
  (`6222` trades, `PF=0.940362`, `total_net_pnl=-48870.021429`). Treat raw
  all-contract TOMAC source positives as untrusted until the corrected
  front-outright/back-adjusted clean replay survives. This exact WPR/fractal
  no-BE parent is terminal negative for ES clean-AQ: no downstream, paper/sim,
  promotion, or trade usability.
- For live-profit factor training, regime is the branch root. Preserve a rooted path such as `main_regime -> sub_regime -> ... -> sub_sub_regime_or_candidate_factor -> profit_factor` through Auto-Quant, filtering, BBN, CatBoost, and execution-tree artifacts. Do not flatten a branch to the factor name or promote if downstream pivots to a sibling path. See `references/regime-rooted-branch-and-cost-stress.md`.
- If Gate 1 passes and downstream commands all exit 0 but execution still fails, classify from the current execution readback contract: actionable/status, gate status, transition/guard hints, readiness, ranker validation/usage, mature rows, and any active alignment fields. Historical packets often used `transition_hazard`, `pda_hybrid_alignment`, and `execution_readiness`; do not preserve `pda_hybrid_alignment` as a hard blocker if current code retired it or marks it non-blocking. Keep the rooted branch as observation-only and patch the same-root execution blocker first, not the cost gates. See `references/mes-15m-gate1-to-execution-blocker-20260519.md`.
- If a 1m compression-breakout/session-liquidity overlay preserves cost-stressed density but downstream still returns low readiness/high transition guard/no actionable candidate under the current schema, stop stacking near-equivalent liquidity overlays. Preserve the branch as observation and move the next same-root experiment toward a directly execution-facing overlay such as VWAP reclaim/persistence plus a tighter transition guard. See `references/ibkr-mnq1m-compression-breakout-session-liquidity-failclosed-20260520.md`.
- For this user's profitability-factor work, the factor tree root may only be the main regime class. Market, product, provider, symbol, contract, base timeframe, and ladder timeframe are portability labels/provenance fields, not branch nodes. The rooted path grammar is `main_regime -> sub_regime -> ... -> sub_sub_regime_or_profit_factor -> profit_factor...`: regimes may branch to regimes or the first profit factor; profit factors may only branch to later profit-factor overlays. Preserve labels separately (for example `market`, `product`, `provider`, `symbol`, `timeframe`, `window`) so a factor can later be tested on sibling symbols and markets without changing its tree identity. Legacy artifacts whose path starts with `FUTURES -> ... -> 5m -> RangeConsolidation` or `CryptoLinearPerp -> RangeReversion` must be reinterpreted as labels plus canonical branch `RangeConsolidation -> ...` or `RangeReversion -> ...`; do not copy the legacy prefix into new `branch_path` values. Start with one specific profit factor under that rooted branch; only add later profit factors as explicit composite overlays after the first earns evidence. Default ladder starts at `1m`, covers `5m/15m/30m/1h/4h/1d` where real provider data exists, and uses the maximum feasible window per lane. Learning admission is separate from paper/live readiness: require `trade_count > 0`, regime-root consistency, declared-friction positive expectancy, leakage pass, and non-blocked provider evidence; exact `5bps/side`, density, validation rows, execution readiness, ranker consumption, and execution materialization remain paper/live blockers. `1/day` or daily density is cancelled, and PDA/transition hazard are telemetry/repair context rather than required base gates. Sparse positive survivors can be learning evidence or repair candidates, but not automatically trade-usable. Keep `promotion_allowed=false` and `trade_usable=false` until downstream extension, validation, provider parity, readiness, ranker consumption, and execution materialization actually pass. See `references/regime-rooted-mtf-provider-ladder.md`.
- For this user's profitability-factor target, ETH is the default and required
  session scope. Interpret ETH as extended trading hours / full retained
  tradable session for the product, not RTH-only. Any factor-search, Gate 1,
  density calculation, split readback, or candidate handoff that uses RTH must
  label it explicitly as an `RTH_comparison` or a same-turn user-requested RTH
  slice. RTH-only evidence must never satisfy the user's default factor target,
  `promotion_allowed`, `trade_usable`, `update_goal`, or
  `same_tree_practical_closure` unless the user explicitly asks for RTH in the
  current task. If ETH/full-retained data exists, compute or preserve the ETH
  verdict first and show RTH only as secondary context. If only RTH data is
  available, classify the lane as `data_scope_blocked_for_eth_target`, keep
  `promotion_allowed=false` / `trade_usable=false` / `update_goal=false`, and
  record the missing ETH evidence in the workdoc plus terminal packet. Every
  workdoc, claim, terminal metrics/summary, and handoff for a profitability
  factor must state `session_scope`, whether an RTH filter was applied, and the
  ETH/full-retained coverage evidence or blocker. Practical-factor counts must
  exclude RTH-only packets unless the current user request explicitly narrowed
  the target to RTH.
- Yahoo/YF stock and ETF wrapper paths that use `fetch_external.py yahoo` are
  RTH comparison evidence by default because the current Yahoo chart fetcher
  sends `includePrePost=false`. Such wrappers must emit a fail-closed session
  readback in dry-run, material profiles, terminal metrics, no-launch summaries,
  workdocs, and claims: `session_scope=RTH_comparison` or a more specific
  value such as `rth_comparison_yfinance_regular_session_only`,
  `rth_filter_applied=true`, and an ETH/full-retained blocker such as
  `blocked_yfinance_includePrePost_false`. Do not count those rows as the
  requested ETH/full-retained evidence. Even if an exact 1m RTH/YF row survives
  hard cost stress, keep `downstream_allowed=false`, `pre_bayes_allowed=false`,
  `bbn_allowed=false`, `catboost_allowed=false`, `execution_tree_allowed=false`,
  `promotion_allowed=false`, and `trade_usable=false` until the wrapper
  refetches native ETH/full-retained data from IBKR/Polygon/Hubble or another
  verified provider. Do not use RTH/YF rows for `same_tree_practical_closure`.
- For IBKR US stock/ETF full-session refetches, omitting `--rth` is necessary
  but not sufficient. Treat `requested_ibkr_historical_omitted_rth_only` as a
  request-shape readback, not session evidence. The wrapper must prove returned
  rows outside the exchange-local RTH window, such as NYSE/Nasdaq
  `09:30-16:00 America/New_York`; otherwise keep
  `eth_full_retained_session_evidence=false`, set
  `eth_full_retained_coverage_status=blocked_full_session_row_coverage_missing`,
  and block downstream with
  `decision=data_scope_blocked_eth_row_coverage_missing`. If terminal metrics
  or rank rows already point at an IBKR full-session CSV, the wrapper should
  derive this row-coverage report from that CSV automatically instead of
  relying on a hand-filled metrics field.
- Apply the same canonical-root rule to readback, blocker-map, and handoff artifacts, not only to Auto-Quant material and training CSVs. If a report summarizes a legacy path such as `FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> ...`, emit `branch_path=RangeReversion -> ...`, preserve the original string as `original_branch_path`, and move `FUTURES/equity_index/M2K/1m` into labels. If no known main regime exists in the path, mark `canonical_root_ok=false` / invalid-root instead of guessing a root.
- Execution-candidate artifacts must preserve the canonical regime-root branch even when the candidate remains fail-closed, non-actionable, or observe-only. If report/pre-Bayes assignments carry a legacy prefix such as `FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> ...`, persist `execution_candidate.branch_path` and `execution_candidate.regime_profit_branch_path` as `RangeReversion -> ...` and keep the market/product/symbol/timeframe only as labels. A missing branch path is an identity/persistence bug, not a promotion gate; fix it without lowering currently active readiness, ranker/materialization, or mature-validation thresholds.
- If `execution_tree_trace.output.split_reason_lineage` exposes a structural
  ranker `path_id` but `closed_loop_branch_admission` is absent, use that
  lineage path only to preserve `execution_candidate.branch_path` /
  `regime_profit_branch_path` as observe-only evidence. Canonicalize away market,
  product, symbol, and timeframe prefixes, keep `actionable=false`, and do not
  infer promotion or trade usability from ranker visibility when
  `path_ranker_score_used_by_execution_tree=false`,
  `ranker_validation_ready=false`, or the execution gate remains `observe`.
- A branch-local survivor is not a full live-trade factor until practical extension is complete. Even after hard cost/density, direction, Pre-Bayes/BBN/CatBoost/execution-tree, current active readiness/ranker/materialization gates pass, record it only as an `extension_candidate` until it has been replayed step by step across the required breadth: full market, full product class, full sibling-symbol set, full timeframe/cycle ladder, and provider parity where available. Historical or packet-local `promotion_allowed=true` / `trade_usable=true` means branch-local admission only unless a later artifact explicitly records `extension_complete=true` after full-breadth replay survives. Do not call a factor "实战" from a single provider/symbol/timeframe packet or before the market/product/symbol/cycle extension has been completed one step at a time.
- If a profitability-factor run produces too few trades, do not tighten overlays or move downstream. First max the provider window for each available timeframe (`1m` feasible upper bound, then `5m/15m/30m/1h/4h/1d` where real provider data exists) and switch to a denser 1m entry family. A compound overlay that turns a passing base factor into sparse/negative rows should be dropped, not promoted. Positive 30m/1h siblings do not rescue a sparse/negative 1m root. If a sparse 1m root only yields 0-2 trades after a fair AQ run, stop grinding the same entry shape and pivot to a denser 1m family inside the same rooted branch. See `references/max-window-density-before-downstream.md` and `references/dense-1m-entry-family-pivot.md`.
- If a 30m/1h expansion or fade family passes mechanics but stays negative after cost stress, treat it as a dead-end observation lane and pivot the root family, not the overlays. The 2026-05-19 MNQ 30m/1h failed-expansion retries are documented in `references/regime-rooted-mnq-failed-expansion-20260519.md`.
- If an exact rooted branch passes Gate 1 and a same-root transition/alignment overlay also preserves cost density, but downstream still reports current-schema observe-only/non-actionable status, high transition guard, low readiness, or ranker validation/usage failure, stop stacking same-timeframe overlays. Keep it as observation and pivot to a denser `1m`/`5m` root or different market cell. The MES 15m overlay blocker is documented as a historical packet in `references/mes-15m-overlay-execution-blocker-20260519.md`.
- A source-backed public trend family can earn a downstream replay without being live-practical. The IBKR `MNQ/1m` SuperTrend/ADX breakout produced dense real futures rows and two `2bps/side` survivors, but no `5bps/side` survivor; exact downstream then ran cleanly through Auto-Quant import, Pre-Bayes, CatBoost/path-ranker registration, and execution-tree readbacks while still failing closed with `mature_rows=0`, `raw_scored_mature=0/30`, `execution_readiness=0.0`, `transition_hazard=1.0`, and `pda_hybrid_alignment=false`. Treat this as observation evidence: do not call a 2bps-only public trend breakout trade-usable, and do not stack another light breakout overlay under the same root unless the hypothesis directly improves mature feedback or the execution predicate trio.
- The same 2bps-only observation rule applies to public Ichimoku cloud trend
  continuation. An IBKR `MNQ/1m` Ichimoku cloud continuation packet found one
  exact-root `2bps/side` survivor (`cloud_fast_dense`: 8 trades, raw `+0.60%`,
  `2bps=+0.28%`) but failed `5bps/side`; exact downstream preserved the rooted
  branch and passed Pre-Bayes neutralization while still failing closed with
  `execution_readiness=0.0`, `transition_hazard=1.0`,
  `pda_hybrid_alignment=false`, `mature_rows=0`, and validation rows `0/30`.
  Treat Ichimoku trend continuation as useful public-family diversity evidence,
  not trade-usable alpha, unless a future exact-root variant survives 5bps/cost
  density and directly improves the execution predicate trio or mature feedback.
- Public crypto SuperTrend/ADX can provide useful higher-timeframe context
  while still failing the user's `1m`-origin hard gate. Kraken public spot
  `XBTUSDT/1m` and `LTCUSD/1m` SuperTrend/ADX continuation packets both fetched
  real `1m/5m/15m/30m/1h/4h/1d` rows and completed Auto-Quant
  batch/dispatch/rank with rooted branch fields preserved, but the exact `1m`
  origin had zero trades/no `5bps/side` survivor. Positive `4h` or sparse `5m`
  context rows are evidence only; do not downstream or repeat the same
  SuperTrend/ADX crypto spot shape unless the hypothesis directly fixes dense
  `1m` entry formation without relaxing cost gates.
- Public crypto Donchian/Keltner trend-continuation can show the same
  higher-timeframe-only failure mode. The Kraken public spot `NEARUSD/DOTUSD`
  Donchian-Keltner trend packet fetched real `1m/5m/15m/30m/1h/4h/1d` rows
  for both symbols and completed strategy compile plus Auto-Quant
  batch/dispatch/rank with rooted `TrendExpansion` fields preserved, but exact
  `1m` origin produced zero trades on both symbols and no hard
  `5bps/side` survivor. DOTUSD `1h` was positive (`8` trades, raw `+2.11%`,
  `5bps=+1.31%`) only as higher-timeframe context. Treat this as a clean Gate
  1 negative; do not downstream or repeat crypto Donchian/Keltner MTF trend
  breakouts unless the hypothesis directly repairs dense exact `1m` entry
  formation without lowering cost gates.
- Local TOMAC XAU/GC SSL-channel trend continuation is a completed dense
  negative boundary sample, not a downstream candidate. The retained local
  2021-01-06 to 2026-01-05 scan preserved the rooted branch
  `TrendExpansion -> SslChannelTrendContinuation -> ssl_channel_mtf_continuation -> tomac_xau_gc_ssl_channel_trend_gate1_v1`,
  built real retained `1m` plus `5m/15m/30m/1h/4h/1d` context, and generated
  three high-cadence rows. Even the best quality row had `2815` trades over
  `1555` sessions (`1.81028939` trades/session), raw `+63.7440%`, and
  `1bps=+7.4440%`, but failed the hard cost floor at `2bps=-48.8560%` and
  `5bps=-217.7560%`; dense and balanced rows were much more negative after
  cost. Treat this as `drop_gate1_no_positive_5bps_after_retained_local_scan`:
  no provider fetch, Auto-Quant, downstream, paper/sim, promotion, or trade
  usability. Do not repeat XAU/GC SSL-channel trend unless the next hypothesis
  directly reduces churn/cost while preserving the same regime root and
  cadence window.
- Local TOMAC XAU/GC SuperTrend/ATR trend-continuation is also a clean Gate 1
  negative boundary. The resumed full retained scan completed at
  `/tmp/ict-engine-tomac-xau-gc-supertrend-atr-trend-gate1-20260525T060356+0800`
  after preserving
  `TrendExpansion -> GoldSupertrendAtrTrendContinuation -> supertrend_atr_mtf_continuation -> tomac_xau_gc_supertrend_atr_trend_gate1_v1`,
  building real retained `1m` plus `5m/15m/30m/1h/4h/1d` context over
  `1,766,247` rows from 2021-01-06 to 2025-12-31. All six dense/balanced/quality
  long/short variants produced `0` trades and `0` same-root hard `5bps/side`
  survivors. Treat this as `drop_gate1_no_same_root_5bps_survivor`: no
  provider fetch, IBKR historical/paper, Auto-Quant, downstream, promotion,
  trade usability, or goal completion. Do not repeat standalone XAU/GC
  SuperTrend/ATR unless the next hypothesis materially changes exact `1m`
  entry formation without relaxing rooted identity, MTF evidence, or hard cost
  gates.
- Public Bybit linear can be provider-blocked by location even when the factor
  cell is otherwise fresh. On 2026-05-24 the Bybit `KAITOUSDT/FARTCOINUSDT`
  momentum-window trend-continuation full-ladder runner saw all
  `1m/5m/15m/30m/1h/4h/1d` fetches exit `1` with CloudFront HTTP `403`
  country blocking and retained `0` rows. Classify that as
  `blocked_provider_runtime_no_candles`, not a factor verdict. Before spending
  a fresh Bybit public lane, run a tiny reachability/symbol preflight on one
  symbol/timeframe; if the block repeats, pivot to Kraken public, retained-real,
  or another available provider rather than creating another full-ladder Bybit
  provider-blocked packet.
- Kraken momentum-window trend-continuation can still collapse to higher-frame
  context only. The 2026-05-24 `ROSEUSD/QTUMUSD` run proved two reusable
  details: `ROSEUSD` is not a valid Kraken spot pair in this fetch path
  (`EQuery:Unknown asset pair`), while `QTUMUSD` fetched all
  `1m/5m/15m/30m/1h/4h/1d` frames and completed strategy compile plus
  Auto-Quant batch/dispatch/rank with rooted `TrendExpansion` metadata
  preserved. Exact `QTUMUSD/1m` had zero trades and no hard `5bps/side`
  survivor; only `QTUMUSD/4h` survived as context (`2` trades, raw `+1.79%`,
  `5bps=+1.59%`). Treat this as a clean Gate 1 negative/context sample: do not
  downstream the failed `1m` origin and do not repeat ROSE/QTUM momentum-window
  trend unless directly repairing dense exact `1m` entry formation after a
  symbol-validity preflight.
- Before promoting low-timeframe intraday factors, run per-side cost stress at 0/1/2/5bps minimum. If the edge flips negative at 1-2bps/side, classify it as incubate/research evidence even when the raw or HTF-veto backtest is positive. The Donchian/RVOL QQQ 1m example is documented in `references/regime-rooted-branch-and-cost-stress.md`.
- Futures-cost survival must use a verified product-specific cost model, not an
  inherited `5bps/side` default. Clean-AQ and Auto-Quant wrappers must compute
  downstream eligibility from a declared and verified cost model, positive trade
  count, branch identity, direction, and diversity; do not require a `1/day`
  density floor, do not name an instrument-cost-only row `survivors_5bps`, set
  `gate1_survivor=true`, or allow Pre-Bayes/BBN/CatBoost/execution-tree handoff
  from an unverified fee assumption. Historical packets may include 1/2/5bps
  stress rows, but for new futures work those rows are slippage/stress telemetry
  unless the commission model is separately verified per contract.
- Stock/ETF/options-cost survival must also be source-backed. US single-stock
  fees cannot be copied into HK/EU/JP/A-share stocks; ETF schedules cannot be
  assumed from equities when domicile, venue, currency, borrow/financing,
  product class, or broker routing differs; options cannot inherit stock/ETF
  fees at all. Before promotion, require a recorded official source for the
  broker/exchange/regulatory fee schedule, pricing plan, currency, effective
  date, minimums/caps, and per-share/per-contract/per-order convention. Missing
  any field means `cost_model_unverified` and no practical handoff.
- Simulated-admission writers must not reopen downstream feedback merely because
  import/analyze/ranker/workflow commands exited `0`. For an exact-root branch,
  derive `downstream_allowed`, `pre_bayes_allowed`, `bbn_allowed`,
  `catboost_allowed`, and `execution_tree_allowed` from command success plus
  explicit source exact cost survivors with positive trade count. Preserve
  the canonical `branch_path` in both top-level metrics and nested
  `selected_gate1_row`; move legacy strings such as
  `FUTURES -> precious_metals -> SI -> 5m -> ...` into
  `original_branch_path`/provenance labels. The SI `5m`
  `RangeConsolidation -> TightRangeBandExpansionFade` true-1m-context repair on
  2026-05-24 produced a contract-clean packet only after `symbol=SI`,
  `timeframe=5m`, `workflow_symbol=<ICT symbol>`, and
  `downstream_gate_source=source_exact_5bps_survivors_and_command_exits` were
  emitted separately.
- Simulated/paper/retained feedback admission readbacks should emit
  machine-readable blocker categories, not only a flat violation list. Current
  no-provider guard output includes `blocker_categories` and
  `next_action_keywords` for `root`, `mtf`, `frequency`, `cost_5bps`,
  `trade_count`, `provider_parity`, `validation`, and `execution_readiness`.
  Use these categories to decide the next no-provider prep or backend launch:
  fix branch identity first, then real MTF resonance, exact positive
  `5bps/side` rows with positive trade count, provider parity, validation rows,
  and execution readiness. Do not treat a simulated or retained feedback bundle
  as promotion/trade evidence because the classifier shows only one category is
  blocked; all categories must be satisfied by real or retained-real evidence
  and current downstream contracts before admission.
- Retained-real MIM cost-window Gate 1 reports must enforce the user's event
  cadence before `auto_quant_gate1_ready=true`: max inter-event gap defaults to
  `3` days and max events/trades per day defaults to `3`. The report should
  emit a `frequency` object and blockers such as `missing_event_timestamp`,
  `trades_per_day_gt_max`, and `max_gap_days_gt_allowed`; if any are present,
  classify the packet as observation/repair rather than launching AQ readiness.
  This frequency gate applies to source-backed event bundles before provider/AQ
  launch, not only to simulated-feedback admission.
- Retained-real MIM feedback rows must preserve lossless branch depth beside
  the fixed regime/profit fields. Emit `branch_path_segments`,
  `branch_path_depth`, and `branch_path_leaf` from the canonical
  `branch_path`; do not infer arbitrary-depth overlays only from
  `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and
  `profit_factor`. Nested profit-factor suffixes must remain inspectable
  through feedback/update inputs without flattening the regime-rooted branch.
- Auto-Quant real-trade feedback training exports must keep the same lossless
  branch-depth contract before feeding BBN/CatBoost/training rows. In addition
  to `regime_profit_branch_path`, `main_regime`, `sub_regime`,
  `sub_sub_regime_or_profit_factor`, and `profit_factor`, emit
  `branch_path_segments`, `branch_path_depth`, and `branch_path_leaf` in the
  training row/CSV so later learners can distinguish recursive profit-factor
  overlays without reparsing fixed-depth fields.
- Source-backed MIM/triple-barrier prep can still fail the hard economics gate
  after Auto-Quant. The retained-real IBKR `EXR/1m`
  `TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter`
  packet had cadence-clean events and AQ completed with 15 trades, raw `+1.19%`,
  `1bps=+0.89%`, and `2bps=+0.59%`, but failed hard `5bps/side` at `-0.31%`.
  Treat this as a clean Gate 1 negative/observation: no Pre-Bayes, BBN,
  CatBoost, execution-tree, promotion, or trade-use handoff unless a future
  exact-root MIM variant survives `5bps/side` with positive trade count.
- The current source-backed repair for thin-edge MIM-like events is the
  `cost_aware_triple_barrier_meta_gate_v1` seed in
  `support/scripts/research/factor_formula_library.py`, derived from
  FinMLKit-style `min_ret` triple-barrier/meta-labeling and this repo's hard
  `5bps/side` gate. Use it as a pre-admission gate (`min_ret_bps` must cover
  round-trip cost plus slippage/edge buffers and `p_hat >= p_min`) before
  sending a primary event family downstream; do not repeat EXR MIM overlays
  unless the exact-root event set first clears this cost-aware gate.
- If real provider fetch, strategy compile, and Auto-Quant all succeed but the 1m-origin lane has no positive cost-stressed rows after 1-2bps/side, stop at Gate 1 (`drop_small_cycle` or negative/suppression sample). Do not run Pre-Bayes/BBN/CatBoost/execution-tree, and do not add overlays to rescue a sparse root; overlays only stack after the first profit factor has earned evidence. See `references/regime-rooted-gate1-cost-density-negative-sample.md`.
- Classic Elder/MACD impulse can satisfy factor-diversity coverage without satisfying practical economics. The IBKR `MES/1m` Elder/MACD impulse packet on retained real `MES 202606` `1m` `7 D` rows completed provider-status, strategy compile, Auto-Quant material batch, dispatch, and rank with exact branch fields preserved, but all rows lived inside the friction envelope: best quality row had `4` trades, raw `+0.12%`, `1bps=+0.04%`, `2bps=-0.04%`, and `5bps=-0.28%`; denser rows were already negative by `1bps/side` or raw. Treat this as a clean Gate 1 negative: do not downstream low-excursion impulse variants or clone them across symbols unless the new hypothesis materially widens per-trade excursion before cost stress.
- For options/profit-factor timeframe ladders, run each IBKR timeframe as its own Auto-Quant Gate 1 lane, downgrade only the provider-window lane that times out, and move the strongest cost-stressed cross-symbol candidate into tree handoff without over-claiming live-readiness before validation row gates mature. See `references/ibkr-options-timeframe-ladder-tree-handoff.md`.
- For new live-profit factor training, prefer a single specific branch root per market/instrument/symbol/timeframe/regime/profit-factor. Start from `1m` when feasible, but treat each specific timeframe as an independent profit-factor lane: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, and `1d` each need their own provider/AQ/Gate 1/cost/downstream decision. Other timeframes are context/neutralization/confirmation/suppression for that lane, not proof that can be flattened into or against the lane. A failed `1m` sibling does not automatically fail a positive `5m` lane; a positive `30m` sibling does not promote a failed `1m` lane. Report ladder results as per-timeframe terminal decisions first, then cross-timeframe summary.
- When a run reports all downstream gates false, reverse the booleans into missing prerequisites before choosing the next candidate. If `pre_bayes_allowed=false`, `bbn_allowed=false`, `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, or `trade_usable=false`, diagnose which exact rooted-path property failed: cost-stressed density, rooted metadata, same-root survivor, mature labels, exact path admission, provider parity, or execution readiness. See `references/gate-bool-reverse-and-timeframe-root-parity-20260519.md`.
- When asked whether a practical/live-ready factor exists or to tune all candidates, inspect candidates repo-wide, not just the current run. Rank by live-readiness gates (`trade_usable`/`promotion_allowed`/`actionable`, mature/production/observation rows, execution tree status, cost stress, provider parity), then tune the nearest blocker. Mature ranker rows without execution admission are still fail-closed; strong YF AQ profit without IBKR/TVR parity and validation rows is still candidate-only. See `references/full-repo-candidate-to-live-readiness.md`.
- For additive `auto-quant-agent-material-batch` experiments, pass a known local Auto-Quant checkout with `--repo-url <local-auto-quant-path>` when available. If omitted, the managed dependency path may try a fresh GitHub clone under the run state; classify that as a bootstrap/provenance blocker, not a factor verdict.
- A zero-trade Auto-Quant ladder with successful backtest exits is a factor-gate failure, not a provider failure; downstream tree readback may prove fail-closed parity but MUST NOT be described as promotion/readiness.
- When an exact-root futures short factor is handed to Auto-Quant, do not let the
  managed harness silently run it as spot or as an unrelated long proxy. For
  Freqtrade-style synthetic futures in `<managed-auto-quant-checkout>`, the direct
  probe needs `config.tomac.json` set to futures/isolated mode, retained OHLCV
  bridged into `user_data/data/futures/<PAIR>-<tf>-futures.feather`, and a
  synthetic leverage tier with exchange-specific keys such as `maintAmt` before
  `run_tomac.py` can produce a real short-side verdict. The 2026-05-20 IBKR
  `M2K/1m` reject-short RVOL/PDA direct strategy proved this path mechanically:
  `IbkrM2KRejectShortRvolPdaGuard` ran exact M2K futures rows with 19 shorts,
  63.1579% win rate, raw `+2.60%`, and 5bps/side `+0.70%`. Treat this as a
  Gate 1 cost-density survivor only; prior same-root downstream still failed
  closed on execution predicates, so do not call it practical until the exact
  branch also materializes an execution candidate and the current execution
  contract shows acceptable readiness, ranker, and maturity state.
- If a TOMAC/XAU/NQ/GC synthetic futures workspace fails before economics with
  `OperationalException: Pairs ... got no leverage tiers available`, classify it
  as `backend_config_blocked_no_factor_verdict`, not as factor-negative. The
  canonical no-runtime repair is to patch the copied workspace `run_tomac.py`
  before launch so `_build_exchange_with_synthetic_pairs(...)` injects a
  `_synthetic_leverage_tiers(...)` helper and assigns
  `exchange._leverage_tiers[pair]` for every futures pair. Add or run focused
  tests proving generated workspaces contain both `_synthetic_leverage_tiers`
  and `exchange._leverage_tiers[pair]`. Do not patch the shared Auto-Quant
  checkout as a substitute for wrapper-owned generation, and do not relaunch AQ
  while compact audit reports foreign active claims or live runtime owners.
- Local/vectorized condition diagnostics are candidate-discovery only. If a
  weekday, volatility, relative-volume, or sector filter looks better in a
  standalone diagnostic, rerun the filtered rule through Auto-Quant before
  claiming improvement; if AQ rank is unchanged or still mixed, terminalize it
  as a failed filter rather than promoting the diagnostic.
- VIX/VIX3M sidecar proxies can be useful as options-volatility context, but
  they are not real historical options-chain IV/HV proof. If a VIX-term-structure
  or VRP proxy packet produces dense but all-negative AQ rows, terminalize it as
  a negative options-proxy sample and do not promote it into the real IV/HV branch
  or downstream chain.
- Short-horizon options-proxy/MACD overlays can look excellent before costs but fail under tiny execution friction. Before promotion, always run walk-forward plus per-side slippage stress (at least 1bps/2bps/5bps) across older years and the apparent winning window. If a 5m strategy flips from PF>1 to PF<1 at 2bps/side or fails 2023-2025 walk-forward, classify it as regime-specific research evidence, not live-practical alpha.
- Paper- or open-source-derived strategy ideas still need the same AQ Gate 1
  portability proof as native ideas. If a paper strategy such as first-half-hour
  intraday momentum only passes one sibling ETF while another sibling is negative
  or a provider fetch is missing, keep it as a sourced negative/mixed sample and
  do not promote it downstream.
- For external alpha intake, prefer source-backed candidates that become exact
  Auto-Quant materials quickly. Papers/repos/blogs/social posts are only idea
  sources until provider rows, rooted material fields, AQ ranks, cost stress, and
  (when earned) downstream readbacks exist. If a paper-backed factor is positive
  only on medium timeframes while `1m` origin has zero trades, keep it as scoped
  seasonal/medium-timeframe evidence, not 1m execution proof. The TOD slot-alpha
  pattern and its CatBoost single-class downstream blocker are documented in
  `references/source-backed-tod-slot-alpha-autoquant.md`.
- Yahoo intraday windows need a safety margin, not a wall-clock `now - 60 days`
  boundary. For `5m`/`15m`/`30m` factor ladders, request inside the last-60-day
  service window, such as 59 days or explicit retained trading dates; exact
  60-day UTC ranges can fail with HTTP 422 before any factor or AQ verdict.
- Provider-status readiness is not direct-fetch proof. If yfinance/Yahoo chart
  fetches fail with HTTPS/SSL EOF while provider-status still says ready, classify
  the fresh leg as a provider reachability/window blocker. A retained same-symbol
  cache can be used to exercise Auto-Quant, Pre-Bayes/BBN, CatBoost, and execution
  mechanics only when artifacts explicitly mark `local_cache_replay=true` and do
  not claim fresh-provider parity or promotion.
- The same direct-fetch rule applies to IBKR. `provider-status --provider ibkr`
  can return ready while every `fetch_external.py ibkr-historical` leg exits `3`
  with `reqHistoricalData: Timeout`, `WARN: ibkr historical empty`, or client-id
  conflict/fallback messages such as `clientId ... already in use`. Treat this as
  `provider_blocked_no_rows` / provider-authority evidence, not a factor verdict
  or an AQ backend verdict. If two adjacent IBKR stock ladders fail this way,
  stop launching more fresh IBKR stock lanes until the live historical fetch path
  is healthy; use readbacks, retained-real packets, or a different provider/cell
  instead. Do not downstream, simulate-admit, or cost-rank a packet with zero
  provider rows and zero materials. Use
  `support/scripts/auto_quant_external/ibkr_provider_guard.py` to classify
  `provider_blocked_no_rows_no_materials` before any material build or AQ step.
  After two or more adjacent zero-row IBKR stock ladders or known-good stock
  probes, pass that count as `recent_blocked_ladders` and honor
  `provider_cooldown_after_repeated_no_rows` / `cooldown_recommended=true` as a
  hard stop for fresh full-ladder IBKR stock launches until a known-good
  preflight writes nonzero rows.
- Before treating a fresh IBKR stock failure as market-specific, verify the
  current fetch script itself compiles and then run a tiny direct health probe
  against a liquid stock/ETF such as `SPY STK SMART/ARCA 1 min 1 D` with a
  bounded `--request-timeout`. On 2026-05-24, LHX, LULU, LII, and this SPY
  probe all returned `reqHistoricalData: Timeout` / empty rows while
  provider-status stayed ready; that means pause fresh IBKR stock lanes and do
  retained-real/readback/futures-or-other-provider work until historical fetch is
  demonstrably healthy. Also run `python3 -m py_compile
  support/scripts/auto_quant_external/fetch_external.py` before the probe if the
  file is dirty, because a half-applied chunking edit can fail before provider
  code runs and would otherwise be misclassified as an IBKR outage.
- For shell wrappers or `/tmp` Gate 1 runners, prefer
  `support/scripts/auto_quant_external/ibkr_provider_guard.py --fail-on-blocked`
  before material build or Auto-Quant. It still prints the JSON verdict, but
  exits `2` when recorded artifacts do not prove provider rows are ready, so
  repeated zero-row/cooldown states can fail closed instead of drifting into
  another launch.
  For fresh IBKR stock ladders after a known repeated-timeout cluster, pass
  `--require-known-good-preflight` plus one or more `--known-good-row-csv`
  handles from a liquid stock/ETF probe. If those known-good CSVs are absent or
  zero-row, honor `known_good_preflight_missing_no_rows` as a hard prelaunch
  stop before any target-symbol fetch, material build, Auto-Quant, or
  downstream step.
- IBKR historical CSVs from `fetch_external.py` commonly use `ts` as the time
  column, not `timestamp`. Provider preflight row counters and normalizers should
  accept `timestamp`, `time`, `datetime`, `date`, and `ts`; otherwise a fully
  successful IBKR fetch can be mislabeled as zero-row provider failure. The UUP
  dollar ETF preflight produced nonzero rows on every ladder frame only after
  repairing the counter to include `ts`.
- For Auto-Quant agent-material packages, `timerange` must be a valid Freqtrade
  range such as `20260320-20260516`; prose like `max feasible window` causes all
  lanes to fail with `ConfigurationError: Incorrect syntax for timerange`. Put
  provenance/window notes in metadata, not the `timerange` field.
- When a retained-real local smoke has positive hard-cost evidence and already
  has event/context artifacts, but a different provider/backend lane is still
  active, it is valid to advance only the no-provider material bundle prep in
  `/tmp`. Preserve canonical regime-root branch metadata, compile/check the
  generated strategy/material JSON, and terminalize with
  `provider_fetch_started=false`, `auto_quant_started=false`,
  `downstream_allowed=false`, `promotion_allowed=false`, and
  `trade_usable=false`. Do not describe this prep as Auto-Quant Gate 1, provider
  parity, downstream admission, or live readiness; the next step remains a
  collision-free AQ dispatch or provider-parity replay.
- When reusing a `/tmp` Gate 1 wrapper as a template for a new symbol/product
  cell, override both metadata and artifact filename prefixes before launch. A
  valid command can still fetch the new symbol while raw/normalized CSV names
  inherit the old template symbol; classify the run from command output and
  material metadata, but record the hygiene defect and fix the template before
  reusing it again.
  Identity validation must assert both provider request identity and artifact
  prefix identity: `--symbol`, `AQ_SYMBOL`, `FACTOR_ID`, branch path, raw output
  filename prefixes such as `ibkr_<symbol>_<tf>_<window>.csv`, normalized CSV
  prefixes, material filenames, and package ids. If the provider command says
  `--symbol LHX` but raw paths still say `ibkr_onon_*`, treat it as a
  template-hygiene defect to repair before any new launch or terminal write.
- For Freqtrade trailing-stop materials, `trailing_stop_positive_offset` must be
  strictly greater than `trailing_stop_positive`; equality fails before factor
  scoring with `ConfigurationError`. Low-timeframe tiny ROI lanes need explicit
  smaller trailing positive values.
- If structural path-ranker CatBoost training fails because all features are
  constant or only one mature training sample exists, treat the CatBoost gate as
  attempted-but-not-trained. Apply/register the `--allow-direct-fallback` weighted
  feature model only as `candidate_set_only`; do not mark live-ready until row
  gates mature (normally >=30 raw-scored mature and validation rows).
- If CatBoost technically trains using fallback pseudo-labels while
  `mature_rows=0` or validation rows are `0/30`, classify it as mechanical tree
  exercise only: `candidate_set_only`, not live-ready. A trained `.cbm` is not
  sufficient without mature raw-scored, production, and observation validation
  gates.
- If `pandas_path_ranker_trainer.py --apply` fails because a CatBoost `.cbm` exists but the active Python cannot import `catboost`, rerun the apply step with a CatBoost-capable Python (on this host `/opt/anaconda3/bin/python3`) before classifying the downstream gate. After apply succeeds, refresh workflow/pre-Bayes/policy readbacks and still fail closed unless the current execution contract shows exact-root actionable status, sufficient readiness, acceptable transition/guard state, mature validation, and ranker consumption. See `references/catboost-apply-env-and-post-apply-failclosed.md`.
- If post-ranker `analyze` hangs after the ranker apply/register/enable steps, kill or timeout that specific analyze run, then classify from the same state dir's refreshed `workflow-status`, `pre-bayes-status`, `policy-training-status`, execution candidate, and execution tree readbacks. Mark the analyze timeout separately; do not let it hide fail-closed gate evidence.
- If an exact Auto-Quant replay wrapper leaves `terminal_metrics.json` stuck at
  a prepare-only state while `run_tomac.exit=0` and `command-output/run_tomac.out`
  contain a completed backtest, classify the factor from the command exit and
  stdout rather than from the stale metrics file. Record the wrapper hygiene bug
  separately and still enforce per-side cost stress before downstream. The Tomac
  shifted-MTF `1m` replay had `338` trades and gross `+30.36%`, but cost stress
  was only `2bps/side` positive and failed `5bps/side`, so it stayed
  observation-only despite the stale prepare metrics.
- For Board A/root-regime evidence, `/tmp`, `/private/tmp`, and ignored repo
  `runs/` roots are audit handles only, not durable consumer surfaces. If a
  regime classifier, Trend-root supplement, posterior audit, or `95%` bull/bear
  confidence calibration should be reused, summarize it into a tracked compact
  packet outside ignored paths and update the Board A current doc to point at
  that packet. Do not open a profitability-factor lane when the task is to run
  or preserve regime factors. See
  `references/regime-evidence-packet-persistence-20260523.md`.
- A very strong exact Gate 1 survivor is still not practical if downstream
  cannot materialize same-root workflow/analyze/execution state. The Tomac
  `NQ/1m` OR15 breakout replay survived `5bps/side` with `1283` trades and
  `+217.60%`, but downstream seed analyze ended by signal/timeout, workflow
  stayed `no_workflow_state`, the structural candidate pivoted to bootstrap
  readiness, and validation was only `raw_scored_mature=1/30` with no execution
  tree/candidate. Treat such packets as execution-materialization repair leads:
  do not promote, simulate-admit, rerun Gate 1, or lower transition/PDA/readiness
  gates.
- If a futures exact-root branch is a real Gate 1 survivor but downstream `analyze` times out before execution materialization, complete the verdict from manual readbacks instead of relaunching duplicate wrappers indefinitely. The IBKR `M2K/1m` liquidity-sweep reject-short packet had a genuine cost survivor (`quality`: 32 trades, raw `+3.33%`, `2bps=+2.05%`, `5bps=+0.13%`), but the downstream root only became classifiable after manual `workflow-status --refresh`, `pre-bayes-status --refresh`, `policy-training-status`, and `export-structural-path-ranking-target` readbacks. Ranker runtime was enabled/ready, yet closed-loop admission stayed `fail_closed`, no exact execution candidate/tree materialized, and validation was only `mature_rows=1`, `history_mature_rows=1`, `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=0/30`. Treat this as the nearest same-root repair candidate, not trade-usable alpha; next work needs mature feedback plus exact execution candidate/tree materialization before testing the current hard execution contract.
- A clean exact-root downstream with every command exiting `0` can still be a
  hard fail-closed verdict. The retained-cleaned IBKR `SI/15m` Turtle Soup
  false-breakout reversal had two real-cost Gate 1 survivors (`balanced`:
  7 trades, raw `+2.39%`, `5bps=+1.69%`; `dense`: 16 trades, raw `+1.91%`,
  `5bps=+0.31%`) and completed Auto-Quant import/prior, seed/final analyze,
  Pre-Bayes, CatBoost train/apply/register, runtime enable, workflow, policy,
  and final export with exits `0`. Exact branch survival was true, but final
  admission stayed `fail_closed` with `execution_candidate_actionable=false`,
  `execution_readiness=0.4226`, `transition_hazard=0.9659`,
  `pda_hybrid_alignment=false`, and validation rows `0/30`. Treat SI Turtle
  Soup as observation/repair evidence only until fresh-provider parity,
  same-root mature validation, readiness, and ranker/materialization gates
  pass together. See `references/si15m-turtle-soup-downstream-failclosed-20260520.md`.
- Current-state/regime-root matching can improve Gate 1 and exact ranker visibility, but it is not enough for practical admission. The IBKR `SI/5m` `RangeConsolidation -> TightRangeBandExpansionFade` branch fixed the earlier SI root/current-state mismatch and produced two retained-real `5bps/side` survivors (`dense_fade`: 9 trades, raw `+2.23%`, `5bps=+1.33%`; `quality_fade`: 7 trades, raw `+1.16%`, `5bps=+0.46%`). Exact downstream then reached CatBoost/path-ranker visibility on the same rooted path (`raw_path_score=0.7506586567765241`) and registered a true `model_family=catboost`, but `analyze` timed out, no exact execution candidate/tree materialized, `mature_rows=0`, `history_mature_rows=0`, `execution_readiness=0.0`, `transition_hazard=1.0`, and `pda_hybrid_alignment=false`. Treat this pattern as a strong observation and same-root maturity/execution-materialization repair lead only. Do not call a cost-surviving RangeConsolidation branch practical until final `analyze`/execution candidate exists and the hard predicate trio passes.
- A clean same-root SI `RangeConsolidation -> TightRangeBandExpansionFade` downstream can clear the prior analyze-timeout/mechanics uncertainty and still fail practical admission. The fresh-retained IBKR `SI/5m` packet `20260520T154206` again kept two `5bps/side` survivors (`dense_fade`: 9 trades, raw `+2.23%`, `5bps=+1.33%`; `quality_fade`: 7 trades, raw `+1.16%`, `5bps=+0.46%`) and exact downstream `20260520T154505` completed import/prior, both analyze passes, workflow, Pre-Bayes, CatBoost train/apply/register, runtime enable, policy, and final export with all exits `0`. Exact branch survived and ranker score was visible, but admission stayed `fail_closed`: execution candidate `no_trade`, `mature_rows=0`, `history_mature_rows=0`, `execution_readiness=0.4445`, `transition_hazard=0.9519`, and `pda_hybrid_alignment=false`. Treat this as observation-only proof that cost density plus clean mechanics are insufficient; the next same-root repair must add acceptable mature/current validation and repair active readiness/ranker/materialization predicates. Transition hazard and PDA remain telemetry unless current source reintroduces them as blockers.
- Same-root simulated feedback can repair an SI `RangeConsolidation` branch from missing execution materialization into concrete fail-closed evidence, but it still is not promotion. The IBKR `SI/5m` `TightRangeBandExpansionFade` dense-fade survivor ingested `9` same-Auto-Quant-workspace simulated trades (`7` wins / `2` losses), completed import/prior/analyze/trade-ingest/export/policy/CatBoost/apply/register/runtime/readbacks with usable artifacts, and preserved the exact rooted path. It improved validation from zero to `mature_rows=2`, `history_mature_rows=10`, exact branch score `raw_path_score=0.850627707257148`, and `raw_scored_mature=10/30`, but final admission stayed `fail_closed`: execution candidate `no_trade`, `execution_readiness=0.2344`, `transition_hazard=0.9680`, `pda_hybrid_alignment=false`, `ranker_validation_ready=false`, and path-ranker score not visible/used by the execution tree. Treat this as a stronger observation/repair lead only; the next same-root work must add real or acceptable mature feedback density and repair readiness, ranker consumption, and execution materialization instead of repeating simulated feedback or lowering gates.
- Same-root simulated-trade admission can repair validation visibility but is not
  a promotion shortcut. The IBKR `M2K/1m` liquidity-sweep reject-short quality
  survivor exported and ingested `32` same-Auto-Quant-workspace simulated trades
  (`18` wins / `14` losses), improved history validation
  (`history_mature_rows=35`, ranker validation ready, exact branch survived),
  and made the CatBoost score visible to execution. It still failed closed with
  `mature_rows=3`, `execution_candidate_status=no_trade`,
  `execution_readiness=0.3181`, `transition_hazard=0.9185`,
  `pda_hybrid_alignment=false`, and `path_ranker_score_used_by_execution_tree=false`.
  Treat simulated feedback as a maturity/readback repair tool only; promotion
  still requires current mature rows plus exact execution admission and the hard
  execution predicates.
- A same-root simulated-admission run that enables CatBoost runtime is still
  fail-closed when analyze cannot materialize the execution state and validation
  rows stay below gate. The IBKR `M2K/1m` RVOL/PDA consistency-floor admission
  ingested `17` same-workspace simulated trades (`11` wins / `6` losses),
  trained/applied CatBoost, registered the true `model_family=catboost`, and
  enabled runtime with `2` active matches, but both analyze passes timed out and
  final metrics were `exact_branch_survived=false`, `mature_rows=2`,
  `history_mature_rows=18`, `raw_scored_mature=18/30`,
  `production_validation=17/30`, `observation_validation=17/30`,
  `execution_readiness=0.0`, `transition_hazard=1.0`, and
  `pda_hybrid_alignment=false`. Treat this as terminal observation only; the
  next same-root repair needs enough mature same-root feedback to clear the
  `30/30` validation gates plus exact execution-candidate materialization,
  not another simulated-feedback replay or lower thresholds.
- Same-root simulated feedback can materially repair execution materialization
  and still remain below the full practical/live standard. The IBKR
  `ETN/5m` Gann HiLo quality survivor ingested `123` same-Auto-Quant-workspace
  simulated trades, made the exact execution candidate actionable
  (`execution_ready`), reached `execution_readiness=0.67`,
  `transition_hazard=0.3693`, `pda_hybrid_alignment=true`,
  `ranker_validation_ready=true`, and got the path-ranker score used by the
  execution tree. Fresh policy readback showed `raw_scored_mature=127/30`,
  `production_validation=127/30`, and `observation_validation=123/30`, so the
  remaining stop is full practical extension plus consumed/entry-model
  validation, not ranker maturity. A follow-up retained-real full-MTF replay
  over `1m/5m/15m/30m/1h/4h/1d` preserved branch-local admission
  (`execution_readiness=0.67`, `transition_hazard=0.3604`,
  `pda_hybrid_alignment=true`, ranker score visible and used). Treat this as
  `branch_local_admitted_extension_candidate`: next work needs sibling,
  product, provider, consumed-validation, and entry-model breadth plus
  `extension_complete=true`, not another full-MTF or simulated-feedback replay
  or gate lowering. See
  `references/etn5m-gann-hilo-simulated-admission-validation-blocker-20260524.md`.
- When retained IBKR multi-timeframe Gate 1 packages encode both timeframe and
  provider window in `package_id`, parse labels from the strategy segment, not
  by naive substring membership. For example `...-15m-1m-v1` means `15m`
  timeframe with a `1 M` window; matching `-1m-` first mislabels the row and can
  create false 1m survivor claims. If a higher-timeframe sibling such as XOP
  `4h` survives `5bps/side` while `1m`/`15m`/`30m` fail or only survive
  `2bps/side`, downstream may be scoped to that exact higher-timeframe lane, but
  it still cannot rescue the failed lower-timeframe origin or justify simulated
  trade admission before exact downstream materializes same-root execution
  readbacks.
- A cost-surviving higher-timeframe ETF branch can still fail the user's hard
  practical gates after clean downstream mechanics. The IBKR XOP `4h`
  `RangeReversion -> EnergyEtfWashoutReclaim -> xop_energy_etf_washout_reclaim_v1`
  survivor (`balanced`: 39 trades, raw `+4.16%`, `5bps=+0.26%`) completed AQ
  import/prior, analyze, workflow, Pre-Bayes, CatBoost train/apply/register,
  runtime enable, policy, and final export with exits `0`, but downstream
  selected a bearish `no_trade` execution candidate while the Gate 1 material was
  long. Final predicates were `execution_readiness=0.3138`,
  `transition_hazard=0.9036`, and `pda_hybrid_alignment=false`. Treat this as
  observation only; do not simulate-admit or promote until a same-root repair
  preserves direction and clears the hard transition/PDA/readiness gates.
- When a simulated-trade or downstream wrapper trains a CatBoost path-ranker,
  register the trainer artifact with the artifact's true `model_family`. Do not
  copy an older `weighted_feature_sum_v1` registration line when
  `trainer_artifact.json` says `model_family=catboost`; the CLI will reject the
  mismatch. If this happens, manually re-register as `catboost`, refresh
  workflow/policy readbacks, patch the wrapper, and keep the factor verdict tied
  to execution predicates rather than the wrapper hygiene bug.
- Simulated same-workspace trade feedback is a repair probe, not a promotion shortcut. In the IBKR `M2K/1m` liquidity-sweep reject-short simulated-trade admission repair, ingesting `32` simulated trades improved readback maturity to `mature_rows=3` and `history_mature_rows=35` and made ranker validation visible, but the branch still failed closed because trainer registration exited non-zero, the execution candidate stayed `no_trade`, `execution_readiness=0.3181`, `transition_hazard=0.9185`, `pda_hybrid_alignment=false`, and the path-ranker score was visible but not used by the execution tree. Preserve such packets as same-root execution-repair leads only; do not call them live-ready unless real or acceptable feedback, trainer registration, exact execution candidate materialization, ranker consumption, and execution readiness all pass together. Transition hazard/PDA values are telemetry in the current schema.
- For same-root simulated-trade feedback wrappers, keep the ingest `--source`
  training-consumable by starting it with `auto_quant_real_trades` while retaining
  explicit provenance such as `auto_quant_real_trades:simulated_backtest:<lane>`.
  A plain `simulated_backtest:<lane>` source is inserted into learning state, but
  `auto_quant_real_trade_feedback_*_training.csv` filters it out and leaves BBN /
  CatBoost feedback rows at zero. When reporting wrapper terminal metrics, read
  validation counts from `policy_after_ranker.structural_path_ranking_validation`
  before falling back to sparse target summaries, or the run can falsely print
  `raw_scored_mature_rows=0` even when policy readback shows `12/30`.
- A retained-real public linear-regression-channel branch can be a true Gate 1
  cost survivor and still remain observation-only. The IBKR `SI/5m` LinReg
  retest row survived `5bps/side` (`9` trades, raw `+1.28%`, `2bps=+0.92%`,
  `5bps=+0.38%`) and exact downstream completed import/prior, Pre-Bayes
  readbacks, structural target export, CatBoost train/apply/register, and runtime
  enable. Both analyze calls timed out, validation stayed `mature_rows=0`,
  `history_mature_rows=0`, `raw_scored_mature=0/30`, and execution predicates
  remained `execution_readiness=0.0`, `transition_hazard=1.0`,
  `pda_hybrid_alignment=false`. Treat this as useful public-family cost evidence,
  not practical alpha; do not clone the same SI `5m` channel shape unless the new
  hypothesis directly repairs exact execution materialization, mature feedback,
  or the transition/PDA blocker trio. See
  `references/si5m-linreg-cost-survivor-downstream-failclosed-20260520.md`.
- The same repair-probe rule applies when all mechanics do exit `0`. The IBKR
  `MNQ/1m` compression-breakout -> VWAP persistence transition-guard survivor
  replayed the same Auto-Quant workspace, ingested `6` simulated trades,
  trained/applied/registered CatBoost, enabled runtime, and preserved the exact
  branch with ranker score visible to execution. It still failed closed with
  `mature_rows=2`, `history_mature_rows=7`, `execution_candidate_status=no_trade`,
  `execution_readiness=0.2313`, `transition_hazard=0.9110`,
  `pda_hybrid_alignment=false`, and path-ranker score not used by execution.
  Treat this as observation only; do not stack another light VWAP/compression
  overlay unless the next hypothesis directly increases same-root feedback
  density or repairs the execution predicate trio. See
  `references/mnq-compression-vwap-sim-feedback-failclosed-20260520.md`.
- A stronger Gate 1 overlay still cannot skip the execution-predicate gates. The
  IBKR `M2K/1m` liquidity-sweep reject-short -> RVOL/PDA guard kept exact-root
  identity and produced four real-cost `5bps/side` survivors on retained real
  IBKR rows (`19` to `31` trades; best `5bps=+0.70%`). Same-root simulated
  admission then completed every command from AQ import through CatBoost train,
  register, runtime enable, analyze, workflow, Pre-Bayes, and policy readback
  with exit `0`; it ingested `19` same-workspace simulated trades and made the
  path-ranker score visible to execution. It still failed closed with
  `mature_rows=2`, `history_mature_rows=20`, `execution_candidate_status=no_trade`,
  `execution_readiness=0.3181`, `transition_hazard=0.9185`,
  `pda_hybrid_alignment=false`, and
  `path_ranker_score_used_by_execution_tree=false`. Treat this as the strongest
  nearby same-root repair lead, not a practical factor: the next experiment must
  directly materialize an exact execution candidate, reduce transition hazard,
  and align PDA. Do not add another light RVOL/VWAP/liquidity overlay or lower
  gates after this pattern. See
  `references/m2k-liquidity-sweep-rvol-pda-sim-feedback-failclosed-20260520.md`.
- A micro-filter can improve Gate 1 density without repairing downstream
  admission. The IBKR `M2K/1m` RVOL/PDA `pda_consistency_floor` variant produced
  a cleaner single real-cost survivor (`17` shorts, `64.7059%` win rate, raw
  `+2.79%`, `2bps=+2.11%`, `5bps=+1.09%`) and same-root simulated admission ran
  every command with exit `0`, ingested `17` trades, preserved the exact branch,
  and made CatBoost/path-ranker visible. Execution predicates were unchanged:
  `execution_candidate_status=no_trade`, `execution_readiness=0.3181`,
  `transition_hazard=0.9185`, `pda_hybrid_alignment=false`, and the ranker score
  was still not used by the execution tree because current market state/PDA
  family alignment disagreed with the branch. Treat this as evidence that the
  next same-root repair must target regime/PDA-family alignment or execution-tree
  candidate materialization, not another same-shape RVOL/PDA/liquidity
  micro-filter.
- A full-MTF clean replay of that same `M2K/1m` RVOL/PDA
  `pda_consistency_floor` root is still not enough when the hard predicates are
  unchanged. The `20260520T182204` simulated-admission rerun ingested `17`
  same-workspace simulated trades (`11` wins / `6` losses), ran all `19`
  import/prior/analyze/feedback/CatBoost/register/runtime/readback commands with
  exit `0`, preserved the exact branch, and supplied analyze coverage for
  `1m/5m/15m/30m/1h/4h` while `1d` was insufficient. It still failed closed:
  `mature_rows=2`, `history_mature_rows=18`,
  `execution_candidate_status=no_trade`, `execution_readiness=0.3211`,
  `transition_hazard=0.9185`, `pda_hybrid_alignment=false`,
  `ranker_validation_ready=false`, and the visible ranker score was not used by
  execution. Treat this as a stop sign for more same-root simulated feedback or
  micro-filters; the next useful work must change PDA/regime-family alignment or
  execution-candidate materialization, or pivot to another cost survivor.
- Auto-Quant autoresearch repair is not enough unless the generated seed
  preserves the exact rooted branch and execution side. The IBKR `M2K/1m`
  RVOL/PDA `pda_consistency_floor` autoresearch repair prepared retained real
  `1m` rows plus derived `5m/15m/30m/1h/4h/1d` context and executed Auto-Quant,
  but the generated seed was a generic `TomacNQ_KillzoneBreakout` long-style
  strategy with zero trades. Classify this as
  `autoresearch_repair_no_candidate_zero_trades`, not as an execution repair or
  live-readiness improvement; the next AQ repair must seed/import the exact
  rooted short/PDA strategy family rather than a generic sibling.
- A clean simulated-feedback rerun can prove the wrapper is fixed while still
  leaving the same economic/execution blocker. The IBKR `SI/15m` Turtle Soup
  clean rerun (`20260520T115328`) had all simulated-admission commands exit `0`,
  ingested `23` same-workspace simulated trades, improved current maturity to
  `mature_rows=2`, and kept `ranker_validation_ready=true`, but still failed
  closed with `execution_candidate_status=no_trade`, `execution_readiness=0.4226`,
  `transition_hazard=0.9659`, `pda_hybrid_alignment=false`, and path-ranker
  visible but not used. The blocker report decision was
  `repair_same_root_pda_sequence_alignment`, with PDA regime-family disagreement
  and weak/low-consistency PDA sequence conflicts. After this pattern, do not
  repeat generic simulated-feedback replay or add light overlays; repair the
  same-root PDA sequence/regime-family evidence, choose an agreeing regime root,
  or pivot to another real `5bps/side` survivor.
- If a `5bps/side` real futures survivor completes same-root simulated-trade
  admission with every command exiting `0`, still inspect the directional and
  regime-family evidence before more feedback ingestion. The IBKR `SI/5m` ATR
  exhaustion short repaired exact-branch survival, CatBoost/ranker visibility,
  and validation readbacks, but execution stayed observe because the current
  market state was `RangeConsolidation/TightRange`, the branch root stayed
  `TrendExpansion -> AtrExhaustionShort`, higher-timeframe bias was bearish
  while the execution candidate selected `Bull`, PDA family disagreed with the
  regime family, and `transition_hazard=0.968`, `pda_hybrid_alignment=false`,
  `execution_readiness=0.234`. Treat this as a direction/regime-root alignment
  repair lead, not a prompt to add another simulated-feedback loop. See
  `references/si5m-atr-sim-feedback-direction-regime-failclosed-20260520.md`.
- Source-backed MGC `1m` oscillator/reclaim variants can be dense but still
  non-practical after real costs. The IBKR `MGC/1m` Relative Vigor reclaim Gate 1
  rewrote a `github.com/cinar/indicator` RVI idea into exact-root AQ material and
  produced `124` total trades on retained real `MGC 202606` `1m` `7 D` rows, but
  every variant was negative raw or after `1bps/side` and there were no
  `2bps/side` or `5bps/side` survivors. Treat RVI as another MGC 1m oscillator
  negative sample alongside Camarilla/Vortex/Williams/MFI-style failures; do not
  downstream or keep retuning it unless the next hypothesis directly increases
  per-trade excursion.
- Public false-breakout and volume-price divergence families still need the
  same density gate as trend and oscillator families. The IBKR `MGC/5m` Turtle
  Soup false-breakout packet completed exact-root AQ materialization/rank on
  retained real `MGC 202606` `5m` `10 D` rows, but its only positive cost-stressed
  row was a single trade (`5bps/side=+0.03%`) while denser rows were negative;
  the IBKR `SI/1m` VPT divergence-reclaim packet completed AQ on retained real
  `SI 202607` `1m` `7 D` rows with `51` total trades, but the dense/balanced rows
  were negative raw and worsened by `1bps/side`. Treat both as clean Gate 1
  negatives: a one-trade positive row is not practical density, and dense
  volume-divergence negatives should not be downstreamed or cloned unless the
  new design materially widens excursion and preserves real-cost trade count.
- Volatility ETP panic-reclaim can look attractive on higher frames while the
  exact `1m` origin is still a clean Gate 1 failure. The IBKR `VXX/1m` Williams
  Vix Fix panic-reclaim packet completed real full-ladder provider fetch,
  Auto-Quant material batch/dispatch/rank, and branch-field preservation, but
  all exact `1m` variants were cost-negative despite 0.7-1.3 trades/day
  (`5bps/side` around `-1.42%` to `-2.05%`). The sibling IBKR `SVXY/1m`
  inverse-volatility packet repeated the pattern with `1m` activity around
  0.87-1.33 trades/day but no `2bps/side` or `5bps/side` density survivor
  (`5bps/side` around `-2.34%` to `-3.46%`). Positive `15m`/`30m` siblings were
  sub-density and cannot rescue the failed origin. Treat this as observation
  evidence for the volatility-ETP family; do not downstream or promote unless a
  future exact-origin variant survives hard 5bps cost and practical density.
- If a same-root simulated-admission rerun completes AQ import, trade ingest,
  CatBoost/ranker train/apply/register, and runtime enable but the analyze legs
  are timeout-killed and final metrics report `exact_branch_survived=false`, do
  not treat the mechanical CatBoost/ranker success as downstream progress. The
  2026-05-20 `M2K/1m` RVOL/PDA rerun ingested `19` simulated same-workspace
  trades and still ended with `mature_rows=2`, `history_mature_rows=20`,
  `ranker_validation_ready=false`, `execution_readiness=0.0`,
  `transition_hazard=1.0`, and `pda_hybrid_alignment=false`. The next repair
  must make the exact branch survive execution readback and materialize an
  execution candidate before optimizing CatBoost/ranker mechanics again.
- If a full retained-window downstream replay times out but a smaller diagnostic
  replay completes, treat the small replay as blocker evidence only, not as a
  promotion substitute. The 2026-05-20 `M2K/1m` RVOL/PDA consistency-floor rerun
  reconfirmed a real `5bps/side` Gate 1 survivor, then the full `7 D` analyze
  timed out; a last-`3000`-row small replay had `exact_branch_survived=true` but
  still failed closed with `pre_bayes_allowed=false`, `bbn_allowed=false`,
  `catboost_allowed=false`, `execution_tree_allowed=false`,
  `execution_readiness=0.1968`, `transition_hazard=0.9487`,
  `pda_hybrid_alignment=false`, `ranker_validation_ready=false`, and PDA
  sequence consistency around `0.357`. Treat this as an execution/PDA-family
  materialization blocker: do not add another light RVOL/PDA/liquidity
  micro-filter, and do not call the branch practical until full replay completes
  and the exact branch clears PDA alignment, transition, readiness, ranker, and
  execution-candidate gates.
- When reusing Auto-Quant experiment scripts as wrappers, check importlib/dataclass
  loading and branch parser assumptions before running. Register dynamically loaded
  dataclass modules in `sys.modules` before `exec_module()`, and do not reuse
  fixed `PARTS[n]` overlay parsing for a shorter independent rooted lane. See
  `references/auto-quant-wrapper-rooted-branch-pitfalls.md`.
- US single-stock lanes must be treated as their own market branch, not as ETF
  evidence. If real individual-stock provider fetches succeed but AQ returns
  sparse or zero-trade rows across sibling stocks, terminalize that exact
  single-stock factor as a Gate 1 failure and try a materially different
  stock-specific condition instead of promoting an ETF surrogate.
- IBKR historical duration strings and FreqTrade/Auto-Quant material `timerange`
  are different contracts. Use IBKR duration strings such as `7 D`, `1 M`, or
  `3 M` only for provider fetch. Derive Auto-Quant material `timerange` as
  `YYYYMMDD-YYYYMMDD` from the fetched CSV timestamps before dispatch; placeholder
  values like `ibkr_available` will fail in FreqTrade before any factor verdict.
- IBKR intraday upper-window fetches can fail per symbol/timeframe even when
  provider-status is ready. If a `5 mins 3 M` request times out for one symbol
  while another symbol succeeds, record it as a provider-window downgrade and
  retry a real smaller upper window such as `1 M`; do not call the factor
  failed until the feasible-window retry has been scored. Verified QQQ upper-window pattern on this host: `1 min 1 M` can fail with exit 3 and should downgrade to `7 D`; `5 mins 3 M` can fail and should downgrade to `1 M`; `15 mins/30 mins/1 hour 3 M` can succeed.
- Auto-Quant rank rows may use `profit_factor` as the branch profit-factor
  identity from `consumer_evidence_profile`, not as a numeric profit-factor
  ratio. Packet summaries must parse numeric PF defensively from an explicit
  numeric ratio field when present, or report it as unavailable, rather than
  coercing the branch string and crashing after AQ already passed.
- When reusing an Auto-Quant material generator as a wrapper template, rewrite
  the material/package namespace as well as the strategy class and branch
  metadata. A stale package id such as `yf-staples-*` inside a fresh tanker or
  analog-chip branch blocks downstream portability even if branch fields and
  `profit_factor` identity are otherwise preserved. Terminalize as a namespace
  blocker or rerun with corrected package ids before Pre-Bayes/BBN/CatBoost/tree.
- A live-practical factor that passes exact rooted gates should become a reusable
  mother-template, not sit idle as a one-off packet. Expand it by cloning the
  factor logic into nearby market cells, but treat every clone as a new exact
  rooted branch: rewrite market/product/symbol/base timeframe/regime path,
  `package_id`, strategy class, artifact names, provider provenance,
  `branch_path_for_spec`/`branch_identity_for_spec`, and any downstream wrapper
  symbols before running Gate 1. Use a staged expansion ladder: same market and
  similar microstructure first, then same market different product class, then a
  different provider/market. A clone is useful only if it survives its own real
  provider rows, cost/density gate, exact-root downstream replay, and execution
  predicates; sibling or aggregate success from the mother factor is transfer
  evidence, not promotion proof.
- Before spending a full downstream replay on a mother-template clone, run a
  clone-identity hygiene check over scripts, generated material libraries,
  summaries, real-trade extractors, command names, source labels, and metric
  decisions. No stale mother symbol/timeframe/factor strings should remain in
  evidence fields except in explicit `derived_from` provenance. A cloned OKTA
  branch that still writes CRWD in summary headings, market/product lines,
  extractor names, source tags, or decision ids is not invalid as a factor result
  if rooted branch fields and input data are correct, but it is evidence hygiene
  debt; patch the wrapper before using that packet as a reusable template.
- Treat a proven mother-template as an impact-radius asset, not a static trophy.
  Build a small portfolio of exact-root clones around it and track both winners
  and failures: a clone that passes Gate 1 expands the template's usable radius;
  a clone that keeps density but fails execution tells you which blocker overlay
  to test next; a clone that loses density or cost survival marks the boundary of
  that template. Do not keep copying blindly after two adjacent cells fail for
  the same structural reason; either repair the blocker under the best same-root
  clone or switch to a materially different mother-template.
- Mother-template clone evidence is only useful if clone identity is clean before
  Auto-Quant ingestion. Rewrite `package_id`, strategy class, material filename,
  title/brief, symbol/product/timeframe, provider provenance, branch path,
  `consumer_evidence_profile`, and command/state identifiers before the AQ batch
  step; keep the original factor only in explicit `derived_from` provenance. The
  2026-05-20 `M2K/1m` liquidity-sweep reject-short clone into `MYM/1m` proved the
  mechanics and also marked an impact-radius boundary: real IBKR `MYM` produced
  dense exact-root rows but raw-negative expectancy and no 2bps/5bps survivors,
  so adjacent-market clone failure should be terminalized as boundary evidence,
  not rescued by lowering costs or running downstream.
- When a mother-template clone passes Gate 1 on a nearby market cell, separate
  the gates explicitly: `downstream_allowed=true` may follow from exact-root
  cost/density survival, but `promotion_allowed=false` and `trade_usable=false`
  must remain until Pre-Bayes/BBN/CatBoost/execution-tree validate the cloned
  branch and the execution predicates pass. A CRWD-derived YF cybersecurity
  software clone can find real S/5m and FTNT/5m cost-stressed survivors; that
  proves the expansion method is worth using, not that the clone is live-ready.
  The OKTA/5m CRWD-derived PDA sequence clone is the same lesson in a nearby
  single-stock cell: fresh YF rows and Gate 1 cost/density survived with `28`
  trades, `64.2857%` win rate, raw `+3.79%`, and `+0.99%` after `5bps/side`,
  and exact downstream mechanics all exited `0`; it still failed live readiness
  because `transition_hazard=0.9641`, `pda_hybrid_alignment=false`, and
  `execution_readiness=0.4049`. Preserve it as impact-radius/boundary evidence
  and repair the same-root execution predicate; do not call it trade-usable.
- If a mother-template clone reaches exact-root downstream with strong cost
  survival but execution remains observe-only, preserve the branch as a scoped
  downstream candidate and target the execution blocker directly. Example: the
  YF cybersecurity-software `S/5m` PDA/MTF clone kept `26` real trades and
  survived `5bps/side`, and Auto-Quant import, Pre-Bayes/workflow, real-trade
  ingest, CatBoost/path-ranker, and execution-tree readbacks all exited `0`, but
  failed closed because `transition_hazard=0.9599`,
  `pda_hybrid_alignment=false`, `execution_readiness=0.501`, and maturity was
  short. The next same-root experiment should be a transition/PDA-alignment or
  session-liquidity overlay under the exact branch, not a looser promotion gate
  or another naked density clone.
- When targeting a transition/PDA execution blocker, keep the Gate 1 density
  floor alive. A same-root `S/5m` transition/PDA alignment overlay that tightened
  trend stack, slope, RSI, volatility expansion, wick, RVOL, and entry window
  preserved branch fields and ran real YF/AQ cleanly, but collapsed the exact
  root from `26` trades to `4` trades. Treat that as suppression evidence and
  stop before downstream; the next overlay should change one or two execution
  blocker features at a time and preserve roughly the original trade density,
  not solve `transition_hazard` by starving the branch.
- The same density-first rule applies to OKTA/5m mother-template repairs. The
  CRWD-derived OKTA PDA-sequence clone had a useful baseline (`28` exact `5m`
  trades and `+0.99%` after `5bps/side`) but failed downstream predicates. A
  direct PDA/hybrid transition repair that added VWAP slope, EMA slope,
  mid-bar stability, RV expansion, session-return, wick, and volume guards ran
  fresh YF/AQ cleanly yet reduced exact `5m` to `16` trades and flipped `5bps`
  cost survival negative (`+1.06%` raw, `+0.42%` after `2bps`, `-0.54%` after
  `5bps`). Treat this as suppression evidence and do not downstream it. For the
  next OKTA repair, compare every overlay against the original 28-trade/5bps
  positive clone and change one predicate family at a time; preserve density and
  cost edge before asking Pre-Bayes/BBN/CatBoost/execution tree to adjudicate.
- A density-preserving transition repair can still be downstream-negative. The
  NET/5m PDA-sequence clone was near-pass (`32` trades, 5bps-positive,
  `execution_readiness=0.67`, `pda_hybrid_alignment=true`) but missed only
  `transition_hazard=0.63049`. A direct PDA/hybrid repair starved the branch
  (`11` exact 5m trades, negative after costs). A softer transition-stability
  repair recovered Gate 1 density/cost (`29` trades, raw `+3.02%`, `+0.12%`
  after `5bps/side`) but failed downstream worse: `transition_hazard=0.98049`,
  `pda_hybrid_alignment=false`, `execution_readiness=0.4056`, and path-ranker
  visibility/use/validation all false. Treat this pattern as observation-only:
  Gate 1 recovery is not evidence that the execution predicate improved. For
  the next NET same-root repair, compare against both the original near-pass
  clone and the soft-transition negative, and avoid overlays that merely smooth
  entries without changing the actual transition-guardrail/PDA-hybrid readback.
- A mild session/liquidity guard that preserves Gate 1 density is still not an
  execution fix unless it actually changes the downstream predicates. The YF
  cybersecurity-software exact `S/5m` `mild_session_liquidity_guard_v1` clone
  kept `23` trades and survived `5bps/side`, then exported/ingested real trades
  and ran Pre-Bayes/workflow, CatBoost/path-ranker, and execution-tree readbacks
  with all exits `0`; it still failed closed with `transition_hazard=0.9599`,
  `pda_hybrid_alignment=false`, and `execution_readiness=0.501`. Treat this as
  evidence that generic session/liquidity guarding can preserve cost edge but may
  leave the actual PDA/hybrid transition blocker untouched. Prefer the stronger
  density-preserving soft PDA/session branch or a direct PDA/hybrid transition
  predicate experiment next; do not repeat mild session guards under the same
  root without a new predicate hypothesis.
- A soft transition-stability repair can preserve or restore Gate 1 density and
  still make the execution blocker worse after exact-root downstream replay.
  The YF AI-security `NET/5m` `soft_transition_stability_v1` overlay kept `29`
  trades and survived `5bps/side` by only nudging EMA-slope, RSI14,
  VWAP-distance, wick, ROI, and trailing predicates, but downstream replay stayed
  fail-closed with `transition_hazard=0.9805`, `pda_hybrid_alignment=false`,
  `execution_readiness=0.4056`, and path-ranker not used. Compare every soft
  repair against the original same-root downstream baseline; if density is
  preserved but `transition_hazard` / PDA alignment do not improve, preserve it
  as negative repair evidence and pivot to a different same-root PDA/hybrid
  direction-agreement hypothesis instead of stacking more soft guards.
- Auto-Quant strategy library manifests require structured
  `validation_errors`; do not put plain strings there for provenance notes.
  Store provider-window blockers, missing timeframes, and cache-replay caveats
  in `metadata`, `notes`, or packet summaries. Plain strings make
  `auto-quant-results-import` fail before any factor verdict.
- Freqtrade spot-market Auto-Quant materials cannot run short strategies. If
  direct TOMAC/AQ replay through `support/scripts/auto_quant_external/run_tomac_one.py`
  or a wrapper using it fails with `Short strategies cannot run in spot markets`,
  classify it as an AQ runtime contract blocker, not a factor verdict. The
  shared `run_tomac_one.py` path must select `trading_mode=futures` and
  `margin_mode=isolated` for known futures roots or `*-futures.feather` inputs,
  while leaving ordinary spot pseudo-pairs on spot mode. If the next failure is
  `No history for <pair>, futures, <timeframe>`, check whether data lives under
  `user_data/data/binance/futures/<PAIR>-<tf>-futures.feather`; in that case the
  replay datadir must be `user_data/data/binance`, not the broader
  `user_data/data` root. If the exact futures feather is missing but legacy
  local AQ data already exists as unsuffixed `user_data/data/<PAIR>-<tf>.feather`
  or `user_data/data/binance/<PAIR>-<tf>.feather`, conservatively copy it into
  the matching `futures/<PAIR>-<tf>-futures.feather` path without overwriting an
  existing futures file; if only retained TOMAC cache parquet exists, stage the
  missing file into `user_data/data/binance/futures/<PAIR>-<tf>-futures.feather`
  without overwriting existing AQ data and record the `data_stage` status in
  terminal metrics. This is a data-contract repair, not a factor-economics
  pardon. Add or rerun focused `test_run_tomac_one` and wrapper staging coverage
  before spending another AQ window. Exact-AQ wrappers must also classify child
  command exits honestly: any nonzero AQ child exit is
  `exact_aq_runtime_failed_fail_closed`, any timeout is
  `exact_aq_timed_out_fail_closed`, and only all-zero child exits may be
  `exact_aq_completed_fail_closed`. Do not work around futures data failures by
  forcing `can_short=False` or by relabeling a short branch as long-only.
- Auto-Quant agent-material rank artifacts store the authoritative row list in
  `ranking[]`. Do not terminalize a packet from stale helper counters such as
  `ranked_results` or `ranked_row_count` without opening the actual
  `auto_quant_agent_material_rank*.json`; if `ranking[]` has completed rows,
  classify the factor result from those rows rather than as a command/rank
  failure.
- When parsing Auto-Quant `package_id` for symbol/timeframe unit labels, do not
  use broad substring checks if the factor id itself contains ticker symbols or
  timeframe tokens (for example `yf-sjb-tlt-credit-stress-continuation-*` or
  `yf-qqq-5m-cost-stable-...`). Parse the exact material suffix after the stable
  factor namespace, such as `package_id.endswith(f"-{timeframe}-v1")`, or fall
  back to the human `unit_label`; otherwise cost-stress and positive-sibling
  summaries can mislabel rows and falsely open downstream gates while the AQ
  verdict itself is still valid.
- If an exact-branch feedback replay preserves the rooted branch path but the
  exported CatBoost/path-ranker target has only one mature label class, treat
  CatBoost training failure as a real downstream blocker. Do not force runtime
  enablement or execution-tree promotion from direct-fallback artifacts; record
  the single-class target and terminalize the branch as fail-closed.
- If a regime-rooted overlay preserves branch fields and covers the full timeframe ladder but the explicit root timeframe fails cost-stressed density, stop at Gate 1 and do not run Pre-Bayes/BBN/CatBoost/execution-tree. Positive sibling/context timeframes can seed a new independent sibling-root experiment, but they must not rescue the failed root. Example: fresh IBKR QQQ `1m` transition/PDA overlay failed 2bps/side on the 1m root while 5m/1h siblings were positive; terminalized as `drop_gate1_no_1m_cost_density`. See `references/ibkr-qqq-1m-overlay-cost-density-failure-20260519.md`.
- For options/volatility factors, never promote missing options-chain fields by name.
  If historical IV/HV, OI, Greeks, GEX, skew, or 0DTE flow are unavailable, use
  explicit `*_proxy` naming and prefer practical OHLCV-derived gates such as
  IV/RV-compression proxies, realized-volatility expansion filters, MACD/reclaim
  density triggers, and short max-hold execution overlays. See
  `references/options-proxy-auto-quant-practicalization.md`.
- If Freqtrade/Auto-Quant reports zero trades while a vectorized signal diagnostic
  shows dense entries, run an always-long smoke strategy on the same pair/timeframe.
  If always-long also returns zero, preserve the AQ attempt but treat subsequent
  pandas/vectorized results as candidate-discovery or clearly labeled proxy rows,
  not a clean Auto-Quant pass.
- When the user requests a 3M IBKR 1m-up timeframe ladder and fresh IBKR returns
  empty/timeouts for every lane despite provider-status readiness, record it as a
  provider-window blocker and continue only with retained real IBKR frames if they
  exist. Mark `local_cache_replay=true`, enumerate missing timeframes, do not
  fabricate 1m/15m/1h from 5m/30m, and never call cache replay live-ready.
- Auto-Quant strategy-library `validation_errors` expects structured error
  objects, not free-form strings. Put provider-window notes in summaries or
  metadata; otherwise import fails before the factor verdict.
- Provider-specific MTF promise is not provider portability. If an IBKR ladder has
  positive rows but the provider-quartet/sibling-provider AQ rank has no positive
  provider rows, stop before BBN/CatBoost/execution-tree for the portability
  variant and classify it as `provider_portability_failed_stop_before_downstream`;
  keep the original provider-specific branch as incubate-only until maturity and
  execution-tree gates pass. See `ict-engine-runtime/references/provider-portability-before-promotion.md`.
- A TVR CRWD 1m full-ladder rerun with real `1m/5m/15m/30m/1h/4h/1d` coverage but `positive_origin_1m=[]` and `cost_gate.pass=false` is a Gate 1 stop even if the 5m sibling is strong; pivot to a denser 1m entry family instead of overlay-grinding. See `references/tvr-crwd-1m-full-ladder-gate1-stop.md`.
- Auto-Quant `factor-autoresearch --auto-quant-profile synthetic_ohlcv` is useful
  for mechanical seed iteration, but it is not live-provider parity when the
  profile collapses real symbols/timeframes into synthetic `ETF/USD` or exact-symbol
  synthetic `1h/4h/1d` artifacts. Keep positive `run_tomac.py` results as
  seed/incubate evidence unless the exact real provider/symbol/timeframe branch is
  preserved through AQ, downstream gates, CatBoost/path-ranker visibility/usage,
  and execution readiness. If the first run returns `auto_quant_prepare_required_before_run`
  or `auto_quant_active_strategy_count=0`, run `auto-quant-prepare`, refresh the
  handoff, then run the advised `run_tomac.py`; still convert any winner back into
  exact rooted material before Gate 1/downstream. If the managed seed is sparse or
  negative after the handoff (for example Tomac MNQ 1h with 4 trades, -0.55%, PF
  0.7746), terminalize it as observation-only and pivot to a new exact-root factor
  shape rather than downstreaming it. See
  `references/auto-quant-synthetic-autoresearch-parity.md`,
  `references/autoquant-synthetic-seed-vs-exact-root-parity-20260519.md`, and
  `references/auto-quant-synthetic-autoresearch-negative-seed-20260519.md`.
- If a strong exact branch is replayed with retained provider rows only (for
  example `local_cache_replay=true`, missing `1m/1h/4h/1d`), classify it as
  observation/refinement seed unless fresh-provider full-ladder parity and
  downstream gates pass; do not call it live-ready even if `execution_readiness >=
  0.65` and Gate 1 cost survives.
- If `factor-autoresearch` returns `auto_quant_prepare_required_before_run`,
  `auto_quant_seed_strategies_required`, or `auto_quant_active_strategy_count=0`,
  treat the run as a control-plane preparation result, not as completed automatic
  iteration. Before rerunning, inspect the managed Auto-Quant workspace, use the
  actual template path present in that checkout (commonly `user_data/strategies/_template.py.example`,
  not necessarily `strategies_external`), seed 1-3 active non-underscore strategies
  with different paradigms, then run the workspace oracle. Preserve the original
  regime-rooted branch metadata when importing any result back into ict-engine.
- For default/managed Auto-Quant handoffs, do not treat an existing requested
  `data_path` plus unrelated workspace feathers as data-ready. The workspace
  data must match the requested file stem or an explicit profile
  `expected_data_files` contract; otherwise classify the handoff as
  `dependency_ready_data_missing` and run/repair `auto-quant-prepare` before
  any `run.py`. A CRWD `yf_crwd_5m.csv` handoff once had active strategies and
  Binance `BTC/ETH/SOL/BNB/AVAX` `1h/4h/1d` feathers, which produced crypto
  seed logs while pretending to train the CRWD root; that output is control-plane
  blocker evidence, not CRWD Gate 1 evidence.
- After an exact `auto_quant_handoff_candidate` exists, generic managed
  Auto-Quant readiness is subordinate to that latest exact handoff. Before
  recommending or running `run.py`, compare `auto-quant-status` against the exact
  `factor-research --backend auto-quant` handoff/adoption-review readiness. If
  the latest exact handoff is `data_ready=false`, generic status must stay
  `dependency_ready_data_missing` even when the managed workspace contains other
  valid market data. Treat any mismatch as a readiness/status-parity bug and stop
  before training, because otherwise Auto-Quant can optimize unrelated retained
  data while the rooted factor appears to advance.
- Same-time-of-day slot alpha and other intraday seasonal micro-edges need an
  early cost gate. If AQ shows a strong low-timeframe row but replay flips
  negative at 1 bps/side, terminalize as `cost_fragile`; do not promote a
  higher-timeframe vector proxy when the matching AQ row is sparse or negative.
- If a `1m` rooted YF branch has no fresh provider rows or no exact Auto-Quant
  Gate 1 pass, stop before Pre-Bayes/BBN/CatBoost/execution-tree even when
  sibling/context frames such as `15m` or `30m` look positive in vectorized
  triage. Positive siblings may seed a new independent sibling-root branch but
  cannot rescue the failed `1m` root. If `4h` is unsupported by the provider
  fetch contract, record it in `missing_timeframes` or resample with an explicit
- If a `1m` rooted YF branch has no fresh provider rows or no exact Auto-Quant Gate 1 pass, stop before Pre-Bayes/BBN/CatBoost/execution-tree even when sibling/context frames such as `15m` or `30m` look positive in vectorized triage. Positive siblings may seed a new independent sibling-root branch but cannot rescue the failed `1m` root. If `4h` is unsupported by the provider fetch contract, record it in `missing_timeframes` or resample with an explicit context/proxy label; never silently substitute `1h`. If the runner only produced provider/proxy summaries, still create/read back `checks/terminal_metrics.json`, write a terminal summary, and close the active claim as a blocked exact-root run with all downstream booleans false. See
  `references/yf-1m-root-ladder-blocked-positive-siblings.md` and `references/exact-root-provider-blocker-vectorized-proxy-terminalization-20260519.md`.
  See `references/tod-slot-alpha-cost-gate.md`.
- 30m high-window/quarter-high reclaim can be a strong OHLCV-first proxy for
  52-week-high continuation when true 52-week context is unavailable. Run it
  cross-symbol first, cost-stress the basket, then hand off to BBN/CatBoost/tree
  only if multiple symbols survive. Treat CatBoost candidate-set visibility as
  parity evidence, not live-readiness, until validation rows mature. If a
  transition-risk guard fixes a weak sibling but reduces basket expectancy,
  keep it as a sizing/risk overlay rather than replacing the matured primary
  branch. See `references/high-window-reclaim-tree-handoff.md`.
- Structural path-ranker CatBoost scores must be applied to the current
  refined AQ row against the original same-symbol AQ row before downstream work.
  If the refinement does not improve the original row and sibling symbols remain
  negative or unproven, classify as `incubate_symbol_specific_only` or
  `done_incubate_no_incremental_improvement`; do not spend BBN/CatBoost/tree
  budget on parity-only refinements. See
  `references/single-stock-refinement-aq-parity.md`.
- Structural path-ranker CatBoost scores must be applied to the current
  post-analyze exported target, not only to a stale pre-analyze target. The
  safe loop is `analyze -> export-structural-path-ranking-target -> CatBoost
  apply -> apply-structural-path-ranking-external-scores ->
  register/enable runtime -> analyze/workflow readback`.
- If exact branch parity, path-ranker runtime, and 30-row validation gates pass
  but `closed_loop_branch_admission` remains `fail_closed`, stop blind timeframe
  sweeps and diagnose `report.supporting.execution_artifact.features`. The
  closed-loop return-to-duty floor is `execution_readiness >= 0.45`; `>= 0.65`
  is only the stronger `execution_ready` class, not a reason to exile otherwise
  cost-positive same-root candidates from the profitability loop. Compute the
  readiness shortfall only below `0.45`, and separately identify whether remaining
  blockers come from execution_score, evidence_quality, overextension,
  reversion_speed, spectral penalty, transition hazard, live-plane artifacts, or
  paper/sim validation. See
  `references/execution-gate-readiness-diagnostics.md`.
- If a strict 1m Gate 1 survivor is cost-positive but the downstream replay/analyze path times out on a large retained-row matrix, first rerun the exact rooted branch on a smaller real retained slice to distinguish input-volume timeout from structural failure. If the smaller slice also times out or produces no execution-tree readback, classify as a downstream replay/runtime blocker, not as promotion evidence. Do not lower gates because the source row survived 2bps. See `references/binance-strict-1m-downstream-timeout-and-small-window-replay.md`.
- If Gate 1 density is already healthy but execution remains `observe` /
  `transition_guardrail`, stop more density sweeps on the same root. Read the
  execution-readiness shortfall from the analyze/workflow artifacts, then target
  a same-root composite overlay aimed at `session_liquidity` and
  `transition_stability` before rerunning Gate 1. If that transition-stable
  overlay also reaches downstream but remains observe-only with
  `ranker_validation_ready=false`, do not keep making near-identical overlays;
  pivot to same-branch mature/validation rows, provider parity, or execution
  readiness feature diagnostics. Do not treat path-ranker visibility as readiness.
  If IBKR/TradingViewMCP fresh fetch probes return zero rows while YF source
  material remains positive, classify the branch as scoped candidate evidence,
  not live-ready provider parity. See
  `references/beauty-rsi-vwap-reclaim-execution-readiness-20260518.md`,
  `references/beauty-transition-stable-overlay-v5-downstream.md`, and
  `references/beauty-transition-stable-overlay-v5-downstream-provider-parity.md`.
- If a Kraken/public-crypto VWAP compression-expansion density branch completes provider fetch and Auto-Quant cleanly but has no dense positive 1m-origin survivor, terminalize at Gate 1 even if branch metadata is preserved and higher-timeframe rows have tiny positive one-trade samples. Do not proceed to Pre-Bayes/BBN/CatBoost/execution tree; pivot to a materially denser 1m entry family under a new rooted branch. See `references/kraken-xlm-algo-compression-expansion-gate1-20260519.md`.
- If a Bybit crypto CMF/OBV accumulation-breakout full-ladder has preserved branch fields but no 1m origin survivor and only sparse HTF positives, terminalize at Gate 1. A 30m/1h positive row with fewer than the minimum trade-count floor (e.g. 1-4 trades) is not subclass evidence strong enough for downstream. Pivot to a denser 1m crypto entry family such as VWAP/RSI/OBV snapback or micro-liquidity reclaim instead of tightening the same breakout shape. See `references/bybit-lpt-arb-cmf-obv-gate1-density-failure-20260519.md`.
- If a TOD / intraday seasonality branch has positive AQ rows but downstream is
  `execution_observe_only` or `fail_closed`, do not force promotion by lowering
  gates. First replay the exact signal into per-trade feedback rows and inspect
  `raw_scored_mature`, production/observation validation, policy matched rows,
  `execution_readiness` shortfall, and PDA/hybrid disagreement. If signal density
  is sparse or mixed, preserve the branch as incubate and pivot to a new
  trade-dense regime-rooted candidate family rather than flattening it into the
  old branch. See `references/tod-slot-alpha-practicalization-pivot.md`.
- When the user asks whether there is a practical/live-ready/profit factor in
  the whole repo, audit the entire repo/run corpus rather than the latest run.
  Search for positive readiness gates (`trade_usable=true`,
  `promotion_allowed=true`, `runtime_eligible`, `quality_ready=true`, mature
  production/observation rows, and actionable closed-loop admission) and then
  verify the same rooted branch is not blocked by `candidate_set_only`,
  `execution_observe_only`, `gate_status=observe`, `actionable=false`, or
  `fail_closed`. A factor with mature ranker gates but observe-only execution is
  a mature candidate, not live-ready. See
  `references/repo-wide-live-ready-audit.md`.
- If a repo-wide practical-factor audit finds a near-pass branch with strong
  Gate 1 cost survival, exact branch survival, history-mature ranker validation,
  and closed-loop execution-tree admission, distinguish persisted analyze
  candidates from the live structural execution surface. A stale persisted
  `execution_candidate.json` with `actionable=false` / `candidate_status=no_trade`
  is not enough to promote, but it also must not hide a same-root
  `execution_tree_trace.json.closed_loop_branch_admission` that is
  `status=admitted`, `ready=true`, `actionable=true`, and
  `candidate_status=execution_ready` after post-ranker readback. The live
  admission owner is the same-root execution-tree closed-loop candidate, not the
  old analyze candidate file. The CRWD `5m` PDA/MTF exact rerun
  `20260519T193157+0800` is the canonical promoted example: all downstream
  commands exited `0`, exact branch survived, `43` real trades were ingested,
  cost stress survived through `5bps/side`, `history_mature_rows=46`,
  `execution_readiness=0.67`, `transition_hazard=0.5950`,
  `pda_hybrid_alignment=true`, and the live structural candidate was
  `execution_ready`, so `promotion_allowed=true`, `trade_usable=true`, and
  `update_goal=true` were correct even though the persisted analyze candidate
  still said `no_trade`. Under the profitability lifecycle split, do not reuse
  this historical shortcut from `execution_ready` alone: re-read the same-root
  closed-loop admission and require `status=admitted`, `live_trade_status=ready`,
  explicit `promotion_allowed=true`, `trade_usable=true`, and `update_goal=true`,
  and a current live branch shape (`fill_viable`; `wait_for_reversion` is
  observe-only). Explicit lifecycle live-plane strings such as
  `live_trade_ready` / `live_trade_usable` count only when the row also has
  mature training evidence (`maturity_mask=true`, calibrated label, positive
  `training_weight`). Current target sparsity such as `mature_rows < 30` can
  be acceptable only when history-backed raw/production/observation validation is
  mature and the same-root live structural execution candidate is actionable;
  preserve the caveat explicitly and add tests around both stale-candidate
  fail-closed and same-root live-admission promotion. See
  `references/crwd5m-pda-soft-confirmation-downstream-retry-20260519.md`.
- When the user asks to microtune all candidates into practical factors, first
  classify each candidate by its missing gate instead of sweeping everything:
  `ranker_mature_but_execution_observe`, `thin_edge_cost_fragile`, or
  `gate1_strong_validation_immature`. Tune only the blocker gate: execution
  readiness/PDA/hybrid diagnostics for mature-but-observe branches; cost and
  turnover filters or abandonment for thin micro-alpha; provider parity plus
  same-root mature rows for strong Gate 1 but validation-immature branches. See
  `references/candidate-microtuning-live-readiness.md`.
- If direct CatBoost training on the current structural target fails with
  constant/ignored features or too few usable rows, do not call the factor
  failed. Train the model on `structural_path_ranking_target_history.csv` in
  classification mode, apply that model to the current post-analyze target,
  then `apply-structural-path-ranking-external-scores`, enable runtime with
  `prefer_history`, and rerun analyze/workflow/policy before judging execution.
  If the history-backed attempt still fails because all features are constant or
  only one mature/varied label exists, preserve a Gate 1 positive as
  `scoped_practical_candidate` / `gate1_pass_downstream_fail_closed`, not live
  readiness. Exact branch survival plus execution observe-only is useful parity
  evidence; next work is adding same-branch sibling rows or diagnosing execution
  readiness, not forcing promotion. See
  `references/gate1-positive-downstream-fail-closed-parity.md`.
- For session VWAP/noise-band breakout branches, positive low-timeframe AQ rows
  with thin trade density can justify downstream parity, but not promotion. If
  AQ import, BBN prior, Pre-Bayes/filter, CatBoost/path-ranker, and execution
  tree all run while `execution_candidate_actionable=false`,
  `execution_tree_gate_status=observe`, `execution_tree_branch=transition_guardrail`,
  `ranker_validation_ready=false`, or maturity/training rows remain zero,
  classify as `gate1_candidate_downstream_fail_closed`. Preserve scoped subclass
  evidence and next seek denser variants or sibling/provider validation. Also
  check downstream helpers for hardcoded `SOURCE` run roots before reuse. See
  `references/noise-band-breakout-downstream-fail-closed.md`.
- When exact-branch maturity and path-ranker gates pass but execution remains
  `execution_observe_only`, decompose `execution_readiness` before more factor
  sweeps. In current code, readiness is driven by `execution_score`,
  `evidence_quality`, OU overextension/reversion, and spectral penalty; the
  analyze completion-pressure input comes from `selected_win_probability`, not
  necessarily from the matured same-branch path-ranker posterior. If the gap is
  marginal, prefer a narrow structural execution overlay proposal over lowering
  `EXECUTION_GATE_READY` or globally treating observe-only as ready. If
  `execution_tree_trace.json` shows `transition_guardrail` with
  `hybrid_transition_hazard` above threshold while the ranker is visible but not
  used, inspect `split_reason_lineage` plus `execution_shap_top_k` before more
  AQ sweeps; top contributors such as `pythagorean_overstretch`,
  `dominant_cycle_energy`, and `spectral_entropy` indicate a same-root
  transition-stability/current-alignment overlay target, not a promotion signal. If a
  1m-origin full-ladder branch passes AQ Gate 1 and cost stress but downstream
  readback shows current-schema readiness/ranker/materialization blockers,
  preserve it as observation/incubation only and
  train the next same-root composite overlay for current readiness/ranker
  agreement; do not lower gates. See
  `references/hack-cybersecurity-density-downstream-fail-closed.md`.
- For public/source-backed intraday factors such as ORB/RVOL, a positive low-timeframe AQ row is only Gate 1 evidence. If `1m/5m/15m` are positive but `30m` is negative or `1h` has zero trades, preserve the branch as `incubate` with low frames as entry/timing evidence and HTF as neutralization/confirmation, then fail closed until BBN/CatBoost/execution-tree maturity gates pass.
- If an opening-drive/impulse-pullback retest branch preserves full rooted identity and provider/AQ commands all succeed, but every ranked AQ material returns zero trades across the `1m` origin and sibling ladder, classify it as `drop_gate1_no_cost_density` and stop before Pre-Bayes/BBN/CatBoost/execution-tree. Do not add overlays to rescue the branch; pivot to a denser 1m entry family inside a fresh rooted branch. See `references/qqq-opening-impulse-zero-trade-density-pivot-20260519.md`.
- For regime-rooted MTF provider ladders in a multi-agent session, claim work outside the repo, check active same-class Auto-Quant/process lanes before launching, and require real 1m-origin trade density before downstream. Sparse positives on 5m/15m/30m/1h with zero or one 1m trade are `keep_subclass_evidence_or_drop_gate1_no_downstream`, not Pre-Bayes/BBN/CatBoost/tree candidates. See `references/regime-rooted-mtf-provider-ladder.md`.
- If a profitability-factor run produces too few trades, do not tighten overlays or move downstream. First max the provider window for each available timeframe (`1m` feasible upper bound, then `5m/15m/30m/1h/4h/1d` where real provider data exists) and switch to a denser 1m entry family. A compound overlay that turns a passing base factor into sparse/negative rows should be dropped, not promoted. Positive 30m/1h siblings do not rescue a sparse/negative 1m root. If a sparse 1m root only yields 0-2 trades after a fair AQ run, stop grinding the same entry shape and pivot to a denser 1m family inside the same rooted branch. See `references/max-window-density-before-downstream.md` and `references/dense-1m-entry-family-pivot.md`.
- For exact rooted-branch validation, execution-tree ranker visibility is not
  enough. Audit `closed_loop_branch_admission.path_id`; if it pivots from the
  tested branch to a sibling path, terminalize as same-branch parity failure
  even when CatBoost is ready and used by the execution tree.
- If CatBoost/path-ranker training succeeds by deriving pseudo-labels from
  `structural_baseline_score` with zero mature samples, treat the model as
  visibility/parity evidence only. Even if the post-ranker execution tree
  selects the exact branch, do not promote unless validation rows mature
  (`raw_scored_mature`, `production_validation`, and `observation_validation`)
  meet the runtime gates and `closed_loop_branch_admission` is actionable.
- For same-root composite overlays built after a dense base factor, require breadth at the 1m origin before downstream handoff. HTF positives are subclass evidence only. If the overlay yields only one positive 1m sibling while 5m/15m/30m/1h look fine, terminalize as `drop_overlay_or_keep_subclass_evidence_no_downstream`, not BBN/CatBoost/execution-tree material. See `references/same-root-overlay-origin-sibling-gate.md`.
- For crypto/altcoin full-ladder Gate 1 runs, a fully successful provider/AQ chain can still be a terminal factor-gate failure when the `1m` origin is sparse. Treat positive `15m`/`1h` siblings as observation or a separate exact timeframe root only; do not run Pre-Bayes/BBN/CatBoost/execution-tree unless the 1m root has enough real-cost trade density. See `references/kraken-crypto-full-ladder-origin-density-gate.md`.
- If a QQQ 1m rooted VWAP/reclaim branch has adequate raw trade density but all 1m variants flip negative at 2bps/side, stop treating it as a 1m promotion candidate. Positive 5m or 30m siblings are evidence to restart under a new exact timeframe root such as `US -> equity_etf -> QQQ -> 5m -> ...`, with 1m retained only as microstructure/context. Do not let HTF cost survivors rescue a failed 1m root. See `references/qqq-rooted-vwap-reclaim-cost-density-20260519.md`.
- If a same-root stability overlay fetches and ranks cleanly but produces zero trades across the practical ladder, classify it as `drop_or_block_gate1_practical` and stop before Pre-Bayes/BBN/CatBoost/execution tree; the next candidate should loosen density constraints or pivot to a materially different entry family under the same root. If Gate 1 density exists and Pre-Bayes/CatBoost visibility passes but execution still fails closed on current-schema readiness/ranker/materialization blockers, preserve exact-branch observation evidence and target those live blockers directly; do not lower promotion gates. See `references/rooted-factor-continuation-zero-trade-and-pda-failclosed-20260519.md`.
- When the user explicitly says IBKR is required, stop using YF/fallback provider evidence for the active verdict. Fetch an IBKR-native full ladder (`1m=7 D`, `5m/15m/30m/1h/4h=1 M`, `1d=1 Y` where supported), set `local_cache_replay=false`, and preserve IBKR provenance in every material. A QQQ `intraday_micro_trend_reclaim_density` family using session VWAP soft reclaim, EMA9/21/55 alignment, EMA21 slope, RVOL/volume, RSI, and ATR extension can produce a cost-positive 1m Gate 1 row; if downstream exact branch survives but current execution readback remains observe-only/non-actionable because of readiness/ranker/maturity state, keep it observation-only and add a same-root execution-facing overlay rather than lowering gates. See `references/ibkr-native-qqq-micro-trend-reclaim-density-20260519.md`.
- A same-root transition/PDA overlay can be too restrictive for the 1m origin even when 5m/1h siblings improve. If the overlay's 1m rows do not survive 1-2bps/side, stop before downstream and classify it as negative/suppression evidence for that exact 1m branch. Positive 5m/1h overlay siblings must restart under their own exact timeframe roots rather than rescuing or promoting the failed 1m root. If fresh IBKR is down and retained real IBKR frames are reused, mark `cache_replay_used=true` / `fresh_ibkr_live_ready=false`; cache replay can exercise AQ only, not live-ready provider parity. If repeated concurrent launches of the same wrapper create duplicate run roots or dispatch processes, kill your duplicate wrapper before summarizing and use the earliest completed terminal metrics for the verdict; do not let duplicate partial roots become separate evidence packets. See `references/ibkr-qqq-transition-pda-overlay-cache-replay-20260519.md`.
- If a positive higher-timeframe sibling from a transition/PDA overlay earns downstream readback under cache replay, preserve it as its own exact timeframe root and require the same execution gates. If exact-branch readback shows path-ranker visible but unused plus current-schema readiness/transition/materialization failure, stop making near-identical transition overlays; pivot the next candidate toward the active blocker instead of repeating old field names. See `references/qqq-transition-pda-overlay-5m-cache-replay-downstream-20260519.md`.
- If a transition/PDA overlay is correctly attached after a Gate1-positive base factor but the 1m-origin rows fail 1-2 bps/side cost stress, stop before Pre-Bayes/BBN/CatBoost/execution-tree even when 5m/1h siblings are positive. Higher-timeframe positives are subclass evidence or new timeframe roots, not rescue evidence for the failed 1m branch. If a fresh long run exits without terminal metrics, prefer the latest completed packet with `checks/terminal_metrics.json` and label the interrupted run incomplete. See `references/transition-pda-overlay-gate1-stop-20260519.md`.
- If a transition/PDA overlay is correctly attached after a Gate1-positive base factor but the 1m-origin rows fail 1-2 bps/side cost stress, stop before Pre-Bayes/BBN/CatBoost/execution-tree even when 5m/1h siblings are positive. Higher-timeframe positives are subclass evidence or new timeframe roots, not rescue evidence for the failed 1m branch. If a fresh long run exits without terminal metrics, prefer the latest completed packet with `checks/terminal_metrics.json` and label the interrupted run incomplete. See `references/transition-pda-overlay-gate1-stop-20260519.md`.
- If a positive higher-timeframe sibling from a transition/PDA overlay earns downstream readback under cache replay, preserve it as its own exact timeframe root and require the same execution gates. If exact-branch readback shows path-ranker visible but unused plus current-schema readiness/transition/materialization failure, stop making near-identical transition overlays; pivot the next candidate toward the active blocker instead of repeating old field names. See `references/qqq-transition-pda-overlay-5m-cache-replay-downstream-20260519.md`.
- If a transition/PDA overlay is correctly attached after a Gate1-positive base factor but the 1m-origin rows fail 1-2 bps/side cost stress, stop before Pre-Bayes/BBN/CatBoost/execution-tree even when 5m/1h siblings are positive. Higher-timeframe positives are subclass evidence or new timeframe roots, not rescue evidence for the failed 1m branch. If a fresh long run exits without terminal metrics, prefer the latest completed packet with `checks/terminal_metrics.json` and label the interrupted run incomplete. See `references/transition-pda-overlay-gate1-stop-20260519.md`.
- For stable-profit training, the stored `branch_path` must start at the main regime: `main_regime -> sub_regime... -> first_profit_factor -> optional_profit_factor_overlays...`. Market, product, provider, symbol, contract, base timeframe, ladder timeframe, source window, and cache/fresh-provider status are labels/provenance only; put them in `labels`, `provider_rows`, `row_counts`, `selected_windows`, or `full_rooted_identity_path`, not in `branch_path`. Preserve the same canonical branch through Pre-Bayes/filtering, BBN, CatBoost/path-ranker, and execution tree. Start from `1m` when feasible, cover `5m/15m/30m/1h/4h/1d` with real rows where available, cost-stress at 0/1/2/5 bps per side, and only promote if real-cost density, direction consistency, mature validation, exact execution candidate materialization, ranker consumption, and current active readiness gates all hold. Gate failures should drive the next factor shape; never lower gates just to avoid `promotion_allowed=false` or `trade_usable=false`. See `references/rooted-gate1-cost-stable-training-20260519.md`.
- Before reusing or launching an older Auto-Quant material runner, audit the runner contract itself: it must preserve the canonical regime-rooted branch path, keep market/product/symbol/timeframe/provider as labels, request the current maximum feasible ladder including `1m/5m/15m/30m/1h/4h/1d`, mark real provider rows vs missing/unsupported lanes, and set explicit downstream booleans (`pre_bayes_allowed`, `bbn_allowed`, `catboost_allowed`, `execution_tree_allowed`, `promotion_allowed`, `trade_usable`, `update_goal`). If the runner only tests a partial ladder such as `1m/15m`, emits a flattened path like `Transition -> OpeningRange -> factor`, or puts provenance before the main regime in `branch_path`, treat the output as partial/contract-invalid Gate 1 evidence and either patch the runner before rerun or record `downstream_allowed=false`. For current Gate 1 metric schemas, read labels from `provider_rows` when present; otherwise derive symbol from `cost_stress_rows[*].label` and ladder/window labels from `row_counts` and `selected_windows` without guessing missing provider/product fields. The QQQ opening-drive / FVG-ORB retest examples showed successful AQ exits with zero or sparse 1m trades; those are factor-gate failures, not candidates to rescue downstream.
- For futures/precious-metals 1m opening VWAP/RVOL reclaim lanes, raw-positive high win rate is not enough. If the exact `1m` row flips negative at `1bps` per side, stop at Gate 1 even when IBKR fetch, strategy compile, AQ batch, dispatch, and rank all succeed. The MGC 202606 `1m 7 D` example had `9320` real IBKR rows, `14` dense trades, `71.4%` win rate, and raw `+0.15%`, but cost stress was already `-0.13%` at `1bps` and `-0.41%` at `2bps`; classify this as thin-target cost failure and pivot to wider-move families such as liquidity-sweep/stop-run reversal or higher-timeframe session expansion.
- For index futures low-turnover volatility compression/expansion siblings, do not send a raw-negative Gate 1 packet downstream just because turnover is lower or the execution tree has been the recent blocker. The MNQ 202606 `30m/1h` low-turnover expansion packet used real IBKR rows and clean AQ exits, but all six ranked rows were raw-negative before costs. Classify that as direction or factor-family failure at Gate 1, not a downstream execution-evidence problem.
- If a same-root futures PDA/transition overlay preserves `2bps` density but
  fails `5bps` and downstream still reports `execution_readiness=0.0`,
  `transition_hazard=1.0`, `pda_hybrid_alignment=false`, and `mature_rows=0`,
  stop repeating PDA guards. The MES 202606 `15m` micro-trend overlay kept one
  `2bps` survivor (`19` trades, `+0.10%`) and ran all downstream commands cleanly,
  but execution stayed `observe` with validation `0/30`; classify as observation
  and pivot to mature feedback/validation evidence or a materially different
  exact-root family.
- If 1m-origin full-ladder runs repeatedly fail after clean provider/AQ execution, stop rotating near-equivalent 1m variants just because higher-timeframe siblings look positive. Either loosen the 1m signal with a pre-AQ density diagnostic, or restart the surviving sibling as its own exact timeframe root such as `... -> 30m -> ...`; never use HTF positives to rescue a failed 1m root or to justify downstream admission. See `references/origin-density-pivots-20260519.md`.
- For MNQ/futures 1m liquidity-sweep or reclaim branches, a 2bps-only survivor is downstream-parity evidence, not practical readiness. If the row fails 5bps and exact downstream later preserves the branch but returns `mature_rows=0`, `history_mature_rows=0`, `execution_readiness=0.0`, `transition_hazard=1.0`, and `pda_hybrid_alignment=false`, classify it as observation/fail-closed. If a simulated-feedback admission script fails while importing an Auto-Quant workspace because the active interpreter lacks `freqtrade`, treat that as an environment handoff blocker, not a factor verdict; rerun with the Auto-Quant venv/interpreter that has `freqtrade` or explicitly probe the import first. If the Auto-Quant workspace emits FreqTrade logs before the final trade JSON, wrap extraction with explicit stdout sentinels and parse only the sentinel payload. A patched liquidity-sweep replay with 7 simulated trades ran `01..19` cleanly and improved the readback to `transition_hazard=0.5821` plus `pda_hybrid_alignment=true`, but still lacked mature validation (`mature_rows=2`, `history_mature_rows=8`); do not call such a short simulated sample mature validation. Its `execution_readiness=0.4931` now clears the 0.45 return-to-duty floor but remains below the stronger 0.65 ready class, so continue downstream repair instead of treating readiness alone as terminal. See `references/mnq-1m-liquidity-sweep-downstream-and-sim-feedback-20260520.md`.
- A higher-timeframe crypto exact branch can look close on historical alignment/transition telemetry and still fail the retention rule. The Bybit `TRXUSDT/4h` Ichimoku exact-root extended-window replay preserved `TrendExpansion -> CryptoIchimokuCloudContinuation -> bybit_trxusdt_ichimoku_cloud_continuation_4h_exact_v1`, fetched `1000` real `4h` rows, and improved Gate 1 to `18` trades, raw `+9.50%`, `5bps/side=+7.70%`. Exact downstream ran all commands with exit `0` and kept historical `pda_hybrid_alignment=true`, but still failed closed with `execution_candidate_status=no_trade`, `execution_readiness=0.4521`, `transition_hazard=0.6056`, `ranker_validation_ready=false`, and path-ranker visible but unused. Treat this as near-threshold observation only: next work needs mature validation and execution-candidate/ranker-consumption repair under the live source/readback contract, not another identical downstream or simulated-feedback replay.
- Older downstream helper scripts may train a `weighted_feature_sum_v1` direct
  fallback artifact with `--allow-direct-fallback` but omit that flag on the
  subsequent `--apply` call. If apply fails with `No trained model found ... pass
  --allow-direct-fallback`, rerun apply with `--allow-direct-fallback`, register
  the artifact as `weighted_feature_sum_v1` (not `catboost`), enable runtime, and
  rerun analyze/workflow/pre-bayes/policy before judging execution.
- If `path_ranker_integration.py --python-runner uv` fails before training due
  PyPI/TLS dependency bootstrap (`Failed to fetch: https://pypi.org/simple/...`),
  do not terminalize the factor. Probe local Python envs for `pandas`, `numpy`,
  and `catboost`; if found, rerun the same integration with that interpreter and
  `--python-runner system`, then apply scores and re-enable runtime before
  judging the branch.
- When a 30m high-window / quarter-high reclaim branch is cross-symbol positive,
  the next Gate 1 refinement should be a rooted 1m-origin MTF lane before any
  promotion claim: request fresh IBKR `1m/5m/15m/30m/1h`, downgrade only the
  blocked timeframe lane, keep provider-fetched rows distinct from derived
  resampled context, and preserve the full regime path in Auto-Quant material
  fields. See `references/ibkr-high-window-reclaim-1m-mtf-gate.md`.
- For forward observation after a matured regime-rooted branch, prefer fresh
  IBKR first and retry a smaller real IBKR window before falling back. If IBKR
  times out but TradingViewMCP/yfinance succeeds, use fallback data only for
  watchlist telemetry; mark `provider_parity=fallback_only_not_ibkr_live_ready`,
  audit `latest_regular_bar` where volume is nonzero, and preserve execution-tree
  fail-closed truth. See `references/forward-watchlist-provider-parity.md`.
- Provider price replay, sibling-symbol isolation, and direct per-timeframe IBKR
  packets still do not prove provider-native signal generation for TOD/session
  seasonal factors when the provider window is only a bounded replay slice. For
  lookback-driven TOD portfolios, first verify the provider history is long
  enough for every selected stream to become history-ready; otherwise classify
  as `provider_native_signal_generation_blocked_by_bounded_history`, keep
  `extension_complete=false`, and build rolling/continuous provider history
  before any trade-usable claim.
- When fresh IBKR is blocked and fallback data is used for source-backed candidate
  discovery, separate three classes clearly: (1) fallback watchlist telemetry,
  (2) Auto-Quant Gate1 incubate evidence, and (3) downstream promotion. A fallback
  candidate such as VWAP reclaim can be worth incubating if cross-symbol and
  cost-stressed, but it must not enter BBN/CatBoost/tree until native/provider
  parity exists. Zero-trade AQ rows such as gap-go or pair z-score are factor-gate
  failures when fetch/dispatch/rank completed. Dense slot-alpha diagnostics must
  pass 5 bps/side or be reduced with a turnover/regime filter before becoming an
  AQ lane. See `references/source-backed-candidate-triage-after-provider-blocker.md`.
- If a cost-positive exact branch reaches downstream but path-ranker visibility/usage is missing, do one post-ranker retry on the current post-analyze target before terminalizing: `path_ranker_integration.py --python-runner system --allow-direct-fallback --register-runtime-artifact`, then `apply-structural-path-ranking-external-scores`, `enable-structural-path-ranking-runtime --reuse-mode candidate_set_only`, rerun `analyze` and `workflow-status --refresh`. If ranker validation rows remain below gate or `execution_readiness < 0.45`, keep it as observation/scoped candidate and target the execution shortfall in the next overlay rather than tightening entries; `execution_readiness >= 0.45` clears only the return-to-duty/live-plane floor, while `>= 0.65` is the stronger `execution_ready` class. See `references/crwd5m-pda-soft-confirmation-downstream-retry-20260519.md`.
- Prefer structural follow-up once a fair search surface still re-selects defaults.
  reclaim stalls, but fallback-provider positives are incubate only. If a
  TradingViewMCP/YF VWAP reclaim Gate 1 is cross-symbol positive but sparse,
  cost-stress it and require IBKR/native-provider validation before BBN/CatBoost/
  execution-tree handoff. See `references/vwap-reclaim-provider-fallback-gate1.md`.
- Prefer structural follow-up once a fair search surface still re-selects defaults.
- Kraken/public full-ladder runs can produce mixed provider-symbol outcomes. If one sibling pair is invalid (for example `EQuery:Invalid asset pair`) but another symbol completes `1m/5m/15m/30m/1h/4h/1d` with real rows and AQ rank output, classify the completed symbol's Gate 1 and report the provider-symbol downgrade separately. Do not call the whole run provider-blocked, but also do not go downstream unless the completed symbol has positive/cost-surviving 1m origin density. See `references/kraken-full-ladder-partial-provider-gate1-stop-20260519.md`.
- If a fresh ORB/RVOL expansion family produces `one_minute_trades=0` and `positive_1m=[]` after a real provider/AQ ladder, stop at Gate 1 and pivot to a denser 1m entry family; sparse higher-timeframe rows are subclass evidence only and must not open Pre-Bayes/BBN/CatBoost/execution-tree. When cloning template runners, override material-level branch helpers (`branch_path_for_spec`, `branch_identity_for_spec`) and package namespaces, not only top-level `BRANCH_PATH`; otherwise canonical branch parity and provenance-label parity can be lost even if generic branch counters pass. See `references/regime-rooted-template-wrapper-and-orb-rvol-density-20260519.md`.
- Treat "profit factor" as a branch node under an exact main-regime root, not as a standalone global signal and not under market/symbol/timeframe roots. Required `branch_path` grammar: `main_regime -> sub_regime... -> first_profit_factor -> overlay_profit_factor...`. A regime node may point to another regime node or the first profit factor; a profit-factor node may point only to later profit-factor overlay nodes; node counts are unbounded, but each path must remain single-rooted and replayable. Preserve this canonical branch through filter/Pre-Bayes, BBN/workflow snapshot, CatBoost/path-ranker, and execution-tree artifacts. Default practical search starts at 1m and covers maximum feasible 5m/15m/30m/1h/4h/1d as labels/provenance. Base evidence requires realistic exact `5bps/side` cost survival with `trade_count > 0` and regime-root consistency; daily density and PDA are not base requirements. Promotion still requires downstream extension, validation, provider parity, AQ -> Pre-Bayes/BBN -> CatBoost -> execution-tree directional alignment, acceptable readiness/ranker state, and execution materialization; otherwise mark observation-only and never lower gates.
- If a 1m-origin branch fails Gate 1 but a higher-timeframe sibling is positive, that sibling may only continue by restarting as its own exact timeframe lane with timeframe/market/symbol recorded as labels and the same canonical main-regime branch preserved. Gate 1 cost survival can open Pre-Bayes/BBN readback, but if the exported policy target has `mature_rows=0` or `history_mature_rows=0`, keep `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, and `trade_usable=false`; do not treat path-ranker/CatBoost as merely optional. See `references/exact-timeframe-root-restart-and-maturity-blocker-20260519.md`.
- For Yahoo/IBKR futures symbols such as `GC=F`, `SI=F`, `ES=F`, or `NQ=F`, do not feed the raw ticker directly into Auto-Quant/Freqtrade pair whitelist. Preserve the raw provider symbol in metadata, but map the AQ pair to a sanitized synthetic pair such as `GCF/USD`, `SIF/USD`, `ESF/USD`, or `NQF/USD`; otherwise Gate 1 can fail with `No pair in whitelist` despite fresh provider rows. The sanitized-pair rerun should still preserve exact rooted identity and must not be called live-ready before downstream maturity/execution gates pass.
- For Yahoo/YF futures symbols (`GC=F`, `SI=F`, `ES=F`, `NQ=F`), a FreqTrade/Auto-Quant `No pair in whitelist` failure is a material pair-contract blocker, not a factor verdict. Preserve raw provider symbols in provenance, but map materials to sanitized pseudo-pairs such as `GCF/USD`, `SIF/USD`, `ESF/USD`, `NQF/USD`; keep the full raw-symbol exact branch in `consumer_evidence_profile`, cost-stress completed AQ rows, and restart any positive sibling as its own exact timeframe root. If downstream policy export has `mature_rows=0` / `history_mature_rows=0`, classify as `downstream_seed_maturity_blocked`, not live-ready. See `references/futures-symbol-sanitization-and-timeframe-root-gate1.md`.
- For futures full-ladder discovery, do not let a broad `symbol x timeframe x variant` dispatch become the admission gate. First formalize the exact 1m lane with a small 1m-only Auto-Quant rank and cost stress while keeping `branch_path` rooted at the main regime; keep `5m/15m/30m/1h/4h/1d` as provider/context evidence until the exact lane survives. If higher-timeframe futures rows are profitable but exact 1m is sparse or cost-negative, terminalize the 1m lane and restart any higher-timeframe survivor as its own exact timeframe-labeled lane under the canonical regime branch instead of opening Pre-Bayes/BBN/CatBoost/tree from the failed origin.
- Local TOMAC futures Auto-Quant wrappers that stage synthetic Freqtrade futures pairs such as `NQ/USD` or `XAU/USD` under `user_data/data/futures` can fail before Gate 1 with `run_tomac.py` return code `-15` after Freqtrade warns that `funding_rate` and `mark` `1h` history are missing. If `round_00_run_tomac.exit=-15`, `rank_rows=0`, and no metric block is emitted, classify the lane as `autoquant_oracle_failed` / runtime-data-contract blocker, not as negative economics. Do not rerun adjacent TOMAC futures families unchanged until the wrapper either stages auxiliary futures candle types or uses a verified non-futures synthetic contract that preserves costs and branch metadata.
- When a downstream wrapper is cloned from an older factor lane, add a contract check before replay: the source runner must preserve the full rooted branch including overlay nodes, point at the matching Auto-Quant material workspace, and carry the correct package namespace. If the wrapper truncates a PDA/MTF or session-liquidity overlay back to the base factor, terminalize the replay as contract-invalid and patch the runner before spending analyze/CatBoost/tree time. If `subprocess.TimeoutExpired` is caught in shared runner helpers, normalize `stdout`/`stderr` bytes to text before writing artifacts; otherwise a timeout can be masked by a `TypeError` and no terminal evidence is produced. A fresh replay that exports/ingests real trades but times out in `analyze` before CatBoost/tree is `downstream_runtime_timeout`, not promotion.
- If Gate 1 passes on a dense RSI/VWAP-style 1m-origin branch but downstream remains `execution_observe_only` / `transition_guardrail`, do not keep adding raw density. Inspect the current execution readback contract: readiness, transition/guard hints, alignment fields if still active, path-ranker visibility/usage, and mature/training rows. If current-schema execution remains guarded or below readiness/materialization gates, classify as `gate1_pass_downstream_fail_closed` and pivot to the active same-root execution blocker, not promotion. See `references/fintech-lending-rsi-vwap-downstream-fail-closed.md`.
- After every factor-training or autoresearch run, classify reusable lessons before finalizing:
  - scoring/search-surface pitfall -> patch this skill or `references/mutation-scoring-and-bottlenecks.md`
  - script/parser/run-isolation pitfall -> patch `references/factor-research-scripting.md`
  - runtime BBN/CatBoost/execution-tree lesson -> patch `ict-engine-runtime` or its reference
  - one-class CatBoost/path-ranker fallback lesson -> patch `references/catboost-single-label-ranker-fallback.md`
  - routing miss -> patch router and both skill indexes in the same slice
  - no reusable lesson -> final evidence must say `skill_update=not_needed` and why
- If a Gate 1 branch reaches downstream but CatBoost fails with `Target contains only one unique value` or `All train targets are equal`, treat it as an insufficient-label ranker problem, not branch proof. Use direct fallback only to verify score plumbing: run trainer `--apply --allow-direct-fallback`, register the artifact with its true model family (`weighted_feature_sum_v1` when `path_ranker_direct_model.json` says so), re-enable structural path ranking runtime, then rerun analyze/workflow/pre-bayes/policy. Do not promote unless execution tree admits the exact branch and ranker validation is sufficient. See `references/catboost-single-label-ranker-fallback.md`.
- **FactorContext with `&'a` references cannot derive Deserialize** — pass regime labels via `&HashMap` reference, not owned struct
- **Per-bar regime lookup needs HashMap keyed by timestamp** — backtest iterates bars, each needs regime at that timestamp
- **4-state HMM insufficient for trend strength** — use 8-state RegimeV2 for trend weak/strong split

## Post-training skillization gate

Before closing any ict-engine factor-training task:

1. Read the run artifact summary, commands, state-dir shape, and decisive failure/success branch.
2. Extract only durable lessons: repeatable pitfalls, validation gates, command order, state isolation, schema/field contracts, provider/runtime assumptions, or routing misses.
3. Put the lesson in the narrowest durable home:
   - this `SKILL.md` for class-level rules;
   - a `references/*.md` file for detailed command recipes or incident-specific evidence;
   - `ict-engine-runtime` references when the lesson crosses BBN/CatBoost/execution tree;
   - router/index files when Chinese intent should load the skill automatically.
4. Verify the skill/index diff before claiming the training lesson is preserved.

Bad closure: "训练完了，经验在聊天里".
Good closure: skill/reference patched, trigger indexed, final names changed paths.

## Agent traceability contract

Any agent entering this repo MUST be able to discover all factor families without scanning a 400KB+ TODO doc. Requirements:

- `AGENTS.md` at repo root: entry map with factor family → `FactorCategory` enum → code location → status table
- `docs/factor-catalog.md`: single-page index of all families (active code + design-only), with Rust coverage, missing subfactors, and priority
- When adding a new `FactorCategory` variant, update BOTH `AGENTS.md` and `factor-catalog.md` in the same commit
- If a family has zero code presence (no enum variant, no compute path), agents will grep and find nothing — this is the primary cause of "no usable factors" false negatives

### Hot-plug factor family addition checklist

When extending the factor registry:

1. Add variant to `FactorCategory` enum in `factor_definition.rs`
2. Add `as_str()` match arm
3. Add `is_footprint_context_only` match arm (if applicable)
4. Add `allowed_roles()` match arm
5. Add `FactorDefinition::<variant>()` constructor with parameters
6. Register in `FactorRegistry::default()` in `factors/registry.rs`
7. Add `evaluate` match arm in `FactorDefinition::evaluate()`
8. Add compute method `evaluate_<variant>()`
9. Add `mutation_parameter_group`, `mutation_direction_hint`, `mutation_step_size_hint` match arms
10. Move impl block BEFORE `#[cfg(test)] mod tests` — clippy rejects items after test module
11. Run `cargo check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`
12. Update `AGENTS.md` traceability table
13. Update `docs/factor-catalog.md` status column
14. Commit

### Pitfall: clippy items-after-test-module

Rust clippy rejects `impl` blocks appearing after `#[cfg(test)] mod tests {}`. All `impl` blocks for `FactorDefinition` (including hot-plug compute stubs) MUST be placed BEFORE the test module. If you add compute stubs at the file end, they will be after tests and fail clippy with `-D warnings`.

## Auto-Quant output path isolation

Auto-Quant artifacts MUST NOT pollute the repo root directory. The enforced path contract:

- Default: all auto-quant output goes to `<state-dir>/auto-quant/` subdirectory
- Override: `ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR` env var for user-specified custom path
- Implementation: `resolve_auto_quant_output_dir(state_dir)` in `main.rs`; all auto-quant shell functions route through `aq_state_dir()` in `auto_quant_command.rs`
- Factor research and analyze paths both apply hot-plug config via `FactorHotplugConfig::apply_to_registry_if_present(state_dir, &mut registry)`
- For agent training loops, choose `/tmp/ict-engine-...` state dirs by default.
  Do not preserve repo-local `state/`, `state_experiments/`, `.local-artifacts/`,
  `catboost_info/`, `path_ranker_model/`, ignored
  `support/docs/experiments/actionable-regime-confidence/runs/`, or loose
  `support/docs/plans/20*.md`/`actionable-regime-confidence/20*.md` scratch
  files unless the slice explicitly promotes them into tracked evidence or
  product surfaces.

## Hot-plug configuration

Users can disable any factor family at runtime via YAML config:

- Config file: `<state-dir>/factor_hotplug.yaml` (optional, absent = all enabled)
- Env var override: `ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` for custom path
- Rust module: `src/factors/hotplug.rs` — `FactorHotplugConfig` with `load()`, `apply_to_registry()`, `apply_to_registry_if_present()`
- YAML format: `families: { family_name: bool }` — missing keys default to true
- Dependencies: `serde_yaml = "0.9"` (note: serde_yaml 0.9 is deprecated but functional)

## What belongs in support files
- exact scoring formulas and bottleneck notes
- JSON parsing patterns and scripting pitfalls
- factor-family-specific bug notes
- cluster-jump mappings and autoresearch operational details

## Verification
- confirm isolated `state_dir` use for comparison experiments
- verify parser extracts top-level JSON correctly
- verify preview scorer reads mutated params, not hardcoded defaults
- verify whether defaults still win after fair isolated runs
- verify reusable training lessons were either written into a skill/reference or explicitly marked `skill_update=not_needed`

## Chinese triggers

`训练因子经验`, `因子训练经验`, `训练完沉淀skill`, `训练后更新skill`, `等待的时候做点有益的`, `等待窗口`, `因子知识储备`, `论文策略指标`, `factor training lessons`, `factor-research经验`, `autoresearch经验`, `mutation scoring经验`, `参数扫完沉淀`, `因子训练复盘`, `paper strategy reserve`, `factor source intake`, `claim/runtime waiting window`, `数据清洗`, `清洗工序`, `每笔 edge`, `交易密度`, `成本墙`, `ETH时间数据`, `数据可证`, `网上找新因子`, `candidate prefilter`, `data cleaning`, `per-trade edge`, `trade density`, `cost wall`, `ETH time data`, `手续费未知`, `交易费率`, `佣金模型`, `期货手续费`, `期货费率`, `股票手续费`, `个股费率`, `ETF费率`, `ETF手续费`, `期权手续费`, `期权佣金`, `fee model`, `commission model`, `cost model`, `futures commission`, `futures cost model`.

## See references
- `references/mutation-scoring-and-bottlenecks.md`
- `references/factor-research-scripting.md`
- `references/hmm-regime-validation-tools.md`
- `references/ibkr-crossasset-large-sample-sweep.md`
- `references/auto-quant-timeframe-ladder-fail-closed.md`
- `references/options-proxy-auto-quant-practicalization.md`
- `references/ibkr-options-timeframe-ladder-tree-handoff.md`
- `references/ibkr-3m-ladder-provider-blocker-cache-replay.md`
- `references/paper-repo-alpha-intake-to-auto-quant.md`
- `references/instrument-cost-model-verification.md`
- `references/futures-contract-cost-models-ibkr.md`
- `references/data-cleaning-and-candidate-prefilter-20260601.md`
- `references/high-window-reclaim-tree-handoff.md`
- `references/ibkr-high-window-reclaim-1m-mtf-gate.md`
- `references/regime-rooted-mtf-provider-ladder.md`
- `references/regime-rooted-branch-grammar-and-provider-blocker-20260518.md`
- `references/single-stock-refinement-aq-parity.md`
- `references/tod-slot-alpha-cost-gate.md`
- `references/regime-rooted-branch-and-cost-stress.md`
- `references/regime-rooted-gate1-cost-density-negative-sample.md`
- `references/regime-rooted-mtf-provider-ladder.md`
- `references/source-backed-candidate-triage-after-provider-blocker.md`
- `references/waiting-window-factor-research.md`
- `references/2026-05-30-paper-strategy-reserve.md`
- `references/2026-05-30-crossasset-carry-risk-reserve.md`
- `references/tomac-6e-multiday-trend-pullback-negative-20260530.md`
- `references/source-backed-tod-slot-alpha-autoquant.md`
- `references/auto-quant-autoresearch-seeding.md`
- `references/tomac-local-futures-nq-xau-continuation-20260521.md`
- `references/forward-watchlist-provider-parity.md`
- `references/vwap-reclaim-provider-fallback-gate1.md`
- `references/execution-gate-readiness-diagnostics.md`
- `references/binance-strict-1m-downstream-timeout-and-small-window-replay.md`
- `references/gate1-positive-downstream-fail-closed-parity.md`
- `references/beauty-transition-stable-overlay-v5-downstream.md`
- `references/beauty-transition-stable-overlay-v5-downstream-provider-parity.md`
- `references/repo-wide-live-ready-audit.md`
- `references/candidate-microtuning-live-readiness.md`
- `references/catboost-single-label-ranker-fallback.md`
- `references/regime-rooted-gate1-downstream-20260518.md`
- `references/regime-rooted-gate1-downstream-20260518.md`
- `references/max-window-density-before-downstream.md`
- `references/same-root-overlay-origin-sibling-gate.md`
- `references/rooted-gate1-cost-stable-training-20260519.md`
- `references/qqq-opening-impulse-zero-trade-density-pivot-20260519.md`
- `references/gate-bool-reverse-and-timeframe-root-parity-20260519.md`
- `references/kraken-xlm-algo-compression-expansion-gate1-20260519.md`
- `references/kraken-crypto-full-ladder-origin-density-gate.md`
- `references/kraken-full-ladder-partial-provider-gate1-stop-20260519.md`
- `references/hack-cybersecurity-density-downstream-fail-closed.md`
- `references/ibkr-mnq1m-compression-breakout-session-liquidity-failclosed-20260520.md`
- `references/si5m-linreg-cost-survivor-downstream-failclosed-20260520.md`
- `references/regime-evidence-packet-persistence-20260523.md`

## Recent futures-index / precious-metals factor lesson

- ETH/full-session evidence is necessary but still not sufficient for this
  user's `trade_usable=true` objective. The 2026-05-30 MGC/COMEX Kalman fair
  value plus session VWAP slope reclaim full-ladder AQ run preserved
  `RangeReversion -> KalmanFairValue -> VwapSlopeReclaim -> ibkr_mgc1m_kalman_vwap_slope_reclaim_full_ladder_v1`, used retained IBKR MGC 202606 data
  with `1m=9660` rows and `5m/15m/30m/1h/4h/1d` context, and completed
  `21` AutoQuant materials with branch fields preserved. It still terminalized
  `autoquant_ranked_no_exact_1m_5bps_survivor`: exact `1m` best was
  `quality-1m` with `10` trades, raw `+0.94%`, `2bps/side=+0.54%`, but
  `5bps/side=-0.06%`. It survived the verified MGC IBKR broker-side cost model
  because actual cost converted to about `0.2127bps/side`, but that is not a
  substitute for the hard `5bps/side` Gate 1 stress target when the lane's
  declared objective is exact `1m` origin. HTF context rows that pass 5bps
  (`30m/1h/4h/1d`) are context or lead evidence only; they must not satisfy
  exact-origin Gate 1, downstream admission, `promotion_allowed`,
  `trade_usable`, or `update_goal` unless a new lane explicitly changes the
  origin timeframe and proves the full practical lifecycle for that origin.
- For IBKR futures profitability work, do not rerun a cost-surviving exact root unless the replay changes a real downstream predicate. The M2K `1m` RVOL/PDA consistency-floor branch survived Gate 1 at `5bps/side`, but stable downstream evidence still failed closed on `execution_candidate_status=no_trade`, high transition telemetry, historical `pda_hybrid_alignment=false`, and low readiness; a later small replay reproduced the blocker with worse readiness and a canonical full replay stopped incomplete after prior init. Treat this as execution-materialization/regime repair work, not factor discovery. Do not add more RVOL/PDA/liquidity micro-filters or duplicate Board rows unless the run materially changes exact execution candidate materialization, current active readiness/ranker state, or mature validation density.
- Auto-Quant autoresearch repair must preserve the exact rooted strategy family. A 2026-05-20 M2K `1m` RVOL/PDA consistency-floor repair successfully materialized the full retained-real `1m -> 5m/15m/30m/1h/4h/1d` ladder and made Auto-Quant data-ready, but the active AQ seed was generic `TomacNQ_KillzoneBreakout` on `M2K/USD` with `0` trades. Treat this as `autoresearch_repair_no_candidate_zero_trades`, not as an execution repair. The next AQ repair for a cost survivor must seed or import the exact short/PDA branch logic before running `run_tomac.py`; otherwise it only proves the control plane can run a generic zero-trade seed and should not move to Pre-Bayes/BBN/CatBoost/execution tree.
- Same-workspace simulated feedback is not an admission shortcut when analyze cannot materialize the execution tree. A 2026-05-21 canonical M2K `1m` RVOL/PDA consistency-floor simulated-admission rerun ingested `17` same-AQ-workspace trades and completed import, Pre-Bayes, policy export, CatBoost train/apply, score import, trainer registration, runtime enable, and final readbacks, but both analyze passes timed out and the final metrics stayed `exact_branch_survived=false`, `mature_rows=2`, `history_mature_rows=18`, `ranker_validation_ready=false`, `execution_readiness=0.0`, `transition_hazard=1.0`, and historical `pda_hybrid_alignment=false`. Keep these packets observation-only; next same-root work must first bound analyze/execution materialization and directly repair current-schema readiness/ranker/materialization blockers, or rotate to a fresh IBKR historical cell with a true `5bps/side` survivor.
- A clean Gate 1 survivor plus clean downstream exits is still observation-only when the execution predicate trio fails. The 2026-05-21 Bybit `LINKUSDT/30m` Ichimoku exact branch preserved `TrendExpansion -> CryptoIchimokuCloudContinuation -> bybit_linkusdt_ichimoku_cloud_continuation_30m_exact_v1` and survived `5bps/side` (`19` trades, raw `+3.22%`, `5bps=+1.32%`). Exact downstream then completed import/prior, analyze, Pre-Bayes, CatBoost, score import, trainer registration, runtime enable, and final readbacks with all exits `0`, but remained fail-closed with execution candidate `no_trade`, `mature_rows=0`, `history_mature_rows=0`, `execution_readiness=0.4706894584861123`, `transition_hazard=0.9697034675842943`, `pda_hybrid_alignment=false`, and path-ranker score visible but not used by execution. Treat similar 30m/HTF exact survivors as useful mechanics/cost evidence only; require same-root maturity plus readiness, ranker consumption, and execution-materialization repair before promotion.
- Do not trust a stale prepare-only `terminal_metrics.json` after an Auto-Quant child exits. The Tomac synthetic-MTF shifted exact replay left `decision=prepared_exact_aq_replay_waiting_for_aq_slot` in metrics even though `checks/run_tomac.exit=0` and stdout contained the completed backtest (`338` trades, gross `+30.36%`, `2bps/side=+16.84%`, `5bps/side=-3.44%`). When process state and stdout/exit contradict metrics, classify from the completed command output, mark the wrapper hygiene issue, and do not downstream unless the real `5bps/side` gate survived.
- Do not treat a present live-process `.exit` file as current terminal truth when it predates the live process. `factor_claim_terminalization_audit.py --compact` can mark `attention_live_processes[].exit_file_state=stale_for_process`; use that as a warning that the root is still live and the old exit/stderr belongs to an earlier failed attempt. Keep the lane active until the current process exits and writes fresh terminal evidence.
- Completion audits for profitability-factor readiness must run the practical admission source surface, not only heavy compile/test/smoke gates. Unsafe downstream wrappers found by `support/scripts/research/downstream_practical_admission_source_check.py` are closure blockers when they map local `admitted`/`downstream`/decision strings into `promotion_allowed`, `trade_usable`, or `update_goal`, use 2bps survivor sets for downstream admission, mix trade-density floors into 5bps survival booleans, or retain retired PDA/transition fields as practical gate templates. As of 2026-05-28 this is wired into `support/scripts/done_definition_audit.py` as `practical_admission_source_surface`; do not claim done-definition or objective completion while that gate fails. The scanner must cover dict-literal practical flags, `dict(promotion_allowed=...)` keyword construction, retired-gate keyword construction such as `dict(pda_hybrid_alignment=True)`, and later subscript assignments such as `metrics["promotion_allowed"] = downstream_allowed`; explicit `False`, explicit false retired-gate telemetry markers, and values routed from `practical_admission_flags(..., extension_complete=...)` remain the safe patterns. Do not trust a helper by name/signature alone: its practical outputs must be explicit false or derive from `branch_local_admitted and extension_complete`, not `branch_local_admitted`, `branch_local_admitted or extension_complete`, or any other fail-open variant.
- Practical admission source scans must detect retired transition hard gates by
  semantics, not only by exact text. Alias forms such as `hazard_f < 0.60`,
  `hybrid_transition_hazard < 0.60`, tainted intermediate `hazard_ok`, or other
  branch-local admission expressions comparing a hazard value to `0.60` are the
  same retired gate and must fail the source surface. Keep transition/PDA values
  as telemetry only, with false requirement markers such as
  `transition_hazard_required=false` and `pda_required=false`. Current
  `done_definition_audit.py` source-scan timeout must be large enough for the
  current wrapper corpus; a scanner timeout is unresolved audit debt, not a
  clean pass and not completion evidence.
- A very strong exact Gate 1 survivor is still not live-practical if downstream cannot materialize same-root workflow/execution state. The Tomac `NQ/1m` OR15 breakout continuation exact replay produced `1283` AQ trades with `5bps/side=+217.60%`, but downstream manual readback failed closed: seed analyze ended `-15`, workflow stayed `no_workflow_state`, exact branch survival was false, no execution candidate/tree materialized, raw-scored mature validation was only `1/30`, and hard predicates were unavailable/false (`execution_readiness=0.0`, `transition_hazard=1.0`, `pda_hybrid_alignment=false`). Treat such packets as priority execution-materialization repair leads, not promotion; the next work should bound analyze/runtime state creation before adding simulated feedback or overlays.
- Multi-timeframe KST/Coppock trend confirmation can be dense enough to occupy a full retained TOMAC NQ window while still failing hard economics. The local TOMAC NQ `KST/Coppock` Gate 1 scan preserved `TrendExpansion -> NasdaqKstCoppockTrendContinuation -> kst_coppock_mtf_continuation -> tomac_nq_kst_coppock_trend_gate1_v1` across `5,302,713` retained 1m rows and `4,652` sessions with a full `1m -> 5m/15m/30m/1h/4h/1d` ladder, but produced `0` same-root hard `5bps` plus cadence survivors and `0` sparse positive `5bps` rows. The best row was `tomac_nq_kst_coppock_trend_long_quality_ctx4_slope16` with `1,426` trades, `0.30653` trades/session, `5bps=-121.46%`, and PF `0.2973`, failing both the one-trade-per-three-sessions floor and economics. Treat this as a clean negative boundary for standalone NQ KST/Coppock trend-continuation: no downstream, paper/sim, promotion, trade usability, or goal completion; if revisited, it must be a materially different rooted repair or protective overlay on an already cost-surviving trend root.
- Standalone 6E/EUR DMI/ADX trend continuation is a clean negative boundary on the retained TOMAC full window. The local TOMAC 6E `DMI/ADX` Gate 1 scan preserved `TrendExpansion -> EuroFxDmiAdxTrendContinuation -> dmi_adx_mtf_continuation -> tomac_6e_dmi_adx_trend_gate1_v1` across `3,818,325` retained 1m rows and `3,423` sessions with a full `1m -> 5m/15m/30m/1h/4h/1d` ladder, but produced `0` same-root hard `5bps` plus cadence survivors and `0` sparse positive `5bps` rows. The best row was `tomac_6e_dmi_adx_trend_short_quality_dmi28_a4` with `318` trades, `0.09290` trades/session, `5bps=-30.48%`, and PF `0.0972`, failing both the one-trade-per-three-sessions floor and economics. Treat this exact 6E DMI/ADX cell as terminal negative evidence: no downstream, IBKR paper/sim, promotion, trade usability, or goal completion; next fresh trend-only work should rotate symbol/family or use DMI/ADX only as a protective overlay on an already cost-surviving trend root.
- Strict SuperTrend/ATR MTF resonance can over-filter a plausible trend-following idea into zero-trade evidence. The retained TOMAC XAU/GC `SuperTrend/ATR` Gate 1 resume preserved `TrendExpansion -> GoldSupertrendAtrTrendContinuation -> supertrend_atr_mtf_continuation -> tomac_xau_gc_supertrend_atr_trend_gate1_v1` across `1,766,247` retained 1m rows from `2021-01-06` through `2025-12-31` with a full `1m -> 5m/15m/30m/1h/4h/1d` ladder, but all six long/short dense/balanced/quality variants had `trade_count=0`, `survivors_5bps=0`, `promotion_allowed=false`, and `trade_usable=false` (`/tmp/ict-engine-tomac-xau-gc-supertrend-atr-trend-gate1-20260525T060356+0800/checks/terminal_metrics.json`). Treat this as a terminal negative boundary for this exact XAU/GC SuperTrend/ATR resonance cell: no downstream, IBKR paper/sim, promotion, trade usability, or goal completion. Future trend-only work should not assume "顺势 + 多周期共振" is automatically profitable; first verify that resonance thresholds still produce real trade density, then cost survival, before any paper/sim or downstream handoff.
- TOMAC is not exhausted just because prior strict OTE/TOD/KST/SuperTrend cells failed. A 2026-05-25 retained-local long-history fast screen over ES/NQ/YM/6E 1m rows (`/tmp/ict-engine-tomac-long-history-trend-pullback-scan-20260525T1229+0800`) found dense positive *leads* under `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> non_ote_dense_trend_pullback_v1`: `192` candidates, `49` rows positive after `5bps/side` plus the one-trade-per-three-sessions cadence floor, with best NQ short fixed-hold lead `1998` trades, `0.5837` trades/session, `net_5bps=+25.8588`, PF `6.0778`. Do not call these trade-usable: the scan used vectorized fixed-hold scoring and proxy MTF slopes, so the next same-root step must run strict stop/target, leakage/year-split, exact branch preservation, Auto-Quant/downstream validation, and current readiness/ranker/execution materialization before promotion. Use this as evidence to continue TOMAC long-history trend-root mining, not as permission to say the strategy is ready.
- The same TOMAC long-history fixed-hold leads can disappear under executable stop/target validation. A same-root strict replay of the top NQ/YM leads (`/tmp/ict-engine-tomac-nq-ym-non-ote-strict-validation-20260525T1242+0800`) preserved `TrendExpansion -> RootEvidencePullbackMssCisd -> strict_trend_root_pullback_mss_cisd -> non_ote_dense_trend_pullback_v1 -> strict_stop_target_split_validation_v1`, selected `16` parent leads, and tested `80` explicit ATR stop/target candidates with year splits. It produced `0` strict survivors; the best row still had high density (`3494` NQ trades, `1.0207` trades/session) but failed economics and robustness (`net_5bps=-4.0965`, PF `0.1469`, positive-year fraction `0.0`). Treat the prior fast-screen packet as useful lead-generation only and this strict packet as a negative boundary for naive non-OTE short pullback stop/target execution. Do not downstream, Auto-Quant, paper/sim, promote, or call trade-usable unless a later same-root repair changes the executable exit/risk structure and passes hard `5bps/side`, cadence, and year-split robustness.
- Standalone 6E/EUR RWI/ATR trend continuation is another dense negative boundary on the retained TOMAC full window. The 2026-05-25 scan (`/tmp/ict-engine-tomac-6e-rwi-atr-trend-gate1-20260525T125409+0800`) preserved `TrendExpansion -> EuroFxRandomWalkAtrTrendContinuation -> rwi_atr_mtf_continuation -> tomac_6e_rwi_atr_trend_gate1_v1`, used `3,825,696` retained 6E `1m` rows over `3,423` sessions with derived `15m/1h/1d` slope context, and tested `8` explicit RWI/ATR stop-target candidates with hard `5bps/side` plus year-split robustness. It produced `0` strict survivors; the best row was `tomac_6e_rwi_atr_trend_long_rwi1p55_adx26_h180_pt3p0_st1p5` with `2,420` trades (`0.7070` trades/session), `net_5bps=-258.2100%`, PF `0.0176`, and positive-year fraction `0.0`. Treat this exact 6E RWI/ATR cell as terminal negative evidence: no downstream, Auto-Quant, IBKR paper/sim, promotion, trade usability, or goal completion. Do not repeat standalone 6E RWI/ATR unless the next hypothesis materially changes the cost/churn structure or uses it only as a protective overlay on an already cost-surviving trend root.
- Clean retained TOMAC futures mining must filter ES/YM spread contracts and absurd bar returns before interpreting broad-screen rows. A 2026-05-25 `/tmp` cleaner (`/tmp/ict-engine-tomac-clean-futures-alpha-miner-20260525T180230+0800`) fixed the prior broad-screen artifact class by filtering ES `845888` spread rows plus `2` absurd-return rows and YM `235167` spread rows plus `3` absurd-return rows, while NQ had no such filtered rows. The clean ORB/TOD low-turnover family preserved `TrendExpansion -> SessionLiquidity -> LowTurnoverOpeningRange -> <factor>` and tested ES/YM/NQ retained-real `1m` histories with hard `5bps/side` and density from one trade per three sessions to three trades per session. It produced `0/18` Gate 1 survivors; a NQ selective ORB repair then tested `72` lower-churn candidates and also produced `0` survivors. Best dense NQ rows were positive gross but negative after `5bps/side`, while best selective rows reduced churn below the cadence floor before cost survival. Treat standalone clean ORB/TOD on these TOMAC futures as terminal negative evidence; next retained-real futures mining should rotate to a materially different family such as volatility-contraction breakout, asymmetric trend pullback, or session carry, and must keep the same spread/return-sanity filters before any downstream/AQ/paper-sim decision.
- TOMAC DailyDonchian `MaxHold3120` remains a near-practical positive-cost seed but not a practical factor after the 2026-05-29 `UncoveredSessionComplement` readback. The local scan at `/tmp/ict-engine-tomac-daily-donchian-uncovered-session-complement-launch-20260529T034904+0800` preserved `TrendExpansion -> DailyDonchianTrendContinuation -> SwingBreakoutContinuation -> DensityRepairPortfolio -> CadenceFloorRotationGuard -> UncoveredSessionComplement -> tomac_idxfut_daily_donchian_uncovered_session_complement_1m_origin_v1`, used the parent `MaxHold3120` portfolio, and ranked only positive 5bps DailyDonchian components by incremental trade-session coverage outside the parent active sessions. It completed with `coverage_exit=0`, `scan_exit=0`, `candidate_count=144`, `parent_component_count=4`, `selected_component_count=0`, `incremental_uncovered_sessions=0`, and decision `reject_no_uncovered_positive_components`. The parent 5bps economics stayed positive but below the practical density floor: `479` trades over `1556` sessions, `trades_per_all_session=0.307840616966581`, `5bps_net_ret=0.2641846131032113`, and PF `1.1395099627411625`. Do not rerun `UncoveredSessionComplement`, `SessionCoverageExpansion`, `HoldCompressionCadenceLift`, `HoldCompressionSymbolBalanceGuard`, or `Lb55SessionBridge` unchanged. Future DailyDonchian work needs a materially different density mechanism that creates new positive-cost trade days without merely reselecting already-covered positive 5bps components; until then keep downstream, provider/AQ, paper/sim, promotion, trade usability, and goal completion false.
- TOMAC OpeningDrive exact-parent false-negative amnesty changed the practical materialization semantics but not the promotion gate. For `tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1`, do not resurrect the old `execution_readiness >= 0.65` or `transition_hazard < 0.60` hard blocker language: current same-root materialization code uses `LIVE_EXECUTION_READINESS_FLOOR = 0.45`, and transition hazard is telemetry unless a separate current-schema gate explicitly consumes it. However, local admission is still not trade usability. Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` unless `path_ranker_score_used_by_execution_tree=true` and the full same-root practical chain passes. The 2026-05-29 OpeningDrive code-prep packet verified this with TDD in `run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py`: readiness `0.457142...` can clear branch-local admission, while ranker-visible-but-not-used remains a hard live blocker. If a foreign TOMAC/AQ runtime is live, terminalize no-launch packets and retry only after compact audit and focused process guard clear.
- The same TOMAC OpeningDrive exact parent has a separate source-level leakage hazard. The source strategy `TomacNqBidirOpeningDrive.py` entered at `15:00 UTC` while computing direction from the `15:29 UTC` opening-range close. A 2026-05-29 Python-only replay under `/tmp/ict-engine-tomac-openingdrive-python-backtest-20260529T112054+0800` showed the source-exact replay stayed 5bps-positive (`+116.5144%` 5bps/side) but was explicitly lookahead; causal variants that entered only after the 15:29 close turned 5bps-negative (best causal `-56.7269%` 5bps/side). Do not treat the old OpeningDrive exact-parent AQ economics as practical evidence unchanged. Before any downstream materialization or promotion retry, repair the rule so signal availability precedes entry, then re-run causal Gate 1/cost/density validation; keep promotion/trade/update false until the repaired causal branch also passes ranker consumption and the full same-root practical chain.
- A broader 2026-05-29 OpeningDrive causal repair scan (`/tmp/ict-engine-tomac-openingdrive-causal-repair-scan-20260529T114648+0800`) tested `1008` no-lookahead after-OR specs (`entry_minute >= 15:30 UTC`, signal available at `15:29 UTC`). It found `9` small positive 5bps legacy-density pockets, but `0` Gate 1 survivors after split/year robustness; the best row (`tomac_nq_openingdrive_causal_continuation_thr60_e935_x1245_hold_short_v1`) had `133` trades, `5bps_per_side_total_profit_pct=+3.453057`, `positive_year_fraction=0.60`, and `split_5bps_consistent=false`. Treat this as demotion evidence for unchanged OpeningDrive exact-parent materialization. Do not retry downstream/AQ from OpeningDrive unless a materially different causal repair first passes 5bps, density, and split/year robustness; Python-only positives remain non-promotion evidence.
- A Python-only TOMAC KST/Coppock variant can be sparse 5bps-positive without being a Gate 1 survivor. The 2026-05-29 retained-feather prescreen under `/tmp/ict-engine-tomac-kst-coppock-pybacktest-20260529T112130+0800` preserved `TrendExpansion -> KstCoppockMomentum -> MtfTrendResonancePullback -> tomac_idxfut_py_kst_coppock_mtf_pullback_continuation_1m_v1` and produced one NQ `quality` row with `115` trades, `0.073907` trades/day, `5bps_per_side_total_profit_pct=+1.551312`, instrument-cost net `+12.668778`, and PF `1.99948`, but it failed the one-trade-per-three-days density gate. Classify this as `terminalized_pybacktest_sparse_positive_density_fail`, not `no_5bps_survivor`; record `full_gate1_survivor_count=0`, keep `promotion_allowed=false` / `trade_usable=false` / `update_goal=false`, and only revisit through a materially denser child that preserves the NQ quality 5bps economics before any clean-AQ/provider parity or downstream handoff.
