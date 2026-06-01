# Regime Evidence Packet Persistence - 2026-05-23

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this note when the task is Board A/root-regime evidence, especially when the
useful artifacts live in `/tmp`, `/private/tmp`, or the ignored repo
`support/docs/experiments/actionable-regime-confidence/runs/` tree.

## Rule

Tmp evidence and ignored run roots are not durable repo evidence. If a regime
classifier, Trend-root supplement, posterior audit, Pre-Bayes/BBN readback, or
95% confidence calibration should be consumed later, create a tracked compact
packet outside ignored paths and point the Board A current doc at that packet.

## Required Checks

1. Read the live Board A current doc before writing:
   `support/docs/plans/2026-05-12-board-a-regime-state-current.md`.
2. Check whether the proposed packet path is ignored:
   `git check-ignore -v <path> || true`.
3. If evidence is under `/tmp`, `/private/tmp`, or ignored `runs/`, summarize it
   into a tracked file such as:
   `support/docs/experiments/actionable-regime-confidence/<slug>_<date>.md`.
4. Keep raw local paths as audit handles only; do not claim they are repo
   consumer surfaces.
5. Update Board A with terminal decision language only: status, requirement,
   evidence packet path, metrics, allowed use, disallowed use, and
   `update_goal=false` unless the whole objective is genuinely complete.

## Regime-Only Boundary

When the user asks to run or preserve regime factors, do not open a profitability
factor lane. Board B/Gate 1/cost-density packets can be referenced only if they
directly prove regime posterior, Pre-Bayes, BBN, CatBoost/path-ranker, execution
tree, or 95% regime-confidence behavior. Otherwise skip them.

## 95% Confidence Audit Shape

For root-regime or Trend-root detector claims, preserve:

- bull and bear precision/accuracy separately
- support count and minimum-count decision
- split discipline, for example train/calibrate/test windows
- whether labels are point-return, persistent segment, cross-market, volatility,
  macro, session, or execution-native
- root registration decision
- allowed supplemental use and disallowed promotion/trading use

If either bull or bear side misses 95%, or high precision has too few rows, the
packet is observation/negative-boundary evidence only.

## 2026-05-23 TOMAC Bayesian/Markov Lesson

TOMAC NQ/XAU Bayesian/Markov and supervised calibration evidence from
`/private/tmp` was useful but negative. It proved the current detector should not
be registered as a 95% bull/bear root classifier:

- NQ synthetic HMM `p>=0.95`: about `53.91%` bull and `45.85%` bear 390m
  direction accuracy.
- Best 2025 shape search: `82.41%` bull over `108` rows, `64.90%` bear over
  `151` rows.
- NQ point-return, persistent segment, NQ/ES, NQ/YM, NQ/EUR, FRED vol, and XAU
  supervised variants all failed the 95% two-sided requirement.

Durable tracked packet:
`support/docs/experiments/actionable-regime-confidence/tomac_regime_confidence_tmp_evidence_20260523.md`.

Related Trend-root supplement packet:
`support/docs/experiments/actionable-regime-confidence/bayesian_markov_trend_supplement_20260523.md`.

## 2026-05-23 Positive/Negative Feedback Ingress Lesson

Training material from Board A regime/subclass runs must not be discarded just
because Gate 1 or downstream promotion fails. Positive rows should feed the
rooted branch as Bayesian support; zero, negative, and failed rows should feed
the same rooted branch as negative boundary samples.

Use the existing repo surfaces first:

- emit `structural-feedback-v1` JSON with
  `support/scripts/auto_quant_external/structural_feedback_trade_enricher.py`
- ingest with `ict-engine update --feedback-file <json>`
- verify with `workflow-status`, `pre-bayes-status`,
  `policy-training-status`, and `export-structural-path-ranking-target`

For negative PnL values, pass the CLI option as `--pnl=<negative-value>` so the
argument parser does not treat the value as a new flag. If target rows include a
distinct `path_id`, preserve it; do not collapse every row to the branch path or
negative boundary samples lose identity.

