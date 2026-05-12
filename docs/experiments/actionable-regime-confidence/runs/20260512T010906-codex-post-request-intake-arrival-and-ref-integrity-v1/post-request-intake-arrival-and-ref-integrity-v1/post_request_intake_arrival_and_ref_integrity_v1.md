# Post-Request Intake Arrival and Reference Integrity v1

- Run id: `20260512T010906-codex-post-request-intake-arrival-and-ref-integrity-v1`.
- Gate result: `post_request_intake_arrival_and_ref_integrity_v1=partial_intake_files_present_schema_ready_no_confidence_no_promotion`.
- Required intake files present: `2/9`.
- Exact target-root required-file hits: `2`.
- Source rows present in arrived files: `248440`.
- Source-label equivalence verifier: `schema_ready_unscored` return code `0`.
- Recent board run references checked: `5`; broken refs: `0`.
- Broken recent run ids: `none`.
- External requests sent: false; source rows acquired: `0`; accepted rows added: `0`.
- Canonical merge allowed: false; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.
- Strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Boundary

This readback is presence/integrity evidence only. It does not create, copy, repair, or promote any intake files.

## Next

Acquire or approve the exact source-owned R6/non-R6 files, then rerun the fail-closed verifiers in Board A order. The missing recent board reference should be repaired by the owner of that artifact or superseded by a present replacement before relying on it.
