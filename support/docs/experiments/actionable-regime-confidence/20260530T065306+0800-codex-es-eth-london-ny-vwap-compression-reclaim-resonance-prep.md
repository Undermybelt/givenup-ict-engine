# ES ETH London-NY VWAP Compression Reclaim Resonance Prep

- created_at: `2026-05-30T06:53:06+0800`
- agent_name: `codex-es-eth-london-ny-vwap-compression-reclaim-resonance-prep`
- factor_id: `es_eth_london_ny_vwap_compression_reclaim_resonance_v1`
- tmp_root: `/tmp/ict-engine-es-eth-london-ny-vwap-compression-reclaim-resonance-20260530T065306+0800`
- workdoc: `/tmp/ict-engine-es-eth-london-ny-vwap-compression-reclaim-resonance-20260530T065306+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T065306+0800-codex-es-eth-london-ny-vwap-compression-reclaim-resonance-prep.claim`
- repo_run_root: `support/docs/experiments/actionable-regime-confidence/runs/20260530T065306+0800-codex-es-eth-london-ny-vwap-compression-reclaim-resonance-prep-v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
- status: `terminalized_source_prep_no_launch_foreign_claims_blocked`

## Scope

Prepare a distinct ES retained-session factor lane while shared Board B runtime is blocked. This is a no-launch packet only: no provider fetch, IBKR historical request, AutoQuant, Freqtrade, paper/sim/live, lifecycle, Pre-Bayes, BBN, CatBoost, execution-tree, or feedback update was started.

## Rooted Branch

`FUTURES -> equity_index -> ES -> ETH/full_retained_session -> 1m origin + 5m/15m/30m/1h/4h/1d context -> LondonNySessionTransition -> VwapCompressionReclaim -> MtfResonance -> AtrBracketContinuation -> es_eth_london_ny_vwap_compression_reclaim_resonance_v1`

## Profit Mechanism

The candidate targets ES retained-session transition behavior rather than a cash-open gap. The planned signal waits for London-session compression near session VWAP, a liquidity probe or controlled drift into the NY handoff, then a 1m VWAP reclaim that is confirmed by 5m/15m resonance and not contradicted by 30m/1h/4h/1d context. Risk is ATR-bracketed with fail-closed cost, density, and retained-session gates.

## Non-Duplication

Same-turn focused search found no existing `es_eth_london_ny_vwap_compression_reclaim_resonance_v1` lane. This candidate is explicitly not:

- `es_cash_open_gap_vwap_reclaim_v1`
- `es_eth_session_vwap_deviation_continuation_screen`
- `es_afternoon_vwap_retest_trend_continuation_screen`
- generic `compression_breakout_continuation`
- M2K/ES risk-on rotation VWAP/ADX
- Aroon/CCI cadence-volume persistence retest
- MGC Asia stoprun VWAP compression reclaim

## Source Evidence

Local retained ES feather files exist under `/Users/thrill3r/Auto-Quant/user_data/data` for `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, and `1d`.

Same-turn retained-session row check:

| timeframe | rows | first_utc | last_utc | rth_rows | non_rth_rows |
|---|---:|---|---|---:|---:|
| 1m | 299107 | 2012-04-23 13:38:00+00:00 | 2025-08-04 12:10:00+00:00 | 116953 | 182154 |
| 5m | 89433 | 2012-04-23 13:35:00+00:00 | 2025-08-04 12:10:00+00:00 | 36021 | 53412 |
| 15m | 39717 | 2012-04-23 13:30:00+00:00 | 2025-08-04 12:00:00+00:00 | 15829 | 23888 |
| 30m | 23811 | 2012-04-23 13:30:00+00:00 | 2025-08-04 12:00:00+00:00 | 9466 | 14345 |
| 1h | 14036 | 2012-04-23 13:00:00+00:00 | 2025-08-04 12:00:00+00:00 | 5346 | 8690 |
| 4h | 5075 | 2012-04-23 12:00:00+00:00 | 2025-08-04 12:00:00+00:00 | 1804 | 3271 |
| 1d | 1383 | 2012-04-23 00:00:00+00:00 | 2025-08-04 00:00:00+00:00 | 0 | 1383 |

Examples of outside-RTH coverage include `2012-05-06 18:36:00-04:00` on 1m and `2012-05-06 18:35:00-04:00` on 5m, using `09:30-16:00 America/New_York` as the RTH comparison window.

## Current Blocker

Same-turn compact audit reported `status=needs_attention`, `active_claims=2`, `fresh_active_claims_without_live_process=1`, `fresh_wait_only_active_claims_without_live_process=1`, `live_factor_processes=0`, `promotion_allowed_true=0`, and `trade_usable_true=0`.

Active blockers at prep time:

- `20260530T064148+0800-codex-mgc-eth-asia-stoprun-vwap-compression-reclaim-full-ladder-training.claim`
- `20260530T064801+0800-codex-tomac-aroon-cci-cadence-volume-persistence-retest-training-prep.claim`

Because fresh claims are present, this lane is terminalized as prep-only and does not add another active wait-only claim.

## Next Valid Work

After compact claim audit and focused process guard are both clear, add a tested wrapper or registered clean-AQ family for the exact `es_eth_london_ny_vwap_compression_reclaim_resonance_v1` identity before any launch. Reusing the existing generic `compression_breakout_continuation` family is not sufficient unless the London-to-NY transition and MTF resonance conditions are encoded and tested.

Candidate launch shape after wrapper support exists and runtime is clear:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_index_futures_clean_aq_v1.py \
  --root /tmp/ict-engine-es-eth-london-ny-vwap-compression-reclaim-resonance-20260530T065306+0800/aq \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/20260530T065306+0800-codex-es-eth-london-ny-vwap-compression-reclaim-resonance-prep-v1/aq \
  --symbols ES \
  --families es_eth_london_ny_vwap_compression_reclaim_resonance \
  --timeframes 1m,5m,15m,30m,1h,4h,1d \
  --aq-smoke-timeframe 1m \
  --aq-symbol-limit 1 \
  --timeout 1800
```

That family key is not asserted to exist in the current runner; the first implementation step is to pin it with a failing test, then register the exact branch grammar and no-runtime guard before launch.
