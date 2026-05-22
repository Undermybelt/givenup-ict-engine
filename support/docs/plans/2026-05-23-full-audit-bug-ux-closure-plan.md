# 2026-05-23 Full Audit Bug and UX Closure Plan

Owner: Codex
Status: active
Route: `sd/ict-engine-maintenance-loop`
Primary question: whether there is 100% confidence that the full ict-engine
audit, bug cleanup, and uncomfortable-use pain-point plan is complete.

## Deterministic Answer

No. Current evidence does not support a 100% completion claim.

This plan keeps the full objective intact:

- audit the whole current repo state;
- find possible bugs and awkward UX surfaces;
- propose and execute reasonable fixes in repeatable slices;
- update this document as evidence changes;
- continue until every requirement below has fresh authoritative proof.

## Baseline Authority

- `CLAUDE.md` delegates to `AGENT.md`.
- `AGENT.md` requires current local CLI evidence before release, readiness,
  provider, or workflow claims.
- Release/closed-loop authority:
  `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`.
- Factor/claim authority:
  `support/docs/plans/2026-05-23-factor-claim-audit-actionability-handoff-todo.md`.
- Done Definition auditor authority:
  `support/docs/plans/2026-05-22-done-definition-audit-handoff-todo.md`.

## Completion Requirements

Completion requires fresh evidence for all rows. Uncertain evidence means not
complete.

| ID | Requirement | Authoritative Proof | Current State |
|---|---|---|---|
| R1 | Zero-config first run is consumer usable | `provider-status --compact`, DEMO `analyze`, `workflow-status --agent`, `pre-bayes-status`, `policy-training-status` from a fresh `/tmp` state dir | smoke passed at 2026-05-23 06:49 CST; see `/tmp/ict-engine-full-audit-20260523-codex/done_definition_smoke.json` |
| R2 | Public surfaces are token-friendly and do not expose private paths/secrets by default | smoke outputs plus privacy/path scan over captured outputs | smoke privacy scan passed over `/private/tmp/ict-engine-done-definition-audit-smoke-20260522T223543265157Z-43488-out`; release blockers remain |
| R3 | Default provider behavior is zero-config and fallback-oriented | `provider-status --compact` and `workflow-status` evidence, no required private profile | smoke provider output passed; `provider_status.out` reports yfinance live zero-config and public crypto runtimes ready |
| R4 | Closed-loop surfaces are inspectable end-to-end | provider -> regime posterior -> Pre-Bayes -> BBN -> path-ranker/CatBoost visibility -> execution tree -> feedback/training readbacks | smoke passed through analyze/update/workflow/pre-Bayes/policy-training readbacks; practical factor promotion remains unproven |
| R5 | Release readiness is clear | `support/scripts/release_readiness_audit.py --compact --check-remotes` exits `0` | fresh fail: worktree dirty, stale release docs, source origin mismatch, reused `v0.1.3` |
| R6 | Factor claim/process hygiene is clear | `support/scripts/factor_claim_terminalization_audit.py --compact` exits `0` | fresh fail: active claims and live factor processes |
| R7 | At least one practical factor is truly promotion/trade usable if the objective claims practical factor closure | downstream evidence has `promotion_allowed=true` and `trade_usable=true` with cost/sample/provider gates | known zero positives in latest handoff |
| R8 | Docs do not become runtime inputs | `support/scripts/ci/check_docs_runtime_isolation.py` exits `0` | fresh pass |
| R9 | Script governance surfaces are consistent | `support/scripts/check_script_manifest.py` exits `0`; relevant script tests pass | fresh pass for manifest; focused script tests still per-slice |
| R10 | Help/CLI UX has no obvious broken output path | `support/scripts/help_audit.py` or Done Definition audit help gate | fresh pass |
| R11 | Cargo build/lint/test floor is known | `done_definition_audit.py --run-all-heavy` or focused cargo commands | fresh pass for smoke, `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`, and `cargo test` |
| R12 | Dirty worktree is either intentionally preserved or sliced into coherent commits | `git status --short`, staged-path readback before each commit | currently broad dirty tree; not release-ready |
| R13 | Release notes/signoff match selected tag/export | fresh release docs for unused selected tag | known failing in latest release readiness evidence |
| R14 | Source/mirror/tag state is publishable | source selected commit pushed or clean export selected; unused version/tag; mirror parity readback | known failing in latest release readiness evidence |

## Known Current Blockers

These are not guesses; they come from the latest handoff readbacks and current
baseline scan.

- Release readiness is not clear:
  `worktree_clean_for_release`, `release_docs_fresh_for_selected_tag`,
  `source_origin_matches_selected_source`, and `release_version_tag_available`
  were unresolved in the latest release-readiness audit.
- Practical factor closure is not proven:
  the latest factor handoff had `promotion_allowed_true=0` and
  `trade_usable_true=0`.
- The worktree is broad and dirty; release must not publish directly from it.
- Fresh consumer smoke, privacy scan, docs/runtime isolation, script manifest,
  and help audit now pass for this checkout state.