Durable tracked packet:
`support/docs/experiments/actionable-regime-confidence/board_a_positive_negative_feedback_ingress_packet_20260523.md`.

Second rooted-branch packet:
`support/docs/experiments/actionable-regime-confidence/board_a_spy_session_compression_feedback_ingress_packet_20260523.md`.

Reusable decision rule: feedback ingress repair is observation/training evidence
only unless readbacks also prove validation maturity, calibration, runtime
selection, and execution-tree consumption. The first sampled run with `8`
feedback rows and `observation_validation=8/30` was useful but not promotion.
The follow-up full available-row replay ingested all `15` source AQ rank rows
(`2` wins, `13` losses) and improved to `observation_validation=15/30`, but it
still remained below validation maturity with `production_validation=0/30`,
`calibration=not_fitted`, `trainer_artifact=missing`, and
`runtime_selection=disabled`. Do not call a feedback-ingress repair a `95%`
confidence closure or execution promotion while any of those gates remain open.

Reusable runner note: the Board A ingress runner now accepts explicit
`--rank-json`, `--source-run`, `--symbol`, and `--candidate-set-id`. Use this to
feed additional Board A regime/subclass rank artifacts through the same audited
path instead of cloning one-off scripts. The 2026-05-23 SPY SessionLiquidity
replay ingested `1` positive and `2` negative rows on
`TrendExpansion -> SessionLiquidity -> session_compression_breakout`, proved
`matched_rows=3` and `outcomes=loss=2,win=1`, and stayed observation-only with
`raw_scored_mature=3/30`, `production_validation=0/30`,
`observation_validation=3/30`, `calibration=not_fitted`,
`trainer_artifact=missing`, and `runtime_selection=disabled`.

Aggregate-state lesson: if several small Board A feedback packets each remain
below validation gates, replay the existing Board A rank artifacts into one
explicit aggregate symbol bucket before trying CatBoost/runtime. The 2026-05-23
aggregate replay used `14` existing `*board-a*` rank JSON artifacts and `47` AQ
rank rows (`9` wins, `38` losses) across `TrendExpansion` subclasses,
`RangeConsolidation -> InsuranceDefensivePremiumCycle`, `BoardA ->
CrossMarketRegime95`, and `BoardA -> IBKRIntradayOptions`. In the aggregate
state, the path-ranker moved from observation-only to runtime-visible CatBoost:
`raw_scored_mature=47/30`, `production_validation=120/30`,
`observation_validation=47/30`, `calibration=evaluated`,
`trainer_artifact=ready`, `runtime_selection=enabled_candidate_set_ready`,
`score_model_family=catboost`, and `runtime_matches=3`.

Durable tracked aggregate packet:
`support/docs/experiments/actionable-regime-confidence/board_a_aggregated_rooted_feedback_ranker_packet_20260523.md`.

Do not overclaim this pattern. Even with aggregate CatBoost/runtime visible, the
2026-05-23 workflow stayed fail-closed with `candidate_status=execution_blocked`,
`pre_bayes_gate_status=pass_neutralized`, no latest execution candidate, no
path-ranker score visibility/use by the execution tree, and no parent-root
`>=95%` confidence proof. Treat aggregate feedback/ranker closure as a repair
lead toward execution materialization and root confidence, not as registration,
trading, or goal completion.

## 2026-05-23 Heterogeneous TMP Inventory Lesson

Do not stop after harvesting the first obvious topic cluster from `/tmp` or
`/private/tmp`. If the user asks to preserve tmp evidence, sweep for all terminal
summaries and terminal metrics, then create a compact inventory packet when the
raw roots are heterogeneous.

Durable tracked inventory packet:
`support/docs/experiments/actionable-regime-confidence/tmp_terminal_evidence_inventory_20260523.md`.

