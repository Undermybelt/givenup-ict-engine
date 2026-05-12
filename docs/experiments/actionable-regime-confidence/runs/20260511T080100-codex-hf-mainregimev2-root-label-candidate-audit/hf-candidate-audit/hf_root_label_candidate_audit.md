# Hugging Face Root Label Candidate Audit

Run id: `20260511T080100+0800-codex-hf-mainregimev2-root-label-candidate-audit`

Goal achieved: `false`

- Dataset candidates seen: `339`
- Accepted Board A candidates: `0`
- Manual schema candidates: `0`
- Manipulation-only candidates: `3`
- Query errors: `0`

## Status Counts

| Status | Count |
|---|---:|
| `manipulation_candidate_only` | 3 |
| `not_a_full_root_label_panel` | 296 |
| `partial_or_ambiguous_market_label_candidate` | 40 |

## Manual Schema Candidates

- None.

## Partial / Sidecar Candidates

- `phobia76/pmxt-l2-dump` (`manipulation_candidate_only`): may help direct Manipulation evidence, not four-root bar-label panel
- `muhammetakkurt/pump-fun-meme-token-dataset` (`manipulation_candidate_only`): may help direct Manipulation evidence, not four-root bar-label panel
- `Washedashore/thepower` (`manipulation_candidate_only`): may help direct Manipulation evidence, not four-root bar-label panel
- `AdaptLLM/finance-tasks` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `shahadalkhalifa/Crypto_Whitepaper_Labeled` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `takala/financial_phrasebank` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `cryptom/ceval-exam` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `zeroshot/twitter-financial-news-topic` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `zeroshot/twitter-financial-news-sentiment` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `Brianferrell787/financial-news-multisource` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `Josephgflowers/Finance-Instruct-500k` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `JanosAudran/financial-reports-sec` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `nickmuchi/financial-classification` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `TimKoornstra/financial-tweets-sentiment` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `raeidsaqur/NIFTY` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `AyoubChLin/northwind-Stock_rapport` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `FinanceInc/auditor_sentiment` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `CFPB/consumer-finance-complaints` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `SahandNZ/cryptonews-articles-with-price-momentum-labels` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `sujinwo/tsie-market-regime-dataset` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `ckandemir/bitcoin_tweets_sentiment_kaggle` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `raeidsaqur/nifty-rl` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `jppgks/twitter-financial-news-sentiment` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `nickmuchi/financial-text-combo-classification` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots
- `kuroneko5943/stock11` (`partial_or_ambiguous_market_label_candidate`): market label metadata found but not full Bull/Bear/Sideways/Crisis roots

## Accounting

- No HF candidate is accepted as a full independent `Bull/Bear/Sideways/Crisis` label panel.
- Metadata matches are source-discovery only; schema and label columns must be verified before calibration.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `blocked_hf_scan_no_accepted_full_root_label_panel`
