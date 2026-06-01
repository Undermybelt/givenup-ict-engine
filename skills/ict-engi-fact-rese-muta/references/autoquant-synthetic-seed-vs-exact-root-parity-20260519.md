# Auto-Quant synthetic seed vs exact rooted-branch parity

Session: 2026-05-19 CRWD 5m PDA/MTF soft-confirmation continuation.

## Durable lesson

`factor-autoresearch --auto-quant-profile synthetic_ohlcv` is useful as an Auto-Quant control-plane and seed-discovery loop, but it may collapse the requested exact timeframe ladder into synthetic `1h/4h/1d` artifacts.

When this happens, a positive `run_tomac.py` result is seed/incubate evidence only. It does not prove exact provider/timeframe branch parity, even if the source Gate 1 packet is strong.

## Observed pattern

Exact source branch:

`US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1`

Gate 1 replay retained real YF rows only for `5m/15m/30m`:

- `CRWD/5m`: 43 trades
- raw profit: `+5.81%`
- 2 bps/side: `+4.09%`
- 5 bps/side: `+1.51%`
- decision: `downstream_allowed=true`, but `promotion_allowed=false`, `trade_usable=false`

Auto-Quant autoresearch state:

`/tmp/ict-engine-runs/20260519T1342+0800-hermes-crwd5m-autoresearch-pda-soft-v1`

First run returned control-plane prep blockers:

- `auto_quant_prepare_required_before_run`
- `auto_quant_seed_strategies_required`
- `auto_quant_active_strategy_count=0`

Correct sequence:

1. Run `ict-engine auto-quant-prepare --state-dir <state>`.
2. Re-run `factor-autoresearch` to refresh handoff/readiness.
3. Run the advised Auto-Quant command: `cd <state>/.deps/auto-quant && ./.venv/bin/python run_tomac.py`.
4. Classify the result by provenance, not by headline PnL.

Observed seed result:

- strategy: `TomacNQ_KillzoneBreakout`
- pair: `CRWD/USD`
- synthetic timeframe: `1h`
- trades: 17
- total profit: `+3.35%`
- win rate: `70.5882%`
- Sharpe: `0.8490`
- profit factor: `1.3240`

Verdict: seed/incubate only. It cannot promote the exact `CRWD/5m` branch.

## Future workflow rule

If the user asks to continue stable-profit training from a strong exact branch:

- keep the exact rooted branch as the admission identity;
- use synthetic Auto-Quant output only to suggest variant structure;
- convert any promising synthetic idea back into exact provider/timeframe material;
- rerun Gate 1 cost/density on the exact root before Pre-Bayes/BBN/CatBoost/execution-tree;
- never let synthetic `1h` success substitute for exact `5m` or `1m` parity.

## 2026-05-20 exact-runtime synthetic profile guard

If a synthetic Auto-Quant profile is built from a decorated exact runtime symbol
such as `IBKR_M2K1M_RVOL_PDA_CONSISTENCY_FLOOR_AUTORESEARCH_REPAIR_V1`, do not
count or copy generic upstream seeds such as `TomacNQ_KillzoneBreakout` as
active strategies unless the seed source is exact-compatible with that
symbol/root.

Correct fail-closed behavior is `auto_quant_seed_strategies_required` and
`auto_quant_active_strategy_count=0`, forcing an exact branch seed to be authored
before `run_tomac.py`.

This guards the Board B M2K repair path where generic NQ ran on `M2K/USD` with
zero trades and no PDA/transition repair value.

## 2026-05-20 exact standalone Freqtrade source seed preservation

If `strategy-material-root` points at a standalone Freqtrade `IStrategy`, the
seed bridge should preserve the source strategy body and adapt only the class
name to the generated seed strategy. This is required for exact futures short
repairs where source semantics include:

- `timeframe = "1m"`
- `can_short = True`
- `enter_short`
- `exit_short`

Do not substitute the generic long-only EMA/RSI scaffold for these standalone
sources. The generic scaffold remains appropriate for non-standalone material,
including source that imports Tomac/local code, because the managed Auto-Quant
workspace must not import maintainer-local runtime code.

Regression guard in `ict-engine`:

`CARGO_TARGET_DIR=.local-artifacts/cargo-target cargo test --lib materializes_exact_freqtrade_source_without_long_scaffold_substitution --quiet`

This is still a bridge repair, not a factor verdict. After preserving exact
source semantics, rerun AQ/downstream and keep the same promotion gates:
cost-stressed density, same-root branch identity, PDA alignment, transition
hazard, execution readiness, and mature validation rows.
