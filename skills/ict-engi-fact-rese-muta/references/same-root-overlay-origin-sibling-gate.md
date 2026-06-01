# Same-root overlay origin sibling gate

Use when a Gate 1 branch already has enough 1m density but downstream execution-readiness is blocked, and the next step is a same-root composite overlay such as session-liquidity or transition-stability.

## Session lesson

A same-root overlay must improve the exact 1m-origin branch broadly enough before downstream handoff. Higher-timeframe positives are useful subclass evidence, but they do not rescue a weak or single-symbol 1m origin.

Observed branch:

```text
RangeReversion -> BeautyPersonalCareOversoldReclaim -> rsi_vwap_reclaim_dense -> session_liquidity_transition_stability_overlay -> yf_beauty_personal_care_rsi_vwap_session_liquidity_overlay_1m_v4
```

Observed Gate 1 readback:

```text
rank_rows=17
rank_total_trades=194
origin_trades_1m=46
positive_rows_trade_ge_5=2
origin_positive_rows_trade_ge_5=1
branch_fields_preserved=true
dense_positive_gate=true
origin_gate=false
```

Useful rows:

```text
ULTA 1m: 33 trades, +1.74%, win 72.7273%
COTY 5m: 48 trades, +4.04%
```

Blocking rows/context:

```text
COTY 1m: 13 trades, -0.06%
ELF 1m: missing in this overlay run
HTF positives existed but did not satisfy exact 1m-origin breadth
```

## Rule

For a same-root composite overlay after a dense base factor:

1. Preserve full branch identity including overlay segment.
2. Require real provider rows; mark missing frames such as Yahoo `4h` as missing, never synthesize.
3. Inspect authoritative `ranking[]` rows.
4. Require ordinary density gates (`total_trades`, `origin_trades_1m`, branch fields).
5. Add an origin breadth gate before downstream:

```text
origin_positive_rows_trade_ge_5 >= 2
```

A single positive 1m sibling plus HTF positives is `drop_overlay_or_keep_subclass_evidence_no_downstream`, not BBN/CatBoost/execution-tree material.

## Correct terminal classification

```text
drop_overlay_or_keep_subclass_evidence_no_downstream
promotion_allowed=false
trade_usable=false
update_goal=false
```

## Practical next step

Try a materially different same-root overlay that targets transition hazard while preserving 1m-origin breadth, for example:

```text
RangeReversion -> BeautyPersonalCareOversoldReclaim -> rsi_vwap_reclaim_dense -> transition_stability_overlay -> profit_factor
```

Do not keep tightening session-liquidity if it reduces sibling breadth below the origin gate.
