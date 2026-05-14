# Source/Control Selected-History Poll After 082215 v1

Run id: `20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1`

Gate result: `source_control_selected_history_poll_after_082215_v1=no_new_required_root_no_selected_history_no_unlock`

## Scope

Read-only local arrival poll after `082215`. This checks required source/control roots,
the R6 approval package, and explicit user-selected historical path markers. It does not
approve partial intake roots, mutate canonical intake, run direct verifier/split
calibration, run selected-data AutoQuant, or run filter / Pre-Bayes -> BBN ->
CatBoost/path-ranking -> execution-tree promotion.

## Readback

- Board B hash at readback: `5c6ac88ee815355aec9a200405ca787a95070c85a7dfcb46904f4a1458cb3a98`
- Board A hash at readback: `a0128fc2a821dd7c9c978a0fc93d07ccdd54904479a67a5590ebca5cba02ffd6`
- R6 owner/export root present: `false` with files `0`
- R5 recency root present: `false` with files `0`
- R3 native-subhour root present: `true` with files `2`; `MainRegimeV2` hits `0`; Crisis hits `713`; matched-control hits `1`
- R6 approval package present: `true`
- R6 approval package gate: `r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge`
- Approval canonical merge allowed: `true`
- Approval downstream rerun allowed: `true`
- Explicit user-selected history marker found: `false`

## Decision

No new required source/control root or selected-history unlock arrived after `082215`.
R6 owner/export, R5 recency, and R3 native-subhour gates remain non-unlocking under the
current contract. The R6 approval package is present only as a decision package and does
not authorize canonical merge or downstream rerun.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3
native-subhour unlock false; valid required-root unlock false; source/control evidence
acquired false; explicit user-selected history false; canonical merge false;
selected-data AutoQuant promotion false; downstream promotion rerun false; strict full
objective false; trade usable false; `promotion_allowed=false`; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/source-control-selected-history-poll-after-082215-v1/source_control_selected_history_poll_after_082215_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/source-control-selected-history-poll-after-082215-v1/source_control_selected_history_poll_after_082215_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/checks/source_control_selected_history_poll_after_082215_v1_assertions.out`

## Next

Continue source/control acquisition only, or obtain exactly one explicit user-selected
historical path (`HTF`, `MTF`, or `LTF`) for non-promotional factor research. Do not run
selected-data AutoQuant or downstream promotion until both gates are satisfied.
