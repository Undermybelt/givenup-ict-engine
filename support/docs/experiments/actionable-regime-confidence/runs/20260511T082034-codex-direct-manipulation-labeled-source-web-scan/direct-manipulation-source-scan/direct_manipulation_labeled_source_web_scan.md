# Direct Manipulation Labeled Source Web Scan

Run id: `20260511T082034+0800-codex-direct-manipulation-labeled-source-web-scan`

## Result

- Candidate sources inspected: `5`
- Accepted direct `Manipulation` label sources added: `0`
- MainRegimeV2 root-label slots added: `0`
- Manipulation label slots added: `0`

## Source Dispositions

| Source | URL | Decision | Reason |
|---|---|---|---|
| Mendeley Data: Detecting Crypto Wash Trades via Machine Learning | `https://data.mendeley.com/datasets/4hyxfwzpgg` | `candidate_reaudit_required` | The current public page describes trade rows with a binary legitimate/wash label and a related GitHub repository. This is the strongest direct-manipulation candidate, but Board A cannot accept it until the current files are re-fetched and the unchanged chronological support, coverage, ECE, and positive/negative control gates pass. |
| GitHub: nft_wash_trading | `https://github.com/niuniu-zhang/nft_wash_trading` | `candidate_code_provenance_only` | Related code can explain feature/label construction, but code alone is not an accepted label panel. |
| Dune: `nft.wash_trades` | `https://docs.dune.com/data-catalog/curated/nft-trades/evm/nft-wash-trades` | `candidate_export_required` | Curated wash-trade table appears relevant, but it must be exported with timestamps, positive/negative windows, and replayable provenance before calibration. |
| Bitquery wash-trading detector label module | `https://docs.bitquery.io/docs/usecases/wash-trading-detector/prepare-data/label/` | `rule_label_sidecar_only` | Rule-generated labels are useful sidecar/provenance, but they are not independent labels until validated against accepted source windows. |
| AnChain / NFT wash-trading papers | `https://arxiv.org/abs/2305.01543` | `paper_method_provenance_only` | Useful definition/method provenance, but no directly attached Board A source-label panel was materialized in this run. |

## Accounting

- Goal achieved: `false`
- Gate result: `blocked_direct_manipulation_labeled_sources_need_reaudit_or_export`
- Runtime code changed: false
- Thresholds relaxed: false
- Raw data committed: false
- Trade usable: false

## Next Action

Run a bounded Mendeley v3 re-fetch/re-audit first. If the current files still fail chronological coverage/ECE or positive/negative control gates, try a Dune `nft.wash_trades` export path. Do not count Bitquery rule labels or paper definitions as accepted labels without independent validation.
