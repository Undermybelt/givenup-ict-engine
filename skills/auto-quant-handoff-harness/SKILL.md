---
name: ict-engine-auto-quant-handoff-harness
description: >
  Use when creating, reviewing, or consuming ict-engine Auto-Quant handoff
  artifacts, especially agent_workflow payloads, isolated Auto-Quant
  workspaces, plan/work/review loops, and adoption-review return packets.
version: 1
---

# Auto-Quant Handoff Harness

## Goal

Keep Auto-Quant agent work isolated, reviewable, and subordinate to
`ict-engine` promotion gates.

This is an agent-facing repo skill. It is not a Rust runtime input, not a
plugin installer, and not a replacement for typed payload fields or tests.

## Use When

- Editing `src/application/auto_quant/handoff.rs`.
- Editing `src/application/auto_quant/command_entry.rs` handoff output.
- Running or reviewing `factor-research` / `factor-autoresearch` with the
  Auto-Quant backend.
- Passing work from `ict-engine` to `/Users/thrill3r/Auto-Quant` or another
  managed Auto-Quant checkout.
- Reviewing artifacts before `auto-quant-adoption-review`.

## Required Handoff Contract

Auto-Quant handoff output must include enough information for a fresh agent to
run a lane without touching shared mutable repo state:

- `workflow_style=plan_work_review`
- lane-local setup commands
- `AUTO_QUANT_WORKSPACE`
- `AUTO_QUANT_DATA_DIR`
- `AUTO_QUANT_CONFIG`
- `AUTO_QUANT_USER_DATA`
- `AUTO_QUANT_STRATEGIES_DIR`
- `AUTO_QUANT_RESULTS_TSV`
- `entry_regime_contract` with `primary_entry_regime=TrendExpansion`,
  allowed entry labels `expansion` and `trend_continuation`, and a clear
  non-entry role for all other regime evidence
- `lifecycle_layers` with environment contract, procedural skill, action
  realization, and trajectory regulation entries
- `evolution_inputs` derived from measured trajectories
- plan, work, and review phases
- expected artifacts back to `ict-engine`
- `regression_checks`
- `freeze_boundary`
- constraints stating that Auto-Quant success does not imply promotion or
  `trade_usable=true`

If these fields are missing, do not ask another agent to start Auto-Quant work.
Repair the handoff first.

## Trend / Expansion Entry Contract

Auto-Quant handoffs are trend / expansion entry harnesses. A strategy may open
an entry only when the regime evidence supports `TrendExpansion`, represented
by `expansion` or `trend_continuation` labels. Compression, reversion,
manipulation, transition, range, unknown, or low-confidence evidence is not an
alternate entry family. It is exclusion, conflict, or counter-evidence used to
block/down-rank the entry and improve regime identification.

When planning or reviewing a lane:

- classify each factor as entry evidence, non-trend exclusion evidence, or
  trend counter-evidence before editing strategy files;
- require the strategy entry condition to include expansion or
  trend-continuation evidence;
- use non-trend factors only as filters, blockers, down-rankers, or review
  diagnostics unless fresh regime evidence reclassifies the state into the
  trend family;
- reject review packets where a compression/reversion/manipulation signal has
  become a standalone entry trigger.

## Repository Admission Boundary

Auto-Quant and TOMAC iteration artifacts belong under the lane-local
`AUTO_QUANT_WORKSPACE`, run root, or `/tmp` claim/workdoc until they become one
of these explicit repo-admitted artifacts:

- a structured evidence packet under
  `support/docs/experiments/actionable-regime-confidence/runs/...`
- a candidate/adoption bundle that is referenced by such an evidence packet
- a current `ict-engine` practical-closure artifact proving
  `promotion_allowed=true` and `trade_usable=true`

Do not commit loose source-intake notes, prep/downstream wrappers, generated
strategy files, `plan.md`, `review.md`, `run.log`, `results.tsv`, or
`strategy_library.json` from a non-promoted lane. A fail-closed, prep-only,
observation-only, or sparse-positive candidate remains `/tmp`-scoped unless it
is packaged as an evidence packet. If the useful part is a reusable harness
rule, promote the rule into this skill or typed code/tests; keep the raw lane
artifact out of the repo.

## Life-Harness Runtime Adaptation Contract

