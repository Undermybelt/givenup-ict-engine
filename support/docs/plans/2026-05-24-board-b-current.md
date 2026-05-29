# Board B Current - Superseded

Superseded: `2026-05-25 12:05 +0800`

Do not use this file as the active Board B entrypoint. The current workboard is:

`support/docs/plans/2026-05-25-board-b-current.md`

Reason: this May 24 board remained useful as historical context, but the live
claim surface became noisy enough that keeping it as the first stop can mislead
new agents into stale lane selection, invalid claim debt, or repeated
zero-trade/low-density loops. Start from the May 25 board, then return here only
for exact references named by that board. The archived content below may still
describe itself as current; ignore that language after the supersession marker.

# Board B Current - Archived Body

Updated: `2026-05-24 23:53 +0800`

Purpose: archived May 24 navigation context for Board B regime-rooted
profitability-factor work. This file is no longer an entrypoint. Use
`support/docs/plans/2026-05-25-board-b-current.md` first, then return here only
for exact references named by that board.

## Latest-Board Rule

This file is superseded. Any agent that opens this file for Board B work must
stop and go to `support/docs/plans/2026-05-25-board-b-current.md` before reading
or appending to any Board B historical file.

Older Board B files are sinks or archives only:

- `support/docs/plans/2026-05-23-board-b-current.md` is superseded by the
  May 25 workboard.
- `support/docs/plans/2026-05-17-board-b-factor-refinement-small-cycle-current.md`
  is the terminal-decision ledger.
- `support/docs/plans/2026-05-12-board-b-profit-factor-current.md` is historical
  compact context.

Hard May 17 rule: do not use
`support/docs/plans/2026-05-17-board-b-factor-refinement-small-cycle-current.md`
as an entrypoint, candidate lookup source, broad grep corpus, or lane-selection
board. Reach it only through the May 25 board, and only for an exact heading,
factor id, run root, or evidence path already identified by that board or a
tracked lifecycle artifact.

## Start Here

For Board B work, do not start from this file. Read
`support/docs/plans/2026-05-25-board-b-current.md` first, then use this archived
reference list only when the May 25 board names an exact target:

- Candidate ingestion rules:
  `support/docs/plans/2026-05-12-factor-candidate-ingestion-instructions.md`.
- Terminal-decision lookup, exact-reference only after this board or the
  active plan names the target:
  `support/docs/plans/2026-05-17-board-b-factor-refinement-small-cycle-current.md`.
- Current source-backed bottleneck refresh:
  `support/docs/experiments/actionable-regime-confidence/runs/20260524T210813+0800-codex-board-b-bottleneck-source-refresh/summaries/bottleneck_source_refresh.md`.
- Current external source/formula refresh for the active bottleneck:
  `support/docs/experiments/actionable-regime-confidence/runs/20260524T2130+0800-codex-board-b-bottleneck-external-source-refresh/summaries/external_source_refresh.md`.
- Current IBKR historical provider blocker after adjacent zero-row stock
  ladders:
  `support/docs/experiments/actionable-regime-confidence/runs/20260524T2118+0800-codex-ibkr-provider-preflight-after-zero-row-ladders/summaries/provider_preflight_summary.md`.
- Historical compact contract and archived rows:
  `support/docs/plans/2026-05-12-board-b-profit-factor-current.md`.
- Board A boundary and regime-state source:
  `support/docs/plans/2026-05-12-board-a-regime-state-current.md`.
- Cleanup and retention gate:
  `support/docs/plans/2026-05-12-board-ab-cleanup-retention-plan.md`.

Old May 10 append-only logs are not live dependencies. Open them only for exact
artifact lookup by heading, root id, hash, or evidence path when a current doc
points there.

The same exact-reference rule applies to the May 17 terminal ledger: do not scan
it broadly for lane selection or candidate discovery.

## Ownership Boundary

Board B owns profitability-factor discovery, training, and downstream admission.
It must root every candidate as:

`main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`

Market, product, provider, symbol, contract, timeframe, source dataset, profile,
and local path are provenance labels only. They must not become branch roots.

Board B must not claim, repair, promote, reject, relabel, or rerun Board A
regime-confidence roots, posterior state, market-state labels, provider
authority preflights owned by Board A, or recovered regime-confidence assets.
Board A context fields inside Board B artifacts are attribution keys only.

## Claim Discipline

Every Board B agent must give itself a stable board-local name before doing any
Board B work. The name must appear in the active claim and in any durable Board
B terminal/readback artifact the agent writes.

Each active claim must state, at minimum:

- `agent_name`
- `owner`
- `claimed_at`
- `last_progress_at`
- `scope`
- `active_task`
- `non_goals`
- `write_surface`
- `run_root` or `tmp_root`
- `status`
- `progress_report` or `latest_report`

An unnamed or vague claim is not valid ownership. An agent that cannot state
exactly what it is doing must stop instead of continuing, repairing, rerunning,
or summarizing a lane. Claims such as "continue", "audit", "help", "repair",
or "readback" are insufficient unless they identify the exact factor/root,
artifact root, gate, and write surface.

