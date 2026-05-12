cd docs/experiments/actionable-regime-confidence/runs/20260512T035511-codex-board-b-032157-ltf-synthetic-autoquant-v1/state_ltf_synthetic_autoquant_v1/.deps/auto-quant && uv run --with ta-lib python - <<PY
[monkey-patch run_tomac._synthetic_market precision amount=0.000001 price=0.01]
PY
