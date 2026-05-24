# IBKR WSO HvacDistribution Range-Expansion Continuation Gate 1

Decision: `drop_gate1_cost_or_density_failed`

Branch path:

```text
TrendExpansion -> HvacDistributionRangeExpansionContinuation -> prior_day_range_breakout_pullback -> ibkr_wso_hvac_distribution_range_expansion_continuation_1m_mtf_gate1_v1
```

Provider/window:

- IBKR-first WSO STK SMART/USD primary exchange NYSE.
- Requested ladder: `1m=7D`, `5m/15m/30m/1h=3M`, `4h=1Y`, `1d=2Y`.
- Provider, symbol, and timeframe are provenance labels, not branch roots.

Gate result:

| Timeframe | Trades | Trades/day | Raw | 1bps/side | 2bps/side | 5bps/side | Gate 1 survivor |
|---|---:|---:|---:|---:|---:|---:|---|
| `1m` | 1 | 0.143 | 0.06% | 0.04% | 0.02% | -0.04% | `False` |
| `1h` | 7 | 0.109 | 3.51% | 3.37% | 3.23% | 2.81% | `False` |
| `30m` | 7 | 0.109 | 1.12% | 0.98% | 0.84% | 0.42% | `False` |
| `15m` | 16 | 0.250 | 3.36% | 3.04% | 2.72% | 1.76% | `False` |
| `5m` | 18 | 0.281 | 0.64% | 0.28% | -0.08% | -1.16% | `False` |
| `4h` | 10 | 0.040 | 0.04% | -0.16% | -0.36% | -0.96% | `False` |
| `1d` | 0 | 0.000 | 0.00% | 0.00% | 0.00% | 0.00% | `False` |

Interpretation:

WSO produced AQ rank rows, but no row survived both hard 5bps/side cost stress and practical trade density. Stop before downstream.

Next:

Preserve as observation and rotate to a materially different family or a same-root variant that widens per-trade excursion before cost stress.
