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

## Repo Hygiene Hard Rule

Factor-training scratch must not accumulate in the repo. During intake,
prescreening, and prep-only work, write temporary plans, workdocs, runners,
local screen outputs, AQ/Freqtrade workspaces, caches, model output, and
non-promoted run trees under `/tmp/ict-engine-...`.

Repo paths are allowed only for intentionally tracked or force-added evidence
packets, product code/tests, or reviewed durable references. If a candidate has
not reached `trade_usable=true` and has not become an explicit evidence packet,
leave it in `/tmp` or delete/externalize it. Do not leave ignored or untracked
training files under `support/docs/plans/`, `support/docs/experiments/`,
`support/docs/experiments/actionable-regime-confidence/runs/`, `state/`,
`state_experiments/`, `.local-artifacts/`, `catboost_info/`, or
`path_ranker_model/`.

The repo done-definition harness enforces this with
`repo_training_scratch_surface`; a failing gate means the residue must be
tracked as a real evidence/product surface, moved to `/tmp`, or removed.

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
- When the user asks to build knowledge reserves while waiting, use the
  waiting-window pattern in `references/waiting-window-factor-research.md`.

Good waiting work is deliberately interruptible. Keep each source note small
enough that another agent can stop after any item and still retain value:
one source, one candidate, one duplicate check, one next command. Prefer
adding to a candidate queue over starting a runtime process.

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

## Candidate Scoring

Use this quick score before spending runtime on a candidate:

| Field | Good sign | Reject or defer |
|---|---|---|
| Data fit | cleaned retained/provider data covers origin plus context ladder | short window, missing HTF, raw stitched source, unverified cleaning provenance |
| Cost fit | hold time and payoff can clear real costs | 1m churn or unknown fee model |
| Density | likely one trade per 3 sessions to 3/session | sparse hero trade or overtrading |
| Branch novelty | materially different from terminalized roots | same root with renamed params |
| Closure path | can feed AQ/provider/paper/lifecycle readbacks | Python-only or marker-only |

If any reject/defer column is hit, record the blocker and keep
`promotion_allowed=false` / `trade_usable=false`.

## Cleaned Data Gate

For TOMAC futures and regime-rooted profitability work, source intake and
prescreens must prove cleaned/full-retained data provenance before a candidate
can move to exact-AQ or provider reproduction.

Required fields in workdocs, terminal metrics, terminal summaries, prep
packets, and regime feedback packets:

```text
data_provenance.cleaning_status=cleaned_or_verified_retained
data_provenance.source_root
data_provenance.symbol_aliases
data_provenance.timeframes
data_provenance.raw_fallback_used=false
data_provenance.resample_policy=closed_left_label_left_for_derived_frames
data_provenance.source_archive_validation.status=pass_zip_pristine_source
```

When cleaned archives exist, prefer them over older retained caches. For TOMAC
futures ZIP payloads, the extracted source directory must match the ZIP exactly
before cleaning: no symlinked OHLCV file, no older same-symbol CSV, no shifted
fallback CSV, and no generated higher-timeframe CSV mixed into the raw source
directory. A cleaned root derived from a polluted extracted directory is not
clean evidence even if downstream files are named `cleaned-*`; delete and
re-extract from the ZIP, then regenerate the cleaned MTF root.

Derived timeframes such as `3m` or `30m` must be causally resampled from cleaned
`1m` or be marked unavailable. If a row used raw, stitched, uncleaned, polluted,
symlinked, non-ZIP-pristine, or unknown provenance data, classify it as
`data_scope_blocked_for_cleaned_target` or `observation_only_uncleaned`, keep
all practical flags false, and do not launch exact-AQ from that row until it is
rebased onto cleaned data.

## Useful Starting References

- `references/waiting-window-factor-research.md` for current source-backed
  candidate families and packet shape to use while runtime is occupied.
- `references/paper-strategy-reserve-20260530.md` for paper/strategy/indicator
  seeds gathered during claim-runtime waits, with first Gate 1 shapes and
  fail-closed notes.
- `references/crossasset-carry-risk-reserve-20260530.md` for lower-turnover
  cross-asset carry, commodity term-structure, and variance-risk stress-gate
  reserves gathered during fresh-claim waits.
- Installed Hermes reference
  `ict-engi-fact-rese-muta/references/paper-repo-alpha-intake-to-auto-quant.md`
  for the source-backed intake to Auto-Quant rule.

## Promotion Rule

Source intake can only create candidates. Promotion requires the normal current
gate chain: real or retained-real data, no-lookahead screen, honest cost model,
density and split survival, then same-root AQ/provider/downstream validation
through Pre-Bayes, BBN, path-ranker/CatBoost, execution tree, and lifecycle
readback. Keep `promotion_allowed=false` and `trade_usable=false` until those
current artifacts prove otherwise.
