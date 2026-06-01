# Single-stock refinement AQ parity

Use when a broad/public factor has one strong single-stock row and the next step is a symbol-specific refinement.

## Pattern from session

Case: public Elder Impulse / MACD histogram 30m, retained real IBKR NVDA 30m candles.

Rooted branch shape:

`TrendExpansion -> MomentumPersistence -> public_elder_impulse_macd_histogram_nvda_refined_30m -> ibkr_nvda_elder_impulse_refined_30m_v1`

Workflow used:
1. Start from the existing cross-symbol AQ evidence, not from a new invented factor.
2. Run a small vector prefilter with explicit cost stress before Auto-Quant.
3. Preserve the regime-rooted branch fields in the material:
   - `branch_path`
   - `regime_profit_branch_path`
   - `main_regime`
   - `sub_regime`
   - `sub_sub_regime_or_profit_factor`
   - `profit_factor`
4. Dispatch the refined candidate through `auto-quant-agent-material-batch`, `dispatch`, and `rank`.
5. Compare the refined AQ row against the original same-symbol AQ row before downstream promotion.

## Decision rule

A symbol-specific refinement that merely reproduces the original same-symbol AQ result is not an improvement.

Do not proceed to BBN / CatBoost / execution tree when all are true:
- only one symbol passes;
- sibling symbols remain negative or untested;
- AQ metrics are equal to or worse than the existing same-symbol row;
- no validation maturity is added.

Classify as:

`incubate_symbol_specific_only` or `done_incubate_no_incremental_improvement`

## Evidence shape to preserve

Minimum summary fields:
- run root
- rank artifact path
- source data path and provider provenance
- original baseline AQ row
- refined AQ row
- vector prefilter path
- branch path
- explicit reason downstream was stopped

## Pitfall

Do not let a good-looking vector-grid result override Auto-Quant parity. The vector grid is only candidate discovery. Promotion requires the refined AQ result to improve over the existing same-symbol row or add portability / maturity evidence.
