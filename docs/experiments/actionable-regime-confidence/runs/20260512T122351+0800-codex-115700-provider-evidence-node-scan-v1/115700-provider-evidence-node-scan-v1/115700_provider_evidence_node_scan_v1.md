# 115700 Provider Evidence Node Scan v1

Run id: `20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
Source enriched chain: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`

## Scope
Read the six-provider 1h CSV panel from `115700`, align provider features to the enriched `121347` trade rows, and identify candidate BBN evidence nodes that may reduce the current `factor_alignment=mixed` / `pass_neutralized` bottleneck.
This is candidate evidence only. It does not mutate BBN priors/CPDs, CatBoost models, or execution-tree gates.

## Coverage
- Provider CSVs: `{'yfinance': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/yfinance_btc_usd_1h.csv', 'rows': 971, 'first_ts': '2026-04-01T00:00:00+00:00', 'last_ts': '2026-05-11T23:00:00+00:00'}, 'kraken_public': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/kraken_xbtusd_1h.csv', 'rows': 721, 'first_ts': '2026-04-12T04:00:00+00:00', 'last_ts': '2026-05-12T04:00:00+00:00'}, 'binance_public': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/binance_btcusdt_1h.csv', 'rows': 985, 'first_ts': '2026-04-01T00:00:00+00:00', 'last_ts': '2026-05-12T00:00:00+00:00'}, 'bybit_public': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/bybit_btcusdt_linear_1h.csv', 'rows': 985, 'first_ts': '2026-04-01T00:00:00+00:00', 'last_ts': '2026-05-12T00:00:00+00:00'}, 'tvr_default_binance': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/tvr_default_binance_btcusdt_1h.csv', 'rows': 720, 'first_ts': '2026-04-12T05:00:00+00:00', 'last_ts': '2026-05-12T04:00:00+00:00'}, 'ibkr_paxos_long_midpoint': {'path': 'docs/experiments/actionable-regime-confidence/runs/20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1/provider-csv/BTC_1h_midpoint.csv', 'rows': 783, 'first_ts': '2026-03-31T20:00:00+00:00', 'last_ts': '2026-05-12T04:00:00+00:00'}}`.
- Trade rows: `237`; matched feature rows: `237`.
- Overall outcome: wins `81`, losses `156`, win rate `0.341772`, loss rate `0.658228`.

