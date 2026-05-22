# Zero-Config Consumer Hot-Plug Handoff TODO

Date: 2026-05-22

Purpose: continue the zero-config / consumer-safe hot-plug lane without
polluting public defaults, while letting a user explicitly choose whether to
reuse maintainer-specific local data contracts.

## Authority And Related Boards

This file is the current continuation board for the 2026-05-22 request:

- "继续实现。保证零配置，满足消费者可用，token友好，无污染无负债，具体到我个人所需的数据内容，设计成热插拔的，可以让用户选择是否沿用。实时更新一个新建的handoff to do文档"

Related authority / prior slices:

- `support/docs/plans/2026-05-09-ict-engine-audit-remediation-todo.md`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `support/docs/plans/2026-05-15-optional-external-history-hotplug-handoff-todo.md`

## Guardrails

- Keep zero-config defaults unchanged for public consumers.
- Keep opt-in personal/local data lanes explicit and inspectable.
- Prefer additive helper surfaces over new mandatory core defaults.
- Keep outputs token-friendly and compact.
- Do not stage unrelated dirty-tree work.
- Use `/tmp` for smoke / generated state.

## Verified Baseline On Entry

- Routing refreshed:
  - `~/.hermes/routing/skill-router.md`
  - `~/.hermes/routing/project-router.md`
  - repo `CLAUDE.md`
  - repo `AGENT.md`
  - runtime skill
    `~/.hermes/skills/software-development/ict-engine-maintenance-loop/SKILL.md`
- The current repo already exposes:
  - repo opt-in provider profiles
  - `available_opt_in_profiles` / `selected_profile_id` in workflow surfaces
  - external-history adoption helper:
    `support/scripts/research/external_history_adoption.py`
- Current live continuation also already landed two verified fixes in
  `src/application/entry_models/training_export.rs` and recorded them in the
  audit-remediation board.

## Current Hypothesis

The remaining ergonomic gap is not raw capability; it is user choice clarity.
The external-history adoption helper currently emits one command lane, which
does not cleanly separate:

1. keep generic zero-config defaults, and
2. explicitly reuse the opt-in personal profile.

For consumer safety, the helper should emit both lanes, keep zero-config as the
default recommendation, and still advertise the opt-in lane for users who want
to reuse the saved profile/material mix.

## Todo Checkpoint

Status legend: `done`, `active`, `next`, `blocked`, `not_yet`.

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Route the repo and reload hot-plug authority docs | Routed to `sd/ict-engine-maintenance-loop`; read repo entry docs and relevant hot-plug boards. |
| done | Identify a narrow additive slice | Chosen slice: dual-lane external-history adoption bundle with zero-config default plus opt-in reuse commands. |
| done | Write RED tests for explicit zero-config vs opt-in command lanes | `python3 -m unittest support/scripts/research/tests/test_external_history_adoption.py -v` initially failed on missing `default_choice_id`, missing command choices, and missing dual-lane shell sections. |
| done | Update adoption helper to emit dual-lane bundle + shell file | `support/scripts/research/external_history_adoption.py` now emits `command_choices`, `default_choice_id=keep_zero_config`, top-level zero-config commands, and separate opt-in commands. |
| done | Fix repo profile selector propagation for emitted `--profile` commands | `support/scripts/research/market_data_resolver.py` now exposes `selected_profile.selector`, and the adoption helper now uses `thrill3r-nq-external-history-v1` rather than the invalid underscore profile id. |
| done | Verify helper tests and shell artifact shape | Unit tests and real `/tmp` smoke passed; emitted JSON and shell now show both `keep_zero_config` and `reuse_saved_profile`. |
| done | Commit the dual-lane adoption slice narrowly | Commit `7deca84b` staged only helper/resolver/tests/handoff-doc files. |
| done | Keep adjacent resolver profile surfaces consistent | `support/scripts/research/factor_candidate_resolver.py` now also exposes `selected_profile.selector`; dedicated tests passed. |
| done | Choose the next consumer-safe hot-plug surface after resolver consistency | Chosen and implemented as script-governance registration for the three consumer adoption/readback helpers. |
| done | Register adoption/readback helpers in script governance | `SCRIPTS.md` and `script_manifest.json` now list `market_data_resolver.py`, `external_history_adoption.py`, and `factor_candidate_resolver.py` with safe-default posture and focused test commands. |
| done | Re-verify script governance and focused helper tests | `check_script_manifest.py` passed with `entries=19`; helper `py_compile` passed; focused resolver/adoption unit tests passed 15/15; `git diff --check` passed. |
| done | Decide checkpoint commit boundary | Verification is green; commit boundary is exactly `support/scripts/SCRIPTS.md`, `support/scripts/script_manifest.json`, and this handoff doc. |

## Verification Checklist

- `python3 -m py_compile support/scripts/research/external_history_adoption.py support/scripts/research/tests/test_external_history_adoption.py`
- `python3 -m unittest support/scripts/research/tests/test_external_history_adoption.py -v`
- `python3 -m py_compile support/scripts/research/market_data_resolver.py support/scripts/research/tests/test_market_data_resolver.py`
- `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py support/scripts/research/tests/test_external_history_adoption.py -v`
- `python3 support/scripts/research/external_history_adoption.py --repo-root . --market NQ --symbol <symbol> --input 1h=<normalized.json> --output-dir /tmp/<run>`
- Inspect:
  - `/tmp/<run>/external_history_adoption_bundle.json`
  - `/tmp/<run>/suggested_commands.sh`

