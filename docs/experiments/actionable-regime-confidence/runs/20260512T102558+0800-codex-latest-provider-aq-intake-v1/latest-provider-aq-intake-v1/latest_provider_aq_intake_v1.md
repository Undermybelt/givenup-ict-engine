# Latest Provider/AQ Intake v1

Run id: `20260512T102558+0800-codex-latest-provider-aq-intake-v1`

Mode: `append_only_non_promoting_intake`

## Scope

This packet registers only the still-unregistered newest run roots visible after
`101623` without promoting them into Board A acceptance. It does not edit
Current Cursor, does not choose `HTF`, `MTF`, or `LTF`, does not approve selected
history, does not approve source/control evidence, does not mutate canonical
intake, does not promote Auto-Quant, BBN, CatBoost, path-ranking, or
execution-tree output, does not make a trade claim, and does not call
`update_goal`.

## Readback

- Board hash before packet creation: `1bdd072ff8c1a940734fbe240b277275f2f8b0fd65722484bf9d75ea1a7d9e50`
- Board hash after concurrent reread: `74d3a78e9f6fc8cff582318cdc921f87ff4304c82548c0fcde1dc955b6188e4b`
- Board hash before final writeback: `00e6e37e3900e4cfcd39eb7831be4943a82eaf6b14d07bca612a2d70f8ed3b50`
- Board hash after `102315` dedicated writeback: `2c0f51eba689303bd1c392d8c07c457d50a52c14a614828b8cd2ead441750119`
- Board hash after `102727` settled readback and `102828` provider-health writeback: `6265fc99d4a8ad42f5f4244660a454df05581a3e242b50c6c55bce2fa4f881ee`
- `101700`: empty run root at readback time; not counted as evidence.
- `101709`: concurrently registered in the board section `Supplemental 101709 / 101944 Provider-Owned NQ Repair Duplicate Guard v1`; do not count here.
- `101944`: concurrently registered in the board section `Supplemental 101709 / 101944 Provider-Owned NQ Repair Duplicate Guard v1`; do not count here.
- `102018`: concurrently registered in the board section `Supplemental 102018 Board A AQ Provider Authority Readback v1`; do not count here.
- `102315`: superseded by the later board section `Supplemental 102315 Yahoo NQ Long AQ Preseed Duplicate Guard v1`; do not count here.
- `102332`: provider Yahoo NQ trend-pulse TOMAC initially read back as stdout-complete with `0` trades; later `102727` settled readback found run exit `0` and probe exit `0`, still `0` trades.
- `102352`: provider BTC signal-canary TOMAC initially read back as stdout-complete with `0` trades; later `102727` settled readback found run exit `0`, still `0` trades.

## Evidence

- `101709` report/assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/provider-owned-aq-pair-timerange-repair-v1/provider_owned_aq_pair_timerange_repair_v1.md`, `docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/checks/provider_owned_aq_pair_timerange_repair_v1_assertions.out`
- `101944` command outputs/checks: `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/command-output/`, `docs/experiments/actionable-regime-confidence/runs/20260512T101944+0800-codex-board-b-provider-yf-alias-ms-repair-v1/checks/`
- `102018` provider matrix/status: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/board-a-aq-provider-authority-readback-v1/provider_matrix_v1.csv`, `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/command-output/08_auto_quant_status_after_prepare_retry.out`
- `102315` provider CSV/fetch output: `docs/experiments/actionable-regime-confidence/runs/20260512T102315+0800-codex-board-b-provider-yahoo-nq-long-aq-preseed-v1/provider-csv/yahoo_nq_f_1h_2y.csv`, `docs/experiments/actionable-regime-confidence/runs/20260512T102315+0800-codex-board-b-provider-yahoo-nq-long-aq-preseed-v1/command-output/00_fetch_yahoo_nq_f_1h_2y.out`
- `102332` TOMAC stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/command-output/00_run_provider_yf_nq_trendpulse.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/command-output/00_run_provider_yf_nq_trendpulse.err`
- `102352` TOMAC stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/command-output/00_run_provider_btc_signal_canary.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T102352+0800-codex-board-b-provider-btc-signal-canary-v1/command-output/00_run_provider_btc_signal_canary.err`

## Decision

Gate: `latest_provider_aq_intake_v1=102332_102352_count_once_settled_by_102727_no_promotion`.

The useful delta left after concurrent board writeback is limited to two TOMAC
zero-trade runs. `101709`, `101944`, `102018`, and `102315` are already
registered elsewhere in the board and are not counted by this packet. `102727`
is the settled gate authority for the `102332` and `102352` exit-code
refinement. No accepted regime packet was produced. No selected-history/source-
control unlock was produced. No mature rooted branch observations were
produced. No downstream promotion chain was run.

Accepted rows added: `0`

Promotion allowed: `false`

`update_goal=false`

## Next

Do not repeat these same Yahoo NQ/BTC zero-trade TOMAC shapes or provider-only
fetches. Continue with a changed branch-specific strategy that can produce
nonzero provider-owned observations, explicit selected-history approval, real
R6/R5/R3 source/control unlock, or a coordinated structural-feedback owner fix.