Every claim and every durable work artifact must carry timestamps. `claimed_at`
records when ownership started. `last_progress_at` must be updated whenever the
agent produces a meaningful result, blocker readback, command exit, metric file,
or terminal decision. `progress_report`/`latest_report` must point to the latest
human-readable or JSON report under the lane root so another agent can reconstruct
what happened without reading chat history.

Start claims belong outside the repo:

- `/tmp/ict-engine-agent-claims/board-b/`
- `/tmp/ict-engine-agent-claims/board-b-factor-refinement/`

If a lane is already claimed, active, done, or blocked, do not continue, repair,
re-run, summarize, or "help" that lane while the owning work is still live. Pick
a new axis or stop with a compact duplicate/blocker note.

Stale active claims may be taken over when both conditions are true:

- no matching live process is visible for the lane (`run_ibkr_*`,
  `fetch_external.py`, Auto-Quant/freqtrade, TOMAC scan/postscan, IBKR
  `provider-status`, or another command writing under the claimed root); and
- `last_progress_at` is more than one hour old, or the claim has no
  `last_progress_at` and the latest report/terminal artifact is more than one
  hour old or missing.

A takeover must append a timestamped takeover report to the original claim with
`takeover_agent_name`, `takeover_reason`, `takeover_run_root`,
`last_progress_at`, `latest_report`, `decision`, and the invariant
`promotion_allowed=false`, `trade_usable=false`, `update_goal=false` unless the
full live-usability gate actually passes.

A new Board B lane must differ by at least one real ownership axis: factor,
root regime, symbol or instrument set, provider/window, artifact root, or gate.

## Profitability Lifecycle Gate Model

Use the smallest lifecycle plane that answers the current factor question. A
factor can be useful for learning without being ready for simulated or live
execution.

- Gate 1, learning viability: a factor may be learning-admitted when a frozen
  or current Board A regime context is correct, leakage checks pass,
  provider/local evidence is real or explicitly retained, and long-run
  expectancy after declared friction is positive. Gate 1 no longer requires
  fixed `5bps/side` survival, 30 validation rows, PDA alignment, transition
  hazard below `0.60`, or execution readiness above `0.65`.
- Gate 2, paper/sim admission: requires enough forward or retained-real
  density, instrument-aware friction, and replayable candidate packs.
- Gate 3, portability: reproduces learning/paper evidence across chosen
  markets or documents the branch as local/scope-limited.
- Gate 4, live trade usability: requires Pre-Bayes, BBN,
  CatBoost/path-ranker, execution tree, and feedback/update checks. Keep
  `promotion_allowed`, `trade_usable`, and `update_goal` false unless this
  live-ready plane passes.

Default terminal decision fields:

`factor_id`, `claimed_gate`, `root_regime` or `root_agnostic`,
`evidence_path`, `decision=keep/drop/incubate/blocked/handoff`,
`next_unclaimed_idea`.

## Write Policy

Runtime truth lives in code, provider configs, state dirs, candidate packs,
admission targets, JSON/CSV/JSONL artifacts, and CLI output. Docs may point to
that truth, but code must not import, parse, grep, or depend on these markdown
plans.

Write detailed evidence to compact run-root packets under
`support/docs/experiments/actionable-regime-confidence/runs/...`, especially
`checks/`, `summaries/`, and `materials/`.

Append only durable terminal decisions to the terminal-decision board. Do not
append routine coordination, start claims, in-progress chatter, or broad
research prose to Board B markdown.

## Current Practical Bias

Prefer real provider or retained-real evidence over synthetic/demo evidence.
For futures/TOMAC continuation, prefer local TOMAC CSV or IBKR historical/sim
data, start at `1m`, and preserve `5m/15m/30m/1h/4h/1d` context when the lane
claims full-MTF or downstream admission.

Until superseded, new Board B factor lanes should be trend-continuation first:
trend-following, breakout/continuation, TrendExpansion, Donchian/Turtle,
SuperTrend/ADX, Keltner/ATR breakout, Heikin-Ashi/ATR trend, Vortex/VI,
Aroon/CCI continuation, PSAR trend flip, momentum-window continuation, and
volatility-expansion trend families. Prefer multi-timeframe resonance: low
timeframe entries, usually `1m`, should align with higher-frame trend evidence
from real retained `5m/15m/30m/1h/4h/1d` frames where available. Countertrend
signals are allowed only as protective filters on an already cost-surviving
trend root.

IBKR historical data and paper/sim fills are preferred validation surfaces when
available, but they are not shortcuts around lifecycle gates. Simulated fills
count as execution-readiness, latency, and slippage evidence only after the
same rooted factor has learning viability and replayable evidence; they do not
set `promotion_allowed`, `trade_usable`, or `update_goal`.

Do not promote a Board B factor from provider success, Auto-Quant exit `0`,
single sparse profitable rows, `2bps`-only survival, visible-only ranker
evidence, paper/sim fills, or observe-only execution status. Promotion requires
the live trade usability plane: exact rooted downstream admission and the
relevant cost, density, transition, validation, and execution-readiness gates.
