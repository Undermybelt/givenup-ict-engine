# Manipulation Stratified Action Surface v1

Run ID: `20260511T205050+0800-codex-board-b-manipulation-stratified-action-surface-v1`

## Decision

- Gate result: `fail:no_tradeable_manipulation_stratified_action_surface`
- Tradeable candidates: `[]`
- Strata evaluated: `13`
- Summary rows: `429`
- Branch rows: `734208`
- Best trade: `coin_neo` / `event_short` / `48h`
- Best trade mean net: `0.013325`
- Best trade LCB 5%: `0.003760`
- Best trade specificity LCB 5%: `0.019594`
- Best specificity: `coin_trx` / `event_short` / `48h`
- Best specificity edge: `0.068581`
- Best specificity LCB 5%: `0.044735`
- Downstream consumption: `not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa`

## Strata

| Stratum | Description | Quote | Coins |
|---|---|---|---|
| `all_events` | all provider-reconstructed direct events | `all` | `all` |
| `quote_usdt` | USDT-quoted provider rows | `USDT` | `all` |
| `quote_btc` | BTC-quoted provider rows | `BTC` | `all` |
| `quote_btc_dense_altbasket` | BTC-quoted coins with >=250 positive and >=250 control rows | `BTC` | `ADA,BAT,ETC,LSK,NEO,OMG,STORJ,TRX,XRP` |
| `coin_ada` | ADA/BTC dense single-coin stratum | `BTC` | `ADA` |
| `coin_bat` | BAT/BTC dense single-coin stratum | `BTC` | `BAT` |
| `coin_etc` | ETC/BTC dense single-coin stratum | `BTC` | `ETC` |
| `coin_lsk` | LSK/BTC dense single-coin stratum | `BTC` | `LSK` |
| `coin_neo` | NEO/BTC dense single-coin stratum | `BTC` | `NEO` |
| `coin_omg` | OMG/BTC dense single-coin stratum | `BTC` | `OMG` |
| `coin_storj` | STORJ/BTC dense single-coin stratum | `BTC` | `STORJ` |
| `coin_trx` | TRX/BTC dense single-coin stratum | `BTC` | `TRX` |
| `coin_xrp` | XRP/BTC dense single-coin stratum | `BTC` | `XRP` |

## Top Summary Rows

