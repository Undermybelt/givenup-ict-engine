# First-class ICT factor evidence packets

Use when Board B asks to train ICT/SMC factors as runtime evidence rather than prose: SMT resolver, liquidity pool texture, sweep quality, FVG/IFVG lifecycle, order block variant, market structure events, Brooks context, and options dealer context.

## Operating rule

Do not treat these factors as template wording. They must become structured JSON/CSV evidence with price levels, provenance, fail-closed reasons, per-regime stats, and runtime field mapping.

Minimum packet shape:

- `factor_id`
- `branch_path` / `regime_profit_branch_path`
- `base_symbol`, `timeframe`, `session`, `provider`
- exact price fields: `level`, `high`, `low`, `top`, `bottom`, `midpoint`, `entry`, `stop`, `target` as applicable
- confirmation fields: `mss_or_cisd_confirmed`, `displacement_confirmed`, `near_pd_array`, `pd_array_type`
- `confidence`
- `fail_closed_reason`
- realized outcome fields when available: `realized_trade`, `realized_r`, `outcome_label`
- per-regime stats for `trend`, `range`, `transition`, `stress`, `other`
- coverage: instruments, providers, timeframes, sample window
- runtime mapping buckets: `Structure`, `Technicals`, `SMT`, `Regime posterior evidence`, `Execution tree features`, `Feedback/update learning fields`

## Factor-specific guardrails

### SMT relationship resolver

If an active SMT lane exists, do not take it over. SMT is not generic correlation or relative strength. It detects sibling-market confirmation failure around the same liquidity/swing event.

Required SMT properties:

- dynamic related-symbol search from the user symbol
- relationship type and confidence
- same timeframe, same session, same swing/liquidity event
- inverse-correlation normalization when needed, with `normalized_for_inverse_correlation=true` plus raw original structure
- base and comparison levels on every signal
- fail closed on unstable relationship, missing overlap, missing levels, missing candles, or mismatched timeframe/session
- never standalone `actionable=true`; it is confirmation / entry-likelihood evidence only

### Order block variant classifier

Use existing provider-backed ATR/CISD/FVG/OB outcome rows when available to bootstrap a first-class packet. Required fields:

- `variant`: `order_block`, `mitigation_block`, `breaker_block`, `rejection_block`, `failed_mitigation`, or `none`
- `direction`
- `high`, `low`, `midpoint`
- `validation_state`
- `mitigation_count`
- `breaker_confirmed`
- `rejection_confirmed`
- `confidence`
- `fail_closed_reason`

Do not promote generic OB evidence if aggregate expectancy is negative or coverage lacks the requested futures/metals universe. Treat it as structure/context evidence until wider provider/instrument coverage and explicit breaker/rejection confirmation rows exist.

### FVG/IFVG lifecycle

Do not borrow OB or direct-limit profitability into FVG. Split the lifecycle rows and judge FVG/IFVG on its own realized outcomes. If isolated FVG retests have zero win rate, mark `drop` or fail closed for downstream admission.

### Liquidity/sweep/Brooks/market-structure

Keep the factor question narrow: one factor, one gate, one root regime if needed. A positive packet may still be non-promotable if branch-path fields disappear before target export, validation rows are immature, or execution tree remains observe/guarded.

## Workflow

1. Check `/tmp/ict-engine-agent-claims/board-b/` and the compact Board B current doc before taking a lane.
2. If a factor is active/claimed, do not continue or repair it unless explicitly asked. Pick a different factor axis.
3. Prefer existing provider-backed outcome rows before creating synthetic rows. Never synthesize realized trades from aggregate summaries.
4. Generate a compact run-root with `materials/`, `schemas/`, `mappings/`, `summaries/`, and `checks/`.
5. Assert parity: required price levels present, fail-closed rows explicit, no standalone actionable rows for confirmation-only factors, per-regime stats written.
6. Only run BBN/CatBoost/execution-tree after Gate 1/2 evidence is worth carrying and branch fields survive.
7. Append only a terminal Board B decision row: `keep`, `drop`, `incubate`, `blocked`, or `handoff`.

## Decision hints

- `keep`: useful factor evidence with positive expectancy, sufficient support, and acceptable coverage, but not necessarily downstream-promoted.
- `incubate`: structured evidence exists but coverage/profitability/readiness is insufficient for promotion.
- `drop`: isolated factor slice is clearly negative and should not continue downstream unchanged.
- `blocked`: required provider/schema/level/outcome data is missing.
- `handoff`: a real downstream chain or diagnostic ran but the next blocker belongs to a different axis.
