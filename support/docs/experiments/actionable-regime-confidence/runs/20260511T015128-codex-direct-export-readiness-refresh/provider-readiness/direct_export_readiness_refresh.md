# Direct Export Readiness Refresh

Run id: `20260511T015128+0800-codex-direct-export-readiness-refresh`

Objective: re-check whether direct L2/L3/MBO/order-lifecycle data or tooling is now available for the active MainRegimeV2 `Manipulation` root gate.

## Readback

- Databento CLI: missing.
- DBN CLI: missing.
- Python `databento`: missing.
- Python `pyarrow`: missing.
- Python `ib_insync` / `ibapi`: missing.
- `zstdcat` and `bsdtar`: present, enough for header/container inspection only.
- Databento env/key file: absent.
- IBKR/TWS listening ports `4001/4002/7496/7497`: absent in this refresh.
- TradingViewRemix config: present, but chart/bar access is not direct L2/L3/order-lifecycle manipulation proof.
- Targeted local file search found large Tomac OHLCV/cleaned bar material and symbology files, but no new qualifying MBO/MBP/L2/L3/order-lifecycle dataset.
- `GLBX-20260404-NQ.zip` contains `condition.json`, `metadata.json`, `manifest.json`, and `glbx-mdp3-20100606-20260403.ohlcv-1m.csv`.
- `gc future 2021-2025/databento.rar` contains `gc_201101_202604.csv` and `nq_201101_202604.csv`.
- Tomac Databento metadata for NQ, GC, ES, YM, and 6E all reports `schema: ohlcv-1m`, `encoding: csv`; no MBO/MBP/L2 schema was found in these manifests.

## Gate Result

- Provider export ready now: false.
- Qualifying direct manipulation input sets: 0.
- `Manipulation`: `blocked_missing_required_inputs`.
- `Bull`: `missing_95_root_packet`.
- `Bear`: `missing_95_root_packet`.
- `Sideways`: `missing_95_root_packet`.
- `Crisis`: prior accepted 95 root evidence preserved only.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Trade usable: false.

## Next Action

Provide or enable a Databento-style historical MBO/L3 export with credentials/tooling, or place an already exported calibration-grade direct L2/L3/MBO/order-lifecycle dataset in a documented local path before rerunning the `Manipulation` gate.
