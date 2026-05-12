# Negative Artifact Cleanup Manifest

Run ID: `20260511T121520+0800-codex-negative-artifact-cleanup`

## Scope

- Purpose: prevent Board A negative/provenance runs from exhausting local disk.
- Preserved: repo-local JSON/MD/check/script evidence artifacts, the current Board A markdown, and accepted positive direct-evidence primary raw clone `/private/tmp/ict-regime-mehrnoom-pump-dump`.
- Removed: disposable raw caches, stale failed/provenance temp workdirs, duplicated repo-local virtualenv dependency caches.
- Runtime code changed: false.
- Thresholds changed: false.
- Board cursor changed: false.

## Disk Result

- Before cleanup: Data volume had about `2.8Gi` free.
- After raw temp cleanup and repo-local virtualenv pruning: Data volume had about `116Gi` free.
- Repo Board A experiment footprint after cleanup: `1.3G`.

## Removed `/private/tmp` Raw/Cache Workdirs

| Path | Size Before | Reason |
|---|---:|---|
| `/private/tmp/ict-regime-bayi-gdrive` | `3.0G` | failed direct `Manipulation` Bayi-Hu gate raw cache; repo evidence preserved |
| `/private/tmp/ict-regime-chain-20260509T231052` | `2.7G` | stale full-chain/provenance temp state; no process held it open |
| `/private/tmp/ict-real-regime-selector-20260510T020632Z` | `1.3G` | stale regime-selector temp state; no process held it open |
| `/private/tmp/ict-regime-mendeley-wash-trading` | `977M` | failed/provenance Mendeley raw cache; repo evidence preserved |
| `/private/tmp/ict-regime-verified-20260509T110030` | `635M` | stale verification temp state; no process held it open |
| `/private/tmp/ict-loop-regime-first-20260510T035355Z` | `628M` | stale loop temp state; no process held it open |
| `/private/tmp/ict-regime-hf-tsie` | `564M` | failed/provenance HF/TSIE source cache; repo evidence preserved |
| `/private/tmp/ict-regime-tsie-parent-root` | `564M` | failed/provenance TSIE parent-root cache; repo evidence preserved |
| `/private/tmp/uv-cache-ict-regime` | `360M` | disposable dependency cache |
| `/private/tmp/ict-regime-mehrnoom-pump-dump-lfs-cache` | `250M` | disposable LFS cache; accepted primary raw clone preserved |

## Removed Repo-Local Dependency Caches

| Path | Size Before | Reason |
|---|---:|---|
| `docs/experiments/actionable-regime-confidence/runs/20260510T191144-board-b-factor-research-mtf1h/ict-engine/state/.deps/auto-quant/.venv` | `559M` | duplicated generated virtualenv, not evidence |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/auto-quant/auto-quant/.deps/auto-quant/.venv` | `559M` | duplicated generated virtualenv, not evidence |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/autoquant/state/auto-quant/auto-quant/.deps/auto-quant/.venv` | `559M` | duplicated generated virtualenv, not evidence |

## Verification

- `lsof +D` returned no open files for the largest deletion targets checked before removal.
- Post-delete `du` confirmed selected `/private/tmp` targets no longer exist.
- Post-delete `find ... .venv` found no remaining embedded experiment virtualenvs under Board A runs.
- Post-cleanup `df -h` showed `/System/Volumes/Data` at about `311Gi` used and `116Gi` available.

## Follow-Up Guardrail

Future negative/provenance runs should keep raw downloads under `/tmp` or `/private/tmp`, write only compact JSON/MD/check artifacts under `docs/experiments/actionable-regime-confidence/runs/`, and delete raw caches once the assertion artifact exists.
