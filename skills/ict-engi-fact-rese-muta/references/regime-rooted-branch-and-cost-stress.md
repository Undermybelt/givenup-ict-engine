# Regime-rooted branch paths and cost-stress gate

## When this applies
Use this note when an ict-engine factor run is intended to continue through Auto-Quant, filtering, belief network/BBN, CatBoost, and execution-tree validation.

## Durable rule
A profitable factor is not a root by itself. The branch root is the regime discriminator. Preserve the full path shape across every downstream artifact:

`main_regime -> sub_regime -> ... -> sub_sub_regime_or_candidate_factor -> profit_factor -> execution_variant`

Do not flatten the branch into only the factor name when handing off to BBN, CatBoost, structural path ranking, or execution tree. If the execution tree pivots to a sibling branch, treat it as same-branch parity failure, not promotion.

## Multi-agent safety
ict-engine training is multi-agent collaborative work. Before changing docs, TODOs, branch ledgers, or shared runtime state:
- identify whether the file is a construction area from another agent;
- prefer adding new run artifacts under a fresh state/output dir;
- avoid rewriting in-progress docs or ledgers unless the task explicitly owns that surface;
- preserve original and derived artifacts separately.

## Provider/timeframe preference
For factor training, prefer real provider execution over doc inference:
- IBKR first when available;
- include TradingViewRemix, yfinance, and Kraken as portability checks when relevant;
- request the largest feasible upper window, commonly one month or one quarter;
- start from 1m and cover 5m, 15m, 30m, and 1h where the provider can support it;
- downgrade only the provider/timeframe lane that fails, then retry a feasible real window.

## Cost-stress gate
Before BBN/CatBoost/execution-tree promotion, run the instrument-appropriate
cost model plus explicit slippage stress on the candidate signal.

For equities, crypto, perps, and other percent-fee instruments where notional
bps is the commission model, run per-side bps stress at minimum:

`0bps, 1bps, 2bps, 5bps` per side; add `10bps` for thin or noisy instruments.

For futures, do not use these bps levels as the commission model. Verify the
exact product's per-contract broker/exchange/regulatory fees, contract
multiplier, tick value, and side convention, then add any bps/tick slippage as a
separate stress. If any field is unknown, mark `cost_model_unverified` and fail
closed. See `futures-contract-cost-models-ibkr.md`.

If a low-timeframe signal is positive before costs but flips negative at 1-2bps/side, classify it as research/incubate evidence only. Do not promote it as live-practical alpha even if Auto-Quant Gate 1 or raw vectorized backtest looks positive.

## Example: Donchian/RVOL 1m HTF-veto stress
Session evidence from QQQ 1m IBKR replay showed:

- raw 1m Donchian/RVOL:
  - 0bps/side: trades=41, total=+0.7243%, PF=1.5085
  - 1bps/side: total=-0.0957%, PF=0.9505
  - 2bps/side: total=-0.9157%, PF=0.6348
- HTF-veto variant:
  - 0bps/side: trades=22, total=+0.4469%, PF=1.3797
  - 1bps/side: total=+0.0069%, PF=1.0048
  - 2bps/side: total=-0.4331%, PF=0.7507

Verdict: fail live-practical cost gate; preserve as sourced/incubate sample, then search for lower-turnover or higher-average-return regime-rooted variants.

## Closure checklist
- Branch path recorded with regime root.
- Provider, symbol, timeframe, and window explicitly recorded.
- Cost model stated with instrument-appropriate units: per-side bps for
  bps-priced instruments, or per-contract per-side plus round-turn totals for
  futures.
- AQ/BBN/CatBoost/execution-tree handoff keeps exact branch ID/path.
- Result classified as promote, incubate, or fail-closed with the gate that decided it.
