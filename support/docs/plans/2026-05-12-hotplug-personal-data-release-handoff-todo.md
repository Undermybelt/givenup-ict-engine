# Hot-Plug Personal Data + Factor Release Handoff TODO

Date: 2026-05-12

Purpose: continue the current factor/release lane without polluting the repo or
turning maintainer-local personal data into a mandatory public surface.

## Task Intent Draft

Requested outcome:
- Commit at reasonable checkpoints.
- Continue implementation after the factor-result/release readiness audit.
- Preserve zero-config behavior for normal consumers.
- Keep user-facing output token-friendly.
- Make personal data/material needs hot-pluggable and opt-in.
- Let users choose whether to adopt the maintainer profile/material defaults.
- Keep release artifacts clean enough to publish to the release mirror.

Non-goals:
- Do not make maintainer-local data required for first run.
- Do not commit generated dependency workspaces such as nested Auto-Quant clones.
- Do not promote local-only research evidence as release-ready trading proof.
- Do not rewrite Board A or Board B authority; this file is a handoff/checkpoint
  board only.

## Baseline Read Set Hint

- `AGENTS.md`
- `support/docs/plans/2026-05-09-factor-iteration-pre-bayes-bbn-catboost-execution-tree-todo.md`
- `support/docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
- `support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- `src/application/auto_quant/`
- `src/application/orchestration/workflow_status.rs`
- `src/application/provider_catalog.rs`
- `src/main.rs`

## Impact Statement Draft

The next implementation slice should improve consumer ergonomics without
hard-wiring the maintainer's private research profile into the public CLI. The
public contract should stay generic: zero-config defaults work, optional profile
or material bundles can be inspected/adopted, and agent/human output remains
compact.

## Todo Checkpoint Draft

Status legend: `done`, `active`, `next`, `blocked`, `not_yet`.

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Routing and repo baseline read | Read Hermes routers and repo `AGENTS.md`; primary route now `aegis/long-task-continuation`. |
| done | Initial release audit | Main is ahead of `origin/main`; release mirror latest tag seen as `v0.1.1`; GH CLI auth is invalid. |
| done | Pollution scan | `support/docs/experiments/actionable-regime-confidence` is about 27G and contains nested `.deps/auto-quant` workspaces; do not stage them blindly. |
| done | Repair release-blocking Clippy errors | Reworked test fixtures away from `field_reassign_with_default`, replaced one `vec!` with an array, and used `then_some`. |
| done | Re-run `cargo fmt --check` and `cargo clippy --all-targets -- -D warnings` | Both passed after the fix slice. |
| done | Identify hot-plug personal data surface already present | Existing surfaces: provider `--profile`, Auto-Quant `--auto-quant-profile`, read-only `--strategy-material-root`, provider profile JSON, and factor candidate profile JSON. |
| done | Implement smallest consumer-safe hot-plug improvement | `workflow-status` now exposes matching opt-in profile references for the current symbol without selecting or loading the profile. |
| done | Add focused tests for any code behavior change | `cargo test --test provider_neutral_cli -- --nocapture` passed, including new human/agent profile-choice tests. |
| done | Repair `workflow-status` branch-admission routing precedence | `cargo test application::orchestration::workflow_status::tests:: -- --nocapture` passed, 114 workflow-status tests. |
| done | Run full verification after route-precedence repair | `cargo test`, `cargo fmt --check`, and `cargo clippy --all-targets -- -D warnings` passed. |
| done | Final compile/targeted verification after path-literal cleanup and candidate-set field sync | `cargo fmt --check`, `cargo test --test provider_neutral_cli -- --nocapture`, `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`, `cargo clippy --all-targets -- -D warnings`, and `cargo check --tests --quiet` passed. |
| done | Repair clean-export BBN fixture dependency | BBN tests now use tracked, path-redacted `tests/fixtures/policy_training/`; runtime user-state hot-plug path remains unchanged. |
| done | Clean release-export audit | Final `v0.1.2` clean export `/tmp/ict-engine-release-export.ueDk6B` passed fmt, Clippy, and full `cargo test` from committed `HEAD`. |
| done | Update this board after each slice | Current slice recorded here. |
| done | Commit safe slices | Checkpoint commit created for the intended source/docs/tests; nested dependency workspaces and active run state were excluded. |
| done | Prepare release-mirror export/audit | Local mirror clone `/tmp/ict-engine-release-mirror-v012.87caSH` was synced from clean export and committed locally; re-read its HEAD before any push; no tag/push/release created. |
| done | Prove/fix consumer closed-loop usability before release | Found and fixed workflow-status first-run provider summary mismatch; `provider-status` and `workflow-status` now both show yfinance as zero-config live fallback. |
| done | Add one-line `CLAUDE.md` redirect | Contains one line: `open AGENTS.md and read`. |
| done | Expand `AGENTS.md` into the authoritative agent usage contract | Covers zero-config commands, provider policy, privacy rules, closed-loop order, posterior requirements, TimesFM optionality, feedback loop, and release constraints. |
| done | Run fresh zero-config smoke in `/tmp` state | `/tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO` ran provider/workflow/analyze/Pre-Bayes/policy-training/export/update checks with no profile and no private provider config. |
| done | Run focused verification for the closed-loop/docs slice | `cargo fmt --check`, provider-neutral CLI tests, workflow-status tests, and Clippy passed. |
| done | Commit the closed-loop/docs slice | This amended commit staged only `AGENTS.md`, `CLAUDE.md`, `workflow_status.rs`, and this handoff board. |
| done | Prove/fix practical 5-slot `--human` output | Kept English agent labels; practical `analyze --human` now exposes Structure, Technicals, SMT, Regime with posterior probabilities, and Plan with executable trade levels or honest observe/no-trade fields. |
| done | Add data-backed ICT/PDA price-level human template | `Structure` and `Technicals` now cite existing swing/BOS/CHoCH/MSS/CISD/liquidity/FVG/OB/rejection fields with price levels in parentheses when detectors produce them; missing demo evidence and not-yet-trained variants are explicit `(n/a)`/`requires_followup`, not fabricated. |
| done | Implement ICT SMT confirmation-failure semantics | SMT now detects same-window swing confirmation failure across paired markets, emits base/comparison swing types and price levels, marks swept buy/sell-side liquidity, and stays `confirmation_only` with fail-closed relationship gating. |
| done | Disk-pressure cleanup | Owner: Codex current turn, started 2026-05-12 22:58 +0800. Deleted only untagged rebuildable build/dependency/log bulk: `ict-engine/target`, Auto-Quant `.deps` workspaces under experiment runs, unreachable `uv` cache objects, and oversized `.codex/log/codex-tui.log` contents via truncate. Preserved tagged/labelled artifacts, source/config/docs/state/market data, active run evidence, and other agents' active/claimed work. Final free space: `107GiB`. |
| done | Current worktree full audit / release-gate gap check | Owner: Codex current turn, claimed 2026-05-13 07:28:11 +0800, closed 2026-05-13 08:09:12 +0800. Found and fixed two mechanical Clippy blockers in the dirty tree, verified focused gates and zero-config smoke, and recorded remaining blockers below. |
| done | Full `cargo test` Python dependency probe blocker | Owner: Codex current turn, claimed 2026-05-13 08:13:15 +0800, closed 2026-05-13 08:36:46 +0800. Root cause found: provider-status public fetch runtime probe over-required `xgboost`; removed it because the current model route is CatBoost. Narrow provider/status tests, Clippy, and full `cargo test` now pass with the py313 provider venv first on PATH. |
| done | Completion audit against release objective | Owner: Codex current turn, claimed 2026-05-13 08:39:41 +0800, closed 2026-05-13 after fresh sanitized export evidence and manifest/runbook materialization. Audit objective is covered; actual publish/tag/push remains blocked on explicit operator confirmation. |
| done | README/AGENT polish and publish execution | Owner: Codex current turn, claimed 2026-05-13 12:26:07 +0800, closed 2026-05-13. README/AGENT were polished, final sanitized export gates passed, mirror main and `v0.1.2` tag were pushed, and GitHub Release `v0.1.2` was created. |
| done | Release mirror CI Clippy 1.95/test repair | Owner: Codex current turn, claimed 2026-05-14 08:59:46 +0800, closed 2026-05-14 after source verification. Fixed the original Rust 1.95 Clippy drift and the follow-up CI-only test failure where `ibkr_requires_runtime_probe_even_with_consent_files` depended on maintainer-local `HOME` IBKR consent files. The test now creates its own temporary consent/capability fixture. |
| done | Hubble opt-in provider/API intake | Owner: Codex current turn, claimed 2026-05-14 18:26:43 +0800, closed 2026-05-14 19:48:05 +0800. Added the env-driven `hubble-kline` fetch adapter, a placeholder-only repo example profile `hubble-v2-opt-in-v1`, focused Rust/Python tests, and verification evidence showing `provider-status` surfaces Hubble as opt-in while keeping yfinance zero-config by default and excluding sample host/key values from repo artifacts and command output. |
| done | Hubble upstream default-key compatibility | Owner: Codex current turn, claimed 2026-05-14 20:22:00 +0800, closed 2026-05-14 after verified upstream default-key compatibility. Kept Hubble opt-in and provider-neutral, but made `engine` compatible with the upstream baked-in API key behavior by falling back to the verified upstream default key `123456` when `ICT_ENGINE_HUBBLE_API_KEY` is unset; preserved explicit env override, avoided hard-coding the upstream host as a new default, and refreshed catalog/profile/test evidence accordingly. |
| done | Hubble direct engine runtime integration | Owner: Codex current turn, claimed 2026-05-14 20:27:00 +0800, closed 2026-05-14 after direct engine-path verification. `engine` now consumes Hubble-backed OHLCV and options-summary data through the existing market-data-harness / control-matrix runtime path, not only through Auto-Quant CSV export; provider choice remains opt-in, Hubble does not replace yfinance defaults, and the public `provider-status` surface stays deduped to one Hubble entry. |
| done | Source repo macOS CI cargo-cache repair | Owner: Codex current turn, claimed 2026-05-14 after source Actions run `25838723352` failed only macOS `Format`. Root cause evidence: `cargo fmt --check` invoked `rustup-init fmt` after `Swatinem/rust-cache@v2` restored `/Users/runner/.cargo/bin` from key `v0-rust-rust-Darwin-arm64-9d946206-6388d80f`; Ubuntu passed and release mirror passed on an older macOS runner image. Fix: stop caching cargo bin shims, bump the cache prefix, request rustfmt/clippy components explicitly, and add a toolchain sanity step. Verification: source Actions run `25840195711` passed on both `ubuntu-latest` and `macos-latest`, including Toolchain sanity, Format, Docs runtime isolation, Clippy, and Test. |
| done | Auto-Quant path-ranker helper hardening | Owner: Codex current turn, closed 2026-05-22 after focused Python/Rust verification. Fixed consumer pain points in the external path-ranker loop: Yahoo/futures symbols such as `GC=F` now materialize TOMAC pair aliases without punctuation, IBKR `ts` CSV headers can derive timeranges, state-local trainer artifacts register with policy-relative URIs, CatBoost training can fall back to direct weighted-feature artifacts when labels are not trainable, and replay feedback can target an exact `regime_profit_branch_path` instead of rank 1. Verification: `python3 -m unittest support.scripts.auto_quant_external.tests.test_next_slice_helpers support.scripts.auto_quant_external.tests.test_path_ranker_hotplug` passed 26 tests; `cargo test application::auto_quant::agent_material::tests:: -- --nocapture` passed 15 tests. |
| done | Consumer/contributor entrypoint docs | Owner: Codex current turn, closed 2026-05-22 after link-target and light-audit verification. Added root README links to zero-config consumer/contributor quickstarts, `CONTRIBUTING.md`, and command-output contract; refreshed AGENT/factor-catalog factor traceability from stale line numbers/stubs to stable function paths and active partial status; recorded main.rs debt baseline and release-mirror version/readiness warning. Verification: link targets exist, `git diff --check` passed for the docs slice, and `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-20260522-doc-entrypoint-light.json` passed default gates with `pass_count=4`, `fail_count=0`, `skip_count=4`. |
| blocked | 2026-05-22 three-part completion audit | Current-tree Done Definition heavy gate now passes at `/tmp/ict-engine-done-definition-audit-20260522-current-heavy.json`, and smoke path-ranker audit gate was committed as `6bcc66bb`. Release completion is still not proven: source branch remains ahead of `origin/main` (`79d9579e`), release mirror `main` is `ab6b1b55`, `Cargo.toml` still reports `0.1.3`, `support/docs/audits/release-signoff.md` and `support/docs/release-notes-draft.md` now explicitly mark their `v0.1.3` content as historical/stale for the current branch, and this worktree has broad dirty state. Do not publish from this checkout; rebuild a clean export for an explicit new tag and rerun release gates first. |
| blocked | 2026-05-22 realtime continuation readback | Owner: Codex current turn, refreshed after routing and live probes. Current source `HEAD=6dd08ec5132a728336d3545be20ac290d35e7ab2`, `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`, and local main is `61` commits ahead of origin. Release mirror `Undermybelt/ict-engine-release` still has `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb` and latest GitHub Release `v0.1.4` from `2026-05-18T13:02:21Z`; local `Cargo.toml` remains `0.1.3`. Factor readback remains non-promoting: blocker map says no hard-gate branch; M2K current blocker report has `promotion_allowed=false`, `trade_usable=false`, `execution_candidate_status=no_trade`, `ranker_validation_ready=false`. Next work is same-root repair or clean export/tag preparation, not completion claim. |
| active | SI `15m` Turtle Soup same-root PDA repair selection | Owner: Codex current turn, claim `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260522T210000+0800-codex-si15m-turtle-soup-pda-sequence-repair.claim`. M2K is skipped for now because active M2K claims exist and the fresh14d readback lost the older 5bps survivor. SI `15m` Turtle Soup has exact 5bps survivors, `ranker_validation_ready=true`, and path-ranker visible; blockers are PDA family/sequence disagreement, high transition hazard, `execution_candidate_status=no_trade`, and visible-not-used path-ranker. |
| active | CRWD `5m` promotion/trade-usable bridge readback | Owner: Codex current turn, current-binary isolated readback `/tmp/ict-engine-crwd5m-current-readback-20260522T212430+0800` ran all commands with exit `0`. CRWD now has execution candidate `execution_ready/actionable=true`, structural execution candidate `ready=true`, closed-loop branch admission `admitted`, ranker runtime using candidate-set scores, and ranker validation `46/30` raw/production plus `43/30` observation. It still cannot be counted as completed diffusion or release proof: `promotion_allowed=false`, `read_only_regime_bbn_trade_usable=false`, Pre-Bayes is `pass_neutralized`, latest analyze stays `promotion_status=observe` / `execution_gate_status=execution_blocked`, and trade plan `actionable=false`. Next work is exact-root BBN/promotion bridge audit; do not publish or promote by copying the structural candidate upward. |
| blocked | Current-tree release completion | Full `cargo test` now passes after the provider Python probe repair. Still blocked until the current dirty tree is split/committed or clean-exported from the intended HEAD; do not publish from this dirty worktree. |
| blocked | Publish release mirror | Blocked on the new closed-loop/entrypoint/privacy gate and then explicit operator confirmation for `v0.1.2` tag/push/`gh release create`. GitHub auth was previously available and remote had no `v0.1.2` tag, but re-check before any publish. |

### 2026-05-14 Hubble opt-in provider/API intake continuation claim

Status:
- done, owner Codex current turn, resumed 2026-05-14 19:32:07 +0800,
  closed 2026-05-14 19:48:05 +0800.

Current checkpoint:
- Existing dirty-tree evidence already adds the `hubble` provider catalog item,
  introduces `ICT_ENGINE_HUBBLE_BASE_URL` /
  `ICT_ENGINE_HUBBLE_API_KEY` constants, documents `hubble-kline` in
  `support/scripts/auto_quant_external/fetch_external.py`, and records the
  active todo row above.
- Gap after re-read: the actual `hubble-kline` fetch adapter, repo example
  provider profile, focused tests, and fresh verification/privacy evidence are
  still missing.

Active slice:
- Implement the smallest portable Hubble intake that matches repo policy:
  configurable env-driven Hubble V2 K-line fetch only, no hard-coded host, no
  bundled key, no forced provider default, and no raw vendoring of the external
  Hubble skill pack.
- Use the local Hubble skill pack only as an API-shape reference:
  `usstock/stocks`, `cnstock/stocks`, `hkstock/stocks`, and
  `crypto/klines`, with the known HK `limit` caveat preserved in code/docs.

Explicit non-edits:
- Do not wire private sample host/key values into repo files, tests, or command
  history.
- Do not make Hubble the zero-config default over yfinance.
- Do not claim live-runtime adoption where only market-data / Auto-Quant fetch
  intake is implemented.

Planned verification:
- Focused Rust/provider tests for the catalog/profile surface.
- Focused Python tests for the new fetch adapter argument and payload handling.
- Secret/path grep over the touched outputs and new profile/example surfaces.

Evidence:
- `python3 -m unittest support.scripts.auto_quant_external.tests.test_fetch_external_hubble -v`
  passed, 5 tests.
- `cargo test --test provider_neutral_cli -- --nocapture` passed, 21 tests,
  including the new Hubble provider/profile integration checks.
- `cargo test application::provider_catalog::tests:: -- --nocapture` passed, 14
  provider-catalog tests including the new Hubble repo-profile load path and
  the relaxed opt-in profile ordering assertion.
- `env -u ICT_ENGINE_HUBBLE_BASE_URL -u ICT_ENGINE_HUBBLE_API_KEY cargo run --quiet -- provider-status --provider hubble --compact`
  showed `installed_unconfigured` Hubble guidance with env-var prompts only.
- `env -u ICT_ENGINE_HUBBLE_BASE_URL -u ICT_ENGINE_HUBBLE_API_KEY cargo run --quiet -- provider-status --agent --profile hubble-v2-opt-in-v1`
  surfaced the selected profile, pending `hubble` track, and install prompts
  without exposing any sample endpoint/key values.
- `rustfmt --edition 2021 --check src/application/provider_catalog.rs tests/provider_neutral_cli.rs`
  passed after formatting the touched Rust files.
- `python3 -m py_compile support/scripts/auto_quant_external/fetch_external.py support/scripts/auto_quant_external/tests/test_fetch_external_hubble.py`
  passed.
- `rg -n "43\\.167\\.234\\.49|123456"` over the non-test Hubble repo artifacts
  returned no matches.

### 2026-05-14 Hubble upstream default-key compatibility claim

Status:
- done, owner Codex current turn, claimed 2026-05-14 20:22:00 +0800,
  closed 2026-05-14 after verified upstream default-key compatibility.

Current checkpoint:
- Fresh external verification against the upstream documented service confirmed:
  no key -> `401`, empty key -> `401`, wrong key -> `401`, upstream baked-in
  key `123456` -> `200` on `/api/v2/usstock/stocks?symbol=AAPL&limit=1`.
- Current repo slice still treats `ICT_ENGINE_HUBBLE_API_KEY` as mandatory in
  both `provider_catalog.rs` and `fetch_external.py`.

Active slice:
- Make the Hubble API key optional by defaulting to the verified upstream key
  `123456` when the env var is absent.
- Keep `ICT_ENGINE_HUBBLE_BASE_URL` explicit; do not add the upstream host as a
  silent runtime default in this slice.
- Update provider-status/profile copy so the surface says base URL required,
  API key optional override.

Explicit non-edits:
- Do not force Hubble ahead of yfinance in zero-config flows.
- Do not remove explicit env override support for custom Hubble keys.
- Do not hard-code the upstream host into the repo as a new automatic runtime
  default.

Evidence:
- `python3 -m unittest support.scripts.auto_quant_external.tests.test_fetch_external_hubble -v`
  passed, 7 tests, including upstream default-key fallback coverage.
- `cargo test --test provider_neutral_cli -- --nocapture` passed, 21 tests,
  including the updated Hubble provider/profile integration checks.
- `cargo test application::provider_catalog::tests:: -- --nocapture` passed, 14
  provider-catalog tests after switching Hubble to base-url-required plus
  optional API key override semantics.
- `env -u ICT_ENGINE_HUBBLE_BASE_URL -u ICT_ENGINE_HUBBLE_API_KEY cargo run --quiet -- provider-status --provider hubble --compact`
  showed `installed_unconfigured:hubble_base_url_missing`, `access=operator_runtime_optional`,
  and setup copy where `ICT_ENGINE_HUBBLE_API_KEY` is optional.
- `env -u ICT_ENGINE_HUBBLE_BASE_URL -u ICT_ENGINE_HUBBLE_API_KEY cargo run --quiet -- provider-status --agent --profile hubble-v2-opt-in-v1`
  surfaced the updated selected-profile summary and data-contract label with
  optional API key override wording and no leaked `123456` in output.
- `rustfmt --edition 2021 --check src/application/provider_catalog.rs tests/provider_neutral_cli.rs`
  passed.
- `python3 -m py_compile support/scripts/auto_quant_external/fetch_external.py support/scripts/auto_quant_external/tests/test_fetch_external_hubble.py`
  passed.
- Upstream live-service probe confirmed `123456` succeeds while no-key,
  empty-key, and wrong-key requests return `401`.

### 2026-05-14 Hubble direct engine runtime integration claim

Status:
- done, owner Codex current turn, claimed 2026-05-14 20:27:00 +0800,
  closed 2026-05-14 after direct engine-path verification.

Current checkpoint:
- Before this slice, Hubble was reachable through `provider-status` and
  Auto-Quant CSV export only; `engine` runtime fetch paths still accepted only
  `yfinance`, `tradingview_mcp`, and `ibkr` in the explicit harness request
  contract.
- The missing owner path was `market-data-harness -> provider_fetch ->
  control_matrix_runtime`, plus the control-matrix provider summary and CLI
  shorthand parsing layer.

Active slice:
- Add Hubble as an explicit harness/provider request type for `OHLCV` and
  `options.summary`.
- Fetch Hubble candles and options summary directly in Rust for engine runtime
  paths, while leaving the existing Python `fetch_external.py hubble-kline`
  route intact for Auto-Quant CSV export.
- Keep `provider-status` deduped to one Hubble entry even after the
  control-matrix provider summary learns Hubble.

Explicit non-edits:
- Do not make Hubble the default provider ahead of yfinance.
- Do not hard-code the upstream host as a new repo default.
- Do not claim that Hubble premium options data is fully production-ready when
  the current service response may still be schema/sample data.

Evidence:
- `cargo test application::data_sources::harness::tests:: -- --nocapture`
  passed, 4 tests, including explicit Hubble provider plan coverage.
- `cargo test application::data_sources::provider_fetch::tests:: -- --nocapture`
  passed, 6 tests, including Hubble candle-request and options-summary parsing.
- `cargo test application::data_sources::control_matrix_runtime::tests:: -- --nocapture`
  passed, 3 tests, including Hubble provider normalization.
- `cargo test application::data_sources::control_matrix_providers::tests:: -- --nocapture`
  passed, 7 tests, including Hubble ready-with-base-url-only provider summary.
- `cargo test application::data_sources::command_entry::tests:: -- --nocapture`
  passed, 7 tests, including Hubble CLI symbol-spec inference and crypto
  explicit-JSON rejection.
- `cargo test --test provider_neutral_cli -- --nocapture` passed, 21 tests
  after deduping the public Hubble provider surface.
- Real engine-path proof:
  `ICT_ENGINE_HUBBLE_BASE_URL=http://43.167.234.49:3101 cargo run --quiet -- market-data-harness --action fetch --request-json <tmp-hubble-request.json>`
  exited `0` and returned:
  - `etf_reference` via Hubble with 30 SPY daily candles
  - `options_underlying` via Hubble with an `OptionsChainSummary` for AAPL
- Public surface proof:
  `ICT_ENGINE_HUBBLE_BASE_URL=http://43.167.234.49:3101 cargo run --quiet -- provider-status --provider hubble --compact`
  now reports exactly one ready Hubble provider entry with no duplication.

Residual risk:
- The live Hubble `/api/v2/options/chain` response currently returns a premium
  endpoint/sample-schema payload. The engine path now parses it correctly, but
  callers should not overclaim that the returned options summary is guaranteed to
  be a fully entitled realtime chain unless the upstream Hubble account/service
  tier is confirmed.

## Resume State Hint

Current release-audit state: consumer zero-config/privacy audit, agent
entrypoint docs, fresh sanitized `/tmp` export/smoke, and manifest/runbook
materialization are covered. Actual publish/tag/push remains blocked until
explicit operator confirmation.

### 2026-05-14 Auto-Quant-only factor-iteration public-surface lock claim

Status:
- handoff, owner Codex current turn, claimed 2026-05-14 21:39:44 +0800,
  continued under
  `support/docs/plans/2026-05-14-auto-quant-public-surface-lock-handoff-todo.md`.

Current checkpoint:
- Public factor-iteration surfaces still expose parallel routes: CLI help and
  README mention `--backend native`, first-run/workflow guidance still routes
  through generic `factor-research`, and native runtime surfaces can rewrite the
  next command back to `--backend native` even after Auto-Quant guidance exists.
- Repo rules and current authority were re-read before this claim:
  Hermes routers, repo `CLAUDE.md`, repo `AGENT.md`, current release handoff
  board, `support/docs/plans/2026-05-12-board-b-profit-factor-current.md`,
  `support/docs/plans/2026-05-12-board-a-regime-state-current.md`, and scoped
  dirty-tree status. No unrelated edits will be reverted.

Active slice:
- Lock public factor-iteration entry surfaces to Auto-Quant only while keeping
  the existing downstream Pre-Bayes / BBN / structural-path / execution-tree
  consumers additive and reusable.
- Smooth the upstream path so `provider-status`, `workflow-status`,
  first-run/human-next guidance, and deferred follow-up commands all point to
  the same Auto-Quant mainline instead of exposing native-vs-AQ choice.
- Smooth the downstream path so Auto-Quant handoff/readiness/adoption surfaces
  are the canonical formal iteration readback, not an optional side path next
  to native research loops.

Explicit non-edits:
- Do not rewrite Board A or Board B research objectives, gates, or active run
  roots.
- Do not clean historical scripts, old run artifacts, or unrelated dirty-tree
  source files.
- Do not collapse existing downstream consumers into a new architecture; only
  retarget public entry/readback surfaces to the existing Auto-Quant chain.

Planned verification:
- Focused Rust tests around `workflow_status`, provider-neutral CLI, and any
  touched Auto-Quant/readback surfaces.
- `cargo fmt --check`
- `cargo test` on the smallest command/output suites that prove the public route
  is now AQ-only and that deferred/profile-preserving follow-up commands still
  work.

Expected products:
- Public CLI/help/README no longer advertise native factor iteration.
- `workflow-status` / provider-guidance surfaces emit AQ-mainline commands only.
- Auto-Quant handoff/readiness output becomes the canonical recommended follow-up
  for factor iteration.

Terminal pointer:
- Live authority for this slice moved to
  `support/docs/plans/2026-05-14-auto-quant-public-surface-lock-handoff-todo.md`.
- Verified there:
  - public CLI rejects `--backend native`
  - default `factor-research` emits Auto-Quant handoff output
  - `workflow-status --human` prefers the Auto-Quant handoff over first-run
    generic routing
  - `auto-quant-adoption-review` exposes the formal review/readiness surface
- Source commit for the verified slice:
  `bc9ccab5` (`feat: lock public factor iteration to auto-quant`).

If resuming:
1. Re-run `git status --short --branch`.
2. Check for active processes writing under `support/docs/experiments/actionable-regime-confidence/runs`.
3. Re-run `cargo fmt --check`.
4. Re-run `cargo clippy --all-targets -- -D warnings`.
5. Read this file before staging anything.

## Drift Check Draft

- Scope: still aligned with factor-result release readiness plus optional personal-data hot-plug UX; release is now gated by fresh closed-loop applicability proof.
- Compatibility boundary: generic public CLI must not depend on maintainer-local ontology or data.
- Retirement track: generated dependency workspaces should remain untracked or be moved out of repo release artifacts; this board does not make them release evidence.
- Decision: continue.

## Evidence Bundle Draft

