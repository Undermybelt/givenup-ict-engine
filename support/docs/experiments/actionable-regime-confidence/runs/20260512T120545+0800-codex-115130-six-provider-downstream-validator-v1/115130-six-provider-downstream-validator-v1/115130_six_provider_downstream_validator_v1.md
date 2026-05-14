# 115130 Six-Provider Downstream Validator v1

Run id: `20260512T120545+0800-codex-115130-six-provider-downstream-validator-v1`
Source AQ root: `20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1`

## Scope
Materialize the 115130 six-provider AQ real-trade JSONL into one downstream ingestion file.
Validate branch path, provider provenance, outcome, failure reason, and quality weight before any ict-engine downstream command consumes it.

## Validation
- Input JSONL files: `12`.
- Records total: `211`.
- Records invalid: `0`.
- Validator pass: `True`.
- Combined JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T120545+0800-codex-115130-six-provider-downstream-validator-v1/real-trades/115130_six_provider_real_trades_validated.jsonl`.

## Provider Counts
- `binance_public`: `52` records.
- `bybit_public`: `51` records.
- `ibkr_midpoint_14d`: `17` records.
- `kraken_public`: `32` records.
- `tradingviewremix_tvr_binance`: `37` records.
- `yfinance`: `22` records.

## Branch Counts
- `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`: `143` records.
- `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`: `68` records.

## Decision
- Ingestion allowed: `True`.
- Evidence class before downstream readback: `market_factor_candidate_pending_downstream`.
- This validator does not promote the candidate and does not call `update_goal`.
