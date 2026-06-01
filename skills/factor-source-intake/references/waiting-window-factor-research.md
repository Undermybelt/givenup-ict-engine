# Waiting-Window Factor Research

Use this when `factor_claim_terminalization_audit.py --compact` blocks new
provider, Auto-Quant, Freqtrade, IBKR, paper, or lifecycle launches because
another factor lane owns the shared runtime, or because a fresh active claim is
not yet stale-safe for takeover.

## Purpose

There is no allowed passive waiting state. A fresh claim, unexpired one-hour
takeover timer, or foreign live runtime is only a no-launch condition. It must
immediately turn into interruptible knowledge work: papers, strategy writeups,
indicator families, public repo ideas, local negative/duplicate evidence, and
market microstructure notes that can later become regime-rooted Gate 1
candidates.

This is source intake only. It cannot prove `promotion_allowed=true` or
`trade_usable=true`.

Machine flags for all waiting-window intake packets:
`promotion_allowed=false`, `trade_usable=false`.

## Allowed Work

- Create or continue a small source-intake / knowledge-reserve packet instead
  of sleeping, polling, or waiting for a fresh claim to become one hour old.
- Search or read papers, strategy notes, indicator docs, public repositories,
  and exchange/broker documentation.
- Extract codeable mechanics: regime root, trigger, confirmation, exit/risk,
  holding period, data fields, cost model, expected cadence, and failure modes.
- Verify source metadata from stable references such as DOI/Crossref/arXiv or
  official docs before writing a paper-backed candidate. If metadata cannot be
  checked in the waiting window, label the source `unverified_info_only` and do
  not spend runtime on it later until verified.
- Check local duplicate/negative evidence before proposing a branch: exact
  factor id, branch labels, `/tmp` claims, and repo run packet names.
- Write compact packets to the current lane workdoc or a repo-local intake
  document under `support/docs/experiments/actionable-regime-confidence/`.
- For Python prescreens run during crowded windows, classify artifacts before
  using them: `*.interrupted.exit`, signal exits, and timeout exits are
  `interrupted_no_verdict`; fixture-only prescreens are parser/readback coverage
  only. Neither can open Gate 1, downstream, promotion, or trade-usability
  gates. Record the no-verdict in the workdoc, claim, and terminal summary.
- Prefer ideas that address current observed bottlenecks: 1m cost wall, sparse
  positive density, cross-engine parity, paper feedback semantics, lifecycle
  maturity, and path-ranker consumption.
- If the wait is long or the user asks for paper, strategy, or indicator
  knowledge reserves, add one small candidate at a time and consult
  `paper-strategy-reserve-20260530.md` for the current seed set.

## Forbidden Work While Waiting

- Do not wait for a one-hour takeover window, fresh claim expiry, or another
  agent's ownership to clear as the primary activity.
- Do not start provider, IBKR, Auto-Quant, Freqtrade, TOMAC, paper, simulated
  trade, or lifecycle commands.
- Do not clone, install, or execute external repos or package managers unless
  the user explicitly approves that runtime scope.
- Do not write `same_tree_practical_closure.json`, practical flags, or update
  Board/current docs from source intake.
- Do not use source popularity, paper Sharpe, blog PnL, or GitHub backtests as
  evidence that the factor is usable.
- Do not turn a filter, risk overlay, or falsification test into a standalone
  entry root unless a later same-root Gate 1 run proves it has independent
  economics.

## Candidate Packet

```text
candidate_id:
source:
source_type: paper | repo | indicator | broker_doc | exchange_doc | article
source_risk: info_only | reviewed_code | rejected
why_now:
regime_root:
branch_path:
instrument/timeframe:
entry:
confirmation:
exit/risk:
expected_holding_period:
expected_cadence:
data_required:
cost_model_required:
duplicate_check:
known_failure_modes:
first_gate1_shape:
next_command_when_clear:
status: idea_only | paper_only | repo_source_only | python_prescreen_ready | blocked_by_runtime
promotion_allowed: false
trade_usable: false
```

## Useful Research Themes

- Cost amortization: multi-session holds, wider payoff distributions, lower
  turnover filters, or instruments with verified lower relative trading cost.
- Cross-engine replay stability: synthetic futures metadata, leverage tiers,
  spot-equivalent stress replay, and declared-fee reproducibility.
- Paper/live semantics without funded fills: order type, slippage, fill model,
  risk controls, reject paths, and broker/paper feedback schema.
- Validation maturity: how to produce branch-local rows that satisfy raw,
  production, and observation counters without reclassifying simulated labels as
  real feedback.
- Regime filters that reduce churn without erasing edge: volatility
  compression, breadth confirmation, liquidity-window constraints, trend
  persistence, and cross-index confirmation.

## Stop Condition

Stop source intake immediately when compact audit clears and a launchable,
owned factor slice is ready. Record the partially completed candidate packet as
`idea_only` or `blocked_by_runtime`, then return to the active factor objective.
