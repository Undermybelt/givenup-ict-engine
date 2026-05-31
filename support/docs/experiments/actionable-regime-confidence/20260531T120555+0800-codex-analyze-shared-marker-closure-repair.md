# Analyze Shared Marker Closure Repair

- Created: 2026-05-31T12:05:55+08:00
- Owner: codex-analyze-shared-marker-closure-repair
- Repo: ict-engine checkout root
- Branch: main
- Workdoc: `/tmp/ict-engine-analyze-shared-marker-closure-repair-20260531T120555+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T120555+0800-codex-analyze-shared-marker-closure-repair.claim`
- Status: terminalized verified source/test repair; no provider, IBKR historical, AutoQuant, Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, or local backtest launch.

## Objective

Repair the same marker-only practical-closure loophole in `src/analyze_shared.rs`.
This owner persists execution candidates from analyze paths; it must not keep a
same-root execution-tree admission actionable merely because arbitrary
`same_tree_practical_closure_validated=true` or `evidence_packet_validated=true`
markers are present.

## TDD Route

- Mode: auto
- Decision: strict
- Reason: analyze persistence affects execution candidate artifacts and
  same-root duplicate/veto handling.
- Verification: add/confirm RED for marker-only admission, patch canonical
  helper, then rerun focused analyze-shared tests.

## Current Constraints

- Compact audit currently reports one live TOMAC/AQ process under `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
- This slice will not launch runtime work.
- promotion_allowed=false
- trade_usable=false
- update_goal=false
- same_tree_practical_closure=null

## Evidence Log

- 2026-05-31T12:13:xx+08:00: RED confirmed with `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-analyze-shared-marker-repair-20260531T120555 cargo test same_root_admission_practical_closure_rejects_marker_only_packet -- --nocapture`; expected failure was `assertion failed: !same_root_admission_practical_closure_validated(&admission)`.
- 2026-05-31T12:20:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-analyze-shared-marker-repair-20260531T120555 cargo test same_root_admission_practical_closure -- --nocapture` passed `2 passed; 0 failed`.
- 2026-05-31T12:23:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-analyze-shared-marker-repair-20260531T120555 cargo test execution_candidate_ -- --nocapture` passed the targeted analyze-shared execution-candidate tests, including same-root actionable, duplicate discard, observe-only, and trace-path preservation paths.

## Terminal Readback

- terminal_status: `terminalized_verified_code_repair_no_runtime_launch`
- Decision: analyze execution-candidate persistence now uses structured `same_tree_practical_closure` packet validation rather than marker-only booleans.
- Positive pass path: a structured packet with `status=pass`, `deploy_ready=true`, correct readiness contract, accepted execution feedback chain, nonempty evidence packet, and evidence validation preserves same-root actionable behavior.
- promotion_allowed=false
- trade_usable=false
- update_goal=false
- same_tree_practical_closure: not produced by this slice
- Remaining full-goal status: not complete; this closes the analyze persistence marker-only loophole only.
