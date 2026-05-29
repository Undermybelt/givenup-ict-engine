---
name: ict-engine-factor-source-intake
description: >
  Use when Board B factor training is blocked by active claims, stale-safe
  timers, or live AQ/provider owners and the agent should do interruptible
  paper, repository, strategy, or indicator intake for future regime-rooted
  factors without launching shared runtime work.
version: 1
---

# Factor Source Intake

## Goal

Use waiting windows productively without colliding with active factor lanes.
Turn papers, repositories, strategy writeups, and indicator families into
codeable regime-rooted candidates for later Gate 1 testing.

This skill is not a runtime input. It is an agent-facing intake discipline.

## Use When

- `factor_claim_terminalization_audit.py --compact` shows fresh active claims,
  stale-safe timers, or live AQ/provider owners.
- The user asks to search papers, repositories, strategies, indicators, or
  build knowledge reserves for factor training.
- A factor lane is waiting for AQ/IBKR/provider/runtime clearance.

## Safe Waiting Work

Allowed while blocked:

- Search papers, public repositories, blogs, docs, and indicator references.
- Extract only codeable hypotheses, regime roots, entry/exit mechanics, data
  needs, expected holding period, cost model needs, and known failure modes.
- Check exact duplicate or terminalized roots in `/tmp` claims and repo run
  packets before proposing a branch.
- Write a compact intake packet or append to the lane workdoc.
- Mark each candidate as `idea_only`, `paper_only`, `repo_source_only`,
  `python_prescreen_ready`, or `blocked_by_runtime`.

Not allowed while blocked:

- Launch Auto-Quant, Freqtrade, TOMAC, IBKR, `provider-status`, or
  `fetch_external.py`.
- Clone, install, or execute external repositories or installers.
- Mutate shared runtime state or shared provider configs.
- Treat a paper, blog, social post, or GitHub result as trading evidence.

## Candidate Note Shape

```text
candidate_id:
source:
source_risk: info_only | reviewed_code | rejected
regime_root:
branch_path:
instrument/timeframe:
entry:
exit/risk:
data_required:
cost_model_required:
duplicate_check:
expected_gate1:
status: idea_only | paper_only | repo_source_only | python_prescreen_ready | blocked_by_runtime
next_command_when_clear:
promotion_allowed: false
trade_usable: false
```

## Promotion Rule

Source intake can only create candidates. Promotion requires the normal current
gate chain: real or retained-real data, no-lookahead screen, honest cost model,
density and split survival, then same-root AQ/provider/downstream validation
through Pre-Bayes, BBN, path-ranker/CatBoost, execution tree, and lifecycle
readback. Keep `promotion_allowed=false` and `trade_usable=false` until those
current artifacts prove otherwise.
