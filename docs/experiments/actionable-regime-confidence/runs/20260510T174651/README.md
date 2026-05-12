# Board A Run 20260510T174651

Purpose: durable artifact home for the May 10 Board A actionable-regime-confidence loop.

Source temp roots copied here:

- `/tmp/ict-board-a-regime-confidence-20260510T174651`
- `/tmp/ict-regime-chain-20260509T231052`
- `/tmp/ict-regime-branch-iteration-20260510-1`

Summary:

- Provider availability was physically probed across Yahoo/yfinance, Kraken, IBKR, TradingViewRemix, and local Auto-Quant cache.
- Auto-Quant entry-aligned windows were pushed through CatBoost release probes and ict-engine execution-tree scans.
- QQQ branch evidence was pushed through Auto-Quant import, pre-Bayes, BBN prior init, CatBoost path-ranker training/application, workflow refresh, and execution-tree trace readback.
- No leak-safe 95%-99% actionable regime packet was accepted.

Key evidence:

- Provider matrix: `provider/full-chain/loop4_provider_matrix_summary.json`
- Current Board A provider packet: `provider/current-board/provider-status-agent.json`
- Entry-aligned Auto-Quant windows: `autoquant/autoquant-entry-windows-512-summary.json`
- Leak-safe CatBoost release probe: `catboost/autoquant_entry_release_leaksafe_probe_512.json`
- 512-window execution-tree scan: `execution-tree/entry_scan_512_summary.json`
- Path-ranker score coverage probe: `path-ranker/autoquant-entry-scorecoverage-summary.json`
- Structural feedback readback: `structural-feedback/feedback_vs_scorecoverage_summary.json`
- Full QQQ branch-chain root: `branch-chain/qqq-regime-branch-iteration/`
- V2 target-schema reset: `target_schema_v2.json`
- Artifact hashes: `checks/sha256sums.txt`

Decision:

`abstain_no_calibrated_release_rule`. The only apparent 95% rule was rejected as same-surface execution-tree leakage. Leak-safe rerun returned `no_95_candidate`, and execution-tree readback stayed observe/blocked.