| Stratum | Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean | Ctrl Mean | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `coin_omg` | `cooldown_relative` | 48h | 316 | 296 | 11 | 0.014044 | -0.014063 | 0.028107 | 0.004678 | 0.016886 | 0.4545 | 0.6364 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500` |
| `coin_ada` | `cooldown_relative` | 18h | 468 | 303 | 8 | 0.012241 | 0.036797 | -0.024555 | 0.004544 | -0.041422 | 0.3333 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_neo` | `event_short` | 48h | 400 | 407 | 12 | 0.013325 | -0.019370 | 0.032695 | 0.003760 | 0.019594 | 0.7500 | 0.5833 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `cooldown_relative` | 6h | 470 | 303 | 8 | 0.007360 | 0.009972 | -0.002612 | 0.003713 | -0.009657 | 0.4444 | 0.6250 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `coin_ada` | `cooldown_relative` | 8h | 470 | 303 | 8 | 0.008525 | 0.019516 | -0.010991 | 0.003615 | -0.020162 | 0.4444 | 0.6250 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `coin_omg` | `event_long` | 48h | 316 | 296 | 11 | 0.012544 | -0.015563 | 0.028107 | 0.003178 | 0.016886 | 0.4545 | 0.6364 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct` |
| `coin_ada` | `cooldown_relative` | 3h | 470 | 303 | 8 | 0.006378 | 0.004356 | 0.002022 | 0.003128 | -0.003590 | 0.7778 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `quote_usdt` | `cooldown_relative` | 48h | 9157 | 3113 | 12 | 0.004387 | 0.037998 | -0.033611 | 0.003065 | -0.035728 | 0.5000 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `event_long` | 18h | 468 | 303 | 8 | 0.010741 | 0.035297 | -0.024555 | 0.003044 | -0.041422 | 0.3333 | 0.5000 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `cooldown_relative` | 12h | 470 | 303 | 8 | 0.008337 | 0.022260 | -0.013923 | 0.002770 | -0.025121 | 0.3333 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `all_events` | `cooldown_relative` | 48h | 13448 | 7088 | 12 | 0.004027 | 0.022206 | -0.018179 | 0.002678 | -0.020722 | 0.4167 | 0.2500 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `quote_usdt` | `cooldown_relative` | 36h | 9108 | 3113 | 12 | 0.003550 | 0.030011 | -0.026461 | 0.002395 | -0.028370 | 0.5833 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_xrp` | `event_short` | 6h | 410 | 328 | 9 | 0.007656 | 0.000157 | 0.007499 | 0.002393 | 0.001895 | 0.5556 | 0.5556 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `all_events` | `cooldown_relative` | 36h | 13389 | 7121 | 12 | 0.003537 | 0.015566 | -0.012030 | 0.002339 | -0.014215 | 0.5000 | 0.2500 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `event_long` | 6h | 470 | 303 | 8 | 0.005860 | 0.008472 | -0.002612 | 0.002213 | -0.009657 | 0.4444 | 0.6250 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `coin_ada` | `event_long` | 8h | 470 | 303 | 8 | 0.007025 | 0.018016 | -0.010991 | 0.002115 | -0.020162 | 0.4444 | 0.6250 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `coin_ada` | `cooldown_relative` | 4h | 470 | 303 | 8 | 0.005357 | 0.006631 | -0.001275 | 0.002085 | -0.007268 | 0.5556 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_omg` | `cooldown_relative` | 36h | 314 | 296 | 11 | 0.010831 | -0.015180 | 0.026011 | 0.001987 | 0.015390 | 0.3636 | 0.5455 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `cooldown_relative` | 2h | 470 | 303 | 8 | 0.004166 | 0.002879 | 0.001288 | 0.001928 | -0.003518 | 0.6667 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `cooldown_relative` | 24h | 468 | 303 | 8 | 0.010811 | 0.048617 | -0.037807 | 0.001856 | -0.059598 | 0.4444 | 0.3750 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_xrp` | `event_short` | 12h | 406 | 328 | 9 | 0.008759 | 0.004147 | 0.004612 | 0.001793 | -0.002949 | 0.5556 | 0.5556 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_etc` | `cooldown_relative` | 8h | 405 | 373 | 10 | 0.005380 | -0.006900 | 0.012280 | 0.001693 | 0.008195 | 0.7000 | 0.8000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500` |
| `coin_ada` | `event_long` | 3h | 470 | 303 | 8 | 0.004878 | 0.002856 | 0.002022 | 0.001628 | -0.003590 | 0.5556 | 0.5000 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `quote_usdt` | `event_long` | 48h | 9157 | 3113 | 12 | 0.002887 | 0.036498 | -0.033611 | 0.001565 | -0.035728 | 0.5000 | 0.5000 | `fail:reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_xrp` | `event_short` | 4h | 410 | 328 | 9 | 0.006664 | -0.000783 | 0.007447 | 0.001502 | 0.001948 | 0.5556 | 0.6667 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct` |
| `coin_storj` | `event_short` | 18h | 300 | 298 | 9 | 0.008710 | 0.014112 | -0.005402 | 0.001421 | -0.014788 | 0.5556 | 0.4444 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `all_events` | `cooldown_relative` | 24h | 13448 | 7085 | 12 | 0.002414 | 0.008482 | -0.006068 | 0.001388 | -0.007768 | 0.5000 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_bat` | `cooldown_relative` | 2h | 253 | 250 | 9 | 0.004971 | 0.002945 | 0.002025 | 0.001276 | -0.002729 | 0.5556 | 0.3333 | `fail:diagnostic_only:not_tradeable_profit_row|reject_positive_rows_lt500|reject_control_rows_lt500|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `coin_ada` | `event_long` | 12h | 470 | 303 | 8 | 0.006837 | 0.020760 | -0.013923 | 0.001270 | -0.025121 | 0.3333 | 0.5000 | `fail:reject_positive_rows_lt500|reject_control_rows_lt500|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `all_events` | `cooldown_relative` | 18h | 13402 | 7060 | 12 | 0.002154 | 0.005843 | -0.003690 | 0.001269 | -0.005090 | 0.5833 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |

## Interpretation

- Strata are predeclared by quote and non-return coverage density; no RC-SPA/action-surface thresholds were relaxed.
- `event_long` and `event_short` include roundtrip cost and are the only tradeable action probes.
- `cooldown_relative` remains diagnostic only and cannot promote downstream.
- Full Board B promotion remains blocked unless Bull, Bear, Sideways, Crisis, and scoped Manipulation all pass branch RC-SPA.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205050-codex-board-b-manipulation-stratified-action-surface-v1/manipulation-stratified-action-surface/manipulation_stratified_action_surface_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205050-codex-board-b-manipulation-stratified-action-surface-v1/manipulation-stratified-action-surface/manipulation_stratified_action_surface_summary_v1.csv`
- Branch rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205050-codex-board-b-manipulation-stratified-action-surface-v1/manipulation-stratified-action-surface/manipulation_stratified_action_surface_branch_rows_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205050-codex-board-b-manipulation-stratified-action-surface-v1/checks/manipulation_stratified_action_surface_v1_assertions.out`

## Next

- B2R-repeat: scoped Manipulation remains fail-closed; use a new source-owned exit dataset or stop treating direct-event overlay as a tradable branch until source/PnL changes.