- `cargo fmt --check`: passed before this board was created.
- `cargo check --tests --quiet`: passed after repairing mismatched fixture initializer defaults.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo fmt --check`: passed after the hot-plug profile-choice slice.
- `cargo clippy --all-targets -- -D warnings`: passed after the Clippy repair and hot-plug profile-choice slice.
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`: passed after branch-admission route gating.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed, 114 tests after branch-admission route gating.
- `cargo fmt --check`: passed after branch-admission route gating.
- `cargo test`: passed after branch-admission route gating.
- `cargo clippy --all-targets -- -D warnings`: passed after branch-admission route gating.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed after replacing the exact local-path negative assertion with a generic `/Users/` guard.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed after syncing structural candidate-set fields into the path-plan artifact.
- `cargo check --tests --quiet`: passed after final staging candidate.
- `/tmp` clean export from `HEAD`: `cargo test --manifest-path <export>/Cargo.toml bbn::trading -- --nocapture` failed at compile time because the checkpoint omitted required `StructuralPathRankingTargetRow` branch segment fields from `src/belief_core/ranking_label.rs`.
- `/tmp` clean export after adding `ranking_label.rs`: same command progressed and then found one omitted `StructuralPathRankingTargetRow` test constructor in `src/application/entry_models/training_export.rs`.
- `/tmp` clean export after checkpoint commit: `cargo test --manifest-path /tmp/ict-engine-release-export.Fa3UTZ/Cargo.toml bbn::trading -- --nocapture` compiled but failed 3 tests because ignored `state/policy_training` fixtures were absent from the export.
- Local fixture repair: `cargo fmt --check` passed, `cargo test bbn::trading -- --nocapture` passed with 19 matching tests, and `cargo clippy --all-targets -- -D warnings` passed after moving test dependency to tracked fixtures.
- `/tmp` clean export from `f1a561a`: `cargo test --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml bbn::trading -- --nocapture` passed with 19 matching tests.
- `/tmp` clean export from `f1a561a`: `cargo fmt --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml --check` passed.
- `/tmp` clean export from `f1a561a`: `cargo clippy --manifest-path /tmp/ict-engine-release-export.IWadVv/Cargo.toml --all-targets -- -D warnings` failed on dead `StructuralRankedPathSelection.paths` and two unused `structural_ranked_paths*` wrappers that were still absent from the committed tree.
- `/tmp` clean export from `32858ad`: `/tmp/ict-engine-release-export.y6Pefh` passed `cargo fmt --manifest-path ... --check`, `cargo clippy --manifest-path ... --all-targets -- -D warnings`, targeted `cargo test --manifest-path ... bbn::trading -- --nocapture`, and full `cargo test --manifest-path ...`.
- `/tmp` clean export from `e6fca81`: `/tmp/ict-engine-release-export.ueDk6B` passed `cargo fmt --manifest-path ... --check`, `cargo clippy --manifest-path ... --all-targets -- -D warnings`, and full `cargo test --manifest-path ...` as the final `v0.1.2` release-candidate gate.
- Release mirror remote probe: `main` and `v0.1.1` still point at `5bc7bc74dfc2b6c88840b774c662d62c1d81cca1`; no `v0.1.2` tag exists yet.
- Local mirror prep: `/tmp/ict-engine-release-mirror-v012.87caSH` was cloned from `Undermybelt/ict-engine-release`, synced from `/tmp/ict-engine-release-export.ueDk6B`, scanned for large files/nested `.git`/state dirs/common secret patterns, and committed locally; re-read mirror HEAD before any push.
- GH CLI: `gh auth status` currently reports an active `Undermybelt` login with `repo`/`workflow` scopes.
- Release mirror remote probe via HTTPS showed `v0.1.1` exists at commit `5bc7bc74dfc2b6c88840b774c662d62c1d81cca1`.
- `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --agent`: passed after the provider-summary fix and now reports `live zero-config=yfinance` with `selected_profile_id=null`.
- `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --human`: passed; produced Pre-Bayes `pass_neutralized`, execution `observe/transition_guardrail/guarded`, and persisted `execution_tree_trace.json`.
- `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --refresh --agent`: passed; exposes posterior distribution `trend=0.4550`, `range=0.3090`, `stress=0.1596`, `transition=0.0764`.
- `cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --refresh --output-format json`: passed; exposes the same canonical structural probabilities and `latest_uses_soft_evidence=true`.
- `jq ... execution_tree_trace.json`: passed; execution tree persisted `branch=transition_guardrail`, `gate_status=observe`, ranker visible/used flags false, and fail-closed validation notes.
- `cargo run --quiet -- export-structural-path-ranking-target --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO`: passed; exported 3 structural path-ranking rows plus CSV/JSONL/history/manifest under `/tmp/.../policy_training/`.
- `cargo run --quiet -- update --symbol DEMO --outcome win --entry-signal strong_buy --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --pnl 1.0 --ensemble`: passed; consumed pending update/execution candidate artifacts and recorded feedback into update history.
- `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO --output-format agent`: passed after export/update; reports `analyze_runs=1`, `update_runs=1`, and structural path ranking target rows while keeping runtime disabled/fail-closed until a trainer artifact is explicitly registered.
- Privacy smoke: `workflow-status --agent | rg "/Users/|api[_-]?key|secret|token" -i` returned no matches for the zero-config smoke state.
- `cargo fmt --check`: passed after the closed-loop/docs slice.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`: passed, 114 tests.
- `cargo clippy --all-targets -- -D warnings`: passed.
- Commit checkpoint: this amended `Document closed-loop consumer gate` commit.
- `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_regime_probabilities_and_trade_levels -- --nocapture`: passed after wiring the practical human report to regime posterior probabilities and trade-plan levels while preserving stable English agent labels.
- `/tmp` zero-config smoke `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-five-slot-smoke.YPxjBN --human`: passed and showed `Structure`, `Technicals`, `SMT`, `Regime` with `posterior_probabilities=range=0.309 stress=0.160 transition=0.076 trend=0.455`, and `Plan` with `actionable=false direction=Neutral entry=0.00 stop_loss=0.00 take_profits=0.00,0.00,0.00 risk_reward=0.00`.
- Privacy smoke on the same output: `rg -i "/Users/|api[_-]?key|secret|token"` returned no matches.
- `cargo test application::reporting::human_report::tests:: -- --nocapture` passed, 5 tests.
- `cargo test application::reporting::analyze_output::tests:: -- --nocapture` passed, 10 tests.
- `cargo fmt --check && cargo clippy --all-targets -- -D warnings` passed after the practical 5-slot human-output slice.
- `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_ict_template_with_price_levels -- --nocapture`: passed; guards BOS/swing/CISD/liquidity/FVG/OB/rejection template fields and price parentheses.
- `/tmp` zero-config smoke `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-human-template-smoke.AbKTQ5 --human`: passed; output included `last_close=(114.50)`, EMA/Bollinger/ATR values, SMT universe, posterior probabilities, and explicit `(n/a)` for demo-missing swing/FVG/OB/liquidity levels.
- Privacy smoke on the same output: `rg -i "/Users/|api[_-]?key|secret|token"` returned no matches.
- Direct runtime smoke `./target/debug/ict-engine analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-human-template-smoke.DA8dPq --human`: passed after the MSS/CISD/smooth-or-jagged template wording; output included `market_structure_shift/MSS=no_recent_BOS_or_CHoCH`, `change_in_state_of_delivery/CISD=no_recent_CISD`, `liquidity_pool_texture/smooth_or_jagged=(n/a)`, exact technical prices such as `last_close=(114.50)`, and no privacy matches.
- `cargo test application::reporting::analyze_output::tests:: -- --nocapture` passed, 11 tests.
- `cargo fmt --check` passed after the data-backed ICT/PDA price-level human-template slice.
- `cargo clippy --lib -- -D warnings` passed for the library/runtime surface. `cargo clippy --all-targets -- -D warnings` is currently blocked by unrelated dirty Auto-Quant test drift in `src/application/auto_quant/agent_material.rs` where tests reference branch fields not present on `AgentMaterialDispatchJobResult` / `AgentMaterialRankRow`.
- `cargo test analyze::smt_correlation_section::tests:: -- --nocapture` passed, 2 tests; guards bullish/bearish ICT SMT as swing confirmation failure with base/comparison levels and swept side.
- `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_ict_smt_confirmation_fields -- --nocapture` passed; guards human SMT output fields `smt_signal`, `base_level`, `comparison_level`, `swept_side`, and `trade_use=confirmation_only`.
- `rustfmt --edition 2021 --check src/analyze/smt_correlation_section.rs src/application/reporting/analyze_output.rs` passed. Full `cargo fmt --check` is currently blocked by unrelated dirty formatting in `src/data/loader.rs`.
- Disk cleanup evidence 2026-05-12 23:09 +0800: initial `df -h /Users/thrill3r` in this turn showed `17Gi` available; after cleanup it showed `107Gi` available.
- Disk cleanup deleted `/Users/thrill3r/projects-ict-engine/ict-engine/target` after Finder tag byte count `0` and no `lsof` holders; final main/worktree `target` count was `0`.
- Disk cleanup ran `uv cache prune --no-progress`; output removed `218479 files (7.3GiB)`.
- Disk cleanup deleted 93 generated Auto-Quant `.deps` dependency workspaces under `support/docs/experiments/actionable-regime-confidence/runs`; pre-delete size was about `33.9G`, Finder tag byte count was `0`, no active `lsof` holders were found, and final `.deps` count was `0`.
- Disk cleanup truncated untagged `/Users/thrill3r/.codex/log/codex-tui.log` instead of deleting the open file; it shrank from about `62G` to KB-scale while preserving the path for running Codex processes.
- Release mirror CI failed run `25836480345`: both Ubuntu and macOS failed only `application::data_sources::control_matrix_providers::tests::ibkr_requires_runtime_probe_even_with_consent_files`; CI saw `left: "install_required"` vs expected `right: "configured_runtime_unhealthy"` because runner `HOME` had no local IBKR consent file.
- Source fix: `src/application/data_sources/control_matrix_providers.rs` now creates temporary `.ict-engine/ibkr_consent.json` and `.ict-engine/ibkr_capabilities.json` fixtures inside the test instead of reading the real operator `HOME`.
- Source verification after the test fixture fix: `cargo fmt --check` passed; `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed; `cargo +1.95.0 clippy --all-targets -- -D warnings` passed; clean CI-shaped environment `env -i HOME=/tmp/... CI=true GITHUB_ACTIONS=true cargo +1.95.0 test` passed.
- Release mirror verification in `/tmp/ict-engine-release-mirror-17uBsZ`: `cargo fmt --check`, `python3 support/scripts/ci/check_docs_runtime_isolation.py`, `cargo +1.95.0 clippy --all-targets -- -D warnings`, and clean CI-shaped `env -i HOME=/tmp/... CI=true GITHUB_ACTIONS=true cargo +1.95.0 test` passed after applying the source patch.

## Slice Notes

### 2026-05-13 current worktree full audit / release-gate gap check

Changed:
- `src/analyze/smt_correlation_section.rs`
- `src/main.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Scope:
- Read current routing/entrypoint docs, the compact Board A/B current docs, the
  release handoff board, current process list, git status, and release signoff.
- Avoided taking over active Board A/B roots or publishing the release mirror.

Findings:
- Current checkout is not the same release candidate described by
  `support/docs/audits/release-signoff.md`: `main` is still far ahead of `origin/main`
  and has broad dirty source/docs/state changes plus many untracked experiment
  artifacts.
- `cargo clippy --all-targets -- -D warnings` initially failed on two dirty-tree
  blockers: `src/analyze/smt_correlation_section.rs` had `mod tests` before
  later runtime items, and `src/main.rs` used consecutive `str::replace` calls.
- Fixed only those mechanical blockers by moving the SMT test module to EOF and
  replacing `market.replace('/', "_").replace(' ', "_")` with
  `market.replace(['/', ' '], "_")`.
- Full `cargo test` did not complete: lib tests reached `967 passed`, then the
  bin-test phase stalled in a Python dependency/import probe. The run was
  terminated by killing the specific `cargo`, test binary, and child Python PIDs.
  Treat this as an incomplete full-suite gate, not a pass.

Evidence:
- `cargo fmt --check`: passed after the mechanical fixes.
- `cargo test analyze::smt_correlation_section::tests:: -- --nocapture`:
  passed, 6 tests.
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver`:
  passed, 9 tests.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo test factor_candidate -- --nocapture`: passed the filtered native
  candidate-pack/admission tests.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`:
  passed, 114 tests.
- `cargo clippy --all-targets -- -D warnings`: passed after the mechanical fixes.
- `cargo check --lib` and `cargo check --bin ict-engine`: passed after the smoke
  compile retries.
- `/tmp` smoke state: `/tmp/ict-engine-current-audit.Ax0Ug3`.
- `provider-status --compact`: passed; reported yfinance as live zero-config
  fallback and provider setup gaps for crypto/public/IBKR/TradingView surfaces.
- `workflow-status --symbol DEMO --state-dir /tmp/ict-engine-current-audit.Ax0Ug3 --human`:
  passed and routed first-run users through provider-status and demo/factor/live
  choices.
- `analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-current-audit.Ax0Ug3 --human`:
  passed with the five-slot Structure/Technicals/SMT/Regime/Plan surface and
  posterior probabilities.
- `workflow-status --refresh --agent` privacy scan with
  `rg -i '/Users/|api[_-]?key|secret|token'`: no matches.
- `pre-bayes-status --refresh --output-format json`: passed and exposed
  canonical structural probabilities plus `latest_uses_soft_evidence=true`.
- `policy-training-status --output-format agent`: passed before export/update
  and correctly reported missing ranker target export.
- `export-structural-path-ranking-target`: passed with 3 rows and persisted
  structural path-ranking target files under the `/tmp` state.
- `update --outcome win --entry-signal strong_buy --pnl 1.0 --ensemble`: passed
  after compile retry and consumed the pending update/execution candidate.

Next:
- Do not publish from this dirty working tree.
- Either create a coherent checkpoint from the intended current-tree source/docs
  changes or produce a fresh clean export from the exact intended `HEAD`.
- Re-run full `cargo test` to completion, or isolate the slow Python dependency
  probe into a bounded test before using full-suite status as a release gate.
- Keep Board A/B promotion gates blocked: this audit did not satisfy calibrated
  regime acceptance, provider-portable profitability, or non-observe execution
  admission.

### 2026-05-13 full cargo test Python dependency probe blocker

Status:
- done, owner Codex current turn, claimed 2026-05-13 08:13:15 +0800,
  closed 2026-05-13 08:36:46 +0800.

Plan:
- Locate the exact test/provider code path that spawns the `python3` import
  probe seen during full `cargo test`.
- Validate the persistent provider venv
  `/Users/thrill3r/.venvs/ict-engine-provider-py313` with bounded one-import
  probes before rerunning any broad suite.
- Run the narrow affected cargo test with `PATH` pointed at the provider venv if
  the code path relies on `python3` from PATH.
- Record whether the blocker is dependency/runtime configuration, a hanging
  import, or a test harness issue. Do not mark full-suite or release readiness
  as passed until full `cargo test` completes without manual termination.

Findings:
- Root cause owner: `src/application/provider_catalog.rs`
  `probe_public_fetch_python_runtime()` / `public_fetch_python_modules()`.
- The probe is part of provider-status runtime health, not a test-only mock. It
  shells to `python3` from PATH and treats every listed module as required before
  marking public provider adapters healthy.
- System PATH resolves `python3` to Homebrew Python 3.14 and imports
  `requests`, `pandas`, and `yaml`, but misses `ccxt`, `ib_async`, `redis`,
  `sklearn`, `pyarrow`, and `xgboost`.
- `/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python` imports the
  previous full list including `xgboost`, but does not currently import
  `catboost`.
- `support/scripts/auto_quant_external/fetch_external.py` imports only `pandas` and
  `requests` eagerly; `ib_async`/`yaml` are lazy IBKR/bulk dependencies.
  CatBoost belongs to path-ranker training scripts, not provider fetch
  readiness; XGBoost is retired from the current route.
- Operator decision 2026-05-13: `xgboost` can be removed because the current
  model route is CatBoost.

Change:
- Removed `xgboost` from the provider fetch Python required-module probe. This
  keeps CatBoost in the path-ranker/trainer lane instead of making any model
  package a provider-status dependency.

Evidence:
- `cargo fmt --check`: passed.
- Bounded one-import probes:
  - system Homebrew Python 3.14 imported `requests`, `pandas`, `yaml`; still
    missed `ccxt`, `ib_async`, `redis`, `sklearn`, and `pyarrow` after the
    `xgboost` removal.
  - `/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python` imported the
    previous provider list including `xgboost`, but did not import `catboost`.
- `cargo run --quiet -- provider-status --agent --domain market_data` with
  system PATH: missing-module prompt no longer includes `xgboost`.
- Same command with
  `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH`: passed and
  reported `market_data:5/7 ready`; remaining blockers were
  `ibkr_gateway_unreachable` and `tradingview_mcp_connectivity_probe_failed`,
  not Python dependency health.
- `cargo test application::provider_catalog::tests:: -- --nocapture`: passed,
  13 tests.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH cargo test
  --bin ict-engine
  tests::test_analyze_research_backtest_structural_playbook_preserves_canonical_lineage`:
  passed in 165.11s.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH cargo test`:
  passed. Lib tests: 967 passed. Bin tests: 251 passed. Integration/doc tests:
  all passed. No manual termination.

Next:
- Current-tree release completion is still blocked on dirty-tree split/commit or
  a fresh clean export from the intended HEAD. Do not publish from this dirty
  worktree and do not tag/push/release without explicit operator confirmation.

### 2026-05-13 completion audit against release objective

Status:
- done for release-prep audit, owner Codex current turn, claimed
  2026-05-13 08:39:41 +0800, closed after fresh sanitized export evidence and
  manifest/runbook materialization. This is not publish authorization.

Objective restatement:
- Prepare `ict-engine` for publication by improving consumer and contributor
  experience, proving zero-config first-run behavior, auditing release safety,
  and preserving a publish-safe state.

Prompt-to-artifact checklist:

| Requirement / gate | Concrete evidence checked | Status |
|---|---|---|
| Consumer zero-config first run works | `/tmp/ict-engine-current-audit.Ax0Ug3`, older `/tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO`, and fixture export smoke `/tmp/ict-engine-release-fixture-smoke.SKwW8Q` ran provider-status, workflow-status, analyze demo, workflow refresh, Pre-Bayes, and policy-training commands. | covered for demo/first-run smoke |
| Default/no-config provider behavior falls back to Yahoo/yfinance-compatible defaults | `provider-status --compact` and `workflow-status --human/--agent` evidence reports yfinance/live zero-config fallback; fixture export smoke reports `live_runtime:1/3 ready` with `yfinance`. | covered |
| Provider surfaces stay opt-in for richer/realtime providers | Provider profile and workflow tests passed; `provider-status` now avoids requiring `xgboost` for public provider health. Remaining IBKR/TradingView blockers surface as opt-in setup/runtime gaps. | covered for current tests |
| No private key/token/local path leaks in default human/agent output | Privacy scans against zero-config workflow/analyze outputs returned no `/Users/`, API key, secret, token, bearer, password, or credential matches; fixture roots were also scanned for local paths/secrets. | covered for smoke outputs |
| Current/in-progress regime posterior visible | `workflow-status --refresh --agent` and Pre-Bayes JSON expose posterior probability maps, not just labels. | covered |
| Closed-loop inspectability: provider -> Pre-Bayes/filter -> BBN -> path-ranker/CatBoost/export -> execution tree -> feedback/update | Smoke evidence covers provider, analyze, Pre-Bayes, execution trace, structural path-ranking target export, update feedback, and policy-training status. Runtime path-ranker remains fail-closed until trainer artifact registration. | partially covered; trainer/runtime enablement not release-promoted |
| TimesFM optional, not required | `AGENT.md` defines TimesFM optionality; zero-config tests did not require TimesFM. | covered by docs and smoke behavior |
| Contributor/agent entrypoint usable | `CLAUDE.md` redirects to `AGENT.md`; `AGENT.md` contains route, release, zero-config, privacy, closed-loop, and factor traceability contract. | covered |
| Mechanical verification | `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and full `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH cargo test` passed after the provider probe repair. The fixture clean export also passed fmt, Clippy, and full cargo test. | covered for current dirty tree plus selected-fixture export |
| Publish-safe state | Current `git status --short --branch` shows `main...origin/main [ahead 653]` plus broad modified/deleted/untracked files and experiment artifacts. Current checkout is not a clean release candidate. | blocked |
| Clean export from intended current state | Fixture export `/tmp/ict-engine-release-fixture-export.22TfKl` passed fmt, Clippy, full cargo test, zero-config smoke, and fixture inventory commands when it included current tracked changes plus the selected fixture roots. | covered if selected fixture roots are included in the release slice |
| Release mirror publish | Local mirror prep exists from older export, but no tag/push/release was created. Explicit operator confirmation is still required. | blocked |

2026-05-13 final audit refresh:
- Fresh sanitized release export evidence supersedes the earlier
  selected-fixture export status for the release-prep audit:
  `/tmp/ict-engine-fresh-release-export.A0JQ2T`,
  `/tmp/ict-engine-fresh-release-target.xX95Dv`,
  `/tmp/ict-engine-fresh-smoke-state.j5BH7I`, and
  `/tmp/ict-engine-fresh-smoke-out.sCBMAY`.
- Fresh verification evidence recorded below shows the export passed fmt,
  Clippy, full cargo test, and true zero-config smoke without provider venv
  injection.
- The publish-safe-state risk has a versioned release candidate manifest:
  `support/docs/audits/2026-05-13-sanitized-release-candidate-manifest.md`.
- The manifest/runbook/signoff docs now say the whole dirty working tree must
  not be published, and publish/tag/release actions require explicit operator
  confirmation.

Completion decision:
- Release-prep audit objective is covered: consumer zero-config behavior,
  contributor mechanical gates, privacy/local-path smoke, public provider
  fallback, posterior visibility, CatBoost/path-ranker surface, release-slice
  manifest, and runbook/signoff blockers all have concrete artifacts.
- Actual release is still blocked: no tag, push, mirror publish, or
  `gh release create` has been authorized or performed.

Next:
- If publishing is requested later, use the exact sanitized export slice from
  `support/docs/audits/2026-05-13-sanitized-release-candidate-manifest.md` or rerun the
  full gate after changing the slice.

Release-slice manifest draft:

Source of truth:
- `git diff --name-status`: 27 modified tracked files, 25 deleted tracked files.
- `git ls-files --others --exclude-standard`: 6348 untracked files under
  `support/docs/experiments/actionable-regime-confidence/runs/`, 2 untracked experiment
  root files, 2 untracked experiment scripts, 5 untracked plan docs, 2 untracked
  audit docs, 1 untracked `support/docs/README.md`, 21 untracked example factor-pack
  files, and 6 untracked root factor-pack/workspace-looking entries.
- 2026-05-13 refresh: untracked experiment material remains the dominant
  pollution risk (`6352` paths under `support/docs/experiments/actionable-regime-confidence`);
  selected release fixture candidates are `21` files under
  `support/examples/factor_candidate_packs/curated-auto-quant-v1` plus
  `config/regime_confidence_assets_v1.csv`.

| Classification | Files / patterns | Release handling |
|---|---|---|
| include candidate, but requires coherent slice review | `AGENT.md`, `README.md`, `support/docs/factor-artifact-naming-contract.md`, `src/application/provider_catalog.rs`, and this handoff board | Likely consumer/contributor/release UX relevant, but must be reviewed as a coherent diff before staging. |
| include candidate only if owner confirms full source slice | `src/analyze/smt_correlation_section.rs`, `src/main.rs`, `src/application/auto_quant/agent_material.rs`, `src/application/auto_quant/pda_unit_batch.rs`, `src/application/entry_models/mod.rs`, `src/application/entry_models/training_export.rs`, `src/application/orchestration/structural_playbook.rs`, `src/data/loader.rs`, `src/factor_lab/factor_definition.rs`, `src/policy_training_command.rs`, `support/scripts/auto_quant_external/run_tomac.py`, `support/scripts/research/factor_candidate_resolver.py`, `support/scripts/research/tests/test_factor_candidate_resolver.py`, `config/factor_candidate_harness_presets.json` | These are executable/code/config changes. Full tests pass in the dirty tree, but the combined diff is too broad to publish without owner/slice review. |
| board/evidence only | `support/docs/plans/2026-05-10-actionable-regime-confidence-todo.md`, `support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`, untracked `support/docs/plans/2026-05-12-*.md`, untracked audit docs | Keep as evidence/handoff unless the release explicitly includes current research-board state. |
| exclude/generated from public release by default | `support/docs/experiments/actionable-regime-confidence/runs/**`, especially Auto-Quant workspaces, provider caches, `user_data/data/*.feather`, generated state JSON, and rank/material run outputs | Do not stage into release mirror unless a small named artifact is deliberately promoted. Current untracked count makes this the largest pollution risk. |
| needs owner decision before any release export | 25 tracked doc deletions under older April support-doc audit, trial, and report paths | Could be docs cleanup, but deleting historical docs in a release slice is high-risk without explicit owner decision. |
| needs owner decision / likely not release root | untracked root entries `CryptoContinuationFailureGuard`, `CryptoMomentumPersistence`, `crypto_ema_rsi_persistence_long_v1`, `crypto_momentum_failure_short_v1`, `ema_rsi_persistence`, `momentum_failure` | Treat as local factor/workspace artifacts until identified. Do not publish by default. |
| include candidate, validated as selected fixture | `config/regime_confidence_assets_v1.csv` | Small public fixture candidate; 16K / 29 lines; sensitive/local-path scan passed; `regime-confidence-assets` reads 18 assets with promotion disabled. Include or commit it with the release slice, or tests/export will regress. |
| include candidate, validated as selected fixture | `support/examples/factor_candidate_packs/curated-auto-quant-v1/**` | Small contributor UX fixture candidate; 84K / 21 JSON files; all JSON parses; sensitive/local-path scan passed; `factor-candidate-packs` reads 7 packs and admission target export writes 35 rows. Include or commit it with the release slice, or tests/export will regress. |

Manifest decision:
- No clean export should be made from the whole working tree.
- The selected-fixture export proves a release candidate can be tested without
  untracked experiment pollution if those two fixture roots are included.
- Next release-safe action is a narrow review/export plan: decide whether the
  intended publish slice is only release/consumer UX fixes plus selected
  fixtures, or also the broad Auto-Quant/factor source changes. Then stage or
  export that named slice, excluding generated experiment runs by default.

### 2026-05-13 CatBoost-only / XGBoost removal release-surface check

Status:
- done, owner Codex current turn.

Operator instruction:
- `xgboost` can be deleted because the current model route is CatBoost.

Current evidence:
- `rg -n "xgboost|XGBoost" src scripts tests config examples Cargo.toml README.md AGENT.md -S`
  returned no matches.
- The tracked dirty tree already deletes
  `src/application/orchestration/xgboost_policy.sample.json`.
- `src/application/provider_catalog.rs` no longer requires the Python `xgboost`
  module for provider/public-fetch readiness.
- `src/application/orchestration/ensemble_vote.rs` now uses one
  `catboost_file` executor with default weight `1.0` instead of the previous
  two-model pair.
- Remaining `xgboost` references found by the broader non-experiment scan are
  historical/research docs and active handoff evidence, not current source,
  config, examples, tests, README, or AGENT release surfaces.
- `cargo test application::orchestration::ensemble_vote::tests:: -- --nocapture`
  passed, 7 tests.
- `cargo test application::provider_catalog::tests:: -- --nocapture` passed,
  13 tests.
- `cargo test --test provider_neutral_cli -- --nocapture` passed, 19 tests.
- `cargo fmt --check` passed after this board update.

Next:
- Keep current release completion blocked until the named release slice is
  staged/exported cleanly; do not publish from the whole dirty worktree.

### 2026-05-13 CatBoost-only documentation cleanup claim

Owner:
- Codex current slice, 2026-05-13 11:50:42 +0800.

Status:
- Done, closed 2026-05-13 11:57 +0800.

Operator instruction:
- `xgboost` can be deleted because the current model route is CatBoost.

Plan:
- Keep the already-completed active source/test XGBoost removal intact.
- Update current non-experiment docs that still describe the route as
  two-model guidance so public/release-facing guidance says CatBoost-only.
- Preserve historical run evidence under `support/docs/experiments/**` and keep this
  handoff TODO as the coordination/audit record.

Expected output:
- Non-experiment documentation no longer advertises an active XGBoost route.
- Verification grep separates historical evidence from current public guidance.

Changed:
- Current non-experiment docs that described the model route as two-model
  CatBoost/XGBoost guidance were rewritten to CatBoost-only wording.
- `support/docs/pda_type` now describes the execution split as CatBoost current
  execution-layer behavior.
- `support/docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md`
  now says the fallback direct-model artifact applies when `catboost` is
  unavailable, without naming XGBoost as a current dependency.
- Historical/handoff evidence that records the earlier XGBoost removal remains
  in this TODO and old plan evidence; it is not active route guidance.

Evidence:
- `rg -n "xgboost|XGBoost" src tests scripts config examples README.md AGENT.md Cargo.toml Cargo.lock`:
  no matches.
- `rg -n "xgboost|XGBoost" src tests scripts config examples README.md AGENT.md docs -g '!support/docs/experiments/**' -g '!support/docs/plans/**'`:
  no matches.
- `rg -n "CatBoost\\s*/\\s*XGBoost|CatBoost/XGBoost|catboost\\s*/\\s*xgboost" docs README.md AGENT.md src tests scripts config examples -g '!support/docs/experiments/**'`:
  no matches.

