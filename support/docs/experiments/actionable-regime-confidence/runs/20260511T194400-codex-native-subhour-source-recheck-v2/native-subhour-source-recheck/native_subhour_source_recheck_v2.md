# Native Subhour Source Recheck v2

- Decision: `native_subhour_source_recheck_v2=no_ready_native_subhour_source_owned_labels`
- Kaggle queries: `4`
- Hugging Face queries: `5`
- GitHub queries: `4`
- Candidate records: `11`
- Ready native sub-hour source-owned label sources: `0`
- Accepted rows added: `0`
- New confidence gate: `false`
- Strict full objective achieved: `false`; `update_goal=false`

Disposition summary:
- `blocked_code_or_signal_surface_not_source_owned_labels`: `4`
- `blocked_generated_or_model_derived_regime_labels`: `4`
- `blocked_raw_provider_panel_no_source_owned_regime_labels`: `1`
- `blocked_research_code_or_prediction_target_not_owner_approved_labels`: `1`
- `blocked_synthetic_panel_not_source_owned_labels`: `1`

No raw rows were downloaded or committed. HMM/classifier datasets, raw
provider panels, synthetic panels, bots, and research-code surfaces remain
fail-closed for Board A native sub-hour source-label validation.
