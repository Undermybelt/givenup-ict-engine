# Data Cleaning And Candidate Prefilter

Use this reference when a profitability-factor lane touches raw provider rows,
retained futures/stock/crypto histories, multi-timeframe features, or
web-sourced factor ideas.

## Data Cleaning Gate

Before scoring or comparing a factor, record these fields in the workdoc and
terminal packet:

- `source_provenance`: provider/API/archive path, fetch command, source URL or
  local verified cache row, fetch timestamp, product/root, exchange/venue,
  currency, and timeframe.
- `timestamp_integrity`: parsed timezone, monotonic order, duplicate count,
  missing/null timestamp count, and gap/session explanation.
- `ohlcv_integrity`: numeric OHLCV fields, null counts, impossible price/volume
  counts, return-sanity filter, futures spread/roll filter when relevant, and
  source row count versus retained row count.
- `session_scope`: ETH/full-retained or RTH comparison, `rth_filter_applied`,
  exchange-local RTH window, retained row count, and rows outside RTH that prove
  ETH/full-retained coverage.
- `mtf_integrity`: origin timeframe, derived context frames, completed-bar
  policy, dropped incomplete/empty resample buckets, and no forward-fill across
  market-closed synthetic buckets.
- `feature_target_alignment`: closed-bar feature availability, entry/label shift,
  no current-bar or future-bar leakage, and exact availability time for session
  features such as opening range or macro/event release windows.

If any of these cannot be proven, do not score the lane as promotion evidence.
Use `data_cleaning_unverified`, `session_scope_unverified`,
`data_scope_blocked_for_eth_target`, or `lookahead_unverified`, and keep
`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

## MTF Resample Rule

For lower-timeframe origins such as `1m`, derive higher-timeframe context only
from completed bars. After resampling to `5m/15m/30m/1h/4h/1d`, drop empty or
incomplete buckets before calculating HTF rolling features and before reindexing
the context back to the origin frame.

The failure mode to avoid: market-closed `1h` buckets can exist as timestamp
bins with no real OHLCV. If they remain in the HTF frame, rolling context and
later low-timeframe joins can create false continuity. The correct process is:
resample, remove NaN/empty bars, compute HTF features on the cleaned completed
bars, then reindex or as-of join back to the origin rows without inventing
missing context.

## Web Candidate Prefilter

When searching papers, repositories, blogs, or social posts for new factors,
screen the idea before coding. A candidate only earns implementation budget if
all four checks are plausible and recordable:

- `per_trade_edge`: the stated or inferable gross edge per trade is large enough
  to exceed realistic commission, exchange/regulatory fees, spread, slippage,
  and borrow/financing where relevant. Tiny gross edge with high turnover is
  churn until proven otherwise.
- `trade_density`: expected cadence fits the lane target. Sparse positives do
  not satisfy practical feedback collection; extreme frequency must clear tick,
  bid/ask, fill, and cost evidence rather than bar-only optimism.
- `cost_wall`: the instrument/root/venue/account/pricing-plan/date cost model is
  verified from official broker/exchange/regulatory sources or a complete
  verified local cache row. Fixed bps stress is diagnostic only unless it is the
  actual verified fee model.
- `eth_time_data_provable`: the required ETH/full-retained timeframe data can be
  obtained and audited for the target product. RTH-only, daily-only, screenshot,
  or unexportable backtests are idea reserve only for the user's default target.

If a source fails one of the four checks, preserve the useful facts in a reserve
packet with `idea_only`, `paper_only`, `repo_source_only`,
`cost_model_unverified`, `data_cleaning_unverified`, or
`data_scope_blocked_for_eth_target`. Do not launch provider/AQ/downstream work
from it until the missing proof is repaired.

## Terminal Classification

Use these classifications consistently:

- `clean_negative`: data cleaning and no-lookahead checks passed, but edge,
  density, cost, or validation failed.
- `data_cleaning_unverified`: source, timestamp, OHLCV, MTF, or feature/target
  integrity was not proven.
- `session_scope_unverified`: the packet cannot prove ETH/full-retained coverage
  or a current user-requested RTH scope.
- `data_scope_blocked_for_eth_target`: only RTH or otherwise insufficient
  session data is available for the default ETH objective.
- `lookahead_unverified`: signal availability does not precede execution.
- `source_reserve_only`: the idea is codeable or interesting but has not yet
  passed the four prefilters.

The S1 TrendExpansion evidence from 2026-06-01 is the reference example: the NQ
`1m` HTF `1h` context had market-closed empty buckets. Dropping completed-bar
NaNs before HTF rolling and reindexing repaired the cleaning issue, then the
candidate still terminalized negative on discrimination and edge. Cleaning
repair can make evidence honest; it does not promote a weak factor.
