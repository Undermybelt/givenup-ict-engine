# Negative Raw Prune Manifest v3

Run ID: `20260511T130749+0800-codex-negative-raw-prune-v3`

## Scope

- Purpose: keep old Board A negative/provenance runs from re-inflating the repo experiment footprint.
- Preserved: JSON, Markdown reports, checks/assertions, scripts, board markdown, current 12:51+ collaboration run roots, and scoped positive parent-root/direct-evidence artifacts.
- Removed: replay-sized generated CSV intermediates from old runs whose compact assertions already recorded `accepted_gate=none`, `ACCEPTED_95 false`, or `GATE blocked_not_complete`.
- Runtime code changed: false.
- Thresholds changed: false.
- Board cursor changed: false.

## Removed Repo-Local Raw/Intermediate Files

| Path | Size Before | SHA-256 Before | Reason |
|---|---:|---|---|
| `docs/experiments/actionable-regime-confidence/runs/20260511T001642-cross-asset-root-evidence-yfinance/downloaded_prices_1d.csv` | `3.6M` | `a19c949370e9231ebd8de4152a56977944bc716d711c914cd50965e33eac73ed` | old yfinance raw download; run assertion records `accepted_gate: none_for_MainRegimeV2` and compact report remains |
| `docs/experiments/actionable-regime-confidence/runs/20260511T001642-cross-asset-root-evidence-yfinance/downloaded_prices_1h.csv` | `11M` | `c9e764d8fcdbbc4b4c4f31dc0b0d768676f0dd36f143d335da4ea8c0f683fc28` | old yfinance raw download; run assertion records `accepted_gate: none_for_MainRegimeV2` and compact report remains |
| `docs/experiments/actionable-regime-confidence/runs/20260511T001642-cross-asset-root-evidence-yfinance/root-v2/cross_asset_root_feature_table.csv` | `36M` | `df9dd4729f5e0d510c7a5bef2d6298237157522df3bf76398736f464374b56b4` | blocked root feature table; assertion preserves per-root blockers |
| `docs/experiments/actionable-regime-confidence/runs/20260511T005259-codex-persistent-root-state-and-direct-input-audit/root-v2-persistent/persistent_root_state_scores.csv` | `12M` | `8f447116bb3f11afd023c034090ebdf4daf7c12919236ad8eb0af9e32193b5f2` | blocked persistent-score table; assertion records `GATE blocked_not_complete` |
| `docs/experiments/actionable-regime-confidence/runs/20260511T030516-codex-breadth-sector-root-gate/breadth-sector-gate/breadth_sector_root_feature_table.csv` | `11M` | `ed43fbe1dbe6994e54877538ed92f4f0c2f0e416e8246ea3e8163ffad277dc2a` | blocked breadth-sector feature table; assertion records `ACCEPTED_95 false` |
| `docs/experiments/actionable-regime-confidence/runs/20260511T030516-codex-breadth-sector-root-gate/breadth-sector-gate/breadth_sector_root_features.csv` | `7.2M` | `4f71ddf893be70a15987111559a26c9c623635e9512a32b9a31f835d0eabfbab` | generated breadth-sector intermediate; compact gate report remains |
| `docs/experiments/actionable-regime-confidence/runs/20260511T030759-codex-cboe-options-vol-root-gate/options-vol-gate/cboe_options_vol_root_feature_table.csv` | `11M` | `ff524ef6abd7b35f1f22d7d6d2db4d42e247f2eab122eb0c4029d8250e373c38` | blocked CBOE/options-vol feature table; assertion records `ACCEPTED_95 false` |
| `docs/experiments/actionable-regime-confidence/runs/20260511T031433-codex-hmm-markov-root-gate/hmm-markov-gate/hmm_markov_root_feature_table.csv` | `16M` | `58fd9f3c517190406baaad5e64fa3316f638cae887527a0659add193ce54d99b` | blocked HMM/Markov feature table; assertion records `GATE blocked_hmm_markov_root_gate_below_95` |
| `docs/experiments/actionable-regime-confidence/runs/20260511T031433-codex-hmm-markov-root-gate/hmm-markov-gate/hmm_markov_root_posterior_table.csv` | `11M` | `2d86131182dc74532c1ffbd064cca37a8fc520e89b999ecb2884adf49579b9ea` | generated posterior table from blocked HMM/Markov scan; compact gate report remains |

## Verification

- `lsof` returned no open handles for the deleted files before removal.
- Pre-delete selected file total was `118M`.
- JSON/MD/check/script artifacts were not removed.
- Board cursor was not edited to avoid racing other agents.

## Follow-Up Guardrail

Negative or provenance runs should keep raw downloads and replay-sized feature matrices in `/tmp` or `/private/tmp`. Repo-local run roots should keep compact JSON/MD/check evidence and prune generated CSV intermediates once assertions exist.
