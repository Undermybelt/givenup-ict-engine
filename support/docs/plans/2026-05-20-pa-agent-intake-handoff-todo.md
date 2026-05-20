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

## Verification log
- `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests.
- `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-zero` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`.
- `python3 support/scripts/research/pa_agent_intake.py --compact --pa-agent-root /Users/thrill3r/Downloads/PA_Agent --include-prompt-inventory --output-dir /tmp/ict-engine-pa-agent-intake-optin` -> `status=ok trade_usable=false mode=opt_in taxonomy=9 rules=7`.
- Artifact inspection: zero-config and opt-in bundles both have `trade_usable=false`; no `/Users/` or `Downloads` leaked into generated JSON.
- Local macOS permission note: direct script read of the Downloads PA_Agent source was blocked by host permissions; artifact records `source_access_warnings=[schemas.py_unreadable, router.py_unreadable]` and safely falls back to embedded defaults.
- `python3 -m py_compile support/scripts/research/pa_agent_intake.py support/scripts/research/tests/test_pa_agent_intake.py` -> OK.
- `python3 -m ruff check ...` blocked because this Python has no `ruff` module installed.

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