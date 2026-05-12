# Current Public Regime Dataset Scout v1

Decision: `current_public_regime_dataset_scout_v1=current_public_candidates_found_but_not_accepted`.

Result:
- Public candidate datasets downloaded to `/tmp`: `2`.
- Current rows were found, but no Board A intake files were created.
- The NIFTY candidate has row-level labels through `2026-03-20`, but its own metadata identifies HMM-based labels and the observed taxonomy is not MainRegimeV2.
- The macro/asset candidate is a feature panel through `2026-02-25`; no source regime label columns were observed.
- Accepted rows added: `0`; new confidence gate: `false`; `update_goal=false`.

Next:
- Keep the v35 outbox as the controlling next action: acquire source-owned or owner-approved rows/provenance for the existing intake roots, then rerun the fail-closed verifiers.
