# Non-Kaggle Source Candidate Scan

Run ID: `20260511T101015+0800-codex-nonkaggle-source-candidate-scan`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Scope

Search outside the current Kaggle public `market regime` hits for any candidate that can fill one of:

- exact-underlying intraday/monthly `MainRegimeV2` parent-root labels for `Bull`, `Bear`, `Sideways`, or `Crisis`;
- Kraken crypto parent-root labels;
- real direct `Manipulation` positive/negative rows.

## Candidate Readback

| Candidate | URL | Shape | Decision |
|---|---|---|---|
| `hidden-regime` | `https://pypi.org/project/hidden-regime/` | Python/tooling style regime detector using market data such as yfinance and HMM-style classification | Rejected: method/proxy output, not an independent exact-underlying source-label panel |
| `Abraxasccs/kraken-market-data` | `https://huggingface.co/datasets/Abraxasccs/kraken-market-data` | Raw Kraken historical market-data candidate | Rejected: raw market data without `MainRegimeV2` root labels or direct `Manipulation` positive/negative rows |
| non-Kaggle web hits across GitHub/HF/Zenodo/Mendeley | mixed search results | Daily/monthly crisis, volatility, herding, HMM, sentiment, or methodology/proxy artifacts | Rejected: no attachable exact-underlying intraday/monthly or Kraken parent-root label panel found |

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_nonkaggle_source_scan_no_attachable_parent_root_or_direct_rows`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Use the Zenodo DEX self-trade preflight candidate for a full or larger bounded chronological direct-`Manipulation` gate, or acquire authenticated exact-underlying intraday/monthly `MainRegimeV2` parent-root labels. Do not promote HMM/yfinance/raw-Kraken proxy outputs.