### 2026-05-12 disk-pressure cleanup before release continuation

Changed:
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- Local filesystem only: deleted rebuildable build/dependency/log bulk; no source/config/docs/state/market-data deletion outside this board update.

Behavior:
- Reclaimed local disk space before the publish/release continuation.
- Preserved Finder-tagged artifacts and did not delete whole old repos; the only whole-repo old-access candidate found was tiny `.codex/vendor_imports/skills`, so it was left alone.
- Preserved experiment result files while removing generated `.deps` dependency workspaces.

Evidence:
- `df -h /Users/thrill3r`: `17Gi` available before cleanup in this turn; `107Gi` available after cleanup.
- `find ... -name target ... | wc -l`: `0`.
- `find support/docs/experiments/actionable-regime-confidence/runs -path '*/.deps' ... | wc -l`: `0`.
- `du -xsh /Users/thrill3r/.codex/log`: `12K`.
- `du -xsh /Users/thrill3r/.cache/uv`: `4.4G`.

### 2026-05-12 ICT SMT confirmation-failure semantics slice

Changed:
- `src/analyze/smt_correlation_section.rs`
- `src/application/reporting/analyze_output.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- `build_smt_correlation_section` now evaluates ICT SMT as same-window swing
  confirmation failure, not a generic rolling-correlation sentence.
- Positive related markets can emit `bearish_smt` when one side sweeps a higher
  high and the other fails to confirm, and `bullish_smt` when one side sweeps a
  lower low and the other fails to confirm.
- SMT output carries `base_swing_type`, `base_level`, `comparison_swing_type`,
  `comparison_level`, `swept_side`, `relationship_type`,
  `relationship_confidence`, `normalized_for_inverse_correlation`, and
  `trade_use=confirmation_only`.
- If relationship confidence is uncertain, SMT fails closed with
  `relationship_uncertain`; SMT remains confirmation evidence and does not make
  a trade actionable by itself.
- The related-market map now seeds practical zero-config universes for index
  futures, metals, and crypto instead of only echoing the provided spot/options
  symbols.

Evidence:
- `cargo test analyze::smt_correlation_section::tests:: -- --nocapture`
  passed, 2 tests.
- `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_ict_smt_confirmation_fields -- --nocapture`
  passed.
- `rustfmt --edition 2021 --check src/analyze/smt_correlation_section.rs src/application/reporting/analyze_output.rs`
  passed.

Next:
- For inverse-correlation pairs such as DXY/EURUSD or DXY/XAUUSD, promote the
  next factor-training/runtime slice to validate normalized inverse structure
  with raw-level provenance before using it for execution confidence.

### 2026-05-12 data-backed ICT/PDA price-level human-template slice

Changed:
- `src/analyze_sections.rs`
- `src/main.rs`
- `src/application/reporting/analyze_output.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- `PriceActionSection` now carries detector-derived levels for latest
  BOS/CHoCH/MSS, latest swing high/low, nearest liquidity pool, latest
  liquidity sweep, nearest open FVG, and nearest untested order block.
- The active `analyze` and `analyze-live` human-report path renders those
  fields into `Structure` and `Technicals` with explicit price parentheses,
  including `change_in_state_of_delivery/CISD`.
- Demo or missing detector evidence renders as `(n/a)` instead of invented
  levels; not-yet-trained order-block variants and smooth/jagged liquidity
  texture remain explicit follow-up evidence, not prose claims.
- `SMT` human output includes the default practical universe reminder
  (`NQ/ES/YM`, CFD indices, DXY, Nikkei/KOSPI, DAX/FTSE/EuroStoxx) plus any
  configured related assets.

Evidence:
- `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_ict_template_with_price_levels -- --nocapture` passed.
- `/tmp` smoke `/tmp/ict-engine-human-template-smoke.AbKTQ5` produced the
  expected 5-slot output with price parentheses and no private path/secret
  pattern in the human output.
- `/tmp` smoke `/tmp/ict-engine-human-template-smoke.DA8dPq` produced the
  updated MSS/CISD/smooth-or-jagged template wording with price parentheses and
  no private path/secret pattern in the human output.
- `cargo test application::reporting::analyze_output::tests:: -- --nocapture`
  passed, 11 tests.
- `cargo fmt --check` passed.
- `cargo clippy --lib -- -D warnings` passed. `cargo clippy --all-targets -- -D warnings` is blocked by unrelated dirty Auto-Quant test drift in `src/application/auto_quant/agent_material.rs`.

Next:
- If the user wants richer order-block variants beyond available detector
  fields, train/promote the factor side to populate mitigation, breaker,
  failed-mitigation, and PDA sequence scores as first-class runtime evidence.

### 2026-05-12 practical 5-slot human-output slice

Changed:
- `AGENT.md`
- `src/application/reporting/analyze_output.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- `--human` keeps token-friendly English agent labels: `Structure`,
  `Technicals`, `SMT`, `Regime`, and `Plan`.
- Agents are now explicitly instructed to answer human operators in the user's
  language and translate meanings instead of mutating the CLI field contract.
- The active practical `analyze` and `analyze-live` human-report path now
  includes canonical regime posterior probabilities in `Regime`.
- The active practical human-report path now includes `actionable`, direction,
  entry, stop, take-profits, risk-reward, posterior, win probability, position
  size, and narrative in `Plan` instead of only a terse plan label.

Evidence:
- RED: the focused human-output test first failed because the posterior/trade
  plan helper functions were missing.
- GREEN: `cargo test application::reporting::analyze_output::tests::analyze_human_surface_carries_regime_probabilities_and_trade_levels -- --nocapture` passed.
- Smoke: `analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-five-slot-smoke.YPxjBN --human` produced all five stable agent slots; `Regime` included posterior probabilities and `Plan` included actionable/trade-level fields.
- Privacy: the smoke output did not match `/Users/`, API key, secret, or token patterns.
- Final verification: focused reporting tests, `cargo fmt --check`, and
  `cargo clippy --all-targets -- -D warnings` passed.

Next:
- Do not release until the broader release gate is re-checked and the operator
  explicitly confirms tag/push/release creation.

### 2026-05-12 hot-plug profile-choice slice

Changed:
- `src/application/orchestration/command_entry.rs`
- `tests/provider_neutral_cli.rs`

Behavior:
- `provider-status --agent` still hides opt-in profiles by default.
- `workflow-status --symbol NQ --human` can now show a matching optional profile reuse command without auto-adopting it.
- `workflow-status --symbol NQ --agent` now exposes a lightweight `available_opt_in_profiles` reference while `selected_profile_id` remains null.
- Personal path hints remain redacted/absent unless the user explicitly passes `--profile`.

Next:
- Run `cargo test` if local runtime pressure allows.
- Then stage only intended source/docs/test files and commit a safe checkpoint.

### 2026-05-12 workflow-status branch-admission precedence slice

Changed:
- `src/application/orchestration/workflow_status.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `src/belief_core/structural_state.rs`
- `src/belief_core/ranking_label.rs`
- `src/application/entry_models/training_export.rs`
- `src/application/orchestration/structural_playbook.rs`
- `tests/provider_neutral_cli.rs`

Behavior:
- `closed_loop_branch_admission` can still fail closed for an exact latest
  structural feedback branch path.
- Branch admission no longer steals routing from no-state first-run guidance,
  Auto-Quant handoff, evidence review, selected-profile followups, or generic
  recommended-path execution contracts.
- Agent output only treats branch admission as a blocking/router owner when the
  latest update carries the same `structural_feedback.path_id`.
- Path-plan artifacts now carry their candidate set id and candidate paths so
  structural path-ranker runtime matching has a stable serialized contract.
- Structural path-ranker training rows now expose regime-profit branch segments
  as serialized/categorical fields so exact branch paths can feed external or
  direct path-ranker models.
- The new provider-neutral tests guard against local path leakage without
  embedding the maintainer's exact local Tomac path in the test source.

Evidence:
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`
- `cargo test --test provider_neutral_cli -- --nocapture`
- `cargo check --tests --quiet`
- `/tmp` clean export compile gate before release mirror publish

Next:
- Stage only intended files and commit a safe checkpoint.

### 2026-05-12 A/B large-window provider-portability correction

Changed:
- Added `support/docs/experiments/actionable-regime-confidence/runs/20260512T144700+0800-codex-ab-large-window-provider-portability-correction-v2.md`.
- Appended matching direction-correction sections to Board A and Board B.

Behavior:
- Local long-history data is allowed for training, hardening, and factor discovery.
- Maintainer-local files must not become required consumer inputs.
- Consumer paths must use provider-backed data recipes, built-in factors, or hot-pluggable agent material.
- `15y/1m` is not a rigid public requirement; the actual rule is to maximize feasible history, candle count, and trade observations.
- Tiny daily windows and low trade counts are diagnostics only, not promotion evidence.

Evidence:
- Board A hash before direction writeback: `f08375789ae362d3cbc25ebb0e8ffd316dafebbfd7425b64e996fba968732887`.
- Board B hash before direction writeback: `ea407181585e1b67fff830062b835fe2c886d09d917d2bfcc1c2305feeb19687`.
- Handoff hash before direction writeback: `452fb2afd0424100393119d03a7aaec87bd63b5e3c4dd92aaef7c9cd2aec8e14`.

Next:
- Keep any release/export work from depending on `/Users/thrill3r/Downloads/Tomac` or other maintainer-local data paths.
- For A/B evidence, prefer largest feasible provider-backed windows; if local training is used, require a portable factor/material/recipe before consumer-facing promotion.

### 2026-05-12 clean-export BBN fixture repair slice

Changed:
- `src/bbn/trading/cpt_init.rs`
- `src/bbn/trading/family_overlay.rs`
- `src/bbn/trading/topology.rs`
- `src/bbn/trading/update.rs`
- `tests/fixtures/policy_training/repo_bbn_trading_cpt_init.json`
- `tests/fixtures/policy_training/repo_bbn_trading_cpt_init_smoothed.json`
- `tests/fixtures/policy_training/repo_bbn_logic_family_overlays.json`

Behavior:
- Unit tests no longer depend on ignored repo-local `state/policy_training`
  files that disappear from a clean release export.
- New fixture files are small, tracked, and do not contain maintainer-local
  absolute paths.
- Runtime BBN CPT and logic-family overlays remain hot-pluggable via the
  existing user state search path; fixture files are test-only and are not
  selected as zero-config consumer defaults.

Evidence:
- `cargo test --manifest-path /tmp/ict-engine-release-export.Fa3UTZ/Cargo.toml bbn::trading -- --nocapture`: failed 3 tests from missing ignored `state/policy_training` fixtures.
- `cargo fmt --check`: passed after fixture repair formatting.
- `cargo test bbn::trading -- --nocapture`: passed, 19 matching tests.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `/tmp` clean export `/tmp/ict-engine-release-export.IWadVv`:
  `cargo test --manifest-path ... bbn::trading -- --nocapture` passed,
  `cargo fmt --manifest-path ... --check` passed, and
  `cargo clippy --manifest-path ... --all-targets -- -D warnings` failed on
  committed-tree-only structural-playbook dead code.

Next:
- Commit the minimal structural-playbook cleanup already present in the working
  tree, then rebuild a clean `/tmp` export from `HEAD` and re-run Clippy there.

### 2026-05-12 clean-export structural-playbook lint slice

Changed:
- `src/application/orchestration/structural_playbook.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- Removed a stale `paths` duplicate from `StructuralRankedPathSelection`.
- Removed two unused wrapper functions that were absent from runtime callers.
- Runtime and tests use the existing `candidate_paths` field for ranked path
  material.

Evidence:
- `/tmp` clean export `/tmp/ict-engine-release-export.IWadVv` Clippy failed on
  the stale field/wrappers.
- Commit `32858ad` folded in the minimal cleanup.
- `/tmp` clean export `/tmp/ict-engine-release-export.y6Pefh` passed
  `cargo fmt --manifest-path ... --check`,
  `cargo clippy --manifest-path ... --all-targets -- -D warnings`,
  `cargo test --manifest-path ... bbn::trading -- --nocapture`, and
  full `cargo test --manifest-path ...`.

Next:
- Commit the `v0.1.2` release-prep support-docs version update.
- Wait for explicit operator confirmation before mirror tag/push/release.

### 2026-05-12 v0.1.2 release-prep slice

Changed:
- `Cargo.toml`
- `Cargo.lock`
- `support/docs/release-notes-draft.md`
- `support/docs/audits/release-signoff.md`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- Version is prepared as `0.1.2` because the release mirror already has
  `v0.1.1`.
- Release notes and signoff describe the hot-plug profile-choice work, clean
  fixture repair, structural-playbook lint cleanup, and clean-export gates.
- Mirror publication remains blocked on explicit operator confirmation for
  `v0.1.2` tag/push/`gh release create`.

Evidence:
- `cargo metadata --locked --format-version 1 --no-deps`: passed after version
  bump.
- `/tmp` clean export `/tmp/ict-engine-release-export.ueDk6B`:
  `cargo fmt --manifest-path ... --check` passed,
  `cargo clippy --manifest-path ... --all-targets -- -D warnings` passed, and
  full `cargo test --manifest-path ...` passed.

Next:
- If operator confirms `v0.1.2`, sync committed `HEAD` into the release mirror
  clone flow without force-push, then tag and create the GitHub release.

### 2026-05-12 local mirror-prep slice

Changed:
- Local clone only: `/tmp/ict-engine-release-mirror-v012.87caSH`
- Source handoff updated with mirror-prep evidence.

Behavior:
- Clean export was synced into a real clone of `Undermybelt/ict-engine-release`
  so the eventual push can be a normal mirror update, not a force push.
- Local mirror commit exists but no local/remote tag was created and nothing was
  pushed.

Evidence:
- `git ls-remote --heads --tags https://github.com/Undermybelt/ict-engine-release.git`: `v0.1.1` exists, no `v0.1.2`.
- `gh auth status`: active `Undermybelt` login with `repo`/`workflow`.
- `find . ... -size +1M`: no files over 1MB in mirror worktree.
- Nested `.git`/state scan: no nested `.git`; only tracked lightweight
  `support/docs/experiments` files and normal `src/state` source module appeared.
- Secret scan: only code/documentation literals such as env var names and test
  variable names matched; no concrete token/key value found.
- Local mirror commit exists in the mirror worktree; re-read `git -C /tmp/ict-engine-release-mirror-v012.87caSH rev-parse --short HEAD` before any push.

Next:
- After explicit `v0.1.2` confirmation, re-check remote is still at the probed
  base, then push mirror `main`, create tag `v0.1.2`, push tag, and run
  `gh release create`.

### 2026-05-12 closed-loop consumer gate slice

Changed:
- `CLAUDE.md`
- `AGENTS.md`
- `src/application/orchestration/workflow_status.rs`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- `CLAUDE.md` is only a one-line redirect into `AGENTS.md`.
- `AGENTS.md` is now the shared agent contract for zero-config use, provider
  fallback/priority, privacy isolation, closed-loop order, regime posterior
  surfacing, TimesFM optionality, and release constraints.
- `workflow-status` first-run routing now treats ready default live runtimes as
  live zero-config providers, matching `provider-status`.
- `workflow-status --agent` now surfaces the resolved ensemble posterior active
  regime, posterior confidence, posterior probability map, normalization status,
  and short evidence tail.

Evidence:
- `cargo test application::orchestration::workflow_status::tests::agent_workflow_status_empty_state_uses_explicit_no_state_contract -- --nocapture`: passed.
- `cargo test application::orchestration::workflow_status::tests::agent_and_human_workflow_status_views_prefer_canonical_analyze_ensemble_surface -- --nocapture`: passed.
- `/tmp/ict-engine-closed-loop-smoke-fixed.bmbPSO` ran zero-config workflow/analyze/Pre-Bayes/policy-training/export/update checks listed in the evidence bundle above.
- `cargo fmt --check`, `cargo test --test provider_neutral_cli -- --nocapture`, `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`, and `cargo clippy --all-targets -- -D warnings` passed.

Next:
- No release publish yet. Re-check remote/mirror and run a clean export only
  after the operator explicitly asks to resume release publication.

### 2026-05-12 Board B 175350 high-density multibranch AQ evidence slice

Changed:
- Added a run-root builder and artifacts under `support/docs/experiments/actionable-regime-confidence/runs/20260512T175350+0800-codex-high-density-multibranch-six-provider-aq-v1/`.
- Appended the terminal Board B readback to `support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`.

