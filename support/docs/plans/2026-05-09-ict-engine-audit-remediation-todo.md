# ICT Engine Audit Remediation TODO

> Scope: architecture, function surface, runtime loop, tests, user experience, consumer view, and open-source contributor view.
> Rule: no subagent/delegate. Keep fixes repo-versioned and verified.

**Goal:** Turn the current research-grade ICT Engine into a clearer, verifiable, contributor-friendly runtime without breaking the existing research loop.

**Architecture:** Keep the current Rust CLI + library + Python external-research bridge. Reduce `src/main.rs`, formalize command/state contracts, and split validation metrics so users can tell whether the loop is merely runnable or actually mature.

**Tech Stack:** Rust 2021, Clap, JSON state files, Python research scripts, optional CatBoost, GitHub Actions.

---

### Live Audit Loop - 2026-05-21 22:21 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. This loop started the
`main.rs` extraction repayment, but fresh Cargo verification is still blocked by
heavy concurrent Rust jobs and an unrelated lib-test compile surface.

Evidence gathered this loop:

- Routing read before work: `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`,
  installed runtime skill
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`,
  plus Aegis TDD and verification-before-completion.
- Active unrelated Cargo, Auto-Quant, TOMAC, and provider jobs were observed;
  this slice did not kill or take over those processes.
- Current-turn starting line counts:
  - `src/main.rs`: 19360
  - `src/application/artifacts.rs`: 3217
  - `src/status_command.rs`: 252
- Extraction performed:
  - Added `src/artifact_cli_args.rs`.
  - Moved the Clap arg payloads for `artifact-status`, `artifact-lineage`, and
    `artifact-diff` out of the monolithic `Commands` enum fields and into
    `ArtifactStatusArgs`, `ArtifactLineageArgs`, and `ArtifactDiffArgs`.
  - Left `main.rs` responsible for subcommand declaration and dispatch only.
  - Kept output rendering in `src/application/artifacts.rs` and shell routing in
    `src/status_command.rs`.
- Post-extraction line counts:
  - `src/main.rs`: 19237
  - `src/artifact_cli_args.rs`: 149
  - Net result: `main.rs` is 123 lines smaller in this turn, but the extraction
    has not yet been Cargo-verified.
- Verification attempted:
  - `cargo test test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    with an isolated target first surfaced unrelated existing lib-test compile
    error `E0369` in `src/ict/bos_choch.rs` because `StructureType` lacks
    `PartialEq`.
  - Corrected target command
    `CARGO_TARGET_DIR=/tmp/ict-engine-codex-artifact-cli-baseline cargo test --bin ict-engine test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    was stopped after long compile contention in `rustc src/lib.rs` with no
    pass/fail signal.
  - Shared-target `cargo test --bin ict-engine ...` was also stopped while
    waiting on the Cargo artifact-directory lock.
  - Bounded command
    `CARGO_TARGET_DIR=/tmp/ict-engine-codex-artifact-cli-baseline cargo check --bin ict-engine`
    was stopped after 180 seconds with no compile error surfaced; it was still
    checking dependencies under the isolated target.
  - `rustfmt --edition 2021 src/main.rs src/artifact_cli_args.rs` completed.
  - `rustfmt --edition 2021 --check src/main.rs src/artifact_cli_args.rs`
    passed.
  - `git diff --check -- src/main.rs src/artifact_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
    passed.
- Continuation recheck:
  - Live `src/types.rs` now already derives `PartialEq, Eq` for
    `StructureType`, so the earlier `E0369` from `src/ict/bos_choch.rs` is
    stale relative to current files. Those files are dirty from another lane
    and were not edited here.
  - Retried
    `CARGO_TARGET_DIR=/tmp/ict-engine-codex-artifact-cli-baseline cargo test --bin ict-engine test_cli_artifact_commands_accept_output_aliases -- --nocapture`.
    It was stopped after another long compile wait in `rustc src/lib.rs`
    with no compiler error or test result surfaced.
  - Reconfirmed `rustfmt --edition 2021 --check src/main.rs src/artifact_cli_args.rs`
    and `git diff --check -- src/main.rs src/artifact_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
    both pass.
- Static agent/contributor truth-map cleanup:
  - Compared `AGENT.md`, `support/docs/factor-catalog.md`, and
    `src/factor_lab/factor_definition.rs`.
  - Found that the catalog still reported only 5 active Rust factors while the
    code and agent map expose 8 `FactorCategory` variants.
  - Updated `support/docs/factor-catalog.md` to list `crowding_herding`,
    `spectral_rhythm`, and `session_liquidity`, and replaced brittle line-number
    references with constructor names.
  - Updated `AGENT.md` to use constructor references and to describe Families
    E/F/H as active partial compute paths rather than stale compute stubs.
  - Added `support/scripts/check_factor_truth_map.py`, a read-only docs guard
    that parses `FactorCategory::as_str()` and checks that all factor keys
    appear in `AGENT.md` and `support/docs/factor-catalog.md`.
  - `python3 support/scripts/check_factor_truth_map.py` passed with
    `factor_truth_map status=pass factors=8 docs=2`.
  - `python3 -m py_compile support/scripts/check_factor_truth_map.py` passed.
  - `git diff --check -- AGENT.md support/docs/factor-catalog.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md support/scripts/SCRIPTS.md support/scripts/check_factor_truth_map.py src/main.rs src/artifact_cli_args.rs`
    passed.
- Continuation verification on 2026-05-21 23:55 +0800:
  - Re-read live worktree and process state before acting. The tree is still
    shared and dirty; this continuation only owns the active plan-doc evidence
    update plus the inherited artifact CLI / factor truth-map slice.
  - Active unrelated Cargo/rustc jobs were still compiling under
    `.local-artifacts/cargo-target`, alongside unrelated TOMAC/provider jobs, so
    this continuation did not kill or take over those processes.
  - Fresh static/doc checks passed:
    - `python3 support/scripts/check_factor_truth_map.py`
      -> `factor_truth_map status=pass factors=8 docs=2
      keys=trend_momentum,volatility_mean_reversion,structure_ict,cross_market_smt,options_hedging,crowding_herding,spectral_rhythm,session_liquidity`
    - `python3 -m py_compile support/scripts/check_factor_truth_map.py`
    - `rustfmt --edition 2021 --check src/main.rs src/artifact_cli_args.rs`
    - `git diff --check -- AGENT.md support/docs/factor-catalog.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md support/scripts/SCRIPTS.md support/scripts/check_factor_truth_map.py src/main.rs src/artifact_cli_args.rs`
  - Full `cargo fmt --check` is not currently green: it exits 1 on formatting
    drift in non-owned dirty files
    `src/application/orchestration/workflow_status.rs` and
    `src/factor_lab/factor_definition.rs`. Scoped formatting for this
    extraction slice remains green.
- Script governance continuation on 2026-05-22 00:04 +0800:
  - RED: `test -f support/scripts/script_manifest.json && python3 support/scripts/check_script_manifest.py`
    exited 1 because the manifest/checker path did not exist yet.
  - Added `support/scripts/script_manifest.json` with stable public helpers,
    public wrappers, read-only utility, active bridges, provider/operator
    bridges, safe-default flags, data requirements, and test commands.
  - Added `support/scripts/check_script_manifest.py`, a read-only manifest
    checker that rejects missing fields, unknown stability values, private path
    leaks, repo-escaping entrypoints, missing entrypoints, duplicate names, and
    missing required public script surfaces.
  - Added standard-library wrapper coverage in
    `support/scripts/tests/test_public_wrappers.py` for:
    `search_local.py`, `search_cluster.py`, `evaluate_bottleneck.py`, and
    `research_verdict.py`. These tests verify default help/no-run behavior,
    target disclosure, run refusal without ready cleaned data, and read-only
    verdict JSON on an empty result directory.
  - Updated `support/scripts/SCRIPTS.md` to point contributors at the manifest
    and checker.
  - Fresh verification passed:
    - `python3 support/scripts/check_script_manifest.py`
      -> `script_manifest status=pass entries=15 required_public_entries=4 safe_required_public_entries=4`
    - `python3 -m py_compile support/scripts/check_script_manifest.py support/scripts/tests/test_public_wrappers.py`
    - `python3 -m unittest support/scripts/tests/test_public_wrappers.py`
      -> `Ran 4 tests ... OK`
    - `python3 -m json.tool support/scripts/script_manifest.json >/dev/null`
    - `git diff --check -- support/scripts/SCRIPTS.md support/scripts/script_manifest.json support/scripts/check_script_manifest.py support/scripts/tests/test_public_wrappers.py support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
- Contribution/release doc continuation on 2026-05-22 00:17 +0800:
  - Read current `CONTRIBUTING.md`, `support/docs/contributor-quickstart.md`,
    `support/docs/main-rs-guardrails.md`, `support/docs/release-mirror-runbook.md`,
    and `Cargo.toml` metadata.
  - `CONTRIBUTING.md` already exists and README links it, but it did not
    directly point contributors to `support/docs/main-rs-guardrails.md`.
  - `support/docs/release-mirror-runbook.md` still had an older status note and
    did not name the current `Cargo.toml` version observed in this tree.
  - Updated `CONTRIBUTING.md` with explicit main-entrypoint placement rules and
    release-mirror/source-tree boundaries.
  - Updated `support/docs/release-mirror-runbook.md` with a current metadata
    note: `version = "0.1.3"`, repository
    `https://github.com/Undermybelt/ict-engine-release`, and no release-readiness
    inference from the version field.
- `main.rs` guardrail continuation on 2026-05-22 00:22 +0800:
  - Measured current line counts:
    - `src/main.rs`: 19,202
    - `src/artifact_cli_args.rs`: 149
    - `src/application/artifacts.rs`: 3,217
    - `src/status_command.rs`: 252
  - Updated `support/docs/main-rs-guardrails.md` with the current debt
    baseline and the retained long-term target `src/main.rs < 5,000` lines.
- Python path-ranker contract continuation on 2026-05-22 00:30 +0800:
  - Added RED test
    `support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`.
  - RED result:
    `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
    ran 3 tests and failed 2:
    - missing target CSV surfaced raw `[Errno 2] No such file or directory`
      instead of stable target-CSV context.
    - malformed target CSV without `path_id` did not fail validation.
  - Existing row-count parity for `--apply --allow-direct-fallback` with no
    mature rows already passed in RED.
  - Updated `pandas_path_ranker_trainer.py::load_target_csv` to:
    - reject missing files with `target CSV does not exist: <path>`;
    - wrap CSV read failures with `failed to read target CSV <path>: ...`;
    - require `candidate_set_id` and `path_id`;
    - reject empty target CSVs.
  - GREEN verification passed:
    - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
      -> 3 tests OK.
    - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_hotplug.py`
      -> 13 tests OK.
    - `python3 -m py_compile support/scripts/auto_quant_external/pandas_path_ranker_trainer.py support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
    - `git diff --check -- support/scripts/auto_quant_external/pandas_path_ranker_trainer.py support/scripts/auto_quant_external/tests/test_path_ranker_contract.py support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
- Cargo verification continuation on 2026-05-22 00:39 +0800:
  - `cargo test --bin ict-engine test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    passed:
    - `1 passed; 0 failed; 0 ignored; 278 filtered out`
    - finished after compiling the bin test profile in about 2m05s.
  - `cargo check --bin ict-engine` was attempted after the focused test, but it
    waited on the shared Cargo build-directory lock behind unrelated process
    `cargo test rooted_short_branch_direction_prevents_false_mtf_factor_conflict --quiet`.
  - The queued `cargo check --bin ict-engine` process was stopped after the lock
    wait; unrelated Cargo/rustc jobs were not killed.
- Cargo verification continuation on 2026-05-22 00:49 +0800:
  - Retried `cargo check --bin ict-engine` after the lock cleared.
  - Result: exit 0, `Finished dev profile`, but the run emitted one warning:
    unused import `build_pre_bayes_evidence_filter` in `src/main.rs`.
  - Moved `build_pre_bayes_evidence_filter` into the `#[cfg(test)] mod tests`
    import scope because all direct call sites are test-only while runtime code
    uses `build_pre_bayes_evidence_filter_with_branch_context`.
  - Ran `rustfmt --edition 2021 src/main.rs src/artifact_cli_args.rs`.
  - Fresh static checks after the warning cleanup passed:
    - `rustfmt --edition 2021 --check src/main.rs src/artifact_cli_args.rs`
    - `git diff --check -- src/main.rs src/artifact_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md support/scripts/auto_quant_external/pandas_path_ranker_trainer.py support/scripts/auto_quant_external/tests/test_path_ranker_contract.py CONTRIBUTING.md support/docs/release-mirror-runbook.md support/docs/main-rs-guardrails.md support/scripts/SCRIPTS.md support/scripts/script_manifest.json support/scripts/check_script_manifest.py support/scripts/tests/test_public_wrappers.py AGENT.md support/docs/factor-catalog.md support/scripts/check_factor_truth_map.py`
  - Warning cleanup still needs a fresh `cargo check --bin ict-engine` rerun;
    unrelated Cargo/rustc jobs became active again before this recheck.
