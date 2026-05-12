# Provider NQ Entry Wire v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102828+0800-codex-board-a-provider-nq-entry-wire-v1`

Mode: `board_a_provider_owned_aq_signal_wiring_diagnostic_no_promotion`

## Scope

This packet tests the latest provider-owned Yahoo NQ Auto-Quant sidecar after the `102332` NQ trendpulse run showed thousands of offline signal hits but `0` Freqtrade trades. It does not edit Current Cursor, does not approve selected history or source/control evidence, does not run Pre-Bayes/BBN/CatBoost/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

## Source

- Source workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1/workspace/auto-quant-yf-nq-trendpulse`
- Upstream provider source: `docs/experiments/actionable-regime-confidence/runs/20260512T101833+0800-codex-board-b-provider-yahoo-nq-long-aq-preseed-v1/workspace/auto-quant-yahoo-nq-long`
- Copied data hash: `NQ_USD-1h.feather` SHA-256 `c549307d194379c0500f71b4908e4d5c6ecd5c090e69c8b46e14efac5bc14b82`
- Config change tested after baseline: `stake_amount` changed from `unlimited` to fixed `1000` inside the isolated run workspace only.

## Commands

- `00_probe_provider_nq_entry_wire_conditions`: exit `0`
- `01_run_provider_nq_entry_wire`: exit `0`
- `02_probe_provider_nq_forced_entry_conditions`: exit `0`
- `03_run_provider_nq_entry_wire_with_forced`: exit `0`
- `04_run_provider_nq_entry_wire_fixed_stake`: exit `0`
- `05_freqtrade_cli_forced_entry`: exit `2`

## Readback

The normal entry-wire canary produced offline signal evidence on the copied provider-owned NQ feathers: `11,086` rows, `10,691` nonzero-volume rows, `3,600` raw entries, `3,571` post-startup entries, `4,772` exits, and `3,171` post-startup entry rows without simultaneous exit.

The forced-entry canary then removed factor strictness as a blocker: it emitted `11,062` raw/post-startup entries and `10,140` post-startup entry rows without simultaneous exit.

Despite those signals, the in-process TOMAC runner completed with `0` trades for both `ProviderNqEntryWireCanary` and `ProviderNqForcedEntryCanary`. Replacing `stake_amount: unlimited` with fixed `1000` did not change the result: both strategies still completed with `0` trades.

The direct `freqtrade backtesting` CLI path was also tested and exited `2` because it attempted to load Binance market metadata and failed at DNS for `api.binance.com`. That confirms the CLI path is not a usable replacement for TOMAC in this isolated run without a local market-metadata bypass.

## Gate

- `pass:provider_owned_nq_feathers_reused_hash_matched`
- `pass:offline_entry_wire_canary_signals_present`
- `pass:offline_forced_entry_canary_signals_present`
- `pass:tomac_runner_exits_zero_for_signal_canaries`
- `fail_closed:tomac_signal_to_trade_conversion_zero_even_for_forced_entries`
- `fail_closed:freqtrade_cli_market_metadata_dns_blocked`
- `fail_closed:zero_trades_no_mature_rooted_branch_observations`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not keep loosening NQ factor thresholds on this TOMAC path. The next useful slice is a runner-level repair or replacement that proves Freqtrade consumes the emitted `enter_long` / `exit_long` signals into trades on cached provider data without remote exchange metadata, then reruns provider-owned AQ before any downstream promotion chain.