This packet preserved TOMAC Time-of-Day SessionRhythm evidence, TOMAC local
futures negatives, reconstruction/parity failures, local CSV MTF boundaries,
IBKR Bayesian-Markov Gate 1 negatives, downstream fail-closed readbacks, and
claim-terminalization audits. The key reusable lesson is that a 5bps Gate 1
survivor is not enough when downstream still fails exact branch survival,
execution candidate materialization, transition hazard, PDA alignment, execution
readiness, or mature validation rows. Keep such material as observation or a
same-root repair lead only; do not open a new profitability lane during evidence
preservation.

## 2026-05-23 TMP Delta Index Lesson

After creating a broad tmp inventory, run a path-level diff before assuming more
tmp evidence is lost. The useful command shape is:

```text
find /tmp /private/tmp -maxdepth 4 \
  \( -name terminal_decision_summary.md -o -name terminal_metrics.json \
     -o -name '*artifact_validation.json' -o -name '*terminalization*.json' \
     -o -name 'regime_confidence_assets_v1.csv' -o -name '*bayesian*json.ok' \
     -o -name '*trend_spec*json.ok' \)
```

For the 2026-05-23 sweep, this returned `192` evidence handles. An exact path
diff against the first inventory packet showed `missing=158`, so the durable fix
needed two layers: a full-handle manifest plus a semantic delta packet. The
semantic gap covered CSV export roots, Bayesian-Markov sentinels,
claim-terminalization snapshots, TOMAC PSAR/Aroon/CCI, Pivot/CPR/Camarilla, ICT
sweep-reality, and Gate-1-survivor/downstream-failed readbacks.

Durable tracked delta packet:
`support/docs/experiments/actionable-regime-confidence/tmp_terminal_evidence_delta_index_20260523.md`.

Durable tracked full-handle manifest:
`support/docs/experiments/actionable-regime-confidence/tmp_terminal_evidence_full_handle_manifest_20260523.md`.

Reusable rule: if path coverage is complete but the user says usable tmp evidence
is still not preserved, create a semantic delta index instead of launching a new
profitability lane. The delta must say which handles are asset-export parity,
format sentinels, collision hygiene, negative family coverage, same-root repair
leads, or non-promoting downstream blockers.

## 2026-05-23 Deep Regime Evidence Lesson

Terminal-summary sweeps can still miss regime-calibration evidence. TOMAC
Bayesian-Markov calibration roots stored the most important regime-only outputs
as `summary.json`, `threshold_table.csv`, `high_confidence_events.csv`, and a
standalone terminal report, so the terminal handle manifest did not enumerate
them even though the earlier semantic packet referenced some paths.

When the user says tmp still has usable evidence after a full terminal manifest,
run a second regime-specific sweep for names like:

```text
summary.json
threshold_table.csv
high_confidence_events.csv
calibration_search.json
calibration_search.csv
*regime_calibration_terminal_report*.md
```

For 2026-05-23 this recovered the deep TOMAC regime handles for NQ synthetic
Bayesian-Markov posterior, 2025 calibration search, supervised h390/h1440,
persistent segment labels, NQ/ES, NQ/YM, NQ/EUR, FRED volatility sidecar, and
XAU/GC supervised calibration. The result remained negative: no branch met
calibrated bull and bear `>=95%` with meaningful support.

Durable tracked deep manifest:
`support/docs/experiments/actionable-regime-confidence/tmp_deep_regime_evidence_manifest_20260523.md`.

Reusable rule: deep regime evidence should be packetized as root-regime or
Trend-root observation evidence only unless it proves both sides of the `95%`
requirement with support. Do not convert the preservation task into a
profitability-factor run.

## 2026-05-23 Legacy TMP Export/Taxonomy Lesson

After terminal-summary, full-handle, semantic-delta, and deep-regime sweeps, tmp
can still contain usable Board A evidence inside old export or verification
trees. Look for copied repo subtrees such as:

```text
/private/tmp/ict-engine-cli-slice-verify/
/private/tmp/ict-engine-privacy-audit-export-*/
```

Within those trees, search for root/subclass regime packets and schema/crosswalk
artifacts:

