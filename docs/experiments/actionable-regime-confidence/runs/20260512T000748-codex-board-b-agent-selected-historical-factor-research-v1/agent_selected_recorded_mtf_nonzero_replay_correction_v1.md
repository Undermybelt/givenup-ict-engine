# Agent-Selected Recorded MTF Replay Correction v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1`

This is an additive correction to the earlier `000748` board row. The board cursor had already advanced to `20260512T002020+0800-codex-board-b-220646-branch-path-closure-readback-v1` before this note was written, so this packet does not supersede the active cursor.

## Data And Auto-Quant Replay

- The original blocker was real: `auto-quant-prepare` and the first `uv run run.py` path failed because FreqTrade tried to reach Binance `exchangeInfo` while DNS was unavailable.
- The run-local recorded profile already existed at `.deps/auto-quant/profile_source.csv`.
- `prepare_external.py` converted the profile into local `BTC_USDT-{1h,4h,1d}.feather` files with exit `0`.
- `run_offline_recorded_mtf.py` patched only FreqTrade market loading and buy-and-hold date normalization, then delegated to unchanged Auto-Quant `run.py`.
- The successful replay log is `logs/11_auto_quant_run_recorded_mtf_offline_bah_fixed.out` with `3` succeeded and `0` failed.

## Measured Candidates

| strategy | trades | sharpe | total_profit_pct | max_drawdown_pct | win_rate_pct | profit_factor | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `RegimeTrendCarry` | 17 | 1.6185 | 1.3200 | -0.5729 | 35.2941 | 2.1478 | fail:profit_floor |
| `RegimeVolBreakout` | 13 | 1.1948 | 1.1000 | -0.8667 | 23.0769 | 2.0124 | fail:profit_floor |
| `RegimeRsiRelief` | 2 | -0.3119 | 0.0000 | -0.0092 | 50.0000 | 0.4627 | fail:profit_floor |

Buy-and-hold over the same recorded window was stronger (`bah_profit_pct=26.4758`, `bah_sharpe=10.4942`), so this is nursery evidence only.

## Downstream Readback

- `auto-quant-results-import` imported the manifest with `n_ok=3`.
- `auto-quant-prior-init` consumed only `RegimeTrendCarry`; BBN evidence-value gate passed, but the posterior moved to mixed win/loss probabilities (`[0.55998592, 0.00000704, 0.44000704]`) from `6` wins and `11` losses.
- `pre-bayes-status --refresh` exited `0` but returned no active bridge or policy.
- `policy-training-status` exited `0`; entry models had `matched_rows=0`.
- `export-structural-path-ranking-target` emitted one bootstrap target row.
- `apply-structural-path-ranking-external-scores`, trainer registration, and runtime enable all exited `0`; runtime consumed one candidate-set score (`runtime_matches=1`, `raw_path_score=0.6185`).
- `workflow-status --phase execution-candidate --agent` remained `ready=false`, `review_status=observe`, `path_ranker_raw_score=0.6185`, with no Pre-Bayes gate or workflow snapshot.

## Decision

`000748` should be corrected from zero-trade failure to `pass:auto_quant_replay_and_downstream_readback_executed; fail_closed:nursery_only_profit_floor_and_downstream_not_ready`.

Promotion remains blocked because:

- the best Auto-Quant candidate fails the profit-floor gate and underperforms buy-and-hold on the recorded path;
- Pre-Bayes has no policy/bridge;
- path-ranker consumed the raw score but has `0/30` mature / production / observation rows;
- execution-candidate is observe-only and not ready.
