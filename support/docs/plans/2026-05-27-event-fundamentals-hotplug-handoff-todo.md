# Event And Fundamentals Hot-Plug Handoff TODO

Date: 2026-05-27

Purpose: continue the zero-config / consumer-safe hot-plug objective with a
first additive sidecar lane for event and lagged-fundamentals data, while
keeping public defaults unchanged and personal data reuse explicitly opt-in.

## Authority And Related Boards

This file is the current continuation board for the approved Phase 1 slice:

- `Phase 1 = earnings/dividend/macro event series + lagged fundamentals adoption lane`

Related authority / prior slices:

- `AGENT.md`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `support/docs/plans/2026-05-22-zero-config-consumer-hotplug-handoff-todo.md`
- `support/docs/external/2026-05-27-stock-screener-intake.md`

## Guardrails

- Keep zero-config defaults unchanged for public consumers.
- Keep opt-in personal/local data lanes explicit and inspectable.
- Do not make event/fundamentals sidecars mandatory runtime inputs.
- Keep emitted artifacts compact and token-friendly.
- Prefer additive helper surfaces over broad runtime rewrites.
- Do not stage unrelated dirty-tree work.
- Use `/tmp` for smoke / generated state.

## Approved Phase 1 Boundary

What is in scope now:

1. explicit opt-in adoption helper for:
   - earnings event series
   - dividend event series
   - macro event series
   - lagged fundamentals sidecar
2. dual-lane output:
   - keep zero-config defaults
   - reuse saved personal sidecar profile
3. provider-profile contract + compact emitted bundle + shell suggestions
4. focused tests and script-governance registration

What is out of scope for this slice:

- auto-consuming these sidecars inside every runtime command
- text/filing ingestion (`SEC EDGAR` style) and document parsing
- mandatory provider additions to zero-config default behavior

## Current Hypothesis

The clean owner is a new helper under `support/scripts/research/` that mirrors
the successful `external_history_adoption.py` pattern:

- explicit input artifact paths
- compact machine-readable bundle
- compact dual-lane shell suggestions
- selected profile surfaced via existing provider-profile resolver

This makes the sidecar lane real and reusable now without pretending the public
runtime already consumes those artifacts by default.

## Todo Checkpoint

Status legend: `done`, `active`, `next`, `blocked`, `not_yet`.

| Status | Item | Evidence / Notes |
|---|---|---|
| done | Re-route repo and reload authority docs after approval | Re-read router files, repo `CLAUDE.md`, repo `AGENT.md`, runtime skill, and relevant prior hot-plug board. |
| done | Lock Phase 1 scope | Approved: event + lagged fundamentals sidecar adoption lane; filings/text deferred. |
| done | Create the live handoff TODO board | This file is the current authoritative continuation board for the slice. |
| done | Write RED tests for a new event/fundamentals adoption helper | Initial failure was `ModuleNotFoundError: No module named 'event_fundamentals_adoption'`. |
| done | Add opt-in provider profile for event/fundamentals sidecars | Added `support/examples/provider_profiles/thrill3r-nq-event-fundamentals-v1.json`. |
| done | Implement compact dual-lane adoption helper | Added `support/scripts/research/event_fundamentals_adoption.py`; helper emits bundle + shell suggestions with zero-config and opt-in lanes. |
| done | Register the helper in script governance | Added `event_fundamentals_adoption` to `support/scripts/SCRIPTS.md` and `support/scripts/script_manifest.json`. |
| done | Run focused verification and narrow commit | Commit `b66c3b5d` staged only the helper/profile/tests/governance/handoff slice. |
| done | Extend the sidecar lane beyond the minimal smoke pack | Helper now emits compact profile-contract readiness for covered vs missing sidecar contracts, and full four-artifact smoke is verified. |
| done | Push the sidecar lane one step closer to downstream practicality | Helper now emits compact lag-safety warnings and a downstream handoff summary. |
| done | Decide the first true consumer of the sidecar handoff | First consumer is now `ict-engine auto-quant-adoption-review --sidecar-handoff <event_fundamentals_adoption_bundle.json>`; it remains explicit, optional, and readback-only. |
| next | Decide the first non-review runtime consumer of the sidecar handoff | Candidate next step: one downstream runtime surface may opt into this bundle after proving fail-closed semantics and keeping zero-config unchanged. |