```text
evidence_packet*.json
*regime*_report.json
*regime*_summary.csv
*crosswalk*.json
*schema*.json
*audit*.json
```

For 2026-05-23 this recovered durable Board A taxonomy evidence that was not a
fresh TOMAC calibration file and not a terminal summary:

- multi-regime expansion accepted `0` new `95%` or `99%` regimes.
- per-regime coverage preserved `SessionLiquidityCoreViable` and
  `ThinLiquidity` but still missed `TrendExpansion`, `RangeConsolidation`,
  `ExtremeStress`, and `ReversalBrewing`.
- cross-market validation covered `QQQ IBKR 1h`, `QQQ yfinance 1h`, `NQ CME
  15m`, and `PF_XBTUSD Kraken 1h`, but accepted no new `95%` regime.
- MainRegimeV2 parent/child crosswalk preserved only prior `Crisis` root
  evidence and left `Bull`, `Bear`, `Sideways`, and `Manipulation` missing.

Durable tracked packet:
`support/docs/experiments/actionable-regime-confidence/legacy_tmp_regime_taxonomy_evidence_20260523.md`.

Reusable rule: old tmp export trees often contain the root/subclass contract
itself. Preserve those as Board A taxonomy/coverage evidence. Do not promote a
child label such as `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`,
`ThinLiquidity`, or `SessionLiquidityCoreViable` into a root unless a later
packet emits the exact calibrated parent root with unchanged gates. Do not open
Board B/profitability work when the task is to preserve these regime packets.

## 2026-05-23 Split-Semantics TMP Readback Lesson

A full-handle manifest and broad inventory can still leave important Board A
meaning too fragmented for root/regime consumers. If tmp evidence is split
across terminal summaries, standalone workflow/analyze JSON readbacks, and
exported CSV assets, create one tracked semantic packet that joins the evidence
by regime branch and states the consumer decision explicitly.

For 2026-05-23 this applied to TOMAC `SessionRhythm` evidence and repeated
`regime_confidence_assets_v1.csv` exports:

- scoped source-backed Bull/Bear/Sideways/Crisis asset exports proved Board A
  asset-export parity, not TOMAC Bayesian-Markov proof.
- TOMAC Cap65 and drop-bad-component overlays had dense positive Gate 1 style
  evidence, but downstream remained fail-closed on exact branch survival,
  transition hazard, PDA alignment, readiness, and mature validation.
- provider-native IBKR NQ fetched a large real `1m` union but reproduced `0`
  same-root trades for the tested component.
- standalone workflow JSON readbacks preserved posterior details such as
  `range` active regime, `pass_neutralized`, read-only BBN branch context, and
  `read_only_regime_bbn_trade_usable=false`.

Durable tracked packet:
`support/docs/experiments/actionable-regime-confidence/tmp_sessionrhythm_regime_asset_semantic_packet_20260523.md`.

Reusable rule: when semantics are split, do not answer by pointing at raw tmp
paths or launching a new factor. Write the compact semantic packet, update Board
A terminal status, and keep all decisions non-promoting unless the packet itself
proves calibrated root-regime `95%` requirements and same-root downstream
admission.

## 2026-05-23 Runtime Root-Coverage Matrix Lesson

