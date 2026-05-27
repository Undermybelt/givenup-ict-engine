---
name: ict-engine-market-structure-context
description: >
  Build structured ICT/SMC market-structure evidence for ict-engine from fresh
  candles and validated structural studies such as BOS, CHoCH, order blocks,
  fair value gaps, equal highs/lows, premium/discount zones, and liquidity
  sweep context. Use for Structure and Technicals evidence only.
version: 1
---

# Market Structure Context

## Goal

Turn market-structure observations into structured evidence for `ict-engine`
without turning them into standalone trade calls.

This skill adapts the structural taxonomy and freshness discipline from
`MobiusQuant/OpenMobius-skill` into an `ict-engine`-compatible evidence packet.
It does not require or assume the Mobius API, Playwright, embeddings, or image
annotation workflows.

## Inputs

- `symbol`
- `timeframe`
- `session`
- provider/profile selected by `provider-selection`
- fresh candles or structure-ready derived series for the requested timeframe
- optional higher-timeframe context
- optional prior session high/low, equal highs/lows, or liquidity map

## Validation Rules

- Every structural claim must cite fresh candles from the selected provider.
- Structure timestamps must map to the requested timeframe and session.
- If BOS/CHoCH depends on unconfirmed swings or mixed stale windows, reduce
  confidence or fail closed.
- Zones must include price bounds and status (`active`, `mitigated`, `filled`,
  or `invalidated`).
- Liquidity labels such as equal highs/lows, premium/discount, and sweep levels
  must be based on explicit price geometry, not narration alone.
- If only chart screenshots or third-party commentary exist without fresh
  candle evidence, fail closed for runtime promotion.

## Output Schema

```json
{
  "skill": "ict-engine-market-structure-context",
  "symbol": null,
  "timeframe": null,
  "session": null,
  "as_of": null,
  "provider": null,
  "swing_bias": "unknown",
  "internal_bias": "unknown",
  "latest_structure_event": {
    "kind": null,
    "bias": null,
    "pivot_time": null,
    "confirm_time": null,
    "evidence_source": null
  },
  "liquidity_state": "unknown",
  "premium_discount_state": "unknown",
  "zones": [
    {
      "zone_type": "order_block",
      "bias": null,
      "top": null,
      "bottom": null,
      "status": "unknown",
      "anchor_time": null,
      "evidence_source": null
    }
  ],
  "levels": [
    {
      "level_type": "equal_high",
      "price": null,
      "status": "unknown",
      "evidence_source": null
    }
  ],
  "regime_posterior_evidence": {
    "trend": null,
    "range": null,
    "transition": null,
    "stress": null,
    "other": null
  },
  "execution_tree_features": {
    "structure_continuation_bias": null,
    "reversal_risk": null,
    "liquidity_sweep_risk": null,
    "zone_proximity": null,
    "premium_discount_alignment": null
  },
  "confidence": 0.0,
  "allowed_for_runtime_promotion": false,
  "fail_closed_reason": null
}
```

## Engine Mapping

- `Structure`: BOS/CHoCH state, swing/internal bias, liquidity sweep context.
- `Technicals`: order blocks, fair value gaps, premium/discount placement,
  equal highs/lows, zone proximity.
- `SMT`: optional confirmation only when a separate SMT skill supplies the
  relationship evidence.
- `Regime posterior evidence`: continuation vs reversal pressure, liquidity
  compression, and transition probability hints.
- `Execution tree features`: structure continuation bias, reversal risk, sweep
  risk, and nearby zone geometry.
- `Feedback/update learning fields`: provider, timestamps, zone status, and
  realized reaction after confirmation or mitigation.

## Fail-Closed Rules

Fail closed when:

- provider is not selected or provider health is unknown;
- candles are stale for the requested timeframe/session;
- structural events cannot be tied to explicit pivot and confirmation bars;
- zone bounds are ambiguous or missing;
- screenshot-only/image-only evidence is used without fresh candle validation;
- confidence is low across the selected timeframe or higher-timeframe context
  contradicts the local claim.
