# Negative Raw Prune Manifest

Run ID: `20260511T122652+0800-codex-negative-raw-prune-v2`

## Scope

- Purpose: keep Board A negative/provenance artifacts from re-inflating the repo experiment footprint.
- Preserved: JSON/MD/check/script evidence, lane summaries, README files, current Board A markdown, and current 12:xx collaboration run roots.
- Removed: large raw feature/candle matrices from old negative/provenance runs after compact evidence already existed.
- Runtime code changed: false.
- Thresholds changed: false.
- Board cursor changed: false.

## Removed Repo-Local Raw Files

| Path | Size Before | SHA-256 Before | Reason |
|---|---:|---|---|
| `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv` | `51M` | `d6408bce383ca166e349b838c8f1e5147cc2f4524b95ec5500ac9514a778491f` | old raw feature matrix; checks/compact audit preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191125-board-b-nq-5m-factor-research/data/NQ_USD_5m_20110102_20251231_candles.json` | `112M` | `72ba76794fef5a829e8e679bc1f4fa16603985cda58fb44d64e589db5670aac7` | raw candle payload; selected dataset summary and run evidence preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/provider-agreement-v2/nq_autoquant_multitimeframe_agreement_15m/provider_agreement_v2_features.csv` | `237M` | `fa9d1da2de7207caeb52e055c1e84876e12374cdf18b6862bc11d8c2da022731` | duplicate large provider-agreement feature matrix; lane summary and probe report preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260510T233911-main-regime-v2-advanced-root-features/advanced_root_features.csv` | `86M` | `5220bebe3635aff200eff54fc6dabce2f57b7c889cf16d19e9363191d736231c` | old raw feature matrix; checks/compact artifacts preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260511T001100-sector-index-breadth-root-probe/sector_index_breadth_features.csv` | `51M` | `0a8a79d7ef2dfcb6f6cd850e7ed58ae7545600bad1fa168fe1633e742fb4e9f2` | old raw breadth matrix; provider/check evidence preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260510T230938-main-regime-v2-schema-preflight/main_regime_v2_augmented_features.csv` | `56M` | `abf99a52b91d0acf1177cb671528003c8047040c41365f7bd5433f5f5fc75744` | old raw augmented matrix; schema/check evidence preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260511T000420-corrected-root-intermarket-breadth/intermarket_breadth_root_features.csv` | `64M` | `83d83dad8f5105d6730a17735d4a5d4f084ed0ef3cc8ce9d5e1e305dc08ea542` | old raw breadth matrix; checks/compact artifacts preserved |
| `docs/experiments/actionable-regime-confidence/runs/20260510T183512/provider-agreement-v2/nq_autoquant_multitimeframe_agreement_15m/provider_agreement_v2_features.csv` | `237M` | `fa9d1da2de7207caeb52e055c1e84876e12374cdf18b6862bc11d8c2da022731` | duplicate large provider-agreement feature matrix; lane summary and probe report preserved |

## Verification

- `lsof` returned no open handles for the deleted files.
- `find docs/experiments/actionable-regime-confidence/runs -type f -size +50M -print` returned no files after cleanup.
- `find docs/experiments/actionable-regime-confidence/runs -type d -name .venv -print` returned no embedded experiment virtualenvs.
- `du -sh docs/experiments/actionable-regime-confidence/runs` dropped from about `1.3G` before this prune to `459M`.
- `df -h /System/Volumes/Data` showed available space at about `123Gi` after cleanup.

## Follow-Up Guardrail

For negative/provenance runs, keep raw downloads and large feature matrices under `/tmp` or `/private/tmp`, then delete them once compact JSON/MD/check assertions exist. Repo-local run roots should keep only audit-ready evidence, not replay-sized raw payloads.
