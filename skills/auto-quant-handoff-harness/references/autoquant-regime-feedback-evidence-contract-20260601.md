# Auto-Quant Regime Feedback Evidence Contract

## Purpose

Every completed Auto-Quant or exact-AQ factor run that produces reusable
regime information must leave a regime feedback evidence packet. The packet
lets later agents feed the result back into regime observation and calibration
without pretending an AQ backtest is paper/live execution feedback.

## Required Artifact

Write this file after terminal metrics and metrics review exist:

```text
${run_root}/checks/regime_feedback_evidence_packet.json
```

If the run has a compact repo mirror under
`support/docs/experiments/actionable-regime-confidence/runs/...`, mirror the
same JSON into that mirror's `checks/` directory. Then add the packet path to
the factor-local workdoc, the repo-local slice doc, and the `/tmp` claim.

## Required Fields

```text
schema_version: autoquant-regime-feedback-evidence-packet/v1
evidence_type: backtest_autoquant_feedback | accepted_paper_execution_feedback | accepted_live_execution_feedback
feedback_source:
regime_root:
branch_path:
entry_policy.entry_allowed_regime:
entry_policy.other_regimes_policy:
entry_policy.side_policy:
entry_policy.session_scope:
entry_policy.rth_filter_applied:
data_provenance:
no_lookahead_controls:
cost_model:
per_timeframe_evidence:
regime_feedback_admission:
practical_flags:
blockers:
source_artifacts:
```

For the user's current TrendExpansion-only operating rule, `entry_allowed_regime`
must be `TrendExpansion` and all other regimes must be
`reference_veto_only_no_entry` unless the user explicitly changes the target.

For TOMAC futures or other cleaned-cache lanes, `data_provenance` must prove:

```text
cleaning_status: cleaned_or_verified_retained
source_root:
symbol_aliases:
timeframes:
raw_fallback_used: false
resample_policy: closed_left_label_left_for_derived_frames
source_archive_validation.status: pass_zip_pristine_source
```

For TOMAC futures ZIP archives, `pass_zip_pristine_source` means the extracted
source directory matches the ZIP payload exactly before cleaning. Symlinked
OHLCV files, older same-symbol CSVs, shifted fallback CSVs, generated
higher-timeframe CSVs, missing ZIP members, or size mismatches are pollution and
must fail closed before cleaning or exact-AQ.

If any candidate used raw, stitched, uncleaned, polluted, non-ZIP-pristine, or
unknown provenance data, set
`regime_feedback_admission.status=data_scope_blocked_for_cleaned_target` or
`observation_only_uncleaned`, and keep all practical flags false. Delete the
polluted extracted source, re-extract from ZIP, regenerate the cleaned MTF root,
and rebuild the candidate from cleaned/full-retained data before exact-AQ or
provider reproduction.

Also include pending closed-loop placement fields so the next agent does not
need to infer where the evidence belongs:

```text
closed_loop_contract.current_stage
closed_loop_contract.stage_order
belief_network_placement.target_surface
belief_network_placement.target_regime_node
belief_network_placement.status
execution_tree_placement.target_surface
execution_tree_placement.target_branch_path
execution_tree_placement.status
reporting_policy.only_report_practical_when_all_true
```

## Admission Boundary

For `backtest_autoquant_feedback`, the packet may feed only:

```text
regime_observation_queue=true
regime_calibration_queue=true
```

It must keep these false:

```text
pre_bayes_feedback=false
bbn_feedback=false
catboost_training=false
path_ranker_training=false
execution_tree_training=false
promotion=false
promotion_allowed=false
trade_usable=false
update_goal=false
```

AQ backtest rows are useful evidence about when a regime-rooted idea worked or
failed, but they are not accepted broker/paper/live feedback. They cannot be
sent to `update --feedback-file`, Pre-Bayes, BBN, CatBoost, path-ranker, or
execution-tree training as accepted feedback until the lane has retained-session
coverage proof, current cost verification, downstream lifecycle evidence, and
accepted broker paper/live feedback rows.

## Closed-Loop Progression

The packet must make the future route explicit:

1. `backtest_autoquant_feedback` enters only regime observation/calibration.
2. Once retained-session coverage and accepted broker paper/live feedback rows
   exist, write a new packet with
   `evidence_type=accepted_paper_execution_feedback` or
   `accepted_live_execution_feedback`.
3. In that accepted packet, set belief-network and execution-tree placement
   fields to ready only after the real readbacks exist:

```text
belief_network_placement.status=visible_in_bbn_feedback
execution_tree_placement.status=visible_in_execution_tree
```

4. Only after the same tree also proves practical closure may the terminal
   packet report:

```text
promotion_allowed=true
trade_usable=true
update_goal=true
```

Do not overwrite an AQ observation packet to pretend the closed loop already
passed. Add a later accepted-feedback packet and link both packet paths from
the workdoc, repo doc, and claim.

## Per-Timeframe Evidence

Each timeframe row should include at least:

```text
timeframe
strategy or factor_id
trades
trades_per_day
gross_profit_total_pct
net_after_verified_cost_pct
profit_factor
winrate
regime_feedback_hint
negative_evidence
```

Use positive and negative evidence together. A cost-positive but sparse 1d row
is a regime observation, not practical readiness. A high-trade row with weak PF
or below-target density should say so in `negative_evidence`.

## Source Artifact Discipline

The packet must point to the real artifacts that were inspected in the same
run:

```text
terminal_metrics
metrics_review
trade exports or AQ result paths
repo_doc
workdoc
claim
runner
runner_test
```

Do not summarize from chat memory. If any artifact is missing, record the
missing path in `blockers` and keep all practical flags false.

## Reporting Rule

Agents should not report "能实战", `trade_usable=true`, or practical readiness
from AQ/backtest evidence. Report practical readiness only when the terminal
metrics, the accepted feedback packet, the belief-network readback, the
execution-tree readback, and same-tree practical closure all agree in the same
run lineage.
