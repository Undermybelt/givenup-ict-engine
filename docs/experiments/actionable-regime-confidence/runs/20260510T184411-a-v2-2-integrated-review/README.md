# Board A A-v2-2 integrated review

Loop ID: `20260510T184411+0800-board-a-v2-2-integrated-review`

Result: `abstain`; accepted gate: `none`.

Blocker: `calibration_support_too_thin;test_support_too_thin;precision_wilson_lcb_below_95`.

This run does not overwrite prior concurrent packets. It integrates:
- same-market QQQ yfinance+IBKR 1h lane
- QQQ yfinance+IBKR + NQ Auto-Quant cache cross-provider lane
- current ict-engine provider/pre-Bayes/policy/workflow readbacks
- prior A-v2 evidence packets from `20260510T183017`, `20260510T183454`, and `20260510T183512`

Best candidate: `qqq_yf_ibkr_nq_cache_cross_provider_agreement_1h_integrated:target_release_long_h8`.

Next: `A7: add realized covariance/correlation eigenstructure as ExtremeStress/ReversalBrewing evidence`.