The native `regime-confidence-assets --output-format json` readback is a runtime
asset inventory, not a promotion event. When it is used for Board A/root-regime
work, convert it into a tracked root/subclass coverage matrix with one row per
root and with explicit asset classes such as `accepted_95_scope_limited`,
`diagnostic_source_control_absent`, `direct_event_overlay`,
`bounded_not_full_coverage`, and `contrast_evidence`.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/runtime_regime_root_coverage_asset_readback_20260523.md`.

Reusable rule: scoped accepted Bull/Bear/Sideways/Crisis assets may be preserved
as Board A gate evidence, but they do not enable runtime registration while
`runtime_selection_enabled=false` and `promotion_allowed=false`. Manipulation
must stay direct-event/bounded-overlay evidence until full parent-root coverage
passes. MainRegimeV2 blockers such as source-confidence labels `0/4`, provider
preflight accepted contexts `0`, strict exact support `41/156`, and unavailable
long-horizon provider acceptance must remain visible as blockers. Do not treat
this readback as Board B profitability evidence or as Trend-root promotion.

## 2026-05-23 Regime Asset Closure-Intake Lesson

`factor-asset-closure-intake` is useful for proving recovered Board A assets can
enter closed-loop policy/artifact/ranker surfaces, but it does not substitute for
a real provider/analyze loop. Run it in an isolated state and then read back
`artifact-status`, `policy-training-status`, `workflow-status`,
`pre-bayes-status`, and `export-structural-path-ranking-target` before claiming
anything about gate movement.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_regime_asset_closure_intake_readback_20260523.md`.

Reusable rule: if intake creates candidate/admission rows and a direct ranker
model, it is acceptable to register and enable that model in the isolated state
as `candidate_set_only` to test readback visibility. Still classify the result
as observation-only unless there is a current provider/analyze posterior,
nonempty Pre-Bayes/BBN workflow state, current execution candidate, execution
tree consumption, and observation validation. A typical fail-closed shape is
`raw_scored_mature=35/30` and `production_validation=35/30` but
`observation_validation=0/30`, with workflow stuck on bootstrap readiness and no
execution candidate. This is Board A admission-surface wiring evidence, not
Board B profitability work and not trade usability.

## 2026-05-23 SessionRhythm Component-Pair Guard Lesson

A tmp-only TOMAC component overlay can be useful Board A subclass evidence even
when it looks like a dense cost-stressed survivor. Preserve it as a regime
packet only if the packet states the whole downstream verdict, not just Gate 1.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/tmp_sessionrhythm_component_pair_guard_packet_20260523.md`.

Reusable rule: when a `SessionRhythm` child branch reaches dense exact replay but
downstream remains fail-closed, classify it by execution predicates. The
component-pair guard produced `1556` real trades at `1.0` trades/session and
`29.22%` at 5bps/side, then ran Auto-Quant import/prior, Pre-Bayes, CatBoost,
ranker register/enable, workflow, and execution-tree readbacks with exit `0`.
It still stayed observation-only because execution candidate was `no_trade`,
execution tree was `observe`, `execution_readiness=0.37842405925447914`,
`hybrid_transition_hazard=0.9890169170703277`, `pda_hybrid_alignment=false`, and
observation validation stayed `0/30`. Do not reopen this as Board B profitability
work; use it as `SessionRhythm` subclass evidence and a transition/PDA/readiness
repair lead unless a later packet proves calibrated parent-root confidence and
same-root execution admission.

## 2026-05-23 Release-Archive Regime Parity Lesson

Release/export worktrees under `/private/tmp/ict-engine-release-*` and
`/private/tmp/ict-engine-v0*` can mirror useful Board A regime-confidence
evidence. They are not durable consumer surfaces by themselves, and repeated
copies are parity mirrors rather than independent acceptances.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/tmp_release_archive_regime_confidence_parity_packet_20260523.md`.

Reusable rule: when release/archive mirrors contain `regime_confidence_assets`,
`regime_high_confidence_decision`, gap-map, provider-path, or context-split
artifacts, preserve the semantic decision in a tracked Board A packet. Accepted
subclass guardrails such as `SessionLiquidityCoreViable` at `95%` and field
complete sets at `95%` remain non-tradeable and non-root unless the runtime
posterior also reaches calibrated parent-root probability and the execution tree
materializes a ready/actionable same-root candidate. A typical archive gap-map
can have CatBoost runtime visible (`raw_scored_mature=237/30`,
`production_validation=237/30`) while active regime probability is still below
`0.95` and execution remains `observe`; that is negative root-calibration
evidence, not a Board B profitability lane.

## 2026-05-23 HGB Numeric Source-Control Diagnostic Lesson