- Heavy cargo gates are now fresh for this snapshot: `cargo check --all-targets`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` passed after
  the compact Done Definition audit. This does not clear release or factor
  blockers.

## Audit Loop

Repeat until all requirements are proven:

1. Run low-pollution read-only audits into `/tmp`.
2. Record exact commands, artifact paths, status, and unresolved gates here.
3. Classify findings:
   - `bug`: wrong behavior or failed invariant;
   - `ux_pain`: confusing, noisy, missing, or maintainer-biased consumer path;
   - `release_blocker`: prevents clean mirror/tag/release;
   - `factor_blocker`: prevents promotion/trade usability;
   - `verification_gap`: completion cannot be proven yet.
4. Pick the smallest coherent repair slice that moves the full objective.
5. Verify the slice with focused tests and relevant audits.
6. Commit only verified files for that slice.
7. Update this document with the new evidence and next unresolved item.

## Current Todo

- [x] Route and baseline readback before main work.
- [x] Admit completion is not proven.
- [x] Create this live full-audit plan.
- [x] Run fresh current-state audits:
  - factor claim terminalization;
  - release readiness with remotes;
  - Done Definition light;
  - docs/runtime isolation;
  - script manifest;
  - help audit;
  - zero-config smoke or its existing smoke auditor.
- [x] Summarize fresh results in the evidence log below.
- [x] Choose the first narrow repair slice from fresh failures:
  convert skipped cargo heavy gates into current evidence.
- [x] Implement and verify the first slice by running focused heavy gates and
  updating this handoff.
- [x] Stage and commit the verified handoff/evidence slice with isolated
  staged paths.

## Evidence Log

### 2026-05-23 06:40 CST Baseline Readback

Routing:

- route alias: `sd/ict-engine-maintenance-loop`.
- runtime skill: `software-development/ict-engine-maintenance-loop`.
- installed runtime skill used; no upstream fallback.

Current baseline:

- Not complete with 100% confidence.
- Current worktree is broad and dirty, with many tracked modifications and
  untracked research/test scripts.
- Latest factor handoff says claim/process hygiene can be clean, but practical
  factor positives remain zero.
- Latest release handoff says release is still blocked by readiness gates.

Next:

- Run fresh audits for this exact HEAD/worktree and update this log.

### 2026-05-23 06:51 CST Fresh Audit Readback

Artifact root:

- `/tmp/ict-engine-full-audit-20260523-codex`.

Commands and results:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex/factor_claim_terminalization.json`
  - exit `1`.
  - status `needs_attention`.
  - unresolved: `active_claims`, `live_factor_processes`.
  - counts: `total_claims=84`, `terminalized_claims=79`,
    `active_claims=5`, `live_factor_processes=5`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-full-audit-20260523-codex/release_readiness.json`
  - exit `1`.
  - status `needs_fix`.
  - failing gates: `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.
  - source HEAD `d7bf41a02ab6ae05bd82de75f159f006ce7bf332`;
    origin/main `79d9579ea38685bd8c798dc80c1f5177e3c220b6`;
    release mirror main `ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
  - `Cargo.toml` version remains `0.1.3`; known release tags include
    `v0.1.3` and `v0.1.4`; audit suggests next patch version `0.1.5`.
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex/done_definition.json`
  - exit `0`.
  - light status `pass`, but `completion_ready=false` because cargo and smoke
    heavy gates were skipped.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`, `docs runtime isolation ok`.
- `python3 support/scripts/check_script_manifest.py`
  - exit `0`, `script_manifest status=pass entries=21`.
- `python3 support/scripts/help_audit.py`
  - exit `0`, status `pass`, `command_count=53`,
    `commands_with_missing_help=0`, `commands_with_help_errors=0`,
    `commands_with_market_bias=0`.
- `python3 support/scripts/done_definition_audit.py --run-smoke --compact --output /tmp/ict-engine-full-audit-20260523-codex/done_definition_smoke.json`
  - exit `0`.
  - status `pass`; `smoke_acceptance_tmp_state=pass`.
  - still `completion_ready=false` because `cargo_check_all_targets`,
    `cargo_clippy_all_targets_deny_warnings`, and `cargo_test` were skipped.
  - smoke output root:
    `/private/tmp/ict-engine-done-definition-audit-smoke-20260522T223543265157Z-43488-out`.
  - explicit privacy scan over that output root passed for:
    `/Users/`, API key, secret, token, and password patterns.
  - provider smoke reports yfinance as live zero-config and
    `binance_public_runtime`, `bybit_public_runtime`, `binance_public`,
    `bybit_public`, and `kraken_public` as public crypto lanes.
- `cargo check --all-targets > /tmp/ict-engine-full-audit-20260523-codex/cargo_check_all_targets.stdout 2> /tmp/ict-engine-full-audit-20260523-codex/cargo_check_all_targets.stderr`
  - exit `0`.
  - finished `dev` profile in `57.93s`.
- `cargo clippy --all-targets -- -D warnings > /tmp/ict-engine-full-audit-20260523-codex/cargo_clippy_all_targets.stdout 2> /tmp/ict-engine-full-audit-20260523-codex/cargo_clippy_all_targets.stderr`
  - exit `0`.
  - finished `dev` profile in `38.39s`.
- `cargo test > /tmp/ict-engine-full-audit-20260523-codex/cargo_test.stdout 2> /tmp/ict-engine-full-audit-20260523-codex/cargo_test.stderr`
  - exit `0`.
  - finished `test` profile in `59.48s`.
  - key readback: `1166 passed; 0 failed` for `src/lib.rs`,
    `327 passed; 0 failed` for `src/main.rs`, integration tests all reported
    `0 failed`, and doc-tests ran with `0 failed`.

Classification:

- `factor_blocker`: active claims and live factor processes still exist; do
  not close practical factor work or claim trade usability.
- `factor_blocker`: `promotion_allowed_true=0` and `trade_usable_true=0`.
- `release_blocker`: release readiness fails because of dirty worktree, stale
  release docs, source remote mismatch, and reused tag/version.
- `verified_current`: cargo check, clippy, and full tests pass for this
  snapshot.
- `verified_current`: zero-config smoke, privacy scan, docs/runtime isolation,
  script manifest, and help audit pass for this worktree snapshot.

Next:

- Do not mark the full objective complete.
- Do not interrupt or claim unrelated live factor processes.
- The first safe repair slice converted skipped heavy cargo gates into fresh
  evidence and updated this handoff.
- Remaining work is not zero:
  active factor claims/processes must terminalize or be externalized, practical
  factor promotion/trade usability still has zero positives, and release
  readiness still needs clean/exported source, fresh release docs/signoff,
  unused version/tag, remote parity, and explicit operator approval.

### 2026-05-23 07:07 CST Factor Claim Audit Classifier Slice

Scope:

- Improve the claim terminalization auditor's current-state accuracy without
  changing any factor verdicts.
- Do not terminalize live claims or interrupt live factor processes.

Patch:

- `support/scripts/factor_claim_terminalization_audit.py`
  - detects current public/provider wrapper families in live process scans:
    `run_bybit_`, `run_yf_`, `run_binance_`, `run_kraken_`, and
    `run_external_`;
  - treats non-path `run_root` sentinels (`none`, `pending`, `n/a`, `na`,
    `null`, `-`) as absent run roots rather than missing filesystem roots.
- `support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - adds regression coverage for all supported sentinel run roots;
  - adds live-process classifier coverage for Bybit, yfinance, Binance,
    Kraken, and external wrapper names.