## Top Candidate Evidence Nodes
- 1. `provider_rv_median_24h` separation `0.463486` bins `{'high': {'rows': 78, 'wins': 48, 'losses': 30, 'win_rate': 0.615385, 'loss_rate': 0.384615, 'avg_pnl': 23.0331}, 'low': {'rows': 80, 'wins': 21, 'losses': 59, 'win_rate': 0.2625, 'loss_rate': 0.7375, 'avg_pnl': -8.658247}, 'mid': {'rows': 79, 'wins': 12, 'losses': 67, 'win_rate': 0.151899, 'loss_rate': 0.848101, 'avg_pnl': -16.302794}}`.
- 2. `provider_return_dispersion_24h` separation `0.372418` bins `{'high': {'rows': 76, 'wins': 36, 'losses': 40, 'win_rate': 0.473684, 'loss_rate': 0.526316, 'avg_pnl': 6.143126}, 'low': {'rows': 79, 'wins': 8, 'losses': 71, 'win_rate': 0.101266, 'loss_rate': 0.898734, 'avg_pnl': -14.896473}, 'mid': {'rows': 82, 'wins': 37, 'losses': 45, 'win_rate': 0.45122, 'loss_rate': 0.54878, 'avg_pnl': 6.413963}}`.
- 3. `provider_range_pos_median_24h` separation `0.343519` bins `{'high': {'rows': 81, 'wins': 42, 'losses': 39, 'win_rate': 0.518519, 'loss_rate': 0.481481, 'avg_pnl': 13.619044}, 'low': {'rows': 80, 'wins': 14, 'losses': 66, 'win_rate': 0.175, 'loss_rate': 0.825, 'avg_pnl': -9.647738}, 'mid': {'rows': 76, 'wins': 25, 'losses': 51, 'win_rate': 0.328947, 'loss_rate': 0.671053, 'avg_pnl': -6.780556}}`.
- 4. `provider_return_median_abs_1h` separation `0.193821` bins `{'high': {'rows': 80, 'wins': 32, 'losses': 48, 'win_rate': 0.4, 'loss_rate': 0.6, 'avg_pnl': 8.956794}, 'low': {'rows': 82, 'wins': 18, 'losses': 64, 'win_rate': 0.219512, 'loss_rate': 0.780488, 'avg_pnl': -11.040633}, 'mid': {'rows': 75, 'wins': 31, 'losses': 44, 'win_rate': 0.413333, 'loss_rate': 0.586667, 'avg_pnl': 0.063862}}`.
- 5. `provider_return_dispersion_4h` separation `0.180538` bins `{'high': {'rows': 79, 'wins': 35, 'losses': 44, 'win_rate': 0.443038, 'loss_rate': 0.556962, 'avg_pnl': 10.04565}, 'low': {'rows': 80, 'wins': 21, 'losses': 59, 'win_rate': 0.2625, 'loss_rate': 0.7375, 'avg_pnl': -7.40606}, 'mid': {'rows': 78, 'wins': 25, 'losses': 53, 'win_rate': 0.320513, 'loss_rate': 0.679487, 'avg_pnl': -4.93744}}`.
- 6. `provider_trend_abs_median_24h` separation `0.152456` bins `{'high': {'rows': 78, 'wins': 21, 'losses': 57, 'win_rate': 0.269231, 'loss_rate': 0.730769, 'avg_pnl': 0.389096}, 'low': {'rows': 83, 'wins': 35, 'losses': 48, 'win_rate': 0.421687, 'loss_rate': 0.578313, 'avg_pnl': 0.211515}, 'mid': {'rows': 76, 'wins': 25, 'losses': 51, 'win_rate': 0.328947, 'loss_rate': 0.671053, 'avg_pnl': -3.051368}}`.
- 7. `provider_return_dispersion_1h` separation `0.142949` bins `{'high': {'rows': 80, 'wins': 34, 'losses': 46, 'win_rate': 0.425, 'loss_rate': 0.575, 'avg_pnl': 4.766556}, 'low': {'rows': 78, 'wins': 22, 'losses': 56, 'win_rate': 0.282051, 'loss_rate': 0.717949, 'avg_pnl': -3.352321}, 'mid': {'rows': 79, 'wins': 25, 'losses': 54, 'win_rate': 0.316456, 'loss_rate': 0.683544, 'avg_pnl': -3.846104}}`.
- 8. `provider_return_median_abs_24h` separation `0.136842` bins `{'high': {'rows': 81, 'wins': 29, 'losses': 52, 'win_rate': 0.358025, 'loss_rate': 0.641975, 'avg_pnl': 6.624813}, 'low': {'rows': 80, 'wins': 32, 'losses': 48, 'win_rate': 0.4, 'loss_rate': 0.6, 'avg_pnl': -1.944516}, 'mid': {'rows': 76, 'wins': 20, 'losses': 56, 'win_rate': 0.263158, 'loss_rate': 0.736842, 'avg_pnl': -7.434833}}`.

## Decision
- Gate: `115700_provider_evidence_node_scan_v1=provider_evidence_node_candidates_identified_no_promotion`.
- The scan found candidate provider-context features, but none is an accepted `>=95%` regime gate. They must be replayed chronologically and across instrument/period/provider contexts before any BBN likelihood mutation.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1/115700-provider-evidence-node-scan-v1/115700_provider_evidence_node_scan_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1/115700-provider-evidence-node-scan-v1/115700_provider_evidence_node_candidates_v1.csv`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1/115700-provider-evidence-node-scan-v1/prompt_to_artifact_checklist_115700_provider_evidence_node_scan_v1.csv`