HGB numeric confidence rows can look like solved parent-root evidence because
their split Wilson lower bounds exceed `0.95`, but in Board A they remain
diagnostic until source/control evidence is present and a downstream promotion
rerun exists. Preserve them in a tracked packet when the details are only in
ignored run roots or long current-doc rows.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_hgb_numeric_source_control_diagnostic_packet_20260523.md`.

Reusable rule: keep HGB rows under `diagnostic_after_source_control_unlock` when
`source_control_evidence_acquired=false`, `canonical_merge=false`, or
`downstream_promotion_rerun=false`. Even if `Bear`, `Bull`, `Crisis`, and
`Sideways` all have accepted diagnostic LCBs (`0.9787578642`, `0.9908918883`,
`0.9930261988`, `0.990666799` respectively), do not register roots or open
profitability work from them. `Manipulation` is absent from this HGB set, and a
real provider -> Auto-Quant -> Pre-Bayes/BBN -> CatBoost/path-ranker ->
execution-tree chain must run after unlock before promotion is reconsidered.

## 2026-05-23 Regime Consumer Bundle Adapter Tmp-Test Lesson

Tmp-only adapter stdout/stderr can be important Board A evidence when it proves
how accepted regime bundles enter the runtime. Preserve it as a tracked packet
if the only durable handle is under `/private/tmp`.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_regime_consumer_bundle_adapter_tmp_test_packet_20260523.md`.

Reusable rule: adapter tests prove ingress mechanics, not root promotion. A
passing suite such as `19 passed; 0 failed` may show strict schema fail-closed
behavior, neutral fallback, accepted `95/99` label mapping into read-only BBN
soft evidence, market-provenance prefix stripping, and branch-path propagation
into Pre-Bayes/BBN/ranker context. Still keep `root_regime_registration_allowed`,
`promotion_allowed`, and `trade_usable` false unless a separate real provider ->
Auto-Quant -> Pre-Bayes/filter -> BBN/workflow -> CatBoost/path-ranker ->
execution-tree chain proves calibrated current-root confidence, same-root mature
rows, and a ready/actionable execution candidate. Do not turn an adapter ingress
test into Board B profitability work.

## 2026-05-23 Direct Manipulation Source-Control Blocker Lesson

Direct `Manipulation` / R6 evidence can be useful Board A direct-event overlay
material while still failing root admission. Preserve it in a tracked packet
when the decisive facts live in ignored audit roots, noncanonical staging roots,
or tmp/source-control readbacks.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_direct_manipulation_source_control_blocker_packet_20260523.md`.

Reusable rule: keep `Manipulation` under bounded direct-event overlay evidence
until support, Wilson95, broad-normal controls, direct species coverage,
canonical owner export, source/control unlock, and downstream promotion rerun all
exist. A v46 shape such as positives `41`, matched controls `41`, min Wilson95
LCB `0.914332`, support gate false, broad-normal false, and species closed false
is below admission even if a noncanonical staging pool has `77/77` rows. If the
staging split fails chronological, heldout-symbol, or heldout-venue gates, and
DataCite/Dataverse plus local-download readbacks find no owner/export unlock,
then `canonical_merge_allowed`, `root_regime_registration_allowed`,
`promotion_allowed`, and `trade_usable` must stay false. Do not turn this blocker
packet into Board B profitability work.

## 2026-05-23 Market-State Gate Real-Chain Lesson

A real-chain A-board market-state gate can be reusable for root/subclass routing
and later single-factor selection even when it is not Board A completion. Preserve
the compact gate contract and provider provenance in a tracked packet when the
evidence is otherwise buried in a run root.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_market_state_gate_real_chain_packet_20260523.md`.

