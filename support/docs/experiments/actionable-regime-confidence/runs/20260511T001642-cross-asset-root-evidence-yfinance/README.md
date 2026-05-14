# Cross-Asset MainRegimeV2 Root Evidence - yfinance

This run downloads yfinance QQQ and BTC-USD target rows on 1h/1d and adds cross-asset risk, credit, breadth, sector, volatility-term, dollar, and crypto-relative features. The unchanged 95% gate is applied with chronological train/calibration/test splits. Manipulation remains fail-closed because yfinance does not provide direct tick/order-flow/L2/order-lifecycle evidence.
