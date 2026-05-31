## ICT Engine Agent Entry

Read [AGENT.md](AGENT.md) first. It is the authoritative deep contract for zero-config behavior, privacy, closed-loop order, and release claims. This `AGENTS.md` is the short routing surface for future AI work.

### What this repo is

- Rust-first CLI and library for inspectable market-structure research, not a black-box signal service.
- Optional hot-plug layers exist for Python, Auto-Quant, provider runtimes, and TimesFM, but zero-config must stay consumer-safe.
- Proof comes from current-turn commands and artifacts, not from old docs or chat memory.

### Read this before editing

- `AGENT.md`
- `support/docs/contributor-quickstart.md`
- `support/docs/command-output-contract.md` if you touch CLI/readback surfaces
- `skills/auto-quant-handoff-harness/SKILL.md` if you touch Auto-Quant handoff,
  workspace isolation, or agent workflow payloads
- `support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md` for the audit/remediation ledger; re-check newer dated status before treating it as current
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md` only when release/provider history matters

### Key directories

- `src/main.rs`: command enum, Clap wiring, large dispatch surface
- `src/application/`: current orchestration and behavior layer
- `src/domain/`: narrower domain contracts for belief, execution, regime, strategy
- `src/state/`: workflow snapshot, persistence, artifact/state schema
- `src/application/data_sources/` and `src/data/realtime/`: provider runtime and live-data boundaries
- `src/application/auto_quant/` plus `support/scripts/auto_quant_external/`: Auto-Quant integration boundary
- `tests/`: Rust integration/contract tests
- `support/scripts/`: Python helpers and audits; public/helper inventory lives in `support/scripts/SCRIPTS.md` and `support/scripts/script_manifest.json`
- `skills/`: existing repo-local evidence skills; optional agent aids, not runtime inputs
- `.agents/skills/` if present: project-specific AI workflow skills added for development tasks

### Non-negotiable repo rules

- Keep trial state in `/tmp/...` even if a command help default says `state`. `support/scripts/smoke_acceptance.sh` rejects repo-local state unless `ICT_ENGINE_ALLOW_REPO_STATE=1`.
- Do not let runtime/code depend on `support/docs/plans/*.md`. CI enforces this with `python3 support/scripts/ci/check_docs_runtime_isolation.py`.
- Do not infer trade readiness from demos, candidate packs, sparse positives, or training surfaces.
- Preserve unrelated dirty work. This repo is often shared and already has many live artifacts.
- Treat `provider-status` as readiness guidance, not proof that the requested provider returned usable rows.
- Auto-Quant handoff payloads that launch agent work must carry lane-local
  workspace instructions and plan/work/review evidence requirements; an
  Auto-Quant run is candidate evidence only, not `trade_usable=true`.

### Reuse before rebuild

- Prefer `src/application/reporting/*` for behavioral report construction; `src/reporting/*` is mostly facade/re-export territory.
- Check `src/application/command_inputs.rs` and existing Clap args before inventing new command DTOs.
- Check `support/scripts/SCRIPTS.md`, `support/scripts/script_manifest.json`, and `support/scripts/check_script_manifest.py` before adding new helper scripts.
- Check existing factor candidate and provider example surfaces under `support/examples/` before creating new fixtures or profile shapes.

### Common command paths

Consumer-safe first-run command set; keep ordering aligned across `AGENT.md`, `README.md`, and CLI help when standardizing:

```bash
cargo run --quiet -- provider-status --compact
cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human
cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent
cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json
cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent
```

Core contributor loop:

```bash
git status --short
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test <focused_test_name> -- --nocapture
support/scripts/smoke_acceptance.sh
git diff --check
```

Python/helper verification:

```bash
python3 -m unittest <module> -v
python3 support/scripts/ci/check_docs_runtime_isolation.py
```

### High-risk areas

- `src/main.rs` and `src/application/orchestration/workflow_status.rs` are both very large control chokepoints.
- `src/state/types.rs` changes can silently break artifact/schema consumers.
- Provider constants and contracts can be duplicated across Rust and Python; verify both sides for IBKR/Hubble/Auto-Quant changes.
- Auto-Quant handoff and adoption surfaces must stay aligned across
  `src/application/auto_quant/handoff.rs`,
  `src/application/auto_quant/command_entry.rs`, and the repo-local
  `skills/auto-quant-handoff-harness/SKILL.md`.
- All Board / Board A / Board B / Board AB / current-board / coverage-matrix docs are archive/reference material only. They are not active state, enabled workflow surfaces, live entrypoints, lock tables, task queues, candidate-selection sources, or execution authority; create a local doc, `/tmp` workdoc, and `/tmp` claim first.
- `support/prompts/*.md` are idea surfaces, not executable contracts.

### Verification checklist

- Run the exact command or targeted test that proves the edited behavior.
- If Python under `support/scripts/**` changed, run the matching unittest root; CI does not currently cover those suites.
- If CLI/help/output changed, re-check `support/docs/command-output-contract.md` parity and first-run command ordering across `AGENT.md`, `README.md`, and help text.
- If path-ranker/trainer artifacts changed, verify both Rust and Python contract surfaces plus `tests/fixtures/policy_training/`.
- If helper inventory changed, keep `support/scripts/SCRIPTS.md` and `support/scripts/script_manifest.json` in sync.
