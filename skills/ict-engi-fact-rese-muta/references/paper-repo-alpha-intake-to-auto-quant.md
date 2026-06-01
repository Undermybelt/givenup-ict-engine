# Paper/repo/blog alpha intake to Auto-Quant

Use this reference when the user asks to stop local parameter grinding and instead source higher-quality factors from papers, repos, blogs, social media, or quant communities before running Auto-Quant.

## Operating pattern

1. Run parallel discovery lanes:
   - academic papers: prefer DOI/arXiv/Semantic Scholar-backed anomalies;
   - public repos/strategy libraries: prefer executable strategy logic and known defaults;
   - blogs/social/forums: treat as idea source only, never evidence.
2. Keep only candidates that can become code:
   - source URL / DOI / repo path;
   - core trading hypothesis;
   - exact required fields;
   - Auto-Quant condition sketch;
   - timeframe and execution assumptions;
   - known failure modes.
3. Apply the OHLCV-first filter:
   - first batch: ORB, failed ORB, VWAP reclaim/deviation, gap fade/go, intraday momentum, pair z-score, time-of-day slot alpha;
   - second batch: VIX/VRP/breadth/auction/news as sidecar only;
   - options-chain claims must be named `*_proxy` unless real historical IV/OI/Greeks/GEX/skew are available.
4. Gate each candidate in Auto-Quant-style slices before tree handoff:
   - same cost model across candidates, at least 2 bps/side for liquid ETFs/stocks;
   - split ETF and single-stock evidence;
   - track per-symbol stability, not just combined PF;
   - require native provider bars where possible; if resampled, label as proxy/resample.
5. Promote only candidates that survive:
   - cross-symbol portability;
   - cost/slippage stress;
   - walk-forward or at least forward bucket audit;
   - structural-path validation gates if sent to tree.

## Session-derived candidate results

### Paper-backed overnight gap reclaim ETF sample

Source:
- Lou / Polk / Skouras, `A Tug of War: Overnight Versus Intraday Expected Returns`, DOI `10.1016/j.jfineco.2019.03.011`.

Tested implementation:
- branch: `Range -> OvernightIntradayTugOfWar -> gap_down_vwap_reclaim -> yf_etf_overnight_gap_reclaim_1m_mtf_v1`;
- provider: yfinance/YF;
- symbols: SPY, QQQ, IWM;
- ladder: `1m/5m/15m/30m/1h`;
- rule: gap-down between roughly -2.2% and -0.35%, early-session VWAP/EMA reclaim, partial gap-fill progress, participation and controlled-vol filters.

Observed run:
- provider fetch, strategy compile, Auto-Quant batch/dispatch/rank all exited 0;
- rows existed for every symbol/timeframe, but Auto-Quant produced 15 rank rows with 0 trades;
- decision: `drop_or_keep_source_backed_negative_sample`; do not run BBN/CatBoost/tree for this exact branch.

Lesson:
- A paper-backed idea still needs density. If a faithful first encoding has zero trades across a multi-symbol MTF ladder, terminalize that exact filter as a negative sample and move to the next sourced candidate or a deliberately looser sibling; do not keep tightening/loosening blindly without declaring the new branch identity.


### Same-time-of-day slot alpha ETF sample

Sources:
- Heston / Korajczyk / Sadka, `Intraday Patterns in the Cross-Section of Stock Returns`, DOI `10.1111/j.1540-6261.2010.01559.x`.
- RobotWealth intraday seasonality blog as community hypothesis only.

Tested implementation:
- branch: `Range -> IntradaySeasonality -> same_time_slot_alpha -> yf_etf_tod_slot_alpha_1m_mtf_v1`;
- provider: yfinance/YF;
- symbols: SPY, QQQ, IWM;
- ladder: `1m/5m/15m/30m/1h`;
- rule: shifted prior same-time-slot return alpha plus slot-relative volume, VWAP/EMA confirmation, RSI/range filters, max-hold exit.

Observed run:
- provider fetch, compile, Auto-Quant batch/dispatch/rank all exited 0;
- Gate 1: 15 rows, 452 trades, 10 positive rows with at least 8 trades;
- strongest rows: IWM 30m +3.39%, IWM 15m +2.41%, QQQ 5m +2.52%, SPY 15m +4.05%, QQQ 15m +2.05%;
- cost stress survived 2 bps/side on 8 higher-timeframe rows;
- downstream reached AQ import, BBN prior, analyze, Pre-Bayes, structural export, and policy readback, but CatBoost stopped with single-class target and execution candidate stayed no-trade;
- 1m origin rows were zero-trade, so this is medium-timeframe seasonal evidence, not 1m execution proof.

Classify as high-quality scoped candidate, not live-ready. Next work: walk-forward bucket validation and a denser 1m-origin sibling if the user specifically needs 1m execution.

Follow-up walk-forward:
- held-out late window `20260501-20260514` reran strongest rows through Auto-Quant batch/dispatch/rank;
- 6 rows, 105 trades, all commands exited 0;
- only the 15m lane survived 2 bps/side: IWM 15m raw +1.79% -> +1.19%, QQQ 15m raw +0.49% -> +0.29%;
- 5m rows were raw-positive but failed 2 bps/side due turnover; 1m origin remained zero-trade.