Verification:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v > /tmp/ict-engine-full-audit-20260523-codex/factor_claim_audit_unittest_refined.stdout 2> /tmp/ict-engine-full-audit-20260523-codex/factor_claim_audit_unittest_refined.stderr`
  - exit `0`, `15` tests passed.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - exit `0`.
- `python3 support/scripts/check_script_manifest.py`
  - exit `0`, `script_manifest status=pass entries=21`.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`, `docs runtime isolation ok`.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py support/docs/plans/2026-05-23-full-audit-bug-ux-closure-plan.md`
  - exit `0`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex/factor_claim_terminalization_after_classifier_refined.json`
  - exit `0`.
  - current summary: `active_claims=0`, `live_factor_processes=0`,
    `missing_run_roots=0`, `terminalized_claims=93`, `total_claims=93`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.

Decision:

- The classifier slice is useful because it catches live non-IBKR/YF/Bybit
  wrapper drift and avoids false missing-root noise from explicit placeholder
  values.
- It clears the current claim/process hygiene blocker only. It does not clear
  factor readiness because there are still zero promotion/trade-usable
  positives.

### 2026-05-23 07:14 CST Post-Commit Drift Readback

Commits landed in this continuation:

- `9df168b3 docs: add full audit closure handoff`
  - created this handoff and recorded fresh audit/smoke/check/clippy/test
    evidence.
- `2853332f fix: tighten factor claim audit classifiers`
  - tightened live factor process detection and run-root sentinel handling.

Fresh post-commit factor audit:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex/factor_claim_terminalization_after_commit_2853332f.json`
  - exit `1`.
  - status `needs_attention`.
  - current summary: `active_claims=1`, `live_factor_processes=2`,
    `missing_run_roots=0`, `terminalized_claims=93`, `total_claims=94`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - active blocker: IHI medical-device ETF Keltner reclaim Gate 1 claim with
    a present run root and live wrapper/fetch processes.

Fresh post-commit release-readiness audit:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-full-audit-20260523-codex/release_readiness_after_commit_2853332f.json`
  - exit `1`.
  - status `needs_fix`, `fail_count=4`, `pass_count=1`.
  - `HEAD=2853332f4b17b0aa6c7a4a494c08439057aa0ea3`.
  - unresolved gates:
    `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.
  - current version remains `0.1.3`; known mirror tags include `v0.1.3` and
    `v0.1.4`; audit still suggests `0.1.5` / `v0.1.5` for a future selected
    release.

Decision:

- The second commit improved audit accuracy but did not make the full objective
  complete.
- Claim/process hygiene is live-drift sensitive and is currently blocked again
  by the IHI lane.
- Release remains blocked by dirty source state, stale release signoff/notes,
  source remote mismatch, reused current version/tag, zero practical
  promotion/trade-usable factors, and missing explicit operator release
  approval.
