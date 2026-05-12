# Mendeley v3 Current Re-audit

Run id: `20260511T082950+0800-codex-mendeley-v3-current-reaudit`

## Result

- Gate result: `blocked_mendeley_v3_current_reaudit_no_accepted_manipulation_label_panel`
- Accepted direct `Manipulation` label sources added: `0`
- MainRegimeV2 root-label slots added: `0`
- Manipulation label slots added: `0`
- Raw data committed: `false`
- Runtime code changed: `false`
- Thresholds relaxed: `false`

## File Status

| File | Size bytes | Local status | Prior gate readback |
|---|---:|---|---|
| `Blur_ml_samples.csv` | 346004976 | `verified_prior_gate_still_applicable` | min_lcb=0.9593303773955086; coverage=False; support=True; chronology=blocked_file_order_not_global_chronology |
| `LooksRare_ml_samples.csv` | 38651230 | `verified_prior_gate_still_applicable` | min_lcb=0.9172855899143008; coverage=False; support=False; chronology=blocked_file_order_not_global_chronology |
| `OpenSea_ml_samples.csv` | 2127010916 | `blocked_not_fetched_disk_capacity` | none |
| `gox_ml_samples.csv` | 986063630 | `verified_prior_gate_still_applicable` | min_lcb=0.8871925447016642; coverage=False; support=True; chronology=indirect_source_script_chronology |

## Gox HGB Readback

- Prior gate: `blocked_mendeley_gox_hgb_wash_below_95`
- Calibration Wilson95 / coverage / ECE: `0.9767279547055007` / `0.030348999954851234` / `0.08171197215474314`
- Test Wilson95 / coverage / ECE: `0.9856146629785103` / `0.008994528877575621` / `0.11550138174952651`

## Blockers

- No verified local Mendeley v3 file has an accepted unchanged 95% direct Manipulation gate.
- LooksRare and Blur remain blocked as NFT ML samples without global chronology-grade timestamp evidence.
- Gox HGB remains blocked by test coverage below 0.03 and calibration/test ECE above 0.05 despite Wilson95 above 0.95.
- OpenSea v3 is 2127010916 bytes and is not present locally; current /private/tmp free space is insufficient for a safe bounded fetch.

Next action: Do not promote Mendeley v3 as accepted. Either free enough temp disk and evaluate OpenSea with the unchanged gate, or move to a provenance-preserving Dune nft.wash_trades export path with replayable timestamps.
