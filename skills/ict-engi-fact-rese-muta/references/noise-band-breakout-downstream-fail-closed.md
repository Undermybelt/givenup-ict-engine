# Noise-band breakout Gate 1 -> downstream fail-closed pattern

## Context

Use this reference when a VWAP/session-noise-band breakout factor produces positive low-timeframe Auto-Quant rows and the user asks to continue through the full ict-engine chain.

Representative packet:

- Branch: `TrendExpansion -> NoiseBandBreakout -> vwap_noise_band_breakout -> vwap_noise_band_breakout_yf_qqq_1m_mtf_v1`
- Provider: yfinance/YF `QQQ`
- Ladder: `1m/5m/15m/30m/1h`
- Gate 1: `5` AQ rows, `3` positive, `24` total trades
- Downstream: AQ import, BBN prior init, analyze, Pre-Bayes/filter, structural target export, CatBoost/path-ranker train/apply/register/enable, execution-tree readback all exited `0`
- Result: path-ranker visible/used, but execution stayed fail-closed: `execution_candidate_actionable=false`, `candidate_status=no_trade`, `execution_tree_gate_status=observe`, `execution_tree_branch=transition_guardrail`, `ranker_validation_ready=false`, `mature_rows=0`, `rows_with_training_weight=0`

## Durable rule

A positive noise-band Gate 1 row set is not enough for promotion when trade density and maturity are thin. If downstream mechanics all run but execution remains `observe/transition_guardrail`, classify as:

`gate1_candidate_downstream_fail_closed`

Preserve it as scoped subclass evidence, not live readiness.

## Practical next step

Do not force this exact branch live or rerun CatBoost blindly. Prefer one of:

1. denser source-backed noise-band variant with more trades at the 1m/5m origin;
2. sibling symbol/provider validation with the same branch contract;
3. a cost-aware or turnover-reduced variant if low-timeframe rows are positive but fragile.

## Script pitfall

Some downstream helper scripts have a hardcoded `SOURCE` run root. If reusing them for a newer Gate 1 run, either patch `SOURCE` explicitly or load the script as a module and override `SOURCE`, `ROOT`, `STATE`, `MATERIALS`, `CMD`, `CHECKS`, `SUMMARIES`, `MODEL_DIR`, and `SCORES` before calling `main()`. Do not let an old hardcoded source produce stale downstream evidence.

## Classification checklist

- Provider rows real and `local_cache_replay=false` or explicitly marked.
- Branch fields preserved in AQ material/rank rows.
- Positive AQ rows have enough trades for the claimed scope.
- Downstream command exits are inspected, not inferred.
- Execution tree branch and readiness are read back after path-ranker enablement.
- If `mature_rows=0` or `rows_with_training_weight=0`, mark fail-closed/incubate even when path-ranker is visible and used.