Source absorbed: arXiv `2605.22166` and
`https://github.com/Tianshi-Xu/Life-Harness`.

Use Life-Harness as methodology only. Do not run or vendor the raw benchmark
runtime, Docker services, `uv` environments, provider calls, or installers from
the source repo as part of `ict-engine` handoffs.

Map Life-Harness to `ict-engine` as a runtime interface adaptation, not as a
model-weight, provider-data, or evaluation-gate change:

- Environment contract: freeze provider/data/cost/evaluation files and name
  the read-only Auto-Quant contract before any factor iteration.
- Procedural skill: write compact lane-local procedure guidance from prior
  measured failures, not chat-only guesses.
- Action realization: validate that the intended strategy file exists, was
  edited, and can be measured before adoption review.
- Trajectory regulation: detect repeated no-fill, no-survivor, stale-data, and
  budget-exhaustion loops before running another same-shape iteration.

Each harness update must be driven by measured trajectory failures, assign the
earliest detectable lifecycle layer, target deterministic/mechanical signals,
avoid hidden oracle labels, and include a regression review for over-triggering,
valid-action blocking, misleading guidance, and degradation on previously
successful trajectories. Once artifacts are returned to `ict-engine`, adoption
and practical-readiness evaluation uses the frozen returned artifacts; do not
keep editing the harness while claiming evaluation evidence.

Do not spread Life-Harness H2/H3/H4/H5 terminology to non-LLM-agent harnesses.
`market-data-harness` is a provider/data request planner and fetch envelope,
`structural_feedback_replay_harness.py` is a deterministic replay helper, and
`factor_candidate_harness_presets.json` is a preset catalog. Harden those
surfaces with their native data, provenance, and replay contracts unless a
future LLM-agent loop is added.

## TraderAlice Auto-Quant Usage Contract

Source absorbed: `https://github.com/TraderAlice/Auto-Quant`, especially
`README.md`, `program.md`, `prepare.py`, and `run.py`.

Release-clone default source: `https://github.com/undermybelt/Auto-Quant`.
Agents starting from an `ict-engine` release clone must surface or run
`ict-engine auto-quant-bootstrap --state-dir <state-dir> --repo-url https://github.com/undermybelt/Auto-Quant`
when the managed Auto-Quant checkout is missing. Do not assume a maintainer
local checkout such as `/Users/thrill3r/Auto-Quant` exists.

Treat upstream Auto-Quant as a measured research harness, not a trading engine:

- The success target is an interpretable iteration loop with `results.tsv`,
  not a promise that a profitable strategy has been found.
- `program.md` is the agent loop. It requires setup, 1-3 starting strategies,
  measured backtests, keep/discard decisions, and repeated iteration.
- `prepare.py` is a read-only data-preparation contract. It checks TA-Lib,
  downloads/verifies the fixed Binance OHLCV arena, and exits ready only when
  the required pair/timeframe feather files exist. Do not edit it to fit a
  factor idea.
- `run.py` is the read-only oracle. It discovers non-underscore `.py`
  strategies, runs FreqTrade backtests in-process, and emits per-strategy
  metric blocks. Do not bypass it with ad hoc FreqTrade CLI calls.
- `config.json`, `prepare.py`, `run.py`, shared data, `_template.py.example`,
  pair lists, timeranges, and timeframe lists are evaluation-contract files.
  The factor surface is the corresponding strategy file under the active
  strategies directory.
- The agent-owned mutation surface is at most 3 active non-underscore strategy
  files. Each factor change must touch the corresponding strategy file and then
  be measured through `run.py`; a chat-only factor tweak is not an iteration.

In ict-engine handoffs, map that contract onto lane-local artifacts:

```text
factor edit -> AUTO_QUANT_STRATEGIES_DIR/<StrategyName>.py
measurement -> uv run run.py > ${AUTO_QUANT_WORKSPACE}/run.log 2>&1
decision log -> AUTO_QUANT_RESULTS_TSV
planning -> ${AUTO_QUANT_WORKSPACE}/plan.md
review -> ${AUTO_QUANT_WORKSPACE}/review.md
return -> ict-engine adoption/feedback packet
```

