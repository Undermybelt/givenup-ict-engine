# 110250 Provider-Matrix Root Readback v1

Readback time: 2026-05-12T11:10:19+0800

## Scope

This readback checks whether the Board A referenced root
`docs/experiments/actionable-regime-confidence/runs/20260512T110250+0800-codex-board-b-104703-provider-matrix-tomac-v1`
exists as a repo-local artifact.

## Evidence

- Candidate root listing:
  `docs/experiments/actionable-regime-confidence/runs/20260512T111019+0800-codex-110250-provider-matrix-root-readback-v1/command-output/00_find_candidate_roots.out`
- Exact root existence check:
  `docs/experiments/actionable-regime-confidence/runs/20260512T111019+0800-codex-110250-provider-matrix-root-readback-v1/checks/01_test_110250_root.exit`

## Result

- The candidate root listing found `104703`, `105245`, `105445`, `110211`, `110221`, `110224`, and this `111019` readback root.
- The exact `110250` provider-matrix TOMAC root was not present.
- The exact root existence check exited `1`.

## Decision

`110250` must not be treated as artifact-backed evidence unless the missing root is later materialized and re-read. This does not change any promotion gate by itself; it only prevents a missing path from being used as proof.

Net Board A effect remains unchanged: accepted rows added `0`, mature rooted branch observations promoted `0`, source/control evidence acquired false, explicit selected-history false, canonical merge false, selected-data AutoQuant promotion false, downstream promotion false, strict full objective false, trade usable false, promotion allowed false, and `update_goal=false`.
