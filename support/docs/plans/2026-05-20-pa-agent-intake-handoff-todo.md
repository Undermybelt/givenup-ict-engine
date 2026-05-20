# PA Agent intake handoff TODO — 2026-05-20

## Contract
- Goal: absorb PA_Agent price-action structure into ict-engine without making it runtime authority.
- Must stay zero-config, consumer-usable, token-friendly, hot-pluggable, no pollution, no debt.
- PA_Agent evidence remains observation-only until ict-engine gates promote it.

## Current claim
- Owner: Hermes GPT-5.5 CLI.
- Scope: add PA Agent intake artifact generator, tests, example hotplug profile, and handoff.
- Route: `sd/ict-engine-surface-intgr`.
- Safety: stage only current-slice files; preserve broad dirty tree.

## TODO
- [x] Review PA_Agent surfaces and identify absorbable contracts.
- [x] Add zero-config intake generator with embedded defaults.
- [x] Support opt-in `--pa-agent-root` source parsing.
- [x] Support opt-in `--profile` hotplug override.
- [x] Emit token-friendly `--compact` line.
- [x] Emit artifact bundle, taxonomy, trace schema, router rules, and candidate-pack template.
- [x] Add tests for zero-config, opt-in source, and profile override.
- [x] Run focused unit tests.
- [x] Run zero-config compact smoke.
- [x] Run opt-in PA_Agent-root compact smoke.
- [x] Inspect generated artifacts for trade_usable=false and no default private path leak.
- [x] Commit only this coherent slice if verification passes.
- [x] Add token-friendly `artifact_index.json` with relative artifact names only.
- [x] Run focused tests for artifact index slice.
- [x] Run compact smoke and inspect index for no private path leak.
- [x] Commit artifact-index slice if verification passes.
- [x] Add consumer discovery docs pointing to `artifact_index.json`.
- [x] Verify docs have no private path leak and commands still smoke.
- [x] Commit consumer-doc slice if verification passes.
- [x] Add the PA Agent intake consumer entry to the top-level docs map.
- [x] Verify top-level docs map privacy and focused intake smoke.
- [x] Commit docs-map slice if verification passes.

## Verification log
- `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests.
- `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-zero` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`.
- `python3 support/scripts/research/pa_agent_intake.py --compact --pa-agent-root /path/to/PA_Agent --include-prompt-inventory --output-dir /tmp/ict-engine-pa-agent-intake-optin` -> `status=ok trade_usable=false mode=opt_in taxonomy=9 rules=7`.
- Artifact inspection: zero-config and opt-in bundles both have `trade_usable=false`; no private absolute paths leaked into generated JSON.
- Local permission note: direct script read of an opt-in PA_Agent source may be blocked by host permissions; artifact records `source_access_warnings=[schemas.py_unreadable, router.py_unreadable]` and safely falls back to embedded defaults.
- `python3 -m py_compile support/scripts/research/pa_agent_intake.py support/scripts/research/tests/test_pa_agent_intake.py` -> OK.
- `python3 -m ruff check ...` blocked because this Python has no `ruff` module installed.
- Artifact index slice: `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests.
- Artifact index smoke: `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-index` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`; emitted `artifact_index.json`.
- Artifact index inspection: `trade_usable=false`, `taxonomy_count=9`, artifact names are relative, no private absolute path leakage.
- Artifact index py_compile: `python3 -m py_compile support/scripts/research/pa_agent_intake.py support/scripts/research/tests/test_pa_agent_intake.py` -> OK.
- Consumer docs slice: `support/examples/README.md` now lists `pa_agent_intake/` and the opt-in profile; `support/examples/pa_agent_intake/README.md` documents zero-config, local-source opt-in, profile opt-in, and observation-only output contract.
- Consumer docs privacy check: support examples README, PA Agent intake README, and this handoff contain no private absolute path markers; all point consumers to `artifact_index.json`.
- Consumer docs smoke: `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests; `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-doc-smoke` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`.
- Docs map slice: `support/docs/README.md` now links consumers to the PA Agent intake README and states the `artifact_index.json` / `trade_usable=false` boundary.
- Docs map privacy check: `rg -n '/Users/|Downloads' support/docs/README.md support/docs/plans/2026-05-20-pa-agent-intake-handoff-todo.md support/examples/pa_agent_intake/README.md support/examples/README.md || true` -> no matches.
- Docs map smoke: `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests; `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-docs-map-smoke` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`.
- Docs map index inspection: generated `artifact_index.json` has `trade_usable=false`, relative artifact names only, and no `/Users/` or `Downloads` leakage.
- Docs map diff check: `git diff --check -- support/docs/README.md support/docs/plans/2026-05-20-pa-agent-intake-handoff-todo.md` -> OK.

## Artifact plan
- Script: `support/scripts/research/pa_agent_intake.py`
- Tests: `support/scripts/research/tests/test_pa_agent_intake.py`
- Example hotplug profile: `support/examples/pa_agent_intake_profile.example.json`
- Default generated state: `/tmp/ict-engine-pa-agent-intake`

## Design notes
- Embedded defaults allow clean-checkout use without PA_Agent installed.
- `--pa-agent-root` is explicit opt-in for local PA_Agent parsing.
- Generated candidate pack is `inactive_by_default` and `candidate_observation`.
- Personal defaults encode 1m base plus 5m/15m/30m/1h/4h/1d context ladder and strict downstream gates.