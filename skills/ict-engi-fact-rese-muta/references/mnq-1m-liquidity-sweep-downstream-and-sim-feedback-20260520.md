# MNQ 1m liquidity sweep downstream + simulated-feedback admission

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session: 2026-05-20

## Exact branch

`FUTURES -> equity_index -> MNQ -> 1m -> RangeReversion -> LiquiditySweepReclaim -> ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1`

## Gate 1 evidence

Source packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260519T220553+0800-codex-ibkr-futures-liquidity-sweep-vwap-reclaim-1m-gate1-v1`

Key row:

- `MNQ/dense/1m`
- `trade_count=7`
- `win_rate_pct=71.4286`
- `raw_total_profit_pct=0.42`
- `1bps_per_side_total_profit_pct=0.28`
- `2bps_per_side_total_profit_pct=0.14`
- `5bps_per_side_total_profit_pct=-0.28`
- `survives_2bps_per_side=true`
- `survives_5bps_per_side=false`

Verdict: Gate 1 can justify downstream parity at 2bps, but this is cost-thin. It is not a 5bps-robust practical factor.

## Downstream evidence

Downstream packet:

`support/docs/experiments/actionable-regime-confidence/runs/20260519T220553+0800-codex-ibkr-futures-liquidity-sweep-vwap-reclaim-1m-gate1-v1/downstream-exact-mnq-1m-liquidity-sweep-vwap-reclaim-20260520T003509+0800`

Result:

- `all_commands_ok=true`
- `exact_branch_survived=true`
- `pre_bayes_allowed=true`
- `bbn_allowed=true`
- `catboost_allowed=true`
- `mature_rows=0`
- `history_mature_rows=0`
- `execution_readiness=0.0`
- `transition_hazard=1.0`
- `pda_hybrid_alignment=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Verdict: exact-root mechanics and ranker plumbing worked, but execution remains fail-closed. Do not promote.

## Simulated feedback admission pitfall

Attempted script:

`support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_mnq1m_liquidity_sweep_simulated_trade_admission_v1.py`

It failed while importing the Auto-Quant workspace `run_tomac.py` because the Python interpreter used for import lacked `freqtrade`:

`ModuleNotFoundError: No module named 'freqtrade'`

Durable lesson: this is a simulated-feedback tooling/environment handoff blocker, not a factor verdict. Future replay should run the workspace with the actual Auto-Quant venv/interpreter that has `freqtrade`, or explicitly probe/import `freqtrade` with the chosen interpreter before importing `run_tomac.py`. If unavailable, classify simulated feedback as blocked and keep the branch observation-only.

## Rule

For 1m futures branches that survive only 2bps but fail 5bps, downstream parity is useful only as observation evidence. If downstream then reports `mature_rows=0`, `history_mature_rows=0`, `execution_readiness=0.0`, `transition_hazard=1.0`, and `pda_hybrid_alignment=false`, the next step is not promotion and not more near-identical density overlays. Either add valid same-root feedback/maturity rows with the correct Auto-Quant environment, or pivot to a materially different same-root execution-readiness/PDA-hybrid factor shape.
