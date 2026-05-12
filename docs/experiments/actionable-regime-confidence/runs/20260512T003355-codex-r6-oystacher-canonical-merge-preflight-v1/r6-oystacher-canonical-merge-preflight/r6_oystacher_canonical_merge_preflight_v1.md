# R6 Oystacher Canonical Merge Preflight v1

- Run id: `20260512T003355-codex-r6-oystacher-canonical-merge-preflight-v1`.
- Isolated verifier status: `schema_ready_unscored`; positives `5182`; matched controls `1553`; matched groups `1313`.
- Technical preflight pass: `true`.
- Split axes pass: `true`; minimum split Wilson95 LCB `0.95771100465`.
- Source policy gate: `false`; canonical merge allowed: `false`.
- Owner target root exists: `false`; owner target mutated: `false`.
- Gate result: `r6_oystacher_canonical_merge_preflight_v1=technical_preflight_pass_policy_approval_required_no_canonical_mutation`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Checklist

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `isolated_verifier_ready` | `pass` | returncode=0; status=schema_ready_unscored; positives=5182; controls=1553 |  |
| `verifier_native_files_present` | `pass` | positive_spoofing_layering_rows.csv=True; matched_negative_normal_activity_rows.csv=True; provenance_manifest.json=True |  |
| `headers_match_verifier_contract` | `pass` | field_count=17; contract_rows=3 |  |
| `split_axes_pass` | `pass` | axes=17; min_split_wilson95_lcb=0.95771100465 |  |
| `source_policy_approval` | `blocked` | source_policy_gate=False; policy_gate_result=r6_oystacher_exhibit_a_source_policy_review_v1=row_evidence_strong_policy_approval_required_before_canonical_merge | explicit board/user approval for RECAP/PACER source provenance and FLIP controls |
| `canonical_target_untouched` | `pass_guardrail` | owner_target_exists=False; live_root_exists=True |  |
| `downstream_chain_not_rerun` | `blocked_not_rerun` | No canonical merge or policy approval; downstream readback would not cover accepted R6 evidence. | approval plus canonical merge |

## Interpretation

- The Oystacher Exhibit A rows are technically ready as an isolated verifier-native intake.
- The canonical merge is still blocked only by explicit policy/owner approval for public RECAP/PACER provenance and same-exhibit `FLIP` rows as controls.
- No canonical root, live root, threshold, runtime code, or downstream chain state was mutated by this preflight.

## Next

If the user/board approves RECAP/PACER Exhibit A provenance and FLIP rows as matched controls, copy the isolated verifier-native intake into /tmp/ict-engine-board-a-r6-owner-export-v1 under a shared lock, rerun direct verifier/split calibration, then rerun provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.
