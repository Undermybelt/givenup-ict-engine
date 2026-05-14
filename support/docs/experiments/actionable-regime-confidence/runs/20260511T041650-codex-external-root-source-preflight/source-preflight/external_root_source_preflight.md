# External Root Source Preflight

Run id: `20260511T041650+0800-codex-external-root-source-preflight`.

## Decision

- Gate result: `blocked_external_source_preflight_no_completion_eligible_new_source`
- Accepted new active roots: none
- Missing active roots remain: `BearExpansion`, `Manipulation`
- Raw external files stayed under `/private/tmp`; repo artifact is metadata/preflight only.

## Newly Downloaded Candidate

- `nickdatak/us-market-regimes-dataset-1995-2024`: `not_completion_eligible_for_active_roots`
  - labels are unsupervised `Calm` / `Stressful` / `Transitional`, not active MainRegimeV3SourceBacked `BearExpansion` evidence
  - single aggregate S&P 500 weekly market context and one timeframe cannot satisfy the board's multi-context root evidence requirement
  - `Stressful` is crisis/stress provenance, not a directional `BearExpansion` root, and `Calm` is unnecessary for completion after the accepted `SidewaysConsolidation` reissue
  - no direct event/order-lifecycle/L2/L3/MBO/social/on-chain manipulation evidence is present

## Search Summary

### Kaggle
- `mafaqbhatti/stock-market-regimes-20002026`: `already_exhausted_in_board` - existing Kaggle direct-label gates accepted `BullExpansion` only; `BearExpansion` remained below 95
- `ashrafkhetran/silver-gold-and-platinum-price-forecasting`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `sergionefedov/oil-and-geopolitics-9k-daily-obs-brent-35-years`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `nickdatak/us-market-regimes-dataset-1995-2024`: `downloaded_preflight_rejected` - unsupervised Calm/Stressful/Transitional labels; one S&P weekly context
- `bsthere/volkswagen-stock-data-1995-2026`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `kanchana1990/tech-giants-and-global-macroeconomic-indicators`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `sergionefedov/synthetic-limit-order-book-market-microstructure`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `ibrahimshahrukh/nvidia-daily-stock-prices-20162026-dataset`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `krupalpatel07/bitcoin-market-microstructure-dataset`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `ibrahimshahrukh/s-and-p-500-historical-data-1980-2026`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source
- `samyakrajbayar/global-fuel-prices-100-years-19242024`: `not_selected_this_loop` - search hit is not direct BearExpansion evidence or a direct manipulation source

### Hugging Face
- `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`: `candidate_not_completion_eligible_without_new_breadth` - single-market/single-family public dataset; insufficient for active multi-context parent-root completion by itself
- `AAdevloper/nifty50-market-regime`: `candidate_not_completion_eligible_without_new_breadth` - single-market/single-family public dataset; insufficient for active multi-context parent-root completion by itself
- `ClarusC64/market-regime-coherence-mapping-v0.1`: `too_small_or_conceptual_mapping` - mapping dataset, not calibration-grade market observations
- `ClarusC64/market-regime-transition-breakpoint-mapping-v0.1`: `too_small_or_conceptual_mapping` - mapping dataset, not calibration-grade market observations
- `sujinwo/tsie-market-regime-dataset`: `already_exhausted_in_board` - TSIE direct-label gates stayed below 95 and had one market context
