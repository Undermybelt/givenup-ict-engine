# Regime Bundle BBN Assignment v1

Board B code-level readback for the regime consumer bundle assignment path.

## Scope

- No selected-data Auto-Quant run.
- No canonical merge.
- No downstream promotion rerun.
- No Current Cursor edit.
- No `update_goal`.

## Change Readback

- `RegimeConsumerBundleAdapter::path_ranker_assignment_entries` now keeps the existing JSON/count branch-path assignments and also expands the primary rooted branch path into direct Pre-Bayes assignment keys.
- Direct assignment keys are:
  - `regime_profit_branch_path`
  - `parent_regime_root`
  - `main_regime`
  - `sub_regime`
  - `sub_sub_regime_or_profit_factor`
  - `profit_factor`
- The focused regression proves the same direct assignments survive through `belief_evidence_packet_from_pre_bayes_filter` into `BeliefEvidencePacket.evidence_assignments`.

## Verification

- RED: `CARGO_TARGET_DIR=/tmp/ict-engine-codex-regime-bundle-bbn-target cargo test single_branch_path_survives_pre_bayes_into_bbn_assignments --test regime_consumer_bundle_adapter -- --nocapture`
  - Result before adapter expansion: failed as expected with missing `regime_profit_branch_path` assignment.
- GREEN focused: same command after adapter expansion.
  - Result: `1 passed; 0 failed; 17 filtered out`.
- Related integration file: `CARGO_TARGET_DIR=/tmp/ict-engine-codex-regime-bundle-bbn-target cargo test --test regime_consumer_bundle_adapter -- --nocapture`
  - Result: `18 passed; 0 failed`.
- Formatting check: `rustfmt --edition 2021 --check src/application/regime/consumer_bundle_adapter.rs tests/regime_consumer_bundle_adapter.rs`
  - Result: exit `0`.

## Gate

- `diagnostic_only:regime_bundle_bbn_assignment_wiring`
- `pass:single_branch_path_survives_pre_bayes_into_bbn_assignments`
- `pass:regime_consumer_bundle_adapter_integration_18_passed`
- `pass:rustfmt_check_targeted_files`
- `fail_closed:no_selected_data_auto_quant_training`
- `fail_closed:no_nonzero_mature_rooted_selected_observations`
- `blocked:user_selected_historical_data_missing`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Count this only as Pre-Bayes/BBN assignment wiring evidence. Board B still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, then selected-data Auto-Quant/factor-research with nonzero mature rooted branch observations before promotion can advance.
