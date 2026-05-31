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
- plan, work, and review phases
- expected artifacts back to `ict-engine`
- constraints stating that Auto-Quant success does not imply promotion or
  `trade_usable=true`

If these fields are missing, do not ask another agent to start Auto-Quant work.
Repair the handoff first.

## Plan Work Review Loop

Plan:
- Read the Auto-Quant checkout `AGENTS.md`, `program.md`, and the current
  handoff artifact.
- Write a lane-local `plan.md` before editing strategy files.
- Include objective, symbol, data paths, workspace env, candidate ideas,
  verification command, stop condition, and adoption return path.

Work:
- Create or evolve at most 3 active non-underscore strategy files inside the
  lane strategies directory.
- Keep `config.json`, `run.py`, `prepare.py`, shared data, and repo-root
  `results.tsv` read-only when `AUTO_QUANT_WORKSPACE` is available.
- Do not run Claude Code Harness installers, hooks, MCP setup, or bundled
  binaries. Use only the workflow pattern.

Review:
- Run the measured Auto-Quant command with the handoff environment.
- Inspect `run.log`, `results.tsv`, strategy files, and any generated
  `strategy_library.json`.
- Write lane-local `review.md` with keep/discard evidence.
- Return artifact paths and measured metrics to `ict-engine`; do not summarize
  from memory.

## Return Packet

Before adoption review, require:

```text
plan.md
run.log
results.tsv
strategy file paths
review.md
strategy_library.json or adoption bundle when a measured candidate survives
```

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
human_output contains Agent workflow: plan -> work -> review
```

For Auto-Quant checkout changes:

```bash
python3 -m unittest tests/test_auto_quant_workspace.py -v
python3 -m py_compile auto_quant_workspace.py run.py prepare.py tests/test_auto_quant_workspace.py
```
