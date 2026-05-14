# External Label Request Package v3

Run ID: `20260511T094002+0800-codex-external-label-request-package-v3`

## Result

- Active taxonomy: `MainRegimeV2`.
- Missing/rejected parent-root source-label slots: `564`.
- Missing by root: `{'Bull': 141, 'Bear': 141, 'Sideways': 141, 'Crisis': 141}`.
- Missing by provider: `{'yfinance': 456, 'kraken_public_lowpollution_http': 108}`.
- Missing by timeframe: `{'1m': 68, '5m': 68, '15m': 68, '30m': 68, '1h': 68, '1d': 44, '1w': 44, '1mo': 68, '4h': 68}`.
- Auth/export paths from latest preflight: `{'dune_ready': False, 'finra_ready': False, 'fred_ready_sidecar_only': False, 'huggingface_ready': False, 'kaggle_ready': False, 'sec_api_ready': False, 'tradingview_config_present': True}`.
- Accepted parent-root sources added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_external_label_request_package_created_no_new_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Artifacts

- Missing-slot request CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/missing_parent_root_label_slots_request_v3.csv`
- Parent-root panel schema: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/parent_root_label_panel_schema_v3.csv`
- Direct Manipulation row schema: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/direct_manipulation_rows_schema_v3.csv`

## Reject Rules

- Do not use HMM/GMM/cluster IDs as independent labels.
- Do not use OHLCV/technical-indicator/Pine-generated labels as parent-root completion labels.
- Do not use future-return labels, strategy predictions, or model service outputs as source labels.
- Do not use near-underlying proxy labels unless the source explicitly labels the requested instrument.
- Do not use document indexes, methodology papers, search surfaces, or credentials alone as accepted evidence.
- Do not accept Manipulation from ThinLiquidity/session-liquidity/sweep/volume-ratio proxies.

## Next Action

Fill the v3 request CSV with an exact-underlying independent parent-root label panel, or provide authenticated direct Manipulation positive/negative rows following the schema.