- Cargo verification continuation on 2026-05-22 00:40 +0800:
  - Re-read live worktree, the plan head, and current Cargo/rustc process state
    before running the shared target. Only an unrelated TOMAC Python scan was
    active; no Cargo/rustc process was holding `.local-artifacts/cargo-target`.
  - `cargo check --bin ict-engine` after the warning cleanup exited 0:
    - `Finished dev profile [unoptimized + debuginfo] target(s) in 19.52s`
    - no warning lines were emitted in the captured output.
  - Refreshed the focused artifact CLI regression:
    - `cargo test --bin ict-engine test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    - result: `1 passed; 0 failed; 0 ignored; 278 filtered out`.
  - Full `cargo fmt --check` remains unresolved because earlier fresh evidence
    showed formatting drift in non-owned dirty files
    `src/application/orchestration/workflow_status.rs` and
    `src/factor_lab/factor_definition.rs`; do not mark the whole tree fmt-clean
    until that drift is explicitly taken or reconciled.
  - Structural path-ranker Rust coverage was refreshed:
    - `cargo test --bin ict-engine test_cli_structural_path_ranker_commands_accept_output_aliases -- --nocapture`
      -> `1 passed; 0 failed; 278 filtered out`.
    - `cargo test applying_structural_path_ranking_external_scores_updates_current_and_history_exports -- --nocapture`
      -> lib test `1 passed; 0 failed; 1133 filtered out`, with all other
      discovered integration targets filtered to zero matching tests.
  - This proves the CLI flag parser surface and the Rust apply/update current
    plus history export path. It does not replace a full command-process smoke
    that runs `apply-structural-path-ranking-external-scores` from a generated
    score file.
  - Full-tree format gate was reconciled as an explicit CI cleanup slice:
    - Previous `cargo fmt --check` failed only on mechanical rustfmt drift in
      already-dirty `src/application/orchestration/workflow_status.rs` and
      `src/factor_lab/factor_definition.rs`.
    - Ran
      `rustfmt --edition 2021 src/application/orchestration/workflow_status.rs src/factor_lab/factor_definition.rs`.
    - `cargo fmt --check` then exited 0.
  - Broader compile gate was refreshed after confirming no Cargo/rustc process
    held the shared target:
    - `cargo check --all-targets`
    - result: exit 0, `Finished dev profile [unoptimized + debuginfo] target(s) in 1m 42s`.
  - Non-Cargo script/doc guards were refreshed while other agents were running
    focused Cargo tests:
    - `python3 support/scripts/check_script_manifest.py`
      -> `script_manifest status=pass entries=15 required_public_entries=4 safe_required_public_entries=4`.
    - `python3 support/scripts/check_factor_truth_map.py`
      -> `factor_truth_map status=pass factors=8 docs=2`.
    - `python3 -m unittest support/scripts/tests/test_public_wrappers.py`
      -> `Ran 4 tests ... OK`.
    - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py support/scripts/auto_quant_external/tests/test_path_ranker_hotplug.py`
      -> `Ran 16 tests ... OK`.
  - Clippy was not started immediately after the all-target check because live
    process state showed other lanes running focused `cargo test`/`rustc`
    against the shared `.local-artifacts/cargo-target`.
  - Clippy warning gate was then run and failed once:
    - `cargo clippy --all-targets -- -D warnings`
    - failure: `clippy::too_many_arguments` at
      `src/config.rs:693` for
      `build_pre_bayes_evidence_filter_with_branch_context` with 8 arguments.
  - Root cause: the branch-direction Pre-Bayes context had been added as an
    eighth positional parameter to an already-threshold builder API.
  - Fix:
    - Added typed `PreBayesEvidenceFilterInput<'a>` in `src/config.rs`.
    - Kept the existing 7-argument `build_pre_bayes_evidence_filter(...)`
      compatibility wrapper.
    - Changed the branch-context helper to accept the typed input.
    - Updated the runtime caller in `src/main.rs` and the focused branch-context
      unit test in `src/config.rs`.
  - Focused regression after the refactor:
    - `cargo test rooted_short_branch_direction_prevents_false_mtf_factor_conflict -- --nocapture`
    - result: lib test `1 passed; 0 failed; 1133 filtered out`; all discovered
      integration targets had zero matching tests.
  - Warning gate after the refactor:
    - `cargo clippy --all-targets -- -D warnings`
    - result: exit 0, `Finished dev profile [unoptimized + debuginfo] target(s) in 31.56s`.
  - Re-ran format and whitespace checks after the refactor:
    - `cargo fmt --check` exited 0.
    - `git diff --check -- src/config.rs src/main.rs src/artifact_cli_args.rs src/application/orchestration/workflow_status.rs src/factor_lab/factor_definition.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` exited 0.
  - Zero-config consumer smoke was refreshed with explicit `/tmp` state:
    - Command:
      `STATE_DIR=/tmp/ict-engine-smoke-acceptance-20260521T165818Z OUT_DIR=/tmp/ict-engine-smoke-acceptance-20260521T165818Z/smoke-output support/scripts/smoke_acceptance.sh`.
    - The script ran `provider-status --compact`, empty-state
      `workflow-status --human`, `analyze --demo --human`,
      refreshed `workflow-status --agent`, `pre-bayes-status --output-format json`,
      and `policy-training-status --output-format agent`.
    - Result:
      `smoke_acceptance: passed state_dir=/tmp/ict-engine-smoke-acceptance-20260521T165818Z output_dir=/tmp/ict-engine-smoke-acceptance-20260521T165818Z/smoke-output`.
    - The built-in private-output scan did not fail on `/Users/...` or
      secret-like strings in the captured smoke output.
  - Full test gate was run and failed once:
    - `cargo test`
    - result: exit 101 after lib tests reported `1131 passed; 3 failed`.
    - failing tests:
      `execution_candidate_phase_keeps_duplicate_analyze_veto_over_same_root_trace_admission`,
      `execution_candidate_phase_records_trace_admission_but_keeps_duplicate_analyze_veto`,
      and `test_structure_ict_large_frame_setup_matches_are_recent_and_rebased`.
  - Root-cause readback:
    - Workflow-status execution-candidate synthesis was allowing same-root
      execution-tree admission to overwrite a persisted duplicate analyze veto,
      and a trace-only path could lose precedence when a synthetic recommended
      bundle was available.
    - The large-frame ICT setup test fixture used
      `OrderBlock -> MarketStructureShift -> OrderBlock`, which does not form a
      matcher-valid recent canonical setup after rebasing.
  - Fixes:
    - `src/application/orchestration/workflow_status.rs` now preserves the
      persisted analyze veto while still recording the same-root execution-tree
      admission payload.
    - `src/factor_lab/factor_definition.rs` fixture now uses a valid recent
      `MarketStructureShift -> InverseFairValueGap` setup to exercise the
      large-frame recent-window rebase path.
  - Focused green reruns:
    - `cargo test duplicate_analyze_veto -- --nocapture`
      -> `2 passed; 0 failed; 1132 filtered out`.
    - `cargo test test_structure_ict_large_frame_setup_matches_are_recent_and_rebased -- --nocapture`
      -> `1 passed; 0 failed; 1133 filtered out`.
  - Full test gate after the fixes:
    - Inherited session `4044` completed `cargo test`.
    - Result: lib/bin-style tests `1134 passed; 0 failed`; main-harness tests
      `279 passed; 0 failed`; integration test crates and doc tests also
      exited with `0 failed`.
    - A later accidental shell-expanded probe exited `2` from `rg` pattern
      parsing after running tests and is not counted as verification evidence.
  - Rust structural path-ranker apply/error-contract continuation on
    2026-05-22:
    - Added `tests/structural_path_ranker_contract.rs` and
      `tests/fixtures/policy_training/structural_path_ranking_scores.csv`.
    - RED:
      `cargo test --test structural_path_ranker_contract -- --nocapture`
      ran 3 tests and failed 2 because missing score files surfaced only
      `No such file or directory (os error 2)` and malformed score CSVs surfaced
      raw CSV deserialize errors without command/schema recovery context.
    - Fix: `load_structural_path_ranking_external_scores(...)` now checks the
      score-file path up front and wraps JSONL/CSV read/parse failures with the
      required score schema `candidate_set_id,path_id,raw_path_score` and the
      recovery command `export-structural-path-ranking-target`.
    - GREEN:
      `cargo test --test structural_path_ranker_contract -- --nocapture`
      -> `3 passed; 0 failed`; the valid fixture score CSV updates the persisted
      target row while the missing/malformed cases include path, schema, and
      recovery context.
    - Guard checks after the patch:
      - `rustfmt --edition 2021 --check src/application/entry_models/training_export.rs tests/structural_path_ranker_contract.rs`
        exited 0.
      - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
        -> `Ran 3 tests ... OK`.
      - `git diff --check -- src/application/entry_models/training_export.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited 0.
      - `cargo check --all-targets` exited 0:
        `Finished dev profile [unoptimized + debuginfo] target(s) in 54.82s`.
  - Full fixture-chain continuation on 2026-05-22:
    - Added fixture target CSV:
      `tests/fixtures/policy_training/structural_path_ranking_target.csv`.
    - Extended Python contract coverage so
      `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
      uses the shared fixture target and proves direct fallback scoring emits
      one score row with `score_model_family=weighted_feature_sum_v1`.
    - Extended Rust integration coverage so
      `tests/structural_path_ranker_contract.rs` now proves:
      fixture score apply -> trainer artifact registration -> runtime enable ->
      status surface reports
      `runtime_selection_status=enabled_registered_artifact_ready`,
      `runtime_source_kind=registered_artifact`, and `runtime_matches=1`.
  - The shared-target Cargo run was not counted because it stayed stuck on the
    artifact-directory lock without a visible Cargo/rustc process. The
    verified proof used an isolated target:
    `CARGO_TARGET_DIR=/tmp/ict-engine-structural-ranker-contract-target cargo test --test structural_path_ranker_contract -- --nocapture`
    -> `4 passed; 0 failed`.
  - Register-artifact error-message continuation on 2026-05-22 01:59 +0800:
    - Added RED coverage in `tests/structural_path_ranker_contract.rs` for
      `register-structural-path-ranking-trainer-artifact` missing target export,
      malformed target summary JSON, and malformed explicit-family trainer
      artifact JSON.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-register-error-contract-target cargo test --test structural_path_ranker_contract -- --nocapture`
      ran 7 tests and failed the 3 new register-artifact assertions:
      missing target export lacked the exact recovery command, malformed summary
      exposed raw serde text, and malformed explicit artifact did not include
      the artifact path.
    - Fix: `register_structural_path_ranking_trainer_artifact(...)` now wraps
      target-summary read/parse failures with target path, expected
      `structural_path_ranking_target` JSON, and
      `export-structural-path-ranking-target` recovery. Explicit rule/tree
      families now require readable trainer-artifact JSON and include the
      artifact path plus `rule_list or tree_json` / register-command context.
  - GREEN:
    `CARGO_TARGET_DIR=/tmp/ict-engine-register-error-contract-target cargo test --test structural_path_ranker_contract -- --nocapture`
    -> `7 passed; 0 failed`.
  - Analyze / factor-research missing-data continuation on 2026-05-22:
    - Added RED coverage for `analyze --data-htf` missing-file context in
      `src/analyze_command.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-data-contract-target cargo test --bin ict-engine load_analyze_slot_candles_wraps_missing_file_with_flag_schema_and_recovery -- --nocapture`
      failed with `cannot find function load_analyze_slot_candles`.
    - Fix: `analyze_command(...)` now loads the three primary frames through a
      slot-aware helper that names the failing flag/path, expected cleaned
      candle JSON/CSV fields/columns, and recovery paths: `--demo`, all three
      `--data-htf/--data-mtf/--data-ltf` flags, or `--data-root`.
    - Added RED coverage for `factor-research --data` handoff notes when the
      requested data file is missing even if the Auto-Quant workspace has
      unrelated prepared feathers.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-factor-research-data-contract-target cargo test handoff_notes_name_missing_requested_data_schema_and_prepare_recovery -- --nocapture`
      failed because notes only reported
      `auto_quant_prepare_required_before_run` and omitted the missing path,
      candle schema, and prepare command.
    - Fix: Auto-Quant handoff builders now add missing requested `--data` and
      `--paired-data` notes with path, cleaned candle JSON/CSV schema, and
      `ict-engine auto-quant-prepare --state-dir ...` recovery.
    - Added RED/GREEN renderer coverage so `factor-research --human` exposes the
      missing-data notes through a redacted `Notes:` line instead of hiding them
      in structured payload only.
    - Focused GREEN:
      `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-data-contract-target cargo test --bin ict-engine load_analyze_slot_candles_wraps_missing_file_with_flag_schema_and_recovery -- --nocapture`
      -> `1 passed; 0 failed`.
    - Focused GREEN:
      `CARGO_TARGET_DIR=/tmp/ict-engine-factor-research-data-contract-target cargo test --lib handoff -- --nocapture`
      -> `22 passed; 0 failed`.
    - Scoped static checks passed:
      `rustfmt --edition 2021 --check src/analyze_command.rs src/application/auto_quant/handoff.rs src/application/auto_quant/command_entry.rs`
      and
      `git diff --check -- src/analyze_command.rs src/application/auto_quant/handoff.rs src/application/auto_quant/command_entry.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`.
  - Smoke acceptance repo-local state guard continuation on 2026-05-22:
    - Added RED coverage in `support/scripts/tests/test_smoke_acceptance.py`
      proving `STATE_DIR=state` reached fake Cargo instead of failing in
      preflight.
    - RED:
      `python3 -m unittest support/scripts/tests/test_smoke_acceptance.py`
      failed with return code mismatch `42 != 2`, proving no repo-local state
      refusal existed before Cargo.
    - Fix: `support/scripts/smoke_acceptance.sh` now resolves `STATE_DIR`
      against the repo root and refuses repo-local state unless
      `ICT_ENGINE_ALLOW_REPO_STATE=1`.
    - Added boundary coverage proving `/tmp` state is allowed and repo-local
      state is allowed only with the explicit override.
    - GREEN:
      `python3 -m unittest support/scripts/tests/test_smoke_acceptance.py`
      -> `3 tests OK`.
    - Regression bundle:
      `bash -n support/scripts/smoke_acceptance.sh`,
      `python3 -m py_compile support/scripts/tests/test_smoke_acceptance.py`,
      and
      `python3 -m unittest support/scripts/tests/test_smoke_acceptance.py support/scripts/tests/test_public_wrappers.py`
      -> `7 tests OK`.
    - Manual preflight probe:
      `STATE_DIR=state OUT_DIR=/tmp/ict-engine-smoke-state-guard-manual-out bash support/scripts/smoke_acceptance.sh`
      exited `2` with
      `refusing repo-local STATE_DIR 'state' ... use /tmp/... or set ICT_ENGINE_ALLOW_REPO_STATE=1`.
    - `rg` found smoke acceptance references in contributor/consumer docs, but
      not in `README.md`; the README command checklist item remains open.
  - README smoke command continuation on 2026-05-22:
    - Added `bash support/scripts/smoke_acceptance.sh` to the README first-run
      section.
    - Added a README note that the script defaults to `/tmp/...` state and
      refuses repo-local `STATE_DIR` unless `ICT_ENGINE_ALLOW_REPO_STATE=1`.
    - This closes the README command pointer only; optional/full smoke checks
      remain open.
  - Optional/full smoke contract probe on 2026-05-22:
    - Re-read `support/scripts/smoke_acceptance.sh`, `support/docs/smoke-acceptance.md`,
      README, script manifest, and live CLI help before adding any full mode.
    - `cargo run --quiet -- factor-research --help` says public factor
      iteration is locked to Auto-Quant and `--backend` should be omitted or set
      to `auto-quant`.
    - Probe:
      `cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --objective generic --state-dir /tmp/ict-engine-full-smoke-probe-native-20260522a --backend native --human`
      exited `1` with
      `factor-research public factor iteration is locked to Auto-Quant`.
    - Probe:
      `cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --objective generic --state-dir /tmp/ict-engine-full-smoke-probe-20260522a --human`
      reached Auto-Quant dependency acquisition and exited `1` because this
      host rewrites GitHub HTTPS to SSH and the clone to
      `TraderAlice/Auto-Quant.git` failed at `198.18.0.21 port 22`.
    - `git config --global --get-regexp '^url\\..*\\.insteadOf$'` confirmed
      the host rewrite rule `url.git@github.com:.insteadof https://github.com/`.
    - `export-structural-path-ranking-target --human` and
      `policy-training-status --human` both run after a demo analyze under
      isolated `/tmp` state.
    - Decision: do not add a full smoke mode in this slice. The current fast
      script remains the verified consumer/no-network gate; a fuller Auto-Quant
      gate needs an explicit dependency strategy or pre-seeded workspace before
      it can be non-flaky.
  - Consumer quickstart verification continuation on 2026-05-22:
    - Re-read `support/docs/consumer-quickstart.md` and ran the documented
      runnable commands with `/tmp` state.
    - Flow 1 demo loop:
      `cargo run --quiet -- provider-status --compact`,
      `workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --human`,
      `analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human`,
      post-analyze
      `workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent`,
      `pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json`,
      and
      `policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent`
      all exited `0`.
    - Initial parallel Flow 1 readbacks raced ahead of `analyze --demo` and
      returned `no_workflow_state`; the post-analyze sequential rerun returned
      `active_regime=trend`, posterior probabilities, `gate_status=pass_hard`,
      and policy-training pending surfaces.
    - Smoke acceptance invocation was verified both as
      `bash support/scripts/smoke_acceptance.sh` with explicit `/tmp` state and
      as direct executable `support/scripts/smoke_acceptance.sh`; both exited
      `0` and passed the private-output scan.
    - Flow 2 provider readiness:
      `provider-status --domain live_runtime --agent` exited `0` with
      `live_runtime:3/5 ready`, and
      `provider-status --domain market_data --agent` exited `0` with
      `market_data:9/9 ready`.
    - Flow 2 live NQ:
      a 45-second bounded run of
      `cargo run --quiet -- analyze-live --symbol NQ --state-dir /tmp/ict-engine-live-nq --human`
      exited `0`, wrote `/tmp/ict-engine-live-nq/NQ/analyze_live_*.json`
      artifacts, and returned an observe-only readback plus a user-selection
      prompt for future historical-data reuse.
    - Flow 3 local cleaned data:
      populated `/tmp/my-data/{1d,1h,15m}.json` from the bundled
      `support/examples/demo/demo-15m.json` fixture, then ran the documented
      `analyze --data-htf/--data-mtf/--data-ltf` command and the two documented
      `workflow-status` / `pre-bayes-status` readbacks. All exited `0` and
      returned inspectable posterior/next-step surfaces.
  - Scope note: this verifies the quickstart command surfaces. It does not
    prove trade readiness, Auto-Quant dependency readiness, or release
    readiness.
  - Status CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move the Clap argument payloads for
      `pre-bayes-status` and `provider-status` out of the inline `Commands`
      enum fields and into `src/status_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-args-target cargo test --bin ict-engine test_cli_status_commands_use_extracted_args -- --nocapture`
      failed before the patch with `E0164` because the test expected tuple
      variants while `Commands::PreBayesStatus` and `Commands::ProviderStatus`
      were still struct variants.
    - Fix: added `src/status_cli_args.rs` with `PreBayesStatusArgs` and
      `ProviderStatusArgs`, changed both `Commands` variants to tuple payloads,
      updated dispatch destructuring, and updated the existing
      `test_cli_pre_bayes_status_accepts_agent_alias` parser test to inspect
      `args.agent`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-args-target cargo test --bin ict-engine test_cli_status_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-args-target cargo test --bin ict-engine test_cli_pre_bayes_status_accepts_agent_alias -- --nocapture`
        -> `1 passed; 0 failed`.
      - `rustfmt --edition 2021 --check src/main.rs src/status_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/status_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
    - Line-count telemetry:
      - Slice start observed before this extraction: `src/main.rs` = 19,250
        lines.
      - After extraction: `src/main.rs` = 19,240 lines and
        `src/status_cli_args.rs` = 63 lines.
    - Scope note: this is a small parser/dispatch extraction batch only. It
      does not close the `<5,000` `main.rs` target or replace the broader full
      gate set before release/commit decisions.
  - Second status CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `policy-training-status` and
      `pre-bayes-diff` Clap argument payloads out of inline `Commands` enum
      fields and into `src/status_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-more-args-target cargo test --bin ict-engine test_cli_more_status_commands_use_extracted_args -- --nocapture`
      failed with `E0164` because the new test expected tuple payloads while
      `Commands::PolicyTrainingStatus` and `Commands::PreBayesDiff` were still
      struct variants.
    - Fix: added `PolicyTrainingStatusArgs` and `PreBayesDiffArgs`, changed
      both `Commands` variants to tuple payloads, updated dispatch
      destructuring, and updated the existing
      `test_cli_policy_training_status_accepts_agent_alias` parser test to
      assert `args.agent`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-more-args-target cargo test --bin ict-engine test_cli_more_status_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-more-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `21 passed; 0 failed`.
      - `rustfmt --edition 2021 --check src/main.rs src/status_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/status_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-status-cli-more-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
    - Line-count telemetry:
      - After this batch: `src/main.rs` = 19,243 lines and
        `src/status_cli_args.rs` = 111 lines.
      - The batch improves ownership by removing more inline Clap payloads from
        the monolithic enum, but the new parser regression means this specific
        batch is line-count neutral/slightly positive in `main.rs`.
    - Scope note: this remains a narrow parser/dispatch extraction. The plan is
      still open because `main.rs < 5,000`, full generated command-output
      matrix, non-empty production validation proof, and release-clean export
      evidence are not closed.
  - Structural path-ranker CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move the six structural path-ranking
      command payloads out of inline `Commands` enum fields and into new
      `src/structural_path_ranker_cli_args.rs`.
    - Commands covered:
      `register-structural-path-ranking-trainer-artifact`,
      `clear-structural-path-ranking-trainer-artifact`,
      `enable-structural-path-ranking-runtime`,
      `disable-structural-path-ranking-runtime`,
      `export-structural-path-ranking-target`, and
      `apply-structural-path-ranking-external-scores`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-structural-cli-args-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_use_extracted_args -- --nocapture`
      failed with six `E0164` errors because the new test expected tuple
      payloads while the six command variants were still struct variants.
    - Fix: added `src/structural_path_ranker_cli_args.rs` with the six payload
      structs, converted the six `Commands` variants to tuple payloads, updated
      dispatch destructuring, and updated the existing structural path-ranker
      output-alias parser test to inspect `args.human` / `args.output_format`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-structural-cli-args-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-structural-cli-args-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_accept_output_aliases -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-structural-cli-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `22 passed; 0 failed`.
      - `rustfmt --edition 2021 --check src/main.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-structural-cli-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
    - Line-count telemetry:
      - After this batch: `src/main.rs` = 19,269 lines,
        `src/status_cli_args.rs` = 111 lines, and
        `src/structural_path_ranker_cli_args.rs` = 131 lines.
      - Ownership improved by moving six payload definitions out of the
        monolithic enum, but the added parser regression is long enough that
        `main.rs` grew in this batch. Future extraction batches should prefer
        moving command bodies/helpers or consolidating parser-test structure so
        `main.rs` actually shrinks after tests.
    - Scope note: this is still a parser/dispatch extraction only. It does not
      prove release readiness, non-empty production validation, or full
      command-output matrix coverage.
  - CLI parser-test module extraction continuation on 2026-05-22:
    - Chosen repayment batch: move parser/output-format/recommended-command
      surface tests out of the large inline `#[cfg(test)] mod tests` in
      `src/main.rs` and into new `src/cli_surface_tests.rs`.
    - Fix: added `#[cfg(test)] mod cli_surface_tests;` at crate-root scope and
      moved 28 parser/surface tests plus their local `parse_cli_from` helper
      into the child module, leaving runtime/business tests in the existing
      inline test module.
    - Verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-cli-surface-tests-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `28 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-cli-surface-tests-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `22 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-cli-surface-tests-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this repayment batch after structural path-ranker args:
        `src/main.rs` = 19,269 lines.
      - After extraction: `src/main.rs` = 18,566 lines,
        `src/cli_surface_tests.rs` = 705 lines,
        `src/status_cli_args.rs` = 111 lines, and
        `src/structural_path_ranker_cli_args.rs` = 131 lines.
      - Net effect: `src/main.rs` is 703 lines smaller while preserving the
        focused parser coverage outside the monolithic entrypoint.
    - Scope note: this is a test-surface/module extraction, not a runtime
      behavior change. It does not close the `<5,000` target or release gates.
  - Workflow-status CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move the large `workflow-status` Clap
      argument payload out of inline `Commands` enum fields and into
      `src/status_cli_args.rs` as `WorkflowStatusArgs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-workflow-status-args-target cargo test --bin ict-engine test_cli_workflow_status_uses_extracted_args -- --nocapture`
      failed with `E0164` because the new test expected a tuple payload while
      `Commands::WorkflowStatus` was still a struct variant.
    - Fix: added `WorkflowStatusArgs`, changed `Commands::WorkflowStatus` to a
      tuple payload, updated dispatch destructuring, and updated the existing
      stable-flag parser test to inspect `args.stable`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-workflow-status-args-target cargo test --bin ict-engine test_cli_workflow_status -- --nocapture`
        -> `2 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-workflow-status-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `23 passed; 0 failed`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-workflow-status-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,566 lines.
      - After extraction: `src/main.rs` = 18,497 lines,
        `src/cli_surface_tests.rs` = 752 lines,
        `src/status_cli_args.rs` = 184 lines, and
        `src/structural_path_ranker_cli_args.rs` = 131 lines.
      - Net effect: `src/main.rs` is 69 lines smaller while preserving parser
        coverage and moving another high-traffic public command payload out of
        the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction, not a release or
      behavior-readiness claim.
  - Market-data/debug CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `market-data-harness` and
      `factor-pipeline-debug` Clap argument payloads out of inline `Commands`
      enum fields and into `src/market_data_cli_args.rs` /
      `src/research_debug_cli_args.rs`.
    - Inherited RED from the interrupted slice:
      `CARGO_TARGET_DIR=/tmp/ict-engine-market-debug-args-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture`
      failed with `E0164` because the new test expected tuple payloads while
      both command variants were still struct variants.
    - Fix: added module declarations/imports for the two new arg modules,
      changed `Commands::MarketDataHarness` and
      `Commands::FactorPipelineDebug` to tuple payloads, and updated dispatch
      destructuring while leaving the existing shell input construction intact.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-debug-args-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-debug-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `24 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-debug-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `30 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-debug-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,497 lines.
      - After extraction: `src/main.rs` = 18,431 lines,
        `src/cli_surface_tests.rs` = 841 lines,
        `src/status_cli_args.rs` = 184 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 47 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 66 lines smaller while preserving parser
        coverage and moving two more public command payloads out of the
        monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` `main.rs` target, full command-output matrix, non-empty
      production validation proof, or release-clean export evidence.
  - Market-data SOP CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `clean-futures`,
      `futures-sop`, and `expansion-sop` Clap argument payloads out of inline
      `Commands` enum fields and into `src/market_data_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-market-sop-args-target cargo test --bin ict-engine test_cli_market_data_sop_commands_use_extracted_args -- --nocapture`
      failed with three `E0164` errors because the new test expected tuple
      payloads while the three command variants were still struct variants.
    - Fix: added `CleanFuturesArgs`, `FuturesSopArgs`, and
      `ExpansionSopArgs`, changed the three `Commands` variants to tuple
      payloads, and updated dispatch destructuring while preserving the
      existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-sop-args-target cargo test --bin ict-engine test_cli_market_data_sop_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-sop-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `25 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-sop-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `31 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-market-sop-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,431 lines.
      - After extraction: `src/main.rs` = 18,384 lines,
        `src/cli_surface_tests.rs` = 920 lines,
        `src/status_cli_args.rs` = 184 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 47 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - Research/status CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `factor-mutation-status`,
      `factor-autoresearch-status`, `research-verdict`, and
      `evidence-quality-breakdown` Clap argument payloads out of inline
      `Commands` enum fields and into `src/status_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-research-status-args-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture`
      failed with four `E0164` errors because the new test expected tuple
      payloads while the four command variants were still struct variants.
    - Fix: added `FactorMutationStatusArgs`,
      `FactorAutoresearchStatusArgs`, `ResearchVerdictArgs`, and
      `EvidenceQualityBreakdownArgs`, changed the four `Commands` variants to
      tuple payloads, and updated dispatch destructuring while preserving the
      existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-status-args-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-status-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `26 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-status-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `32 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-status-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,384 lines.
      - After extraction: `src/main.rs` = 18,311 lines,
        `src/cli_surface_tests.rs` = 1,012 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 73 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - AutoQuant setup CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `auto-quant-status`,
      `auto-quant-futures-cost`, `auto-quant-bootstrap`, `auto-quant-update`,
      `auto-quant-prepare`, `auto-quant-adoption-review`, and
      `auto-quant-adoption-decision` Clap argument payloads out of inline
      `Commands` enum fields and into `src/auto_quant_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-setup-args-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture`
      failed with seven `E0164` errors because the new test expected tuple
      payloads while the seven AutoQuant setup command variants were still
      struct variants.
    - Fix: added `src/auto_quant_cli_args.rs` with
      `AutoQuantStatusArgs`, `AutoQuantFuturesCostArgs`,
      `AutoQuantBootstrapArgs`, `AutoQuantUpdateArgs`,
      `AutoQuantPrepareArgs`, `AutoQuantAdoptionReviewArgs`, and
      `AutoQuantAdoptionDecisionArgs`, changed the seven `Commands` variants
      to tuple payloads, and updated dispatch destructuring while preserving
      the existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-setup-args-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-setup-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `27 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-setup-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `33 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-setup-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 41.09s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,311 lines.
      - After extraction: `src/main.rs` = 18,189 lines,
        `src/cli_surface_tests.rs` = 1,165 lines,
        `src/auto_quant_cli_args.rs` = 151 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 122 lines smaller while parser coverage
        is still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - AutoQuant seed/agent-material CLI args extraction continuation on
    2026-05-22:
    - Chosen low-risk extraction batch: move `auto-quant-seed-evidence`,
      `auto-quant-agent-material-batch`,
      `auto-quant-agent-material-dispatch`, and
      `auto-quant-agent-material-rank` Clap argument payloads out of inline
      `Commands` enum fields and into `src/auto_quant_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-agent-args-target cargo test --bin ict-engine test_cli_auto_quant_agent_material_commands_use_extracted_args -- --nocapture`
      failed with four `E0164` errors because the new test expected tuple
      payloads while the four command variants were still struct variants.
    - Fix: added `AutoQuantSeedEvidenceArgs`,
      `AutoQuantAgentMaterialBatchArgs`,
      `AutoQuantAgentMaterialDispatchArgs`, and
      `AutoQuantAgentMaterialRankArgs`, changed the four `Commands` variants
      to tuple payloads, and updated dispatch destructuring while preserving
      the existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-agent-args-target cargo test --bin ict-engine test_cli_auto_quant_agent_material_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-agent-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `28 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-agent-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `34 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-agent-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 36.74s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,189 lines.
      - After extraction: `src/main.rs` = 18,115 lines,
        `src/cli_surface_tests.rs` = 1,268 lines,
        `src/auto_quant_cli_args.rs` = 240 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 74 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - AutoQuant result/prior/live/trade CLI args extraction continuation on
    2026-05-22:
    - Chosen low-risk extraction batch: move `auto-quant-results-import`,
      `auto-quant-prior-init`, `auto-quant-consume-live-signals`, and
      `auto-quant-ingest-real-trades` Clap argument payloads out of inline
      `Commands` enum fields and into `src/auto_quant_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-result-args-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture`
      failed with four `E0164` errors because the new test expected tuple
      payloads while the four command variants were still struct variants.
    - Fix: added `AutoQuantResultsImportArgs`, `AutoQuantPriorInitArgs`,
      `AutoQuantConsumeLiveSignalsArgs`, and
      `AutoQuantIngestRealTradesArgs`, changed the four `Commands` variants
      to tuple payloads, and updated dispatch destructuring while preserving
      the existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-result-args-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-result-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `29 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-result-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `35 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-result-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 57.94s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 18,115 lines.
      - After extraction: `src/main.rs` = 17,985 lines,
        `src/cli_surface_tests.rs` = 1,389 lines,
        `src/auto_quant_cli_args.rs` = 383 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 130 lines smaller while parser coverage
        is still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - AutoQuant PDA unit CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `auto-quant-pda-unit-batch` and
      `auto-quant-pda-unit-dispatch` Clap argument payloads out of inline
      `Commands` enum fields and into `src/auto_quant_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-pda-args-target cargo test --bin ict-engine test_cli_auto_quant_pda_unit_commands_use_extracted_args -- --nocapture`
      failed with two `E0164` errors because the new test expected tuple
      payloads while the two PDA unit command variants were still struct
      variants.
    - Fix: added `AutoQuantPdaUnitBatchArgs` and
      `AutoQuantPdaUnitDispatchArgs`, changed the two `Commands` variants to
      tuple payloads, and updated dispatch destructuring while preserving the
      existing shell call boundaries.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-pda-args-target cargo test --bin ict-engine test_cli_auto_quant_pda_unit_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-pda-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `30 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-pda-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-pda-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 42.35s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,985 lines.
      - After extraction: `src/main.rs` = 17,890 lines,
        `src/cli_surface_tests.rs` = 1,487 lines,
        `src/auto_quant_cli_args.rs` = 485 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 95 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - AutoQuant promote-canonical-setup CLI args extraction continuation on
    2026-05-22:
    - Chosen low-risk extraction batch: move
      `auto-quant-promote-canonical-setup` Clap argument payload out of the
      inline `Commands` enum field and into `src/auto_quant_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-promote-args-target cargo test --bin ict-engine test_cli_auto_quant_promote_canonical_setup_uses_extracted_args -- --nocapture`
      failed with one `E0164` error because the new test expected a tuple
      payload while the command variant was still a struct variant.
    - Fix: added `AutoQuantPromoteCanonicalSetupArgs`, changed the
      `Commands::AutoQuantPromoteCanonicalSetup` variant to a tuple payload,
      and updated dispatch destructuring while preserving the existing
      `PromoteCanonicalSetupCommandInput` shell boundary.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-promote-args-target cargo test --bin ict-engine test_cli_auto_quant_promote_canonical_setup_uses_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-promote-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `31 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-promote-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `37 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-auto-quant-promote-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 47.40s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,890 lines.
      - After extraction: `src/main.rs` = 17,857 lines,
        `src/cli_surface_tests.rs` = 1,525 lines,
        `src/auto_quant_cli_args.rs` = 521 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 33 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - Factor asset CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `factor-candidate-packs`,
      `factor-candidate-admission-targets`, `regime-confidence-assets`, and
      `factor-asset-closure-intake` Clap argument payloads out of inline
      `Commands` enum fields and into new `src/factor_asset_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-factor-asset-args-target cargo test --bin ict-engine test_cli_factor_asset_commands_use_extracted_args -- --nocapture`
      failed with four `E0164` errors because the new test expected tuple
      payloads while the four command variants were still struct variants.
    - Fix: added `FactorCandidatePacksArgs`,
      `FactorCandidateAdmissionTargetsArgs`, `RegimeConfidenceAssetsArgs`, and
      `FactorAssetClosureIntakeArgs`, changed the four `Commands` variants to
      tuple payloads, updated dispatch destructuring, and refreshed the older
      parser tests that previously matched inline fields.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-asset-args-target cargo test --bin ict-engine test_cli_factor_asset_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-asset-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `32 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-asset-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `38 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-asset-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 1m 01s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/factor_asset_cli_args.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/factor_asset_cli_args.rs src/auto_quant_cli_args.rs src/status_cli_args.rs src/structural_path_ranker_cli_args.rs src/market_data_cli_args.rs src/research_debug_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,857 lines.
      - After extraction: `src/main.rs` = 17,777 lines,
        `src/cli_surface_tests.rs` = 1,630 lines,
        `src/factor_asset_cli_args.rs` = 98 lines,
        `src/auto_quant_cli_args.rs` = 521 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 80 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, or release-clean export evidence.
  - Core runtime CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `validate-market-state`, `train`,
      and `update` Clap argument payloads out of inline `Commands` enum fields
      and into new `src/core_runtime_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-core-runtime-args-target cargo test --bin ict-engine test_cli_core_runtime_commands_use_extracted_args -- --nocapture`
      failed with three `E0164` errors because the new test expected tuple
      payloads while `ValidateMarketState`, `Train`, and `Update` were still
      struct variants.
    - Fix: added `ValidateMarketStateArgs`, `TrainArgs`, and `UpdateArgs`,
      changed the three `Commands` variants to tuple payloads, updated dispatch
      destructuring, and refreshed the existing validate-market-state parser
      tests to match the extracted tuple payload.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-core-runtime-args-target cargo test --bin ict-engine test_cli_core_runtime_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-core-runtime-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `33 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-core-runtime-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `39 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-core-runtime-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 1m 21s.
      - `rustfmt --edition 2021 src/main.rs src/cli_surface_tests.rs src/core_runtime_cli_args.rs`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,777 lines.
      - After extraction: `src/main.rs` = 17,694 lines,
        `src/cli_surface_tests.rs` = 1,716 lines,
        `src/core_runtime_cli_args.rs` = 95 lines,
        `src/factor_asset_cli_args.rs` = 98 lines,
        `src/auto_quant_cli_args.rs` = 521 lines,
        `src/status_cli_args.rs` = 270 lines,
        `src/structural_path_ranker_cli_args.rs` = 131 lines,
        `src/market_data_cli_args.rs` = 105 lines, and
        `src/research_debug_cli_args.rs` = 31 lines.
      - Net effect: `src/main.rs` is 83 lines smaller while the core runtime
        parser coverage remains outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, release-clean export evidence, or full dirty-tree
      completion.
  - Backtest CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move the `backtest` Clap argument
      payload out of inline `Commands` enum fields and into
      `src/core_runtime_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-backtest-args-target cargo test --bin ict-engine test_cli_backtest_uses_extracted_args -- --nocapture`
      failed with one `E0164` error because the new test expected a tuple
      payload while `Commands::Backtest` was still a struct variant.
    - Fix: added `BacktestArgs`, changed `Commands::Backtest` to a tuple
      payload, updated dispatch destructuring, and refreshed the existing
      human-output-alias parser test to match the extracted payload.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-backtest-args-target cargo test --bin ict-engine test_cli_backtest_uses_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-backtest-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `34 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-backtest-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `40 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-backtest-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 46.00s.
      - `rustfmt --edition 2021 src/main.rs src/cli_surface_tests.rs src/core_runtime_cli_args.rs`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,694 lines.
      - After extraction: `src/main.rs` = 17,642 lines,
        `src/cli_surface_tests.rs` = 1,766 lines, and
        `src/core_runtime_cli_args.rs` = 150 lines.
      - Net effect: `src/main.rs` is 52 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, release-clean export evidence, or full dirty-tree
      completion.
  - Research-loop CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `factor-research`,
      `factor-autoresearch`, and `factor-backtest` Clap argument payloads out
      of inline `Commands` enum fields and into new
      `src/research_loop_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-research-loop-args-target cargo test --bin ict-engine test_cli_research_loop_commands_use_extracted_args -- --nocapture`
      failed with three `E0164` errors because the new test expected tuple
      payloads while `Commands::FactorResearch`, `Commands::FactorAutoresearch`,
      and `Commands::FactorBacktest` were still struct variants.
    - Fix: added `FactorResearchArgs`, `FactorAutoresearchArgs`, and
      `FactorBacktestArgs`, changed the three `Commands` variants to tuple
      payloads, updated dispatch destructuring, and refreshed the older parser
      tests that matched inline fields.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-loop-args-target cargo test --bin ict-engine test_cli_research_loop_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-loop-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `35 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-loop-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `41 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-research-loop-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 52.33s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/research_loop_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/research_loop_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,642 lines.
      - After extraction: `src/main.rs` = 17,416 lines,
        `src/cli_surface_tests.rs` = 1,977 lines, and
        `src/research_loop_cli_args.rs` = 238 lines.
      - Net effect: `src/main.rs` is 226 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, release-clean export evidence, or full dirty-tree
      completion.
  - Analyze CLI args extraction continuation on 2026-05-22:
    - Chosen low-risk extraction batch: move `analyze` and `analyze-live`
      Clap argument payloads out of inline `Commands` enum fields and into new
      `src/analyze_cli_args.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-cli-args-target cargo test --bin ict-engine test_cli_analyze_commands_use_extracted_args -- --nocapture`
      failed with two `E0164` errors because the new test expected tuple
      payloads while `Commands::Analyze` and `Commands::AnalyzeLive` were still
      struct variants.
    - Fix: added `AnalyzeArgs` and `AnalyzeLiveArgs`, changed the two
      `Commands` variants to tuple payloads, updated dispatch destructuring,
      and refreshed the existing parser test that matched inline analyze
      fields.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-cli-args-target cargo test --bin ict-engine test_cli_analyze_commands_use_extracted_args -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-cli-args-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-cli-args-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `42 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-cli-args-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 40.46s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/analyze_cli_args.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/analyze_cli_args.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "Commands::Analyze \\{|Commands::AnalyzeLive \\{" src/main.rs src/cli_surface_tests.rs src/analyze_cli_args.rs`
        found no stale inline struct-pattern matches.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,416 lines.
      - After extraction: `src/main.rs` = 17,270 lines,
        `src/cli_surface_tests.rs` = 2,085 lines, and
        `src/analyze_cli_args.rs` = 155 lines.
      - Net effect: `src/main.rs` is 146 lines smaller while parser coverage is
        still outside the monolithic entrypoint.
    - Scope note: this is still a parser/dispatch extraction. It does not close
      the `<5,000` target, full command-output matrix, non-empty production
      validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Owner-module runtime input DTO extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move `UpdateCommandInput` into
      `src/update_command.rs` and `RunProbabilisticBacktestInput` into
      `src/probabilistic_backtest_runtime.rs` so the runtime command modules own
      the DTOs they consume instead of depending on private `main.rs` root
      definitions through `use super::*`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-owner-input-target cargo test --bin ict-engine test_runtime_command_input_types_live_with_owner_modules -- --nocapture`
      failed with two expected `E0603` errors because
      `crate::update_command::UpdateCommandInput` and
      `crate::probabilistic_backtest_runtime::RunProbabilisticBacktestInput`
      were still private imports referring back to structs defined in
      `src/main.rs`.
    - Fix: moved `UpdateCommandInput` and `RunProbabilisticBacktestInput` into
      their owner modules, made the DTOs/fields `pub(crate)`, and changed
      `main.rs` to import the types from those modules.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-owner-input-target cargo test --bin ict-engine test_runtime_command_input_types_live_with_owner_modules -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-owner-input-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-owner-input-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `43 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-owner-input-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 1m 44s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/update_command.rs src/probabilistic_backtest_runtime.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/update_command.rs src/probabilistic_backtest_runtime.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "^struct (RunProbabilisticBacktestInput|UpdateCommandInput)|RunProbabilisticBacktestInput|UpdateCommandInput" src/main.rs src/update_command.rs src/probabilistic_backtest_runtime.rs src/cli_surface_tests.rs`
        showed the struct definitions now live only in the owner modules; `main.rs`
        only imports/constructs the owner-module types.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,270 lines.
      - After extraction: `src/main.rs` = 17,246 lines,
        `src/cli_surface_tests.rs` = 2,097 lines,
        `src/update_command.rs` = 1,072 lines, and
        `src/probabilistic_backtest_runtime.rs` = 446 lines.
      - Net effect: `src/main.rs` is 24 lines smaller and two runtime DTO
        ownership boundaries are now explicit outside the monolithic entrypoint.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Output-format owner module extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move the cross-cutting `OutputFormat`
      enum and `resolve_output_format` alias/default resolver out of
      `src/main.rs` and into new `src/output_format.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-target cargo test --bin ict-engine test_output_format_types_live_in_owner_module -- --nocapture`
      failed with two expected `E0433` errors because `crate::output_format`
      did not exist while `OutputFormat` and `resolve_output_format` were still
      root-level `main.rs` definitions.
    - Fix: added `src/output_format.rs`, made `OutputFormat` and
      `resolve_output_format` `pub(crate)`, removed the root definitions from
      `main.rs`, and imported the owner-module items at the binary root so
      existing command modules keep their current `use super::*` access path.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-target cargo test --bin ict-engine test_output_format_types_live_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `44 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 43.16s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/output_format.rs src/update_command.rs src/probabilistic_backtest_runtime.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/output_format.rs src/update_command.rs src/probabilistic_backtest_runtime.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "^enum OutputFormat|^fn resolve_output_format|OutputFormat|resolve_output_format" src/main.rs src/output_format.rs src/cli_surface_tests.rs src/analyze_command.rs src/factor_research_command.rs`
        showed the enum/resolver definitions now live only in
        `src/output_format.rs`; `main.rs` imports them and existing callers use
        the same resolved types.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,246 lines.
      - After extraction: `src/main.rs` = 17,197 lines,
        `src/cli_surface_tests.rs` = 2,103 lines, and
        `src/output_format.rs` = 52 lines.
      - Net effect: `src/main.rs` is 49 lines smaller and the shared
        output-format contract now has an explicit owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - State-dir owner module extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move the shared state-dir constants and
      readiness helper out of `src/main.rs` and into new `src/state_dir.rs`.
      The binary root still imports the owner-module items so existing command
      modules keep their current `use super::*` access path.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-state-dir-target cargo test --bin ict-engine test_state_dir_helpers_live_in_owner_module -- --nocapture`
      failed with three expected `E0433` errors because `crate::state_dir` did
      not exist while `DEFAULT_STATE_DIR`, `STATE_DIR_ENV_VAR`, and
      `ensure_state_dir_ready` were still root-level `main.rs` definitions.
    - Fix: added `src/state_dir.rs`, moved `DEFAULT_STATE_DIR`,
      `STATE_DIR_ENV_VAR`, the internal default-state-dir warning predicate,
      and `ensure_state_dir_ready` into that module, made the public contract
      `pub(crate)`, and imported the items at the binary root.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-state-dir-target cargo test --bin ict-engine test_state_dir_helpers_live_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-state-dir-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-state-dir-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `45 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-state-dir-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 45.63s.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/state_dir.rs src/output_format.rs src/update_command.rs src/probabilistic_backtest_runtime.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/state_dir.rs src/output_format.rs src/update_command.rs src/probabilistic_backtest_runtime.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "^const (DEFAULT_STATE_DIR|STATE_DIR_ENV_VAR)|^fn should_warn_about_default_state_dir|^fn ensure_state_dir_ready|DEFAULT_STATE_DIR|STATE_DIR_ENV_VAR|ensure_state_dir_ready" src/main.rs src/state_dir.rs src/cli_surface_tests.rs src/analyze_live_command.rs src/auto_quant_command.rs src/factor_research_command.rs src/policy_training_command.rs src/research_debug_command.rs src/update_command.rs`
        showed the constants/helper definitions now live in `src/state_dir.rs`;
        `main.rs` only imports/uses them and command modules retain the same
        root-scope call path.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,197 lines.
      - After extraction: `src/main.rs` = 17,171 lines,
        `src/cli_surface_tests.rs` = 2,113 lines, and
        `src/state_dir.rs` = 31 lines.
      - Net effect: `src/main.rs` is 26 lines smaller and the shared state-dir
        contract now has an explicit owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Env command owner module extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move `build_env_report()` and
      `env_command()` out of `src/main.rs` and into new
      `src/env_command.rs`. `Commands::Env` now dispatches through the owner
      module while the env report schema remains unchanged.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo test --bin ict-engine test_env_report_helpers_live_in_owner_module -- --nocapture`
      failed with expected `E0433` because `crate::env_command` did not exist.
    - Intermediate GREEN catch:
      after adding `src/env_command.rs`, the same focused test found one stale
      old test call in `src/main.rs` (`E0425` for `build_env_report`), which
      was corrected to call `crate::env_command::build_env_report()`.
    - Fix: added `src/env_command.rs`, moved the env report builder and shell
      command there, imported Auto-Quant env-var constants from the existing
      `ict_engine::application::auto_quant` owner module, removed stale
      root-local Auto-Quant env constants, and kept `main.rs` as dispatch only.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo test --bin ict-engine test_env_report_helpers_live_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo test --bin ict-engine 'env_report' -- --nocapture`
        -> `2 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `46 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-env-command-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 1.90s after warning cleanup.
      - `rustfmt --edition 2021 --check src/main.rs src/env_command.rs src/cli_surface_tests.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/env_command.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn build_env_report\\(|fn env_command\\(|build_env_report\\(|Commands::Env" src/main.rs src/env_command.rs src/cli_surface_tests.rs`
        showed the helper definitions now live only in `src/env_command.rs`;
        `main.rs` only dispatches and the existing bin-harness test calls the
        owner module.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,171 lines.
      - After extraction: `src/main.rs` = 17,108 lines,
        `src/env_command.rs` = 75 lines, and
        `src/cli_surface_tests.rs` = 2,131 lines.
      - Net effect: `src/main.rs` is 63 lines smaller and the env-report shell
        boundary now has an explicit owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Auto-Quant output-dir helper owner extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move
      `AUTO_QUANT_OUTPUT_DIR_ENV_VAR`, `DEFAULT_AUTO_QUANT_SUBDIR`, and
      `resolve_auto_quant_output_dir(...)` out of `src/main.rs` and into
      `src/auto_quant_command.rs`, where the Auto-Quant shell routing already
      owns output-dir isolation and existing `aq_state_dir` behavior.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine test_auto_quant_output_dir_helpers_live_in_owner_module -- --nocapture`
      failed with two expected `E0603` errors because
      `crate::auto_quant_command::DEFAULT_AUTO_QUANT_SUBDIR` and
      `crate::auto_quant_command::resolve_auto_quant_output_dir(...)` were
      still private imports of root-level `main.rs` definitions.
    - Fix: added the constants and resolver to `src/auto_quant_command.rs`,
      removed the duplicate root definitions from `src/main.rs`, and changed
      `src/env_command.rs` to name `ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR` through
      the Auto-Quant command owner module instead of a string literal.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine test_auto_quant_output_dir_helpers_live_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine aq_state_dir -- --nocapture`
        -> `5 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine env_report -- --nocapture`
        -> `2 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `47 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-output-dir-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 37.37s.
      - `rustfmt --edition 2021 --check src/main.rs src/auto_quant_command.rs src/env_command.rs src/cli_surface_tests.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/auto_quant_command.rs src/env_command.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "AUTO_QUANT_OUTPUT_DIR_ENV_VAR|DEFAULT_AUTO_QUANT_SUBDIR|resolve_auto_quant_output_dir" src/main.rs src/auto_quant_command.rs src/env_command.rs src/cli_surface_tests.rs`
        showed the definitions now live only in `src/auto_quant_command.rs`;
        `src/env_command.rs` imports the env-var constant from that owner and
        `src/main.rs` has no stale root definitions.
      - One attempted combined Cargo filter
        `'auto_quant_output_dir|aq_state_dir|env_report'` matched zero tests
        and is not counted as evidence; the separate filters above are the
        counted verification.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,108 lines.
      - After extraction: `src/main.rs` = 17,093 lines,
        `src/auto_quant_command.rs` = 412 lines,
        `src/env_command.rs` = 76 lines, and
        `src/cli_surface_tests.rs` = 2,143 lines.
      - Net effect: `src/main.rs` is 15 lines smaller and the Auto-Quant
        output-dir isolation helper now has an explicit owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Analyze output adapter owner extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move the binary-local
      `emit_analyze_output(report, OutputFormat, inline_ledger)` adapter out of
      `src/main.rs` and into `src/analyze_command.rs`, where the explicit
      analyze command already owns the call boundary. The library reporting
      dispatcher remains the output renderer.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo test --bin ict-engine test_emit_analyze_output_adapter_lives_in_analyze_command_module -- --nocapture`
      failed with expected `E0603` because
      `crate::analyze_command::emit_analyze_output` was still only a private
      import of the root-level `src/main.rs` helper.
    - Fix: added `pub(crate) fn emit_analyze_output(...)` to
      `src/analyze_command.rs`, preserved the exact `OutputFormat` to
      reporting string mapping, kept dispatch through
      `ict_engine::application::reporting::dispatch_analyze_output(...)`, and
      removed the root-level helper from `src/main.rs`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo test --bin ict-engine test_emit_analyze_output_adapter_lives_in_analyze_command_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo test --bin ict-engine analyze_command -- --nocapture`
        -> `13 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `48 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-analyze-output-adapter-target cargo check --bin ict-engine`
        exited `0` with `Finished dev profile` in 1m 02s.
      - `rustfmt --edition 2021 --check src/main.rs src/analyze_command.rs src/cli_surface_tests.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/analyze_command.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn emit_analyze_output\\(|emit_analyze_output\\(|dispatch_analyze_output|AnalyzeOutputDispatchInput" src/main.rs src/analyze_command.rs src/application/reporting/analyze_output.rs src/cli_surface_tests.rs`
        showed the binary adapter definition now lives only in
        `src/analyze_command.rs`; `src/main.rs` has no stale root helper, and
        the existing library reporting API remains under
        `src/application/reporting/analyze_output.rs`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,093 lines.
      - After extraction: `src/main.rs` = 17,073 lines,
        `src/analyze_command.rs` = 737 lines, and
        `src/cli_surface_tests.rs` = 2,157 lines.
      - Net effect: `src/main.rs` is 20 lines smaller and the analyze output
        adapter now has an explicit command owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Output-format label owner extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: add an agent-preserving
      `output_format_label(OutputFormat) -> &'static str` helper to
      `src/output_format.rs`, then replace duplicated root dispatch matches
      that map `OutputFormat::Agent` to `"agent"`. The existing branches that
      intentionally map `OutputFormat::Agent` to `"json"` remain explicit in
      `src/main.rs`.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine test_output_format_agent_preserving_label_lives_in_owner_module -- --nocapture`
      failed with expected `E0425` because
      `crate::output_format::output_format_label(...)` did not exist yet.
      The same compile also emitted unrelated library dead-code warnings from
      `src/application/orchestration/structural_playbook.rs`; they were not the
      failure cause.
    - Fix: added `output_format_label(...)` in `src/output_format.rs`, changed
      `src/analyze_command.rs` and `src/factor_research_command.rs` to use the
      owner helper, and replaced the agent-preserving output-format string
      matches in `src/main.rs` with `output_format_label(resolve_output_format(...))`.
      The Auto-Quant/pre-Bayes branches that preserve `--agent` as JSON output
      still use their local explicit match.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine test_output_format_agent_preserving_label_lives_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine output_format -- --nocapture`
        -> `11 passed; 0 failed` before formatting, then `11 passed; 0 failed`
        again after formatting.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed` before formatting, then `36 passed; 0 failed`
        again after formatting.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `49 passed; 0 failed` before formatting, then `49 passed; 0 failed`
        again after formatting.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine analyze_command -- --nocapture`
        -> `13 passed; 0 failed` before formatting, then `13 passed; 0 failed`
        again after formatting.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo test --bin ict-engine factor_research -- --nocapture`
        -> `13 passed; 0 failed` before formatting, then `13 passed; 0 failed`
        again after formatting.
      - `rustfmt --edition 2021 --check src/main.rs src/output_format.rs src/analyze_command.rs src/factor_research_command.rs src/cli_surface_tests.rs`
        first found three line-wrap diffs in `src/main.rs`; after running
        `rustfmt --edition 2021` on those touched files, the same check exited
        `0`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-output-format-label-target cargo check --bin ict-engine`
        exited `0` before formatting with `Finished dev profile` in 1m 18s,
        then exited `0` again after formatting with `Finished dev profile` in
        2.90s.
      - `git diff --check -- src/main.rs src/output_format.rs src/analyze_command.rs src/factor_research_command.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n -C 2 "OutputFormat::Agent => \"agent\"|OutputFormat::Agent => \"json\"|output_format_label" src/main.rs src/output_format.rs src/analyze_command.rs src/factor_research_command.rs src/cli_surface_tests.rs`
        showed no remaining `OutputFormat::Agent => "agent"` branch outside
        `src/output_format.rs`; three `OutputFormat::Agent => "json"` branches
        remain explicit in `src/main.rs`.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,073 lines.
      - After extraction and rustfmt: `src/main.rs` = 17,068 lines,
        `src/output_format.rs` = 61 lines, `src/analyze_command.rs` = 732
        lines, `src/factor_research_command.rs` = 338 lines, and
        `src/cli_surface_tests.rs` = 2,169 lines.
      - Net effect: `src/main.rs` is 5 lines smaller and the
        agent-preserving output-format label mapping now has an explicit owner
        helper.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Auto-Quant futures-cost shell owner extraction continuation on 2026-05-22:
    - Chosen low-risk ownership batch: move
      `auto_quant_futures_cost_shell(...)` and its private
      `futures_root_for_error(...)` helper out of `src/main.rs` and into
      `src/auto_quant_command.rs`, where the adjacent Auto-Quant shell routing
      already lives.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo test --bin ict-engine test_auto_quant_futures_cost_shell_lives_in_owner_module -- --nocapture`
      failed with expected `E0603` because
      `crate::auto_quant_command::auto_quant_futures_cost_shell` was still
      only a private import of the root-level `src/main.rs` helper.
    - Fix: added `pub(crate) fn auto_quant_futures_cost_shell(...)` and
      private `futures_root_for_error(...)` to `src/auto_quant_command.rs`,
      imported `FuturesCostCatalog` there, removed the root-level helper block
      from `src/main.rs`, and kept the CLI dispatch calling the same shell
      name through the Auto-Quant command owner module.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo test --bin ict-engine test_auto_quant_futures_cost_shell_lives_in_owner_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo test --bin ict-engine auto_quant_setup -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo test --bin ict-engine test_cli -- --nocapture`
        -> `36 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `50 passed; 0 failed` before formatting, then `50 passed; 0 failed`
        again after formatting.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo run --quiet -- auto-quant-futures-cost --symbol NQ --price 17000 --compact`
        exited `0` and printed `symbol=NQ profile=CME_NQ_default_v1
        price=17000 round_trip_cost_pct=0.004365
        round_trip_cost_points=0.742000 ... fixed_bps_is_diagnostic_only`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-aq-futures-cost-target cargo check --bin ict-engine`
        exited `0` before formatting with `Finished dev profile` in 1m 06s,
        then exited `0` again after formatting with `Finished dev profile` in
        20.61s.
      - One attempted `rustfmt --edition 2021 --check ... support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        incorrectly included the Markdown plan file and is not counted as a
        valid rustfmt evidence command; it also found Rust line-wrap diffs.
      - After running `rustfmt --edition 2021 src/main.rs src/auto_quant_command.rs src/cli_surface_tests.rs`,
        the valid check
        `rustfmt --edition 2021 --check src/main.rs src/auto_quant_command.rs src/cli_surface_tests.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/auto_quant_command.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn auto_quant_futures_cost_shell\\(|auto_quant_futures_cost_shell\\(|fn futures_root_for_error\\(|FuturesCostCatalog" src/main.rs src/auto_quant_command.rs src/cli_surface_tests.rs`
        showed the shell definition, `FuturesCostCatalog` import, and
        `futures_root_for_error(...)` helper now live in
        `src/auto_quant_command.rs`; `src/main.rs` only dispatches to the
        owner shell.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 17,068 lines.
      - After extraction and rustfmt: `src/main.rs` = 16,988 lines,
        `src/auto_quant_command.rs` = 513 lines, and
        `src/cli_surface_tests.rs` = 2,176 lines.
      - Net effect: `src/main.rs` is 80 lines smaller and the futures-cost
        shell now has an explicit Auto-Quant command owner module.
    - Scope note: this is still an ownership/refactor extraction. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Error-message contract recheck on 2026-05-22:
    - Re-read the existing `analyze --data-*` and Auto-Quant
      `factor-research --data` missing-file test/code surfaces because the
      lower checklist still showed those items as open.
    - Real CLI probe:
      `CARGO_TARGET_DIR=/tmp/ict-engine-error-contract-probe-target cargo run --quiet -- analyze --symbol DEMO --data-htf /tmp/ict-engine-missing-htf.json --data-mtf support/examples/demo/demo-15m.json --data-ltf support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-error-contract-probe-analyze --human`
      exited `1` with a stable message naming `analyze --data-htf`, the
      missing path, cleaned candle JSON/CSV schema, `timestamp/open/high/low/close`,
      and recovery via demo, all three `--data-htf/--data-mtf/--data-ltf`
      flags, or `--data-root`.
    - Real CLI probe:
      `CARGO_TARGET_DIR=/tmp/ict-engine-error-contract-probe-target cargo run --quiet -- factor-research --symbol DEMO --data /tmp/ict-engine-missing-factor-research.json --objective generic --state-dir /tmp/ict-engine-error-contract-probe-factor --human`
      exited `0` with a human Auto-Quant handoff surface. Its `Notes:` line
      included `auto_quant_requested_data_missing`, `flag=--data`, the
      redacted missing path, cleaned candle JSON/CSV schema, and recovery
      `ict-engine auto-quant-prepare --state-dir <local-path>`.
    - Interpretation: the listed missing-file paths for apply-score,
      register-artifact, `analyze --data-*`, and public Auto-Quant
      `factor-research --data` now have focused test evidence plus live CLI
      process evidence for the two user-facing data-entry commands. This does
      not replace the broader generated command-output matrix.
  - Executor-summary formatter owner extraction continuation on 2026-05-22
    08:02 +0800:
    - Re-read live routing, repo instructions, this plan doc, and current
      dirty/process state before editing. The tree is still shared and dirty;
      this slice touched only `src/main.rs`, `src/cli_surface_tests.rs`, and
      this plan doc.
    - Candidate selected:
      `format_executor_summary_lines(...)` was already implemented in
      `src/application/output_foundation.rs`, while `src/main.rs` still carried
      a duplicate test-only helper.
    - RED:
      `cargo test --bin ict-engine test_executor_summary_formatter_lives_in_output_foundation_module -- --nocapture`
      failed as expected because `src/main.rs` still contained
      `fn format_executor_summary_lines(`.
    - Fix:
      removed the duplicate helper from `src/main.rs`, imported
      `ict_engine::application::output_foundation::format_executor_summary_lines`
      into the test module, and added the owner-boundary test in
      `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `cargo test --bin ict-engine test_executor_summary_formatter_lives_in_output_foundation_module -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_format_executor_summary_lines_clones_executor_summaries -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_emit_analyze_output_includes_executor_scorecard_summary -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_factor_research_output_summary_uses_executor_summaries -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `51 passed; 0 failed`.
      - `cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 15.40s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn format_executor_summary_lines\\(" src/main.rs src/application/output_foundation.rs src/cli_surface_tests.rs`
        now shows only the owner definition in
        `src/application/output_foundation.rs` plus the boundary-test string.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,988 lines.
      - After extraction: `src/main.rs` = 16,981 lines,
        `src/application/output_foundation.rs` = 239 lines, and
        `src/cli_surface_tests.rs` = 2,192 lines.
      - Net effect: `src/main.rs` is 7 lines smaller and the executor-summary
        formatter now has a single owner module.
    - Scope note: this does not close the `<5,000` target, full
      command-output matrix, non-empty production validation proof,
      manual/nightly Auto-Quant smoke design, release-clean export evidence, or
      full dirty-tree completion.
  - Executor scorecard source owner extraction continuation on 2026-05-22:
    - Re-read live worktree, process state, and this plan before editing. No
      Cargo/rustc process was active at the initial probe; later waits on the
      shared Cargo lock were caused by unrelated agent jobs and were not killed.
    - Candidate selected:
      `resolved_vote_scorecards(...)` still had a duplicate helper in
      `src/main.rs`, while `src/application/orchestration/workflow_status.rs`
      already exposed an owner helper used by workflow-status/backtest/update
      surfaces.
    - Semantic bug found before extraction:
      the owner helper returned hardcoded `"fallback"` when persisted scorecards
      were absent, while the old `main.rs` helper preserved
      `vote.executor_scorecards_source.unwrap_or("fallback")`.
    - RED:
      `cargo test --bin ict-engine test_resolved_vote_scorecards_lives_in_orchestration_and_preserves_vote_source -- --nocapture`
      failed with `left: "fallback" right: "vote_snapshot"`, proving the owner
      helper would lose source provenance before the duplicate could be removed.
    - Fix:
      - changed `ict_engine::application::orchestration::resolved_vote_scorecards`
        to return `(Vec<EnsembleExecutorScorecard>, String)` and preserve
        `vote.executor_scorecards_source` when using vote fallback scorecards;
      - removed the duplicate `resolved_vote_scorecards(...)` from
        `src/main.rs`;
      - updated `src/main.rs` tests and `src/update_output.rs` to import the
        orchestration owner helper explicitly;
      - added an owner-boundary test in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `cargo test --bin ict-engine test_resolved_vote_scorecards_lives_in_orchestration_and_preserves_vote_source -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_ensemble_vote_history_view_uses_resolved_scorecard_source -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_executor_scorecard_surface_marks_fallback_and_persisted -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `52 passed; 0 failed`.
      - `cargo test --bin ict-engine test_workflow_status_human_view_prefers_persisted_scorecards -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 0.33s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/workflow_status.rs src/update_output.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/workflow_status.rs src/update_output.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn resolved_vote_scorecards\\(|resolved_vote_scorecards\\(" src/main.rs src/cli_surface_tests.rs src/application/orchestration/workflow_status.rs src/update_output.rs src/application/backtest/command_entry.rs`
        shows the only definition is now in
        `src/application/orchestration/workflow_status.rs`; the remaining
        `main.rs` occurrence is a test-module call to the owner helper.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,981 lines.
      - After extraction: `src/main.rs` = 16,966 lines,
        `src/application/orchestration/workflow_status.rs` = 13,622 lines,
        `src/update_output.rs` = 351 lines, and
        `src/cli_surface_tests.rs` = 2,224 lines.
      - Net effect: `src/main.rs` is 15 lines smaller and executor-scorecard
        source provenance has one orchestration owner.
    - Scope note: this is still one verified bug/refactor slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Multi-timeframe phase hint owner extraction continuation on 2026-05-22:
    - Re-read live routing, repo instructions, current worktree, process state,
      and this plan before editing. A separate Auto-Quant/TOMAC process was
      active, so this slice avoided Board A/B/provider artifacts and touched
      only the helper owner boundary.
    - Candidate selected:
      `multi_timeframe_phase_hint(...)` was still a private helper in
      `src/main.rs`, while `src/workflow_snapshot_runtime.rs` used it through
      broad binary-root visibility. The formatter belongs with the other
      multi-timeframe summary utilities in
      `src/application/multi_timeframe_inputs.rs`.
    - RED:
      `cargo test --bin ict-engine test_multi_timeframe_phase_hint_lives_in_multi_timeframe_owner -- --nocapture`
      failed as expected with `E0425` because
      `ict_engine::application::multi_timeframe_inputs::multi_timeframe_phase_hint`
      did not exist yet; the compiler suggested the old
      `crate::multi_timeframe_phase_hint` path.
    - Fix:
      - added public
        `ict_engine::application::multi_timeframe_inputs::multi_timeframe_phase_hint`;
      - removed the private duplicate helper from `src/main.rs`;
      - imported the owner helper explicitly in `src/main.rs` and
        `src/workflow_snapshot_runtime.rs`;
      - added the owner-boundary test in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `cargo test --bin ict-engine test_multi_timeframe_phase_hint_lives_in_multi_timeframe_owner -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `53 passed; 0 failed`.
      - `cargo test --bin ict-engine workflow_snapshot_runtime::tests::analyze_snapshot_keeps_applied_regime_bundle_bbn_evidence_visible -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 11.27s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/multi_timeframe_inputs.rs src/workflow_snapshot_runtime.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/multi_timeframe_inputs.rs src/workflow_snapshot_runtime.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn multi_timeframe_phase_hint\\(|multi_timeframe_phase_hint\\(" src/main.rs src/workflow_snapshot_runtime.rs src/application/multi_timeframe_inputs.rs src/cli_surface_tests.rs`
        shows the only definition is now in
        `src/application/multi_timeframe_inputs.rs`; `src/main.rs` and
        `src/workflow_snapshot_runtime.rs` only call the owner helper.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,966 lines.
      - After extraction: `src/main.rs` = 16,939 lines,
        `src/application/multi_timeframe_inputs.rs` = 647 lines,
        `src/workflow_snapshot_runtime.rs` = 2,621 lines, and
        `src/cli_surface_tests.rs` = 2,248 lines.
      - Net effect: `src/main.rs` is 27 lines smaller and the
        multi-timeframe phase summary formatter now has a single application
        owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate branch helper owner extraction continuation on
    2026-05-22:
    - Re-read the factor-candidate helper cluster and orchestration exports
      before editing. This slice avoided file IO, ledger writes, and command
      bodies; it moved only pure branch/slug helpers.
    - Candidate selected:
      `resolve_factor_candidate_branch_fields(...)` and
      `candidate_pack_root_slug(...)` were still private `src/main.rs`
      helpers, while the structural path-ranking target types they feed are
      already owned by `src/application/orchestration`.
    - RED:
      `cargo test --bin ict-engine test_factor_candidate_branch_helpers_live_in_orchestration_owner -- --nocapture`
      failed as expected with `E0425` for missing
      `ict_engine::application::orchestration::resolve_factor_candidate_branch_fields`
      and
      `ict_engine::application::orchestration::candidate_pack_root_slug`; the
      compiler suggested the old `crate::...` helpers.
    - Fix:
      - added `src/application/orchestration/factor_candidate.rs` with public
        `FactorCandidateBranchFields`,
        `resolve_factor_candidate_branch_fields(...)`, and
        `candidate_pack_root_slug(...)`;
      - re-exported the module through `src/application/orchestration/mod.rs`;
      - imported the owner helpers in `src/main.rs`;
      - removed the private duplicate struct/helpers from `src/main.rs`;
      - added the owner-boundary test in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `cargo test --bin ict-engine test_factor_candidate_branch_helpers_live_in_orchestration_owner -- --nocapture`
        -> `1 passed; 0 failed` before and after rustfmt.
      - `cargo test --bin ict-engine test_build_factor_candidate_admission_target_artifact -- --nocapture`
        -> `3 passed; 0 failed`.
      - `cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `54 passed; 0 failed` after rustfmt.
      - `cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 58.39s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs`
        exited `0` after formatting the touched Rust files.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn resolve_factor_candidate_branch_fields\\(|fn candidate_pack_root_slug\\(|resolve_factor_candidate_branch_fields\\(|candidate_pack_root_slug\\(" src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        shows the only function definitions are now in
        `src/application/orchestration/factor_candidate.rs`; `src/main.rs`
        only calls the owner helpers.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,939 lines.
      - After extraction: `src/main.rs` = 16,838 lines,
        `src/application/orchestration/factor_candidate.rs` = 104 lines,
        `src/application/orchestration/mod.rs` = 29 lines, and
        `src/cli_surface_tests.rs` = 2,296 lines.
      - Net effect: `src/main.rs` is 101 lines smaller and the
        factor-candidate branch identity helpers now have a single
        orchestration owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate admission target builder owner extraction continuation on
    2026-05-22:
    - Re-read the builder dependencies before editing. This slice moved the
      read-only structural target builder and candidate-pack JSON reader, but
      left command dispatch, ledger writes, workflow refresh, and inventory
      persistence in `src/main.rs` for later extraction.
    - Candidate selected:
      `build_factor_candidate_admission_target_artifact(...)` still lived in
      `src/main.rs`, even though it builds
      `StructuralPathRankingTargetArtifact` rows owned by orchestration.
    - RED:
      `cargo test --bin ict-engine test_factor_candidate_admission_target_builder_lives_in_orchestration_owner -- --nocapture`
      failed as expected with `E0425` because
      `ict_engine::application::orchestration::build_factor_candidate_admission_target_artifact`
      did not exist; the compiler suggested the old
      `crate::build_factor_candidate_admission_target_artifact` path.
    - Debug note:
      the first GREEN attempt failed only because the new boundary test
      asserted the full candidate id in the branch path. A real `/tmp` CLI
      export and fixture readback showed the fixture contract uses
      `profit_factor=liquidity_sweep_reclaim_15m_wide_v1`, so the test was
      corrected to the existing branch contract instead of changing runtime
      logic.
    - Fix:
      - moved `build_factor_candidate_admission_target_artifact(...)` into
        `src/application/orchestration/factor_candidate.rs`;
      - moved `read_candidate_pack_json(...)` into the same owner module and
        imported it back into `src/main.rs` for the remaining inventory builder;
      - removed stale `candidate_pack_root_slug` and `BTreeSet` imports from
        `src/main.rs`;
      - added the owner-boundary test in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `cargo test --bin ict-engine test_factor_candidate_admission_target_builder_lives_in_orchestration_owner -- --nocapture`
        -> `1 passed; 0 failed`.
      - `cargo test --bin ict-engine test_build_factor_candidate_admission_target_artifact -- --nocapture`
        -> `3 passed; 0 failed`.
      - `cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `55 passed; 0 failed`.
      - `cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 8.20s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0`.
      - `rg -n "fn build_factor_candidate_admission_target_artifact\\(|build_factor_candidate_admission_target_artifact\\(|fn read_candidate_pack_json\\(|read_candidate_pack_json\\(" src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        shows the builder definition now only in
        `src/application/orchestration/factor_candidate.rs`; `main.rs` only
        calls the owner builder and JSON reader while the remaining inventory
        code is still local.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,838 lines.
      - After extraction: `src/main.rs` = 16,571 lines,
        `src/application/orchestration/factor_candidate.rs` = 373 lines,
        `src/application/orchestration/mod.rs` = 29 lines, and
        `src/cli_surface_tests.rs` = 2,326 lines.
      - Net effect: `src/main.rs` is 267 lines smaller and the
        factor-candidate admission target row builder now has a single
        orchestration owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate pack inventory builder owner extraction continuation on
    2026-05-22:
    - Resumed from the in-progress move and re-verified the current worktree
      before treating the slice as closed. This slice moved the read-only
      pack-inventory JSON builder into the orchestration factor-candidate
      owner, while leaving command dispatch, inventory persistence, ledger
      writes, workflow refresh, and trainer-artifact writing in `src/main.rs`
      for later extraction.
    - Candidate selected:
      `build_factor_candidate_pack_inventory(...)` no longer belongs in
      `src/main.rs` because it reads candidate-pack metadata and builds the
      JSON inventory consumed by the factor-candidate command surface; the
      admission-target builder and branch helpers already live in
      `src/application/orchestration/factor_candidate.rs`.
    - Fix:
      - moved `build_factor_candidate_pack_inventory(...)` into
        `src/application/orchestration/factor_candidate.rs`;
      - reused the owner module's existing candidate-pack JSON reader;
      - imported the owner builder in `src/main.rs`;
      - added the owner-boundary test in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-pack-inventory-target cargo test --bin ict-engine factor_candidate_pack_inventory -- --nocapture`
        -> `3 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-pack-inventory-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `56 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-pack-inventory-target cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 39.51s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/mod.rs src/application/orchestration/factor_candidate.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0` before this evidence writeback.
      - `rg -n "fn build_factor_candidate_pack_inventory\\(|build_factor_candidate_pack_inventory\\(" src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        shows the only function definition is now in
        `src/application/orchestration/factor_candidate.rs`; `src/main.rs`
        only calls the owner builder in command and test code.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,571 lines.
      - After extraction: `src/main.rs` = 16,483 lines,
        `src/application/orchestration/factor_candidate.rs` = 461 lines,
        `src/application/orchestration/mod.rs` = 29 lines, and
        `src/cli_surface_tests.rs` = 2,348 lines.
      - Net effect: `src/main.rs` is 88 lines smaller and the
        factor-candidate pack inventory builder now has a single orchestration
        owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate trainer artifact payload owner extraction continuation on
    2026-05-22:
    - Candidate selected:
      the direct-model and trainer-artifact JSON payloads inside
      `write_factor_candidate_trainer_artifacts(...)` were still assembled in
      `src/main.rs`, even though their schema is factor-candidate orchestration
      behavior. File writes, ledger writes, and workflow refresh were left in
      `src/main.rs` because they still depend on binary-local persistence and
      snapshot plumbing.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo test --bin ict-engine test_factor_candidate_trainer_artifact_payloads_live_in_orchestration_owner -- --nocapture`
      failed as expected with `E0425` for missing
      `ict_engine::application::orchestration::build_factor_candidate_ranker_direct_model_artifact`
      and `build_factor_candidate_trainer_artifact`.
    - Fix:
      - added pure owner builders
        `build_factor_candidate_ranker_direct_model_artifact()` and
        `build_factor_candidate_trainer_artifact(...)` to
        `src/application/orchestration/factor_candidate.rs`;
      - imported those builders in `src/main.rs`;
      - replaced inline JSON construction in
        `write_factor_candidate_trainer_artifacts(...)` with owner-builder
        calls while preserving saved filenames and ledger behavior;
      - added owner-boundary coverage in `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo test --bin ict-engine test_factor_candidate_trainer_artifact_payloads_live_in_orchestration_owner -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo test --bin ict-engine test_export_factor_candidate_admission_targets_writes_policy_training_target -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo test --bin ict-engine factor_candidate_trainer -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `57 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-artifact-target cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 33.86s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0` before this evidence writeback.
      - `rg -n "build_factor_candidate_ranker_direct_model_artifact|build_factor_candidate_trainer_artifact|structural-path-ranker-direct-model-v1|structural-path-ranking-trainer-artifact-v1" src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        shows both function definitions and direct-model JSON protocol in
        `src/application/orchestration/factor_candidate.rs`; `src/main.rs`
        only calls the owner builders in production code. One unrelated
        trainer protocol string remains in `src/main.rs` test fixture code.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,483 lines.
      - After extraction: `src/main.rs` = 16,440 lines,
        `src/application/orchestration/factor_candidate.rs` = 517 lines,
        `src/application/orchestration/mod.rs` = 29 lines, and
        `src/cli_surface_tests.rs` = 2,413 lines.
      - Net effect: `src/main.rs` is 43 lines smaller and the
        factor-candidate trainer payload schema now has a single orchestration
        owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate trainer artifact writer owner extraction continuation on
    2026-05-22:
    - Candidate selected:
      `write_factor_candidate_trainer_artifacts(...)` still lived in
      `src/main.rs`, but after the payload-builder extraction it only handled
      factor-candidate trainer artifact files and the matching ledger row. It
      does not require the binary-local workflow snapshot refresh dependency.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-writer-target cargo test --bin ict-engine test_factor_candidate_trainer_artifact_writer_lives_in_orchestration_owner -- --nocapture`
      failed as expected with `E0425` because
      `ict_engine::application::orchestration::write_factor_candidate_trainer_artifacts`
      did not exist yet.
    - Debug note:
      the first GREEN attempt compiled but failed with `No such file or
      directory` for
      `policy_training/factor_candidate_ranker_direct_model.json`. Root cause:
      the old binary-local writer relied on
      `export_factor_candidate_admission_targets(...)` creating the
      `policy_training/` directory first. The owner API now creates that
      directory itself before writing nested files.
    - Fix:
      - moved `write_factor_candidate_trainer_artifacts(...)` into
        `src/application/orchestration/factor_candidate.rs`;
      - reused public state APIs `save_text_state`,
        `append_artifact_ledger_entry`, and `artifact_state_path`;
      - made the owner writer create
        `<state_dir>/<symbol>/policy_training/` before saving artifacts;
      - imported the owner writer in `src/main.rs`;
      - added writer owner-boundary and side-effect coverage in
        `src/cli_surface_tests.rs`.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-writer-target cargo test --bin ict-engine test_factor_candidate_trainer_artifact_writer_lives_in_orchestration_owner -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-writer-target cargo test --bin ict-engine test_export_factor_candidate_admission_targets_writes_policy_training_target -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-writer-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `58 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-trainer-writer-target cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 41.91s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        exited `0`.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0` before this evidence writeback.
      - `rg -n "fn write_factor_candidate_trainer_artifacts\\(|write_factor_candidate_trainer_artifacts\\(" src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        shows the only function definition is now in
        `src/application/orchestration/factor_candidate.rs`; `src/main.rs`
        only calls the owner writer.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,440 lines.
      - After extraction: `src/main.rs` = 16,376 lines,
        `src/application/orchestration/factor_candidate.rs` = 588 lines,
        `src/application/orchestration/mod.rs` = 29 lines, and
        `src/cli_surface_tests.rs` = 2,464 lines.
      - Net effect: `src/main.rs` is 64 lines smaller and the
        factor-candidate trainer artifact writer now has a single
        orchestration owner.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.
  - Factor-candidate pack inventory persistence owner extraction continuation
    on 2026-05-22:
    - Candidate selected:
      `persist_factor_candidate_pack_inventory(...)` still lived in
      `src/main.rs` and was the remaining factor-candidate inventory
      state/ledger writer. The reusable persistence part belongs with the
      factor-candidate orchestration owner, while workflow snapshot refresh
      remains a binary command concern because `workflow_snapshot_runtime` is
      currently a bin-local module.
    - RED:
      `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo test --bin ict-engine test_factor_candidate_pack_inventory_persistence_lives_in_orchestration_owner -- --nocapture`
      failed as expected with `E0425` because
      `ict_engine::application::orchestration::persist_factor_candidate_pack_inventory`
      did not exist yet.
    - Fix:
      - moved the factor-candidate inventory file write and artifact-ledger row
        into `src/application/orchestration/factor_candidate.rs`;
      - reused public state APIs `save_state`, `append_artifact_ledger_entry`,
        and `artifact_state_path`;
      - imported the owner writer in `src/main.rs`;
      - made `factor_candidate_packs_command(...)` refresh the workflow
        snapshot explicitly after the owner persistence call;
      - left `export_factor_candidate_admission_targets(...)` on its existing
        final snapshot refresh, removing the previous implicit double refresh
        through the inventory helper;
      - adjusted the main-unit regression to prove the owner persistence writes
        ledger state and that an explicit snapshot refresh still surfaces the
        artifact.
    - GREEN / verification:
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo test --bin ict-engine test_factor_candidate_pack_inventory_persistence_lives_in_orchestration_owner -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo test --bin ict-engine test_persist_factor_candidate_pack_inventory_writes_ledger_and_allows_snapshot_refresh -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo test --bin ict-engine test_export_factor_candidate_admission_targets_writes_policy_training_target -- --nocapture`
        -> `1 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
        -> `59 passed; 0 failed`.
      - `CARGO_TARGET_DIR=/tmp/ict-engine-factor-inventory-persist-target cargo check --bin ict-engine`
        -> `Finished dev profile [unoptimized + debuginfo] target(s) in 52.64s`;
        after rustfmt, rerun with warm target finished in `2.18s`.
      - `rustfmt --edition 2021 --check src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs`
        exited `0` after applying mechanical rustfmt line wrapping.
      - `git diff --check -- src/main.rs src/cli_surface_tests.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
        exited `0` before this evidence writeback.
      - `rg -n "fn persist_factor_candidate_pack_inventory\\(|persist_factor_candidate_pack_inventory\\(" src/main.rs src/application/orchestration/factor_candidate.rs src/application/orchestration/mod.rs src/cli_surface_tests.rs`
        shows the only function definition is now in
        `src/application/orchestration/factor_candidate.rs`; `src/main.rs`
        only calls the owner writer.
    - Line-count telemetry:
      - Before this extraction: `src/main.rs` = 16,376 lines.
      - After extraction: `src/main.rs` = 16,327 lines,
        `src/application/orchestration/factor_candidate.rs` = 640 lines,
        and `src/cli_surface_tests.rs` = 2,494 lines.
      - Net effect: `src/main.rs` is 49 lines smaller and the
        factor-candidate pack inventory persistence path now has a single
        orchestration owner for reusable state/ledger writes.
    - Scope note: this is still one verified extraction slice. It does not
      close the `<5,000` target, full command-output matrix, non-empty
      production validation proof, manual/nightly Auto-Quant smoke design,
      release-clean export evidence, or full dirty-tree completion.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 loop truth / validation contract | Fresh continuation checks prove the status split: repeated structural feedback observations can show `observation_validation=30/30` while target-row production validation remains `2/30`; fixture production-ready status also has direct coverage | split_and_fixture_ready_verified | Still need release-grade live production validation packet before any trading/release-readiness claim |
| P0 `src/main.rs` reduction | `main.rs` reduced from 19360 to 19237 lines in the artifact arg extraction; status, structural path-ranker, market-data, research/status, factor-asset, core runtime/backtest, research-loop, analyze/analyze-live, and multiple AutoQuant arg extractions moved command payloads into focused `*_cli_args.rs` modules; parser/output-format tests moved to `src/cli_surface_tests.rs`; owner-module runtime input DTOs moved to `src/update_command.rs` and `src/probabilistic_backtest_runtime.rs`; shared output-format resolver and agent-preserving label helper moved to `src/output_format.rs`; shared state-dir helper moved to `src/state_dir.rs`; env report/shell helpers moved to `src/env_command.rs`; Auto-Quant output-dir isolation helper and futures-cost shell moved to `src/auto_quant_command.rs`; analyze output adapter moved to `src/analyze_command.rs`; executor-summary formatter duplicate removed from `src/main.rs` in favor of `src/application/output_foundation.rs`; executor-scorecard source resolution duplicate removed from `src/main.rs` in favor of `src/application/orchestration/workflow_status.rs`; multi-timeframe phase hint formatting moved from `src/main.rs` to `src/application/multi_timeframe_inputs.rs`; factor-candidate branch/slug helpers, admission-target row builder, pack-inventory builder, inventory persistence writer, trainer artifact payload builders, and trainer artifact writer moved from `src/main.rs` to `src/application/orchestration/factor_candidate.rs`; after this inventory persistence extraction, `src/main.rs` is 16327 lines with parser/owner-boundary coverage preserved | bin_cargo_verified_arg_and_test_extractions | Continue extraction in small Cargo-verified batches; the `<5,000` target remains open |
| P0 external ranker Python contract | Python trainer now preserves target row count under direct fallback and validates target CSV existence/required columns with stable errors; shared fixture target and score CSV exist; Rust integration contract now covers valid fixture score apply, missing/malformed score-file recovery context, trainer artifact registration, runtime enable, and status readback with `runtime_source=registered_artifact`; fresh continuation reran Python contract `3/3`, hotplug `13/13`, and Rust integration `7/7` | fixture_chain_verified | Optional next: add CLI-process smoke using a generated score file if this becomes release evidence |
| P0 compile/test health | focused artifact CLI test passed again; focused status/structural/workflow/market-data-debug/market-data-SOP/research-status, factor-asset, core runtime/backtest, research-loop, analyze/analyze-live, owner-module runtime DTO, output-format owner module, output-format label owner helper, state-dir owner module, env-command owner module, Auto-Quant output-dir owner helper, Auto-Quant futures-cost owner shell, analyze output adapter owner, executor-summary formatter owner, executor-scorecard source owner, multi-timeframe phase-hint owner, factor-candidate branch-helper owner, factor-candidate admission-target builder owner, factor-candidate pack-inventory builder/persistence owner, and multiple AutoQuant CLI parser tests passed; `cli_surface_tests` now passes 59/59 after moving parser tests out of `main.rs` and adding owner-boundary coverage; latest full `test_cli` parser sweep passes 36/36; focused `output_format` passes 11/11; focused `analyze_command` regression filter passes 13/13; focused `factor_research` regression filter passes 13/13; focused Auto-Quant setup parser passes 1/1; real `auto-quant-futures-cost --symbol NQ --price 17000 --compact` exits 0; isolated/shared `cargo check --bin ict-engine` exits 0; earlier full `cargo fmt --check`, `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`, zero-config smoke, and full `cargo test` had passed in this live loop | fmt_check_clippy_smoke_full_test_verified_with_focused_parser_rechecks | Continue shrinking `main.rs` in small Cargo-verified batches; do not treat this as release readiness |
| P0 guardrail baseline | `support/docs/main-rs-guardrails.md` now records `src/main.rs` at 19,202 lines and the `<5,000` target | doc_check_verified | Continue extraction in small Cargo-verified batches |
| P1 human output consistency | Zero-config smoke ran the documented human/agent/json surfaces successfully under `/tmp` | smoke_verified_partial | Full generated command-output matrix still pending |
| P1 first-run product path | Consumer quickstart Flow 1 demo, Flow 2 provider/live NQ, and Flow 3 local cleaned-data commands now have fresh `/tmp` exit-0 evidence; smoke script direct and bash invocations both pass | quickstart_commands_verified_observe_only | Keep clear that outputs are inspectable/observe-only, not trade or release readiness |
| P1 smoke acceptance script | Script now refuses repo-local `STATE_DIR` before Cargo unless `ICT_ENGINE_ALLOW_REPO_STATE=1`; README names `bash support/scripts/smoke_acceptance.sh`; old full-smoke checklist item `factor-research --backend native --human` is proven stale; Auto-Quant factor-research is dependency/network-sensitive on this host | fast_smoke_verified_full_gate_needs_design | Keep fast script as consumer smoke; design a separate manual/nightly Auto-Quant smoke only with explicit dependency/preseed strategy |
| P1 Python script governance | `script_manifest.json`, manifest checker, and wrapper tests now exist and pass local non-Cargo verification | verified_manifest_partial | Optional: wire checker into CI after full gate pressure clears |
| P1 error message contract | Apply-score, register-artifact, `analyze --data-htf`, and Auto-Quant `factor-research --data` missing-file paths now have focused RED/GREEN coverage with path/schema/recovery context and human handoff notes; fresh real CLI probes show `analyze --data-htf` exits with flag/path/schema/recovery context and `factor-research --human` exposes missing-data recovery notes | listed_paths_cli_verified_partial_matrix_open | Continue broad generated command-output matrix; optional CLI-process smoke for generated structural score files |
| P2 agent/contributor truth map cleanup | `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` now agree on 8 Rust factor categories; `check_factor_truth_map.py` passed | doc_check_verified | Optional: add CI wiring later if this becomes release evidence |
| P2 contribution/release cleanup | `CONTRIBUTING.md` exists, README links it, main.rs guardrails are cited, and release mirror runbook names current source metadata and clean-export boundary | doc_check_verified | Still not a release claim; clean export, privacy scan, fmt/clippy/test/smoke remain required |

Next audit loop:

1. Continue extracting the next small command/arg batch from `main.rs`.
2. Keep each extraction batch behind focused parser tests plus fresh
   `cargo check --bin ict-engine`; run the full gate set again before any
   release or commit decision.

## Current Evidence

- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- CLI commands: 49
- Rust: 422 files / ~149k LOC
- Python: 183 files / ~41k LOC
- Docs: 194 markdown / ~44k LOC
- Rust tests discovered: ~1161 `#[test]` across 203 Rust files
- CI: `.github/workflows/ci.yml` runs `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test` on Ubuntu and macOS
- Verified during audit:
  - `cargo check --all-targets` passed in 16m33s
  - `ict-engine analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-audit-demo --human` passed
  - `ict-engine factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-audit-demo --backend native --human` passed
  - `ict-engine workflow-status --symbol DEMO --state-dir /tmp/ict-engine-audit-demo --human` passed
  - `ict-engine export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-audit-demo` passed
  - `support/scripts/auto_quant_external/pandas_path_ranker_trainer.py` fallback path produced a direct weighted model when CatBoost was unavailable
- Not completed:
  - `cargo test --no-run` was manually killed after a long compile/lock wait; no failure signal, but no pass signal either

### Live Continuation Checkpoint - 2026-05-21 16:56 +0800

Owner: Codex current turn.
Claim: `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. Completion is not proven, and several planned user/contributor comfort surfaces are still missing in the live worktree.

Evidence gathered this turn:

- Routing read before work: `~/.hermes/routing/skill-router.md`, `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`, and installed runtime skill `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`.
- Dirty tree is large and shared; active TOMAC/Board B Python, Auto-Quant, and `ict-engine` jobs are running. This lane must not take over Board A/B terminal rows or active factor artifacts.
- `git status --short` shows many unrelated code/docs/script changes. Stage or revert nothing broadly.
- `src/main.rs` is now `19039` lines by `wc -l src/main.rs`, so the main-entrypoint reduction item is not closed.
- Source search shows `target_row_validation` and `feedback_observation_validation` structs/fields/tests now exist in `src/application/entry_models/training_export.rs`; this suggests the first P0 item may be implemented in the dirty tree, but it still needs fresh targeted test and CLI readback before marking done here.
- Missing-file probes show these plan deliverables are still absent:
  - `support/scripts/smoke_acceptance.sh`
  - `support/docs/consumer-quickstart.md`
  - `support/docs/contributor-quickstart.md`
  - `support/docs/command-output-contract.md`
  - `support/scripts/SCRIPTS.md`
  - `CONTRIBUTING.md`

Immediate audit loop:

1. Verify the potentially implemented P0 loop-truth split with targeted Rust tests and `policy-training-status` CLI output.
2. Inventory current CLI output-format support from real help output rather than from source guesses.
3. Run zero-config smoke with explicit `/tmp` state and capture private-path/secret leakage signals.
4. Update this document after each probe with one of: `proved_complete`, `contradicted`, `incomplete`, `weak_evidence`, or `missing_evidence`.
5. Only patch code/docs when a gap is confirmed and the edit is narrow enough to avoid active-lane collisions.

Current gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 loop truth / validation contract | Fields and tests found in source, not verified live this turn | weak_evidence | Run targeted `cargo test` and CLI readback |
| P0 external ranker contract test | No fresh fixture/test proof yet | missing_evidence | Inspect tests and run Python/Rust contract checks |
| P0 `src/main.rs` reduction | `19039` lines | contradicted | Identify extractable command batch; do not mark complete |
| P1 human output consistency | Output flags appear uneven in source; no matrix doc exists | incomplete | Generate command/help matrix from actual binary |
| P1 first-run product path | Consumer/contributor quickstarts absent | missing_evidence | Create docs after verifying exact commands |
| P1 smoke acceptance script | `support/scripts/smoke_acceptance.sh` absent | missing_evidence | Add script only after command smoke is proven |
| P1 Python script governance | `support/scripts/SCRIPTS.md` absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | Not reverified this turn | weak_evidence | Probe known missing-file commands |
| P2 agent/contributor truth map cleanup | Not reverified this turn | weak_evidence | Compare `AGENT.md`, factor catalog, and enum variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` absent | missing_evidence | Draft public contributor flow after verification gates settle |

### Live Audit Loop - 2026-05-21 17:56 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. One command-output UX gap was repaired, but broader audit completion is still contradicted.

Evidence gathered this loop:

- TDD red test added first:
  - Test: `test_cli_structural_path_ranker_commands_accept_output_aliases`
  - Red result: `cargo test test_cli_structural_path_ranker_commands_accept_output_aliases -- --nocapture` failed because `Commands::ExportStructuralPathRankingTarget` had no `human` field and `Commands::ApplyStructuralPathRankingExternalScores` had no `output_format` field.
- Fix applied:
  - Added `--output-format json|compact|agent|human` plus `--compact`, `--agent`, and `--human` aliases to:
    - `export-structural-path-ranking-target`
    - `apply-structural-path-ranking-external-scores`
  - Kept default JSON behavior for compatibility.
  - Added compact JSON and a one-line human summary for both command paths.
  - Touched files:
    - `src/main.rs`
    - `src/policy_training_command.rs`
    - `src/application/entry_models/mod.rs`
    - `src/application/entry_models/training_export.rs`
- Verification:
  - `rustfmt --edition 2021 --check src/main.rs src/policy_training_command.rs src/application/entry_models/mod.rs src/application/entry_models/training_export.rs` passed after formatting.
  - `cargo test test_cli_structural_path_ranker_commands_accept_output_aliases -- --nocapture` passed.
  - `cargo run --quiet -- export-structural-path-ranking-target --help` now shows `--output-format`, `--compact`, `--agent`, and `--human`.
  - `cargo run --quiet -- apply-structural-path-ranking-external-scores --help` now shows `--output-format`, `--compact`, `--agent`, and `--human`.
  - `cargo run --quiet -- export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --human` printed a one-line structural-path target summary.
  - `cargo run --quiet -- export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --compact` emitted valid compact JSON.
  - A `/tmp/ict-engine-demo-ranker-scores.csv` score file generated from the DEMO target applied successfully with `cargo run --quiet -- apply-structural-path-ranking-external-scores --symbol DEMO --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --scores-file /tmp/ict-engine-demo-ranker-scores.csv --human`, raising `raw_scores=3/3` in the human summary.
  - `git diff --check -- src/main.rs src/policy_training_command.rs src/application/entry_models/mod.rs src/application/entry_models/training_export.rs src/state/persistence.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.
- Residual risk:
  - `wc -l src/main.rs` is now `19127`, so the command-output fix improved UX while moving the `main.rs` reduction gate in the wrong direction. This must be repaid by extraction work before completion.
  - Current `cargo run` / `cargo test` probes still emit warnings that would likely break `cargo clippy --all-targets -- -D warnings`: unused `workflow_status_needs_provider_surface`, unused `command_status_with_timeout`, unused Deribit `theta`/`rho`, unused `pseudo_inverse`, and unused `main.rs` imports `infer_interval_for_analyze_frame` / `native_frame_computations`.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Targeted validation split test and ranker CLI alias test pass; touched files are rustfmt/diff-check clean | proved_targeted | Run `cargo check --all-targets`, then full `cargo test`, before any completion claim |
| P0 loop truth / validation contract | Focused split test passes; demo `policy-training-status` human/JSON readback exposes target-row and feedback-observation surfaces | proved_surface_presence | Still need non-empty policy-training state readback before marking production validation complete |
| P0 external ranker contract test | Unit/mocked Python hotplug contract passed 13/13; DEMO export/apply human smoke passed through Rust CLI and `/tmp` score file | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime |
| P0 `src/main.rs` reduction | `19127` lines after this UX patch | contradicted | Extract ranker command output/rendering or another command batch out of `main.rs` to reverse growth |
| P1 human output consistency | Ranker export/apply now support output formats and aliases; other commands still need matrix audit | partial_fix | Generate command-output matrix from real help output and patch next inconsistent command |
| P1 first-run product path | Consumer/contributor quickstarts absent | missing_evidence | Create docs after exact smoke commands are reverified |
| P1 smoke acceptance script | `support/scripts/smoke_acceptance.sh` absent | missing_evidence | Add script after smoke chain is proven against current binary |
| P1 Python script governance | `support/scripts/SCRIPTS.md` absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | Not reverified in this loop | weak_evidence | Probe missing-file cases after compile health is restored |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` absent | missing_evidence | Draft public contributor flow after verification gates settle |
| Release/CI warning gate | Fresh cargo probes emit multiple warnings | incomplete | Run `cargo clippy --all-targets -- -D warnings`; fix warnings in scoped batches |

Next audit loop:

1. Run `cargo check --all-targets` to determine whether the current dirty tree is broadly compile-clean after the targeted patches.
2. Run or deliberately scope `cargo clippy --all-targets -- -D warnings` to prove or list the current warning gate.
3. Generate a command-output matrix from real `--help` surfaces.
4. Choose the next UX or compile warning fix that reduces `main.rs` or keeps it from growing.

### Live Audit Loop - 2026-05-21 18:36 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. The Rust test/lint gate is now green for this dirty tree, but the full audit plan is still not closed because consumer docs, smoke scripts, script governance, contributor docs, and `main.rs` reduction remain open.

Evidence gathered this loop:

- Root-cause investigation:
  - Full `cargo test` previously failed only `tests::test_build_analyze_report_uses_current_analyze_regime_for_ranker_path_join`.
  - Focused reproduction showed runtime ranker matching was healthy: `runtime_active_match_count=2`, `runtime_artifact_match_count=2`, score source `registered_artifact`, and `execution_gate_status=pass`.
  - The actual blocker was the test fixture: it registered a 2-row trainer artifact, so `policy-training-status` correctly reported production validation `0/30` or `2/30` and `ready=false`; `execution_tree.rs` intentionally treats such scores as visible-only until validation is ready.
- Fix applied:
  - Updated only the stale test fixture in `src/main.rs` so this branch-join test writes validated trainer artifact metrics before enabling runtime, matching the adjacent CLI runtime-threading test.
  - Production behavior was not relaxed: validation-insufficient ranker scores still remain visible-only.
- Verification:
  - `cargo test test_build_analyze_report_uses_current_analyze_regime_for_ranker_path_join -- --nocapture` passed.
  - `cargo test test_build_analyze_report_path_ranker_lineage_uses_state_dir_runtime_scores -- --nocapture` passed.
  - `cargo test` passed:
    - `src/lib.rs`: 1126 tests passed.
    - `src/main.rs`: 276 tests passed.
    - Integration tests passed, including provider-neutral CLI, regime adapter, execution tree, sparse/spectral/tucker suites.
    - Doc-tests passed with 0 tests.
  - `cargo clippy --all-targets -- -D warnings` passed.
  - `cargo fmt --check` passed.
  - `git diff --check` passed.
  - `wc -l src/main.rs` is now `19153`.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | `cargo test`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt --check`, and `git diff --check` pass in this loop | proved_current_dirty_tree | Keep green while reducing remaining docs/UX/architecture debt |
| P0 loop truth / validation contract | Focused split test and live policy-training surfaces exist; execution tree preserves visible-only behavior for validation-insufficient ranker scores | proved_guard_behavior | Still need non-empty policy-training state readback before marking production validation complete |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract have passed; current-analyze runtime branch join now passes with validated artifact fixture | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | `19153` lines after ranker UX/test patches | contradicted | Extract ranker command output/rendering or another command batch out of `main.rs` to reverse growth |
| P1 human output consistency | Ranker export/apply aliases fixed; other commands still need real help/output matrix | partial_fix | Generate command-output matrix from actual `--help` output |
| P1 first-run product path | `support/docs/consumer-quickstart.md` and `support/docs/contributor-quickstart.md` still absent | missing_evidence | Create docs after exact smoke commands are reverified |
| P1 smoke acceptance script | `support/scripts/smoke_acceptance.sh` still absent | missing_evidence | Add script after smoke chain is proven against current binary |
| P1 Python script governance | `support/scripts/SCRIPTS.md` still absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | Not reverified in this loop | weak_evidence | Probe missing-file cases after command matrix |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` still absent | missing_evidence | Draft public contributor flow after verification gates settle |

Next audit loop:

1. Create the command-output matrix from real help/output surfaces.
2. Add the smoke acceptance script only after the command chain is reverified from `/tmp`.
3. Draft consumer/contributor quickstarts and `CONTRIBUTING.md`.
4. Start a `main.rs` extraction batch so the line-count gate moves down instead of up.

### Live Audit Loop - 2026-05-21 18:51 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. The AGENT zero-config smoke chain is now encoded and verified, but consumer/contributor docs, command-output contract, script governance, contribution docs, and `main.rs` reduction remain open.

Evidence gathered this loop:

- Re-read authority surfaces before work: `~/.hermes/routing/skill-router.md`, `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`, installed runtime skill `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`, and this plan.
- Completed the remaining explicit `/tmp` smoke commands from `AGENT.md`:
  - `cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-smoke-20260521-continue --refresh --output-format json` passed and returned posterior/soft-evidence JSON with `gate_status=pass_hard`.
  - `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-smoke-20260521-continue --output-format agent` passed and returned agent JSON that correctly keeps entry-model/ranker training pending rather than trade-promoting demo evidence.
- Added `support/scripts/smoke_acceptance.sh`.
  - It runs from repo root.
  - It defaults `STATE_DIR` to `/tmp/ict-engine-smoke-acceptance-<utc timestamp>` and writes command output under `$STATE_DIR/smoke-output`.
  - It runs the AGENT zero-config chain: `provider-status --compact`, empty `workflow-status --human`, `analyze --demo --human`, refreshed `workflow-status --agent`, `pre-bayes-status --output-format json`, and `policy-training-status --output-format agent`.
  - It fails on nonzero commands and scans captured output for `/Users/` plus secret-like markers.
- Verification:
  - `bash -n support/scripts/smoke_acceptance.sh` passed.
  - `STATE_DIR=/tmp/ict-engine-smoke-acceptance-verify-20260521 support/scripts/smoke_acceptance.sh` passed.
  - Script leak scan found no private path or secret-like matches in `/tmp/ict-engine-smoke-acceptance-verify-20260521/smoke-output`.
- Scope note:
  - This script proves the current `AGENT.md` zero-config consumer chain. The older P1 section below still mentions adding `factor-research` and structural-path export checks; decide separately whether that becomes a second/full mode instead of bloating the first-run smoke.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Previous loop: `cargo test`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt --check`, and `git diff --check` passed | proved_current_dirty_tree | Re-run after further code changes; shell/doc-only changes still need diff checks |
| P0 loop truth / validation contract | Pre-Bayes and policy-training smoke surfaces pass; demo state still has no non-empty structural path-ranking target export | proved_surface_presence | Still need non-empty policy-training state readback before marking production validation complete |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | `19153` lines in previous loop | contradicted | Extract ranker command output/rendering or another command batch out of `main.rs` |
| P1 human output consistency | Ranker export/apply aliases fixed; other commands still need real help/output matrix | partial_fix | Generate command-output matrix from actual `--help` output |
| P1 first-run product path | `support/docs/consumer-quickstart.md` and `support/docs/contributor-quickstart.md` still absent | missing_evidence | Create docs from the verified smoke chain |
| P1 smoke acceptance script | `support/scripts/smoke_acceptance.sh` exists and passed `bash -n` plus live `/tmp` execution | implemented_verified_zero_config | Decide whether to add optional/full checks for factor-research/export or document this as the fast smoke gate |
| P1 Python script governance | `support/scripts/SCRIPTS.md` still absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | Not reverified in this loop | weak_evidence | Probe missing-file cases after command matrix |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` still absent | missing_evidence | Draft public contributor flow after verification gates settle |

Next audit loop:

1. Run `git diff --check` for the new script and plan doc.
2. Create consumer/contributor quickstarts from the verified smoke chain.
3. Create the command-output contract matrix from actual help output.
4. Start a `main.rs` extraction batch only after docs/smoke surfaces are stable.

### Live Audit Loop - 2026-05-21 19:14 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. Three user-facing P1 docs now exist and are linked, but the full audit still has open script governance, artifact output-format gaps, error-message probes, non-empty ranker validation proof, and `main.rs` reduction.

Evidence gathered this loop:

- Re-read authority surfaces before work: `~/.hermes/routing/skill-router.md`, `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`, installed runtime skill `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`, and this plan.
- Current missing-file probe still showed these absent before edits:
  - `support/docs/consumer-quickstart.md`
  - `support/docs/contributor-quickstart.md`
  - `support/docs/command-output-contract.md`
  - `CONTRIBUTING.md`
  - `support/scripts/SCRIPTS.md`
- Added:
  - `support/docs/consumer-quickstart.md`
  - `support/docs/contributor-quickstart.md`
  - `support/docs/command-output-contract.md`
- Updated `README.md` near the first-run section to link the consumer quickstart, contributor quickstart, and command-output contract.
- Real help probes used for the command-output matrix:
  - `cargo run --quiet -- --help`
  - `cargo run --quiet -- provider-status --help`
  - `cargo run --quiet -- analyze --help`
  - `cargo run --quiet -- analyze-live --help`
  - `cargo run --quiet -- workflow-status --help`
  - `cargo run --quiet -- pre-bayes-status --help`
  - `cargo run --quiet -- policy-training-status --help`
  - `cargo run --quiet -- export-structural-path-ranking-target --help`
  - `cargo run --quiet -- apply-structural-path-ranking-external-scores --help`
  - `cargo run --quiet -- artifact-status --help`
  - `cargo run --quiet -- artifact-lineage --help`
  - `cargo run --quiet -- artifact-diff --help`
- Matrix result:
  - `analyze`, `analyze-live`, `workflow-status`, `export-structural-path-ranking-target`, and `apply-structural-path-ranking-external-scores` now expose the full shared output-format/alias surface.
  - `provider-status` remains a partial legacy surface (`--compact`, `--agent`, `--jsonl`, no `--output-format`).
  - `pre-bayes-status` has `json|compact|human`, no agent mode.
  - `policy-training-status` accepts `agent` via `--output-format`, but lacks a `--agent` alias.
  - `artifact-status`, `artifact-lineage`, and `artifact-diff` still lack output-format aliases.
- Public-data probe:
  - `cargo run --quiet -- provider-status --domain live_runtime --agent` passed and reports `live_runtime:3/5 ready`, including default-enabled `yfinance`.
  - `cargo run --quiet -- provider-status --domain market_data --agent` passed and reports `market_data:9/9 ready`.
  - `cargo run --quiet -- analyze-live --symbol SPY --futures-symbol SPY --state-dir /tmp/ict-engine-quickstart-public-verify --human` failed with a clear missing spot-symbol error.
  - `cargo run --quiet -- analyze-live --symbol SPY --futures-symbol SPY --spot-symbol SPY --state-dir /tmp/ict-engine-quickstart-public-verify --human` failed with a clear missing options-symbol error.
  - `cargo run --quiet -- analyze-live --symbol SPY --futures-symbol SPY --spot-symbol SPY --options-symbol SPY --state-dir /tmp/ict-engine-quickstart-public-verify --human` failed because Yahoo returned 404 for `SPY=F`.
  - `cargo run --quiet -- analyze-live --symbol NQ --state-dir /tmp/ict-engine-quickstart-public-verify --human` stalled on provider/network fetch and was killed after no output. The consumer quickstart documents this as provider-dependent and routes users back to `provider-status --domain live_runtime --agent` on failure or stall.
- Verification:
  - `STATE_DIR=/tmp/ict-engine-smoke-doc-verify-20260521 support/scripts/smoke_acceptance.sh` passed.
  - `cargo run --quiet -- provider-status --domain live_runtime --agent` passed.
  - `cargo run --quiet -- provider-status --domain market_data --agent` passed.
  - `git diff --check -- README.md support/docs/consumer-quickstart.md support/docs/contributor-quickstart.md support/docs/command-output-contract.md support/scripts/smoke_acceptance.sh support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Previous loop: full Rust tests/clippy/fmt were green; this loop touched docs plus README only | proved_previous_code_green | Re-run code gates after any code change; doc slice has diff-check proof |
| P0 loop truth / validation contract | Smoke surfaces pass; no non-empty structural path-ranking validation state proved in this loop | proved_surface_presence | Build or reuse a non-empty state to prove production validation counters |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | `19153` lines in previous loop | contradicted | Extract ranker command output/rendering or another command batch out of `main.rs` |
| P1 human output consistency | `support/docs/command-output-contract.md` exists from real help probes and records remaining artifact/pre-bayes/policy gaps | partial_doc_complete | Patch artifact/pre-bayes/policy output alias gaps or document intentional exceptions with tests |
| P1 first-run product path | Consumer/contributor quickstarts exist and README links them; demo smoke and provider-readiness commands passed | implemented_partially_verified | Public `analyze-live` remains provider/network-dependent; local cleaned-data flow remains placeholder-command documented |
| P1 smoke acceptance script | Script exists and passed again with `/tmp/ict-engine-smoke-doc-verify-20260521` | implemented_verified_zero_config | Decide whether to add optional/full checks for factor-research/export or keep as fast first-run smoke |
| P1 Python script governance | `support/scripts/SCRIPTS.md` still absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | SPY analyze-live failure paths are clear; broader missing-file cases not reverified | weak_partial | Probe missing-file cases after output contract code gaps |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` still absent | missing_evidence | Draft public contributor flow after verification gates settle |

Next audit loop:

1. Create `CONTRIBUTING.md` using the contributor quickstart and current verification gates.
2. Create `support/scripts/SCRIPTS.md` without moving active scripts.
3. Patch the smallest output-format gap (`policy-training-status --agent` alias or artifact status output modes), then verify with focused tests/help probes.
4. Start a `main.rs` extraction batch after the P1 docs/governance slice is stable.

### Live Audit Loop - 2026-05-21 19:34 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. The public/contributor/script governance docs are now present, and a false-positive audit helper was fixed, but output-format code gaps and architecture reduction remain open.

Evidence gathered this loop:

- Added `CONTRIBUTING.md`.
  - Records `/tmp` state discipline, dirty-worktree preservation, verification commands, output/evidence rules, and release boundaries.
  - Linked from `README.md`.
- Added `support/scripts/SCRIPTS.md`.
  - Classifies public smoke/CI helpers, active external bridge scripts, provider/operator bridges, research helpers, and archived/generated script surfaces.
  - Does not move or rename active scripts.
- Found and fixed a real audit-tool bug in `support/scripts/help_audit.py`:
  - Symptom: `python3 support/scripts/help_audit.py` exited 0 with `command_count=0`, even though root help lists many commands.
  - Root cause 1: `command_list()` required whitespace after a command token, but current Clap help prints command names alone on one line and descriptions on the next.
  - Root cause 2: the script used `cargo run` for every subcommand help probe; `cargo run --quiet -- futures-sop --help` and `cargo run --quiet -- expansion-sop --help` timed out, while the built binary returned help immediately.
  - Fix: accept end-of-line command tokens, prefer an existing built binary under `.local-artifacts/cargo-target/debug/ict-engine` or `target/debug/ict-engine`, and keep timeout/error reporting for help probes.
- Verification:
  - Direct help probes proved `.local-artifacts/cargo-target/debug/ict-engine futures-sop --help` and `expansion-sop --help` return 0.
  - `python3 support/scripts/help_audit.py` now passes with `command_count=53`, `commands_with_missing_help=0`, `commands_with_help_errors=0`, and `commands_with_market_bias=0`.
  - `python3 -m py_compile support/scripts/help_audit.py` passed.
  - `bash -n support/scripts/smoke_acceptance.sh` passed.
  - `git diff --check -- README.md CONTRIBUTING.md support/docs/consumer-quickstart.md support/docs/contributor-quickstart.md support/docs/command-output-contract.md support/scripts/SCRIPTS.md support/scripts/smoke_acceptance.sh support/scripts/help_audit.py support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Previous loop: full Rust tests/clippy/fmt were green; current loop changed Python/docs only | proved_previous_code_green | Re-run Rust gates after Rust code changes |
| P0 loop truth / validation contract | Smoke surfaces pass; no non-empty structural path-ranking validation state proved in this loop | proved_surface_presence | Build or reuse a non-empty state to prove production validation counters |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | `19153` lines in previous loop | contradicted | Extract ranker command output/rendering or another command batch out of `main.rs` |
| P1 human output consistency | `support/docs/command-output-contract.md` exists; `help_audit.py` now audits 53 commands instead of falsely passing 0 | partial_doc_and_tooling | Patch artifact/pre-bayes/policy output alias gaps or document intentional exceptions with tests |
| P1 first-run product path | Consumer/contributor quickstarts exist, README links them, smoke/provider probes passed | implemented_partially_verified | Public `analyze-live` remains provider/network-dependent; local cleaned-data flow remains placeholder-command documented |
| P1 smoke acceptance script | Script exists and passed syntax plus live smoke earlier this turn | implemented_verified_zero_config | Decide whether to add optional/full checks for factor-research/export or keep as fast first-run smoke |
| P1 Python script governance | `support/scripts/SCRIPTS.md` exists and classifies current script families without moving active scripts | implemented_doc_only | Add `script_manifest.json` or tests only if this becomes a hard gate |
| P1 error message contract | SPY analyze-live failure paths are clear; broader missing-file cases not reverified | weak_partial | Probe missing-file cases after output contract code gaps |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` exists and is linked from README | implemented_doc_only | Still need release/readiness clean-export process before any release claim |

Next audit loop:

1. Patch the smallest output-format code gap: likely `policy-training-status --agent` alias because the backend already accepts `agent` via `--output-format`.
2. Add focused CLI parse/help test for that alias.
3. Probe artifact status output-format gaps and decide code fix vs documented exception.
4. Start a `main.rs` extraction batch after output surfaces stop growing.

### Live Audit Loop - 2026-05-21 20:25 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. One more output-consistency gap is fixed, but artifact output modes, broader error-message checks, non-empty production validation proof, and `main.rs` reduction remain open.

Evidence gathered this loop:

- Targeted TDD slice: `policy-training-status --agent` alias.
  - RED test added: `test_cli_policy_training_status_accepts_agent_alias`.
  - RED result: `cargo test test_cli_policy_training_status_accepts_agent_alias -- --nocapture` failed with `E0026` because `Commands::PolicyTrainingStatus` had no `agent` field.
  - Fix: added `--agent` alias to `Commands::PolicyTrainingStatus` and routed it through existing `resolve_output_format(&output_format, compact, agent, human)`.
- Verification:
  - `cargo check --bin ict-engine` passed after a long compile.
  - `cargo run --quiet -- policy-training-status --help` now shows `--agent` and the help text lists `--compact`, `--agent`, and `--human` aliases.
  - `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-smoke-doc-verify-20260521 --agent` passed and emitted agent JSON.
  - `cargo test test_cli_policy_training_status_accepts_agent_alias -- --nocapture` passed: 1 matching `src/main.rs` test passed.
- Updated `support/docs/command-output-contract.md`:
  - `policy-training-status` is now marked as meeting the alias contract.
  - Remaining known output gaps are `artifact-status`, `artifact-lineage`, `artifact-diff`, and `pre-bayes-status` agent mode.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Focused code compile and test passed for the policy-training alias; previous full Rust gates are older | focused_pass | Re-run full Rust gates after output/architecture code slices settle |
| P0 loop truth / validation contract | Smoke surfaces pass; no non-empty structural path-ranking validation state proved in this loop | proved_surface_presence | Build or reuse a non-empty state to prove production validation counters |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | `main.rs` grew by the alias test/field; still far above target | contradicted | Extract ranker/output command helpers out of `main.rs` |
| P1 human output consistency | `policy-training-status --agent` alias fixed and verified; command-output contract updated | partial_fix | Patch artifact/pre-bayes output gaps or document intentional exceptions with tests |
| P1 first-run product path | Consumer/contributor quickstarts exist, README links them, smoke/provider probes passed | implemented_partially_verified | Public `analyze-live` remains provider/network-dependent; local cleaned-data flow remains placeholder-command documented |
| P1 smoke acceptance script | Script exists and passed syntax plus live smoke earlier this turn | implemented_verified_zero_config | Decide whether to add optional/full checks for factor-research/export or keep as fast first-run smoke |
| P1 Python script governance | `support/scripts/SCRIPTS.md` exists and classifies current script families without moving active scripts | implemented_doc_only | Add `script_manifest.json` or tests only if this becomes a hard gate |
| P1 error message contract | SPY analyze-live failure paths are clear; broader missing-file cases not reverified | weak_partial | Probe missing-file cases after output contract code gaps |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` exists and is linked from README | implemented_doc_only | Still need release/readiness clean-export process before any release claim |

Next audit loop:

1. Probe `artifact-status`, `artifact-lineage`, and `artifact-diff` runtime output shape, then patch the smallest shared output-format gap.
2. Re-run `cargo fmt --check`, scoped tests, `python3 support/scripts/help_audit.py`, smoke script, and diff checks.
3. Start a `main.rs` extraction batch once output aliases stop increasing line count.

### Live Audit Loop - 2026-05-21 20:58 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. `pre-bayes-status --agent`
is now fixed and verified, but artifact output modes, broader error-message
checks, non-empty production validation proof, and `main.rs` reduction remain
open.

Evidence gathered this loop:

- Re-read authority surfaces before work: `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`,
  installed runtime skill
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`,
  and this plan.
- Shared worktree remains dirty with active TOMAC/Board B process
  `10887` running under `/tmp/ict-engine-tomac-nq-bidir-opening-drive-twoleg-clean-downstream-20260521T2112+0800`;
  this slice avoided those artifacts.
- Targeted TDD slice: `pre-bayes-status --agent` alias.
  - RED test added: `test_cli_pre_bayes_status_accepts_agent_alias`.
  - RED result: `cargo test test_cli_pre_bayes_status_accepts_agent_alias -- --nocapture`
    failed with `E0026` because `Commands::PreBayesStatus` had no `agent`
    field.
  - Fix: added `--agent` alias to `Commands::PreBayesStatus` and routed it
    through existing `resolve_output_format(&output_format, compact, agent,
    human)`, preserving `OutputFormat::Agent => "json"` for the existing
    Pre-Bayes output renderer.
  - Compile also exposed adjacent Auto-Quant alias destructuring gaps where
    `auto-quant-status` and `auto-quant-futures-cost` already had `agent`
    parser fields but dispatch ignored them. Those dispatch paths now route
    through the same resolver and keep `Agent => "json"`.
- Verification:
  - `cargo test test_cli_pre_bayes_status_accepts_agent_alias -- --nocapture`
    passed: 1 matching `src/main.rs` test passed.
  - `cargo run --quiet -- pre-bayes-status --help` now shows `--agent` and the
    help text lists `compact, agent, or human`.
  - `cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-smoke-doc-verify-20260521 --agent`
    passed and emitted JSON-compatible agent output with `gate_status=pass_hard`.
  - `cargo run --quiet -- auto-quant-status --agent` passed and emitted JSON.
  - `cargo run --quiet -- auto-quant-futures-cost --symbol NQ --price 22000 --agent`
    passed and emitted JSON.
  - `cargo fmt --check` passed after formatting the new test.
  - `cargo check --bin ict-engine` passed.
  - `python3 -m py_compile support/scripts/help_audit.py && python3 support/scripts/help_audit.py`
    passed with `command_count=53`, no missing help, no help errors, and no
    market-bias hits.
  - `bash -n support/scripts/smoke_acceptance.sh` passed.
  - `STATE_DIR=/tmp/ict-engine-smoke-prebayes-agent-20260521 support/scripts/smoke_acceptance.sh`
    passed.
  - `git diff --check -- src/main.rs support/docs/command-output-contract.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md support/scripts/help_audit.py support/scripts/smoke_acceptance.sh`
    passed.
- Updated `support/docs/command-output-contract.md`:
  - `pre-bayes-status` is now marked as meeting the alias contract.
  - Added `auto-quant-status` and `auto-quant-futures-cost` to the verified
    matrix as meeting the contract.
  - Remaining known output gaps are `artifact-status`, `artifact-lineage`, and
    `artifact-diff`.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Focused test and runtime probes passed for the Pre-Bayes/Auto-Quant alias slice; previous full Rust gates are older | focused_pass | Re-run full Rust gates after output/architecture code slices settle |
| P0 loop truth / validation contract | Smoke surfaces pass; no non-empty structural path-ranking validation state proved in this loop | proved_surface_presence | Build or reuse a non-empty state to prove production validation counters |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | Alias tests/fields grew `main.rs`; reduction remains contradicted | contradicted | Extract ranker/output command helpers out of `main.rs` |
| P1 human output consistency | `pre-bayes-status --agent` fixed and command-output contract updated | partial_fix | Patch artifact output gaps or document intentional exceptions with tests |
| P1 first-run product path | Consumer/contributor quickstarts exist, README links them, smoke/provider probes passed | implemented_partially_verified | Public `analyze-live` remains provider/network-dependent; local cleaned-data flow remains placeholder-command documented |
| P1 smoke acceptance script | Script exists and passed syntax plus live smoke earlier | implemented_verified_zero_config | Decide whether to add optional/full checks for factor-research/export or keep as fast first-run smoke |
| P1 Python script governance | `support/scripts/SCRIPTS.md` exists and classifies current script families without moving active scripts | implemented_doc_only | Add `script_manifest.json` or tests only if this becomes a hard gate |
| P1 error message contract | SPY analyze-live failure paths are clear; broader missing-file cases not reverified | weak_partial | Probe missing-file cases after output contract code gaps |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` exists and is linked from README | implemented_doc_only | Still need release/readiness clean-export process before any release claim |

Next audit loop:

1. Run scoped verification: `cargo fmt --check`, focused tests, help audit,
   smoke script, and diff checks.
2. Start a `main.rs` extraction batch once output aliases stop increasing line
   count.

### Live Audit Loop - 2026-05-21 21:28 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. The known artifact output-mode
gap is fixed and runtime-probed, but full-audit completion is still contradicted
by `main.rs` growth, missing non-empty production validation proof, broader
error-message checks, and clean-export/release evidence.

Evidence gathered this loop:

- Re-read authority surfaces before work: `~/.hermes/routing/skill-router.md`,
  `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`,
  installed runtime skill
  `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`,
  and this plan.
- Memory quick pass only reinforced two existing constraints: keep `ict-engine`
  work scoped to the true repo root and continue modularizing `main.rs` rather
  than treating distribution as the fix.
- Shared worktree remains dirty and active TOMAC/Board B processes are running
  under `/tmp`; this slice avoided those lanes.
- Targeted TDD slice: artifact read-only output aliases.
  - RED test added: `test_cli_artifact_commands_accept_output_aliases`.
  - RED result: `cargo test test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    failed with `E0026` because `Commands::ArtifactStatus`,
    `Commands::ArtifactLineage`, and `Commands::ArtifactDiff` had no alias
    fields.
  - Fix: added `--output-format json|compact|agent|human` plus `--compact`,
    `--agent`, and `--human` aliases to `artifact-status`,
    `artifact-lineage`, and `artifact-diff`.
  - Output rendering stays in `src/application/artifacts.rs`, not in
    `main.rs`: JSON and agent remain structured, compact emits compact JSON,
    and human emits concise one-line summaries.
  - Touched files in this slice:
    - `src/main.rs`
    - `src/status_command.rs`
    - `src/application/artifacts.rs`
    - `support/docs/command-output-contract.md`
    - this plan
- Verification so far:
  - `cargo test test_cli_artifact_commands_accept_output_aliases -- --nocapture`
    passed: 1 matching `src/main.rs` test passed.
  - `cargo run --quiet -- artifact-status --help`,
    `cargo run --quiet -- artifact-lineage --help`, and
    `cargo run --quiet -- artifact-diff --help` now show the shared
    output-format and alias flags.
  - `cargo run --quiet -- artifact-status --symbol DEMO --state-dir /tmp/ict-engine-smoke-prebayes-agent-20260521 --agent`
    passed and emitted structured artifact JSON.
  - `cargo run --quiet -- artifact-lineage --symbol DEMO --state-dir /tmp/ict-engine-smoke-prebayes-agent-20260521 --human`
    passed with `artifact-lineage summaries=5`.
  - A fresh two-analyze demo state at
    `/tmp/ict-engine-artifact-output-verify-20260521` proved human runtime
    readbacks:
    - `artifact-status --kind pending_update --human` printed 2 pending entries.
    - `artifact-lineage --artifact-id pending-update:DEMO:analyze:v2 --human`
      printed focused node/edge counts.
  - `artifact-diff --left-artifact-id pending-update:DEMO:analyze:v1 --right-artifact-id pending-update:DEMO:analyze:v2 --human`
      printed same-kind diff summary.
  - `cargo fmt --check` passed.
  - `cargo check --bin ict-engine` passed.
  - `python3 -m py_compile support/scripts/help_audit.py && python3 support/scripts/help_audit.py`
    passed with `command_count=53`; artifact commands now report higher option
    counts and no missing help/errors.
  - `bash -n support/scripts/smoke_acceptance.sh` passed.
  - `STATE_DIR=/tmp/ict-engine-smoke-artifact-output-20260521 support/scripts/smoke_acceptance.sh`
    passed.
  - `git diff --check -- src/main.rs src/status_command.rs src/application/artifacts.rs support/docs/command-output-contract.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md support/scripts/help_audit.py support/scripts/smoke_acceptance.sh`
    passed.
- Updated `support/docs/command-output-contract.md`:
  - `artifact-status`, `artifact-lineage`, and `artifact-diff` are now marked
    as meeting the shared output-format contract.
  - The remaining known gap is that the matrix is still high-value-command
    scoped, not a fully generated audit over every command.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Focused artifact alias test, `cargo check --bin ict-engine`, `cargo fmt --check`, help audit, smoke, and diff-check passed for this slice | focused_pass | Re-run full Rust gates after architecture/code slices settle |
| P0 loop truth / validation contract | Smoke surfaces pass; no non-empty structural path-ranking validation state proved in this loop | proved_surface_presence | Build or reuse a non-empty state to prove production validation counters |
| P0 external ranker contract test | Rust CLI export/apply smoke and Python hotplug unit contract passed earlier | partial_live_proof | Add/run full fixture chain with trainer scorer output and register/enable runtime if this becomes a release gate |
| P0 `src/main.rs` reduction | Output aliases added more CLI fields/tests; reduction remains contradicted | contradicted | Start extraction batch next; move command/report rendering out of `main.rs` |
| P1 human output consistency | Artifact status/lineage/diff aliases and human summaries now exist; help/runtime/focused tests passed | implemented_verified_artifact_slice | Continue with generated full command matrix later |
| P1 first-run product path | Consumer/contributor quickstarts exist, README links them, smoke/provider probes passed | implemented_partially_verified | Public `analyze-live` remains provider/network-dependent; local cleaned-data flow remains placeholder-command documented |
| P1 smoke acceptance script | Script exists and passed syntax plus live smoke earlier | implemented_verified_zero_config | Re-run after code changes |
| P1 Python script governance | `support/scripts/SCRIPTS.md` exists and classifies current script families without moving active scripts | implemented_doc_only | Add `script_manifest.json` or tests only if this becomes a hard gate |
| P1 error message contract | SPY analyze-live failure paths are clear; broader missing-file cases not reverified | weak_partial | Probe missing-file cases after output contract code gaps |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` exists and is linked from README | implemented_doc_only | Still need release/readiness clean-export process before any release claim |

Next audit loop:

1. Start a `main.rs` extraction batch; output aliases have stopped exposing new
   contract gaps, but they increased the entrypoint size.
2. Continue the broader audit with error-message probes and non-empty production
   validation proof.

### Live Audit Loop - 2026-05-21 17:36 +0800

Owner: Codex current turn.
Claim: continuing `/tmp/ict-engine-agent-claims/full-audit/20260521T165608+0800-codex-full-audit-plan-refresh.claim`.

Current answer to "is this 100% complete?": no. Fresh current-tree evidence contradicts completion.

Evidence gathered this loop:

- Re-read authority surfaces before work: `~/.hermes/routing/skill-router.md`, `~/.hermes/routing/project-router.md`, repo `CLAUDE.md`, repo `AGENT.md`, installed runtime skill `/Users/thrill3r/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`, and this plan.
- Shared worktree is still highly dirty; active Board B/TOMAC processes are running, so this lane remains plan/audit-scoped unless a narrow fix is explicitly non-conflicting.
- `wc -l src/main.rs` reports `19039`, so the entrypoint reduction is still contradicted.
- Missing deliverables verified by file existence probe:
  - `support/scripts/smoke_acceptance.sh`
  - `support/docs/consumer-quickstart.md`
  - `support/docs/contributor-quickstart.md`
  - `support/docs/command-output-contract.md`
  - `support/scripts/SCRIPTS.md`
  - `CONTRIBUTING.md`
- Targeted validation test command failed to compile:
  - Command: `cargo test structural_path_ranking_status_splits_target_rows_from_feedback_observations -- --nocapture`
  - Result: exit `101`
  - Blocker: `src/state/persistence.rs:691:39` cannot find `StructuralFeedbackRefs`; compiler suggests importing `crate::state::StructuralFeedbackRefs`.
  - Consequence: the P0 validation split may exist in source, but current test evidence is `contradicted` until the compile blocker is fixed and the targeted test passes.
- CLI help probes completed, but emitted warnings:
  - `cargo run --quiet -- policy-training-status --help` exposes `--output-format` and `--human`, but no `--agent` alias even though `agent` is accepted through `--output-format`.
  - `cargo run --quiet -- export-structural-path-ranking-target --help` exposes only `--symbol` and `--state-dir`; no `--output-format`, `--human`, `--compact`, or `--agent`.
  - `cargo run --quiet -- apply-structural-path-ranking-external-scores --help` exposes only `--symbol`, `--state-dir`, and `--scores-file`; no `--output-format`, `--human`, `--compact`, or `--agent`.
  - Current warnings include unused `workflow_status_needs_provider_surface`, unused `command_status_with_timeout`, unused Deribit greeks fields, unused `pseudo_inverse`, and unused `main.rs` imports. They are not yet `-D warnings` failures in these help probes but must be cleared before claiming Clippy readiness.
- Narrow compile fix applied:
  - Root cause: `StructuralFeedbackRefs` had been removed from the module-level import in `src/state/persistence.rs`, while the local test module still constructed it without a test-scope import.
  - Patch: add `StructuralFeedbackRefs` to the existing `use crate::state::types::{...}` list inside the test module only.
  - Verification: `cargo test structural_path_ranking_status_splits_target_rows_from_feedback_observations -- --nocapture` passed; 1 matching lib test passed, 0 failed.
  - Formatting: `rustfmt --edition 2021 --check src/state/persistence.rs` passed after formatting the touched file.
- Demo CLI readback:
  - Command: `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --human`
  - Result: passed and wrote workflow state under `/tmp`.
  - Human readback: `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --human` printed `Ranker validation: ... raw_scored_mature=0/0 production_validation=0/0 observation_validation=0/0 ready=false`.
  - JSON readback: `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-loop-20260521-1736 --output-format json` contains both `structural_path_ranking_validation.target_row_validation` and `structural_path_ranking_validation.feedback_observation_validation`.
  - Limitation: the demo state has no structural path-ranking target export, so this proves surface presence, not production validation maturity.
- External ranker contract subset:
  - `python3 -m pytest support/scripts/auto_quant_external/tests/test_path_ranker_hotplug.py -q` failed immediately because the active Python 3.13 environment has no `pytest` module.
  - Equivalent unittest route passed: `python3 -m unittest support.scripts.auto_quant_external.tests.test_path_ranker_hotplug -v` ran 13 tests, 0 failures.
  - Covered behaviors include direct-model artifact contract, CatBoost companion preference, ranking-mode candidate-set grouping, direct fallback when CatBoost cannot fit, runtime artifact registration command shape, state-local relative artifact URI, and reuse-model apply flow.
  - Limitation: this is a mocked/unit contract subset. It does not prove a full live Rust export -> Python scorer -> Rust apply/register/enable runtime chain against a fresh real state.

Updated gap ledger:

| Item | Current evidence | Status | Next proof/action |
|---|---|---|---|
| P0 compile/test health | Missing `StructuralFeedbackRefs` import was patched locally; targeted test now passes and touched file is rustfmt-clean | proved_targeted | Run wider `cargo test` / `cargo check --all-targets` later before any completion claim |
| P0 loop truth / validation contract | Focused split test passes; demo `policy-training-status` human/JSON readback exposes target-row and feedback-observation surfaces | proved_surface_presence | Still need a non-empty policy-training state readback before marking production validation complete |
| P0 external ranker contract test | `pytest` is unavailable, but `python3 -m unittest support.scripts.auto_quant_external.tests.test_path_ranker_hotplug -v` passed 13/13 mocked/unit contract tests | proved_subset | Add/run a full fixture chain using current Rust binary and Python scorer |
| P0 `src/main.rs` reduction | `19039` lines | contradicted | Extract command batches only after current compile blocker is fixed; keep `main.rs` shrinking as a measurable gate |
| P1 human output consistency | Real help shows ranker export/apply commands lack output-format/human surfaces; `policy-training-status` lacks `--agent` alias | incomplete | Add a command-output matrix doc from help output, then patch read-only ranker commands |
| P1 first-run product path | Consumer/contributor quickstarts absent | missing_evidence | Create docs after exact smoke commands are reverified |
| P1 smoke acceptance script | `support/scripts/smoke_acceptance.sh` absent | missing_evidence | Add script after smoke chain is proven against current binary |
| P1 Python script governance | `support/scripts/SCRIPTS.md` absent | missing_evidence | Classify scripts without moving active experiment code |
| P1 error message contract | Not reverified in this loop | weak_evidence | Probe missing-file cases after compile health is restored |
| P2 agent/contributor truth map cleanup | Not reverified in this loop | weak_evidence | Compare `AGENT.md`, `support/docs/factor-catalog.md`, and `FactorCategory` variants |
| P2 contribution/release cleanup | `CONTRIBUTING.md` absent | missing_evidence | Draft public contributor flow after verification gates settle |

Next audit loop:

1. Build a real command-output matrix from help output for read-only status/export commands.
2. Patch the ranker export/apply output-format gap or document why those commands are intentionally artifact-only.
3. Add/run a full fixture chain for Rust export -> Python scorer -> Rust apply/register/enable runtime.
4. Continue widening only after each probe has a current evidence row here.

---

## P0 - Loop Truth / Validation Contract

### Problem

`policy-training-status` mixes row-level target maturity with observation-level feedback truth. Prior work recorded 30 structural-feedback records, but status can still show low `raw_scored_mature` because the exported structural path target is de-duplicated by candidate/path rows.

### Risk

Users and agents can overclaim that the external ranker is validated when only replay observations exist, or underclaim when feedback exists but row counters stay low.

### Solution

Split the status surface into two explicitly named metric groups:

- `target_row_validation`: current row-level maturity over `structural_path_ranking_target_history.*`
- `feedback_observation_validation`: observation-level maturity over structural feedback records in `learning_state.feedback_history`

### Steps

- [x] Add a failing Rust test for `policy-training-status` with repeated feedback observations but few distinct target rows.
  - File: `src/policy_training_command.rs` or the library module that builds the status payload.
  - Expected: status exposes both row-level and observation-level counters.
- [x] Add a helper that counts eligible structural-feedback observations separately from target rows.
  - Source: `learning_state.feedback_history`
  - Filter: structural path-ranking / structural-feedback source records only.
- [x] Update `policy-training-status --human` to print both groups.
  - Example: `target_rows raw_scored_mature=2/30 | observations mature=30/30`
- [x] Update JSON output with stable keys:
  - `target_row_validation.raw_scored_mature`
  - `target_row_validation.production_validation`
  - `feedback_observation_validation.mature_observations`
  - `feedback_observation_validation.outcome_distribution`
- [x] Update `support/docs/plans/2026-05-09-vrp-v2-loop-handoff-todo.md` to stop using one counter for both meanings.
- [x] Verify:
  - `cargo test policy_training -- --nocapture`
  - `cargo check --all-targets`
  - `./target/debug/ict-engine policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-demo --human`
  - Fresh continuation evidence on 2026-05-22:
    - `CARGO_TARGET_DIR=/tmp/ict-engine-proof-target cargo test --lib structural_path_ranking_status_splits_target_rows_from_feedback_observations -- --nocapture`
      -> `1 passed; 0 failed`.
    - `CARGO_TARGET_DIR=/tmp/ict-engine-proof-target cargo test --lib policy_training_status -- --nocapture`
      -> `4 passed; 0 failed`.
    - `CARGO_TARGET_DIR=/tmp/ict-engine-proof-target cargo test --lib structural_path_ranking_target_training_status_reports_production_validation_ready -- --nocapture`
      -> `1 passed; 0 failed`.
    - `CARGO_TARGET_DIR=/tmp/ict-engine-proof-target cargo check --all-targets`
      -> `Finished dev profile [unoptimized + debuginfo] target(s) in 53.46s`.
    - Scope note: this verifies the counter split and fixture
      production-ready status; it still does not prove release readiness or a
      live production trading validation packet.

---

## P0 - External Ranker Contract Test

### Problem

The external path-ranking bridge exists, but Rust export/apply/register/runtime and Python trainer fallback are not covered by one small end-to-end fixture.

### Risk

Schema drift can silently break the closed loop. Python may generate scores that Rust accepts incorrectly, or Rust may export columns the trainer no longer handles.

### Solution

Create a minimal fixture-driven contract test for:

`export target -> Python fallback scorer -> apply scores -> register artifact -> enable runtime -> status reflects runtime source`

### Steps

- [x] Create a tiny fixture target CSV under `tests/fixtures/policy_training/structural_path_ranking_target.csv`.
- [x] Add a Python test for `pandas_path_ranker_trainer.py --apply` that asserts output row count equals target row count even when no rows are mature.
  - File: `support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
  - The test now uses the shared fixture target and asserts the fallback
    scorer preserves the fixture candidate/path and emits
    `weighted_feature_sum_v1`.
- [x] Add Rust integration test for `apply-structural-path-ranking-external-scores` using the fixture scores.
  - File: `tests/structural_path_ranker_contract.rs`
  - Fixture score CSV:
    `tests/fixtures/policy_training/structural_path_ranking_scores.csv`
- [x] Assert required columns and error messages for missing/malformed target CSV.
  - Python trainer checks `candidate_set_id` and `path_id` before scoring.
- [x] Assert required columns and error messages for missing CSV / malformed score file on the Rust `apply-structural-path-ranking-external-scores` path.
  - Missing/malformed score-file errors now include the path, expected
    `candidate_set_id,path_id,raw_path_score` schema, and
    `export-structural-path-ranking-target` recovery command.
- [x] Verify:
  - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
  - `cargo test --test structural_path_ranker_contract -- --nocapture`
  - Shared-target Cargo lock was anomalous during the latest run; verified with
    isolated target:
    `CARGO_TARGET_DIR=/tmp/ict-engine-structural-ranker-contract-target cargo test --test structural_path_ranker_contract -- --nocapture`
  - Fresh continuation evidence on 2026-05-22:
    - `python3 -m unittest support/scripts/auto_quant_external/tests/test_path_ranker_contract.py`
      -> `3 tests; OK`.
    - `python3 -m unittest support.scripts.auto_quant_external.tests.test_path_ranker_hotplug -v`
      -> `13 tests; OK`.
    - `CARGO_TARGET_DIR=/tmp/ict-engine-proof-target cargo test --test structural_path_ranker_contract -- --nocapture`
      -> `7 passed; 0 failed`.
    - Environment note: the first verification attempt failed before running
      assertions because repo-local and `/tmp` Cargo targets hit `No space left
      on device`. Cleared only ephemeral `/tmp/ict-engine-*-target` Cargo build
      directories and re-ran the focused checks successfully.

---

## P0 - `src/main.rs` Reduction

### Problem

`src/main.rs` is ~14,797 lines. A guardrail doc already says not to add business logic there, but the current entrypoint remains the largest maintainability risk.

### Risk

New contributors patch the wrong layer. Reviewers cannot reason locally. Command changes cause accidental reporting/state regressions.

### Solution

Extract command bodies and DTO/report helpers into library/application modules while keeping `main.rs` as Clap declarations + dispatch only.

### Steps

- [x] Measure current `src/main.rs` line count and add it to `support/docs/main-rs-guardrails.md` as baseline debt.
  - 2026-05-22 measurement: `src/main.rs` = 19,202 lines.
- [ ] Pick one low-risk command first: `provider-status`, `artifact-status`, or `pre-bayes-status`.
- [ ] Add/redirect tests to the target library API before moving code.
- [ ] Move command body from `src/main.rs` to the existing `*_command.rs` or `src/application/*` module.
- [ ] Leave only argument matching and shell call in `main.rs`.
- [ ] Repeat in batches until `main.rs < 5000` lines.
- [ ] Verify every batch:
  - `cargo fmt --check`
  - `cargo check --all-targets`
  - `cargo test <moved_command_keyword>`

---

## P1 - Human Output Consistency

### Problem

Some commands support `--human`; some equivalent status/export commands do not. Example: `artifact-status --human` and `export-structural-path-ranking-target --human` reject the flag.

### Risk

Consumer UX feels inconsistent. Agent workflows must special-case JSON-only commands.

### Solution

Define a command output contract: every read-only status/export command supports `--output-format json|compact|agent|human`, or explicitly documents why not.

### Steps

- [x] Inventory all discovered commands and mark output support.
  - `support/scripts/help_audit.py` now derives output-mode support from real
    `--help` output for all 53 discovered top-level subcommands.
  - Fresh summary: 15 full output-mode surfaces, 6 partial surfaces, and 32
    commands with no output-mode flags.
- [x] Create `support/docs/command-output-contract.md` with command matrix.
  - Current matrix is based on real `--help` probes for high-value status/export commands.
  - It records remaining gaps instead of pretending the contract is fully implemented.
- [ ] Add `--human` to read-only commands first:
  - `artifact-status`
  - `artifact-lineage`
  - `artifact-diff`
  - `export-structural-path-ranking-target`
  - `apply-structural-path-ranking-external-scores`
- [ ] Add tests that unsupported flags fail only when intentionally unsupported.
- [ ] Verify:
  - `python3 support/scripts/help_audit.py`
  - `cargo test command_output_contract -- --nocapture`

---

## P1 - First-Run Product Path

### Problem

First-run docs are good, but real users still face too many paths: demo, cleaned JSON, TOMAC data, yfinance, Auto-Quant, provider harness, Python wrappers.

### Risk

Consumers can run a demo but fail to reach a useful real-data loop. They may also pollute repo-local `state/` by omitting `--state-dir`.

### Solution

Create one blessed consumer path and one blessed contributor path.

### Steps

- [x] Add `support/docs/consumer-quickstart.md` with exactly three flows:
  - demo: analyze + workflow-status
  - public data: provider-status + analyze-live/yfinance path
  - local cleaned data: analyze with explicit `--data-htf/mtf/ltf`
- [x] Add `support/docs/contributor-quickstart.md` with:
  - build/test commands
  - where to add code
  - where not to add code
  - how to run smoke acceptance
- [x] Change README to link to those two pages near the top.
- [x] Add warning text near state-dir docs: use `/tmp/...` for trials.
- [x] Verify by running only commands shown in `consumer-quickstart.md`.
  - Flow 1 demo loop passed under `/tmp/ict-engine-first-run`; post-analyze reruns exposed posterior/readback surfaces.
  - `support/scripts/smoke_acceptance.sh` passed as both direct executable and `bash support/scripts/smoke_acceptance.sh`.
  - Flow 2 provider-readiness commands passed, and bounded public `analyze-live --symbol NQ` exited `0` under `/tmp/ict-engine-live-nq`.
  - Flow 3 local cleaned-data command shape passed after substituting concrete `/tmp/my-data/{1d,1h,15m}.json` fixture copies.
  - Verification is observe/readback evidence only, not trade-readiness or release-readiness evidence.

---

## P1 - Smoke Acceptance Script

### Problem

`support/docs/smoke-acceptance.md` documents the main chain, but no single script enforces it.

### Risk

CI and contributors may pass unit tests while breaking the user-visible loop.

### Solution

Create `support/scripts/smoke_acceptance.sh` with a fast mode using demo/generated candles and explicit `/tmp` state.

### Steps

- [x] Create `support/scripts/smoke_acceptance.sh`.
  - Current implementation covers the `AGENT.md` zero-config chain and writes all output to `/tmp` by default.
  - Verified with `bash -n support/scripts/smoke_acceptance.sh`.
  - Verified with `STATE_DIR=/tmp/ict-engine-smoke-acceptance-verify-20260521 support/scripts/smoke_acceptance.sh`.
- [ ] Include optional/full checks only after the boundary is explicit:
  - Fast smoke already covers `ict-engine analyze --demo --human`, `ict-engine workflow-status --human`, and `ict-engine policy-training-status --agent`.
  - Fresh probes show `ict-engine export-structural-path-ranking-target --human` and `ict-engine policy-training-status --human` run after a demo analyze under `/tmp`.
  - `ict-engine factor-research --backend native --human` is stale and invalid; current help says public factor iteration is locked to Auto-Quant.
  - Default Auto-Quant `factor-research --human` is dependency/network-sensitive on this host because the GitHub URL rewrite sends the dependency clone over SSH.
  - Next valid action: design a separate manual/nightly Auto-Quant smoke with an explicit dependency or pre-seeded workspace strategy; keep the first-run script as the fast no-network consumer gate.
- [x] Make script refuse repo-local `state/` unless `ICT_ENGINE_ALLOW_REPO_STATE=1` is set.
  - Verified with `python3 -m unittest support/scripts/tests/test_smoke_acceptance.py`.
  - Verified with `STATE_DIR=state OUT_DIR=/tmp/ict-engine-smoke-state-guard-manual-out bash support/scripts/smoke_acceptance.sh`.
  - The guard exits before Cargo with code `2` and allows repo-local state only when `ICT_ENGINE_ALLOW_REPO_STATE=1`.
- [x] Add README command:
  - `bash support/scripts/smoke_acceptance.sh`
  - Verified with `rg -n "bash support/scripts/smoke_acceptance.sh" README.md`.
- [ ] Optional CI job: manual or nightly only, not default PR blocker until runtime is stable.

---

## P1 - Python Script Governance

### Problem

Python scripts include public wrappers, active external trainer code, archived experiments, paper2code prototypes, and local utilities in one broad tree.

### Risk

Consumers cannot tell stable CLI helpers from research prototypes. Contributors may depend on archived scripts accidentally.

### Solution

Add a script classification manifest and enforce wrapper behavior.

### Steps

- [x] Create `support/scripts/SCRIPTS.md` with groups:
  - public wrappers
  - active external bridge
  - Auto-Quant strategies
  - archived experiments
  - paper2code prototypes
  - local utilities
- [x] Add `support/scripts/script_manifest.json` with `name`, `stability`, `entrypoint`, `safe_default`, `requires_data`, `test_command`.
- [x] Extend `support/scripts/help_audit.py` to verify public wrappers default to help/no execution.
  - Fixed false-positive command discovery (`command_count=0`) and cargo-run help stalls.
  - Current result: `command_count=53`, no missing descriptions, no command help errors, no market-bias hits.
- [x] Add pytest-compatible standard-library coverage for public wrappers:
  - `search_local.py`
  - `search_cluster.py`
  - `evaluate_bottleneck.py`
  - `research_verdict.py`
  - Verification: `python3 -m unittest support/scripts/tests/test_public_wrappers.py`
    ran 4 tests and passed.
- [x] Verify script manifest:
  - `python3 support/scripts/check_script_manifest.py`
  - `python3 -m py_compile support/scripts/check_script_manifest.py support/scripts/tests/test_public_wrappers.py`
  - `python3 -m json.tool support/scripts/script_manifest.json >/dev/null`
- [ ] Verify:
  - `python3 -m pytest support/scripts/research/tests support/scripts/auto_quant_external/tests -q`
  - Current blocker: `python3 -m pytest --version` exits 1 because pytest is not
    installed in this local Python environment.

---

## P1 - Error Message Contract

### Problem

Several CLI failures expose raw IO errors. Example: applying nonexistent external scores prints only `No such file or directory`.

### Risk

Users do not know required schema, command order, or recovery path.

### Solution

Wrap high-friction IO errors with context and next command hints.

### Steps

- [x] Add tests for missing file errors in the listed high-friction paths:
  - `apply-structural-path-ranking-external-scores`
    - Covered for missing/malformed score files by
      `tests/structural_path_ranker_contract.rs`.
  - `register-structural-path-ranking-trainer-artifact`
    - Covered for missing target export, malformed target summary JSON, and
      malformed explicit-family trainer artifact JSON by
      `tests/structural_path_ranker_contract.rs`.
  - `factor-research --data`
    - Covered for missing requested data in Auto-Quant handoff notes and
      `factor-research --human` rendering.
  - `analyze --data-*`
    - Covered for `--data-htf`; helper is shared by `--data-mtf` and
      `--data-ltf`.
- [x] Replace raw errors with `anyhow::Context` messages on the listed paths.
- [x] Include expected schema or recovery command where relevant.
- [x] Verify listed-path output contains:
  - missing path
  - expected file type
  - next command or doc link
- [ ] Continue broader command-output matrix for other raw IO paths.

### 2026-05-22 continuation - generated command-output matrix

Current answer to "is this 100% complete?": no. The full top-level command
inventory now exists, but the policy classification/remediation for every
`none` surface is still open.

Evidence:

- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `python3 support/scripts/help_audit.py` exited 0 and reported:
  - `command_count=53`
  - `commands_with_full_output_modes=15`
  - `commands_with_partial_output_modes=6`
  - `commands_with_no_output_modes=32`
  - `commands_with_missing_help=0`
  - `commands_with_help_errors=0`
  - `commands_with_market_bias=0`
- `support/docs/command-output-contract.md` was refreshed from the generated
  matrix and now records every discovered top-level command, not only the prior
  high-value subset.
- Added alias parity for four two-mode asset/intake commands:
  `factor-candidate-packs`, `factor-candidate-admission-targets`,
  `regime-confidence-assets`, and `factor-asset-closure-intake`. For these
  commands, `--human` maps to existing human output and `--agent`/`--compact`
  map to existing JSON output.
- Post-patch help audit against `/tmp/ict-engine-command-matrix-target/debug/ict-engine`
  reported:
  - `commands_with_full_output_modes=19`
  - `commands_with_partial_output_modes=2`
  - `commands_with_no_output_modes=32`
- Added `validate-market-state` output alias coverage and a tested exception:
  human/compact outputs are supported through `--output-format`, `--human`, and
  `--compact`; structured `json`/`agent` requests now fail with a clear message
  until a stable validation-result schema is added.
- Post-`validate-market-state` help audit against
  `/tmp/ict-engine-command-matrix-target/debug/ict-engine` reported:
  - `commands_with_full_output_modes=20`
  - `commands_with_partial_output_modes=1`
  - `commands_with_no_output_modes=32`
- Added `provider-status` output-format coverage:
  `--output-format json|compact|agent|jsonl|human` is now accepted;
  `--human` maps to existing compact human output and `--jsonl` remains
  available as both an alias and output-format value.
- Post-`provider-status` help audit against
  `/tmp/ict-engine-command-matrix-target/debug/ict-engine` reported:
  - `commands_with_full_output_modes=21`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=32`
- Verification for the `provider-status` slice:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine provider_status -- --nocapture` passed 2 tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
  - `cargo fmt --check` passed.
  - `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
  - `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
  - `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported `status=pass`.
  - `git diff --check` over the touched command-output slice passed.
- Verification for this slice:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine validate_market_state -- --nocapture` passed 7 tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 61 tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
  - `cargo fmt --check` passed.
  - `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
  - `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
  - `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported `status=pass`.
  - `git diff --check` over the touched slice passed.

### 2026-05-22 continuation - pre-bayes-diff output alias slice

Current answer to "is this 100% complete?": no. One more read-only report
surface was removed from the `none` bucket, but 31 commands still need explicit
classification or remediation, and the broader raw IO/error matrix remains
open.

Change:

- Added full output-mode coverage for `pre-bayes-diff`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON payload.
- `human` prints a compact operator summary with gate, policy, regime,
  confidence, and bridge-diff field count.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  22 full surfaces, 0 partial surfaces, 31 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_more_status_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `PreBayesDiffArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_more_status_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after applying `cargo fmt` to the touched Rust files.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=22`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=31`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 31 `none` commands.
- Likely read-only/report candidates still needing inspection include
  `factor-mutation-status`, `factor-autoresearch-status`, `research-verdict`,
  `evidence-quality-breakdown`, `market-data-harness plan`, and
  `factor-pipeline-debug`.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - factor-mutation-status output alias slice

Current answer to "is this 100% complete?": no. One more read-only status
surface was removed from the `none` bucket, but 30 commands still need explicit
classification/remediation, and broad raw IO/error plus full-goal validation
remain open.

Change:

- Added full output-mode coverage for `factor-mutation-status`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON payload.
- `human` prints a compact operator summary with symbol, total run count,
  accepted run count, latest mutation id, and recommended-focus item count.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  23 full surfaces, 0 partial surfaces, 30 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `FactorMutationStatusArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after applying `cargo fmt` to the touched Rust files.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=23`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=30`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 30 `none` commands.
- Likely read-only/report candidates still needing inspection include
  `factor-autoresearch-status`, `research-verdict`,
  `evidence-quality-breakdown`, `market-data-harness plan`, and
  `factor-pipeline-debug`.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - factor-autoresearch-status output alias slice

Current answer to "is this 100% complete?": no. One more read-only status
surface was removed from the `none` bucket, but 29 commands still need explicit
classification/remediation, and broader raw IO/error plus full-goal validation
remain open.

Change:

- Added full output-mode coverage for `factor-autoresearch-status`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON payload.
- `human` prints a compact operator summary with symbol, effective status,
  session count, attempt count, best attempt id, and derived warning count.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  24 full surfaces, 0 partial surfaces, 29 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `FactorAutoresearchStatusArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after applying `cargo fmt` to the touched Rust files.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=24`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=29`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 29 `none` commands.
- Likely read-only/report candidates still needing inspection include
  `research-verdict`, `evidence-quality-breakdown`, `market-data-harness plan`,
  and `factor-pipeline-debug`.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - research-verdict output alias slice

Current answer to "is this 100% complete?": no. One more read-only report
surface was removed from the `none` bucket, but 28 commands still need explicit
classification/remediation, and broader raw IO/error plus full-goal validation
remain open.

Change:

- Added full output-mode coverage for `research-verdict`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON-compatible
  report payload.
- `human` prints a compact verdict summary with symbol, stop/continue decision,
  bottleneck, next experiment, and contamination flag.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  25 full surfaces, 0 partial surfaces, 28 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `ResearchVerdictArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after applying `cargo fmt` to the touched Rust files.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=25`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=28`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 28 `none` commands.
- Likely read-only/report candidates still needing inspection include
  `evidence-quality-breakdown`, `market-data-harness plan`, and
  `factor-pipeline-debug`.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

Remaining gaps:

- Classify the 28 remaining `none` commands into intentional mutating/bootstrap surfaces
  versus read-only/report commands that should adopt output aliases.
- No discovered command remains partial by help-derived output-mode support.
  The remaining command-output work is classification/remediation of the 28
  `none` surfaces and the broader raw IO/error matrix.
- Continue the broader raw IO/error matrix; this slice only covers help-derived
  output-mode support.

### 2026-05-22 continuation - evidence quality output aliases

Current answer to "is this 100% complete?": no. This slice moved one more
read-only/report command out of the no-output-mode bucket, but the broader audit
still has open command classification, raw IO/error matrix, production
validation, and `main.rs` reduction gaps.

Change:

- Added full output-mode coverage for `evidence-quality-breakdown`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON-compatible
  evidence-quality report payload.
- `human` prints a compact evidence-quality summary with symbol, gate status,
  score, hard/neutralized gaps, soft-evidence divergence count, and bridge entry
  quality.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  26 full surfaces, 0 partial surfaces, 27 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `EvidenceQualityBreakdownArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_status_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=26`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=27`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 27 `none` commands.
- Likely read-only/report candidates still needing inspection include
  `market-data-harness plan` and `factor-pipeline-debug`.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - factor pipeline debug output aliases

Current answer to "is this 100% complete?": no. This slice moved another
read-only/report command out of the no-output-mode bucket, but `market-data-harness`
still needs action-aware classification and the broader audit gates remain open.

Change:

- Added full output-mode coverage for `factor-pipeline-debug`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON-compatible
  pipeline debug payload.
- `human` prints a compact pipeline summary with symbol, factor, objective,
  latest direction, confidence, gate status, and soft-evidence divergence count.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  27 full surfaces, 0 partial surfaces, 26 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `FactorPipelineDebugArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after `cargo fmt` fixed a formatting-only diff in `src/application/factor_pipeline_debug.rs`.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=27`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=26`
  - `status=pass`

Remaining gaps:

- Classify/remediate the remaining 26 `none` commands.
- Inspect `market-data-harness` action semantics next; `plan` is read-only but
  `fetch` performs provider work and can fail partially after printing a bundle.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - market data harness output aliases

Current answer to "is this 100% complete?": no. This slice closed the last
obvious read-only/report candidate from the current help matrix, but the
remaining `none` commands still need intentional-exception classification or
targeted remediation, and the broader raw IO/error matrix remains open.

Change:

- Added full output-mode coverage for `market-data-harness`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON-compatible
  output for both `--action plan` and `--action fetch`.
- `human` prints action-aware summaries: plan task/missing-role/warning/provider
  counts, or fetch task/result/failure/missing-role/warning counts.
- Preserved the existing fetch failure contract: fetch still collects failures
  after output and exits nonzero when provider/task failures exist.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  28 full surfaces, 0 partial surfaces, 25 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `MarketDataHarnessArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_market_data_and_debug_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=28`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=25`
  - `status=pass`

Remaining gaps:

- Classify the remaining 25 `none` commands as intentional mutating/bootstrap
  surfaces or patch any read-only/report commands that remain hidden in that set.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - env output aliases

Current answer to "is this 100% complete?": no. This slice closed another
read-only/status surface and reduced environment-value leakage risk in human
mode, but remaining `none` commands still need classification/remediation and
the broader raw IO/error matrix remains open.

Change:

- Added full output-mode coverage for `env`: `--output-format
  json|compact|agent|human`, plus `--compact`, `--agent`, and `--human` aliases.
- `json`, `compact`, and `agent` preserve a redacted JSON-compatible environment
  report.
- `human` summarizes variable count, set/unset count, state dir env var, and
  default state dir without printing environment values.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  29 full surfaces, 0 partial surfaces, 24 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_env_command_parses -- --nocapture` failed before implementation because `Commands::Env` was a unit variant, not an args-bearing variant:
  `E0532 expected tuple struct or tuple variant, found unit variant Commands::Env`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_env_command_parses -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after `cargo fmt` fixed import ordering in `src/env_command.rs`.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=29`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=24`
  - `status=pass`

Remaining gaps:

- Inspect `auto-quant-adoption-review` next; it appears read-only/report-like.
- Classify the other remaining `none` commands as mutating/bootstrap/import
  intentional exceptions or patch any remaining read-only/report surfaces.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - auto quant adoption review output aliases

Current answer to "is this 100% complete?": no. This slice closed the
read-only Auto-Quant adoption review surface, but mutating/bootstrap/import
commands still need explicit exception classification and the broader raw
IO/error matrix remains open.

Change:

- Added full output-mode coverage for `auto-quant-adoption-review`:
  `--output-format json|compact|agent|human`, plus `--compact`, `--agent`, and
  `--human` aliases.
- `json`, `compact`, and `agent` preserve the existing redacted JSON-compatible
  adoption review payload.
- `human` prints a compact adoption review summary with symbol, status,
  handoff kind, backend, data/dependency readiness, and recommended next
  command.
- Left `auto-quant-adoption-decision` unchanged because it records a decision
  artifact and is not a read-only status/report surface.
- Updated `support/docs/command-output-contract.md` from the fresh help matrix:
  30 full surfaces, 0 partial surfaces, 23 no-output-mode surfaces.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture` failed before implementation with missing fields on `AutoQuantAdoptionReviewArgs`:
  `agent` and `output_format`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=30`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=23`
  - `status=pass`

Remaining gaps:

- Classify the remaining 23 `none` commands as mutating/bootstrap/import
  intentional exceptions or patch any remaining read-only/report surfaces.
- Continue the broader raw IO/error matrix after the help-derived command matrix
  policy is closed.

### 2026-05-22 continuation - remaining no-output-mode classification checkpoint

Current answer to "is this 100% complete?": no. The help-derived output-mode
matrix now has no known partial surfaces and no obvious read-only/status/report
surface left in the `none` bucket, but this is only a help-surface checkpoint;
it does not close broader UX, error-message, production-validation, or `main.rs`
reduction gates.

Fresh classification evidence:

- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'` reported:
  - `command_count=53`
  - `commands_with_full_output_modes=30`
  - `commands_with_partial_output_modes=0`
  - `commands_with_no_output_modes=23`
  - `status=pass`
- Remaining `none` commands from `/tmp/ict-engine-adoption-review-help-audit.json`:
  - Training/update/mutating: `train`, `update`, `factor-autoresearch`.
  - Auto-Quant dependency/bootstrap/workspace mutation: `auto-quant-bootstrap`,
    `auto-quant-update`, `auto-quant-prepare`.
  - Explicit decision/promotion/registration toggles: `auto-quant-promote-canonical-setup`,
    `auto-quant-adoption-decision`, `register-structural-path-ranking-trainer-artifact`,
    `clear-structural-path-ranking-trainer-artifact`,
    `enable-structural-path-ranking-runtime`,
    `disable-structural-path-ranking-runtime`.
  - Filesystem/SOP generation flows: `clean-futures`, `futures-sop`,
    `expansion-sop`.
  - Auto-Quant material/import/live-ingest/prior mutation flows:
    `auto-quant-seed-evidence`, `auto-quant-agent-material-batch`,
    `auto-quant-agent-material-dispatch`, `auto-quant-agent-material-rank`,
    `auto-quant-results-import`, `auto-quant-consume-live-signals`,
    `auto-quant-ingest-real-trades`, `auto-quant-prior-init`.

Provisional decision:

- Do not blindly add output aliases to the remaining 23 commands inside this
  help-derived read-only/status slice. They mutate state, write files, run
  training/research loops, import artifacts, toggle runtime config, or bridge
  external Auto-Quant flows.
- Next audit step should switch from help-surface parity to the broader raw
  IO/error matrix and user-pain checks, or begin paying down `main.rs` extraction.

Remaining gaps:

- Run a raw stdout/stderr/error-message audit for the remaining mutating flows,
  especially whether failures name the flag/path/schema/recovery action.
- `src/main.rs` is still far over the target (`wc -l src/main.rs` currently
  reports `16485`), so completion remains contradicted.
- Full release/consumer readiness still requires broader gates than command help
  parity.

### 2026-05-22 continuation - Auto-Quant results import missing-library error

Current answer to "is this 100% complete?": no. This slice fixed one concrete
raw IO/error-message gap, but the raw IO matrix remains broader than one path,
and `main.rs` reduction plus production/consumer readiness gates remain open.

Problem found by real CLI probe:

- Before remediation, running
  `ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe --library /tmp/ict-engine-missing-strategy-library.json`
  exited 1 with stderr:
  - `Error: loading strategy library from '/tmp/ict-engine-missing-strategy-library.json'`
  - `failed to read strategy library manifest ...`
  - `No such file or directory (os error 2)`
- The error named the path but did not name `flag=--library`, the expected
  `strategy_library.json` schema/source, or a recovery command.

Change:

- Added command-level missing-library preflight in
  `src/application/auto_quant/command_entry.rs::auto_quant_results_import_command`.
- New error format includes:
  - `auto_quant_results_import_library_missing`
  - `flag=--library`
  - missing path
  - expected `strategy_library.json` from `Auto-Quant/export_strategy_library.py`
  - `recovery=` with the rerun shape.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib results_import_missing_library_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because the error did not contain `auto_quant_results_import_library_missing`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib results_import_missing_library_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- Real CLI probe after remediation:
  `ict-engine auto-quant-results-import --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe --library /tmp/ict-engine-missing-strategy-library.json` exited 1 and stderr contained `auto_quant_results_import_library_missing`, `flag=--library`, the missing path, `strategy_library.json`, `Auto-Quant/export_strategy_library.py`, and `recovery=`.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for the other mutating flows,
  especially missing file/directory paths for SOP generation, Auto-Quant material
  intake, live-signal ingestion, and structural path ranker toggles.
- `src/main.rs` remains far over target; this slice does not address extraction.
- Help-surface parity remains a partial UX win, not proof of full audit closure.

### 2026-05-22 continuation - Auto-Quant agent material missing-file error

Current answer to "is this 100% complete?": no. This slice fixed the next
concrete raw IO/error-message gap for agent material intake, but the raw IO
matrix is still incomplete and `src/main.rs` remains far above the target.

Problem found by real CLI probe:

- Before remediation, running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-agent-material-batch --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-agent-material --material /tmp/ict-engine-missing-agent-material.json`
  exited 1 with stderr:
  - `Error: reading agent material '/tmp/ict-engine-missing-agent-material.json'`
  - `No such file or directory (os error 2)`
- The error named the path but did not name `flag=--material`, the expected
  `AgentMaterialPackage` JSON schema fields, or a recovery command.

Change:

- Added command-level missing-material preflight in
  `src/application/auto_quant/command_entry.rs::auto_quant_agent_material_batch_command`.
- New error format includes:
  - `auto_quant_agent_material_missing`
  - `flag=--material`
  - missing path
  - expected `AgentMaterialPackage` JSON with `data_path` and
    `strategy_source_path`
  - `recovery=` with the rerun shape.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib agent_material_batch_missing_material_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because stderr only contained `reading agent material ... No such file or directory` and missed the structured marker/schema/recovery context.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib agent_material_batch_missing_material_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/auto_quant/command_entry.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.
- Real CLI probe after remediation:
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-agent-material-batch --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-agent-material --material /tmp/ict-engine-missing-agent-material.json` exited 1 and stderr contained `auto_quant_agent_material_missing`, `flag=--material`, the missing path, `AgentMaterialPackage`, `data_path`, `strategy_source_path`, and `recovery=`.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for SOP generation,
  `auto-quant-seed-evidence`, live-signal ingestion, real-trade ingest, and
  structural path ranker toggle/register/clear flows.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - Auto-Quant real-trades missing-file error

Current answer to "is this 100% complete?": no. This slice fixed another
concrete raw IO/error-message gap for real-trade ingest, but the broader raw IO
matrix, production validation, and `main.rs` reduction gates remain open.

Problem found by real CLI probe:

- Before remediation, running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-ingest-real-trades --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-real-trades --trades /tmp/ict-engine-missing-real-trades.jsonl`
  exited 1 with stderr:
  - `Error: ingesting real trades for symbol 'NQ' from '/tmp/ict-engine-missing-real-trades.jsonl'`
  - `reading real-trades JSONL artifact at '/tmp/ict-engine-missing-real-trades.jsonl'`
  - `No such file or directory (os error 2)`
- The error named the path but did not name `flag=--trades`, the expected JSONL
  producer/schema source, or a recovery command.

Change:

- Added command-level missing-trades preflight in
  `src/application/auto_quant/command_entry.rs::auto_quant_ingest_real_trades_command`.
- New error format includes:
  - `auto_quant_real_trades_missing`
  - `flag=--trades`
  - missing path
  - expected JSONL from `Auto-Quant/auto_quant_export_real_trades.py`
  - `recovery=` with the rerun shape.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib ingest_real_trades_missing_trades_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because stderr only contained `ingesting real trades ... reading real-trades JSONL artifact ... No such file or directory` and missed the structured marker/flag/schema/recovery context.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib ingest_real_trades_missing_trades_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/auto_quant/command_entry.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.
- Real CLI probe after remediation:
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-ingest-real-trades --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-real-trades --trades /tmp/ict-engine-missing-real-trades.jsonl` exited 1 and stderr contained `auto_quant_real_trades_missing`, `flag=--trades`, the missing path, `JSONL`, `Auto-Quant/auto_quant_export_real_trades.py`, and `recovery=`.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for SOP generation,
  `auto-quant-seed-evidence`, live-signal ingestion, and structural path ranker
  toggle/register/clear flows.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - Auto-Quant live-signals Redis connection error

Current answer to "is this 100% complete?": no. This slice fixed another
operator-facing raw IO/runtime error for live-signal ingestion, but the broader
raw IO matrix, production validation, and `main.rs` reduction gates remain open.

Problem found by real CLI probe:

- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-consume-live-signals --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-live --redis-url redis://127.0.0.1:1 --max-iter 1 --block-ms 1`
  exited 1 with stderr:
  - `Error: connecting to redis at 'redis://127.0.0.1:1' (sanitised: redis://127.0.0.1:1)`
  - `failed to connect to redis at redis://127.0.0.1:1: Connection refused (os error 61)`
- The error sanitized the URL and preserved the underlying connection failure,
  but did not name `flag=--redis-url`, the expected Redis stream source, the
  Auto-Quant publisher dependency, or a recovery command.

Change:

- Added command-level connection-failure context in
  `src/application/auto_quant/command_entry.rs::auto_quant_consume_live_signals_command`.
- New error format includes:
  - `auto_quant_live_signals_redis_unavailable`
  - `flag=--redis-url`
  - sanitized Redis URL
  - expected Redis stream written by the Auto-Quant publisher
  - `recovery=` with the rerun shape.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib live_signals_redis_connect_error_names_flag_source_and_recovery -- --nocapture` failed before implementation because stderr only contained `connecting to redis ... failed to connect ... Connection refused` and missed the structured marker/flag/source/recovery context.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib live_signals_redis_connect_error_names_flag_source_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_result_application_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/auto_quant/command_entry.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.
- Real CLI probe after remediation:
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-consume-live-signals --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-live --redis-url redis://127.0.0.1:1 --max-iter 1 --block-ms 1` exited 1 and stderr contained `auto_quant_live_signals_redis_unavailable`, `flag=--redis-url`, `Redis stream`, `Auto-Quant publisher`, sanitized `redis://127.0.0.1:1`, and `recovery=`.

Nearby probe that did not need code in this slice:

- `register-structural-path-ranking-trainer-artifact --artifact-uri /tmp/ict-engine-missing-trainer-artifact.json --model-family catboost` exited 1 with a clear prerequisite message: missing `structural_path_ranking_target_summary.json`, expected structural-path target export summary JSON, and `run export-structural-path-ranking-target before register-structural-path-ranking-trainer-artifact`.
- `enable-structural-path-ranking-runtime` exited 1 with a clear prerequisite message: missing target export summary and `export target rows before enabling runtime reuse`.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for SOP generation,
  `auto-quant-seed-evidence`, and remaining structural path ranker toggle/clear
  flows.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - Auto-Quant seed-evidence missing material root error

Current answer to "is this 100% complete?": no. This slice fixed another
operator-facing raw IO/runtime error for seed-evidence intake, but the broader
raw IO matrix, production validation, and `main.rs` reduction gates remain open.

Problem found by real CLI probe before the fix:

- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-seed-evidence --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-seed --strategy-material-root /tmp/ict-engine-missing-seed-material`
  exited 1 with stderr:
  - `Error: no external strategy materials with usable evidence were found under '/tmp/ict-engine-missing-seed-material'`
- The error named the missing root path but did not name
  `flag=--strategy-material-root`, expected external strategy/evidence files,
  or a recovery path.

Change:

- Added command-level missing-root context in
  `src/application/auto_quant/command_entry.rs::auto_quant_seed_evidence_command`.
- New missing-root error format includes:
  - `auto_quant_seed_evidence_material_root_missing`
  - `flag=--strategy-material-root`
  - the missing root path
  - expected external strategy material and evidence CSV files
  - `recovery=` with the rerun shape.
- Also upgraded the existing-root-but-unusable scan error to
  `auto_quant_seed_evidence_material_root_unusable` with the same flag/schema/
  recovery contract.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib seed_evidence_missing_strategy_material_root_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because stderr only contained `no external strategy materials with usable evidence were found under ...` and missed the structured marker/flag/schema/recovery context.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib seed_evidence_missing_strategy_material_root_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_agent_material_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- auto-quant-seed-evidence --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-seed --strategy-material-root /tmp/ict-engine-missing-seed-material` exited 1 and stderr contained `auto_quant_seed_evidence_material_root_missing`, `flag=--strategy-material-root`, `/tmp/ict-engine-missing-seed-material`, `external strategy material`, `evidence CSV files`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/auto_quant/command_entry.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining structural path
  ranker toggle/clear flows and any other unprobed mutating/bootstrap paths.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - futures SOP missing TOMAC root error

Current answer to "is this 100% complete?": no. This slice fixed another
operator-facing raw IO/runtime error for futures SOP generation, but the broader
raw IO matrix, production validation, and `main.rs` reduction gates remain open.

Problem found by real CLI probe before the fix:

- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- futures-sop --root /tmp/ict-engine-missing-sop-root --output-dir /tmp/ict-engine-sop-out --interval 1m`
  exited 1 with stderr:
  - `Error: no TOMAC futures datasets found under '/tmp/ict-engine-missing-sop-root'`
- The error named the root path but did not name `flag=--root`, the required
  TOMAC futures dataset shape, sibling `symbology.csv`, or recovery.

Change:

- Added structured missing-dataset context in
  `src/application/data_sources/clean_futures.rs::run_clean_futures`.
- New error format includes:
  - `futures_sop_tomac_root_missing`
  - `flag=--root`
  - the root path
  - expected TOMAC futures `*.ohlcv-1m.csv` files with sibling `symbology.csv`
  - `recovery=` with the `clean-futures` and `futures-sop` rerun shape.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib futures_sop_missing_root_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because stderr only contained `no TOMAC futures datasets found under ...` and missed the structured marker/flag/schema/recovery context.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib futures_sop_missing_root_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_market_data_sop_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- futures-sop --root /tmp/ict-engine-missing-sop-root --output-dir /tmp/ict-engine-sop-out --interval 1m` exited 1 and stderr contained `futures_sop_tomac_root_missing`, `flag=--root`, `/tmp/ict-engine-missing-sop-root`, `*.ohlcv-1m.csv`, `symbology.csv`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/data_sources/clean_futures.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Nearby probes classified in this slice:

- `clear-structural-path-ranking-trainer-artifact --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-ranker-clear` exited 0 with JSON status and warning `structural_path_ranking_target_export_missing`; this is an intentional no-op/status surface, not a code fix in this slice.
- `disable-structural-path-ranking-runtime --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-ranker-disable` exited 0 with JSON status and warning `structural_path_ranking_target_export_missing`; this is also classified as an intentional no-op/status surface for now.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for any remaining unprobed
  mutating/bootstrap paths and deeper structural path-ranker artifact/schema
  failure modes.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - structural path-ranker flag validation errors

Current answer to "is this 100% complete?": no. This slice fixed more
operator-facing raw IO/runtime errors for structural path-ranker register and
runtime enablement flags, but broader production validation and `main.rs`
reduction gates remain open.

Problems found by real CLI probes before the fix:

- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- register-structural-path-ranking-trainer-artifact --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-ranker-reg-empty-uri --artifact-uri '' --model-family catboost`
  exited 1 with stderr:
  - `Error: artifact uri must not be empty`
- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- register-structural-path-ranking-trainer-artifact --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-ranker-reg-empty-family --artifact-uri /tmp/ict-engine-missing-trainer-artifact.json --model-family ''`
  exited 1 with stderr:
  - `Error: model family must not be empty`
- Running
  `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- enable-structural-path-ranking-runtime --symbol NQ --state-dir /tmp/ict-engine-raw-io-probe-ranker-enable-bad-mode --reuse-mode banana`
  exited 1 with a missing summary prerequisite, so the invalid `--reuse-mode`
  value was masked by deeper state validation.

Change:

- Added structured validation errors in
  `src/application/entry_models/training_export.rs` for:
  - empty `--artifact-uri`: `structural_path_ranker_trainer_artifact_uri_missing`
  - empty `--model-family`: `structural_path_ranker_model_family_missing`
  - invalid `--reuse-mode`: `structural_path_ranker_runtime_reuse_mode_invalid`
- Moved runtime reuse-mode validation before summary-path existence checks so
  bad user input is reported before deeper state prerequisites.
- Each error now names the flag, expected values/schema, and `recovery=` rerun
  guidance.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_trainer_artifact_empty_flags_name_recovery -- --nocapture` failed before implementation because the message was only `artifact uri must not be empty`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib enable_structural_path_ranking_runtime_invalid_reuse_mode_names_flag_before_state -- --nocapture` failed before implementation because the invalid reuse mode was hidden by the missing-summary prerequisite.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_trainer_artifact_empty_flags_name_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib enable_structural_path_ranking_runtime_invalid_reuse_mode_names_flag_before_state -- --nocapture` passed 1 test.
- Real empty `--artifact-uri` CLI probe exited 1 and stderr contained `structural_path_ranker_trainer_artifact_uri_missing`, `flag=--artifact-uri`, expected trainer/score/model artifact guidance, and `recovery=`.
- Real empty `--model-family` CLI probe exited 1 and stderr contained `structural_path_ranker_model_family_missing`, `flag=--model-family`, `catboost`, and `recovery=`.
- Real invalid `--reuse-mode banana` CLI probe exited 1 and stderr contained `structural_path_ranker_runtime_reuse_mode_invalid`, `flag=--reuse-mode`, `banana`, `candidate_set_only`, `prefer_history`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/entry_models/training_export.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Nearby probes classified in this slice:

- Missing export summary for
  `register-structural-path-ranking-trainer-artifact --artifact-uri /tmp/ict-engine-missing-trainer-artifact.json --model-family catboost` already exits 1 with a clear prerequisite: missing `structural_path_ranking_target_summary.json`, expected structural-path target export summary JSON, and `run export-structural-path-ranking-target before register-structural-path-ranking-trainer-artifact`.
- Missing export summary for `enable-structural-path-ranking-runtime --reuse-mode candidate_set_only` already exits 1 with a clear prerequisite: missing target export summary and `export target rows before enabling runtime reuse`.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for any remaining unprobed
  mutating/bootstrap paths and non-explicit structural path-ranker score artifact
  failure modes.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - explicit structural path-ranker artifact schema errors

Current answer to "is this 100% complete?": no. This slice fixed deeper
operator-facing schema errors for explicit structural path-ranker artifacts, but
broader production validation, non-explicit score-artifact failures, and
`main.rs` reduction gates remain open.

Prerequisite setup for real probes:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-ranker-schema-probe --output-format json` exited 0 and wrote
  `/tmp/ict-engine-ranker-schema-probe/DEMO/policy_training/structural_path_ranking_target_summary.json` plus row files.

Problems found by real CLI probes before the fix:

- Registering `--model-family corels --artifact-uri Cargo.toml` exited 1 with
  `failed to parse structural path ranking trainer artifact Cargo.toml as JSON ... expected structural path ranking trainer artifact JSON with rule_list or tree_json; rerun ...`, but did not include a stable marker, `flag=--artifact-uri`, or `recovery=`.
- Registering `--model-family corels --artifact-uri /tmp/ict-engine-ranker-schema-probe/DEMO/policy_training/structural_path_ranking_target_summary.json` exited 1 with `explicit path-ranker family 'corels' requires ...`, but did not include a stable marker, `flag=--artifact-uri`, or `recovery=`.
- Registering `--model-family corels --artifact-uri /tmp/ict-engine-missing-corels-artifact.json` exited 1 with `structural path ranking trainer artifact does not exist ...`, but did not include a stable marker, `flag=--artifact-uri`, or `recovery=`.

Change:

- Added structured explicit-artifact schema errors in
  `src/application/entry_models/training_export.rs` for:
  - missing explicit artifact: `structural_path_ranker_explicit_artifact_missing`
  - invalid JSON explicit artifact: `structural_path_ranker_explicit_artifact_invalid_json`
  - readable but incompatible explicit artifact schema:
    `structural_path_ranker_explicit_artifact_schema_invalid`
  - explicit artifact family mismatch:
    `structural_path_ranker_explicit_artifact_family_mismatch`
- Each error now names `flag=--artifact-uri` or `flag=--model-family`, the
  expected `rule_list` / `tree_json` schema where relevant, and `recovery=`
  rerun guidance.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_explicit_family_artifact_errors_name_flag_schema_recovery -- --nocapture` failed before implementation because the missing explicit artifact path used the old unstructured message.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_explicit_family_artifact_errors_name_flag_schema_recovery -- --nocapture` passed 1 test.
- Real invalid-JSON explicit artifact probe (`--artifact-uri Cargo.toml --model-family corels`) exited 1 and stderr contained `structural_path_ranker_explicit_artifact_invalid_json`, `flag=--artifact-uri`, `rule_list`, `tree_json`, and `recovery=`.
- Real incompatible explicit artifact schema probe using the exported summary JSON exited 1 and stderr contained `structural_path_ranker_explicit_artifact_schema_invalid`, `flag=--artifact-uri`, `corels`, `rule_list`, `tree_json`, and `recovery=`.
- Real missing explicit artifact probe exited 1 and stderr contained `structural_path_ranker_explicit_artifact_missing`, `flag=--artifact-uri`, `rule_list`, `tree_json`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for any remaining unprobed
  mutating/bootstrap paths and non-explicit structural path-ranker score artifact
  failure modes.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - non-explicit structural path-ranker local artifact errors

Current answer to "is this 100% complete?": no. This slice closed one confirmed
raw IO gap for non-explicit structural path-ranker registrations, but broader
mutating/bootstrap probing, production validation, and `main.rs` reduction gates
remain open.

Problem found by real CLI probes before the fix:

- After exporting `/tmp/ict-engine-ranker-schema-probe/DEMO/policy_training/structural_path_ranking_target_summary.json`, registering `--model-family catboost --artifact-uri /tmp/ict-engine-missing-score-artifact.json` exited 0 and wrote a ready trainer artifact even though the local score artifact path did not exist.
- Registering `--model-family catboost --artifact-uri Cargo.toml` also exited 0 and treated an incompatible local file as an opaque usable artifact.
- `apply-structural-path-ranking-external-scores` was probed with missing and malformed score files and already returned clear schema messages, so that command was not changed in this slice.

Change:

- Added local-path validation for non-explicit structural path-ranker artifact
  registration in `src/application/entry_models/training_export.rs`.
- Remote/opaque URIs remain allowed.
- Existing local `.csv`, `.jsonl`, `.cbm`, `.bin`, and `.model` score/model
  artifacts remain allowed.
- Readable trainer-artifact JSON companion files remain allowed.
- Missing local paths now fail with
  `structural_path_ranker_score_artifact_missing`.
- Invalid local `.json` artifacts now fail with
  `structural_path_ranker_score_artifact_invalid_json`.
- Unsupported existing local files now fail with
  `structural_path_ranker_score_artifact_schema_invalid`.
- The new errors include `flag=--artifact-uri`, model family, expected local
  score/model/trainer artifact schema, remote URI allowance, and `recovery=`
  guidance.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_catboost_local_artifact_errors_name_flag_schema_recovery -- --nocapture` failed before implementation because the missing local catboost artifact path returned `Ok(...)` and wrote `structural_path_ranking_trainer_artifact.json`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_catboost_local_artifact_errors_name_flag_schema_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_trainer_artifact_accepts_catboost_companion_scores -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_trainer_artifact_writes_ready_artifact -- --nocapture` passed 1 test.
- Real missing local catboost artifact probe exited 1 and stderr contained
  `structural_path_ranker_score_artifact_missing`, `flag=--artifact-uri`,
  `model_family=catboost`, `score artifact CSV/JSONL`, and `recovery=`.
- Real invalid local catboost JSON artifact probe exited 1 and stderr contained
  `structural_path_ranker_score_artifact_invalid_json`, `flag=--artifact-uri`,
  `model_family=catboost`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_structural_path_ranker_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/entry_models/training_export.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining unprobed
  mutating/bootstrap paths.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - Auto-Quant prior/adoption raw IO errors

Current answer to "is this 100% complete?": no. This slice closed two confirmed
Auto-Quant raw IO errors, but the full audit objective remains open because
other mutating/bootstrap paths, production validation, full test gates, and
`main.rs` reduction are still not fully proven.

Problems found by real CLI probes before the fix:

- `auto-quant-agent-material-dispatch --symbol DEMO --state-dir /tmp/ict-engine-raw-io-probe-agent-dispatch` exited 1 with `no auto_quant_agent_material_batch artifact found for DEMO`; this is a clear prerequisite message and was not changed.
- `auto-quant-agent-material-rank --symbol DEMO --state-dir /tmp/ict-engine-raw-io-probe-agent-rank` exited 1 with `no auto_quant_agent_material_dispatch artifact found for DEMO`; this is a clear prerequisite message and was not changed.
- `auto-quant-prior-init --symbol DEMO --state-dir /tmp/ict-engine-raw-io-probe-prior-init --library /tmp/ict-engine-missing-strategy-library.json` exited 1 with raw load context ending in `No such file or directory (os error 2)`.
- `auto-quant-adoption-decision --symbol DEMO --state-dir /tmp/ict-engine-raw-io-probe-adoption-decision --decision adopt --rationale probe` exited 1 with raw `No such file or directory (os error 2)` when the routed Auto-Quant state root did not exist.

Change:

- `auto_quant_prior_init_command` now preflights the resolved `--library` path
  and reports `auto_quant_prior_init_library_missing` with `flag=--library`,
  expected `strategy_library.json`, `auto-quant-results-import` guidance, and
  `recovery=` before attempting to parse the manifest.
- Auto-Quant adoption handoff lookup now returns
  `auto_quant_adoption_handoff_missing` for missing handoff artifacts and for a
  missing state root, including `symbol=`, expected `auto_quant_handoff_candidate`,
  `auto-quant-adoption-review` guidance, and `recovery=`.
- The CLI shell fallback for adoption-decision now recognizes the new stable
  `auto_quant_adoption_handoff_missing` marker when falling back from routed
  `state-dir/auto-quant` to the caller-provided state dir.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib prior_init_missing_library_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because the error only contained raw strategy-library load context and `os error 2`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib decision_missing_handoff_error_names_prerequisite_and_recovery -- --nocapture` failed before implementation because the error only said `no auto-quant handoff artifact found for 'NQ'` without stable marker or recovery.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib decision_missing_handoff_error_handles_missing_state_root -- --nocapture` failed before implementation with raw `No such file or directory (os error 2)`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib prior_init_missing_library_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib decision_missing_handoff_error_names_prerequisite_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib decision_missing_handoff_error_handles_missing_state_root -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib auto_quant::adoption -- --nocapture` passed 8 tests.
- Real prior-init missing-library probe exited 1 and stderr contained
  `auto_quant_prior_init_library_missing`, `flag=--library`,
  `strategy_library.json`, `auto-quant-results-import`, and `recovery=`.
- Real adoption-decision missing-handoff probe exited 1 and stderr contained
  `auto_quant_adoption_handoff_missing`, `symbol=DEMO`,
  `auto_quant_handoff_candidate`, `auto-quant-adoption-review`, and `recovery=`;
  it no longer exposed raw `os error 2`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` initially reported rustfmt diffs; after `cargo fmt`, `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/auto_quant/command_entry.rs src/application/auto_quant/adoption.rs src/auto_quant_command.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining mutating/bootstrap
  paths not yet probed in this loop.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - factor-autoresearch auxiliary evidence raw IO error

Current answer to "is this 100% complete?": no. This slice closed one confirmed
raw IO error in the research/autoresearch shell path, but the broader audit
objective remains open.

Probe results before the fix:

- `expansion-sop --root /tmp/ict-engine-missing-tomac-root --output-dir /tmp/ict-engine-raw-io-expansion-sop` exited 1 with existing structured `futures_sop_tomac_root_missing`, `flag=--root`, TOMAC schema, and `recovery=`; no change needed.
- `factor-autoresearch --symbol DEMO --data /tmp/ict-engine-missing-cleaned-candles.json --iterations 1 --state-dir /tmp/ict-engine-raw-io-autoresearch` exited 0 with handoff JSON plus `auto_quant_requested_data_missing` note, expected candle schema, and `ict-engine auto-quant-prepare` recovery; no change needed.
- `factor-autoresearch --symbol DEMO --data support/examples/demo/demo-15m.json --mutation-spec /tmp/ict-engine-missing-mutation-spec.json --iterations 1 --state-dir /tmp/ict-engine-raw-io-autoresearch-spec` exited 0 at handoff stage without raw IO; no change made in this slice.
- `factor-autoresearch --symbol DEMO --data support/examples/demo/demo-15m.json --auxiliary-evidence /tmp/ict-engine-missing-auxiliary-evidence.json --iterations 1 --state-dir /tmp/ict-engine-raw-io-autoresearch-aux` exited 1 with raw `reading auxiliary/options evidence ... No such file or directory (os error 2)`.

Change:

- Added a preflight missing-path check in `src/factor_research_command.rs` for
  `--auxiliary-evidence` before reading the file.
- Missing auxiliary evidence now reports
  `factor_research_auxiliary_evidence_missing`, `flag=--auxiliary-evidence`,
  expected `AuxiliaryMarketEvidence` or analyze-report `supporting.auxiliary`
  schema, and `recovery=` guidance.
- The shared loader covers both `factor-research` and `factor-autoresearch`.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine missing_auxiliary_evidence_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because the error only contained raw `No such file or directory (os error 2)`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine missing_auxiliary_evidence_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine loads_auxiliary_evidence_from -- --nocapture` passed 2 tests.
- Real missing auxiliary evidence autoresearch probe exited 1 and stderr contained `factor_research_auxiliary_evidence_missing`, `flag=--auxiliary-evidence`, `AuxiliaryMarketEvidence`, `supporting.auxiliary`, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_research_loop_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` initially reported a rustfmt diff; after `cargo fmt`, `cargo fmt --check` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/factor_research_command.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining mutating/bootstrap
  paths not yet probed in this loop.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - train/update/bootstrap missing-input raw errors

Current answer to "is this 100% complete?": no. This slice closed three
confirmed raw missing-input errors in remaining `none` output-mode command
surfaces, but the broader audit objective remains open.

Probe results before the fix:

- `train --symbol DEMO --data /tmp/ict-engine-missing-train.json --state-dir /tmp/ict-engine-raw-io-train` exited 1 with raw `Failed to read file ... No such file or directory (os error 2)`.
- `update --symbol DEMO --outcome win --feedback-file /tmp/ict-engine-missing-feedback.json --state-dir /tmp/ict-engine-raw-io-update` exited 1 with raw `No such file or directory (os error 2)`.
- `auto-quant-bootstrap --state-dir /tmp/ict-engine-raw-io-bootstrap --repo-url /tmp/ict-engine-missing-autoquant-repo` exited 1 with raw `git clone ... fatal: repository ... does not exist`.
- `auto-quant-prepare --state-dir /tmp/ict-engine-raw-io-prepare` already exited 1 with clear bootstrap guidance; no change needed.
- `auto-quant-update --state-dir /tmp/ict-engine-raw-io-update-aq` bootstrapped/updated successfully against the default upstream; no missing-input error was present in that probe.

Change:

- `train_command` now preflights `--data` and reports `train_data_missing`,
  `flag=--data`, expected cleaned candle JSON, and `recovery=` guidance before
  the lower-level JSON reader exposes `os error 2`.
- `update_command` now preflights explicit `--feedback-file` and reports
  `update_feedback_file_missing`, `flag=--feedback-file`, expected
  `PendingUpdateArtifact`/`FeedbackRecord`/`StructuralFeedbackSubmission` JSON,
  and `recovery=` guidance before attempting to read the path.
- `auto_quant_bootstrap` now preflights missing local `--repo-url` values and
  reports `auto_quant_bootstrap_repo_missing`, `repo-url=`, expected local git
  repository or reachable Auto-Quant git URL, and `recovery=` guidance before
  invoking `git clone`.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine train_missing_data_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because the error only contained raw file-read context and `os error 2`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine update_missing_feedback_file_error_names_flag_schema_and_recovery -- --nocapture` failed before implementation because the error only contained raw `No such file or directory (os error 2)`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib bootstrap_missing_local_repo_error_names_input_and_recovery -- --nocapture` failed before implementation because the error exposed raw `git clone ... fatal: repository ... does not exist`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine train_missing_data_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine update_missing_feedback_file_error_names_flag_schema_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib bootstrap_missing_local_repo_error_names_input_and_recovery -- --nocapture` passed 1 test.
- Real train missing-data probe exited 1 and stderr contained `train_data_missing`, `flag=--data`, `cleaned candle JSON`, and `recovery=`.
- Real update missing-feedback probe exited 1 and stderr contained `update_feedback_file_missing`, `flag=--feedback-file`, `PendingUpdateArtifact`, `FeedbackRecord`, `StructuralFeedbackSubmission`, and `recovery=`.
- Real Auto-Quant missing-local-repo bootstrap probe exited 1 and stderr contained `auto_quant_bootstrap_repo_missing`, `repo-url=`, expected local git repository or reachable Auto-Quant git URL, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_core_runtime_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine update_feedback_file_rejects_proxy_non_trade_structural_feedback -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_train_command_persists_train_run_and_snapshot -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib bootstrap_clones_repo_and_persists_config -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib readiness_reports_data_missing_after_healthy_bootstrap -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after `cargo fmt` corrected formatting in the new training test.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `python3 support/scripts/help_audit.py` passed with `command_count=53`, `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`, `commands_with_no_output_modes=23`, `status=pass`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/training_command.rs src/update_command.rs src/application/auto_quant/update.rs src/application/auto_quant/mod.rs` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining mutating/import
  paths not yet probed in this loop, especially successful-path output clarity
  and less common invalid-input branches.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - PB12 canonical promotion missing prerequisite

Current answer to "is this 100% complete?": no. This slice closed one confirmed
raw prerequisite error in the internal Auto-Quant canonical setup promotion
surface, but the broader audit objective remains open.

Probe results before the fix:

- `auto-quant-promote-canonical-setup --symbol DEMO --setup-name probe --sequence-label 'a -> b' --state-dir /tmp/ict-engine-raw-io-promote-canonical` exited 1 with raw `no pb12 research artifacts found for DEMO`.
- `clean-futures --root /tmp/ict-engine-missing-tomac-root --output-dir /tmp/ict-engine-raw-io-clean-futures` already exited 1 with structured `futures_sop_tomac_root_missing`, `flag=--root`, expected TOMAC schema, and `recovery=`; no change needed.
- `register-structural-path-ranking-trainer-artifact --symbol DEMO --state-dir /tmp/ict-engine-raw-io-register-structural --artifact-uri /tmp/ict-engine-missing-cb.json --model-family catboost` already exited 1 with a clear missing export-summary prerequisite; no change needed.
- `auto-quant-agent-material-dispatch --symbol DEMO --state-dir /tmp/ict-engine-raw-io-agent-dispatch-fresh` exited 1 with `no auto_quant_agent_material_batch artifact found for DEMO`; classified as a clear prerequisite for now.
- `auto-quant-agent-material-rank --symbol DEMO --state-dir /tmp/ict-engine-raw-io-agent-rank-fresh` exited 1 with `no auto_quant_agent_material_dispatch artifact found for DEMO`; classified as a clear prerequisite for now.

Change:

- `auto_quant_promote_canonical_setup_command` now reports
  `auto_quant_promote_canonical_setup_pb12_missing`, `symbol=`, expected `PB12`
  control-matrix research artifact, and `recovery=` guidance before promotion
  when no PB12 artifact exists for the requested symbol.
- The change is isolated to `src/application/backtest/canonical_promotion.rs`;
  no new logic was added to `src/main.rs`.

RED evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib promote_canonical_setup_missing_pb12_artifact_names_prerequisite_and_recovery -- --nocapture` failed before implementation because the error only said `no pb12 research artifacts found for DEMO`.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib promote_canonical_setup_missing_pb12_artifact_names_prerequisite_and_recovery -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib promote_canonical_setup_writes_repo_manifest_and_generated_file -- --nocapture` passed 1 test.
- Real promote-canonical missing-PB12 probe exited 1 and stderr contained `auto_quant_promote_canonical_setup_pb12_missing`, `symbol=DEMO`, expected `PB12` artifact, and `recovery=`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_auto_quant_promote_canonical_setup_uses_extracted_args -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `cargo fmt --check` passed after `cargo fmt` corrected formatting in the new canonical-promotion test.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `python3 support/scripts/help_audit.py` passed with `command_count=53`, `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`, `commands_with_no_output_modes=23`, `status=pass`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/application/backtest/canonical_promotion.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed.

Remaining gaps:

- Continue raw stdout/stderr/error-message audit for remaining mutating/import
  paths not yet probed in this loop, especially successful-path output clarity
  and less common invalid-input branches.
- `wc -l src/main.rs` still reports `16485`; this remains incompatible with
  the `<5,000` `main.rs` reduction target.
- This slice is not a release, trading, or full audit-completion claim.

### 2026-05-22 continuation - analyze structural-feedback helper extraction

Current answer to "is this 100% complete?": no. This slice pays down part of
the `main.rs` architecture gate, but the entrypoint remains far above the
`<5,000` line target and the broader raw IO/production-validation gates remain
open.

Change:

- Moved the structural-feedback branch helper logic out of `src/main.rs` and
  into `src/analyze_shared.rs`:
  - `regime_profit_branch_assignment_entries_from_feedback_history`
  - `regime_profit_branch_path_is_exact`
  - `regime_profit_branch_assignment_entries_from_path`
  - `pre_bayes_branch_direction_context_from_assignment_entries`
- `src/main.rs` now imports the owner helpers and no longer keeps duplicate
  root-local definitions.

RED / boundary evidence:

- The owner-boundary test
  `test_regime_profit_branch_assignments_derive_from_feedback_history` existed
  in `src/analyze_shared.rs` before extraction and passed against the old
  root-private helpers via `use super::*`, which proved behavior but not owner
  placement. The extraction removed the stale root owner and left the test
  passing against the owner module definitions.

GREEN / verification evidence:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_regime_profit_branch_assignments_derive_from_feedback_history -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_command_derives_branch_path_from_structural_feedback_history -- --nocapture` passed 1 test and retained `regime_profit_branch_path_source=structural_feedback_history` in the analyze evidence.
- `rg -n "^pub\(crate\) fn regime_profit_branch_assignment_entries_from_feedback_history|^fn regime_profit_branch_assignment_entries_from_feedback_history|^pub\(crate\) fn pre_bayes_branch_direction_context_from_assignment_entries|^fn pre_bayes_branch_direction_context_from_assignment_entries|^pub\(crate\) fn regime_profit_branch_path_is_exact|^fn regime_profit_branch_path_is_exact" src/main.rs src/analyze_shared.rs` showed the helper definitions only in `src/analyze_shared.rs`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture` passed 63 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.
- `rustfmt --edition 2021 --check src/main.rs src/analyze_shared.rs` passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py` passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2 tests.
- `python3 support/scripts/help_audit.py` passed with `command_count=53`,
  `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`,
  `commands_with_no_output_modes=23`, `status=pass`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine` passed.
- `git diff --check -- src/main.rs src/analyze_shared.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` passed before this doc append.

Line-count movement:

- Pre-interruption baseline from the previous slice: `src/main.rs` = `16485`.
- After this extraction and formatting: `src/main.rs` = `16390`; net reduction
  is 95 lines.
- `src/analyze_shared.rs` is now `2311` lines.

Remaining gaps:

- `src/main.rs` is still far above the `<5,000` target, so the P0 architecture
  gate remains contradicted.
- Continue extracting owner-bounded helpers/command bodies in small verified
  batches; do not treat this slice as release, trading, or full audit closure.
- Continue raw stdout/stderr/error-message audit for remaining mutating/import
  paths not yet probed in this loop.

### 2026-05-22 continuation - aligned PDA hybrid confidence floor verification

Current answer to "is this 100% complete?": no. This slice verifies and
terminalizes an already-present hybrid-regime behavior change in the dirty tree,
but it does not close the full audit objective, the `main.rs <5,000` gate, or
the remaining raw IO/production-validation work.

Problem / pain point:

- Downstream execution can remain guarded by `transition_hazard >= 0.60` even
  when PDA sequence evidence is aligned with the selected hybrid regime family.
- The practical symptom is an aligned range/trend PDA readback being treated too
  much like a transition-blocker, which preserves `observe/transition_guardrail`
  behavior despite supportive structure evidence.

Change observed in `src/domain/regime/hybrid.rs`:

- Added `aligned_pda_confidence_floor(...)`, which only applies when:
  - PDA/hybrid family alignment is explicitly true;
  - the PDA family matches the hybrid family and is not `transition`;
  - session density, primary cluster confidence, consistency, ensemble
    confidence, and directional confirmation provide enough support.
- The confidence floor raises effective hybrid confidence only for aligned,
  directionally confirmed PDA evidence, then records:
  - `aligned_pda_confidence_floor=...`
  - `hybrid_effective_confidence=...`
- Existing disagreement handling remains intact: transition PDA and missing
  directional confirmation still produce `pda_hybrid_alignment=false` and keep
  the guardrail path observable.

Verification evidence:

- `rustfmt --edition 2021 --check src/domain/regime/hybrid.rs` passed after
  formatting the existing dirty file.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib aligned_pda_range_evidence_reduces_confidence_owned_transition_hazard -- --nocapture` passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --test regime_core_first_pass -- --nocapture` passed 12 tests, including PDA disagreement, transition-PDA, directional-confirmation, duration-prior, and pipeline evidence regressions.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib application::belief::execution_temporal_controls -- --nocapture` passed 1 focused guardrail lineage test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine` passed.

Remaining gaps:

- This is a verified behavior slice, not proof of production/trading readiness.
- Still need a real downstream analyze/workflow-status probe on representative
  material before claiming the guarded execution issue is resolved for any
  concrete market lane.
- Continue `main.rs` reduction and raw IO/error-message auditing; the overall
  audit plan remains open.

### 2026-05-22 continuation - update prompt-builder extraction and compile blocker closure

Current answer to "is this 100% complete?": no. This slice closes one more
`src/main.rs` ownership leak and repairs the compile blocker that prevented the
slice from being verified, but the full audit objective remains open.

Scope / ownership:

- Extracted the update feedback agent prompt builder from `src/main.rs` into
  the update command owner module `src/update_command.rs`.
- Added owner-boundary coverage in `src/cli_surface_tests.rs` so future drift
  fails if `build_update_agent_prompts` or `BuildUpdateAgentPromptsInput` moves
  back into `src/main.rs`.
- Kept the old prompt behavior tests available through a test-only import in
  `src/main.rs`; runtime ownership is now in `src/update_command.rs`.
- While verifying, Cargo surfaced an unrelated dirty-tree compile blocker in
  `src/application/orchestration/workflow_status.rs`: the local variable
  `structural_candidate_for_posterior` was declared inside the
  `if let Value::Object(map)` block and later consumed outside the block.
  The minimal fix was to lift the shared candidate construction just above the
  `if let`, preserving the same value for posterior and `phase_detail` output.

Line-count evidence:

- Pre-slice `src/main.rs` baseline from the prior verified extraction: `16390`.
- Post-extraction `src/main.rs`: `16257`.
- Net reduction: 133 lines.
- `src/update_command.rs`: `1250` lines after taking the prompt builder.
- `src/cli_surface_tests.rs`: `2758` lines after the owner-boundary guard.

Verification evidence:

- `rustfmt --edition 2021 src/application/orchestration/workflow_status.rs`
  completed after the minimal scope fix.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_update_agent_prompt_builder_lives_in_update_command_module -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_update_agent_prompts -- --nocapture`
  passed 2 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_cli_core_runtime_commands_use_extracted_args -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
  passed 64 tests.
- `rustfmt --edition 2021 --check src/main.rs src/update_command.rs src/cli_surface_tests.rs src/application/orchestration/workflow_status.rs`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine`
  passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2
  tests.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'`
  reported `status=pass`, `command_count=53`,
  `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`,
  `commands_with_no_output_modes=23`.
- `git diff --check -- src/main.rs src/update_command.rs src/cli_surface_tests.rs src/application/orchestration/workflow_status.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  passed before this evidence section was appended.

Corrected verification note:

- `python3 -m unittest support.scripts.help_audit` is not an authoritative
  command for this repo; it fails to import sibling `path_defaults` from the
  package context. `python3 -m unittest help_audit` from `support/scripts` also
  reports zero tests. The actual test module is
  `support.scripts.tests.test_help_audit`, and the live audit command is
  `python3 support/scripts/help_audit.py` or the same command with
  `ICT_ENGINE_HELP_AUDIT_BIN` pinned to the just-built binary.

Remaining gaps:

- `src/main.rs` is still `16257` lines, so the `<5,000` P0 architecture gate is
  still contradicted.
- Full raw stdout/stderr/error contract matrix is still not closed.
- Production/downstream validation is still not proven for concrete trading
  lanes.
- Full fresh `cargo clippy --all-targets -- -D warnings`, full `cargo test`,
  and clean-state smoke gates remain required before any full-audit or release
  closure claim.

### 2026-05-22 continuation - analyze agent prompt-builder extraction

Current answer to "is this 100% complete?": no. This slice pays down another
`src/main.rs` ownership leak by moving the analyze agent prompt builder into the
analyze shared owner module, but it does not close the full audit objective.

Scope / ownership:

- Moved `BuildAnalyzeAgentPromptsInput` and `build_analyze_agent_prompts` from
  `src/main.rs` to `src/analyze_shared.rs`.
- Added owner-boundary coverage in `src/cli_surface_tests.rs` so the prompt
  builder and input payload cannot drift back into `src/main.rs` unnoticed.
- Updated suggested prompt file paths from `src/main.rs` to
  `src/analyze_shared.rs` for the moved analyze prompt records.
- Kept the existing analyze prompt behavior test in `src/main.rs` calling the
  owner function through imports, matching the current test layout.

Line-count evidence:

- Pre-slice `src/main.rs` baseline from the previous verified extraction:
  `16257`.
- Post-extraction `src/main.rs`: `16070`.
- Net reduction: 187 lines.
- `src/analyze_shared.rs`: `2501` lines after taking the prompt builder.
- `src/cli_surface_tests.rs`: `2774` lines after the owner-boundary guard.

Verification evidence:

- `rustfmt --edition 2021 src/main.rs src/analyze_shared.rs src/cli_surface_tests.rs`
  completed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_agent_prompt_builder_lives_in_analyze_shared_module -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_agent_prompts_adds_pre_bayes_soft_evidence_prompt -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_command_derives_branch_path_from_structural_feedback_history -- --nocapture`
  passed 1 test and retained `regime_profit_branch_path_source=structural_feedback_history`.
- `rustfmt --edition 2021 --check src/main.rs src/analyze_shared.rs src/cli_surface_tests.rs`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
  passed 65 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine`
  passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2
  tests.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'`
  reported `status=pass`, `command_count=53`,
  `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`,
  `commands_with_no_output_modes=23`.
- `git diff --check -- src/main.rs src/analyze_shared.rs src/cli_surface_tests.rs support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  passed before this evidence section was appended.

Remaining gaps:

- `src/main.rs` is still `16070` lines, so the `<5,000` P0 architecture gate is
  still contradicted.
- Full raw stdout/stderr/error contract matrix is still not closed.
- Production/downstream validation is still not proven for concrete trading
  lanes.
- Full fresh `cargo clippy --all-targets -- -D warnings`, full `cargo test`,
  and clean-state smoke gates remain required before any full-audit or release
  closure claim.

### 2026-05-22 continuation - analyze signal-ranking helper extraction

Current answer to "is this 100% complete?": no. This slice removes another
analyze-owned helper from `src/main.rs`, but the main architecture gate and full
audit gates are still open.

Scope / ownership:

- Moved `analyze_signal_rankings` from `src/main.rs` to
  `src/analyze_shared.rs`.
- Added owner-boundary coverage in `src/cli_surface_tests.rs` so the helper
  cannot drift back into `src/main.rs` unnoticed.
- Kept the existing analyze call site in `src/main.rs` importing the helper
  from the analyze owner module.

Line-count evidence:

- Pre-slice `src/main.rs`: `16070`.
- Post-extraction `src/main.rs`: `15979`.
- Net reduction: 91 lines.
- `src/analyze_shared.rs`: `2593` lines after taking the signal-ranking helper.
- `src/cli_surface_tests.rs`: `2786` lines after the owner-boundary guard.

Verification evidence:

- RED: `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_signal_rankings_lives_in_analyze_shared_module -- --nocapture`
  failed as expected while `analyze_signal_rankings` still lived in `src/main.rs`.
- GREEN: the same command passed 1 test after the helper move.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_report_path_ranker_lineage_uses_state_dir_runtime_scores -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_command_derives_branch_path_from_structural_feedback_history -- --nocapture`
  passed 1 test and retained `regime_profit_branch_path_source=structural_feedback_history`.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_analyze_agent_prompt_builder_lives_in_analyze_shared_module -- --nocapture`
  passed 1 test.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_agent_prompts_adds_pre_bayes_soft_evidence_prompt -- --nocapture`
  passed 1 test.
- `rustfmt --edition 2021 --check src/main.rs src/analyze_shared.rs src/cli_surface_tests.rs`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine cli_surface_tests -- --nocapture`
  passed 66 tests.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine`
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo build --bin ict-engine`
  passed.
- `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py`
  passed.
- `python3 -m unittest support.scripts.tests.test_help_audit -v` passed 2
  tests.
- `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py | jq '.summary'`
  reported `status=pass`, `command_count=53`,
  `commands_with_full_output_modes=30`, `commands_with_partial_output_modes=0`,
  `commands_with_no_output_modes=23`.

Observed unrelated regression during verification:

- `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_report_uses_current_analyze_regime_for_ranker_path_join -- --nocapture`
  failed before any attempted fix with
  `structural_path_ranker_score_artifact_missing: path=current_analyze_scores.jsonl`.
  The test writes the score file under `<state>/NQ/policy_training/current_analyze_scores.jsonl`
  but registers the relative artifact URI `current_analyze_scores.jsonl`; current
  validation requires that relative path to exist from process cwd. This failure
  is not closed in this slice and should be handled separately if selected.

Remaining gaps:

- `src/main.rs` is still `15979` lines, so the `<5,000` P0 architecture gate is
  still contradicted.
- Full raw stdout/stderr/error contract matrix is still not closed.
- Production/downstream validation is still not proven for concrete trading
  lanes.
- Full fresh `cargo clippy --all-targets -- -D warnings`, full `cargo test`,
  and clean-state smoke gates remain required before any full-audit or release
  closure claim.

---

## P2 - Agent / Contributor Truth Map Cleanup

### Problem

`AGENTS.md` contains a stale conflict: E/F/H are listed as active compute stubs in one table, but still described as missing in the design-gap table.

### Risk

Agents and contributors may make wrong claims about available factors.

### Solution

Update `AGENTS.md` and `support/docs/factor-catalog.md` so every factor family has one current status.

### Steps

- [x] Update E/F/H in `AGENTS.md` design-gap table:
  - not missing category
  - active partial compute path
  - list remaining quality/completeness gap
- [x] Update `support/docs/factor-catalog.md` to match.
- [x] Add a small grep/check script or doc test that ensures all `FactorCategory` variants appear in both docs.
  - Added `support/scripts/check_factor_truth_map.py`.
- [x] Verify doc check script passes:
  - `python3 support/scripts/check_factor_truth_map.py`
  - `python3 -m py_compile support/scripts/check_factor_truth_map.py`
- [ ] Optional Rust registry verification after Cargo contention clears:
  - `cargo test factor_registry -- --nocapture`

---

## P2 - Release / Open Source Contribution Flow

### Problem

Release docs mention a private mirror and historical v0.0.1 flow while `Cargo.toml` says `0.1.0`. There is no standard `CONTRIBUTING.md`.

### Risk

Open-source contributors do not know whether to target source repo or mirror, which tests are mandatory, or how releases are versioned.

### Solution

Add a public-facing contribution contract and reconcile release/version docs.

### Steps

- [x] Create `CONTRIBUTING.md`.
- [x] Include mandatory checks:
  - `cargo fmt --check`
  - `cargo clippy --all-targets -- -D warnings`
  - `cargo test`
  - selected Python pytest if touching scripts
- [x] Add architecture placement rules from `support/docs/main-rs-guardrails.md`.
- [x] Clarify release repo vs source repo in `support/docs/release-mirror-runbook.md`.
- [x] Align `Cargo.toml` version notes and release docs.
  - Current observed metadata: `version = "0.1.3"`, `publish = false`,
    `license = "PolyForm-Noncommercial-1.0.0"`, repository
    `https://github.com/Undermybelt/ict-engine-release`.
  - This is doc/readiness hygiene only. It does not prove release readiness.

---

## Research / GitHub Search Backlog

All above items have direct local solutions. No external search is required before starting.

Use external search only if these local approaches fail:

- [ ] If path-ranking validation design remains unclear, search papers for:
  - off-policy evaluation for contextual bandits
  - inverse propensity scoring trading strategy evaluation
  - doubly robust policy evaluation financial trading
- [ ] If command contract tooling becomes heavy, search GitHub for:
  - Rust clap snapshot testing
  - insta snapshot tests CLI output
  - assert_cmd predicates CLI tests
- [ ] If Python script governance needs a template, search GitHub for:
  - research repo script manifest
  - ML experiment script registry
  - cookiecutter data science command layout

Preferred likely crates/tools to evaluate first if needed:

- `assert_cmd` for Rust CLI command tests
- `predicates` for stdout/stderr assertions
- `insta` for snapshot testing
- `trycmd` for markdown-like CLI examples

---

## Execution Order

1. P0 loop truth / validation contract
2. P0 external ranker contract test
3. P0 `main.rs` first extraction batch
4. P1 human output consistency
5. P1 smoke acceptance script
6. P1 first-run docs
7. P1 Python script governance
8. P1 error message contract
9. P2 doc truth-map cleanup
10. P2 contribution/release cleanup

---

## Done Definition

- `cargo check --all-targets` passes
- `cargo clippy --all-targets -- -D warnings` passes
- `cargo test` passes or documented known slow/blocked subset is isolated
- Python tests pass for touched scripts
- Smoke script passes from a clean `/tmp` state dir
- README points consumers and contributors to distinct quickstarts
- `policy-training-status` no longer conflates target-row maturity with feedback-observation maturity
- `src/main.rs` is shrinking, not growing

---

## 2026-05-22 continuation - structural path-ranker relative artifact URI resolution

### Problem

`register-structural-path-ranking-trainer-artifact` rejected a common local
workflow where the score artifact URI was passed as
`current_analyze_scores.jsonl` after the file had been written under
`<state>/<symbol>/policy_training/`.

### Root Cause

`src/application/entry_models/training_export.rs` validated non-URL local
artifacts against `PathBuf::from(artifact_uri)` only. Relative score artifact
URIs were therefore interpreted as cwd-relative, not state-local
policy-training-relative, even though the analyze/report path-ranking tests and
the CLI workflow both stage current-analyze score files inside
`<state>/<symbol>/policy_training/`.

### Fix

- Added state-aware local artifact resolution in
  `src/application/entry_models/training_export.rs`.
- Relative non-URL artifact URIs now fall back to
  `<state>/<symbol>/policy_training/<artifact_uri>` when the raw relative path
  does not exist.
- Validation and explicit artifact merge now use the same resolver.
- When that fallback is used, persisted `artifact.artifact_uri` is rewritten to
  the resolved state-local path so downstream runtime/status readers do not keep
  a brittle cwd-relative filename.
- Preserved existing behavior for absolute paths, `file://` URIs, and remote
  `://` URIs.

### Verification

- RED:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_accepts_policy_training_relative_score_uri -- --nocapture`
    - failed before patch with
      `structural_path_ranker_score_artifact_missing: path=current_analyze_scores.jsonl`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_report_uses_current_analyze_regime_for_ranker_path_join -- --nocapture`
    - failed before patch with the same missing-artifact error
- GREEN:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_accepts_policy_training_relative_score_uri -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_report_uses_current_analyze_regime_for_ranker_path_join -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib register_structural_path_ranking_trainer_artifact_accepts_catboost_companion_scores -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --bin ict-engine test_build_analyze_report_path_ranker_lineage_uses_state_dir_runtime_scores -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo check --bin ict-engine`
  - Zero-config smoke after the patch still passed:
    - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- provider-status --compact`
      - observed summary: `entry_model:3/3 ready | live_runtime:3/5 ready | local_runtime:2/2 ready | market_data:9/9 ready`
    - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-audit-smoke-20260522 --human`
      - observed decision surface remained consumer-safe and fail-closed: `Decision: Observe only`, `Action: TUNE trend_momentum`

### Remaining Gaps

- This closes one verified path-ranker registration/runtime friction point only.
  It does not prove the full repo audit/remediation plan is complete.
- Full completion is still unproven until the broader Done Definition evidence
  is refreshed on the current tree, including full-target compile/lint/test
  gates and cross-surface contributor/user/agent smoke coverage.

---

## 2026-05-22 continuation - policy-training-status missing-export minima contract

### Problem

The zero-config smoke chain exposed a misleading read-only status surface:
`policy-training-status --output-format agent` reported
`raw_scored_mature=0/0`, `production_validation=0/0`, and blank nested summary
lines when the structural path-ranking export had never been created.

### Root Cause

`structural_path_ranking_target_training_status` returned early on missing
`structural_path_ranking_target_summary.json` with
`StructuralPathRankingTargetTrainingStatusSurface::default()`. That default path
zeroed the validation minima and left nested `target_row_validation` /
`feedback_observation_validation` summary lines empty, even though the status
contract elsewhere uses the configured 30-row validation thresholds.

### Fix

- Patched the missing-export early return in
  `src/application/entry_models/training_export.rs`.
- The missing-export surface now preserves the configured ranker validation
  minima/shortfalls:
  - `raw_scored_mature_min_rows=30`
  - `production_validation_min_rows=30`
  - `observation_validation_min_rows=30`
- Added explicit nested summary lines for:
  - `target_rows raw_scored_mature=0/30 production_validation=0/30 ready=false`
  - `observations mature=0/30 pending=0 total=0 ready=false`
- Kept the top-level missing-export summary wording unchanged so downstream
  consumers still see the absence of the export as the primary condition.

### Verification

- Discovery probe:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-audit-smoke-20260522 --refresh --agent`
    - passed
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-audit-smoke-20260522 --refresh --output-format json`
    - passed
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-smoke-20260522 --output-format agent`
    - before patch, showed the confusing `0/0` validation minima
- RED:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib policy_training_status_preserves_ranker_validation_minima_when_export_missing -- --nocapture`
    - failed before patch with `left: 0 right: 30`
- GREEN:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib policy_training_status_preserves_ranker_validation_minima_when_export_missing -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo test --lib policy_training_status_lists_registered_providers -- --nocapture`
  - `CARGO_TARGET_DIR=/tmp/ict-engine-command-matrix-target cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-audit-smoke-20260522 --output-format agent`
    - after patch, the same surface now reports `raw_scored_mature=0/30`,
      `production_validation=0/30`, and
      `observation_validation=0/30` with explicit nested summary lines

### Remaining Gaps

- This fixes a status-surface ambiguity only; it does not change runtime
  behavior or prove full audit completion.
- The broader audit still needs continued closed-loop surface review plus the
  remaining Done Definition evidence on the current tree.

---

## 2026-05-22 continuation - help_audit none-output policy classification guard

Current answer to "is this 100% complete?": no. This slice closes one
long-standing weak-evidence point in the command-output audit by turning the
remaining `none` surfaces into an explicit, test-checked policy, but full audit
completion is still unproven.

### Problem

`support/docs/command-output-contract.md` had a known open item:
the 23 commands with `output_mode_status=none` were counted but not enforced as
an intentional exception set. That left a regression gap: a future read-only
command could silently lose output-mode aliases and still pass basic counting.

### Root Cause

`support/scripts/help_audit.py` only reported aggregate counts
(`commands_with_no_output_modes`) and had no policy check for which commands
were allowed to remain `none`.

### Fix

- Added `EXPECTED_NO_OUTPUT_MODE_COMMANDS` to `support/scripts/help_audit.py`
  as the explicit allowlist for intentional no-output-mode surfaces.
- Added `none_output_mode_policy(rows)` to compute:
  - `unclassified_none_commands`
  - `missing_expected_commands`
  - `matches_expected`
  - expected/observed sets and counts
- Integrated policy verdict into report/summary:
  - new summary field: `none_output_mode_policy_matches_expected`
  - `status=pass` now requires `none_output_mode_policy_matches_expected=true`
- Added regression tests in `support/scripts/tests/test_help_audit.py`:
  - unclassified command case must fail policy match
  - exact expected set must pass policy match

### Verification

- RED:
  - `python3 -m unittest support.scripts.tests.test_help_audit -v`
    failed before implementation due to missing
    `EXPECTED_NO_OUTPUT_MODE_COMMANDS` / `none_output_mode_policy`.
- GREEN:
  - `python3 -m py_compile support/scripts/help_audit.py support/scripts/tests/test_help_audit.py`
  - `python3 -m unittest support.scripts.tests.test_help_audit -v`
    passed 4 tests.
  - `ICT_ENGINE_HELP_AUDIT_BIN=/tmp/ict-engine-command-matrix-target/debug/ict-engine python3 support/scripts/help_audit.py > /tmp/help_audit_policy_after.json`
  - `jq '.summary, .none_output_mode_policy' /tmp/help_audit_policy_after.json`
    reports:
    - `commands_with_no_output_modes=23`
    - `none_output_mode_policy_matches_expected=true`
    - `unclassified_none_commands=[]`
    - `missing_expected_commands=[]`

### Remaining Gaps

- This only hardens output-mode classification; it does not complete all P0/P1
  remediation goals.
- Full completion still requires:
  - unresolved `main.rs` extraction debt reduction,
  - continued P0 closed-loop verification on current tree,
  - remaining user-facing pain-point sweeps documented in this plan.

---

## 2026-05-22 continuation - done_definition_audit helper for repeatable closure evidence

Current answer to "is this 100% complete?": still no. This slice does not claim
completion; it introduces a repeatable audit helper to make that answer
evidence-backed and less manual.

### Problem

The plan's Done Definition remained mostly manual to verify each loop:

- lightweight doc/surface checks (`main.rs` growth, quickstart links, script governance),
- output-mode policy sanity (`help_audit` expected none-set),
- optional heavy gates (`cargo check/clippy/test` + smoke).

Without a single helper, evidence quality drifted by operator memory and each
pass cost extra tokens and repeated ad-hoc command glue.

### Root Cause

No `support/scripts/**` helper consolidated Done Definition gates with:

- zero-config safe defaults,
- opt-in heavy verification,
- JSON output suitable for handoff/automation,
- explicit unresolved gate list for fail-closed loops.

### Fix

- Added `support/scripts/done_definition_audit.py`.
- Default mode runs low-cost read-only checks:
  - `main_rs_line_guardrail`: parse baseline from
    `support/docs/main-rs-guardrails.md` and compare to live `src/main.rs` line
    count,
  - `quickstart_surface`: verify README links to consumer/contributor
    quickstarts and both quickstart docs exist,
  - `script_governance_surface`: verify `SCRIPTS.md` and
    `script_manifest.json` exist,
  - `help_audit_none_output_policy`: execute `help_audit.py` and require
    `none_output_mode_policy_matches_expected=true`.
- Added opt-in heavy checks behind flags/env (skip by default):
  - `--run-cargo-check` / `ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_CHECK`,
  - `--run-cargo-clippy` / `ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_CLIPPY`,
  - `--run-cargo-test` / `ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_TEST`,
  - `--run-smoke` / `ICT_ENGINE_DONE_DEFINITION_RUN_SMOKE`,
  - `--run-all-heavy` / `ICT_ENGINE_DONE_DEFINITION_RUN_HEAVY`.
- Added unit tests: `support/scripts/tests/test_done_definition_audit.py`.
- Registered governance surface:
  - `support/scripts/SCRIPTS.md`,
  - `support/scripts/script_manifest.json`.
- Maintained no-pollution behavior: no repo-local default state writes; smoke
  defaults to `/tmp/ict-engine-done-definition-audit-smoke` when explicitly
  enabled.

### Verification

- `python3 -m py_compile support/scripts/done_definition_audit.py support/scripts/tests/test_done_definition_audit.py`
- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
- `python3 -m unittest support.scripts.tests.test_help_audit -v`
- `python3 support/scripts/check_script_manifest.py`
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-light.json`
- `python3 support/scripts/done_definition_audit.py --run-smoke --output /tmp/ict-engine-done-definition-audit-smoke.json`
  (heavy optional gate probe; still fail-closed if unresolved checks remain)

### Remaining Gaps

- This helper improves repeatability only; it does not by itself make all Done
  Definition gates green.
- Full closure still needs periodic heavy gate refresh on the current tree,
  plus continued `main.rs` extraction and P0 closed-loop verification slices.

---

## 2026-05-22 continuation - Done Definition heavy gates closed on current tree

Current answer to "is this 100% complete?": no release claim. This slice closes
the current Done Definition audit helper's full gate set and records the exact
remaining boundary: release readiness still depends on the broader release
contract, but this maintenance gate is green on the live tree.

### Problem

The first full run of
`python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-heavy.json`
found unresolved heavy gates:

- `cargo_clippy_all_targets_deny_warnings`
- `cargo_test`

Those failures meant the new repeatable auditor was useful, but the repo still
could not honestly treat the Done Definition gate set as closed.

### Root Cause

- Two status shell adapters still used long argument lists after nearby shell
  adapters had moved to input structs:
  - `provider_status_shell`
  - `factor_mutation_status_shell`
- Structural path-ranker explicit artifact validation had one error branch that
  did not include the required flag/schema/recovery context.
- Registered-artifact runtime score selection could prefer a stale duplicate
  row sharing a `path_id` over the exact row for the current
  `candidate_set_id`.

### Fix

- Added `ProviderStatusShellInput` and `FactorMutationStatusShellInput` in
  `src/status_command.rs`, then updated the two `src/main.rs` call sites.
- Kept `FactorMutationStatusCommandInput` at the application command boundary
  so the shell adapter and application command both stay token-friendly and
  clippy-clean.
- Tightened structural path-ranker explicit artifact validation and test
  expectation for the required schema/recovery wording.
- Updated registered-artifact runtime row selection to prefer the current
  candidate set before falling back to same-`path_id` artifact rows.

### Verification

- `cargo clippy --all-targets -- -D warnings`
  - passed.
- `cargo test application::entry_models::training_export::tests::register_structural_path_ranking_trainer_artifact_requires_rule_or_tree_for_explicit_family -- --nocapture`
  - passed.
- `cargo test application::orchestration::structural_playbook::tests::path_ranker_runtime_prefers_current_candidate_row_over_stale_duplicate_artifact_row -- --nocapture`
  - passed.
- `python3 support/scripts/done_definition_audit.py --run-all-heavy --output /tmp/ict-engine-done-definition-audit-heavy.json`
  - `summary.status=pass`
  - `pass_count=8`
  - `fail_count=0`
  - `skip_count=0`
  - `unresolved=[]`
  - passed heavy gates include `cargo_check_all_targets`,
    `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
    `smoke_acceptance_tmp_state`.

### Remaining Gaps

- Done Definition auditor closure is green for the current tree, but this is
  not a release-ready claim.
- Continue using the auditor after future maintenance slices so heavy-gate
  drift is caught before handoff.
- Broader closed-loop/release criteria from repo `AGENT.md` still require
  separate fresh evidence before any publish/tag/release statement.

---

## 2026-05-22 continuation - zero-config closed-loop/privacy release-gate audit

Current answer to "is this 100% complete?": no. The Done Definition helper is
green, but the broader repo `AGENT.md` release gate still requires fresh
evidence that a clean consumer can inspect the chain without private paths,
keys, maintainer datasets, or hidden profile assumptions.

Dedicated handoff TODO for this slice:
`support/docs/plans/2026-05-22-zero-config-closed-loop-smoke-handoff-todo.md`.

### Active Slice

Run a fresh zero-config consumer smoke from `/tmp`, then inspect the actual
captured outputs and state artifacts against the release-gate checklist:

- no-profile provider behavior falls back to public/default data surfaces;
- human/agent outputs stay compact and token-friendly;
- outputs do not leak private paths, keys, tokens, or maintainer-local data;
- regime posterior and uncertainty are visible before claiming readiness;
- Pre-Bayes/filter, BBN/workflow snapshot, structural path-ranker/training
  status, execution tree trace, and feedback/update learning surfaces are
  inspectable or explicitly marked missing;
- any missing evidence becomes a concrete next remediation item, not a
  release-ready claim.

### Planned Evidence

- `STATE_DIR=/tmp/ict-engine-closed-loop-privacy-audit-20260522T1800Z`
- `OUT_DIR=/tmp/ict-engine-closed-loop-privacy-audit-20260522T1800Z/smoke-output`
- `bash support/scripts/smoke_acceptance.sh`
- targeted `jq` / `rg` readback over captured output and state files.

### Status

- fresh zero-config smoke passed under
  `/tmp/ict-engine-closed-loop-privacy-audit-20260522T1800Z`.
- inspected outputs:
  - `provider_status.out`: no-profile public fallback visible;
  - `analyze_demo.out`: compact human output and observe-only decision;
  - `workflow_agent.out`: regime/filter/BBN surfaces visible, but
    `latest_structural_feedback=null`;
  - `policy_training_agent.out`: structural path-ranker stays fail-closed with
    `update_runs=0` and `0/30` maturity shortfalls.
- ran explicit demo-safe learning update:
  `cargo run --quiet -- update --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-privacy-audit-20260522T1800Z --outcome breakeven --pnl 0`
  with output captured in `smoke-output/update_demo.out`.
- post-update evidence:
  - `DEMO/update_runs.json`: `update_runs_len=1`,
    `feedback_records_applied=1`,
    `structural_learning_credit_class=fractional_breakeven`,
    `execution_gate_status=execution_blocked`;
  - `DEMO/learning_state.json`: `feedback_history_len=1`,
    latest feedback `realized_outcome=breakeven`;
  - `smoke-output/workflow_agent_after_update.out`: source phase moved to
    `update` while execution remains blocked;
  - `smoke-output/policy_training_agent_after_update.out`: `update_runs=1`,
    target export ready, ranker runtime still disabled/not ready because
    mature validation rows remain `0/30`.
- privacy scan after update over `smoke-output` produced no matches for
  private path/secret patterns.
- remediation applied in this slice: `support/scripts/smoke_acceptance.sh` now
  includes a zero-config demo update step using
  `SMOKE_UPDATE_OUTCOME=breakeven` and `SMOKE_UPDATE_PNL=0` defaults, followed
  by after-update workflow/policy status readback. The script now asserts
  `feedback_records_applied=1`, `source_phase=update`, and `update_runs=1`
  before passing. The defaults are smoke-only and can be overridden by
  consumers.

### Verification

- `bash -n support/scripts/smoke_acceptance.sh`
  - passed.
- `python3 -m unittest support.scripts.tests.test_smoke_acceptance -v`
  - `Ran 3 tests`; `OK`.
- `git diff --check -- support/scripts/smoke_acceptance.sh support/scripts/tests/test_smoke_acceptance.py support/docs/smoke-acceptance.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  - passed.
- `STATE_DIR=/tmp/ict-engine-smoke-acceptance-after-update-20260522T1819Z OUT_DIR=/tmp/ict-engine-smoke-acceptance-after-update-20260522T1819Z/smoke-output bash support/scripts/smoke_acceptance.sh`
  - passed.
  - `DEMO/update_runs.json`: `update_runs_len=1`,
    `realized_outcome=breakeven`, `feedback_records_applied=1`,
    `structural_learning_credit_class=fractional_breakeven`.
  - `policy_training_agent.out`: `update_runs=1`,
    `structural_path_ranking_target.export_ready=true`,
    `trainer_manifest_ready=true`.
  - `workflow_agent_after_update.out`: source phase `update`,
    `execution_gate_status=execution_blocked`,
    `blocking_status=bridge_needs_confirmation`.
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-light-after-smoke-update.json`
  - `summary.status=pass`, `pass_count=4`, `fail_count=0`,
    `skip_count=4`, `unresolved=[]`.
- after adding smoke assertions:
  - `bash -n support/scripts/smoke_acceptance.sh` passed.
  - `python3 -m unittest support.scripts.tests.test_smoke_acceptance -v`
    passed 3/3.
  - `STATE_DIR=/tmp/ict-engine-smoke-acceptance-asserted-update-20260522T1825Z OUT_DIR=/tmp/ict-engine-smoke-acceptance-asserted-update-20260522T1825Z/smoke-output bash support/scripts/smoke_acceptance.sh`
    passed with the built-in assertions active.
  - `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-light-after-smoke-assertions.json`
    passed with `summary.status=pass`, `pass_count=4`, `fail_count=0`,
    `skip_count=4`, `unresolved=[]`.

### Remaining Boundary

- The reusable zero-config smoke now proves the demo update/writeback path.
- This still is not a release-ready or trade-ready claim: structural
  path-ranker runtime remains disabled/not ready until mature validation rows
  reach the configured threshold, and DEMO `breakeven` is smoke-only feedback.

## Pollution Cleanup - Nested macOS Metadata

Claim: done for focused cleanup, owner Codex current turn, claimed
2026-05-22 20:28:08 +0800.

### Finding

`git status --short` still surfaced nested macOS `.DS_Store` files under
`src/` and `support/` even though the root `.gitignore` ignored only
`/.DS_Store`. This is a low-level repo hygiene bug: it keeps recurring local
Finder metadata in the working tree and makes audit/commit boundaries noisier.

Observed untracked files before cleanup:

- `src/.DS_Store`
- `src/application/.DS_Store`
- `src/bbn/.DS_Store`
- `src/domain/.DS_Store`
- `support/.DS_Store`
- `support/docs/.DS_Store`
- `support/paper2code/.DS_Store`

### Remediation

- Changed `.gitignore` from root-only `/.DS_Store` to recursive
  `**/.DS_Store`.
- Deleted only the seven untracked `.DS_Store` files listed above.
- No source, docs, run roots, or tagged artifacts were deleted.

### Verification

- `git status --short -- .gitignore .DS_Store src/.DS_Store src/application/.DS_Store src/bbn/.DS_Store src/domain/.DS_Store support/.DS_Store support/docs/.DS_Store support/paper2code/.DS_Store`
  - showed only `.gitignore` and this plan doc as modified; the seven nested
    `.DS_Store` paths no longer appear.
- `git diff --check -- .gitignore support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  - passed.
- `git status --ignored --short -- src/.DS_Store src/application/.DS_Store src/bbn/.DS_Store src/domain/.DS_Store support/.DS_Store support/docs/.DS_Store support/paper2code/.DS_Store`
  - returned no tracked/untracked rows after deletion; future nested files will
    match `**/.DS_Store`.

### Boundary

- This closes one repo-hygiene/no-pollution pain point only.
- It does not prove release readiness, full dirty-tree cleanliness, or
  trade-usable factor promotion.

## Root Scratch And Local Agent-Material Classification

Claim: done for focused scratch cleanup and classification, owner Codex
current turn, claimed 2026-05-22 20:33:28 +0800.

### Finding

The root worktree still has three different untracked classes:

- empty scratch file: `0.5201009511947632`;
- local Aegis workspace: `docs/aegis/**`;
- local agent-skill material: `skills/**`.

`git ls-files docs skills 0.5201009511947632` returned no tracked paths, so
none of these are currently versioned release/runtime inputs.

### Classification

- `0.5201009511947632` is a zero-byte scratch file. The value is meaningful in
  historical text as a CatBoost split threshold, but the root file itself has no
  content and no consumer/runtime role.
- `docs/aegis/**` contains indexed design/work artifacts with real Board A/B
  evidence references. It is untracked local agent material, not immediate
  release source.
- `skills/**` contains optional agent-facing skill docs and a manifest stating
  `runtime_consumed_by_ict_engine=false`. It is useful reference material, but
  not a typed runtime contract.

### Remediation

- Deleted the empty root scratch file `0.5201009511947632`.
- Deleted already-ignored local metadata:
  - `docs/.DS_Store`
  - `docs/aegis/.DS_Store`
  - `skills/.DS_Store`
- Preserved `docs/aegis/**` and `skills/**` content for a later explicit
  decision: either migrate durable pieces into `support/docs/...`, or ignore
  the local agent-material roots if they must stay outside release source.

### Verification

- `git status --short -- 0.5201009511947632 docs/.DS_Store docs/aegis/.DS_Store skills/.DS_Store docs skills`
  - no longer shows `0.5201009511947632` or any `.DS_Store`;
  - still shows preserved `docs/aegis/**` and `skills/**` as untracked local
    agent material.
- `git diff --check -- support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  - passed.
- `test ! -e 0.5201009511947632 && test ! -e docs/.DS_Store && test ! -e docs/aegis/.DS_Store && test ! -e skills/.DS_Store`
  - passed.

### Remaining Decision

- Decide later whether `docs/aegis/**` and `skills/**` should be:
  - migrated into `support/docs/...` as durable repo artifacts, or
  - ignored as local agent workspace material.
- Do not silently delete them; they contain indexed design/evidence content and
  optional agent-skill contracts.

## 2026-05-22 continuation - root agent material boundary

Current answer to "is this 100% complete?": no. This slice closes one concrete
repo-hygiene gap, but factor promotion, clean release export, and full
dirty-tree closure remain unproven.

### Finding

The preserved untracked roots `docs/aegis/**` and `skills/**` were still visible
in `git status --short`. Current readback showed:

- `git check-ignore -v docs/aegis/README.md skills/README.md` had no match.
- `docs/aegis/README.md` describes a local Aegis workspace for durable
  design/spec artifacts.
- `skills/manifest.json` declares `runtime_consumed_by_ict_engine=false`.
- `skills/README.md` says these skills are optional agent-facing contracts, not
  runtime inputs.

### Remediation

- Added `.gitignore` entries for root `/docs/` and `/skills/`.
- Added `support/docs/local-agent-material-boundary.md` as the versioned public
  boundary:
  - public docs belong under `support/docs/`;
  - root local agent material is opt-in operator context;
  - release exports and zero-config consumers must not depend on those roots;
  - behavior changes must move into typed config, flags, schemas, fixtures, or
    tests.
- Did not delete `docs/aegis/**` or `skills/**`; user-local content is preserved
  but no longer pollutes default source/release status.

### Verification

- `git check-ignore -v docs/aegis/README.md docs/aegis/INDEX.md skills/README.md skills/manifest.json`
  - all four paths now match root `/docs/` or `/skills/` rules in
    `.gitignore`.
- `git diff --check -- .gitignore support/docs/local-agent-material-boundary.md support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
  - passed.
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-after-agent-boundary-light.json`
  - passed with `summary.status=pass`, `pass_count=4`, `fail_count=0`,
    `skip_count=4`.

### Remaining Broad Blockers

- Practical factor diffusion is still unproven: latest readback had
  `trade_usable=true: 0` and `promotion_allowed=true: 0`.
- Release mirror completion is still unproven: a clean sanitized export and
  explicit publish/tag confirmation are still required.
- The worktree remains broadly dirty from other lanes; commit only this narrow
  boundary slice if verification passes.
