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
| R6 | Factor claim/process hygiene is clear | `support/scripts/factor_claim_terminalization_audit.py --compact` exits `0` | live-drift sensitive: passed at 07:39, reopened after `4f54a6bf` with active claims, live processes, and one missing run root |
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
  the latest factor audit has `promotion_allowed_true=0` and
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
- [x] Patch the factor-claim audit parser so `pending_*` run-root placeholders
  do not become false `missing_run_roots` blockers.
- [ ] Terminalize or externalize current active factor claims without
  interrupting live provider/AQ processes.
- [ ] Keep release readiness blocked until a clean selected export, fresh
  release docs/signoff, unused version/tag, remote parity, and explicit
  operator approval exist.

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

### 2026-05-23 07:26 CST Pending Run-Root Sentinel Slice

Trigger:

- Fresh factor audit at
  `/tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_latest.json`
  still exited `1`.
- Summary before the patch: `active_claims=6`, `live_factor_processes=4`,
  `missing_run_roots=1`, `terminalized_claims=94`, `total_claims=100`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- The missing-root blocker came from a not-yet-launched claim using
  `run_root=pending_runner_timestamp`, which is a placeholder, not a filesystem
  path.

Patch:

- `support/scripts/factor_claim_terminalization_audit.py`
  - treats `pending_*` `run_root` values as absent/pending sentinels.
- `support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - adds regression coverage for `pending_runner_timestamp` and
    `pending_runner_launch_after_ibkr_fetch_clear`.

TDD / verification:

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_build_report_ignores_none_and_pending_run_root_sentinels -v`
  - exit `1` before the parser patch.
  - expected failure: `missing_run_roots` was `2` instead of `0`.
- GREEN:
  same focused test after the parser patch
  - exit `0`.
- Regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v > /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_pending_sentinels.stdout 2> /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_pending_sentinels.stderr`
  - exit `0`, `15` tests passed.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - exit `0`.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - exit `0`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_pending_sentinels.json`
  - exit `1`.
  - current summary after patch: `active_claims=7`, `live_factor_processes=2`,
    `missing_run_roots=1`, `terminalized_claims=95`, `total_claims=102`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - remaining attention includes active DUOL, XBI, TOMAC TOD, NTNX, USDCHF,
    DYDX/APE, and NEO/QTUM lanes; live processes were NTNX wrapper and child
    IBKR historical fetch at the audit moment.

Decision:

- The parser fix removes one deterministic false-positive class and keeps
  claim/process hygiene more accurate for hot-plug pending runner claims.
- It does not clear factor readiness. There are still active claims/live
  processes, zero promotion/trade-usable positives, and release blockers.

### 2026-05-23 07:33 CST Readback Process Classifier Slice

Trigger:

- Post-commit factor audit at
  `/tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_commit_7fb46d2a.json`
  exited `1`.
- Summary: `active_claims=5`, `live_factor_processes=5`,
  `missing_run_roots=0`, `terminalized_claims=98`, `total_claims=103`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- One `attention_live_processes` entry was a read-only status probe:
  `/bin/zsh -lc ps auxww | rg -i "...run_ibkr...run_bybit"`.
- A later fresh audit also exposed a read-only source readback:
  `sed -n .../scripts/run_ibkr_ntnx_bayesian_markov_trend_detector_1m_mtf_gate1.py`.

Patch:

- `support/scripts/factor_claim_terminalization_audit.py`
  - treats `ps auxww | rg/grep ...` commands as readback commands, same as
    existing `ps -axo | rg/grep ...` handling.
  - treats direct `sed -n ...` source readbacks as readback commands.
  - keeps TOMAC helper scans such as
    `tomac_tod_portfolio_density_repair_scan.py` classified as live factor
    work.
- `support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - adds regression coverage for the `ps auxww | rg` and `sed -n` probe
    shapes.
  - adds coverage that TOMAC helper scans remain detected.

TDD / verification:

- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_ps_auxww_rg_readback_commands -v`
  - exit `1` before the classifier patch.
  - expected failure: `_is_live_factor_command(...)` returned `True`.
- GREEN:
  same focused test after the classifier patch
  - exit `0`.
- RED:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_sed_readback_of_factor_wrappers -v`
  - exit `1` before the refined classifier patch.
  - expected failure: `_is_live_factor_command(...)` returned `True`.
- GREEN:
  same focused `sed -n` test after the refined classifier patch
  - exit `0`.
- Regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v > /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_ps_auxww_readback.stdout 2> /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_ps_auxww_readback.stderr`
  - exit `0`, `16` tests passed.
