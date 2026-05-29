# TOMAC clean-AQ pre-clean claim guard repair

created_at: 2026-05-30T03:30:00+0800
owner: codex
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
status: repaired_guard_not_practical_factor
promotion_allowed: false
trade_usable: false
update_goal: false

## Current answer

There is still no practical factor in this slice:

- promotion_allowed_true: 0
- trade_usable_true: 0
- same_tree_practical_closure: null

The repeated failure mode is not one single bad indicator. Current evidence
splits it into four blockers:

1. Gate-1 economics/density still often fail hard 5bps and cadence gates.
2. Practical closure remains false unless provider -> Pre-Bayes -> BBN/workflow
   -> path-ranker/CatBoost -> execution tree -> feedback -> policy training all
   close in the same rooted packet.
3. Shared claim/runtime ownership blocks safe launch windows.
4. The clean-AQ wrapper allowed expensive clean/stage work before the final AQ
   claim guard, wasting runtime/disk while a fresh foreign claim existed.

This slice fixes blocker 4. It does not claim a practical factor exists.

## Root cause

The clean-AQ wrapper previously ran `run_claim_collision_audit()` only after
raw retained data cleaning and AQ strategy staging. That could still avoid the
final `run_tomac.py` child, but it was too late: long clean/stage work already
occupied shared disk/runtime and made other agents see a live factor process.

Same-turn evidence:

- `factor_claim_terminalization_audit.py --compact` showed a fresh foreign ZS
  claim plus a live TOMAC clean-AQ process.
- The live regression-channel workdoc said the wrapper guard must run before AQ
  child spawn, but `/tmp` contained no `pre_aq_claim_collision_guard.json` while
  cleaning was already in progress.
- That live run ended as host storage failure, not a factor result:
  `runtime_blocked_no_space_before_aq`, `aq_child_started=false`,
  `promotion_allowed=false`, `trade_usable=false`.

## Fix

Changed `run_tomac_index_futures_clean_aq_v1.py` so AQ-enabled runs perform the
claim-collision audit before cleaning retained data or staging AQ strategies.
When a foreign active claim or live runtime exists, it now writes a fail-closed
summary immediately with:

- clean_bundles: []
- aq_staging: []
- aq_commands: []
- promotion_allowed: false
- trade_usable: false

The wrapper keeps the later pre-AQ guard too, because another claim can appear
between cleaning and AQ child spawn.

## Files changed

- support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py
- support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_index_futures_clean_aq.py
- /Users/thrill3r/.hermes/skills/software-development/ict-engi-fact-rese-muta/SKILL.md
- support/docs/experiments/actionable-regime-confidence/20260530T033000+0800-codex-tomac-clean-aq-preclean-claim-guard-repair.md

## Verification

RED:

```bash
python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_run_blocks_foreign_claim_before_cleaning_or_staging_when_aq_enabled -v
```

Observed failure before the fix: `{'clean': 1, 'stage': 1} != {'clean': 0, 'stage': 0}`.

GREEN:

```bash
python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq.TomacIndexFuturesCleanAqTest.test_run_blocks_foreign_claim_before_cleaning_or_staging_when_aq_enabled -v
```

Result: passed.

Regression:

```bash
python3 -m unittest support.docs.experiments.actionable-regime-confidence.scripts.test_tomac_index_futures_clean_aq -v
```

Result: `Ran 87 tests`, `OK`.

Live no-clean/no-stage smoke while a fresh XAU claim existed:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  --root /tmp/ict-engine-guard-preclean-smoke-20260530T033000+0800/aq \
  --compact-root /tmp/ict-engine-guard-preclean-smoke-20260530T033000+0800/compact \
  --symbols ES \
  --timeframes 1m \
  --families regression_channel_r2_slope_breadth \
  --aq-smoke-timeframe 1m \
  --aq-symbol-limit 1 \
  --timeout 5
```

Result: `decision=launch_blocked_by_foreign_claim_or_runtime`,
`clean_bundles=[]`, `aq_staging=[]`, `aq_commands=[]`,
`promotion_allowed=false`, `trade_usable=false`.

## Current blockers

- Fresh active claim at verification time:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T032027+0800-codex-xau-eth-asia-compression-falsebreak-fade-screen.claim`.
- Current compact audit remained `needs_attention`, with `active_claims=1`,
  `live_factor_processes=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- Disk remained tight but improved after the failed live run: `22Gi` available
  on `/System/Volumes/Data` at the last `df -h` check.
- A separate heavy `done_definition_audit.py --run-all-heavy` process was still
  compiling in an Aegis worktree during this slice.

## Next steps

1. Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`.
2. If no fresh active claim and no live runtime exists, choose one fresh lane or
   stale-safe takeover from `/tmp` claims only, not board docs.
3. Before any clean-AQ launch, confirm this wrapper returns no-clean/no-stage on
   foreign claims and writes `pre_aq_claim_collision_guard.json`.
4. If a Gate-1 survivor appears, do not promote until same-root practical
   closure validates provider, Pre-Bayes, BBN/workflow, path-ranker/CatBoost,
   execution tree, feedback/update, and policy training.
5. Clean up disk pressure before any long retained-data multi-symbol run.