Use `ict-engine auto-quant-prepare --state-dir <state-dir>` when the managed
workspace is missing prepared data. Use upstream `uv run prepare.py` only when
working directly inside the Auto-Quant checkout. In both cases, preparation is
a prerequisite, not the factor iteration itself.

## Plan Work Review Loop

Plan:
- Read the Auto-Quant checkout `AGENTS.md`, `README.md`, `program.md`,
  `prepare.py`, `run.py`, `_template.py.example`, the current handoff artifact,
  and the Life-Harness layer contract in that handoff.
- Write a lane-local `plan.md` before editing strategy files.
- Include objective, symbol, data paths, workspace env, candidate ideas,
  factor-to-strategy-file mapping, lifecycle-layer mapping, verification
  command, stop condition, and adoption return path.
- Inspect prior measured trajectories when available and write
  `failure_patterns.md` with dominant deterministic failures, earliest
  lifecycle layer, and why each pattern is mechanical rather than hidden-oracle
  reasoning.

Work:
- Create or evolve at most 3 active non-underscore strategy files inside the
  lane strategies directory.
- Keep `config.json`, `run.py`, `prepare.py`, shared data, and repo-root
  `results.tsv` read-only when `AUTO_QUANT_WORKSPACE` is available.
- For every factor change, update the corresponding strategy file first, then
  append the decision to `AUTO_QUANT_RESULTS_TSV` after the measured run. Do
  not report an iteration from notes, prompts, or metric interpretation alone.
- Record targeted layer updates in `harness_layer_updates.md`.
- Do not run Claude Code Harness installers, hooks, MCP setup, or bundled
  binaries. Use only the workflow pattern.

Review:
- Run the measured Auto-Quant command with the handoff environment.
- Inspect `run.log`, `results.tsv`, strategy files, and any generated
  `strategy_library.json`.
- Write lane-local `review.md` with keep/discard evidence, lifecycle safety
  rationale, and remaining failure modes.
- Write `regression_review.md` for over-triggering, valid-action blocking,
  misleading guidance, loop regression, and prior-success degradation.
- Return artifact paths and measured metrics to `ict-engine`; do not summarize
  from memory.
- `auto-quant-adoption-review` must expose `life_harness_review`. A prepared
  workspace with strategy files can be ready for external execution while
  `life_harness_review.status=pending_return_artifacts`; adoption and practical
  readiness evaluation remain blocked until
  `life_harness_review.adoption_evaluation_allowed=true`.
- Existence is not enough. `auto-quant-adoption-review` must also expose
  `life_harness_review.artifact_checks` and block with
  `life_harness_review.status=return_artifact_validation_failed` plus
  `life_harness_review.invalid_artifacts` when returned files are empty or lack
  the deterministic failure, lifecycle-layer, safety, regression, and strategy
  evidence required by the handoff. `run.log` must show measured backtest and
  strategy output, not just arbitrary non-empty text.
- Legacy handoffs without `agent_workflow`, or handoffs with an `agent_workflow`
  but no lifecycle layers, are not Life-Harness-complete. They must surface
  `life_harness_review.adoption_evaluation_allowed=false` with
  `life_harness_review.status=legacy_handoff_without_life_harness_contract` or
  `life_harness_review.status=legacy_handoff_without_lifecycle_layers`.
- `auto-quant-status` / readiness output may describe external execution
  readiness, but when a Life-Harness handoff exists it must expose
  `life_harness_hint.status=adoption_review_required` and keep
  `life_harness_hint.adoption_evaluation_allowed=false` until
  `auto-quant-adoption-review` verifies frozen return artifacts.

## Return Packet

Before adoption review, require:

```text
plan.md
failure_patterns.md
harness_layer_updates.md
run.log
results.tsv
strategy file paths
review.md
regression_review.md
strategy_library.json or adoption bundle when a measured candidate survives
```

For every completed Auto-Quant or exact-AQ run that has terminal metrics,
also require a regime feedback evidence packet:

```text
${run_root}/checks/regime_feedback_evidence_packet.json
```

Mirror it to the compact run `checks/` directory when a compact run mirror
exists. Add its path to the factor-local workdoc, repo-local slice doc, and
`/tmp` claim. Use
`references/autoquant-regime-feedback-evidence-contract-20260601.md` for the
schema and admission boundary.

