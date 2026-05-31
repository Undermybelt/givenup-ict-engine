# Smoke Harness Binary Reuse - 2026-05-31

Owner: Codex
Route: `sd/ict-engine-maintenance-loop`
Status: verified slice / full objective not complete
Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
Branch: `main`
Observed HEAD: `a74576265a7f06b332155c95aae497df93b6dded`

## Context

The consumer UX / objective-closure audit still fails full completion. A heavy
done-definition packet at
`/tmp/ict-engine-done-definition-heavy-20260531T-after-source-scope-commit.json`
reported `9` passing gates and one failing heavy gate:
`smoke_acceptance_tmp_state`.

The smoke gate failed because `support/scripts/smoke_acceptance.sh` timed out
after `900s` at `update_demo`. The captured `update_demo.out` and
`update_demo.err` were both empty:

```text
/tmp/ict-engine-done-definition-audit-smoke-20260531T041204243248Z-68177-out/update_demo.out
/tmp/ict-engine-done-definition-audit-smoke-20260531T041204243248Z-68177-out/update_demo.err
```

Focused reproduction with an already-built binary proved the `update` command
itself is not the hang:

```bash
.local-artifacts/cargo-target/debug/ict-engine update --symbol DEMO --state-dir /tmp/ict-engine-update-demo-repro-20260531T-current-turn --outcome breakeven --pnl 0
```

The direct binary path completed in `0.603s` and wrote output. This points to
the smoke harness repeatedly invoking `cargo run` under shared concurrent cargo
load, not to the zero-config update workflow.

## Change

`support/scripts/smoke_acceptance.sh` now accepts:

```bash
ICT_ENGINE_BIN=/path/to/ict-engine
```

When set, the smoke harness reuses that executable for every probe. When unset,
the default remains the prior consumer-facing `cargo run --quiet -- ...`
behavior.

`support/scripts/SCRIPTS.md` documents this optional reuse path.

## Verification

Passed syntax check:

```bash
bash -n support/scripts/smoke_acceptance.sh
```

Passed full smoke with direct binary:

```bash
ICT_ENGINE_BIN=$PWD/.local-artifacts/cargo-target/debug/ict-engine \
STATE_DIR=/tmp/ict-engine-smoke-bin-20260531T-current-turn \
OUT_DIR=/tmp/ict-engine-smoke-bin-20260531T-current-turn-out \
bash support/scripts/smoke_acceptance.sh
```

Result:

```text
smoke_acceptance: passed state_dir=/tmp/ict-engine-smoke-bin-20260531T-current-turn output_dir=/tmp/ict-engine-smoke-bin-20260531T-current-turn-out
```

## Remaining Blockers

This is not objective completion evidence. Remaining blockers still include:

- heavy done-definition proof must be rerun successfully with current `HEAD`
  and current tracked-worktree fingerprint;
- `same_tree_practical_closure` is still unproven;
- factor closure is time-variant and has recently been blocked by live TOMAC
  processes;
- release readiness remains blocked by the dirty shared tree and selected-source
  origin alignment.

