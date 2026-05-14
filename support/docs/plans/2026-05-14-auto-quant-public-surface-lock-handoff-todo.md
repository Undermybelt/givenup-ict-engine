# Auto-Quant Public Surface Lock Handoff TODO

Date: 2026-05-14

Parent board:
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`

Goal:
- Lock public factor-iteration entry surfaces to Auto-Quant while preserving
  zero-config consumer start, opt-in hot-plug provider/material reuse, compact
  human/agent output, and no-pollution state handling.

Non-goals:
- Do not rewrite Board A or Board B research objectives, gates, or active run
  roots.
- Do not remove internal native research code paths that are not public CLI
  entry surfaces.
- Do not force maintainer-local provider profiles, paths, or private data into
  zero-config flows.
- Do not broaden into unrelated architecture cleanup or historical artifact
  deletion.

Current diagnosis:
- Public surfaces still leaked a parallel native-vs-AQ story even though the
  intended consumer path already centered on Auto-Quant handoff artifacts.
- Specific leaks included:
  - CLI help and README advertising `--backend native`
  - native runtime recommendation rewriting back to `factor-research ... --backend native`
  - first-run workflow guidance describing the factor route as generic
    backtest/factor looping instead of formal Auto-Quant handoff plus review
  - human research output treating Auto-Quant as optional instead of primary

Status legend:
- `done`, `active`, `next`, `blocked`, `not_yet`

## Current Todo Board

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Re-run routing and repo authority read for continuation | Route kept on `sd/ict-engine-surface-intgr`; re-read Hermes routers, repo `CLAUDE.md`, repo `AGENT.md`, and runtime skill. |
| done | Recover aborted verification state | Previous `cargo test public_factor_iteration_backend -- --nocapture` completed successfully after the interrupted turn. |
| done | Create AQ-only public CLI gate | `factor-research` / `factor-autoresearch` shell entry now rejects non-`auto-quant` backend values on the public CLI. |
| done | Remove native rewrite from public next-command generation | Native report/runtime command rewrite back to `--backend native` was removed from factor-research recommendation flow. |
| done | Reframe first-run factor route as Auto-Quant handoff | `workflow-status` first-run guide now labels the route as Auto-Quant iteration and points follow-up to `auto-quant-adoption-review`. |
| done | Remove native factor-iteration wording from public help/docs | `src/main.rs`, `README.md`, and `README.zh-CN.md` now advertise the AQ path instead of native factor research. |
| done | Re-run focused verification after the source edits | `cargo fmt --check`; `cargo test public_factor_iteration_backend -- --nocapture`; `cargo test single_recorded_research_path_does_not_require_user_selection -- --nocapture`; `cargo test factor_research_human_output_is_short_text_not_json_dump -- --nocapture`; `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`; `cargo test workflow_provider_support_stays_inactive_when_command_has_no_provider_gap -- --nocapture` all passed. |
| done | Run zero-config smoke against the revised public route wording | Real CLI proof under `/tmp/ict-engine-aq-lock-smoke`: native backend rejected; default `factor-research` emitted AQ handoff; `workflow-status --human` preferred the AQ handoff; `auto-quant-adoption-review` returned the formal review surface. |
| active | Decide commit boundary | The slice is now verification-complete and appears commit-worthy; confirm touched-file set and preserve unrelated dirty work before committing. |
| next | Write terminal result back to parent release board | Parent board should get a compact pointer plus evidence once this slice is committed or explicitly handed off. |

## File ownership for this slice

Public route + help:
- `src/main.rs`
- `README.md`
- `README.zh-CN.md`

Command/recommendation surfaces:
- `src/factor_research_command.rs`
- `src/factor_research_runtime.rs`
- `src/application/backtest/finalize_recommendations.rs`
- `src/application/orchestration/workflow_status.rs`
- `src/application/reporting/backtest_output.rs`
- `src/application/provider_catalog.rs`

Authority docs:
- this file
- parent release board after terminal verification

## Verification commands

```bash
cargo fmt --check
cargo test public_factor_iteration_backend -- --nocapture
cargo test single_recorded_research_path_does_not_require_user_selection -- --nocapture
cargo test factor_research_human_output_is_short_text_not_json_dump -- --nocapture
cargo test application::orchestration::workflow_status::tests:: -- --nocapture
cargo test workflow_provider_support_stays_inactive_when_command_has_no_provider_gap -- --nocapture
```

Zero-config smoke target:

```bash
cargo run --quiet -- provider-status --compact
cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --human
```

## Live evidence log

- 2026-05-14 current turn: `cargo test public_factor_iteration_backend -- --nocapture`
  passed after the interrupted turn resumed. It executed the new
  `factor_research_command` AQ-lock tests and finished cleanly.
- 2026-05-14 current turn: `cargo fmt --check` passed after formatting the
  touched workflow-status file.
- 2026-05-14 current turn:
  `cargo test single_recorded_research_path_does_not_require_user_selection -- --nocapture`
  passed.
- 2026-05-14 current turn:
  `cargo test factor_research_human_output_is_short_text_not_json_dump -- --nocapture`
  passed.
- 2026-05-14 current turn:
  `cargo test application::orchestration::workflow_status::tests:: -- --nocapture`
  passed (`114` workflow-status tests).
- 2026-05-14 current turn:
  `cargo test workflow_provider_support_stays_inactive_when_command_has_no_provider_gap -- --nocapture`
  passed.
- 2026-05-14 current turn:
  `cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-aq-lock-smoke --backend native --human`
  failed closed with:
  `factor-research public factor iteration is locked to Auto-Quant; rerun without --backend or pass --backend auto-quant`.
- 2026-05-14 current turn:
  `cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-aq-lock-smoke --human`
  exited `0` and emitted an `Auto-Quant handoff | status=dependency_ready_data_missing`
  surface with `Review: ict-engine auto-quant-adoption-review ...` and
  `Workflow: ict-engine workflow-status ...`.
- 2026-05-14 current turn:
  `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-aq-lock-smoke --human`
  exited `0` and preferred the AQ handoff:
  `Next: Continue the Auto-Quant handoff. Run ict-engine auto-quant-prepare ... then review with ict-engine auto-quant-adoption-review ...`.
- 2026-05-14 current turn:
  `cargo run --quiet -- auto-quant-adoption-review --symbol DEMO --state-dir /tmp/ict-engine-aq-lock-smoke`
  exited `0` with `backend=auto-quant`, `review_status=prepare_required`,
  and `recommended_next_command=ict-engine auto-quant-prepare --state-dir /tmp/ict-engine-aq-lock-smoke`.
