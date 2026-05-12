python3 docs/experiments/actionable-regime-confidence/runs/20260512T151746+0800-codex-ob-fvg-trend-pullback-screen-v1/scripts/ob_fvg_trend_pullback_screen.py \
  --output-dir docs/experiments/actionable-regime-confidence/runs/20260512T151746+0800-codex-ob-fvg-trend-pullback-screen-v1/summaries \
  --exit-horizon 12 \
  --max-wait 24 \
  --confluence-window 24 \
  --min-trades 50 \
  --source Binance BTCUSDT docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/binance_btcusdt_1h_20170817_20260512.normalized.csv 0.0010 \
  --source IBKR SPY docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/ibkr_spy_1h_5y.normalized.csv 0.0005 \
  --source Yahoo ES docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/yahoo_es_1h_20240513_20260512.normalized.csv 0.0005
