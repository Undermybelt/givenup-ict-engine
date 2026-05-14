# Source Label ExtraTrees Threshold Screen v1

Run id: `20260512T045830-codex-source-label-extra-trees-threshold-screen-v1`

Gate result: `source_label_extra_trees_threshold_screen_v1=terminated_no_terminal_screen_no_promotion`

## Readback

- The ExtraTrees threshold screen was launched against the existing source-label equivalence package.
- The run exceeded the useful diagnostic window without producing JSON/report/gates/candidates artifacts.
- The Python worker was terminated by this agent to avoid blocking the lane and to avoid colliding with other active qualifier writers.
- Command exit: `143`.
- Stdout bytes: `0`.
- Stderr contains only dependency download/install lines from the isolated `uv` environment.

## Decision

Do not count this run as model-screen evidence. It produced no scored rows, no accepted labels, no gates CSV, and no stable candidate output.

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired false, new confidence gate false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Boundary

This fail-closed readback does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.
