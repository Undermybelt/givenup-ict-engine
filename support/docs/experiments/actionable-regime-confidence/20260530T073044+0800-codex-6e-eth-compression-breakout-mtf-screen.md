# 6E ETH Compression Breakout MTF Screen

Created: 2026-05-30T07:30:44+0800
Owner: codex-6e-eth-compression-breakout-mtf-20260530T073044+0800

## Goal

Create a non-colliding profitability-factor training packet while the shared
Auto-Quant/provider runtime is occupied by fresh Board B claims. This lane is a
local retained-data screen only. It must not claim `promotion_allowed=true`,
`trade_usable=true`, or `update_goal=true` without later provider/AQ/paper and
downstream same-tree closure.

## Branch Hypothesis

- factor_id_prefix: `6e_eth_compression_breakout_mtf`
- branch_path: `RangeConsolidation -> VolatilityCompression -> CompressionBreakoutContinuation -> 6e_eth_compression_breakout_mtf_range_consolidation_squeeze_breakout_v1`
- instrument: `6E` EUR futures from TOMAC GLBX retained CSV
- origin timeframe: `1m`
- context ladder: `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`

盈利方式：只在 6E full retained session 内寻找波动压缩后的顺势突破。
1m 负责触发，5m/15m/30m/1h/4h/1d 由 runner 从同一 1m retained source 重采样
形成多周期上下文。当前不启动 Auto-Quant；若本地筛选没有 5bps/side 成本后
生存者，就直接终端化为非实战。

## Collision Readback

Same-turn compact audit before this packet reported a live NQ volatility-
contraction AutoQuant/runtime owner under
`/private/tmp/ict-engine-tomac-nq-volatility-contraction-trend-quality-cont-20260530T071803+0800`.
Therefore this lane uses only `--skip-aq` local screening and does not touch
provider, IBKR, Auto-Quant, Freqtrade, paper/sim, or lifecycle downstream.

## Artifacts

- tmp workdoc: `/tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/workdoc.md`
- tmp claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T073044+0800-codex-6e-eth-compression-breakout-mtf-screen.claim`
- run root: `/tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/local_gate1`
- runner: `support/docs/experiments/actionable-regime-confidence/scripts/run_local_nq_csv_regime_rooted_mtf_gate1_v1.py`

## Planned Command

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_local_nq_csv_regime_rooted_mtf_gate1_v1.py \
  --source-csv '/Users/thrill3r/Downloads/Tomac/eur future 2015-2025/glbx-mdp3-20150101-20251231.ohlcv-1m.csv' \
  --symbol 6E \
  --product fx_futures \
  --contract-label eur_glbx_retained \
  --provider tomac_databento_glbx_csv \
  --factor-id-prefix 6e_eth_compression_breakout_mtf \
  --aq-symbol 6E_ETH_COMPRESSION_BREAKOUT_MTF_20260530T073044 \
  --run-slug 6e-eth-compression-breakout-mtf-screen-20260530T073044-v1 \
  --session-scope ETH/full_retained_session \
  --session-coverage-evidence 'GLBX 6E 1m retained rows, no RTH filter; source starts at 2015-01-01T23:00Z and includes overnight rows.' \
  --families range_consolidation_squeeze_breakout \
  --run-root /tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/local_gate1 \
  --start 2021-01-01 \
  --end 2025-12-31 \
  --contract-prefix 6E \
  --outright-only \
  --positive-prices-only \
  --screen-selected-aq \
  --skip-aq \
  --max-parallel 1
```

## Current Status

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- status: `terminalized`
- decision: `drop_gate1_no_cost_density`

## Terminal Readback

The local retained-session screen completed at 2026-05-29T23:41:34Z. It produced
21 screen rows from 1,746,944 retained 1m 6E rows covering
2021-01-03T23:00:00Z through 2025-12-31T21:59:00Z. Session scope stayed
`ETH/full_retained_session`, `rth_filter_applied=false`.

No row survived transaction-cost stress: `screen_survivors_2bps=0` and
`screen_survivors_5bps=0`. `selected_for_auto_quant.csv` is empty, so this lane
does not advance to provider/AQ/paper/downstream lifecycle work.

Evidence:

- `/tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/local_gate1/checks/terminal_metrics.json`
- `/tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/local_gate1/summaries/terminal_decision_summary.md`
- `/tmp/ict-engine-6e-eth-compression-breakout-mtf-screen-20260530T073044+0800/local_gate1/summaries/screen_rows.csv`
