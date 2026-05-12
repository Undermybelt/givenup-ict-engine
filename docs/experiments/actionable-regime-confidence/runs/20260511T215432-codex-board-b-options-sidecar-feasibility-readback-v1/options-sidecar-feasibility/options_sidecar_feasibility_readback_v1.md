# Options Sidecar Feasibility Readback v1

Run id: `20260511T215432+0800-codex-board-b-options-sidecar-feasibility-readback-v1`.

## Decision

- Gate result: `fail:options_sidecar_single_snapshot_not_trainable`
- Total option rows: `1038`
- Unique option snapshots: `2`
- IV present: `True`; Greeks present: `True`; open interest present: `True`; volume present: `True`
- Branch RC-SPA scored: `false`
- Branch rows emitted: `0`
- Downstream consumption: `not_started:blocked_by_options_sidecar_feasibility`
- Primary blocker: Local options sidecar has IV/Greek snapshot fields but not a historical snapshot time series, so it cannot be aligned to Board A roots across chronological folds or treated as a profitability factor.

## Root-First Interpretation

- Intended path shape would be `main_regime -> options_vol_sidecar_context -> option_iv_skew_oi_factor -> profit_factor`.
- Current local sidecar cannot emit that path across chronological folds because it is only a snapshot readback.
- Do not attach IV/skew/OI as a Board B profit factor until a historical sidecar exists.

## Sources

| Source | Rows | Unique snapshots | Unique expiries | Fields |
|---|---:|---:|---:|---|
| `/Users/thrill3r/Auto-Quant/user_data/data/options/binance_BTC.csv` | 538 | 1 | 12 | iv, greeks |
| `/Users/thrill3r/Auto-Quant/user_data/data/options/bybit_BTC.csv` | 500 | 1 | 9 | iv, greeks, oi, volume |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215432-codex-board-b-options-sidecar-feasibility-readback-v1/options-sidecar-feasibility/options_sidecar_feasibility_readback_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215432-codex-board-b-options-sidecar-feasibility-readback-v1/options-sidecar-feasibility/options_sidecar_feasibility_sources_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215432-codex-board-b-options-sidecar-feasibility-readback-v1/checks/options_sidecar_feasibility_readback_v1_assertions.out`

## Next

- Acquire or build a historical options/dealer-positioning sidecar with >=20 dated snapshots and >=4 chronological folds before using IV/skew/OI as a Board B root-branch profit factor.
