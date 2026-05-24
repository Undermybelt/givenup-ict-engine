# IBKR NUE Bayesian-Markov Trend Detector Gate 1

Decision: `drop_gate1_no_exact_1m_5bps_density_survivor`

Branch path:

```text
TrendExpansion -> SteelProducerBayesianMarkovTrendContinuation -> bayesian_markov_trend_detector -> ibkr_nue_steel_producer_bayesian_markov_trend_detector_1m_mtf_gate1_v1
```

Provider/window:

- IBKR-first NUE STK SMART/USD primary exchange NYSE.
- Requested ladder: `1m=30D`, `5m/15m/30m/1h=3M`, `4h=1Y`, `1d=2Y`, with narrower retry windows if a provider leg times out.
- Provider, symbol, product, and timeframe are provenance labels, not branch roots.

Gate result:

| Timeframe | Trades | Trades/day | Raw | 1bps/side | 2bps/side | 5bps/side | Gate 1 survivor |
|---|---:|---:|---:|---:|---:|---:|---|
| `4h` | 35 | 0.130 | 1.33% | 0.63% | -0.07% | -2.17% | `False` |
| `1d` | 5 | 0.010 | -0.43% | -0.53% | -0.63% | -0.93% | `False` |
| `30m` | 22 | 0.333 | 3.23% | 2.79% | 2.35% | 1.03% | `False` |
| `4h` | 24 | 0.089 | -1.54% | -2.02% | -2.50% | -3.94% | `False` |
| `1h` | 26 | 0.394 | 1.27% | 0.75% | 0.23% | -1.33% | `False` |
| `4h` | 39 | 0.144 | -4.27% | -5.05% | -5.83% | -8.17% | `False` |
| `30m` | 32 | 0.485 | -0.34% | -0.98% | -1.62% | -3.54% | `False` |
| `15m` | 70 | 1.061 | 0.32% | -1.08% | -2.48% | -6.68% | `False` |
| `1h` | 29 | 0.439 | 0.44% | -0.14% | -0.72% | -2.46% | `False` |
| `4h` | 35 | 0.130 | -4.90% | -5.60% | -6.30% | -8.40% | `False` |
| `30m` | 37 | 0.561 | -2.45% | -3.19% | -3.93% | -6.15% | `False` |
| `30m` | 16 | 0.242 | 0.92% | 0.60% | 0.28% | -0.68% | `False` |
| `1d` | 4 | 0.008 | -1.21% | -1.29% | -1.37% | -1.61% | `False` |
| `15m` | 86 | 1.303 | -4.12% | -5.84% | -7.56% | -12.72% | `False` |
| `15m` | 48 | 0.727 | 0.57% | -0.39% | -1.35% | -4.23% | `False` |
| `15m` | 37 | 0.561 | -1.44% | -2.18% | -2.92% | -5.14% | `False` |
| `1h` | 16 | 0.242 | 0.48% | 0.16% | -0.16% | -1.12% | `False` |
| `5m` | 149 | 2.258 | 0.95% | -2.03% | -5.01% | -13.95% | `False` |
| `5m` | 115 | 1.742 | 1.25% | -1.05% | -3.35% | -10.25% | `False` |
| `5m` | 50 | 0.758 | 1.18% | 0.18% | -0.82% | -3.82% | `False` |
| `5m` | 79 | 1.197 | 0.28% | -1.30% | -2.88% | -7.62% | `False` |
| `1h` | 13 | 0.197 | 0.77% | 0.51% | 0.25% | -0.53% | `False` |
| `1m` | 27 | 2.700 | -2.43% | -2.97% | -3.51% | -5.13% | `False` |
| `1d` | 7 | 0.014 | -4.47% | -4.61% | -4.75% | -5.17% | `False` |
| `1d` | 7 | 0.014 | -4.18% | -4.32% | -4.46% | -4.88% | `False` |
| `1m` | 35 | 3.500 | -2.42% | -3.12% | -3.82% | -5.92% | `False` |
| `1m` | 19 | 1.900 | -3.31% | -3.69% | -4.07% | -5.21% | `False` |
| `1m` | 13 | 1.300 | -1.83% | -2.09% | -2.35% | -3.13% | `False` |

Interpretation:

NUE produced AQ rank rows, but the exact 1m Bayesian-Markov origin did not survive both hard 5bps/side cost stress and practical trade density. Stop before downstream.

Next:

Preserve as observation and rotate to a materially different family or a same-root variant that widens per-trade excursion before cost stress.
