# R6 JPM CBOT Treasury Control Uplift v1

- Run id: `20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1`
- Live mutation: `false` because the shared intake lock already existed.
- Selected JPM CBOT Treasury positive/control pairs in isolated projection: `4`.
- Baseline rows: `73/73`; projected rows: `77/77`.
- Projected verifier status: `schema_ready_unscored`, return code `0`.
- Projected pooled direct Wilson95 LCB: `0.952479911333`; pooled direct gate `true`.
- Sidecar broad-normal rows: `80`; sidecar axis gate `true`.
- Chronological split gate: `false`; heldout symbol gate: `false`; heldout venue gate: `false`.
- Gate result: `r6_jpm_cbot_treasury_control_uplift_v1=isolated_projection_ready_shared_lock_present_split_species_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Selected Rows

- `cftc_jpm_20090720_trader7_tbond_buy_layered_spoof` 2009-07-20 T-Bond Futures contract, September 2009 expiry
- `cftc_jpm_20100204_trader8_tnote_sell_spoof` 2010-02-04 10-Year T-Note Futures contract, March 2010 expiry
- `cftc_jpm_20110927_trader9_tnote_sell_spoof` 2011-09-27 10-Year T-Note Futures contract, December 2011 expiry
- `cftc_jpm_20150630_trader10_ultra_tbond_sell_spoof` 2015-06-30 Ultra T-Bond Futures contract, September 2015 expiry

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/r6_jpm_cbot_treasury_control_uplift_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/r6_jpm_cbot_treasury_control_uplift_v1.md`
- Selected positives: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/jpm_cbot_treasury_selected_positive_rows_v1.csv`
- Selected matched controls: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/jpm_cbot_treasury_selected_matched_controls_v1.csv`
- Projected positive snapshot: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/positive_spoofing_layering_rows_projected_v1.csv`
- Projected matched-control snapshot: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/matched_negative_normal_activity_rows_projected_v1.csv`
- Split metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/r6_jpm_cbot_treasury_split_metrics_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/checks/r6_jpm_cbot_treasury_control_uplift_v1_assertions.out`

## Next

When the shared lock clears, re-run this uplift against the live root or keep sourcing post-2017/non-spoofing direct species rows; do not mark Board A complete.
