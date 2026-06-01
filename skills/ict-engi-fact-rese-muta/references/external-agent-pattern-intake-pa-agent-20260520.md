# External agent pattern intake: PA_Agent -> ict-engine (2026-05-20)

## Durable lesson
When importing ideas from an external agent/research repo into ict-engine, treat the repo as a source of observable patterns, not executable strategy. The default product should be a compact, local, observation-only artifact set that downstream code can inspect explicitly.

## Useful shape
- Keep runtime opt-in: no default provider, strategy, cron, or live-trading path is enabled by intake.
- Preserve source boundary: record the upstream root/profile only as metadata; do not bake private absolute paths into committed docs.
- Emit a consumer entrypoint: `artifact_index.json` should be the first file future agents/tools read.
- Emit a compact profile example: e.g. `pa_agent_intake_profile.example.json` for optional external-source/profile overrides.
- Mark all derived trading signals as `trade_usable=false` until ict-engine gates prove otherwise.
- Prefer embedded defaults for smoke/replay so the intake tool works without the external repo present.

## ict-engine implementation pattern observed
The PA_Agent intake landed as support artifacts, not live runtime wiring:
- `support/scripts/research/pa_agent_intake.py`
- `support/scripts/research/tests/test_pa_agent_intake.py`
- `support/examples/pa_agent_intake/artifact_index.json`
- `support/examples/pa_agent_intake/README.md`
- `support/examples/pa_agent_intake_profile.example.json`
- `support/docs/plans/2026-05-20-pa-agent-intake-handoff-todo.md`

## Verification pattern
Use a bounded proof before declaring the intake usable:
- unit test the parser/intake script;
- run zero-config smoke with embedded defaults;
- verify output reports `status=ok` and `trade_usable=false`;
- run docs privacy scan for private absolute paths;
- run whitespace/diff sanity checks before committing.

Known verification from the session:
- `python3 -m unittest support.scripts.research.tests.test_pa_agent_intake` -> OK, 3 tests
- `python3 support/scripts/research/pa_agent_intake.py --compact --output-dir /tmp/ict-engine-pa-agent-intake-doc-smoke` -> `status=ok trade_usable=false mode=embedded_defaults taxonomy=9 rules=7`
- docs privacy scan passed for support examples README, PA Agent intake README, and handoff doc

## Consumer docs pitfall
Do not only commit raw artifacts. Add a discoverable consumer README that tells future agents:
1. start from `artifact_index.json`,
2. use `--pa-agent-root` only when intentionally opting into the local source tree,
3. use `--profile` only when intentionally applying a profile,
4. keep the output observation-only until the normal ict-engine Gate 1/cost/downstream gates admit it.