## Verification Checklist

- `python3 -m unittest support/scripts/research/tests/test_event_fundamentals_adoption.py -v`
- `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py -v`
- `python3 -m py_compile support/scripts/research/event_fundamentals_adoption.py support/scripts/research/tests/test_event_fundamentals_adoption.py`
- `python3 support/scripts/research/event_fundamentals_adoption.py --repo-root . --market NQ --symbol <symbol> --artifact earnings=<path> --artifact fundamentals=<path> --output-dir /tmp/<run>`
- Inspect:
  - `/tmp/<run>/event_fundamentals_adoption_bundle.json`
  - `/tmp/<run>/suggested_commands.sh`

## Live Notes

- 2026-05-27 15:57:07 +0800
  - User approved both the design boundary and moving forward without further
    design debate.
  - The repo already has the reusable profile/adoption pattern for external
    history; this slice should extend that pattern rather than invent a second
    mechanism.
  - Event and lagged-fundamentals sidecars are treated as explicit optional
    evidence packs, not default runtime truth.
- 2026-05-27 16:00 +0800
  - RED behaved correctly:
    - `python3 -m unittest support/scripts/research/tests/test_event_fundamentals_adoption.py -v`
    - initial failure: `ModuleNotFoundError: No module named 'event_fundamentals_adoption'`
  - Resolver/profile seam was already green:
    - `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py -v`
    - passed 5 tests including the new opt-in event/fundamentals profile coverage.
  - GREEN helper implementation now exists:
    - `support/scripts/research/event_fundamentals_adoption.py`
    - emits `event_fundamentals_adoption_bundle.json`
    - emits dual-lane `suggested_commands.sh`
- 2026-05-27 16:03 +0800
  - GREEN verification passed:
    - `python3 -m unittest support/scripts/research/tests/test_market_data_resolver.py support/scripts/research/tests/test_event_fundamentals_adoption.py -v`
      - passed `7` tests
    - `python3 support/scripts/check_script_manifest.py`
      - passed with `entries=28`
    - `python3 -m py_compile support/scripts/research/event_fundamentals_adoption.py support/scripts/research/tests/test_event_fundamentals_adoption.py`
      - passed
    - `git diff --check -- support/scripts/research/event_fundamentals_adoption.py support/scripts/research/tests/test_event_fundamentals_adoption.py support/scripts/research/tests/test_market_data_resolver.py support/examples/provider_profiles/thrill3r-nq-event-fundamentals-v1.json support/scripts/SCRIPTS.md support/scripts/script_manifest.json support/docs/plans/2026-05-27-event-fundamentals-hotplug-handoff-todo.md`
      - passed
  - Real smoke:
    - run root: `/private/tmp/ict-engine-event-fundamentals.97RYxK/out`
    - command:
      - `python3 support/scripts/research/event_fundamentals_adoption.py --repo-root . --market NQ --symbol NQ_EVENT_CONTEXT --artifact earnings=<tmp>/earnings.json --artifact fundamentals=<tmp>/fundamentals.json --output-dir /private/tmp/ict-engine-event-fundamentals.97RYxK/out`
    - observed bundle facts:
      - `default_choice_id=keep_zero_config`
      - `provided_artifact_count=2`
      - `provided_artifact_kinds=[earnings, fundamentals]`
      - `selected_profile.selector=thrill3r-nq-event-fundamentals-v1`
      - `choice_ids=[keep_zero_config, reuse_saved_profile]`
    - observed shell facts:
      - section `# keep_zero_config (recommended)`
      - section `# reuse_saved_profile`
      - label `# review_sidecars`
      - opt-in commands use `--profile thrill3r-nq-event-fundamentals-v1`
