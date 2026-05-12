# Normalized LTF Tomac Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-ltf-tomac-normalized-20260512T040232+0800`

This is an append-only readback of the agent-selected LTF follow-up for Board B. It does not edit the Board B Current Cursor and does not satisfy the workflow's explicit `user_selected_historical_data` gate.

## Command Results

| Command | Exit | Evidence |
|---|---:|---|
| `00_normalize_workspace` | 0 | `command-output/00_normalize_workspace.exit` |
| `01_run_tomac_normalized` | 0 | `command-output/01_run_tomac_normalized.out`, `command-output/01_run_tomac_normalized.err` |

## Readback

- Root cause of the prior synthetic `No pair in whitelist` failure was the generated pair string containing underscores. FreqTrade's `expand_pairlist(..., keep_invalid=True)` drops pairs with `_`, leaving an empty whitelist.
- The normalized sidecar copied the prepared B2R feathers to `NQ_USD-{1h,4h,1d}.feather` and used `NQ/USD` in `config.tomac.json`.
- FreqTrade then loaded the local NQ data and ran `TomacNQ_KillzoneBreakout` successfully.
- The measured result was still not useful for branch maturation: `0` trades, `0.0000` Sharpe, `0.0000` total profit, and `0.0000` win rate.
- The backtestable window after startup was only `2025-12-25 22:00:00` to `2025-12-31 21:00:00`, so this sidecar creates no mature branch observations and no downstream promotion evidence.

## Decision

Gate: `pass:pairlist_repaired;fail_closed:zero_trade_short_window`.

Promotion: `false`.

Next: keep `034002/downstream-combined-v1` as the current fail-closed cursor. A true next attempt still needs explicit historical dataset selection plus a measured nonzero Auto-Quant packet before running Pre-Bayes / BBN / CatBoost / execution-tree promotion checks.