- Regression after refinement:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v > /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_readback_commands_refined.stdout 2> /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_audit_unittest_readback_commands_refined.stderr`
  - exit `0`, `18` tests passed.
- `python3 -m py_compile support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - exit `0`.
- `git diff --check -- support/scripts/factor_claim_terminalization_audit.py support/scripts/tests/test_factor_claim_terminalization_audit.py`
  - exit `0`.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_readback_refined.json`
  - exit `1`.
  - current summary after refined classifier patch: `active_claims=4`,
    `live_factor_processes=2`, `missing_run_roots=0`,
    `terminalized_claims=99`, `total_claims=103`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - remaining live processes were the NTNX wrapper and child IBKR historical
    fetch; read-only `ps auxww | rg` and `sed -n` commands no longer appeared
    as live factor processes.
- `python3 support/scripts/check_script_manifest.py`
  - exit `0`, `script_manifest status=pass entries=21`.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py`
  - exit `0`, `docs runtime isolation ok`.

Decision:

- This removes another deterministic audit-noise class from live factor process
  detection.
- It does not clear the objective. Real active claims/live wrappers can still
  exist and must terminalize or be externalized by evidence.

### 2026-05-23 07:40 CST Post-Classifier Claim Hygiene Readback

Commits landed since the previous drift readback:

- `7fb46d2a fix: ignore pending factor run roots`
  - prevents `pending_*` run-root placeholders from becoming false missing-root
    blockers.
- `49c2bc31 fix: filter factor audit readback probes`
  - filters read-only `ps auxww | rg/grep` and `sed -n` probes while preserving
    real wrapper/fetch/TOMAC helper process detection.

Fresh factor claim/process audit:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_process_exit_probe.json`
  - exit `0`.
  - status `pass`.
  - summary: `active_claims=0`, `live_factor_processes=0`,
    `missing_run_roots=0`, `terminalized_claims=103`, `total_claims=103`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - attention claims/processes: none.
- NTNX run-root evidence:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T072352+0800-codex-ibkr-ntnx-bayesian-markov-trend-detector-1m-mtf-gate1-v1/`
  - terminal decision: `provider_or_aq_blocked_no_gate1_verdict`.
  - provider rows acquired: `0`; material count: `0`; rank rows: `0`.
  - `promotion_allowed=false`, `trade_usable=false`.

Fresh release-readiness audit:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-full-audit-20260523-codex-refresh/release_readiness_after_commit_49c2bc31.json`
  - exit `1`.
  - status `needs_fix`, `fail_count=4`, `pass_count=1`.
  - `HEAD=49c2bc31a4a5aa8acf9817994c9112620ea90754`.
  - unresolved gates:
    `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.
  - current version remains `0.1.3`; existing mirror tags include `v0.1.3`
    and `v0.1.4`; audit still suggests `0.1.5` / `v0.1.5`.

Decision:

- Factor claim/process hygiene is now clear for the current audit snapshot.
- Practical factor completion is still not proven because there are zero
  `promotion_allowed=true` and zero `trade_usable=true` results.
- Release remains blocked by dirty source state, stale release docs/signoff,
  source remote mismatch, reused current version/tag, and missing explicit
  operator release approval.

### 2026-05-23 07:44 CST Post-Handoff Drift Reopened

Trigger:

- After commit `4f54a6bf docs: record factor hygiene pass`, fresh audits were
  rerun because claim/process state is live-drift sensitive.