Updated classification: `15m_tod_slot_alpha_walkforward_survives`, not live-ready. Next useful slice is dedicated 15m TOD with stricter turnover/cost controls and IBKR/native validation, not forcing the 5m/1m rows downstream.

Dedicated 15m cost-gated follow-up:
- native IBKR validation attempted first, but TWS/IBG was unreachable at `127.0.0.1:7497`; classify as provider-unreachable, not factor failure;
- fallback native YF 15m rerun over `SPY/QQQ/IWM` fetched 833 rows each and completed Auto-Quant batch/dispatch/rank;
- strict turnover/cost variant produced 3 rows, 18 trades; `QQQ/15m` and `SPY/15m` survived 2 bps/side, while `IWM/15m` failed cost;
- classification: `native_yf_15m_cost_gate_survives` as scoped practical candidate only; still needs same-branch downstream readback and IBKR/native parity before any live claim.

### 30m MACD trend compression baseline

Source class: OHLCV-derived practical options/profit proxy.

Rule:
- timeframe: IBKR 30m;
- symbols: SPY, QQQ, IWM, XLK, SMH, NVDA;
- condition: close > EMA50 > EMA200, MACD crosses above signal, RV12 < RV72 * 1.8;
- target 3.0%, stop 2.5%, hold 36 bars, cost 2 bps/side.

Observed run:
- 41 trades, 35W/6L, PF 43.49, Sharpe 8.26, profit +68.60%;
- all six symbols positive;
- monthly buckets stayed positive in April and May;
- CatBoost path-ranker runtime reached `enabled_candidate_set_ready` with `score_model_family=catboost` and `runtime_matches=2`.

Use as current baseline, not final live proof. Needs broader date windows and native forward validation.

### 15m MACD resample proxy

Rule:
- 15m bars resampled from existing IBKR 5m CSV;
- target 6.0%, stop 1.5%, hold 18 bars.

Observed run:
- 37 trades, PF 2.21, Sharpe 1.76, profit +13.28%;
- IWM negative and XLK near flat;
- CatBoost runtime ready after tree handoff.

Classify as proxy/supporting evidence only because bars were resampled from 5m, not native 15m provider fetch. Do not let it replace the 30m baseline without native 15m validation.

### Intraday momentum paper factor

Source:
- Gao / Han / Li / Zhou, Intraday Momentum, DOI `10.2139/ssrn.2440866`.

Tested implementation:
- first 30m return predicts last 30m direction;
- entry last 30m, exit close, cost 2 bps/side;
- symbols: SPY, QQQ, IWM, XLK, SMH, NVDA.

Observed result:
- best variant still failed: PF 0.93, profit -0.41%, only 1/6 positive.

Classify as negative sample for this current data/window. It may still be useful as a tail-session filter, but not as a standalone long/short factor until broader data contradicts this.

### ORB/RVOL failed-breakout fade

Source class:
- QuantConnect ORB / stocks-in-play;
- QuantifiedStrategies ORB;
- trading blog/community ORB + relative volume heuristics.

Best observed variants:
- failed ORB fade, 1 opening bar, target 0.5%, stop 1.5%, hold 6 bars, RVOL 1.5x:
  - 35 trades, PF 2.84, Sharpe 2.56, profit +4.34%, 3/6 symbols positive;
- failed ORB fade, 1 opening bar, target 1.0%, stop 1.5%, hold 12 bars, RVOL 1.5x:
  - 35 trades, PF 2.18, profit +4.81%, 5/6 symbols positive, but QQQ sharply negative.

Classify as second-line candidate. Needs market-regime filter, QQQ exclusion/filter, and trend-day avoidance before tree handoff.

## High-priority next candidates

Run these before inventing more MACD variants:

1. VWAP reclaim / VWAP deviation
   - OHLCV-only intraday;
   - promising as trend continuation or mean-reversion regime switch.
2. Gap fade vs gap-and-go
   - OHLCV plus previous close/opening range;
   - split news-like strong continuation from weak gap fade.
3. Pair z-score relative value
   - pairs: NVDA/SMH, XLK/QQQ, QQQ/SPY, IWM/SPY;
   - requires synchronized multi-symbol bars and rolling beta/correlation gate.
4. Same-time-of-day slot alpha
   - rolling mean return by bar slot;
   - must walk-forward to avoid slot overfit.
5. 52-week-high + intraday reclaim
   - daily context plus intraday trigger;
   - likely more robust as trend context than raw entry rule.

## Pitfalls

- Do not call blog/social results proof. They only seed candidates.
- Do not promote resampled timeframe evidence as native provider evidence.
- Do not optimize on combined PF alone; require per-symbol stability.
- Do not hide single-symbol failures: if QQQ or SPY fails badly, record it even when the basket is profitable.
- If a broad grid times out, narrow to literature/default parameter ranges and rerun a fast Gate1 before abandoning the factor.
