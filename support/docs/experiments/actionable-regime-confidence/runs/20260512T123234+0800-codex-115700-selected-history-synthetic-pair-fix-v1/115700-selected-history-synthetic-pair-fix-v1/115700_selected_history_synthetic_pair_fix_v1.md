# 115700 Selected-History Synthetic Pair Fix v1

Run id: `20260512T123234+0800-codex-115700-selected-history-synthetic-pair-fix-v1`
Source run root: `docs/experiments/actionable-regime-confidence/runs/20260512T122600+0800-codex-115700-selected-history-factor-research-v1`

## Root Cause
- `run_tomac.py` originally failed under `uv run --with ta-lib` because that environment lacked `freqtrade`.
- Running with the Auto-Quant venv reached Freqtrade but failed with `No pair in whitelist` because `StaticPairList` uses `expand_pairlist(..., keep_invalid=True)`, which drops underscore-containing pairs.
- After the underscore-free alias was added, Freqtrade loaded the pair but found no data because the copied `config.tomac.json` timerange stopped at `20251231` while the selected-history data begins on `2026-04-01`.

## Isolated Fix
- Pair alias: `B2R-SAME-ROOT-SIX-PROVIDER-1H-AQ-115700/USD`.
- Timerange: `20260401-20260512`.
- Data files were copied inside this run root only, from the original underscore pair filenames to matching alias filenames.
- Repo runtime code was not changed.

## Auto-Quant Result
- Command exit: `0`.
- Strategies succeeded/failed: `3` / `0`.
- Total trades across strategies: `0`.
- `TomacAggressiveBE`: trades `0`, total_profit_pct `0.0000`, win_rate_pct `0.0000`, profit_factor `0.0000`.
- `TomacKillzoneBreakout`: trades `0`, total_profit_pct `0.0000`, win_rate_pct `0.0000`, profit_factor `0.0000`.
- `TomacRRWinRate`: trades `0`, total_profit_pct `0.0000`, win_rate_pct `0.0000`, profit_factor `0.0000`.

## Board A Decision
- This repairs the selected-history Auto-Quant execution path for this isolated BTC 1h packet.
- It does not produce a usable Auto-Quant recipe because all strategies generated zero trades.
- It does not add non-BTC instrument validation, non-1h cycle validation, direct Manipulation evidence, BBN >=95% confidence, CatBoost promotion, or execution readiness.
- `production_likelihood_mutation=false`; `promotion_allowed=false`; `trade_usable=false`; `update_goal=false`.

## Artifacts
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T123234+0800-codex-115700-selected-history-synthetic-pair-fix-v1/115700-selected-history-synthetic-pair-fix-v1/115700_selected_history_synthetic_pair_fix_v1.json`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T123234+0800-codex-115700-selected-history-synthetic-pair-fix-v1/checks/115700_selected_history_synthetic_pair_fix_v1_assertions.out`
- Command: `command-output/run_tomac_alias_timerange_fix.cmd`
- stdout/stderr/exit: `command-output/run_tomac_alias_timerange_fix.out`, `command-output/run_tomac_alias_timerange_fix.err`, `command-output/run_tomac_alias_timerange_fix.exit`
