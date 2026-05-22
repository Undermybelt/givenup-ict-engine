# Zero-Config Closed-Loop Smoke Handoff TODO

Updated: 2026-05-22 18:25 +0800.

## Contract

- Keep first-run behavior zero-config: no required profile, credentials, or
  maintainer-local dataset.
- Keep state and smoke outputs outside the repo by default under `/tmp`.
- Keep consumer overrides explicit and hot-pluggable:
  - `STATE_DIR`
  - `OUT_DIR`
  - `SYMBOL`
  - `SMOKE_UPDATE_OUTCOME`
  - `SMOKE_UPDATE_PNL`
- Treat the default `SMOKE_UPDATE_OUTCOME=breakeven SMOKE_UPDATE_PNL=0` as
  smoke-only feedback. It proves update/writeback mechanics, not trade quality.

## Current Evidence

- Fresh manual audit root:
  `/tmp/ict-engine-closed-loop-privacy-audit-20260522T1800Z`.
- Asserted smoke root:
  `/tmp/ict-engine-smoke-acceptance-asserted-update-20260522T1825Z`.
- `support/scripts/smoke_acceptance.sh` now runs:
  - `provider-status --compact`
  - empty `workflow-status --human`
  - `analyze --demo --human`
  - `workflow-status --refresh --agent`
  - `pre-bayes-status --refresh --output-format json`
  - `update --outcome "$SMOKE_UPDATE_OUTCOME" --pnl "$SMOKE_UPDATE_PNL"`
  - after-update `workflow-status --refresh --agent`
  - after-update `policy-training-status --output-format agent`
- Built-in smoke assertions now require:
  - update output has `feedback_records_applied=1`
  - update output preserves `SMOKE_UPDATE_OUTCOME`
  - after-update workflow reports `source_phase=update`
  - policy training reports `update_runs=1`
  - output privacy scan has no `/Users`, key, secret, token, or password match

## Verified

- `bash -n support/scripts/smoke_acceptance.sh` passed.
- `python3 -m unittest support.scripts.tests.test_smoke_acceptance -v`
  passed 3/3.
- `STATE_DIR=/tmp/ict-engine-smoke-acceptance-asserted-update-20260522T1825Z OUT_DIR=/tmp/ict-engine-smoke-acceptance-asserted-update-20260522T1825Z/smoke-output bash support/scripts/smoke_acceptance.sh`
  passed.
- `python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-done-definition-audit-light-after-smoke-assertions.json`
  passed with `summary.status=pass`, `pass_count=4`, `fail_count=0`,
  `skip_count=4`, `unresolved=[]`.

## Not Done

- Not a release-ready claim.
- Not a trade-ready claim.
- Structural path-ranker runtime is still disabled/not ready in DEMO smoke:
  mature validation remains `0/30`.
- DEMO `breakeven` feedback is intentionally synthetic smoke feedback.

## Next TODO

- [ ] Decide whether release gating treats fail-closed structural path-ranker
  runtime as acceptable for zero-config DEMO, or requires a separate seeded
  validation fixture.
- [ ] If a seeded validation fixture is required, design it as opt-in test data,
  not a hidden default consumer dataset.
- [ ] Re-run heavy Done Definition gates after the next code slice touching
  workflow, update, or policy-training surfaces.
- [ ] Keep personal/provider profile examples opt-in and clearly separate from
  the zero-config public path.