Reusable rule: a market-state gate is usable for factor selection when it exposes
`active_regime`, `confidence`, `probabilities`, `pre_bayes_gate_status`, and
provider/timeframe/run-root provenance, with primary selection at
`pre_bayes_gate_status == pass_hard && confidence >= 0.75`. Treat `confidence >=
0.80` as strong auxiliary support and keep `0.95` as Board A completion only.
Provider examples may include IBKR/KRE `range@0.8180523711264852 pass_hard`,
Kraken/APT `trend@0.812313505621835 pass_hard`, and TVR/KRE
`range@0.7766993364023601 pass_hard`; `pass_neutralized` examples such as YF/MDY
`trend@0.7457488021493103` are weak context only. If CatBoost/path-ranker and
execution-tree consumption are proven but execution stays
`fail_closed/execution_observe_only`, classify the packet as selection/routing
evidence, not root registration or trade usability. Do not turn the packet into
Board B profitability work.

## 2026-05-23 Aggregate Asset/Ranker State-Root Split Lesson

Regime-confidence asset visibility and aggregate feedback/ranker maturity can
land in different symbol-root views under one state directory. Preserve both the
asset bridge and the split diagnosis before attempting a runtime repair.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_aggregated_rooted_feedback_ranker_packet_20260523.md`.

Reusable rule: after running `regime-confidence-assets`, rerun
`workflow-status`, `pre-bayes-status`, `policy-training-status`, and
`export-structural-path-ranking-target` against the same `--state-dir`. If the
post-asset workflow/policy readbacks show `regime_confidence_assets.inventory`
ready but a fresh structural-path export drops to a tiny top-level symbol root
such as `rows=1` and `mature_rows=0`, do not claim the mature CatBoost/ranker
state was lost. Inspect whether feedback/ranker state lives under
`state/ict-engine-feedback/<SYMBOL>/` while asset inventory lives under
`state/<SYMBOL>/`.

Treat this as a canonical-root unification blocker, not a promotion event. It is
valid Board A progress when inventory changes from missing to ready and exposes
recovered gates such as scope-limited `Bull` and `Bear` Wilson95 LCB assets, but
`promotion_allowed=false`, `runtime_selection_enabled=false`, missing execution
candidate readiness, and absent path-ranker score usage still prohibit root
registration, root `95%` completion claims, trade use, and Board B profitability
work. The next repair should make the asset inventory and `ict-engine-feedback`
ranker/training state visible to the same workflow/execution-tree consumer
surface, then rerun the full readback chain.

## 2026-05-23 Policy/Export Root-Unification Lesson

The first safe repair for the aggregate Board A state-root split can be
policy/export readback unification, not artifact copying. Keep the recovered
regime-confidence asset inventory under the top-level symbol root, but let
policy/export choose the stronger `state/ict-engine-feedback/<SYMBOL>/`
structural path-ranker summary when that child root has mature rows, validation
rows, CatBoost scores, and runtime selection while the top-level root only has a
weak bootstrap summary.

For 2026-05-23 the durable packet is:
`support/docs/experiments/actionable-regime-confidence/board_a_aggregated_rooted_feedback_ranker_packet_20260523.md`.

Reusable rule: prove this repair with both a targeted regression and real CLI
readbacks. The expected positive shape is one policy surface that shows
`regime_confidence_assets.inventory_status=ready` plus the child-root ranker
metrics such as `rows=50`, `mature_rows=50`, `history_rows=188`,
`raw_scored_mature=47/30`, `production_validation=120/30`,
`observation_validation=47/30`, `calibration_ready=true`,
`trainer_artifact_ready=true`, `runtime_selection_status=enabled_candidate_set_ready`,
and `score_model_family=catboost`. The expected export shape has
`summary_path` under `state/ict-engine-feedback/<SYMBOL>/policy_training/`.

Do not overclaim policy/export unification. If `workflow-status` still reports
`closed_loop_branch_admission.status=fail_closed`, no ready/actionable execution
candidate, no execution readiness, and no path-ranker score visible or used by
the execution tree, then the remaining blocker is workflow/execution consumer
materialization. That status remains non-promoting: no root registration, no
root `95%` completion claim, no trading, no Board B profitability lane, and no
goal completion.