Fresh factor claim/process audit:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_commit_4f54a6bf.json`
  - exit `1`.
  - status `needs_attention`.
  - summary: `active_claims=3`, `live_factor_processes=5`,
    `missing_run_roots=1`, `terminalized_claims=103`, `total_claims=106`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - active claims:
    APEUSDT 5m Elder Ray exact Gate 1, APEUSDT exact downstream replay, and
    TOMAC TOD BalancedAdaptiveSlotPortfolio exact AQ broad replay.
  - live processes:
    USDCHF and XBI IBKR wrapper/fetch work, APEUSDT Bybit downstream replay,
    and a USDCHF Auto-Quant/TOMAC child.

Fresh release-readiness audit:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-full-audit-20260523-codex-refresh/release_readiness_after_commit_4f54a6bf.json`
  - exit `1`.
  - status `needs_fix`, `fail_count=4`, `pass_count=1`.
  - `HEAD=4f54a6bf9f9481a533b28ae99cd646d5c27484c9`.
  - unresolved gates:
    `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.

Decision:

- The previous factor hygiene pass remains valid only for its audit timestamp.
- Current state is not clean: active/live factor lanes reopened after that
  snapshot.
- Do not mark full objective complete, do not publish a release, and do not
  claim practical factor usability.

### 2026-05-23 07:47 CST Post-Drift Commit Readback

Trigger:

- After commit `b4e0bc32 docs: record reopened factor drift`, fresh audits were
  rerun to avoid relying on a stale live-process snapshot.

Fresh factor claim/process audit:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-full-audit-20260523-codex-refresh/factor_claim_terminalization_after_commit_b4e0bc32.json`
  - exit `1`.
  - status `needs_attention`.
  - summary: `active_claims=3`, `live_factor_processes=5`,
    `missing_run_roots=0`, `terminalized_claims=105`, `total_claims=108`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - active claims:
    TOMAC TOD BalancedAdaptiveSlotPortfolio exact AQ broad replay,
    TOMAC TOD cap65 exact AQ rebuild, and Bybit WOO/CFX PGO reclaim Gate 1.
  - live processes:
    XBI IBKR wrapper/fetch plus TOMAC exact-AQ / run_tomac child processes.

Fresh release-readiness audit:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-full-audit-20260523-codex-refresh/release_readiness_after_commit_b4e0bc32.json`
  - exit `1`.
  - status `needs_fix`, `fail_count=4`, `pass_count=1`.
  - `HEAD=b4e0bc329094eccdf7bbfb8ae6f753e9810af20c`.
  - unresolved gates:
    `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.

Decision:

- No release action is allowed from this state.
- No practical-factor completion claim is allowed from this state.
- Next safe actions are limited to waiting for live factor lanes to terminalize,
  externalizing abandoned claims from evidence, or cutting a narrow verified
  docs/audit slice that does not touch unrelated dirty source.

### 2026-05-23 07:53 CST Resume Readback

Trigger:

- The operator asked whether there is nothing left to do. Fresh audits were
  rerun instead of answering from the prior snapshot.

Routing:

- route alias: `sd/ict-engine-maintenance-loop`.
- routing files read:
  `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, and repo
  `AGENT.md`.
- `project-router.md` supplied the ict-engine maintenance override.
- runtime skill path:
  `~/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`.
- installed runtime skill used; no upstream fallback.

Fresh factor claim/process audit:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/factor_claim_terminalization_resume_20260523.json`
  - exit `1`.
  - status `needs_attention`.
  - summary: `active_claims=3`, `live_factor_processes=4`,
    `missing_run_roots=0`, `terminalized_claims=106`, `total_claims=109`,
    `promotion_allowed_true=0`, `trade_usable_true=0`.
  - active claims:
    TOMAC TOD cap65 exact AQ rebuild, Bybit WOO/CFX PGO reclaim Gate 1, and
    Bybit ALGO/XTZ Choppiness breakout/reclaim Gate 1.
  - live processes:
    XBI IBKR wrapper/fetch, TOMAC cap65 exact-AQ child, and Bybit WOO/CFX
    wrapper work.

Fresh release-readiness audit:

- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/release_readiness_resume_20260523.json`
  - exit `1`.
  - status `needs_fix`, `fail_count=4`, `pass_count=1`.
  - `HEAD=90ead16f9eca60e9b8eb54aaea2bb3e24c4d372b`.
  - unresolved gates:
    `worktree_clean_for_release`,
    `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`,
    `release_version_tag_available`.
  - current version remains `0.1.3`; existing mirror tags include `v0.1.3`
    and `v0.1.4`; audit suggests `0.1.5` / `v0.1.5` for a future selected
    release.

Current answer:

- There is still work to do.
- Do not claim the full audit/UX/release objective is complete.
- Do not claim practical factor trade usability: current positives remain
  zero for both `promotion_allowed=true` and `trade_usable=true`.
- Do not release, tag, or push from this state.

Next safe actions:

- Recheck factor claims after the live XBI/TOMAC/Bybit processes finish, then
  terminalize or externalize only from evidence.
- Keep release readiness blocked until the dirty source is cut into a clean
  selected export, release docs/signoff are refreshed for an unused version/tag,
  remote parity is proven, and the operator explicitly approves release action.
