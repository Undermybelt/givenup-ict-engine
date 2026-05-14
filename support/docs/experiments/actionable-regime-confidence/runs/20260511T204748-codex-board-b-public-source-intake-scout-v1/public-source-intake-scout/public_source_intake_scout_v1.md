# Board B Public Source Intake Scout v1

Run id: `20260511T204748+0800-codex-board-b-public-source-intake-scout-v1`.

## Decision

- Gate result: `fail:no_verifier_ready_profitability_or_source_intake_rows`
- Downstream consumption: `not_started:source_scout_only`
- Board B profitability rows added: `0`
- Ready source-intake roots populated: `0`
- Raw data committed to repo: `false`

## Inputs Checked

The payloads were downloaded by a concurrent `/tmp` scout and inspected without committing raw data into the repo.

| Dataset | Local Payload | License | Rows / Range | Source Label Status | Board B Status |
|---|---|---|---:|---|---|
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | `/tmp/ict-engine-public-source-intake-scout/nifty` | CC BY 4.0 | market regime `3,464` rows from `2012-02-02` to `2026-03-20`; behavior regime `3,846` rows from `2010-09-20` to `2026-03-20`; features `3,500` rows from `2012-02-02` to `2026-03-20` | Daily NIFTY 500 HMM labels exist: `Durable/Fragile`, `Calm/Choppy/Stress`, `Trending/Mean-Reverting/Noisy`, plus confidence fields | Useful source-label candidate only; not a Board B profitability packet because it has no standardized provenance file, no source-owned trade/PnL rows, no matched controls, and no direct scoped Manipulation bridge |
| `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes` | `/tmp/ict-engine-public-source-intake-scout/macro` | CC-BY-NC-SA-4.0 | `4,150` rows from `2014-10-17` to `2026-02-25` | Cross-asset prices/features exist, but the CSV does not include source-owned regime labels | Useful panel-feature candidate only; not an accepted source-label or profitability input |

## Readback

- NIFTY source labels could support a future cross-market/source-label equivalence intake if they are converted into `source_label_equivalence_rows.csv` plus `source_label_equivalence_provenance.json`.
- The macro dataset can support future cross-asset feature construction, but it cannot repair Board B alone because it lacks source-owned regime labels and direct Manipulation PnL rows.
- No Pre-Bayes / BBN / CatBoost / execution-tree consumption was started because there is no RC-SPA-passing profitability packet and no verifier-ready source intake.

## Next

- B2R-repeat: do not treat the `/tmp` Kaggle payload as hidden promotion evidence. Convert only a provenance-clean source-label package into the required `/tmp/ict-engine-source-label-equivalence-intake` shape, or continue sourcing trade/PnL-usable direct Manipulation positives plus matched controls.
