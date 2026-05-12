# Current Objective Audit After R3 TSIE Quarantine v1

Run id: `20260512T063906+0800-codex-current-objective-audit-after-r3-tsie-quarantine-v1`

Gate result: `current_objective_audit_after_r3_tsie_quarantine_v1=not_complete_tsie_root_present_policy_quarantined_no_unlock`

Readback:
- R3 target path present: `True`.
- R3 physical rows from TSIE materialization: `5032903`.
- Physical mapping labels: `Bear, Bull, Sideways`.
- R6 owner/export root present: `False`.
- R5 recency root present: `False`.

Decision:
- The TSIE root is present but policy-quarantined by the current board ledger.
- It does not count as an R3 unlock, accepted Board A evidence, canonical merge input, downstream promotion evidence, or trade evidence.
- Board A accepted rows added remains `0` for this TSIE branch; `update_goal=false`.

Next:
- Treat the TSIE root as quarantined/proxy evidence only. Replace it with explicit source/control-approved R3 MainRegimeV2 labels or obtain R6 owner/export controls, source-owned R5 recency, or a genuine Crisis-capable source packet before canonical merge and downstream readback.
