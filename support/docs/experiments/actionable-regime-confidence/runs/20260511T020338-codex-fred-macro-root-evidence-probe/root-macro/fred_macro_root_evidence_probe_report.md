# FRED Macro Root Evidence Probe

Run id: `20260511T020338+0800-codex-fred-macro-root-evidence-probe`

This probe joins public FRED rates/credit/financial-condition series to the existing cross-market root feature table and reruns unchanged train-selected root gates. It does not use `future_*` or `target_*` fields as predictors.

Rows evaluated: 28517.
Features used: treasury_10y_2y_spread, treasury_10y_3m_spread, high_yield_oas, corp_oas, financial_conditions, fred_vix_close, treasury_10y_2y_spread_chg5, treasury_10y_2y_spread_chg20, treasury_10y_2y_spread_rank252, treasury_10y_3m_spread_chg5, treasury_10y_3m_spread_chg20, treasury_10y_3m_spread_rank252, high_yield_oas_chg5, high_yield_oas_chg20, high_yield_oas_rank252, corp_oas_chg5, corp_oas_chg20, corp_oas_rank252, financial_conditions_chg5, financial_conditions_chg20, financial_conditions_rank252, fred_vix_close_chg5, fred_vix_close_chg20, fred_vix_close_rank252, vix_level_rank252, vix3m_vix_log_ratio, vix_term_rank252, cross_asset_risk_on_score16, credit_breadth_score16, crypto_risk_score16, macro_stress_score16, qqq_spy_rel16, iwm_spy_rel16, rsp_spy_rel16, xly_xlp_rel16, hyg_lqd_rel16, eth_btc_rel16.

| Root | State | Rule | Cal LCB | Test LCB | Test Support | Blockers |
|---|---|---|---:|---:|---:|---|
| Bull | blocked | `treasury_10y_3m_spread_chg5 >= 0.31 AND rsp_spy_rel16 >= 0.000381775351933` | 0.036223 | 0.000000 | 0 | calibration_support_below_50, test_support_below_50, calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_instruments_below_2, test_market_contexts_below_2, test_timeframes_below_2 |
| Bear | blocked | `treasury_10y_2y_spread_chg20 >= 0.32 AND treasury_10y_3m_spread_chg5 >= 0.1` | 0.325903 | 0.000000 | 0 | calibration_support_below_50, test_support_below_50, calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_instruments_below_2, test_market_contexts_below_2, test_timeframes_below_2 |
| Sideways | blocked | `vix_term_rank252 >= 1 AND financial_conditions_rank252 <= 0.00396825396825` | 0.000000 | 0.000000 | 0 | calibration_support_below_50, test_support_below_50, calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_instruments_below_2, test_market_contexts_below_2, test_timeframes_below_2 |
| Crisis | blocked | `corp_oas_chg5 >= 0.05 AND treasury_10y_3m_spread_chg20 <= -0.39` | 0.158217 | 0.000000 | 0 | calibration_support_below_50, test_support_below_50, calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_instruments_below_2, test_market_contexts_below_2, test_timeframes_below_2 |

Decision: `none_for_new_macro_roots`.
Accepted from this run: none.
Missing from this run: Bull, Bear, Sideways, Crisis.
Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