## Live Notes

- 2026-05-22 21:58 +0800 live readback for "所以无事可做了":
  - Deterministic answer: no. Current repo evidence still has unresolved work.
  - `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-release-readiness-audit-current.json`
    exited `1` with `summary.status=needs_fix`, `pass_count=1`,
    `fail_count=4`, unresolved gates:
    `worktree_clean_for_release`, `release_docs_fresh_for_selected_tag`,
    `source_origin_matches_selected_source`, and
    `release_version_tag_available`.
  - `python3 support/scripts/factor_claim_terminalization_audit.py --output /tmp/ict-engine-factor-claim-terminalization-audit-current.json --compact`
    exited `1` by design with `summary.status=needs_attention`,
    `total_claims=42`, `terminalized_claims=28`, `active_claims=14`,
    `missing_run_roots=0`, `trade_usable_true=0`, and
    `promotion_allowed_true=0`.
  - `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-current.json`
    passed the light gate with `pass_count=4`, `fail_count=0`, `skip_count=4`;
    this is not a current full-heavy completion claim.
  - Next safe target: continue from release readiness or factor claim
    terminalization without taking over active Board B lanes; keep zero-config
    defaults and personal/profile reuse as opt-in.

- RED evidence:
  - `python3 -m unittest support/scripts/research/tests/test_external_history_adoption.py -v`
  - failure surface: missing `default_choice_id`, missing `command_choices`, no explicit zero-config / opt-in split
- GREEN evidence:
  - `python3 -m py_compile support/scripts/research/market_data_resolver.py support/scripts/research/external_history_adoption.py support/scripts/research/tests/test_market_data_resolver.py support/scripts/research/tests/test_external_history_adoption.py`
  - `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py support/scripts/research/tests/test_external_history_adoption.py -v`
    - passed: `6` tests
- Adjacent consistency follow-up:
  - RED:
    - `python3 -m unittest support/scripts/research/tests/test_factor_candidate_resolver.py -v`
    - failed on missing `selected_profile.selector`
  - GREEN:
    - `python3 -m py_compile support/scripts/research/factor_candidate_resolver.py support/scripts/research/tests/test_factor_candidate_resolver.py`
    - `python3 -m unittest support/scripts/research/tests/test_factor_candidate_resolver.py -v`
    - passed: `9` tests
- Real smoke:
  - run root: `/tmp/ict-engine-external-history-adoption-rRPMTB`
  - `python3 support/scripts/research/external_history_adoption.py --repo-root . --market NQ --symbol BTCUSDT_EXT_1H --input 1h=/tmp/ict-engine-external-history-adoption-rRPMTB/btc-1h.json --output-dir /tmp/ict-engine-external-history-adoption-rRPMTB/out`
  - observed bundle facts:
    - `schema_version=external-history-adoption/v2`
    - `default_choice_id=keep_zero_config`
    - `selected_profile.selector=thrill3r-nq-external-history-v1`
    - `command_choices[0].choice_id=keep_zero_config`
    - `command_choices[1].choice_id=reuse_saved_profile`
  - observed shell facts:
    - section `# keep_zero_config (recommended)`
    - section `# reuse_saved_profile`
    - opt-in commands use `--profile thrill3r-nq-external-history-v1`
 - Narrow checkpoint already committed:
  - `7deca84b` `feat: split external history adoption into zero-config and opt-in lanes`
- The dirty worktree is large; this board stays scoped to the external-history
  adoption helper unless new evidence forces a narrower or safer target.

## 2026-05-22 Script-Governance Registration Continuation

Status:
- done for implementation and focused verification, owner Codex current turn,
  claimed 2026-05-22 20:21:31 +0800.

Current deterministic answer to "所以无事可做了":
- no. The latest completion boards still mark release completion and factor
  diffusion as unproven, and this board had an active consumer hot-plug follow-up.

Implemented narrow slice:
- Registered the already-tested adoption/readback helpers in
  `support/scripts/SCRIPTS.md`.
- Added machine-readable manifest entries in
  `support/scripts/script_manifest.json`.
- Kept the helpers classified as safe-default/read-only-style utilities:
  they require explicit output paths, and personal/profile reuse remains opt-in.

Verification:
- `python3 support/scripts/check_script_manifest.py`
  - passed with `script_manifest status=pass entries=19`.
- `python3 -m py_compile support/scripts/research/market_data_resolver.py support/scripts/research/external_history_adoption.py support/scripts/research/factor_candidate_resolver.py`
  - passed.
- `python3 -m unittest support.scripts.research.tests.test_market_data_resolver support.scripts.research.tests.test_external_history_adoption support.scripts.research.tests.test_factor_candidate_resolver -v`
  - passed 15 tests.
- `git diff --check -- support/scripts/SCRIPTS.md support/scripts/script_manifest.json support/docs/plans/2026-05-22-zero-config-consumer-hotplug-handoff-todo.md`
  - passed.

Commit boundary selected:
- stage only:
  - `support/scripts/SCRIPTS.md`
  - `support/scripts/script_manifest.json`
  - `support/docs/plans/2026-05-22-zero-config-consumer-hotplug-handoff-todo.md`
- do not stage unrelated dirty source, Board A/B docs, run roots, or generated
  experiment scripts.
- checkpoint commit message: `docs: register hotplug adoption helpers`.
