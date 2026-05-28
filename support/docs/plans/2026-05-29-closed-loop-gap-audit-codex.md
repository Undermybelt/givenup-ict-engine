# Closed-Loop Gap Audit - 2026-05-29

- created_at: `2026-05-29T05:35:07+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- local workdoc: `/tmp/ict-engine-closed-loop-gap-audit-20260529T053507+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T053507+0800-codex-closed-loop-gap-audit.claim`
- status: `terminalized_partial_static_source_guard`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Continue the user's full objective without narrowing it: find and close concrete
loopholes that could let factor-training, practical admission, or closed-loop
readiness be claimed without evidence across provider/data, regime posterior,
Pre-Bayes, BBN, structural path-ranker, execution tree, feedback/update, and
training/refinement.

## Current Readback

- Routing completed through `skill-router.md`, `project-router.md`, repo
  `CLAUDE.md`, repo `AGENTS.md`, repo `AGENT.md`, and installed runtime skill
  `software-development/ict-engi-fact-rese-muta/SKILL.md`.
- Compact claim audit at start of slice: `status=needs_attention`,
  `active_claims=1`, `valid_active_claims=1`, `live_factor_processes=0`,
  `fresh_active_claims_without_live_process=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`.
- Focused process scan showed an active `ict-engine auto-quant-prepare` process
  under `/tmp/ict-engine-tomac-opening-drive-exact-long-aq-probe-20260529T0532+0800/state`.
- Decision: no provider, IBKR, Auto-Quant, TOMAC, factor-research, materialization,
  paper/sim, or live launch in this slice. Work is static/readback audit only.

## Non-Goals

- Do not take over the fresh OpeningDrive claim unless it becomes stale by the
  documented takeover rule and no matching live process is present.
- Do not edit active factor runtime roots or launch wrappers owned by another
  active claim.
- Do not lower cost, density, validation, ranker, execution, provider,
  feedback, simulated/paper/live, promotion, or trade-use gates.
- Do not mark the full objective complete unless current evidence proves every
  closed-loop requirement.

## Audit Targets

- `support/scripts/objective_closure_snapshot.py`
- `support/scripts/done_definition_audit.py`
- practical-admission source checker coverage and its debt/quarantine behavior
- existing closed-loop tracking artifacts under `/tmp` and `support/docs/plans/`

## Findings

- `2026-05-29T05:58:24+0800`: Static practical-admission source scan slice
  verified a narrower source-checker contract and one real fail-closed repair.
  The checker now allows passive readbacks of existing practical fields from
  claim/report/lifecycle payloads, explicit local `False` aliases, and
  diagnostic `allowed_targets` maps without treating them as practical-use
  writers. It still flags reassigned aliases and practical dicts that bypass
  `practical_admission_flags(...)`.
- Real source repair: `support/scripts/research/recovered_regime_asset_bundle.py`
  no longer lets `--allow-trade-usable` promote a recovered regime asset into
  `trade_usable=true`; recovered assets remain inspection/scope-limited until a
  downstream live-admission surface exists. `consumer_contract.promotion_allowed`
  is explicit `false`.
- Done-definition practical source coverage now includes the tracked helper
  report `support/scripts/research/regime_root_survivor_blocker_report.py` in
  addition to tracked `run_*.py` wrappers, while staying root-local in temp-root
  tests.
- Production tracked source scan over non-test `support/scripts/**` practical
  flag surfaces returned no violations. A broader all-file scan still reports
  deliberate test fixtures with `promotion_allowed=True`, `trade_usable=True`,
  `None`, or string values; those are test data, not runtime source, and are not
  part of the done-definition production scan set.
- Objective closure remains red. The after-fix snapshot exited `1` with blockers:
  `done_definition_not_completion_ready`, `practical_admission_source_debt`,
  `factor_closure_blocked`, `release_readiness_blocked`, and
  `release_remote_checks_not_run`.
- Current factor closure blocker is still active-claim state, not live runtime.
  Before terminalizing this packet, compact audit reported `active_claims=2`.
  After terminalizing this packet, compact audit reported `active_claims=1`,
  `live_factor_processes=0`, and one fresh wait-only OpeningDrive claim.

## Verification

- RED before implementation:
  - `python3 -m unittest support.scripts.research.tests.test_recovered_regime_asset_bundle -v` failed
    `test_allow_trade_usable_flag_does_not_bypass_downstream_live_admission_requirement`.
  - Focused new checker tests failed for explicit-false aliases, passive report
    readback, and diagnostic `allowed_targets` before the checker patch.
  - New done-definition helper-report scan-set test errored before the scan-set
    constant existed.
- GREEN after implementation:
  - `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v`
    passed `28/28`.
  - `python3 -m unittest support.scripts.research.tests.test_recovered_regime_asset_bundle -v`
    passed `3/3`.
  - `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
    passed `25/25`.
  - Production source scan:
    `git ls-files 'support/scripts/research/*.py' 'support/scripts/auto_quant_external/*.py' 'support/scripts/*.py' | rg -v '/tests/' | xargs rg -l 'promotion_allowed|trade_usable|update_goal|practical_admission_flags' | rg -v 'support/scripts/research/downstream_practical_admission_source_check.py$' | xargs python3 support/scripts/research/downstream_practical_admission_source_check.py --pretty`
    exited `0`; all scanned production reports were `ok=true`.
  - `python3 support/scripts/objective_closure_snapshot.py --compact --output-dir /tmp/ict-engine-closed-loop-gap-audit-20260529T053507+0800/objective-snapshot-after-static-fix`
    exited `1`; see blocker list above.
  - `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
    exited `1`; active claims still block factor closure.
  - `git diff --check` exited `0`.

## Terminal Decision

- Static source-checker slice verified and terminalized as partial evidence only.
- Full objective is not complete and no 100% confidence claim is valid.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
- Do not launch provider/AQ/TOMAC/factor-research work until active claims are
  rechecked and cleared or stale-safe takeover rules are satisfied.