The terminal metrics, terminal summary, packet, and any exact-AQ prep packet
must also carry cleaned data provenance. For futures TOMAC lanes, this means
the source root, symbol aliases, timeframe list, derived-timeframe resample
policy, `raw_fallback_used=false`, and
`data_provenance.source_archive_validation.status=pass_zip_pristine_source`
when ZIP archives are the source authority. A source directory with symlinked
OHLCV, old same-symbol CSV, shifted fallback CSV, or generated higher-timeframe
CSV beside the ZIP payload is polluted; delete/re-extract it from ZIP and
regenerate the cleaned MTF root before exact-AQ. If the strategy was prepared
from uncleaned/raw fallback/polluted data, mark the packet
`data_scope_blocked_for_cleaned_target`, keep practical flags false, and do not
launch exact-AQ until the candidate is rebuilt from cleaned/full-retained data.

That packet must also carry pending belief-network and execution-tree placement
fields. For AQ/backtest evidence those placements stay pending, not admitted.
After accepted paper/live feedback exists, write a later accepted-feedback
packet that proves the branch is visible in the BBN and execution tree before
any practical report.

Minimum metrics to report:

```text
trade_count
win_rate
profit_factor
total_profit_pct
max_drawdown_pct
cost assumptions
provider/data path
```

## Promotion Boundary

Auto-Quant can produce candidate evidence. It cannot, by itself, promote a
factor to live readiness.

AQ/backtest results can feed regime observation and calibration only through a
`backtest_autoquant_feedback` evidence packet. They must not be treated as
accepted `update --feedback-file`, Pre-Bayes, BBN, CatBoost, path-ranker, or
execution-tree training feedback until paper/live broker feedback and lifecycle
gates pass.

Do not report a factor as `trade_usable=true` or "能实战" until the same lineage
has all of these current artifacts:

```text
accepted paper/live execution feedback packet
update --feedback-file ingestion evidence
belief network / BBN readback showing the branch feedback is visible
execution_tree_trace or workflow-status evidence showing the branch has a place
same-tree practical closure
terminal metrics with promotion_allowed=true and trade_usable=true
```

Keep these false until current `ict-engine` artifacts prove otherwise:

```text
promotion_allowed=false
trade_usable=false
```

Downstream readiness still requires the current gate chain: provider/data
truth, no-lookahead and cost checks, density/split evidence, adoption review,
Pre-Bayes/filter, BBN, path-ranker/CatBoost, execution tree, and lifecycle
readback.

## Verification

For handoff payload changes:

```bash
cargo fmt --check
cargo test auto_quant_handoff -- --nocapture
cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-aq-harness-smoke/state --output-format json
```

The smoke JSON must show:

```text
agent_workflow.workflow_style=plan_work_review
agent_workflow.environment contains AUTO_QUANT_WORKSPACE
agent_workflow.entry_regime_contract.primary_entry_regime=TrendExpansion
agent_workflow.entry_regime_contract.allowed_entry_labels contains expansion and trend_continuation
agent_workflow.entry_regime_contract.non_entry_factor_role=exclude_non_trend_or_counter_evidence
agent_workflow.lifecycle_layers contains Environment Contract Layer
agent_workflow.lifecycle_layers contains Procedural Skill Layer
agent_workflow.lifecycle_layers contains Action Realization Layer
agent_workflow.lifecycle_layers contains Trajectory Regulation Layer
agent_workflow.freeze_boundary names frozen returned artifacts
auto-quant-adoption-review agent/json output contains life_harness_review.status
auto-quant-adoption-review agent/json output contains life_harness_review.artifact_checks
auto-quant-adoption-review weak return files produce life_harness_review.status=return_artifact_validation_failed
auto-quant-adoption-review legacy handoffs produce life_harness_review.adoption_evaluation_allowed=false
auto-quant-adoption-review weak run.log produces life_harness_review.invalid_artifacts
auto-quant-adoption-review human output contains life_harness_status
auto-quant-status agent/json output contains life_harness_hint.status=adoption_review_required after a handoff exists
human_output contains Agent workflow: plan -> work -> review
```

For Auto-Quant checkout changes:

```bash
python3 -m unittest tests/test_auto_quant_workspace.py -v
python3 -m py_compile auto_quant_workspace.py run.py prepare.py tests/test_auto_quant_workspace.py
```
