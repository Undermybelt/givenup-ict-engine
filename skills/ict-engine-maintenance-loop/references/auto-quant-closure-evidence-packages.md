# Auto-Quant closure evidence package notes

Session-shaped lesson:
- Import/apply runs can succeed while the ranker path is still non-executable.
- If CatBoost fails with "All features are either constant or ignored", treat it as a feature-support problem, not a reason to stop the closure. Fall back to the documented direct score path (`weighted_feature_sum_v1`) when the evidence package is meant to close path scoring rather than train a new model.
- For each asset, record `n_error`, `n_meta_invalid`, `n_not_run`, `n_ok`, `rows_with_raw_path_score`, and the post-apply workflow status.
- Do not claim live-execution readiness unless the asset has mature target rows and a real workflow snapshot, not just bootstrap readiness.
- If the evidence bundle uses gamma wall / IV / OI / Greeks proxies, label them as proxies unless a live option-chain source was actually consumed.
- Keep the evidence package compact and reproducible: manifest, closure summary, per-asset import logs, apply logs, workflow status.

Observed closure shape from this session:
- Assets covered: ES, NQ, GC, SPY, AAPL
- Import success: all assets had `n_ok=1` and `n_error=0`
- Path score application: direct fallback path, one candidate row per asset
- Workflow result: bootstrap readiness only; no actionable trade command