- 2026-05-27 16:05 +0800
  - Narrow checkpoint committed:
    - `b66c3b5d` `feat: add event fundamentals hotplug adoption`
  - Commit scope:
    - `support/scripts/research/event_fundamentals_adoption.py`
    - `support/scripts/research/tests/test_event_fundamentals_adoption.py`
    - `support/scripts/research/tests/test_market_data_resolver.py`
    - `support/examples/provider_profiles/thrill3r-nq-event-fundamentals-v1.json`
    - `support/scripts/SCRIPTS.md`
    - `support/scripts/script_manifest.json`
    - this handoff board
- 2026-05-27 16:12 +0800
  - Continued the helper beyond minimal artifact counting:
    - `event_fundamentals_adoption.py` now emits `artifact_readiness`
    - readiness reports:
      - `profile_contract_ready`
      - `covered_contract_count`
      - `covered_contract_ids`
      - `missing_contract_ids`
  - GREEN verification passed:
    - `python3 -m unittest support/scripts/research/tests/test_event_fundamentals_adoption.py -v`
      - passed `3` tests
    - `python3 -m py_compile support/scripts/research/event_fundamentals_adoption.py support/scripts/research/tests/test_event_fundamentals_adoption.py`
      - passed
    - `git diff --check -- support/scripts/research/event_fundamentals_adoption.py support/scripts/research/tests/test_event_fundamentals_adoption.py support/docs/plans/2026-05-27-event-fundamentals-hotplug-handoff-todo.md`
      - passed
  - Full four-artifact smoke:
    - run root: `/private/tmp/ict-engine-event-fundamentals-full.BJ4Kw2/out`
    - command used all four artifacts:
      - `earnings`
      - `dividends`
      - `macro`
      - `fundamentals`
    - observed readiness facts:
      - `profile_contract_ready=true`
      - `covered_contract_count=4`
      - `covered_contract_ids=[dividend_event_series, earnings_event_series, lagged_fundamentals_sidecar, macro_event_series]`
      - `missing_contract_ids=[]`
- 2026-05-27 16:18 +0800
  - Continued the helper toward safer downstream reuse:
    - `event_fundamentals_adoption.py` now emits:
      - `usage_warnings`
      - `downstream_handoff`
  - GREEN verification passed:
    - `python3 -m unittest support/scripts/research/tests/test_event_fundamentals_adoption.py -v`
      - passed `3` tests
  - Full four-artifact smoke:
    - run root: `/private/tmp/ict-engine-event-fundamentals-full2.zSMmq1/out`
    - observed warnings:
      - `Lag fundamentals by effective date before backtest or live reuse.`
      - `Treat earnings timestamps as scheduled-event context until confirmed effective in your replay or live clock.`
      - `Use ex-dividend timestamps rather than announcement time when deriving trading context.`
      - `Keep macro events aligned to scheduled release timestamps and explicit importance tiers.`
    - observed downstream handoff facts:
      - `readiness=profile_contract_ready`
      - `missing_artifact_kinds=[]`
      - `allowed_use_modes=[research_context, factor_research_opt_in, auto_quant_handoff_context]`
- 2026-05-27 current continuation
  - Added the first explicit downstream review bridge on the Rust side:
    - `ict-engine auto-quant-adoption-review --sidecar-handoff <bundle>`
  - Current review behavior:
    - sidecar bundle is optional; omitting it preserves the old zero-config AQ
      review path
    - JSON review now exposes:
      - `sidecar_handoff_status`
      - `sidecar_missing_artifact_kinds`
      - merged sidecar `usage_warnings` in `notes`
    - `--human` now emits a compact `sidecar_status=<...>` field
  - Verification planned for this bridge:
    - `cargo test review_surfaces_sidecar_handoff_readiness_when_explicitly_provided -- --nocapture`
    - `cargo test test_cli_auto_quant_setup_commands_use_extracted_args -- --nocapture`
    - `cargo fmt --check`