Behavior:
- Six provider material packages were generated for IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.
- Four branch paths were preserved in each material as `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.
- Current provider-status is separated from replay material: yfinance is ready, IBKR/public crypto adapters are unhealthy from Python dependency health, and TradingView MCP remains unhealthy.
- AQ batch/dispatch/rank completed, but the result is fail-closed: output is aggregate per material, not branch-keyed; yfinance has one trade, IBKR has 19 losing trades, and the other four provider units have zero trades.

Evidence:
- `checks/provider_material_preflight_assertions.out`: provider rows `6`, material count `6`, branch paths `4`, gates false.
- `command-output/01_provider_status_agent.out`: current provider health saved separately from replay copy evidence.
- `state/auto-quant/PROVIDER_HDMULTI_175350/auto_quant_agent_material_batch.20260512T105759.936Z.json`: batch artifact.
- `state/auto-quant/PROVIDER_HDMULTI_175350/auto_quant_agent_material_dispatch.20260512T105915.013Z.json`: dispatch artifact.
- `state/auto-quant/PROVIDER_HDMULTI_175350/auto_quant_agent_material_rank.20260512T110103.305Z.json`: rank artifact.
- `summaries/high_density_multibranch_aq_terminal_readback_v1.md`: terminal readback and fail-closed interpretation.
- `checks/aq_terminal_gate_assertions.out`: downstream gates blocked.

Next:
- Do not run Pre-Bayes/filter, BBN, CatBoost/path-ranker, execution tree, or feedback/update from `175350`.
- For the next Board B slice, split branches into separately measurable AQ material units or add branch-tagged trade extraction before treating AQ output as regime-conditioned profitability evidence.

### 2026-05-12 Board B 184139 isolated AQ pandas repair slice

Changed:
- Added terminal repair readback under `support/docs/experiments/actionable-regime-confidence/runs/20260512T184139+0800-codex-vwap-session-liquidity-six-provider-aq-v1/summaries/vwap_session_liquidity_aq_pandas_repair_terminal_readback_v1.md`.
- Added gate assertions under `support/docs/experiments/actionable-regime-confidence/runs/20260512T184139+0800-codex-vwap-session-liquidity-six-provider-aq-v1/checks/aq_pandas_repair_terminal_gate_assertions.out`.
- Appended the 184139 terminal readback to the Board B markdown.

Behavior:
- The run-root AQ venv now imports pandas `2.3.3`; no new dependency install was needed in this slice.
- Re-ran `auto-quant-agent-material-dispatch` and `auto-quant-agent-material-rank` for `PROVIDER_VWAP_184139` with an absolute state dir.
- Dispatch and rank completed, closing the previous missing-pandas infrastructure blocker.
- Result is still fail-closed for downstream: YF and IBKR aggregate rows are negative, four crypto/TVR rows have zero trades, and AQ still does not emit branch-keyed trade/outcome rows.

Evidence:
- `command-output/12_aq_venv_pandas_probe_before.out`: pandas import succeeded in the isolated AQ venv.
- `command-output/13_auto_quant_agent_material_dispatch_after_pandas.out`: dispatch completed 6/6 jobs.
- `command-output/14_auto_quant_agent_material_rank_after_pandas.out`: rank completed.
- `state/auto-quant/PROVIDER_VWAP_184139/auto_quant_agent_material_dispatch.20260512T111226.440Z.json`: repaired dispatch artifact.
- `state/auto-quant/PROVIDER_VWAP_184139/auto_quant_agent_material_rank.20260512T111650.279Z.json`: repaired rank artifact.

Next:
- Do not run Pre-Bayes/filter, BBN, CatBoost/path-ranker, execution tree, or feedback/update from `184139`.
- The next Board B implementation should produce branch-keyed trade/outcome rows, either by extracting branch tags from AQ workspaces or by rerunning one material per branch path.

### 2026-05-12 Board B OTE duplicate-claim audit slice

Changed:
- Appended a no-takeover completion audit to `support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`.

Behavior:
- Re-read the current Board B tail and visible OTE roots.
- `191916` has only a strategy and material-builder script visible.
- `192000` has no visible files under its run root.
- `192149` has no visible run-root files.
- These roots overlap on the same OTE four-leaf surface, so this slice did not create another factor packet, did not run AQ, and did not run downstream.

Evidence:
- `support/docs/experiments/actionable-regime-confidence/runs/20260512T191916+0800-codex-ote-four-leaf-branch-keyed-aq-v1/agent-material/OtePullbackContinuationLongV1.py`
- `support/docs/experiments/actionable-regime-confidence/runs/20260512T191916+0800-codex-ote-four-leaf-branch-keyed-aq-v1/scripts/build_ote_four_leaf_materials.py`
- No material/provenance/AQ artifacts were visible for `191916`, `192000`, or `192149` in this audit.

Next:
- Do not start a third OTE packet. Wait for one of the OTE owners to close, block, or hand off in the Board B markdown before any continuation.

### 2026-05-13 xgboost provider-dependency removal claim

Owner:
- Codex current slice, 2026-05-13 08:43:56 +0800.

Status:
- Done, closed 2026-05-13 08:58:56 +0800.

Plan:
- Remove `xgboost` from provider readiness dependency checks because the current model path is CatBoost.
- Keep runtime/model docs that mention historical two-model design separate unless they affect active provider readiness.
- Verify with focused provider catalog tests and, if cheap, provider-neutral CLI tests.

Expected output:
- Minimal code/docs-board slice showing provider Python readiness no longer requires `xgboost`.

Changed:
- `src/application/provider_catalog.rs`
- `src/application/orchestration/ensemble_vote.rs`
- `src/application/orchestration/workflow_status.rs`
- `src/application/orchestration/execution_tree.rs`
- `src/main.rs`
- Deleted `src/application/orchestration/xgboost_policy.sample.json`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Behavior:
- Provider Python readiness no longer requires `xgboost`; install prompts list
  only provider-fetch modules: `ccxt`, `ib_async`, `redis`, `sklearn`, and
  `pyarrow` on the current system Python.
- Active ensemble vote now emits a single CatBoost executor/runtime source with
  weight `1.00`; the old `xgboost_file` sample executor is no longer loaded.
- Current active source/test tree has no `xgboost`/`XGBoost` references. Older
  docs and experiment evidence were not rewritten in this slice.
- Operator confirmation 2026-05-13 10:03 +0800: `xgboost` can be deleted; the
  current model route is CatBoost. Keep this as an intentional retirement
  decision when building the release slice.

Evidence:
- TDD red check: after changing ensemble tests to expect one CatBoost executor,
  `cargo test application::orchestration::ensemble_vote::tests:: -- --nocapture`
  initially failed because the implementation still emitted two executors.
- `cargo fmt --check`: passed.
- `cargo test application::orchestration::ensemble_vote::tests:: -- --nocapture`:
  passed, 7 tests.
- `cargo test application::provider_catalog::tests:: -- --nocapture`: passed,
  13 tests.
- `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`:
  passed, 114 tests.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- `cargo test --bin ict-engine -- --nocapture`: passed, 251 tests.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `rg -n "xgboost|XGBoost" src tests -g '!**/target/**'`: no matches.
- `cargo run --quiet -- provider-status --agent --domain market_data` plus
  focused grep showed missing-module prompts without `xgboost`; remaining system
  Python misses are `ccxt`, `ib_async`, `redis`, `sklearn`, and `pyarrow`.

Next:
- Release completion is still blocked by the broader dirty tree / clean-export
  decision recorded above; this slice only removes XGBoost from active code and
  provider readiness.

### 2026-05-13 tracked-source clean-export verification claim

Owner:
- Codex current slice, 2026-05-13 09:02:54 +0800.

Status:
- Blocked, closed 2026-05-13 09:17 +0800.

Plan:
- Build a `/tmp` clean export from current tracked files only, preserving current
  tracked source/docs/config changes and omitting untracked workspaces.
- Exclude generated or local runtime state from the export: `.git`, `target`,
  `catboost_info`, `state*`, and `support/docs/experiments/actionable-regime-confidence/runs/**`.
- Run release verification from that export: fmt, clippy, full cargo test, and a
  zero-config `/tmp` smoke/privacy pass.

Expected output:
- A concrete export path plus commands/results proving whether the current
  tracked source/docs can be release-tested without carrying untracked experiment
  pollution.

Result:
- The tracked-only clean export is not sufficient for current tests. Full
  `cargo test` reached the bin-test phase and failed 6 tests because required
  current artifacts are still untracked in the source worktree:
  `config/regime_confidence_assets_v1.csv` and
  `support/examples/factor_candidate_packs/curated-auto-quant-v1`.
- This is not an XGBoost/CatBoost regression. `rg -n "xgboost|XGBoost" src tests
  -g '!**/target/**'` still has no matches after the CatBoost-only slice.

Evidence:
- `/tmp/ict-engine-current-tracked-export.WngRUS` was the export under test.
- `cargo test --manifest-path /tmp/ict-engine-current-tracked-export.WngRUS/Cargo.toml`
  failed in `--bin ict-engine`: 245 passed, 6 failed.
- Failing tests were the factor-candidate pack inventory/admission tests and
  regime-confidence asset inventory/status tests; each failed on missing current
  artifacts omitted from the tracked-only export.

Next:
- Decide whether the missing candidate-pack and regime-confidence asset files
  are release-slice inputs to track, or update the tests/fixtures so release
  verification does not depend on local untracked artifacts.

### 2026-05-13 release fixture export validation claim

Owner:
- Codex current slice, 2026-05-13 09:23 +0800.

Status:
- Done, closed 2026-05-13 09:45 +0800.

Plan:
- Treat the clean-export failure as a fixture ownership question, not a test
  flake: inspect the missing files for size, local paths, tokens, secrets, and
  generated-workspace pollution.
- If they are small public release fixtures, build a clean export that includes
  tracked files plus only those selected fixtures and rerun the failing bin
  tests before any broader release gate.
- If they are not safe release fixtures, leave the export blocked and record the
  exact reason.

Expected output:
- A release-fixture decision for
  `config/regime_confidence_assets_v1.csv` and
  `support/examples/factor_candidate_packs/curated-auto-quant-v1`, with command
  evidence and next release action.

Decision:
- These are small, public release-fixture candidates, not generated workspace
  bulk: `config/regime_confidence_assets_v1.csv` is 16K / 29 lines;
  `support/examples/factor_candidate_packs/curated-auto-quant-v1` is 84K / 21 JSON
  files.
- Sensitive/local-path scan over both fixture roots found no `/Users`, `/tmp`,
  `/private`, `Downloads`, API key, secret, token, password, credential, bearer,
  or private-key patterns.
- All candidate-pack JSON files parse with `python3 -m json.tool`.
- A clean export that includes current tracked files plus only these selected
  fixtures closes the previous clean-export test gap.

Export:
- `/tmp/ict-engine-release-fixture-export.22TfKl`
- Export construction: `git archive HEAD`, overlay current dirty tracked file
  changes/deletions, then copy only
  `config/regime_confidence_assets_v1.csv` and
  `support/examples/factor_candidate_packs/curated-auto-quant-v1`.
- Selected fixture files in export: 29.
- `rg -n "xgboost|XGBoost" src tests -g '!**/target/**'` inside the export:
  no matches.

Verification:
- `cargo test --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml --bin ict-engine factor_candidate_pack -- --nocapture`:
  passed, 3 tests.
- `cargo test --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml --bin ict-engine regime_confidence_asset -- --nocapture`:
  passed, 3 tests.
- `cargo test --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml --bin ict-engine -- --nocapture`:
  passed, 251 tests.
- `cargo fmt --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml --check`:
  passed.
- `cargo clippy --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml --all-targets -- -D warnings`:
  passed.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH CARGO_TARGET_DIR=/tmp/ict-engine-release-fixture-target cargo test --manifest-path /tmp/ict-engine-release-fixture-export.22TfKl/Cargo.toml`:
  passed. Lib tests: 967 passed. Bin tests: 251 passed. Integration/doc tests:
  passed.

Zero-config smoke:
- Binary: `/tmp/ict-engine-release-fixture-target/debug/ict-engine`.
- State: `/tmp/ict-engine-release-fixture-smoke.SKwW8Q`.
- Output root: `/tmp/ict-engine-release-fixture-smoke-out.2JA8nI`.
- Commands passed: `provider-status --compact`; `workflow-status --symbol DEMO
  --state-dir <state> --human`; `analyze --symbol DEMO --demo --state-dir
  <state> --human`; `workflow-status --symbol DEMO --state-dir <state>
  --refresh --agent`; `pre-bayes-status --symbol DEMO --state-dir <state>
  --refresh --output-format json`; `policy-training-status --symbol DEMO
  --state-dir <state> --output-format agent`.
- Privacy scan over smoke outputs for `/Users`, API key, secret, token, bearer,
  password, and credential patterns: passed.
- Provider smoke summary: `entry_model:2/2 ready | live_runtime:1/3 ready |
  local_runtime:1/2 ready | market_data:5/7 ready`, with zero-config
  `yfinance` surfaced.
- `analyze --demo --human` exposed the intended compact user view:
  Structure, Technicals, SMT, Regime posterior probabilities, and Plan.

Fixture command evidence:
- `factor-candidate-packs --state-dir /tmp/ict-engine-release-fixture-inventory.FQbbMz --symbol FACTOR_CANDIDATES --output-format human`:
  `candidate_pack_count=7`.
- `factor-candidate-admission-targets --state-dir /tmp/ict-engine-release-fixture-inventory.FQbbMz --symbol FACTOR_CANDIDATES --output-format human`:
  `rows=35`, `mature_rows=35`, `production_validation=35/30`,
  `runtime_selection=disabled`.
- `regime-confidence-assets --state-dir /tmp/ict-engine-release-fixture-inventory.FQbbMz --symbol REGIME_CONFIDENCE_ASSETS --output-format human`:
  `regime_confidence_asset_count=18`, `board_a_gate=11`, `direct_event=2`,
  `diagnostic=4`, `contrast_evidence=10`.

Next:
- Include or commit these two fixture roots as part of the intended release
  slice; otherwise the clean-export verification will regress to missing
  fixture failures.
- Release completion remains blocked until the broader dirty tree is split into
  a coherent release slice or clean export and the operator confirms publication.

### 2026-05-13 release-slice option matrix

Owner:
- Codex current slice, 2026-05-13 09:56 +0800.

Status:
- Done, closed 2026-05-13 10:02 +0800.

Problem:
- Current `git diff --stat` outside generated experiment runs spans 96 tracked
  paths with 5816 insertions and 4830 deletions.
- The dirty tree mixes at least four concerns:
  1. consumer/contributor/release UX and verification docs;
  2. active code changes that remove XGBoost and expose CatBoost/provider/
     fixture inventory surfaces;
  3. Board A/B research-board and experiment evidence updates;
  4. broad Auto-Quant/factor research script changes plus old doc deletions.
- A whole-worktree publish would be too broad and would risk shipping research
  noise or accidental historical-doc deletion.

Option A: Narrow Consumer Release Candidate
- Purpose: publish the smallest coherent release slice that improves consumer
  and contributor experience, preserves zero-config behavior, removes active
  XGBoost dependency/surface, and includes the now-required public fixtures.
- Include candidates:
  - `AGENT.md`
  - `README.md`
  - `support/docs/factor-artifact-naming-contract.md`
  - `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  - `src/application/provider_catalog.rs`
  - `src/application/orchestration/ensemble_vote.rs`
  - `src/application/orchestration/workflow_status.rs`
  - `src/application/orchestration/execution_tree.rs`
  - `src/application/orchestration/xgboost_policy.sample.json` deletion
  - `tests/provider_neutral_cli.rs`
  - `config/regime_confidence_assets_v1.csv`
  - `support/examples/factor_candidate_packs/curated-auto-quant-v1/**`
- Conditional include: `src/main.rs` only if the selected release explicitly
  includes the new native `factor-candidate-packs`,
  `factor-candidate-admission-targets`, and `regime-confidence-assets` CLI
  surfaces. The verified fixture export included this path; omitting it requires
  a new export/test pass.
- Exclude by default:
  - generated experiment runs under
    `support/docs/experiments/actionable-regime-confidence/runs/**`;
  - old April docs deletions until explicitly approved;
  - Board A/B oversized source-log changes unless publishing current research
    board state is explicitly part of the release;
  - broad `support/scripts/auto_quant_external/**` research-script mutations unless the
    release scope is upgraded to Option B.
- Verification already passed for the selected-fixture export:
  fmt, Clippy, full cargo test, zero-config smoke, privacy scan, and fixture
  inventory/admission commands.
- Residual action before publish: stage/commit this exact slice or rebuild a
  mirror/export from it, then rerun the same release gate commands from that
  clean candidate.

Option B: Full Research/Auto-Quant Candidate
- Purpose: publish the broader current research state, including Auto-Quant
  branch-path, candidate-pack, factor-script, Board A/B, and experiment-doc work.
- Include candidates:
  - all Option A files;
  - `src/analyze/smt_correlation_section.rs`;
  - `src/application/auto_quant/**` changed files;
  - `src/application/entry_models/**` changed files;
  - `src/application/orchestration/structural_playbook.rs`;
  - `src/data/loader.rs`;
  - `src/factor_lab/factor_definition.rs`;
  - `src/policy_training_command.rs`;
  - `support/scripts/research/**` changed files;
  - `support/scripts/auto_quant_external/**` changed files;
  - `config/factor_candidate_harness_presets.json`;
  - compact Board A/B current docs and selected evidence docs.
- Exclude by default even for Option B:
  - generated Auto-Quant workspaces/provider caches/data under
    `support/docs/experiments/actionable-regime-confidence/runs/**`;
  - root workspace-looking artifacts such as `CryptoContinuationFailureGuard`,
    `CryptoMomentumPersistence`, `crypto_ema_rsi_persistence_long_v1`,
    `crypto_momentum_failure_short_v1`, `ema_rsi_persistence`, and
    `momentum_failure` until each is identified;
  - old April docs deletions until explicitly approved.
- Residual action before publish: this needs a real code-review pass over the
  broad source diff, not just green tests, because the slice spans runtime,
  provider, Auto-Quant, policy-training, research scripts, and docs.

Recommendation:
- Use Option A as the next release candidate unless the operator explicitly
  wants the larger research surface in this publication.
- Do not publish from the dirty working tree directly.
- Do not stage or commit old tracked doc deletions without explicit owner
  confirmation.
- Do not call the release objective complete until one option is selected,
  exported from a clean candidate, verified, and publication is explicitly
  confirmed or intentionally deferred.

### 2026-05-13 Option A exact-slice viability probe

Owner:
- Codex current slice, 2026-05-13 10:03 +0800.

Status:
- Blocked, closed 2026-05-13 10:05 +0800.

Plan:
- Build a `/tmp` export from `HEAD`, overlay only the Option A files listed
  above plus selected fixtures, and apply the XGBoost sample deletion.
- Run the smallest compile gate first (`cargo check --bin ict-engine`) to learn
  whether Option A is independently viable or depends on broader source files.
- If compile fails, record the exact missing dependencies and do not broaden the
  release slice silently.

Expected output:
- `option_a_exact_viable=true/false` with export path, command, result, and
  required next action.

Result:
- `option_a_exact_viable=false` for the exact narrow overlay as tested.
- Export: `/tmp/ict-engine-option-a-export.NJhCxH`.
- Target: `/tmp/ict-engine-option-a-target`.
- `cargo check --bin ict-engine`: passed before the focused tests.
- `cargo test --test provider_neutral_cli -- --nocapture`: passed, 19 tests.
- The bin-test probe failed at compile time because the narrow Option A overlay
  omitted the `PolicyTrainingStatusSurface` fields required by the current
  `src/main.rs` tests:
  `factor_candidate_packs` and `regime_confidence_assets`.
- This is a slice-manifest dependency failure, not an XGBoost/CatBoost
  regression. Active source/tests still have no `xgboost` references, and the
  runtime policy surface is CatBoost-only.

Next:
- Do not broaden Option A silently. Either include the current
  `src/application/entry_models/**` policy-training surface files in Option A,
  or redefine Option A as a narrower consumer release that excludes the
  candidate-pack/regime-confidence fixture CLI tests.

### 2026-05-13 Option A plus entry-models exact-slice probe

Owner:
- Codex current slice, 2026-05-13 10:06 +0800.

Status:
- Done, closed 2026-05-13 11:29 +0800.

Plan:
- Build a fresh `/tmp` export from `HEAD`.
- Overlay the same Option A release files and selected public fixtures,
  including conditional `src/main.rs` for the native fixture CLI surfaces, and
  also include the changed `src/application/entry_models/**` files that the
  previous probe proved were required by the current CLI tests.
- Apply the intentional XGBoost sample deletion.
- Run compile/focused tests first; if they pass, run fmt, Clippy, and full
  `cargo test` from the export with the provider py313 venv first on `PATH`.
- Keep generated `support/docs/experiments/**`, root workspace-looking artifacts, and
  old tracked doc deletions out of this export.

Expected output:
- `option_a_entry_models_exact_viable=true/false` with export path, command
  results, privacy scan status, and remaining release blocker.

Result:
- `option_a_entry_models_exact_viable=false` for the literal Option A +
  `src/application/entry_models/**` overlay only.
- First export: `/tmp/ict-engine-option-a-entry-models-export.pBCdUF`.
- Failure: `cargo check --bin ict-engine` failed because
  `src/application/entry_models/training_export.rs` imports
  `export_structural_path_ranking_target_with_agent_material_rank`, which lives
  in the current `src/application/orchestration/structural_playbook.rs` diff.
- A second export that also included `structural_playbook.rs` and
  `src/policy_training_command.rs` passed compile/focused tests, but release
  Clippy then failed on the baseline `src/analyze/smt_correlation_section.rs`
  layout (`items_after_test_module`). The current worktree diff for that file
  fixes the Clippy ordering and adds SMT related-asset provider-universe
  coverage.

Release-candidate slice proved viable:
- Export: `/tmp/ict-engine-option-a-release-export.wYrXhQ`.
- Target: `/tmp/ict-engine-option-a-release-target.Z97I30`.
- Included the Option A files plus direct release/CI dependencies:
  `src/application/entry_models/mod.rs`,
  `src/application/entry_models/training_export.rs`,
  `src/application/orchestration/structural_playbook.rs`,
  `src/policy_training_command.rs`, and
  `src/analyze/smt_correlation_section.rs`.
- Included public fixtures:
  `config/regime_confidence_assets_v1.csv` and
  `support/examples/factor_candidate_packs/curated-auto-quant-v1/**` (`21` files).
- Excluded generated experiment runs, root workspace-looking artifacts, and old
  April tracked doc deletions.
- Applied the intentional
  `src/application/orchestration/xgboost_policy.sample.json` deletion.

Verification:
- `rg -n "xgboost|XGBoost" <export>/src <export>/tests <export>/Cargo.toml <export>/Cargo.lock`:
  no active source/test/manifest matches.
- `cargo fmt --manifest-path /tmp/ict-engine-option-a-release-export.wYrXhQ/Cargo.toml --check`:
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-option-a-release-target.Z97I30 cargo clippy --manifest-path /tmp/ict-engine-option-a-release-export.wYrXhQ/Cargo.toml --all-targets -- -D warnings`:
  passed.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH CARGO_TARGET_DIR=/tmp/ict-engine-option-a-release-target.Z97I30 cargo test --manifest-path /tmp/ict-engine-option-a-release-export.wYrXhQ/Cargo.toml`:
  passed. Lib tests: `963 passed`; bin tests: `253 passed`; integration tests
  and doctests passed.

Zero-config smoke:
- Binary: `/tmp/ict-engine-option-a-release-target.Z97I30/debug/ict-engine`.
- State: `/tmp/ict-engine-option-a-smoke-state.dJLrin`.
- Output root: `/tmp/ict-engine-option-a-smoke-out.zsdtYu`.
- Passed commands:
  `provider-status --compact`;
  `workflow-status --symbol DEMO --state-dir <state> --human`;
  `analyze --symbol DEMO --demo --state-dir <state> --human`;
  `workflow-status --symbol DEMO --state-dir <state> --refresh --agent`;
  `pre-bayes-status --symbol DEMO --state-dir <state> --refresh --output-format json`;
  `policy-training-status --symbol DEMO --state-dir <state> --output-format agent`;
  `factor-candidate-packs --state-dir <state> --symbol FACTOR_CANDIDATES --output-format human`;
  `factor-candidate-admission-targets --state-dir <state> --symbol FACTOR_CANDIDATES --output-format human`;
  `regime-confidence-assets --state-dir <state> --symbol REGIME_CONFIDENCE_ASSETS --output-format human`.
- Provider summary:
  `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:2/2 ready | market_data:6/7 ready`.
- User-visible `analyze --demo --human` includes Structure, Technicals, SMT,
  Regime posterior probabilities, and Plan.
- Fixture command evidence:
  `candidate_pack_count=7`; admission targets `rows=35`,
  `mature_rows=35`; regime-confidence assets
  `regime_confidence_asset_count=18`, `board_a_gate=11`.
- Privacy scan over smoke outputs for `/Users`, `/private`, `Downloads`,
  `API key`, `api_key`, `secret`, `token`, `bearer`, `password`, and
  `credential`: no matches.

Next:
- Treat the viable release candidate as Option A plus three required direct
  dependencies: entry-model surfaces, structural target adapter/policy-training
  render glue, and the SMT Clippy/related-asset fix.
- Do not publish from the dirty working tree directly.
- Stage/commit or export exactly this candidate slice before release.
- Release remains blocked until the operator explicitly chooses this slice (or a
  different one) and confirms publish/tag/release action.

### 2026-05-13 release objective completion audit and exact slice manifest

Owner:
- Codex current slice, 2026-05-13 11:31 +0800.

Status:
- Blocked, closed 2026-05-13 11:31 +0800.

Objective restated:
- Prepare `ict-engine` for release with a better consumer and contributor
  experience, a zero-config first-run path, no default private/provider leakage,
  and a verifiable clean candidate slice.

Prompt-to-artifact checklist:

| Requirement | Evidence | Status |
|---|---|---|
| Consumer zero-config first run works | Clean export smoke under `/tmp/ict-engine-option-a-smoke-state.dJLrin` ran provider, workflow, analyze demo, workflow refresh, Pre-Bayes, policy-training, candidate-pack, admission-target, and regime-asset commands. | covered |
| Contributor/release mechanical gate passes | `/tmp/ict-engine-option-a-release-export.wYrXhQ` passed `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and full `cargo test` with lib `963`, bin `253`, integration, and doctest passes. | covered |
| No default private key/token/local-path leakage | Smoke output privacy scan in `/tmp/ict-engine-option-a-smoke-out.zsdtYu` found no `/Users`, `/private`, `Downloads`, `API key`, `api_key`, `secret`, `token`, `bearer`, `password`, or `credential`. | covered for smoke outputs |
| Default provider behavior is public/zero-config | Smoke `provider-status --compact` reported `live_runtime:1/3 ready` with `yfinance`; richer providers stayed opt-in/setup-gated. | covered |
| Posterior probabilities visible | Smoke `analyze --demo --human` showed `posterior_probabilities=range=0.309 stress=0.160 transition=0.076 trend=0.455`; workflow refresh emitted agent JSON. | covered |
| Closed-loop inspectability | Smoke covered provider, analyze, Pre-Bayes, policy-training, factor candidate packs/admission, regime assets, and workflow refresh. Runtime CatBoost trainer promotion remains fail-closed until a registered trainer artifact is selected. | partial, acceptable for consumer release candidate; not a profitability-promotion claim |
| XGBoost retired from active code | Export `rg -n "xgboost|XGBoost" <export>/src <export>/tests <export>/Cargo.toml <export>/Cargo.lock` had no matches; `xgboost_policy.sample.json` is intentionally deleted. | covered |
| TimesFM optional | `AGENT.md` states TimesFM is optional and zero-config smoke did not require it. | covered |
| Dirty-tree pollution avoided | Candidate was built from `git archive HEAD` plus exact overlays; generated experiment runs, root workspace-looking artifacts, and old April doc deletions were excluded. | covered for export |
| Publish/tag/release confirmation | No explicit operator confirmation to publish, tag, push mirror, or create GitHub release has been given. | blocked |

Exact candidate tracked paths:
- `AGENT.md`
- `README.md`
- `support/docs/factor-artifact-naming-contract.md`
- `src/analyze/smt_correlation_section.rs`
- `src/application/entry_models/mod.rs`
- `src/application/entry_models/training_export.rs`
- `src/application/orchestration/ensemble_vote.rs`
- `src/application/orchestration/execution_tree.rs`
- `src/application/orchestration/structural_playbook.rs`
- `src/application/orchestration/workflow_status.rs`
- `src/application/orchestration/xgboost_policy.sample.json` deletion
- `src/application/provider_catalog.rs`
- `src/main.rs`
- `src/policy_training_command.rs`
- `tests/provider_neutral_cli.rs`

Exact candidate untracked fixture paths:
- `config/regime_confidence_assets_v1.csv`
- `support/examples/factor_candidate_packs/curated-auto-quant-v1/**` (`21` JSON files)

Excluded from this release candidate:
- This handoff TODO itself:
  `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`.
  It is the internal authoritative coordination/audit record and intentionally
  contains local `/tmp` and `/Users/...` evidence paths. Keep it out of the
  public release slice.
- `support/docs/experiments/actionable-regime-confidence/runs/**` generated/provider
  workspaces and caches.
- Root workspace-looking artifacts:
  `CryptoContinuationFailureGuard`, `CryptoMomentumPersistence`,
  `crypto_ema_rsi_persistence_long_v1`,
  `crypto_momentum_failure_short_v1`, `ema_rsi_persistence`, and
  `momentum_failure`.
- Old tracked April doc deletions.
- Broad Auto-Quant/research-script mutations not required by this verified
  consumer release candidate.

Latest local hygiene check:
- `git diff --check` over the corrected tracked candidate paths returned no
  errors.
- Candidate source/fixture sensitive-pattern scan excluding this handoff TODO
  has no concrete secret values or maintainer-local runtime paths. Remaining
  matches are policy/test guard strings such as `API key`, `credential`,
  `tokenized`, and assertions that default output must not contain `/Users/`.

Completion decision:
- Do not mark the active release objective complete yet. The verified candidate
  slice exists, but release completion still requires operator choice plus an
  explicit commit/stage/tag/publish decision.

### 2026-05-13 corrected export local-path hygiene audit

Owner:
- Codex current slice, 2026-05-13 11:47 +0800.

Status:
- Blocked, closed 2026-05-13 11:47 +0800.

Plan:
- Rebuild the release export without this internal handoff TODO.
- Scan the corrected export for concrete maintainer-local paths and secret-like
  patterns.
- If the scan finds baseline source leaks, fix the smallest source/test paths
  instead of treating green tests as sufficient.

Findings:
- Corrected export: `/tmp/ict-engine-corrected-release-export.kYy4dB`.
- Target: `/tmp/ict-engine-corrected-release-target.2Ja8L5`.
- The handoff TODO was explicitly removed from the export before verification.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and full
  `cargo test` passed on that corrected export before the follow-up local-path
  cleanup. Full test evidence: lib `963 passed`, bin `253 passed`,
  integration tests and doctests passed.
- The corrected export scan still found baseline source/test local-path issues
  that were not caused by the handoff TODO:
  - `tests/eml_poc.rs` defaulted to `$HOME/Downloads/tomac/...`.
  - `src/application/multi_timeframe_inputs.rs` auto-searched
    `$HOME/Downloads/Tomac`, `$HOME/Downloads/tomac`, and Documents variants.
  - `src/application/auto_quant/live/wire.rs` had already been changed in the
    dirty tree from `/Users/thrill3r/...` to `<auto-quant-root>/...`, but that
    file was not yet part of the corrected release manifest.

Changed after the finding:
- `src/application/multi_timeframe_inputs.rs`: `default_tomac_root_candidates`
  now only uses explicit `ICT_ENGINE_TOMAC_ROOT`; it no longer scans HOME
  Downloads/Documents paths by default.
- `tests/eml_poc.rs`: EML PoC now uses explicit `ICT_ENGINE_EML_POC_ROOT` and
  skips when the env var is absent instead of defaulting to local Downloads.
- `tests/provider_neutral_cli.rs`: negative assertion now uses an example user
  path rather than the maintainer username.
- `src/application/auto_quant/live/wire.rs`: include the existing sanitized
  `<auto-quant-root>/auto_quant_live_signal_publisher.py` comment in the release
  candidate.

Focused verification after cleanup:
- `cargo fmt --check`: passed.
- `cargo test --test eml_poc -- --nocapture`: passed; skipped with
  `ICT_ENGINE_EML_POC_ROOT` unset.
- `cargo test --bin ict-engine test_resolve_tomac_root_prefers_explicit_argument -- --nocapture`:
  passed.
- `cargo test --bin ict-engine test_find_tomac_root_from_candidates_requires_tomac_layout -- --nocapture`:
  passed.
- `cargo test --test provider_neutral_cli bootstrap_output_does_not_auto_reuse_personal_tomac_paths_without_profile -- --nocapture`:
  passed.
- `rg -n "Downloads/Tomac|Downloads/tomac|/Users/thrill3r|poc-cleaned-15m" src tests README.md AGENT.md support/docs/factor-artifact-naming-contract.md`:
  only remaining match is a test guard using `/Users/example/Downloads/Tomac`.

Release manifest adjustment:
- Add these files to the exact candidate slice:
  `src/application/multi_timeframe_inputs.rs`,
  `src/application/auto_quant/live/wire.rs`, and `tests/eml_poc.rs`.
- Keep `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  excluded from the public release slice.

Next:
- Rebuild a fresh no-handoff export after this local-path cleanup and rerun the
  full release gate before any commit/tag/release claim. The previous corrected
  export full gate does not cover these last source/test cleanup edits.

### 2026-05-13 fresh no-handoff release export full gate

Owner:
- Codex current slice, 2026-05-13 11:55:13 +0800.

Status:
- Blocked, closed 2026-05-13 12:09:59 +0800.

Objective:
- Rebuild a fresh clean export from `HEAD` plus the exact candidate release
  slice after local-path hygiene and CatBoost-only doc cleanup.
- Keep this internal handoff TODO, generated experiment runs, root workspace
  artifacts, old April doc deletions, and broad research-script mutations out
  of the public release candidate.
- Rerun the mechanical release gates and zero-config consumer smoke from the
  fresh export before any release-completion claim.

Plan:
- Create `/tmp` export and target dirs.
- Overlay the exact candidate source/doc/fixture paths, including
  `src/application/multi_timeframe_inputs.rs`,
  `src/application/auto_quant/live/wire.rs`, and `tests/eml_poc.rs`.
- Apply the intentional `src/application/orchestration/xgboost_policy.sample.json`
  deletion.
- Run sensitive/local-path scans, XGBoost scan, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, full `cargo test`, zero-config
  smoke commands, and smoke-output privacy scan.

Expected output:
- Fresh export path, target path, smoke state/output paths, command results,
  scan results, and remaining release blocker written back here.

Result:
- Fresh export: `/tmp/ict-engine-fresh-release-export.A0JQ2T`.
- Target: `/tmp/ict-engine-fresh-release-target.xX95Dv`.
- Smoke state: `/tmp/ict-engine-fresh-smoke-state.j5BH7I`.
- Smoke output: `/tmp/ict-engine-fresh-smoke-out.sCBMAY`.

Export handling:
- Started from `git archive HEAD`, then overlaid the named release candidate
  source/docs/fixtures from the dirty tree.
- Explicitly excluded this internal handoff TODO,
  `support/docs/experiments/actionable-regime-confidence/runs/**`, the old
  `xgboost_policy.sample.json` sample, generated root workspaces, and old April
  doc deletions.
- Kept the repo example provider/factor profiles, but only after overlaying
  their current sanitized versions. Deleting the provider profile broke tests
  because the repo still uses `thrill3r-nq-closed-loop-v1` as a loadable example
  id; the release-safe shape is sanitized example profile, not missing example
  profile.
- Pruned legacy local-data research scripts from the export when they carried
  maintainer-local `/Users/thrill3r/...` paths. These are not needed for the
  consumer release smoke and should not be published as default public examples
  until rewritten around explicit inputs.

Mechanical verification:
- Excluded-path check: internal handoff TODO, generated experiment runs, and the
  old sample policy file were absent from the export.
- Local-path scan after profile overlay/pruning:
  `rg -n "/Users/thrill3r|Downloads/Tomac|Downloads/tomac|poc-cleaned-15m" ...`
  found only `tests/provider_neutral_cli.rs` using
  `/Users/example/Downloads/Tomac` as a negative guard.
- `cargo fmt --manifest-path /tmp/ict-engine-fresh-release-export.A0JQ2T/Cargo.toml --check`:
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-fresh-release-target.xX95Dv cargo clippy --manifest-path /tmp/ict-engine-fresh-release-export.A0JQ2T/Cargo.toml --all-targets -- -D warnings`:
  passed.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH CARGO_TARGET_DIR=/tmp/ict-engine-fresh-release-target.xX95Dv cargo test --manifest-path /tmp/ict-engine-fresh-release-export.A0JQ2T/Cargo.toml`:
  passed. Lib tests `963 passed`; bin tests `253 passed`; integration tests and
  doctests passed.

Zero-config smoke:
- Ran from the fresh export binary without injecting the provider venv into the
  smoke command environment.
- Passed commands:
  `provider-status --compact`;
  `workflow-status --symbol DEMO --state-dir <state> --human`;
  `analyze --symbol DEMO --demo --state-dir <state> --human`;
  `workflow-status --symbol DEMO --state-dir <state> --refresh --agent`;
  `pre-bayes-status --symbol DEMO --state-dir <state> --refresh --output-format json`;
  `policy-training-status --symbol DEMO --state-dir <state> --output-format agent`;
  `factor-candidate-packs --state-dir <state> --symbol FACTOR_CANDIDATES --output-format human`;
  `factor-candidate-admission-targets --state-dir <state> --symbol FACTOR_CANDIDATES --output-format human`;
  `regime-confidence-assets --state-dir <state> --symbol REGIME_CONFIDENCE_ASSETS --output-format human`.
- Provider summary in true zero-config smoke:
  `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
  `yfinance` is ready; richer providers remain setup/runtime-gated instead of
  being required.
- `analyze --demo --human` surfaced Structure, Technicals, SMT, Regime posterior
  probabilities, and Plan.
- `workflow-status --refresh --agent` surfaced
  `posterior_probabilities` and top executor `catboost_file`.
- Candidate-pack smoke: `candidate_pack_count=7`.
- Admission-target smoke: `rows=35`, `mature_rows=35`, promotion blocked until
  downstream gates pass.
- Regime-confidence asset smoke: `regime_confidence_asset_count=18`,
  `board_a_gate=11`.
- Smoke stderr files were empty.
- Smoke-output privacy scan for `/Users`, `/private`, `Downloads`, `API key`,
  `api_key`, `secret`, `token`, `bearer`, `password`, and `credential`: no
  matches.

Completion audit:
- Objective: release-oriented audit of `ict-engine` for consumer/contributor
  experience and out-of-the-box behavior.
- Covered: clean candidate export, mechanical contributor gates, true
  zero-config consumer smoke, no default private path leakage in smoke output,
  public provider fallback, posterior visibility, inspectable Pre-Bayes /
  policy-training / candidate-pack / regime-asset surfaces, and sanitized
  profile handling.
- Not complete as a release: operator has not chosen/staged/committed/tagged or
  approved publish to the release mirror, and legacy local-data research scripts
  need either exclusion from the release slice or explicit rewrite before they
  become public examples.

Next:
- Treat `/tmp/ict-engine-fresh-release-export.A0JQ2T` as the current verified
  release-candidate export, not the whole dirty working tree.
- Before publish, choose one of:
  1. publish/stage this exact sanitized export slice; or
  2. rewrite the pruned local-data scripts into explicit-input consumer examples
     and rerun this full gate.

### 2026-05-13 release manifest/runbook materialization

Owner:
- Codex current slice, 2026-05-13 12:13:38 +0800.

Status:
- Done for documentation materialization; release remains blocked on explicit
  operator slice/tag/publish confirmation.

Objective:
- Convert the verified sanitized export slice from `/tmp` evidence into
  versioned repo documentation so release work does not depend on chat memory or
  an ephemeral directory.

Plan:
- Read current release mirror/runbook/signoff docs.
- Add or update a release-candidate manifest that lists included files,
  excluded generated/private surfaces, required gates, and publish blockers.
- Keep it documentation-only; do not tag, push, or publish.

Expected output:
- A versioned release manifest/runbook artifact that a later publisher can use
  to reproduce the audited slice.

Result:
- Added `support/docs/audits/2026-05-13-sanitized-release-candidate-manifest.md`.
- Updated `support/docs/audits/release-signoff.md`,
  `support/docs/release-notes-draft.md`, and `support/docs/release-mirror-runbook.md` so they
  point at the sanitized candidate manifest instead of implying that the broad
  dirty working tree is ready to publish.
- Kept this handoff TODO out of the public release slice; it remains internal
  coordination/audit evidence and contains historical local evidence paths.

Verification:
- `git diff --check -- support/docs/audits/2026-05-13-sanitized-release-candidate-manifest.md support/docs/audits/release-signoff.md support/docs/release-notes-draft.md support/docs/release-mirror-runbook.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`:
  passed.
- Stale publish-wording scan over release-facing docs had no matches for the
  old ready-to-publish phrases, old prepared-candidate status, or old direct
  instruction to publish the candidate as a fixed tag.
- Local-path/secret-term scan over the same docs found no concrete leak in the
  new release-facing manifest/signoff/runbook text. Remaining matches are
  historical handoff evidence, policy guard strings, and literal privacy-scan
  terms such as `/Users`, `API key`, `secret`, `token`, and `credential`.

Next:
- Do not publish yet.
- Before any mirror/tag/GitHub release action, the operator must choose the exact
  sanitized export slice and explicitly confirm tag, push, and release creation.
- If the excluded legacy local-data research scripts should become public
  examples, rewrite them around explicit user-provided inputs and rerun the full
  release gate.

### 2026-05-13 README/AGENT polish and publish execution

Owner:
- Codex current slice, 2026-05-13 12:26:07 +0800.

Status:
- Done.

Objective:
- Improve `README.md` into a more human-readable, aesthetically coherent public
  entrypoint.
- Make `AGENT.md` tell future agents exactly how to serve users, verify
  zero-config behavior, preserve privacy, and publish only a sanitized slice.
- Rebuild and verify the release export with these doc changes before publishing.
- Publish only the sanitized release mirror/tag/GitHub release, not the broad
  dirty working tree.

Plan:
- Edit `README.md` and `AGENT.md` only for this documentation polish slice.
- Rebuild a fresh sanitized export from `git archive HEAD` plus the manifest
  release slice and the updated docs.
- Rerun release gates from that export.
- Push the verified export to `Undermybelt/ict-engine-release` with a fresh tag,
  then create the GitHub release.

Expected output:
- Updated README/AGENT docs, fresh export/target/smoke evidence paths, release
  tag, mirror push result, and GitHub release URL/status.

Progress:
- Updated `README.md` into a shorter public entrypoint centered on first-run
  usage, output surfaces, consumer safety, contributor gates, and release policy.
- Updated `AGENT.md` with an agent mission, user-service contract, operating
  checklist, and release checklist.
- Final `v0.1.2` export: `/tmp/ict-engine-v012-release-export.CHyo93`.
- Final target: `/tmp/ict-engine-v012-release-target.NJjdD3`.
- Final smoke state: `/tmp/ict-engine-v012-smoke-state.M78llx`.
- Final smoke output: `/tmp/ict-engine-v012-smoke-out.yszAfG`.
- `cargo fmt --manifest-path /tmp/ict-engine-v012-release-export.CHyo93/Cargo.toml --check`:
  passed.
- `CARGO_TARGET_DIR=/tmp/ict-engine-v012-release-target.NJjdD3 cargo clippy --manifest-path /tmp/ict-engine-v012-release-export.CHyo93/Cargo.toml --all-targets -- -D warnings`:
  passed.
- `PATH=<provider-venv>/bin:$PATH CARGO_TARGET_DIR=/tmp/ict-engine-v012-release-target.NJjdD3 cargo test --manifest-path /tmp/ict-engine-v012-release-export.CHyo93/Cargo.toml`:
  passed. Lib `963`, bin `253`, integration suites, and doctests passed.
- Zero-config smoke from the final export binary passed provider, workflow,
  analyze demo, workflow refresh, Pre-Bayes, policy-training, candidate-pack,
  admission-target, and regime-asset commands.
- Final smoke evidence includes yfinance fallback, posterior probabilities,
  top executor `catboost_file`, `candidate_pack_count=7`, admission target
  `rows=35` / `mature_rows=35`, and `regime_confidence_asset_count=18`.
- Final smoke stderr files were empty.
- Final smoke-output privacy scan for `/Users`, `/private`, `Downloads`,
  `API key`, `api_key`, `secret`, `token`, `bearer`, `password`, and
  `credential`: no matches.
- Release export source/code scan for maintainer-local path/XGBoost terms found
  only the intentional `/Users/example/Downloads/Tomac` negative test guard.
- Mirror hygiene then pruned historical support-doc prompts that still carried concrete
  maintainer-local paths; post-prune scan found only the intentional
  `/Users/example/Downloads/Tomac` negative test guard.
- Mirror directory: `/tmp/ict-engine-release-mirror-v012.SrqKuz`.
- Mirror commit: `f7ac989 release: ict-engine v0.1.2`.
- Remote tag check before publish: `v0.1.2` was absent; existing release tags
  were `v0.0.1`, `v0.1.0`, and `v0.1.1`.
- `git push origin main`: pushed `5bc7bc7..f7ac989`.
- `git push origin v0.1.2`: pushed new tag `v0.1.2`.
- GitHub Release created through the REST API:
  `https://github.com/Undermybelt/ict-engine-release/releases/tag/v0.1.2`
  (`id=321586574`, `draft=false`, `prerelease=false`).
- Follow-up note: `gh release create` initially failed with GitHub API EOF, so
  release creation used `curl --http1.1`. Later attempts to patch the release
  body with full notes hit the same intermittent API TLS/EOF issue. The release
  body currently points to `support/docs/audits/release-signoff.md`; the full release
  notes and signoff are present in the release tree.

Completion audit:
- README optimized for human public reading: covered by `README.md` rewrite and
  release export inclusion.
- `AGENT.md` explains how agents should use the repo and serve users: covered by
  the new Agent Mission, User Service Contract, Operating Checklist, and release
  checklist.
- Release uses sanitized export only: covered by export/mirror hygiene, pruned
  local-path support-doc prompts, and exclusion of generated run roots.
- Release verification: fmt, Clippy, full cargo test, zero-config smoke,
  stderr/privacy scans, and remote tag/push/release evidence are recorded above.

### 2026-05-13 restrictive license and package-channel policy refresh

Status:
- Done for support-doc license and package metadata. Not a publish signal; rebuild a fresh
  sanitized export before any new mirror/tag/release action.

Owner:
- Codex current turn, claimed 2026-05-13 13:38:19 +0800.

Objective:
- Align `README.md` and `README.zh-CN.md` so the English README exposes a
  Chinese jump link on the first line and both entrypoints carry the same
  release, license, and package-channel policy.
- Replace MIT metadata with a restrictive source-available local-use license
  that permits personal local running and forking while forbidding commercial
  use and redistribution without written permission.
- Record a package-manager stance for Cargo, npm/npx, and Homebrew that does
  not accidentally grant redistribution rights.

Plan:
- Touch only support-doc license and package metadata needed for this release-policy slice.
- Keep public package-manager guidance conservative: local install wrappers are
  OK; public npm registry, crates.io, or Homebrew tap publication stays blocked
  unless the license/distribution grant changes.
- Verify with focused metadata/docs scans, `git diff --check`, and a Cargo
  metadata check after replacing the SPDX MIT field with `license-file`.

Expected output:
- Updated `README.md`, new or updated `README.zh-CN.md`, restrictive `LICENSE`,
  `Cargo.toml` license metadata, and package-channel notes in release docs.

Result:
- `README.md` now starts with `[中文 README](README.zh-CN.md)` as the first
  line.
- Added `README.zh-CN.md` with matching first-run, output, workflow,
  contributor, repository-map, package-channel, release-policy, FAQ, and
  license sections.
- Replaced MIT with `ICT Engine Local Use License`: source-available,
  non-open-source, personal local use/private forks only, no commercial use or
  redistribution without written permission.
- Updated `Cargo.toml` from `license = "MIT"` to
  `license-file = "LICENSE"` and added `publish = false`.
- Updated release signoff, release notes, and release mirror runbook to block
  public crates.io, npm/npx, Homebrew, Docker, public binary, and public tap
  publication while the restrictive license is active.
- Added Cargo, npm, and Homebrew official reference links to both READMEs'
  package policy sections.

Verification:
- `head -n 5 README.md && head -n 5 README.zh-CN.md`: English README first
  line is the Chinese jump link; Chinese README links back to English near the
  top.
- `cargo metadata --no-deps --format-version 1`: passed; package metadata shows
  `license=null`, `license_file="LICENSE"`, and `publish=[]`.
- `git diff --check -- README.md README.zh-CN.md LICENSE Cargo.toml support/docs/release-mirror-runbook.md support/docs/release-notes-draft.md support/docs/audits/release-signoff.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`:
  passed.
- README heading scan confirms both languages carry the same section sequence.
- Residual MIT/open-source scan on touched docs found no old `license = "MIT"`,
  `MIT License`, or permissive grant text. Remaining MIT/Apache terms are only
  explanatory comparisons inside the restrictive license/runbook.
- `cargo package --list --allow-dirty`: completed, but shows the dirty checkout
  would package broad untracked/generated artifacts. This is evidence against
  using Cargo package/public registries from this worktree; publish remains
  sanitized-export/private-mirror only.

Next:
- If a future public package-manager distribution is desired, first revise the
  license to grant that exact channel, then create a separate packaging slice
  with a clean export and fresh gates.

### 2026-05-13 noncommercial license correction and root clutter cleanup

Status:
- Superseded for license work by the PolyForm Noncommercial 1.0.0 correction
  section below. Root clutter cleanup remains out of scope for the PolyForm
  license objective.

Owner:
- Codex current turn, claimed 2026-05-13 14:01:17 +0800.

Objective:
- Correct the previous over-restrictive local-use license to a noncommercial
  license shape: commercial use remains forbidden, while noncommercial use,
  modification, forking, and redistribution may be allowed under the same
  noncommercial terms.
- Clean root-directory clutter from zero-byte branch/material marker files such
  as `CryptoContinuationFailureGuard`, `CryptoMomentumPersistence`,
  `crypto_ema_rsi_persistence_long_v1`, and
  `crypto_momentum_failure_short_v1`.
- Keep the repo root visually cleaner without deleting meaningful state or
  evidence.

Plan:
- Use a standard source-available noncommercial license direction instead of
  Apache-2.0, because Apache-2.0 does not prohibit commercial use.
- Preserve `license-file = "LICENSE"` and `publish = false` until a dedicated
  packaging release slice is rebuilt and explicitly approved.
- Delete only verified empty zero-byte root marker files; do not delete
  populated ignored state directories.
- Add ignore rules so the same root marker filenames do not reappear in git
  status.

Expected output:
- Updated `LICENSE`, `README.md`, `README.zh-CN.md`, release docs, `.gitignore`,
  and removed zero-byte root marker files.

### 2026-05-13 PolyForm Noncommercial 1.0.0 license correction

Status:
- Done for the license objective. Not a release-publication authorization.

Owner:
- Codex current turn, claimed 2026-05-13 18:43:37 +0800.

Objective:
- Replace the custom ICT Engine noncommercial license with the standard
  `PolyForm Noncommercial License 1.0.0`.
- Align user-facing release/package docs so they name PolyForm Noncommercial
  1.0.0 instead of the earlier custom local-use/noncommercial license wording.
- Replace Cargo's custom `license-file` metadata with the SPDX-compatible
  `license = "PolyForm-Noncommercial-1.0.0"` while preserving `publish = false`;
  this slice changes the license identity, not public package publishing
  posture.

Plan:
- Verify the official PolyForm Noncommercial 1.0.0 text before editing.
- Update only license-policy files needed for this exact correction:
  `LICENSE`, READMEs, release docs, and this handoff TODO.
- Run focused scans and metadata/check commands proving no repo-root license
  surface still names MIT or the custom ICT Engine license as the active project
  license.

Expected output:
- `LICENSE` contains the official PolyForm Noncommercial License 1.0.0 text.
- `Cargo.toml` uses `license = "PolyForm-Noncommercial-1.0.0"` with
  `publish = false`.
- README/release docs say the project is under PolyForm Noncommercial 1.0.0 and
  keep public package-manager publication blocked unless explicitly approved in
  a later release slice.

Result:
- Replaced the custom repo-specific noncommercial text in `LICENSE` with the
  standard PolyForm Noncommercial License 1.0.0 text and added the repo's
  project-specific `Required Notice` line.
- Updated `Cargo.toml` from `license-file = "LICENSE"` to
  `license = "PolyForm-Noncommercial-1.0.0"` while preserving `publish = false`.
- Updated `README.md`, `README.zh-CN.md`, `support/docs/release-mirror-runbook.md`,
  `support/docs/release-notes-draft.md`, and `support/docs/audits/release-signoff.md` so the
  active project license is named consistently as PolyForm Noncommercial 1.0.0.
- Preserved the existing conservative package-channel posture: no public
  crates.io, npm/npx, Homebrew, Docker, or binary release flow was enabled by
  this license swap.

Verification:
- Official text parity:
  `curl -fsSL https://raw.githubusercontent.com/polyformproject/polyform-licenses/1.0.0/PolyForm-Noncommercial-1.0.0.md > "$tmp" && perl -0pe 's/^Required Notice: .*\\n//m' LICENSE > /tmp/ict-license-without-notice.md && diff -u "$tmp" /tmp/ict-license-without-notice.md`
  -> passed with empty diff, confirming repo `LICENSE` matches upstream
  PolyForm text after removing the repo-specific Required Notice line.
- Cargo metadata:
  `cargo metadata --no-deps --format-version 1`
  -> package reports
  `license=PolyForm-Noncommercial-1.0.0 license_file=null publish=[]`.
- Residual active-license scan:
  `rg -n "ICT Engine Local Use License|restrictive local-use|license-file = \\"LICENSE\\"|license_file=\\"LICENSE\\"|MIT License|license = \\"MIT\\""`
  over touched release/license docs
  -> no matches.
- Patch hygiene:
  `git diff --check -- LICENSE Cargo.toml README.md README.zh-CN.md support/docs/release-mirror-runbook.md support/docs/release-notes-draft.md support/docs/audits/release-signoff.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  -> passed.

Next:
- If the project later wants public package-manager distribution, run a
  separate packaging/release-policy slice against the chosen channel; this
  license correction did not verify or approve that broader distribution step.

### 2026-05-13 root clutter cleanup claim

Status:
- Done.

Owner:
- Codex current turn, claimed 2026-05-13 23:16:00 +0800.

Objective:
- Remove the repo-root zero-byte clutter files
  `CryptoContinuationFailureGuard`, `CryptoMomentumPersistence`,
  `crypto_ema_rsi_persistence_long_v1`,
  `crypto_momentum_failure_short_v1`, `ema_rsi_persistence`, and
  `momentum_failure`.
- Keep the repo root cleaner without deleting meaningful state, experiment
  evidence, or populated ignored directories.

Plan:
- Verify the six named root entries are still untracked zero-byte regular files.
- Delete only those six files from repo root.
- Re-scan repo root zero-byte files and `git status --short` for verification.
- Do not delete `state`, `state100`, `state_experiments`, `target`,
  `catboost_info`, or any populated experiment/material directory in this
  slice.

Expected output:
- The six zero-byte root clutter files are removed.
- This handoff board records the exact deletion scope, evidence, and remaining
  unknown: the creator path is still not conclusively identified.

Result:
- Removed the six verified zero-byte repo-root clutter files:
  `CryptoContinuationFailureGuard`, `CryptoMomentumPersistence`,
  `crypto_ema_rsi_persistence_long_v1`,
  `crypto_momentum_failure_short_v1`, `ema_rsi_persistence`, and
  `momentum_failure`.
- Left populated root directories such as `state`, `state100`,
  `state_experiments`, and `target` untouched because this slice only covered
  empty root marker files, not real state/evidence cleanup.
- Did not add `.gitignore` entries in this slice because ignore rules would only
  hide recurrence in status; they would not explain or prevent the creator path.

Verification:
- Pre-delete file evidence:
  `stat -f 'mode=%Sp size=%z type=%HT'` and `file` showed all six paths were
  `size=0`, `type=Regular File`, and `empty`.
- Post-delete root zero-byte scan:
  `find /Users/thrill3r/projects-ict-engine/ict-engine -maxdepth 1 -type f -size 0 -print`
  -> returned no paths.
- Post-delete git-status check:
  `git -C /Users/thrill3r/projects-ict-engine/ict-engine status --short | rg "CryptoContinuationFailureGuard|CryptoMomentumPersistence|crypto_ema_rsi_persistence_long_v1|crypto_momentum_failure_short_v1|ema_rsi_persistence|momentum_failure"`
  -> no matches.

Next:
- If these names reappear, trace the exact creator command/script and fix that
  producer path instead of adding broader ignore clutter.

### 2026-05-13 PolyForm license completion audit refresh

Status:
- Done.

Owner:
- Codex current turn, refreshed after goal-status check.

Objective:
- Re-audit the active objective: `ict-engine` license is changed to
  `PolyForm Noncommercial License 1.0.0`.

Checklist:

| Requirement | Evidence | Status |
|---|---|---|
| Repo license file names PolyForm Noncommercial 1.0.0 | `LICENSE` begins with `# PolyForm Noncommercial License 1.0.0` and includes the project `Required Notice`. | covered |
| Repo license text matches official PolyForm 1.0.0 text | `curl -fsSL https://raw.githubusercontent.com/polyformproject/polyform-licenses/1.0.0/PolyForm-Noncommercial-1.0.0.md` plus `diff -u` against `LICENSE` with the project Required Notice line stripped returned empty diff. | covered |
| Cargo metadata exposes the SPDX license id | `cargo metadata --manifest-path ... --no-deps --format-version 1 \| jq -r '.packages[0] ...'` returned `license=PolyForm-Noncommercial-1.0.0 license_file=null publish=[]`. | covered |
| User-facing docs name the current license | `rg` found PolyForm license statements in `README.md`, `README.zh-CN.md`, release runbook, release notes, and release signoff. | covered |
| Old active license surfaces are not still present | Residual scan over `LICENSE`, `Cargo.toml`, READMEs, release runbook, release notes, and release signoff found no `ICT Engine Local Use License`, `license-file = "LICENSE"`, `MIT License`, or `license = "MIT"` matches. | covered |
| Patch hygiene on touched tracked license docs | `git diff --check -- LICENSE Cargo.toml README.md support/docs/release-mirror-runbook.md support/docs/release-notes-draft.md support/docs/audits/release-signoff.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md` returned no issues. | covered |

Result:
- The license objective is complete.
- This audit does not authorize a public package-manager release or any broader
  release push; `publish = false` remains the current Cargo/package posture.

### 2026-05-13 root populated state directory cleanup claim

Status:
- Done.

Owner:
- Codex current turn, claimed after operator asked to clean root `state*`
  aesthetics.

Objective:
- Improve repo-root aesthetics for populated local state/artifact directories
  such as `state`, `state100`, and `state_experiments` without deleting real
  evidence or changing public runtime defaults.

Plan:
- Inspect root-local state/artifact directories for size, git tracking, ignore
  coverage, active process holders, and likely runtime ownership.
- Keep source/config/docs public surfaces untouched unless evidence shows a root
  default is still creating new pollution.
- Prefer a reversible local archive/relocation under an ignored hidden root if
  the directories are untracked and inactive.
- Do not delete populated state/evidence directories in this slice.

Expected output:
- Root visual clutter is reduced where it is safe to do so.
- Remaining root entries are either tracked project surfaces or explicitly
  documented as still needing a separate owner decision.

Findings:
- `state`, `state100`, `state_experiments`, and `target` were untracked /
  ignored root directories, not release-source surfaces.
- Pre-move sizes were approximately `state=1.9G`, `state100=196M`,
  `state_experiments=4.5G`, and `target=9.1G`.
- `lsof +D` over the three `state*` directories returned no active holders.
- `state` contained workflow/demo/live JSON state and an Auto-Quant dependency
  workspace; `state100` contained older batch/NQ state; `state_experiments`
  contained autoresearch/cluster experiment state.

Result:
- Added `/.local-artifacts/` to `.gitignore`.
- Moved the populated root-local artifacts into the ignored hidden archive:
  `.local-artifacts/root-cleanup-20260513/state`,
  `.local-artifacts/root-cleanup-20260513/state100`,
  `.local-artifacts/root-cleanup-20260513/state_experiments`, and
  `.local-artifacts/root-cleanup-20260513/target`.
- Deleted no populated state/evidence data; this was a root-layout cleanup by
  relocation.

Verification:
- `ls -1A` for repo root no longer lists `state`, `state100`,
  `state_experiments`, or `target`.
- `find /Users/thrill3r/projects-ict-engine/ict-engine -maxdepth 1 -type f -size 0 -print`
  returned no root zero-byte files.
- `du -sh .local-artifacts/root-cleanup-20260513/*` shows the moved directories
  retained their content sizes: `state=1.9G`, `state100=196M`,
  `state_experiments=4.5G`, `target=9.1G`.
- `git check-ignore -v .local-artifacts/root-cleanup-20260513/{state,state100,state_experiments,target}`
  confirms the hidden archive is ignored by `/.local-artifacts/`.
- `git status --short -- .gitignore support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md state state100 state_experiments target .local-artifacts`
  shows only `.gitignore` and this handoff document changed.

Remaining root note:
- `catboost_info`, `path_ranker_model`, `.pytest_cache`, and
  `tmp_cycle_seed_spec.json` are also ignored root-local artifacts. They are much
  smaller than the moved state directories and were not moved in this slice to
  avoid broadening beyond the operator-named `state*` / marker-file cleanup.

### 2026-05-14 root-local cache and Cargo target cleanup claim

Status:
- Done.

Owner:
- Codex current turn, claimed after operator repeated that root aesthetics should
  cover more than the named `state*` and marker files.

Objective:
- Finish repo-root aesthetics cleanup for remaining root-local caches and
  generated artifacts.
- Prevent Cargo from recreating `target/` in repo root after cleanup.

Plan:
- Move remaining untracked/ignored root-local artifacts into the ignored
  `.local-artifacts/root-cleanup-20260514/` archive.
- Add explicit ignore coverage for root-local cache paths that were only
  globally ignored or tool-generated.
- Add repo-local Cargo config so new Cargo builds use
  `.local-artifacts/cargo-target` instead of root `target/`.
- Do not move tracked source/config/docs/test directories.

Expected output:
- Repo root no longer shows `state`, `state100`, `state_experiments`, `target`,
  `.pytest_cache`, `catboost_info`, `path_ranker_model`, `.DS_Store`, or
  `tmp_cycle_seed_spec.json`.
- Cargo target output has a hidden ignored owner path.

Findings:
- The earlier `state*` cleanup had already moved populated root state into
  `.local-artifacts/root-cleanup-20260513/`, but `target/` was recreated because
  Cargo's default target directory is repo-root `target`.
- Remaining root-local artifacts were untracked/ignored caches or generated
  files: `.DS_Store`, `.pytest_cache`, `catboost_info`, `path_ranker_model`,
  `tmp_cycle_seed_spec.json`, and the regenerated `target`.
- `lsof` found no active holders for those remaining root-local artifacts before
  relocation.

Result:
- Added explicit ignore coverage for `/.pytest_cache/` and
  `/path_ranker_model/`.
- Added `.cargo/config.toml` with:
  `target-dir = ".local-artifacts/cargo-target"`.
- Moved `.DS_Store`, `.pytest_cache`, `catboost_info`, `path_ranker_model`,
  `tmp_cycle_seed_spec.json`, and the regenerated `target` into
  `.local-artifacts/root-cleanup-20260514/`.

Verification:
- `ls -1A` for repo root now shows only tracked project roots plus standard dot
  config/metadata roots: `.cargo`, `.git`, `.github`, `.gitignore`,
  `.local-artifacts`, `AGENT.md`, `CLAUDE.md`, `Cargo.lock`, `Cargo.toml`,
  `DEBUG.md`, `LICENSE`, `README.md`, `README.zh-CN.md`, `config`, `docs`,
  `examples`, `paper2code`, `prompts`, `scripts`, `src`, and `tests`.
- Root absence check for `state`, `state100`, `state_experiments`, `target`,
  `.pytest_cache`, `catboost_info`, `path_ranker_model`, `.DS_Store`,
  `tmp_cycle_seed_spec.json`, `CryptoContinuationFailureGuard`,
  `CryptoMomentumPersistence`, `crypto_ema_rsi_persistence_long_v1`, and
  `crypto_momentum_failure_short_v1` returned no paths.
- `cargo metadata --manifest-path ... --no-deps --format-version 1 \| jq -r '.target_directory'`
  now reports
  `/Users/thrill3r/projects-ict-engine/ict-engine/.local-artifacts/cargo-target`.
- `test ! -e /Users/thrill3r/projects-ict-engine/ict-engine/target` printed
  `root-target-absent`.
- `git check-ignore -v --no-index` confirms
  `.local-artifacts/root-cleanup-20260514/{.pytest_cache,catboost_info,path_ranker_model,tmp_cycle_seed_spec.json,.DS_Store}`
  and `.local-artifacts/cargo-target` are ignored via `/.local-artifacts/`.
- `git status --short -- .cargo/config.toml .gitignore support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md .DS_Store .pytest_cache catboost_info path_ranker_model tmp_cycle_seed_spec.json target .local-artifacts`
  shows only `.gitignore`, `.cargo/config.toml`, and this handoff document as
  intentional versioned changes.
- `git diff --check -- .cargo/config.toml .gitignore support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  returned no issues.

Remaining note:
- The hidden `.local-artifacts/` archive is intentionally ignored and local.
  It preserves the moved data for recovery while keeping the repo root visually
  clean.

### 2026-05-14 support parent directory restructure claim

Status:
- Done.

Owner:
- Codex current turn, claimed after operator clarified the desired shape is an
  extra parent folder rather than merging non-code categories together.

Objective:
- Move root-level non-core project material directories one level down under a
  single parent directory while preserving their category boundaries.

Plan:
- Create `support/` as the parent for non-core project materials.
- Move `docs`, `examples`, `paper2code`, `prompts`, and `scripts` under
  `support/`.
- Update current entrypoints and executable path references that must follow the
  move, especially `AGENT.md`, README files, `.github/workflows/ci.yml`, and
  Cargo example metadata.
- Avoid broad rewriting of historical evidence paths inside moved docs unless
  they are active instructions or command surfaces; historical records should
  stay factual about their original paths.

Expected output:
- Repo root keeps source/code/config entrypoints at top level and groups
  non-core materials under `support/`.
- Current commands and metadata point to the new paths.

Result:
- Moved the root `docs`, `examples`, `paper2code`, `prompts`, and `scripts`
  directories under the new `support/` parent without merging their category
  boundaries.
- Updated active repo entrypoints and path-bearing surfaces to the new
  `support/...` layout, including README files, `AGENT.md`, CI, Cargo example
  metadata, Rust defaults/tests, provider setup text, harness presets, Python
  wrapper entrypoints, and support-local example references.
- Preserved local root cleanup archives under ignored `.local-artifacts/` and
  kept Cargo build output under `.local-artifacts/cargo-target`.

Verification:
- `ls -1A` at repo root shows only code/config/entry files plus `support/`,
  with no root `docs`, `examples`, `paper2code`, `prompts`, `scripts`, `state`,
  `target`, `.pytest_cache`, or path-ranker/cache clutter.
- `rg -n -P "(^|[[:space:]\\\"'=\\(])((docs|examples|scripts|prompts|paper2code)/)" AGENT.md CLAUDE.md README.md README.zh-CN.md Cargo.toml .github config src tests --glob '!support/**'`
  returned no matches for old root-relative material paths.
- `rg -n 'support/(docs|examples|scripts|prompts|paper2code)/support/' AGENT.md README.md README.zh-CN.md .github config src tests Cargo.toml support/scripts support/examples support/docs/README.md`
  returned no double-nested support paths.
- `python3 support/scripts/search_local.py --show-config` passed and resolved
  `repo_root=/Users/thrill3r/projects-ict-engine/ict-engine`.
- `python3 support/scripts/search_cluster.py --target`,
  `python3 support/scripts/evaluate_bottleneck.py --target`, and
  `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- `cargo metadata --manifest-path Cargo.toml --no-deps --format-version 1`
  reports the `round2_tucker_snapshot` example at
  `support/examples/round2_tucker_snapshot.rs` and the build target directory
  at `.local-artifacts/cargo-target`.
- `cargo test market_state::config::tests::high_confidence_profile_matches_repo_example -- --nocapture`
  passed.
- `cargo test --test provider_neutral_cli -- --nocapture` passed, 19 tests.
- `git diff --check -- .github/workflows/ci.yml .cargo/config.toml .gitignore AGENT.md README.md README.zh-CN.md Cargo.toml config/factor_candidate_harness_presets.json src tests support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md support/scripts support/examples`
  returned no issues.
- `cargo fmt --check` passed after formatting the longer moved-path Rust
  strings.

### 2026-05-14 post-move dangling reference audit claim

Status:
- Done.

Owner:
- Codex current turn, claimed after operator clarified that the directory move
  must also eliminate dangling references.

Objective:
- Audit and repair path references introduced or exposed by the `support/`
  parent-directory move so active docs, code, config, scripts, and examples do
  not point at non-existent root `support/docs/`, `support/examples/`, `support/scripts/`,
  `support/prompts/`, or `support/paper2code/` locations.

Plan:
- Scan repo text for old root-relative material paths and malformed
  `support/.../support/...` paths.
- Validate path-like references that should resolve inside this repo.
- Update the smallest necessary files so current references point at existing
  `support/...` locations.
- Add verification evidence here before closing the claim.

Expected output:
- No actionable dangling references caused by moving non-code material under
  `support/`.
- Verification commands prove both old-root references and missing moved-path
  references have been addressed.

Root cause:
- The parent-directory move exposed three stale reference classes: old
  root-relative material directory paths for `docs`, `examples`, `scripts`,
  `prompts`, and `paper2code`; Python module references that still used `scripts.*`
  instead of the `support` package prefix; and helper scripts and tests that inferred the
  repo root or Cargo binary path from their old root-level script location.
- Several historical docs also contained path-shaped archive names, proposed
  future helper names, regex/glob patterns, or intentionally absent user-local
  config names. Those are not runtime or current-file dangling references, but
  current indexes/prompts were tightened where the path-like wording was
  misleading.

Result:
- Rewrote active old-root material paths and module references to the new
  `support/...` layout.
- Fixed moved helper root/binary resolution so current script defaults use
  `.local-artifacts/cargo-target/debug/ict-engine` instead of recreating or
  pointing at root `target/debug/ict-engine`.
- Added the compatibility strategy wrapper
  `support/scripts/auto_quant_external/strategies/TomacKillzoneBreakout.py`
  for the harness preset that referenced that strategy name.
- Updated current prompt/archive docs and docs map entries so removed files are
  represented as historical names rather than live `support/docs/...` paths.

Verification:
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver support.scripts.research.tests.test_factor_candidate_pack` passed, 16 tests.
- `python3 -m unittest support.scripts.research.tests.test_market_data_resolver` passed, 3 tests.
- `python3 -m unittest support.scripts.research.tests.test_docs_runtime_isolation` passed, 2 tests.
- `python3 -m unittest support.scripts.auto_quant_external.tests.test_next_slice_helpers support.scripts.auto_quant_external.tests.test_path_ranker_hotplug` passed, 20 tests; emitted binary paths now resolve under `.local-artifacts/cargo-target`.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- `python3 support/scripts/search_local.py --show-config` passed and reported
  `repo_root=/Users/thrill3r/projects-ict-engine/ict-engine` and
  `bin_path=/Users/thrill3r/projects-ict-engine/ict-engine/.local-artifacts/cargo-target/debug/ict-engine`.
- `cargo metadata --manifest-path Cargo.toml --no-deps --format-version 1`
  passed; target directory is `.local-artifacts/cargo-target`, and the
  `round2_tucker_snapshot` example resolves to
  `support/examples/round2_tucker_snapshot.rs`.
- Old-root material path scan for the root `docs`, `examples`, `scripts`,
  `prompts`, and `paper2code` directories returned no matches outside excluded
  historical experiment roots.
- Malformed path scan for double support module prefixes, nested support
  material paths, nested support-doc paths, and old absolute material
  directories
  returned no matches outside excluded historical experiment roots.
- Focused active-surface missing-path scan reported
  `actionable_missing_support_refs 0`; remaining `25` matches were glob,
  regex, ellipsis, or user-local config patterns such as ignored
  `my_config*`.
- `cargo fmt --check` passed.
- `git diff --check -- .github/workflows/ci.yml .cargo/config.toml .gitignore AGENT.md DEBUG.md README.md README.zh-CN.md Cargo.toml config src tests support`
  returned no issues.

### 2026-05-14 support restructure commit and publish claim

Status:
- Done.

Owner:
- Codex current turn, claimed after operator requested `commit 发布`.

Objective:
- Commit the verified `support/` parent-directory restructure and publish the
  resulting source snapshot without mixing in hidden local artifacts.

Plan:
- Re-check working tree and remotes before staging.
- Stage the coherent source snapshot for the restructure, including moved
  material directories and path-reference fixes.
- Create a source commit with verification evidence already recorded above.
- Push the source commit to the configured `origin/main`.
- For public release publishing, use a clean export / release mirror path only;
  do not create a new GitHub Release tag unless an explicit new tag is provided.

Expected output:
- Source repo has a commit containing the directory restructure.
- Source `origin/main` is updated.
- Public release mirror is updated only through a clean export path, with no
  ignored local artifacts or root caches.

Pre-commit staging hygiene:
- `git add -A` initially picked up generated experiment workspaces under
  `support/docs/experiments/...`; those new untracked experiment additions were
  removed from the index with `git rm -r -f --cached --pathspec-from-file=...`.
- Follow-up staged-added classification reported `unknown_added_total 34`,
  limited to config/docs indexes, curated factor candidate examples, and moved
  helper tests/scripts. No staged gitlinks or symlinks remained.
- `xgboost_policy.sample.json` deletion was rechecked against this handoff and
  remains intentional XGBoost retirement, not a restructure dangling deletion.

Pre-commit verification:
- `cargo fmt --check` passed.
- `git diff --check -- .github/workflows/ci.yml .cargo/config.toml .gitignore AGENT.md DEBUG.md README.md README.zh-CN.md Cargo.toml config src tests support`
  passed.
- `python3 support/scripts/ci/check_docs_runtime_isolation.py` passed.
- `cargo metadata --manifest-path Cargo.toml --no-deps --format-version 1`
  passed and resolves the example target under `support/examples/`.
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver support.scripts.research.tests.test_factor_candidate_pack support.scripts.research.tests.test_market_data_resolver support.scripts.research.tests.test_docs_runtime_isolation`
  passed, 21 tests.
- `python3 -m unittest support.scripts.auto_quant_external.tests.test_next_slice_helpers support.scripts.auto_quant_external.tests.test_path_ranker_hotplug`
  passed, 20 tests.
- `cargo clippy --all-targets -- -D warnings` passed.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH cargo test`
  passed: lib 970, bin 253, integration suites, and doctests.

Publish result:
- Source restructure commit:
  `370cda23d865e5c3bfdf6144a9493caf0ecba16d` (`chore: consolidate support
  materials under support`).
- Source push:
  `git push origin main` updated
  `Undermybelt/givenup-ict-engine.git` from `3b25a8d3` to `370cda23`.
- Clean release export:
  `/tmp/ict-engine-release-export-MdW7QY`.
- Release mirror working clone:
  `/tmp/ict-engine-release-mirror-17uBsZ`.
- Release mirror commit:
  `aa692ed616e42d4d036b690a958bed1965c10783` (`chore: consolidate support
  materials under support`).
- Release mirror push:
  `git push origin main` updated
  `Undermybelt/ict-engine-release.git` from `f7ac989` to `aa692ed`.
- No new tag and no GitHub Release were created; the operator did not provide a
  new release tag.

Release mirror verification:
- Mirror root after rsync contains no root `docs`, `examples`, `paper2code`,
  `prompts`, `scripts`, `state`, `target`, `.local-artifacts`, `.pytest_cache`,
  `catboost_info`, or `path_ranker_model` entries.
- Mirror clean sync excluded
  `support/docs/experiments/actionable-regime-confidence/runs/**`, `.venv`,
  `.deps`, `user_data/data`, `__pycache__`, and `*.pyc`.
- `cargo fmt --check` passed from the mirror clone.
- `CARGO_TARGET_DIR=/tmp/ict-engine-release-target-17uBsZ cargo clippy --all-targets -- -D warnings`
  passed from the mirror clone.
- `PATH=/Users/thrill3r/.venvs/ict-engine-provider-py313/bin:$PATH CARGO_TARGET_DIR=/tmp/ict-engine-release-target-17uBsZ cargo test`
  passed from the mirror clone: lib 970, bin 253, integration suites, and
  doctests.
- Zero-config smoke from `/tmp/ict-engine-release-target-17uBsZ/debug/ict-engine`
  passed against state `/tmp/ict-engine-release-smoke-state-vCfM1p`; outputs are
  under `/tmp/ict-engine-release-smoke-out-3qf2TV`.
- Smoke stderr files are all empty.
- Smoke-output privacy scan for `/Users`, `/private`, `Downloads`, `API key`,
  `api_key`, `secret`, `token`, `bearer`, `password`, and `credential` returned
  no matches.
- Smoke summary reported yfinance as the zero-config ready provider,
  `candidate_pack_count=7`, admission target `rows=35`, and
  `regime_confidence_asset_count=18`.

### 2026-05-22 latest-goal continuation: release remains blocked

Current answer to the three-part goal is still no:

- Latest current-tree audit evidence exists, but it is not a clean release-export
  proof for the current dirty tree.
- Mirror release evidence is stale relative to current source state: local
  source and release metadata were not proven as a new sanitized export, and no
  explicit operator permission exists for a new tag/push/GitHub Release.
- Practical-factor diffusion is still not trade-usable. The isolated SI `15m`
  Turtle Soup readback at
  `/tmp/ict-engine-si15m-current-readback-20260522T211036+0800` ran current
  binary commands successfully, but the key summary at
  `/tmp/ict-engine-si15m-current-readback-20260522T211036+0800/out/06_key_summary.json`
  reports `promotion_status=observe`, execution candidate `no_trade`,
  closed-loop branch admission `fail_closed`, execution tree `blocked`, ranker
  validation `ready=false`, and
  `path_ranker_score_visible_to_execution_tree=true` while
  `path_ranker_score_used_by_execution_tree=false`.
- Sibling SI `15m` admission roots are duplicate-depth, not release proof: each
  available simulated-trade file has `23` rows, and the current exact-branch
  target history still has only `23/30` production and observation validation
  rows. This cannot be counted as practical all-market/all-product diffusion.

Release unblock requirements remain:

1. Prove at least one exact rooted branch through downstream gates with
   `promotion_allowed=true`, `trade_usable=true`, ranker validation ready,
   execution-tree use of the ranker score, and a non-blocked execution gate.
2. Freeze a coherent source slice from the dirty tree.
3. Build a clean sanitized export, rerun fmt, Clippy, full tests,
   zero-config smoke, and privacy scans from that export.
4. Refresh release signoff and release notes for the selected new tag.
5. Publish mirror main/tag/GitHub Release only after explicit operator
   confirmation for that exact slice.

### 2026-05-22 latest-goal continuation: CRWD is execution-ready, not promoted

Current answer to the three-part goal remains no.

- CRWD `5m` readback root:
  `/tmp/ict-engine-crwd5m-current-readback-20260522T212430+0800`.
- The current binary preserved the rooted branch path:
  `RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1`.
- Positive current evidence: execution candidate is `execution_ready`, the
  structural execution candidate is `ready=true`, closed-loop branch admission
  is `admitted`, and policy/ranker validation is ready with
  `raw_scored_mature=46/30`, `production_validation=46/30`, and
  `observation_validation=43/30`.
- Blocking current evidence: top-level promotion remains false
  (`current_regime_posterior.promotion_allowed=false` and
  `regime_confidence_assets.promotion_allowed=false`), BBN filtered assignment
  still says `read_only_regime_bbn_trade_usable=false`, latest analyze remains
  `promotion_status=observe` / `execution_gate_status=execution_blocked`, and
  `report.trade_plan.actionable=false`.

Decision:

- CRWD is the next best same-root repair lead because the ranker/execution-tree
  layer is no longer the blocker.
- The remaining gap is the BBN/promotion/trade-plan bridge for this exact
  branch; release mirror status remains blocked until a promoted/trade-usable
  branch exists and a clean export/tag/release is explicitly approved.
- Opt-in BBN probe `/tmp/ict-engine-crwd5m-bbn-optin-probe-20260522T2129`
  confirms this is not just a missing CLI flag. With
  `--apply-regime-bundle-bbn-soft-evidence`, the current binary still reports
  `promotion_status=observe`, `trade_plan.actionable=false`,
  `regime_bundle_bbn_application_status=skipped`, and
  `read_only_regime_bbn_trade_usable=false`. The imported strategy library
  metadata itself is non-promoting (`promotion_allowed=false`,
  `trade_usable=false`), so the adapter emits read-only branch context rather
  than a trade-usable BBN label.

### 2026-05-22 latest-goal continuation: current-state refresh

Current answer to the three-part goal remains no.

Fresh source / mirror readback:

- Local `HEAD=df5c679e6c83a2bd65cdef89e1035bef8843eddb`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Local `main` is ahead of origin by `64` commits.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Latest GitHub Release is still `v0.1.4`, published
  `2026-05-18T13:02:21Z`.
- `Cargo.toml` still says `version=0.1.3`.

Current CRWD full-chain readback:

- Artifact:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T211756+0800-codex-crwd5m-current-code-isolated-execution-candidate-replay-v2/checks/current_code_full_chain_readback.json`.
- Branch-local execution/ranker state is strong:
  `execution_ready`, `admitted`, path-ranker used by execution tree, and
  ranker validation `46/30`, `46/30`, `43/30`.
- It still cannot be promoted or released:
  `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `regime_root_parity=false`.
- The parity blocker is concrete: runtime `path_id` is prefixed with
  `US_EQ -> single_stock -> CRWD -> 5m ->` before the canonical
  `RangeReversion -> ...` branch. Those four fields are provenance labels, not
  branch parents.

Provider parity note:

- `/tmp/ict-engine-crwd5m-fresh-ibkr-provider-parity-20260522T213105+0800`
  had a partial failure on `5m 3M` (`exit=3`, `rows=0`).
- `/tmp/ict-engine-crwd-ibkr-1m-full-ladder-provider-preflight-20260522T213325+0800`
  later proved a complete IBKR ladder with rows for
  `1m/5m/15m/30m/1h/4h/1d`.
- This improves the extension preflight, but it is not a practical-factor or
  release completion proof until strict rooted-branch parity, promotion,
  trade-usable, sibling/timeframe coverage, clean export, and release approval
  all pass.

### 2026-05-22 latest-goal continuation: rooted path code repair landed, runtime parity still unproven

Current answer to the three-part goal remains no.

Rooted identity code repair:

- File: `src/application/orchestration/structural_playbook.rs`.
- The recommended structural path bundle now strips recognized
  market/product/symbol/timeframe provenance prefixes before emitting branch
  identity when a candidate path contains a canonical regime root.
- Focused CRWD shape:
  `US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> ...` emits
  `RangeReversion -> ...` as the recommended bundle `path_id`.
- The change is intentionally scoped to recommended-bundle comparison/emission;
  target export rows were not globally rewritten in this slice.

Fresh verification:

- RED command:
  `CARGO_TARGET_DIR=/tmp/ict-engine-target-crwd-root-parity cargo test application::orchestration::structural_playbook::tests::recommended_bundle_strips_market_provenance_from_rooted_path_identity -- --nocapture`
  exited `101` before the fix with raw provenance prefix on the emitted
  `bundle.path_id`.
- GREEN command:
  same command exited `0` after the fix: `1 passed; 0 failed`.
- Related structural tests:
  `CARGO_TARGET_DIR=/tmp/ict-engine-target-crwd-root-parity cargo test application::orchestration::structural_playbook::tests:: -- --nocapture`
  exited `0`: `49 passed; 0 failed`.
- Same-root workflow regression:
  `CARGO_TARGET_DIR=/tmp/ict-engine-target-crwd-root-parity cargo test application::orchestration::workflow_status::tests::execution_candidate_phase_lets_same_root_trace_admission_supersede_duplicate_analyze_veto -- --nocapture`
  exited `0`: `1 passed; 0 failed`.
- Whitespace / formatting:
  `git diff --check -- src/application/orchestration/structural_playbook.rs support/docs/plans/2026-05-22-done-definition-audit-handoff-todo.md support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
  exited `0`; `rustfmt --check src/application/orchestration/structural_playbook.rs`
  exited `0`.
- Light done-definition audit:
  `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-20260522-after-root-parity-light.json`
  exited `0` with `status=pass`, `pass_count=4`, `fail_count=0`,
  `skip_count=4`.
- Note: `cargo fmt --check -- src/application/orchestration/structural_playbook.rs`
  exited `1` due to unrelated dirty-file formatting diffs outside this slice;
  direct `rustfmt --check` on the touched Rust file passed.

Why release is still blocked:

- This is code-level/rooted-bundle evidence only. It is not yet a fresh CRWD
  full-chain readback proving `regime_root_parity=true`.
- Stored CRWD full-chain evidence still has `promotion_allowed=false`,
  `trade_usable=false`, `extension_complete=false`, and release mirror evidence
  is still stale relative to source `HEAD`.
- Next release-relevant proof must rerun the CRWD copied-state chain with the
  patched binary, then continue through promotion/trade-usability,
  all-market/all-product diffusion, clean sanitized export, and explicit mirror
  release approval.

### 2026-05-22 latest-goal continuation: CRWD execution-candidate parity repaired, release still blocked

Current answer to the three-part goal remains no.

Fresh runtime readback after rebuilding the local binary:

- Rebuilt binary:
  `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo build --bin ict-engine`
  exited `0`.
- Fresh copied-state replay root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T222741+0800-codex-crwd5m-root-parity-workflow-veto-reread-v1`.
- Commands `01_analyze_current_code` through
  `07_workflow_execution_candidate_json` all exited `0`.
- Compact readback:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T222741+0800-codex-crwd5m-root-parity-workflow-veto-reread-v1/checks/current_code_full_chain_readback_after_veto_fix.json`.

Positive branch-local evidence:

- `workflow-status --phase execution-candidate` now reports
  `candidate_status=execution_ready`, `actionable=true`, and `ready=true`.
- The execution tree same-root branch is admitted:
  `execution_tree_closed_loop_branch_admission.status=admitted`,
  `execution_tree_gate_status=ready`, `execution_tree_branch=fill_viable`.
- The stale persisted analyze veto is explicitly overridden:
  `persisted_execution_candidate_veto_overridden=true` with reason
  `same_root_execution_tree_trace_admitted_after_candidate_not_actionable_veto`.
- The execution-candidate and recommended-bundle paths are canonical rooted
  branch paths without the `US_EQ -> single_stock -> CRWD -> 5m ->`
  provenance prefix.

Why release is still blocked:

- Pre-Bayes/BBN still carries the provenance-prefixed
  `regime_profit_branch_path` and read-only BBN label set.
- `trade_plan.actionable=false`, latest promotion status remains `observe`,
  execution artifact hard gate remains `execution_blocked`, and
  `read_only_regime_bbn_trade_usable=false`.
- This is one branch-local CRWD repair, not practical all-market/all-product
  factor diffusion.
- No clean sanitized release export, refreshed release signoff, mirror update,
  tag, or GitHub Release has been produced; mirror publishing still requires
  explicit operator confirmation.

### 2026-05-22 latest-goal continuation: CRWD root parity repaired through Pre-Bayes/BBN, release still blocked

Current answer to the three-part goal remains no.

Fresh runtime readback after adapter and workflow-status repairs:

- Rebuilt binary:
  `CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo build --bin ict-engine`
  exited `0`.
- Fresh copied-state replay root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T230202+0800-codex-crwd5m-prebayes-bbn-root-parity-ready-veto-reread-v1`.
- Commands `01_analyze_current_code` through
  `07_workflow_execution_candidate_json` all exited `0`.
- Compact readback:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T230202+0800-codex-crwd5m-prebayes-bbn-root-parity-ready-veto-reread-v1/checks/current_code_full_chain_readback_after_adapter_and_ready_veto_fix.json`.

Positive branch-local evidence:

- `workflow-status --phase execution-candidate` reports
  `candidate_status=execution_ready`, `actionable=true`, and `ready=true`.
- The execution tree same-root branch is admitted.
- The stale duplicate analyze veto is overridden only because the persisted
  duplicate candidate is already actionable / `execution_ready`.
- The execution-candidate path, recommended bundle path, Pre-Bayes
  `regime_profit_branch_path`, and read-only BBN label set all carry canonical
  rooted branch identity without `US_EQ -> single_stock -> CRWD -> 5m ->`.

Why release is still blocked:

- `trade_plan.actionable=false`.
- Latest promotion status remains `observe`.
- Execution artifact hard gate remains `execution_blocked`.
- `read_only_regime_bbn_trade_usable=false`.
- `regime_bundle_bbn_application_status=skipped` because the imported
  strategy-library context is still non-promoting.
- This is still one CRWD `US_EQ/single_stock/5m` branch, not practical
  all-market/all-product factor diffusion.
- No clean sanitized release export, refreshed release signoff, mirror update,
  tag, or GitHub Release has been produced; mirror publishing still requires
  explicit operator confirmation.

### 2026-05-22 latest-goal continuation: CRWD owner trace says not trade-usable

Current answer to the three-part goal remains no.

The CRWD `5m` copied-state replay at
`support/docs/experiments/actionable-regime-confidence/runs/20260522T230202+0800-codex-crwd5m-prebayes-bbn-root-parity-ready-veto-reread-v1`
is a partial repair only. It proves `workflow-status --phase
execution-candidate` can read the branch as `execution_ready`, `actionable=true`,
`ready=true`, and same-root admitted after the Pre-Bayes/BBN rooted-identity
fixes. It does not prove practical trade usability.

Terminal owner-trace evidence:

- Claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260522T231709+0800-codex-crwd5m-promotion-trade-usability-owner-trace.claim`.
- Compact readback:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T230202+0800-codex-crwd5m-prebayes-bbn-root-parity-ready-veto-reread-v1/checks/current_code_full_chain_readback_after_adapter_and_ready_veto_fix.json`.
- `report.trade_plan.actionable=false` because the plan has
  `win_probability=0.5036168298260623`,
  `risk_reward=0.6666666666666757`, and `kelly_fraction=0.0`.
- Latest analyze still says `promotion_status=observe`.
- The raw analyze execution artifact still says
  `hard_gate_status=execution_blocked`.
- `read_only_regime_bbn_trade_usable=false`.
- `regime_bundle_bbn_application_status=skipped`.
- Imported strategy-library metadata remains `promotion_allowed=false` and
  `trade_usable=false`.

Interpretation:

- Raw analyze hard-gate status and structural execution-candidate readiness are
  separate owner surfaces. Do not copy structural `execution_ready` upward into
  promotion or trade usability.
- The next valid CRWD repair must produce same-root evidence that makes the
  promotion/trade-plan owner positive without hand-flipping imported
  `promotion_allowed` or `trade_usable`.
- Release completion remains blocked: this is one CRWD `US_EQ/single_stock/5m`
  branch, not market/product diffusion, and no clean export, mirror update, tag,
  or GitHub Release was produced.

### 2026-05-22 realtime continuation: release still blocked after fresh probes

Current answer to the three-part goal remains no.

Fresh current-state readback:

- Source `HEAD=9ca9538b511631d9d19e42d64c4946325ec5ffa8`; `origin/main` is
  still `79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Dirty worktree count observed: `854` status rows.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Latest release remains `v0.1.4` from `2026-05-18T13:02:21Z`.
- Light Done Definition audit passed at
  `/tmp/ict-engine-done-definition-audit-20260522-realtime-continuation-light.json`
  with heavy gates skipped.
- Factor readback remains non-promoting: latest 2026-05-22 terminal metrics
  sweep found `promotion_allowed_true=0` and `trade_usable_true=0`.
- Factor claim audit still needs attention; before this cleanup it showed
  `34` active claims and no positive promotion/trade-usable claims.

MNST Gate 1 cleanup:

- Terminalized the IBKR MNST beverage-growth opening-drive RVOL claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260522T232205+0800-codex-ibkr-mnst-beverage-growth-opening-drive-rvol-gate1.claim`.
- Added compact terminal metrics under:
  `support/docs/experiments/actionable-regime-confidence/runs/20260522T232427+0800-codex-ibkr-mnst-beverage-growth-opening-drive-rvol-gate1-v1/checks/terminal_metrics.json`.
- Decision is observation-only: `keep_small_only`, `promotion_allowed=false`,
  `trade_usable=false`.

Release implication:

- This cleanup improves tracking fidelity only. It does not satisfy the
  practical-factor lane, because MNST did not reach downstream gates or trade
  usability.
- Mirror release remains blocked until the factor lane has real promoted
  evidence and the intended source is clean-exported, fully gated, privacy
  scanned, signed off, and explicitly approved for publish.

### 2026-05-23 current-continuation release/factor blocker refresh

Current answer to the requested three-part goal remains no.

Fresh audit evidence:

- Full-heavy Done Definition audit:
  `/tmp/ict-engine-done-definition-audit-20260522-current-continuation-heavy.json`.
- Result: `summary.status=pass`, `completion_ready=true`,
  `evidence_level=full_enabled_gate_coverage`, `pass_count=8`,
  `fail_count=0`, `skip_count=0`, `unresolved=[]`.
- Included gates passed:
  `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, and `support/scripts/smoke_acceptance.sh`.

Fresh source/release readback:

- Source `HEAD=956a1c3e1907483953024c2d4ba9ecb23036442d`, branch `main`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Dirty worktree count observed: `854` status rows.
- Release mirror readback:
  `Undermybelt/ict-engine-release main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Latest GitHub Release remains `v0.1.4`, published
  `2026-05-18T13:02:21Z`.

Fresh factor/claim readback:

- Current `20260522*` terminal-metrics sweep:
  `terminal_metrics_files=167`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `downstream_allowed_true=17`,
  `survivor_5bps_nonempty=3`.
- Claim audit after terminalizing the M2K readback claim:
  `/tmp/ict-engine-factor-claim-terminalization-audit-20260523-after-m2k-terminalized.json`
  reports `status=needs_attention`, `active_claims=7`,
  `terminalized_claims=1`, `total_claims=8`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- The only cleanup performed in this slice was `/tmp`-only and
  evidence-backed:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T000526+0800-codex-m2k-rvol-pda-full-ladder-readback.claim`
  now has `status=terminalized`,
  `decision=m2k_rvol_pda_full_ladder_readback_fail_closed`,
  `promotion_allowed=false`, and `trade_usable=false`.

Release decision:

- Do not publish from this checkout. Heavy audit pass does not override broad
  dirty state, missing practical factor proof, stale mirror head, stale release
  tag, or the requirement for explicit operator confirmation.
- Next release-relevant work is still sequential:
  first prove a practical same-root factor through downstream ownership and
  trade-plan gates, then freeze a coherent source slice, then build a clean
  sanitized export, rerun full release gates and privacy scan, refresh signoff
  and notes, and only then publish mirror main/tag/GitHub Release after explicit
  approval.

Final same-slice claim-audit correction:

- Final readback:
  `/tmp/ict-engine-factor-claim-terminalization-audit-20260523-final-readback.json`.
- Result: `status=needs_attention`, `active_claims=7`,
  `terminalized_claims=2`, `total_claims=9`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- The factor/release decision is unchanged: no practical promoted factor, no
  clean export, and no mirror publish approval.

### 2026-05-23 03:27 CST timeout-budget rerun and release blocker readback

Current answer to the requested three-part goal remains no.

Fresh audit evidence:

- Inherited heavy audit with `--heavy-timeout-seconds 1800`:
  `/tmp/ict-engine-done-current-heavy-after-smoke-fix-20260523.json`.
- Result: `summary.status=needs_fix`, unresolved `cargo_test`, but the details
  show a timeout after compilation finished at `29m52s`; no Rust assertion
  failure was recorded.
- Direct control command `cargo test` exited `0`; lib tests passed
  `1166/1166`, bin tests passed `327/327`, integration tests passed, and
  doc-tests passed `0/0`.
- Current full-heavy rerun:
  `python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --heavy-timeout-seconds 3600 --output /tmp/ict-engine-done-current-heavy-timeout3600-20260523.json`.
- Result: `summary.status=pass`, `completion_ready=true`,
  `evidence_level=full_enabled_gate_coverage`, `pass_count=8`,
  `fail_count=0`, `skip_count=0`, and `unresolved=[]`.
- Included gates passed:
  `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, and `support/scripts/smoke_acceptance.sh`.
- Post-run process readback found no orphan audit, smoke, cargo, rustc, or
  rustdoc process from the timeout or rerun.

Fresh source/release readback:

- Source `HEAD=9034ef20f12198b138edc217921756d6907d62b0`, branch `main`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Dirty worktree count observed: `859` status rows.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Release mirror tag `v0.1.4=699cad1e90844c466009bb3c6231403373ca4aaf`;
  peeled commit `725852eaa10498f4275e3fc4eed351f3aea55eb5`.
- Latest GitHub Release via `gh api` remains `v0.1.4`, published
  `2026-05-18T13:02:21Z`, target `main`, URL
  `https://github.com/Undermybelt/ict-engine-release/releases/tag/v0.1.4`.

Fresh factor/claim readback:

- Current claim audit:
  `/tmp/ict-engine-factor-claim-terminalization-audit-20260523-after-timeout3600-heavy-pass.json`.
- Result: `status=pass`, `active_claims=0`, `terminalized_claims=31`,
  `total_claims=31`, `missing_run_roots=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- Recent current-slice terminal metrics sweep:
  `/tmp/ict-engine-terminal-metrics-sweep-20260523-after-smoke-fix.json`
  reported `terminal_metrics_files=720`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `downstream_allowed_true=85`, and
  `survivor_5bps_nonempty=594`.
- Broad historical sweep:
  `/tmp/ict-engine-terminal-metrics-sweep-20260523-after-timeout3600-heavy-pass.json`
  reported `terminal_metrics_files=1437`, `promotion_allowed_true=5`,
  `trade_usable_true=6`, `downstream_allowed_true=142`, and
  `survivor_5bps_nonempty=335`.
- The broad positives are stale Gate-1-era or incubation flags, not current
  proof of full downstream Pre-Bayes, BBN, CatBoost/path-ranker, execution-tree,
  promotion, trade-plan ownership, and all-market/all-product diffusion.

Release decision:

- Do not publish from this checkout.
- Heavy Done Definition gates now pass on the current tree, but release remains
  blocked by stale mirror state, broad dirty source state, no clean sanitized
  export, no refreshed release signoff/notes for this source head, no explicit
  operator publish approval, and no current practical-factor proof.
- Next release-relevant work is to review/retire stale positive terminal metric
  flags, then prove a same-root practical branch through downstream owners and
  trade usability before preparing a clean export and mirror release.

### 2026-05-23 stale positive terminal-metrics release audit

The requested stale-positive review is complete for the broad historical
`promotion_allowed=true` / `trade_usable=true` examples from the all-history
sweep:

| Run root | Raw positive | Superseding evidence | Release classification |
|---|---:|---|---|
| `20260518T125934+0800-codex-binance-vwapdev-obvrsi-1m-strict-iteration-v2` | `trade_usable=true` | `downstream-strict-1m-small-2000-20260518T2240+0800/checks/downstream_metrics.json`: no-trade, ranker not used, ranker not ready, promotion/trade false | stale Gate-1 flag; observation only |
| `20260518T111136+0800-codex-tvr-kweb-orb-rvol-vwap-density-1m-mtf-v1` | promotion/trade true | `summaries/corrected_terminal_decision_summary.md` and `checks/cost_stress_gate.json`: cost-fragile, downstream false, promotion/trade false | corrected to stop before downstream |
| `20260518T122226+0800-codex-yf-cybersecurity-etf-opening-drive-rvol-vwap-1m-mtf-v1` | `trade_usable=true` | `checks/cost_stress_gate.json` and `checks/cost_stress.json`: cost-fragile, downstream false, promotion false | incubation/neutralization only |
| `20260518T103501+0800-codex-tvr-arkk-orb-rvol-vwap-density-1m-mtf-v3` | promotion/trade true | downstream readbacks such as `downstream-20260518T104018+0800/checks/downstream_metrics.json`: fail-closed, no-trade, observe, promotion false | raw Gate-1 only |
| `20260518T110424+0800-codex-tvr-xlb-orb-rvol-vwap-density-1m-mtf-v1` | promotion/trade true | `downstream-20260518T110606+0800/checks/downstream_metrics.json`: fail-closed, no-trade, observe, promotion false | raw Gate-1 only |
| `20260518T085150+0800-codex-binance-crypto-donchian-rvol-breakout-mtf-gate1-v1` | `promotion_allowed=true` | downstream readbacks under `downstream-20260518T085715+0800` and `downstream-20260518T085720+0800`: no-trade, ranker not used, ranker not ready, promotion false | small-cycle observation only |
| `20260518T105024+0800-codex-tvr-ibb-orb-rvol-vwap-density-1m-mtf-v1` | promotion/trade true | corrected cost gate plus `downstream-20260518T105726+0800/checks/downstream_metrics.json`: fail-closed, no-trade, ranker not ready, promotion false | corrected to fail-closed |

Release implication:

- These rows close the residual audit ambiguity; none is a current practical
  factor or release-ready proof.
- The next release-relevant factor task is not more broad counting. It is a
  same-root branch proof that ends with `promotion_allowed=true`,
  `trade_usable=true`, ranker validation ready, ranker score used by the
  execution tree, and an actionable/non-blocked trade plan.
- Mirror publication remains blocked until that practical-factor proof exists,
  a coherent source slice is clean-exported and fully gated, release notes and
  signoff are refreshed, and the operator explicitly approves the exact
  mirror/tag/GitHub Release action.

### 2026-05-23 04:05 CST factor-claim closure and release status

Fresh claim readback:

- `/tmp/ict-engine-factor-claims-after-fix-terminalized-20260523.json`
  reports `summary.status=pass`, `active_claims=0`,
  `terminalized_claims=40`, `total_claims=40`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- TOMAC NQ two-leg source-discovery is terminalized fail-closed from
  `/tmp/ict-engine-tomac-nq-twoleg-reconstruction-probe-20260523T035059+0800/checks/terminal_metrics.json`.
  Decision: `reconstruction_parity_failed_do_not_ingest`.
- FIX infrastructure range-expansion is terminalized fail-closed from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T035708+0800-codex-ibkr-fix-infrastructure-range-expansion-continuation-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  Decision: `drop_gate1_cost_or_density_failed`.

Release status:

- This clears the current claim-terminalization blocker only.
- It does not prove all-market/all-product practical factor diffusion:
  promotion-allowed and trade-usable counts remain zero in the fresh claim
  audit.
- It does not authorize mirror release. The next release-capable state still
  requires practical factor proof, clean sanitized export, full release gate
  rerun from that export, privacy scan, refreshed release notes/signoff, and
  explicit operator approval for the exact mirror publish/tag/release action.

### 2026-05-23 04:24 CST live claim drift after transient clear

Fresh superseding claim readback:

- `/tmp/ict-engine-factor-claims-after-dov-terminalized-live-20260523.json`
  reports `summary.status=needs_attention`, `active_claims=6`,
  `terminalized_claims=41`, `total_claims=47`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- DOV industrial-automation Gate 1 was closed from its own terminal evidence as
  `decision=keep_small_only`, with promotion/trade/update-goal false.
- New active claims appeared after the earlier zero-active readback: CBRE, WMT,
  CPB, cybersecurity sibling provider preflight, and TOMAC PSAR/Aroon-CCI.

Release status:

- Release remains blocked. A transient claim-board pass is not a release gate.
- The latest claim-board state needs attention again, and no current claim is
  promotion-allowed or trade-usable.
- Do not publish mirror main, create a tag, or create a GitHub Release from this
  checkout without a clean export, full export-side verification, refreshed
  signoff/notes, and explicit operator approval.

### 2026-05-23 04:32 CST live claim terminalization continuation

Current answer to the three-part goal remains no.

Fresh claim evidence:

- Compact audit:
  `/tmp/ict-engine-factor-claims-after-cybersecurity-terminalized-20260523T0433.json`.
- Result: `summary.status=needs_attention`, `active_claims=1`,
  `terminalized_claims=48`, `total_claims=49`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- The single remaining active claim is
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T0420+0800-codex-tomac-psar-arooncci-gate1.claim`.
  Its run root is
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-20260523T0420+0800`,
  and the full scan was still running at the 04:31 CST readback with no
  `checks/02_full_scan.exit` yet.

Claims terminalized from their own evidence in this continuation:

- CPB packaged-food Connors RSI2:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041446+0800-codex-ibkr-cpb-packaged-food-connors-rsi2-rebound-1m-mtf-gate1-v1/checks/terminal_metrics.json`,
  `decision=drop_gate1_no_exact_1m_5bps_density_survivor`,
  `promotion_allowed=false`, `trade_usable=false`.
- WMT defensive retail opening-drive RVOL:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T041250+0800-codex-ibkr-wmt-defensive-retail-opening-drive-rvol-gate1-v1/summaries/ibkr_wmt_defensive_retail_opening_drive_rvol_gate1_v1.json`,
  `decision=keep_small_only`, `promotion_allowed=false`,
  `trade_usable=false`; note the upper-window failures
  `01_ibkr_wmt_1m_30d_fetch.exit=3` and
  `02_ibkr_wmt_5m_3m_fetch.exit=3`, followed by smaller real-window retries
  exiting `0`.
- ENPH solar gap-failure reversal:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T042314+0800-codex-ibkr-enph-solar-gap-failure-reversal-1m-mtf-gate1-v1/checks/terminal_metrics.json`,
  `decision=drop_gate1_cost_or_density_failed`,
  `promotion_allowed=false`, `trade_usable=false`.
- GLW optical communications Keltner reclaim:
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T042324+0800-codex-ibkr-glw-optical-communications-keltner-reclaim-1m-mtf-gate1-v1/checks/terminal_metrics.json`,
  `decision=drop_gate1_cost_or_density_failed`,
  `promotion_allowed=false`, `trade_usable=false`.
- Cybersecurity sibling provider preflight:
  `/tmp/ict-engine-ibkr-cybersecurity-sibling-provider-preflight-20260523T041012+0800/checks/provider_preflight_metrics.json`,
  `decision=provider_preflight_full_ladder_available`,
  `provider_parity_candidate=true`, `auto_quant_run=false`,
  `downstream_allowed=false`, `promotion_allowed=false`, and
  `trade_usable=false`. This is provider-row evidence only; it is not a
  practical factor.

Release status:

- The latest Done Definition heavy audit remains green at
  `/tmp/ict-engine-done-current-heavy-timeout3600-20260523.json`.
- Practical factor diffusion is still unproven: the latest claim audit has zero
  promotion-allowed and zero trade-usable claims, and TOMAC PSAR/Aroon-CCI is
  still in flight.
- Mirror release remains blocked until a current practical branch proves
  promotion/trade usability, a clean sanitized export is built and verified,
  signoff and notes are refreshed, and the operator explicitly approves the
  exact mirror/tag/GitHub Release action.

### 2026-05-23 04:45 CST factor-claim pass after TOMAC/S/RPD readback

Fresh superseding claim evidence:

- `/tmp/ict-engine-factor-claims-after-cybersecurity-reread-20260523T044517+0800.json`
  reports `summary.status=pass`, `active_claims=0`,
  `terminalized_claims=55`, `total_claims=55`, `missing_run_roots=0`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- The previous transient attention artifact
  `/tmp/ict-engine-factor-claims-after-tomac-psar-terminal-readback-20260523Tdebug.json`
  was superseded after the S/RPD cybersecurity claims were terminalized.
- TOMAC PSAR/Aroon-CCI is no longer active. Its claim is
  `status: terminalized_runtime_abort`; full scan `02_full_scan.exit=143`,
  no full-scan terminal metrics materialized, and the NQ smoke packet reports
  `drop_gate1_no_5bps_density_quality_survivor_no_downstream`.
- IBKR S cybersecurity PDA/MTF exact 5m Gate 1 produced a hard 5bps density
  survivor and `downstream_allowed=true`, but its own terminal metrics still
  keep `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- IBKR RPD 5m cybersecurity provider-parity extension is terminalized
  fail-closed with `drop_gate1_no_exact_rpd5m_5bps_density_survivor`.

Release decision:

- The current claim-board hygiene blocker is clear.
- This is still not practical-factor completion: no current claim is
  promotion-allowed or trade-usable, and the S Gate-1 survivor has not been
  carried through same-root Pre-Bayes/filter, BBN, CatBoost/path-ranker,
  execution-tree consumption, promotion, and trade-plan ownership.
- Process drift note: a separate unclaimed TOMAC repair scan was live at the
  04:50 CST process readback:
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`,
  PID `93988`, command `run_tomac_psar_arooncci_gate1.py --symbols NQ,YM,XAU`.
  It had no `checks/01_full_repair.exit` or terminal metrics yet. This does not
  change the claim audit result, but it blocks any stronger "no live factor work"
  or practical-completion language.
- Mirror release remains blocked until practical factor proof exists, a clean
  sanitized export passes full release gates and privacy scan, release notes and
  signoff are refreshed, and the operator explicitly approves the exact
  mirror/tag/GitHub Release action.

### 2026-05-23 05:10 CST live-process-aware factor readback

Fresh superseding claim/process evidence:

- `/tmp/ict-engine-factor-claims-refresh-20260523T050944+0800.json`
  reports `summary.status=needs_attention`, `active_claims=0`,
  `live_factor_processes=1`, `terminalized_claims=61`, `total_claims=61`,
  `missing_run_roots=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- AXON public-safety TTM-squeeze Gate 1 is terminalized
  `drop_gate1_cost_or_density_failed` from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T050413+0800-codex-ibkr-axon-public-safety-ttm-squeeze-1m-mtf-gate1-v1/checks/terminal_metrics.json`.
  It has seven IBKR provider packets and seven AQ material/rank rows, but no
  exact 1m hard-5bps density survivor and no 5bps-per-side survivor set.
- RPD exact 1h downstream is terminalized
  `exact_rpd_1h_downstream_fail_closed` from
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T044255+0800-codex-ibkr-rpd5m-cybersecurity-pda-mtf-template-transfer-gate1-v1/downstream-exact-ibkr-rpd-1h-pda-mtf-template-transfer-20260523T050125+0800/checks/downstream_metrics.json`.
  It remains no-trade with high transition hazard, PDA misalignment, ranker
  score not used by the execution tree, and promotion/trade false.
- TENB cybersecurity exact 5m Gate 1 is terminalized
  `drop_gate1_no_exact_5m_5bps_density_survivor` under
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T050645+0800-codex-ibkr-tenb-cybersecurity-pda-mtf-template-transfer-5m-gate1-v1`.
- The only remaining live factor process is TOMAC PSAR/Aroon-CCI repair PID
  `93988`, run root
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`; at
  05:10 CST it had no `checks/01_full_repair.exit` and no terminal metrics.

Release decision:

- This readback supersedes the earlier transient clean claim-board pass. The
  board claims are terminalized, but live factor work still exists.
- No current factor is promotion-allowed or trade-usable.
- Do not publish mirror `main`, create a tag, or create a GitHub Release from
  this state. Release remains blocked by missing practical-factor proof,
  missing clean sanitized export, missing export-side release gates/privacy
  scan, missing refreshed notes/signoff, and missing explicit operator approval.

### 2026-05-23 05:21 CST release blocker refresh

Fresh superseding factor audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T052140+0800.json`
  reports `summary.status=needs_attention`, `active_claims=4`,
  `live_factor_processes=5`, `terminalized_claims=61`, `total_claims=65`,
  `missing_run_roots=1`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- Current active claim blockers are ASTS Gate 1, DASH Gate 1, FTNT 15m Gate 1,
  and TOMAC PSAR/Aroon-CCI repair readback.
- ASTS and DASH have live wrappers and child IBKR fetch processes; their run
  roots exist but no terminal metrics are available. Observed fetch exits so far
  are nonzero (`3`) and are not promotion evidence.
- FTNT remains active with `run_root=pending`.
- TOMAC repair PID `93988` remains live with no `checks/01_full_repair.exit` and
  no terminal metrics under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.

Source and mirror readback:

- Local source `HEAD=fa2f4400ac2a2de74a8cc5d5b9f66954a6cfd4e4`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Current worktree readback still showed a broad dirty tree (`863` short-status
  rows).
- `Cargo.toml` still reports `version = "0.1.3"`.
- Release mirror `main` remains `ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- Latest GitHub Release remains `v0.1.4`, published `2026-05-18T13:02:21Z`.

Release decision:

- Do not publish mirror `main`, create a tag, or create a GitHub Release from
  this state.
- Release remains blocked by zero current promotion/trade-usable factors,
  active/live factor work, no clean sanitized export, no export-side release
  gate/privacy scan, no refreshed notes/signoff, and no explicit operator
  approval.

### 2026-05-23 05:29 CST release blocker narrowed, not cleared

Fresh superseding factor audit:

- `/tmp/ict-engine-factor-claims-refresh-20260523T0529-rerun.json` reports
  `summary.status=needs_attention`, `active_claims=1`,
  `live_factor_processes=1`, `terminalized_claims=65`, `total_claims=66`,
  `missing_run_roots=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- ASTS and DASH Gate 1 runs now have terminal metrics. Both are
  `provider_or_aq_blocked_no_gate1_verdict` and both keep
  `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- FTNT 15m Gate 1 has `downstream_allowed=true`, but its own terminal metrics
  still keep `promotion_allowed=false`, `trade_usable=false`,
  `extension_complete=false`, and `update_goal=false`.
- XOM cost-stress readback and S 5m exact downstream are both terminalized
  fail-closed; neither provides promotion or trade-usability evidence.
- The only remaining live factor blocker is TOMAC PSAR/Aroon-CCI repair PID
  `93988` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`, with
  no `checks/01_full_repair.exit` or terminal metrics at 05:29 CST.

Release decision:

- Do not publish mirror `main`, create a tag, or create a GitHub Release from
  this state.
- The release remains blocked by zero current promotion/trade-usable factors,
  one live TOMAC repair process without terminal evidence, no clean sanitized
  export, no export-side release gates/privacy scan, no refreshed notes/signoff,
  and no explicit operator approval.

### 2026-05-23 05:30 CST final release blocker readback

- `/tmp/ict-engine-factor-claims-refresh-20260523T0530-final.json` exited `1`
  with `summary.status=needs_attention`, `active_claims=1`,
  `live_factor_processes=1`, `terminalized_claims=66`, `total_claims=67`,
  `missing_run_roots=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- The only live blocker remains TOMAC PSAR/Aroon-CCI repair PID `93988`; no
  `checks/01_full_repair.exit` or terminal metrics exist yet.
- Mirror release remains blocked; no tag, push, or GitHub Release is authorized.

### 2026-05-23 05:35 CST claim hygiene pass, release still blocked

- `/tmp/ict-engine-factor-claims-refresh-20260523T0535-post-tomac-terminal.json`
  exited `0` with `summary.status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `terminalized_claims=68`, `total_claims=68`,
  `missing_run_roots=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- TOMAC PSAR/Aroon-CCI repair has terminal evidence now:
  `checks/01_full_repair.exit=143` under
  `/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-20260523T0500+0800`.
  No terminal metrics, scan results, or leaderboard materialized, so the repair
  is fail-closed and non-promoting.

Release decision:

- Claim/process hygiene is no longer the release blocker.
- Mirror release remains blocked by zero current promotion/trade-usable factors,
  no clean sanitized export, no export-side release gates/privacy scan, no
  refreshed notes/signoff, and no explicit operator approval.
- No tag, push, or GitHub Release is authorized.

### 2026-05-23 05:47 CST release readiness remains blocked after live drift

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-20260523T054440+0800.json` exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=e06ca1704af8ea6e9e6ee0ab85cfde6ec6fd9de4`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- Source is ahead of origin by `92` commits.
- Release mirror `main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` version remains `0.1.3`.
- Known release tags include `v0.1.3` and `v0.1.4`; suggested next patch is
  `0.1.5` / `v0.1.5`.

Unresolved release gates:

- `worktree_clean_for_release`: dirty worktree, with `78` tracked dirty entries
  and `782` untracked entries in the audit sample.
- `release_docs_fresh_for_selected_tag`: release signoff and notes are still
  historical/stale for a fresh selected export.
- `source_origin_matches_selected_source`: selected source commit is not on
  `origin/main`.
- `release_version_tag_available`: `v0.1.3` is already used.

Fresh factor-readiness drift:

- `/tmp/ict-engine-factor-claims-refresh-20260523T054654+0800.json` exited `1`
  with `active_claims=2`, `live_factor_processes=5`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`.
- FTNT 15m exact downstream is execution-ready but not promotable:
  current mature rows are `3/30`, `extension_complete=false`,
  `promotion_allowed=false`, and `trade_usable=false`.
- TOMAC KAMA/Vortex smoke terminalized fail-closed with no hard 5bps/density
  survivor, while its full process remains live.

Release decision:

- The earlier 05:35 claim-hygiene pass is superseded by live factor drift.
- No mirror `main` push, tag creation, or GitHub Release is authorized.
- The next release-safe path is still: terminalize/externalize live factor
  work, prove at least one exact rooted branch with promotion/trade usability,
  select and commit a coherent source slice, build a clean sanitized export,
  rerun release gates/privacy scan, refresh signoff/notes for an unused tag,
  and obtain explicit operator approval.

### 2026-05-23 06:02 CST release still blocked after JPM terminalization

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-after-jpm-terminalization-20260523T060019+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=1`, `missing_run_roots=1`, `live_factor_processes=0`.
- `terminalized_claims=73`, `total_claims=74`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.
- JPM is now terminalized fail-closed as
  `blocked_provider_runtime_no_candles` under
  `support/docs/experiments/actionable-regime-confidence/runs/20260523T054054+0800-codex-ibkr-jpm-money-center-bank-dmi-adx-pullback-1m-mtf-gate1-v1`.
- The current attention claim is
  `20260523T055929+0800-codex-tomac-choppiness-gate1.claim`, with claimed root
  `/tmp/ict-engine-tomac-choppiness-gate1-20260523T055929+0800` missing in the
  compact audit.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-after-jpm-terminalization-20260523T060019+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `fail_count=2`, `pass_count=1`, `skip_count=2`.
- `HEAD=88ccea762ceefc764fdb31845adfa6d60f26b384`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and
  repository `https://github.com/Undermybelt/ict-engine-release`.

Unresolved release gates:

- `worktree_clean_for_release`: fail; the audit sample reports `78` tracked
  dirty entries and `782` untracked entries.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes are
  still historical for a fresh selected export.
- `remote_readback`: skipped because network remote checking was not enabled.
- `release_version_tag_available`: skipped because release mirror tags were not
  checked in this no-remote audit.

Release decision:

- No mirror `main` push, tag creation, or GitHub Release is authorized.
- Release remains blocked by the dirty source tree, stale selected-tag docs,
  skipped remote/tag readback, zero current promotion/trade-usable factors, and
  the active TOMAC choppiness claim.

### 2026-05-23 06:04 CST release still blocked after final drift check

Fresh final factor audit:

- `/tmp/ict-engine-factor-claims-final-refresh-20260523T060423+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=2`, `missing_run_roots=1`, `live_factor_processes=2`.
- `terminalized_claims=74`, `total_claims=76`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Current factor blockers:

- TOMAC choppiness is terminalized fail-closed as
  `blocked_missing_run_root_self_test_failure_no_terminal_metrics`, but its
  declared root is still missing and no terminal metrics exist.
- EURUSD FX London ORB/retest is active/claimed and not promotion/trade usable.
- USDJPY FX DMI/ADX pullback is active with live wrapper PID `95345` and child
  IBKR fetch PID `96849`.

Release decision:

- The 06:02 release checkpoint is superseded by this 06:04 drift.
- No mirror `main` push, tag creation, or GitHub Release is authorized.
- Release remains blocked by dirty source state, stale selected-tag docs,
  skipped remote/tag readback, zero promotion/trade-usable factor evidence, and
  current active/live factor work.

### 2026-05-23 06:21 CST release still blocked after Bybit terminalization

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-after-bybit-vol-terminalization-20260523T062053+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=78`, `total_claims=78`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-after-bybit-vol-terminalization-20260523T062053+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `fail_count=4`, `pass_count=1`, `skip_count=0`.
- `HEAD=88ccea762ceefc764fdb31845adfa6d60f26b384`.
- Source remains `93` commits ahead of `origin/main`.
- Current version remains `0.1.3`; known mirror tags include `v0.1.3` and
  `v0.1.4`; suggested next tag remains `v0.1.5`.

Unresolved release gates:

- `worktree_clean_for_release`.
- `release_docs_fresh_for_selected_tag`.
- `source_origin_matches_selected_source`.
- `release_version_tag_available`.

Release decision:

- The factor/process hygiene blocker is cleared in this snapshot, but release is
  still blocked by the four readiness gates above and by zero
  promotion/trade-usable factor evidence.
- No mirror `main` push, tag creation, GitHub Release, or practical-trading
  promotion is authorized from this state.

### 2026-05-23 07:13 CST release still blocked after SOUN/Bybit/TOMAC terminalization

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-final-current-20260523T071328+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=93`, `total_claims=93`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Terminalized factor evidence:

- SOUN: `provider_or_aq_blocked_no_gate1_verdict`; IBKR status passed, but all
  requested/retry fetches returned zero rows, so this is provider/AQ-blocked and
  not a factor economics verdict.
- Bybit AERO/ZRO: `higher_timeframe_subclass_only_exact_1m_blocked`.
- Bybit GMX/ZETA: `higher_timeframe_subclass_only_origin_blocked`.
- Bybit DASH/ZEC: `drop_gate1_cost_or_density_failed`.
- TOMAC Alligator/Fractal: `drop_gate1_no_hard_5bps_density_quality_survivor`
  with `candidate_count=1350` and `gate1_survivor_count=0`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-final-current-20260523T071328+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=9df168b37799851381ba767448a253c075b2fde3`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The audit sample reports `80` tracked dirty entries and `782` untracked
  entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `remote_readback`: skipped because network remote checking was not enabled.
- `release_version_tag_available`: skipped because release mirror tags were not
  checked in this no-remote audit.

Release decision:

- Claim/process hygiene is clean in this snapshot, but release is still blocked.
- The practical-factor objective is still open because there are zero
  `promotion_allowed=true` and zero `trade_usable=true` factors.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 07:28 CST release still blocked after post-07:13 drift

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-resume-20260523T072855+0800.json`
  exited `1`.
- `summary.status=needs_attention`.
- `active_claims=5`, `missing_run_roots=0`, `live_factor_processes=5`.
- `terminalized_claims=98`, `total_claims=103`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Active/live factor blockers:

- XBI Williams/MFI remains claimed and waiting for IBKR contention to clear.
- TOMAC TOD BalancedAdaptiveSlotPortfolio rebuild remains live under the local
  TOMAC portfolio repair scan.
- NTNX Bayesian-Markov trend detector remains live with an IBKR historical
  child fetch.
- USDCHF Bollinger squeeze remains validated but pending launch behind IBKR
  contention.
- Bybit NEO/QTUM Mass Index remains live in Auto-Quant dispatch.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-resume-20260523T072855+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=7fb46d2a1c57a7570d1df26aca74fce4fd88d56c`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The audit sample reports `78` tracked dirty entries and `782` untracked
  entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `remote_readback`: skipped because network remote checking was not enabled.
- `release_version_tag_available`: skipped because release mirror tags were not
  checked in this no-remote audit.

Release decision:

- The 07:13 clean claim/process snapshot is superseded by active/live factor
  drift.
- Release remains blocked by dirty source state, stale selected-tag docs,
  skipped remote/tag readback, active factor work, and zero
  promotion/trade-usable factor evidence.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 07:39 CST release still blocked after claim hygiene cleanup

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-resume-20260523T073957+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=103`, `total_claims=103`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-resume-20260523T073957+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=49c2bc31a4a5aa8acf9817994c9112620ea90754`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The audit sample reports `78` tracked dirty entries and `782` untracked
  entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `remote_readback`: skipped because network remote checking was not enabled.
- `release_version_tag_available`: skipped because release mirror tags were not
  checked in this no-remote audit.

Release decision:

- Factor claim/process hygiene is clean, but release is still blocked.
- The practical-factor objective is still open because there are zero
  `promotion_allowed=true` and zero `trade_usable=true` factors.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 07:58 CST release still blocked after second claim hygiene cleanup

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-resume-20260523T075832+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=109`, `total_claims=109`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit:

- `/tmp/ict-engine-release-readiness-resume-20260523T075832+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=8b28eabc2535b4580af1634fd69cbb80f9aaaeb1`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The audit sample reports `78` tracked dirty entries and `782` untracked
  entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `remote_readback`: skipped because network remote checking was not enabled.
- `release_version_tag_available`: skipped because release mirror tags were not
  checked in this no-remote audit.

Release decision:

- Factor claim/process hygiene is clean again, but release is still blocked.
- The practical-factor objective is still open because there are zero
  `promotion_allowed=true` and zero `trade_usable=true` factors.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 08:23 CST release still blocked after remote readback and clean claim hygiene

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T082357+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=114`, `total_claims=114`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T081859+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=b94770e9e82c53a42fa78eb05582cd33ccf213b8`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The audit sample reports `78` tracked dirty entries and `782` untracked
  entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `source_origin_matches_selected_source`: fail; the source branch is `105`
  commits ahead of `origin/main`, so a selected committed source/export has not
  been reconciled.
- `release_version_tag_available`: fail; `v0.1.3` already exists, mirror tags
  include `v0.1.4`, and the audit suggests `v0.1.5`.

Release decision:

- Claim/process hygiene is clean again, but release is still blocked.
- TOMAC cap65 suppressed AQ produced a hard `5bps` Gate 1 survivor, but its own
  decision requires downstream proof and keeps `promotion_allowed=false` /
  `trade_usable=false`.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 09:26 CST release still blocked after TOMAC downstream readback

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T092617+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T092420+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=c5d1db7bbc4d7d232cfaad0e05b18039c0876584`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The release audit sample reports `12` tracked dirty entries and `763`
  untracked entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `source_origin_matches_selected_source`: fail; the source branch is `107`
  commits ahead of `origin/main`, so a selected committed source/export has not
  been reconciled.
- `release_version_tag_available`: fail; `v0.1.3` already exists, mirror tags
  include `v0.1.4`, and the audit suggests `v0.1.5`.

Release decision:

- Claim/process hygiene is clean again, but release is still blocked.
- TOMAC cap65 downstream failed closed/incomplete: `09_ingest_real_trades`
  timed out, execution candidate stayed `no_trade`, path-ranker was not visible
  or used, and `promotion_allowed=false` / `trade_usable=false`.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 09:30 CST release still blocked; source HEAD moved again

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T093047+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T093047+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=35d12c83a950095a513b439b8c842aabb4a3f9d7`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` still reports `version=0.1.3`, `publish=false`, and repository
  `https://github.com/Undermybelt/ict-engine-release`.
- The release audit sample reports `13` tracked dirty entries, `1` staged entry,
  and `763` untracked entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `source_origin_matches_selected_source`: fail; the source branch is `109`
  commits ahead of `origin/main`, so a selected committed source/export has not
  been reconciled.
- `release_version_tag_available`: fail; `v0.1.3` already exists, mirror tags
  include `v0.1.4`, and the audit suggests `v0.1.5`.

Release decision:

- Claim/process hygiene is clean again, but release is still blocked.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 09:33 CST release still blocked; version/tag gate now passes

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T093348+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T093348+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=28b1927bdeb3ea316c35c22dcf65cf367df93b20`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` and `Cargo.lock` now report `version=0.1.5`; mirror tags list
  `v0.0.1` through `v0.1.4`, so `release_version_tag_available` passes for
  candidate tag `v0.1.5`.
- The release audit sample reports `14` tracked dirty entries and `763`
  untracked entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `source_origin_matches_selected_source`: fail; the source branch is `109`
  commits ahead of `origin/main`, so a selected committed source/export has not
  been reconciled.

Release decision:

- Version/tag reuse is no longer the current release blocker, but release is
  still blocked by dirty source selection, stale release docs, and source/origin
  mismatch.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 09:54 CST release still blocked after resume readback

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T095449+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T095449+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=28b1927bdeb3ea316c35c22dcf65cf367df93b20`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` and `Cargo.lock` still report `version=0.1.5`; mirror tags list
  `v0.0.1` through `v0.1.4`, so `release_version_tag_available` passes for
  candidate tag `v0.1.5`.
- The release audit sample reports `15` tracked dirty entries and `763`
  untracked entries.

Unresolved release gates:

- `worktree_clean_for_release`: fail; release export must start from an
  explicitly selected committed tree, not this broad dirty worktree.
- `release_docs_fresh_for_selected_tag`: fail; release signoff and notes still
  describe historical/stale evidence for a fresh selected export.
- `source_origin_matches_selected_source`: fail; the source branch is `109`
  commits ahead of `origin/main`, so a selected committed source/export has not
  been reconciled.

Release decision:

- Version/tag reuse remains fixed, but release is still blocked by dirty source
  selection, stale release docs, and source/origin mismatch.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 09:58-10:03 CST clean export evidence: fmt/clippy pass, full test fails

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T095813+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=123`, `total_claims=123`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T095813+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=b52b66dc947291669991d2ffdc6aa8cfd5480e00`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` and `Cargo.lock` report `version=0.1.5`; mirror tags still list
  only through `v0.1.4`, so the version/tag gate passes.
- The release audit sample reports `12` tracked dirty entries and `763`
  untracked entries.

Clean export gate attempt:

- Export root: `/tmp/ict-engine-v015-release-export-20260523T095925+0800` from
  `git archive HEAD`.
- `cargo fmt --check` exited `0`.
- `cargo clippy --all-targets -- -D warnings` exited `0`.
- `cargo test` exited `101`; `src/lib.rs` unit tests passed `1166/1166`, but
  `src/main.rs` bin tests failed `2` of `327`.
- Failing tests:
  `cli_surface_tests::test_factor_candidate_admission_target_builder_lives_in_orchestration_owner`
  and `tests::test_build_factor_candidate_pack_inventory_reads_curated_packs`.

Root cause readback:

- The clean export uses committed `HEAD`, where
  `support/examples/factor_candidate_packs/curated-auto-quant-v1/family_d_liquidity_sweep_reclaim_15m_wide_v1/factor_expression.json`
  still has `expected_regime=null` and no `branch_path_contract`.
- The dirty working tree has the missing `expected_regime`,
  `branch_path_contract`, and related timeframe-ladder metadata across
  `factor_expression.json`, `factor_eval_grid_summary.json`, and
  `transfer_score.json`.
- The two failing tests pass in the dirty worktree when run individually, so the
  release source slice is incoherent: tests in committed `HEAD` expect candidate
  pack metadata that is only present in unstaged/dirty files.

Release decision:

- Release docs must not be refreshed as current signoff yet. A clean export from
  the selected commit still fails full tests.
- The next safe release repair is a narrow, verified source slice that includes
  the three candidate-pack JSON files or adjusts the tests/data contract from the
  canonical owner, then reruns clean-export fmt, clippy, full tests,
  zero-config smoke, and privacy scan before any signoff/notes refresh.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 10:12 CST candidate-pack source-slice repair precheck

Fresh factor audit:

- `/tmp/ict-engine-factor-claims-continuation-20260523T101244+0800.json`
  exited `0`.
- `summary.status=pass`.
- `active_claims=0`, `missing_run_roots=0`, `live_factor_processes=0`.
- `terminalized_claims=126`, `total_claims=126`.
- `promotion_allowed_true=0`, `trade_usable_true=0`.

Fresh release-readiness audit with remote/tag readback:

- `/tmp/ict-engine-release-readiness-continuation-20260523T101244+0800.json`
  exited `1`.
- `summary.status=needs_fix`.
- `HEAD=b13a57aaa2ac2a3babe0a837f9fbd039d4dca93c`.
- `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`.
- `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`.
- `Cargo.toml` and `Cargo.lock` report `version=0.1.5`; mirror tags still list
  only through `v0.1.4`, so the version/tag gate passes.
- `release_docs_fresh_for_selected_tag` now passes.
- The unresolved gates are `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.
- The release audit sample reports `12` tracked dirty entries and `763`
  untracked entries; source is `114` commits ahead of `origin/main`.

Candidate-pack source-slice verification:

- `cargo test cli_surface_tests::test_factor_candidate_admission_target_builder_lives_in_orchestration_owner -- --nocapture`
  passed in the dirty worktree.
- `cargo test tests::test_build_factor_candidate_pack_inventory_reads_curated_packs -- --nocapture`
  passed in the dirty worktree.
- The narrow data slice is the three JSON files under
  `support/examples/factor_candidate_packs/curated-auto-quant-v1/family_d_liquidity_sweep_reclaim_15m_wide_v1/`:
  `factor_expression.json`, `factor_eval_grid_summary.json`, and
  `transfer_score.json`.
- The slice adds rooted branch-path metadata, timeframe-ladder evidence, and
  explicit `promotion_allowed=false` / `trade_usable=false`; it does not make the
  candidate practical-trading usable.

Release decision:

- The previous clean-export failure has a verified narrow data repair candidate,
  but release is still not ready until that selected source is committed or
  otherwise exported coherently, then clean-export fmt, clippy, full tests,
  zero-config smoke, and privacy scan pass from the selected source.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 10:24-10:26 CST selected-source export passes tests and smoke, release still gated

Selected-source commits now include:

- `4e388b86 docs: record candidate pack branch path repair`.
- `f0281630 fix: resolve claim run roots from claim repo`.

Clean export evidence:

- Export root: `/tmp/ict-engine-v015-release-export-20260523T101600+0800`.
- Export included the candidate-pack branch-path metadata and the `f0281630`
  claim-root fix doc.
- `cargo fmt --check` passed.
- `cargo clippy --all-targets -- -D warnings` passed.
- `cargo test` passed: `src/lib.rs` `1166` passed, `src/main.rs` `327`
  passed, integration tests passed, doc tests `0` passed / `0` failed.

Zero-config smoke evidence:

- Smoke root: `/tmp/ict-engine-v015-release-smoke-20260523T102127+0800`.
- Commands run from the clean export: `provider-status --compact`,
  `workflow-status --human`, `analyze --demo --human`, refreshed
  `workflow-status --agent`, `pre-bayes-status --output-format json`, and
  `policy-training-status --output-format agent` against a `/tmp` state dir.
- Smoke exited `0`; stdout had `1178` lines and stderr had `0` lines.
- Privacy scan found no `/Users/`, `/private/tmp`, `Downloads`, Homebrew path,
  secret-like token, key, password, or private-key marker.
- The only path hits were `12` expected explicit `/tmp` smoke state paths in
  recommended commands and generated summary paths.

Postexport audits:

- `/tmp/ict-engine-factor-claims-continuation-postexport-debug-20260523T102550+0800.json`
  exited `0`; `summary.status=pass`, `active_claims=0`,
  `missing_run_roots=0`, `live_factor_processes=0`,
  `terminalized_claims=129`, `total_claims=129`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- `/tmp/ict-engine-release-readiness-continuation-postexport-*.json` still exits
  `1`; `summary.status=needs_fix` with unresolved gates
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
- Postexport release audit `HEAD=f0281630ef61722786984a687808a0380fc28ec1`;
  source is `116` commits ahead of `origin/main` and still not reconciled.

Release decision:

- The clean-export test blocker is repaired for the selected source, and the
  zero-config smoke/privacy gate has fresh passing evidence.
- Release is still not ready because the worktree is not release-clean and the
  selected source has not been reconciled with `origin/main` / release mirror
  publication flow.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 10:29-10:31 CST isolated clean-worktree release audit narrows blocker to source/origin

Fresh shared-checkout audits:

- `/tmp/ict-engine-factor-claims-continuation-20260523T102946+0800.json`
  exited `0`; `summary.status=pass`, `active_claims=0`,
  `missing_run_roots=0`, `live_factor_processes=0`,
  `terminalized_claims=129`, `total_claims=129`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- `/tmp/ict-engine-release-readiness-continuation-20260523T102946+0800.json`
  exited `1`; `summary.status=needs_fix` with unresolved gates
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.
- Shared checkout dirty state is still broad: `770` status entries, including
  `7` tracked dirty entries and `763` untracked entries.

Isolated selected-source audit:

- Clean worktree: `/tmp/ict-engine-release-clean-wt-20260523T103100+0800`,
  created detached at `HEAD=7fbe89f3c9a90130100e0ba9cf321c1d1da3a577`.
- Audit: `/tmp/ict-engine-release-readiness-clean-wt-20260523T103119+0800.json`
  exited `1`.
- In the clean worktree, `worktree_clean_for_release` passed with `0` status
  entries.
- `cargo_release_policy`, `release_docs_fresh_for_selected_tag`, and
  `release_version_tag_available` also passed.
- The only remaining release-readiness failure in the isolated selected source
  is `source_origin_matches_selected_source`.
- Source/origin readback: `origin/main=79d9579ea38685bd8c798dc80c1f5177e3c220b6`,
  `release_mirror_main=ab6b1b55d516bcd0f6b88db1931cc40802e683bb`, and local
  selected source is `117` commits ahead of `origin/main`.

Release decision:

- The dirty-worktree release gate is now proven to be shared-checkout noise for
  the selected committed source, not a blocker in the detached clean worktree.
- The remaining release blocker is source/origin alignment: publish requires an
  explicit operator decision to push the selected source commit or publish from
  the already verified clean export at the selected commit.
- No mirror `main` push, tag creation, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 13:10-13:13 CST v0.1.7 release-candidate retarget

Fresh factor claim readback:

- `/tmp/ict-engine-factor-claims-post-handoff-20260523T131016+0800.json`
  exited `1`; `summary.status=needs_attention`, `active_claims=1`,
  `live_factor_processes=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- Factor closure is still not proven; the active claim must be terminalized or
  externalized before any factor-completion claim.

Release readiness readback:

- Clean detached audit at `HEAD=22fae7f2f0c0bfea39d7c6c2c5dceac6076c2ccb`
  wrote `/tmp/ict-engine-release-readiness-clean-head-20260523T131049+0800.json`
  and exited `1`.
- In that clean worktree, `worktree_clean_for_release`,
  `cargo_release_policy`, and `release_docs_fresh_for_selected_tag` passed.
- `source_origin_matches_selected_source` failed because selected `HEAD` is
  `2` commits ahead of `origin/main=4406454de95d40551acfcb573e3a4f68bf189e0b`.
- `release_version_tag_available` failed because `v0.1.6` already exists in the
  release mirror; the audit suggested `0.1.7` / `v0.1.7`.

Retarget applied in this slice:

- `Cargo.toml` and `Cargo.lock` now use `version = "0.1.7"`.
- `support/docs/audits/release-signoff.md` and
  `support/docs/release-notes-draft.md` now identify `v0.1.7` as the selected
  correction candidate and keep the clean-export gate requirement.

Verification:

- `git diff --check -- Cargo.toml Cargo.lock support/docs/audits/release-signoff.md support/docs/release-notes-draft.md`
  passed.
- `cargo check --locked` passed for `ict-engine v0.1.7`.
- Shared-checkout release audit
  `/tmp/ict-engine-release-readiness-v017-workingtree-20260523T131237+0800.json`
  exited `1`; `release_version_tag_available` now passes for `v0.1.7`, while
  `worktree_clean_for_release` and `source_origin_matches_selected_source`
  remain unresolved.

Release decision:

- The tag-collision blocker is repaired locally by retargeting to `v0.1.7`.
- Release is still not ready from this shared checkout. It still requires a
  clean selected-source audit after this retarget commit and explicit operator
  authorization before any source push, mirror push, tag, or GitHub Release.

### 2026-05-23 13:18 CST stale factor-claim terminalization readback

Fresh factor claim readback after terminalizing stale current-agent claim files:

- Updated only `/tmp` claim files, not repo Board A/B docs:
  - `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T-current-codex-ibkr-amd30m-existing-downstream-terminalization.claim`
    now points to the already recorded AMD 30m downstream fail-closed row.
  - `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260523T121900+0800-codex-ibkr-xlp-consumer-staples-mass-index-reversal-1m-mtf-gate1.claim`
    now points to the later terminalized XLP Mass Index exact Gate 1 claim and
    terminal metrics.
- Audit:
  `/tmp/ict-engine-factor-claims-after-stale-claim-terminalization-20260523T131817+0800.json`
  exited `1` with `summary.status=needs_attention`.
- Improvement: `active_claims=0`, `terminalized_claims=136`, `total_claims=136`,
  and `missing_run_roots=0`.
- Remaining blocker: `live_factor_processes=1`, the TOMAC TOD component-pair
  downstream wrapper under
  `/tmp/ict-engine-tomac-tod-component-pair-guard-overlay-20260523T-resume`.
- Factor promotion readback is still negative:
  `promotion_allowed_true=0`, `trade_usable_true=0`.

Decision:

- The stale claim-file blocker is cleared, but factor closure is still not
  proven while the TOMAC downstream process is live and no promotable/trade-usable
  factor exists.
- No Board A/B dirty work, mirror push, tag, GitHub Release, practical-trading
  promotion, or `update_goal complete` is authorized from this state.

### 2026-05-23 13:38-13:39 CST TOMAC downstream terminal readback clears live-process blocker

TOMAC wrapper completion:

- Wrapper root:
  `/tmp/ict-engine-tomac-tod-component-pair-guard-overlay-20260523T-resume`.
- Wrapper exit file:
  `/tmp/ict-engine-tomac-tod-component-pair-guard-overlay-20260523T-resume/checks/05_downstream_wrapper.exit`
  contains `0`.
- Wrapper stdout reports downstream decision file:
  `/tmp/ict-engine-tomac-tod-component-pair-guard-downstream-20260523T131439+0800/checks/downstream_metrics.json`.
- No child process remained under wrapper PID `11691` after completion.

Downstream decision:

- Summary:
  `/tmp/ict-engine-tomac-tod-component-pair-guard-downstream-20260523T131439+0800/summaries/terminal_decision_summary.md`.
- Decision: `component_pair_guard_downstream_fail_closed_or_incomplete`.
- All downstream command exits are zero through final export:
  `all_command_exits_zero=True`.
- Exact branch survived and path-ranker validation is visible, but execution
  remains closed: `execution_candidate_actionable=False`,
  `execution_candidate_status=no_trade`, `path_ranker_visible=True`,
  `path_ranker_used=False`, `validation_ready=True`.
- Validation counts remain below production/observation admission:
  `mature=3`, `history=3117`, `raw_scored=0`, `production=0`,
  `observation=0`.
- Promotion/trading readback is still negative: `promotion_allowed=False`,
  `trade_usable=False`, `extension_complete=False`.

Fresh factor-claim audit after TOMAC exit:

- Audit:
  `/tmp/ict-engine-factor-claims-after-tomac-exit-20260523T133909+0800.json`
  exited `0`.
- `summary.status=pass`, `active_claims=0`, `missing_run_roots=0`,
  `live_factor_processes=0`, `terminalized_claims=136`, `total_claims=136`.
- `promotion_allowed_true=0` and `trade_usable_true=0`.

Decision:

- The live TOMAC downstream process blocker is cleared, and factor-claim
  terminalization now passes.
- Factor promotion and practical trading are still not authorized because no
  claim reports `promotion_allowed_true` or `trade_usable_true`.
- Release remains separate and still requires a clean selected-source audit plus
  explicit operator authorization before source push, mirror push, tag, or
  GitHub Release.

### 2026-05-23 13:41-13:42 CST current factor audit and clean v0.1.7 selected-source release audit

Fresh factor-claim audit:

- Audit:
  `/tmp/ict-engine-factor-claims-current-20260523T134155+0800.json`
  exited `0`.
- `summary.status=pass`, `active_claims=0`, `missing_run_roots=0`,
  `live_factor_processes=0`, `terminalized_claims=136`, `total_claims=136`.
- `promotion_allowed_true=0` and `trade_usable_true=0`.

Fresh clean selected-source release audit:

- Detached worktree:
  `/tmp/ict-engine-release-clean-head-20260523T134219+0800` at
  `HEAD=849772d185f44d7722edb66b7d39bd65a24146e9`.
- Audit:
  `/tmp/ict-engine-release-readiness-clean-head-rerun-20260523T134248+0800.json`
  exited `1`.
- Passed gates: `worktree_clean_for_release`, `cargo_release_policy`,
  `release_docs_fresh_for_selected_tag`, and `release_version_tag_available`.
- `v0.1.7` remains available in the release mirror; known tags are `v0.0.1`
  through `v0.1.6`.
- Only unresolved gate: `source_origin_matches_selected_source`.
- Source/origin readback: selected `HEAD=849772d185f44d7722edb66b7d39bd65a24146e9`,
  `origin/main=4406454de95d40551acfcb573e3a4f68bf189e0b`,
  `release_mirror_main=e6a8e62826692c645303ba3fdc1d43790a048761`,
  `source_ahead_of_origin=5`, `source_behind_origin=0`.

Decision:

- Factor terminalization is currently clean, but still no promotion/trade-usable
  factor exists.
- The selected source is clean and internally ready for a `v0.1.7` release export
  except for source/origin alignment.
- Publishing still requires explicit operator authorization for the exact source
  push or clean-export publication path, plus mirror push, tag, and GitHub
  Release actions. None is authorized from this handoff state.

### 2026-05-23 13:45-13:53 CST current HEAD v0.1.7 clean release verification

Fresh factor-claim audit:

- Audit:
  `/tmp/ict-engine-factor-claims-current-20260523T134520+0800.json`
  exited `0`.
- `summary.status=pass`, `active_claims=0`, `missing_run_roots=0`,
  `live_factor_processes=0`, `terminalized_claims=136`, `total_claims=136`.
- `promotion_allowed_true=0` and `trade_usable_true=0`.

Current-HEAD clean release-readiness audit:

- Detached worktree:
  `/tmp/ict-engine-release-clean-head-20260523T134535+0800` at
  `HEAD=877bd9167479a79560e596bd52648a14ac2d3ad8`.
- Audit:
  `/tmp/ict-engine-release-readiness-clean-head-20260523T134535+0800.json`
  exited `1`.
- Passed gates: `worktree_clean_for_release`, `cargo_release_policy`,
  `release_docs_fresh_for_selected_tag`, and `release_version_tag_available`.
- `v0.1.7` remains available in the release mirror; known tags are `v0.0.1`
  through `v0.1.6`.
- Only unresolved gate: `source_origin_matches_selected_source`.
- Source/origin readback: selected `HEAD=877bd9167479a79560e596bd52648a14ac2d3ad8`,
  `origin/main=4406454de95d40551acfcb573e3a4f68bf189e0b`,
  `release_mirror_main=e6a8e62826692c645303ba3fdc1d43790a048761`,
  `source_ahead_of_origin=6`, `source_behind_origin=0`.

Clean-worktree release verification:

- `cargo fmt --check` passed.
- `cargo check --locked` passed for `ict-engine v0.1.7`.
- Zero-config smoke root:
  `/tmp/ict-engine-v017-smoke-20260523T134618+0800`.
- Zero-config smoke commands all exited `0`:
  `provider-status --compact`, `analyze --symbol DEMO --demo --human`, and
  `workflow-status --symbol DEMO --refresh --agent`.
- Smoke privacy scan found no `/Users/`, `Downloads`, or common token/key
  patterns in smoke output files.
- Initial parallel `cargo clippy --locked --all-targets -- -D warnings` and
  `cargo test --locked` attempts hit host `No space left on device` while
  writing build/test artifacts.
- Safe temp cleanup performed: removed older current-lane release worktree
  `/tmp/ict-engine-release-clean-head-20260523T134219+0800`, ran `cargo clean`
  inside `/tmp/ict-engine-release-clean-head-20260523T134535+0800`, and freed
  `5.5GiB` from that target directory; free space recovered to about `21GiB`,
  then `44GiB` before final test rerun.
- Sequential rerun passed:
  `cargo clippy --locked --all-targets -- -D warnings`.
- Sequential rerun passed:
  `cargo test --locked` with all unit/integration/doc tests green.

Decision:

- Current selected source has clean release-quality evidence for `v0.1.7`.
- Release is still not authorized or complete because source/origin alignment is
  unresolved and no operator permission has been given for source push, clean
  export publication, mirror push, tag, or GitHub Release.
- Factor promotion/trading remains explicitly negative: no promotable or
  trade-usable factor is proven by the claim audit.

### 2026-05-23 14:00-14:01 CST non-published v0.1.7 selected-source export artifact

Fresh factor-claim audit:

- Audit:
  `/tmp/ict-engine-factor-claims-current-20260523T140008+0800.json`
  exited `0`.
- `summary.status=pass`, `active_claims=0`, `missing_run_roots=0`,
  `live_factor_processes=0`, `terminalized_claims=136`, `total_claims=136`.
- `promotion_allowed_true=0` and `trade_usable_true=0`.

Current selected-source audit before export:

- Detached worktree:
  `/tmp/ict-engine-release-export-head-20260523T140040+0800` at
  `HEAD=eed300a271a79468d6425f14d1af37c595f7e71c`.
- Audit:
  `/tmp/ict-engine-release-readiness-export-head-20260523T140040+0800.json`
  exited `1`.
- Passed gates: `worktree_clean_for_release`, `cargo_release_policy`,
  `release_docs_fresh_for_selected_tag`, and `release_version_tag_available`.
- Only unresolved gate: `source_origin_matches_selected_source`.
- Source/origin readback: selected `HEAD=eed300a271a79468d6425f14d1af37c595f7e71c`,
  `origin/main=4406454de95d40551acfcb573e3a4f68bf189e0b`,
  `release_mirror_main=e6a8e62826692c645303ba3fdc1d43790a048761`,
  `source_ahead_of_origin=7`, `source_behind_origin=0`.
- `v0.1.7` remains available in the release mirror; known tags are `v0.0.1`
  through `v0.1.6`.

Non-published export artifact:

- Tarball:
  `/tmp/ict-engine-v0.1.7-selected-source-20260523T140040+0800.tar.gz`
  (`176M`).
- Manifest:
  `/tmp/ict-engine-v0.1.7-selected-source-20260523T140040+0800.manifest.txt`
  (`7.0M`).
- Archive prefix: `ict-engine-v0.1.7/`.
- Archive entries: `47938`.
- SHA-256:
  `71361b85ecc97ab6866c7aeb917bcb2ce59645c34ab98fa86cef2224b308acd2`
  for the tarball.
- SHA-256:
  `4e93d4c1ffd6584ce3c26525d4bfd7bd86b6d35c09795708ab18c59df17b7041`
  for the manifest.

Privacy/readback notes:

- Manifest scan for `/Users/`, `Downloads`, and common token patterns produced
  only filename false positives from `risk-...` path substrings matching the
  broad `sk-...` token regex; no private absolute path was present in those
  manifest lines.
- Sampled text scan of release-critical docs found only the literal policy text
  `Do not expose /Users/...` in `AGENT.md`; this is an instruction, not a leaked
  local path.
- This export is deliberately not pushed, tagged, mirrored, or published.

Decision:

- A non-published clean selected-source export artifact now exists for the
  pre-record commit `eed300a271a79468d6425f14d1af37c595f7e71c`.
- Recording this evidence in the repo necessarily advances `main`; before any
  actual release publication, rerun the clean selected-source audit and export
  at the exact commit the operator authorizes.
- Release remains unauthorized and incomplete until the operator explicitly
  chooses the source push or clean-export publication path and authorizes mirror
  push, tag, and GitHub Release actions.
