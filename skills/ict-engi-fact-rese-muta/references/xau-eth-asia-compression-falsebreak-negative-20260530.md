# XAU ETH Asia Compression False-Break Fade Negative, 2026-05-30

## Context

The user corrected the profitability-factor target to ETH/full retained
tradable session, not RTH. A new XAU/GC retained-data local screen was created
while provider/AQ runtime was blocked by other owners. It explicitly avoided
rerunning the earlier XAU VWAP washout, compression breakout, EMA pullback,
wide-range retest, KAMA, tailshock entropy, and London/NY high-frequency
microbreakout packets.

## Branch Tested

- `factor_id`: `xau_eth_asia_compression_falsebreak_fade_v1`
- Branch: `FUTURES -> PreciousMetals -> XAU/GC -> ETH/full_retained_session -> 1m execution + shifted 5m/15m/30m/1h/4h/1d context -> SessionCompression -> AsiaRangeCompression -> FalseBreakFailureFade -> MtfVwapMeanReversionRiskManaged`
- Session scope: `ETH/full_retained_session`
- `rth_filter_applied=false`
- Data: retained local `XAU_1m.parquet` from `<private-tomac-data-cache>/factor_training/cache`, plus available retained XAU MTF context files.
- Run root: `/tmp/ict-engine-xau-eth-asia-compression-falsebreak-fade-screen-20260530T032027+0800`
- Repo packet: `support/docs/experiments/actionable-regime-confidence/20260530T032027+0800-codex-xau-eth-asia-compression-falsebreak-fade-screen.md`

## Result

- ETH coverage passed: `635274` retained 1m rows; `336716` rows outside proxy US RTH.
- Core event-screen rows: `32`.
- Gate 1 candidate rows: `0`.
- Terminal decision: `python_screen_no_5bps_density_split_survivor`.
- `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

Best row:

- `trade_count=162`
- `trades_per_retained_day=0.128063`
- raw total profit `+1.418788%`
- `2bps_per_side_total_profit_pct=-5.061212%`
- `5bps_per_side_total_profit_pct=-14.781212%`
- `profit_factor_5bps=0.503840`
- in-sample 5bps `-11.408692%`
- validation 5bps `-3.372520%`

## Lesson

For retained XAU ETH/full-session 1m OHLCV, Asia-session compression followed
by failed range break and VWAP mean-reversion fade can produce raw positives at
acceptable low density, but the edge did not survive even 2bps/side, and the
validation split was negative. Do not rerun this exact false-break fade branch
unchanged as a practical candidate.

Future XAU ETH work should either:

- bring lower-friction execution evidence such as bid/ask or paper-fill
  semantics before revisiting fine intraday reversions; or
- move to a materially different lower-turnover source such as event/carry/
  sidecar filtering rather than another 1m OHLCV range-fade threshold variant.

Python-only retained-data evidence remains triage only. It cannot set
`promotion_allowed=true`, `trade_usable=true`, or `update_goal=true` without a
same-root downstream practical-closure chain.
